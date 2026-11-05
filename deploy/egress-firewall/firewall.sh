#!/bin/sh
# Keeps user containers in their sandbox: they reach the public internet and
# their own network, but not the host, the LAN or cloud metadata. Docker only
# isolates bridges from each other. Without this, a student can open everything
# the host publishes or can reach itself.
#
# Usage: firewall.sh          apply, then re-apply if the rules disappear
#        firewall.sh remove   take the rules out again
#
# Runs on the host network. The rules stay when this container stops, so
# stopping it does not open the sandbox: use `remove` for that.
set -eu

SUBNET="${USER_NETWORK_SUBNET:-10.213.0.0/16}"
ALLOW="$(echo "${EGRESS_ALLOW:-}" | tr ',' ' ')"
INTERVAL="${EGRESS_CHECK_INTERVAL:-30}"
FORWARD_CHAIN=SPAWNER-EGRESS
INPUT_CHAIN=SPAWNER-HOST
BLOCKED="10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 169.254.0.0/16 224.0.0.0/4"

# Has to be the backend Docker uses, its DOCKER-USER chain only exists there
if iptables-nft -S DOCKER-USER >/dev/null 2>&1; then
    IPT=iptables-nft
elif iptables-legacy -S DOCKER-USER >/dev/null 2>&1; then
    IPT=iptables-legacy
else
    echo "[FIREWALL] Chain DOCKER-USER not found, is Docker using iptables?" >&2
    exit 1
fi

ipt() {
    "$IPT" -w "$@"
}

hooked() {
    ipt -C DOCKER-USER -s "$SUBNET" -j "$FORWARD_CHAIN" 2>/dev/null \
        && ipt -C INPUT -s "$SUBNET" -j "$INPUT_CHAIN" 2>/dev/null
}

# Docker forwards DNS queries from inside the container, so a resolver on a
# private address (usual in a LAN) must stay reachable. Loopback resolvers are
# queried from the host and need no rule.
resolvers() {
    sed -n 's/^nameserver[[:space:]]*\([0-9.]*\).*/\1/p' /etc/resolv.conf | grep -v '^127\.' || true
}

apply() {
    ipt -N "$FORWARD_CHAIN" 2>/dev/null || ipt -F "$FORWARD_CHAIN"
    ipt -N "$INPUT_CHAIN" 2>/dev/null || ipt -F "$INPUT_CHAIN"

    for chain in "$FORWARD_CHAIN" "$INPUT_CHAIN"; do
        ipt -A "$chain" -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
        for resolver in $(resolvers); do
            ipt -A "$chain" -d "$resolver" -p udp --dport 53 -j RETURN
            ipt -A "$chain" -d "$resolver" -p tcp --dport 53 -j RETURN
        done
    done

    # A student's own containers talk to each other. Other students stay
    # blocked by Docker's isolation rules, which run after DOCKER-USER.
    ipt -A "$FORWARD_CHAIN" -d "$SUBNET" -j RETURN
    for net in $ALLOW; do
        ipt -A "$FORWARD_CHAIN" -d "$net" -j RETURN
    done
    for net in $BLOCKED; do
        ipt -A "$FORWARD_CHAIN" -d "$net" -j REJECT
    done

    # Traffic to the host's own addresses never reaches DOCKER-USER
    ipt -A "$INPUT_CHAIN" -j REJECT

    ipt -C DOCKER-USER -s "$SUBNET" -j "$FORWARD_CHAIN" 2>/dev/null \
        || ipt -I DOCKER-USER 1 -s "$SUBNET" -j "$FORWARD_CHAIN"
    ipt -C INPUT -s "$SUBNET" -j "$INPUT_CHAIN" 2>/dev/null \
        || ipt -I INPUT 1 -s "$SUBNET" -j "$INPUT_CHAIN"
    echo "[FIREWALL] Rules applied for $SUBNET ($IPT, resolvers: $(resolvers | tr '\n' ' '))"
}

remove() {
    ipt -D DOCKER-USER -s "$SUBNET" -j "$FORWARD_CHAIN" 2>/dev/null || true
    ipt -D INPUT -s "$SUBNET" -j "$INPUT_CHAIN" 2>/dev/null || true
    for chain in "$FORWARD_CHAIN" "$INPUT_CHAIN"; do
        ipt -F "$chain" 2>/dev/null || true
        ipt -X "$chain" 2>/dev/null || true
    done
    echo "[FIREWALL] Rules removed"
}

if [ "${1:-}" = "remove" ]; then
    remove
    exit 0
fi

trap 'exit 0' TERM INT
apply
while true; do
    sleep "$INTERVAL" &
    wait $!
    hooked || apply
done
