"""Egress firewall for user containers (Traefik mode).

Runs in its own container on the host network, started and kept current by the
backend (ContainerManager.ensure_egress_firewall). User containers keep the
public internet and their own network. They lose the host, the LAN, cloud
metadata, Traefik's own ports (its API and dashboard) and outgoing mail.

Docker only isolates bridges from each other: without this, a student reaches
everything the host publishes and everything the host can reach.

Stopping the container keeps the rules, so a stopped firewall does not open the
sandbox. `python -m app.services.egress_firewall remove` takes them out.
"""

import ipaddress
import os
import signal
import subprocess
import sys
import time

import docker

EGRESS_CHAIN = "SPAWNER-EGRESS"
HOST_CHAIN = "SPAWNER-HOST"

# Private, shared, link-local (cloud metadata), multicast and reserved ranges
BLOCKED = (
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "224.0.0.0/4",
    "240.0.0.0/4",
)


def log(message):
    print(f"[FIREWALL] {message}", flush=True)


def run(args, stdin=None):
    try:
        return subprocess.run(
            args, input=stdin, capture_output=True, text=True, check=False
        )
    except OSError as e:  # binary missing
        return subprocess.CompletedProcess(args, 127, "", str(e))


def detect_variant():
    """The iptables variant Docker uses: its DOCKER-USER chain only exists there."""
    for variant in ("nft", "legacy"):
        if run([f"iptables-{variant}", "-w", "-S", "DOCKER-USER"]).returncode == 0:
            return variant
    return None


def parse_allow(value):
    """EGRESS_ALLOW entries: CIDR or CIDR:port (tcp), comma-separated."""
    rules = []
    for entry in (e.strip() for e in value.split(",")):
        if not entry:
            continue
        address, _, port = entry.partition(":")
        net = ipaddress.ip_network(address, strict=False)
        if port:
            rules.append(f"-d {net} -p tcp --dport {int(port)} -j RETURN")
        else:
            rules.append(f"-d {net} -j RETURN")
    return rules


def egress_rules(subnet, allow, traefik_ips):
    """Traffic from user containers that the host forwards (DOCKER-USER)."""
    rules = ["-m conntrack --ctstate RELATED,ESTABLISHED -j RETURN"]
    # Traefik opens the connections to user containers, never the other way
    # round. Its API on port 8080 would show every route and middleware.
    rules += [f"-d {ip}/32 -j REJECT" for ip in traefik_ips]
    # Docker's DNS forwards the containers' queries from inside their network.
    # The resolver is often on a private address, and on hosts with
    # systemd-resolved it is not even visible in /etc/resolv.conf.
    rules += ["-p udp --dport 53 -j RETURN", "-p tcp --dport 53 -j RETURN"]
    # Spam from the school's only public address would get it blocklisted
    rules += ["-p tcp --dport 25 -j REJECT"]
    # A student's own containers talk to each other. Other students stay
    # blocked by Docker's isolation rules, which run after DOCKER-USER.
    rules += [f"-d {subnet} -j RETURN"]
    rules += allow
    rules += [f"-d {net} -j REJECT" for net in BLOCKED]
    return rules


def host_rules():
    """Traffic from user containers to the host itself (INPUT)."""
    return [
        "-m conntrack --ctstate RELATED,ESTABLISHED -j RETURN",
        "-p udp --dport 53 -j RETURN",
        "-p tcp --dport 53 -j RETURN",
        "-j REJECT",
    ]


def hooks(subnet):
    return [
        ("DOCKER-USER", EGRESS_CHAIN, f"-s {subnet} -j {EGRESS_CHAIN}"),
        # Traffic to the host's own addresses never reaches DOCKER-USER
        ("INPUT", HOST_CHAIN, f"-s {subnet} ! -i lo -j {HOST_CHAIN}"),
    ]


def hooked(variant, chain, spec):
    return (
        run([f"iptables-{variant}", "-w", "-C", chain, *spec.split()]).returncode == 0
    )


def rule_count(variant, chain):
    out = run([f"iptables-{variant}", "-w", "-S", chain])
    if out.returncode != 0:
        return -1
    return sum(line.startswith("-A ") for line in out.stdout.splitlines())


def intact(variant, subnet, egress, host):
    """Hooks in place and both chains complete (nothing flushed or edited)."""
    return (
        all(hooked(variant, chain, spec) for chain, _, spec in hooks(subnet))
        and rule_count(variant, EGRESS_CHAIN) == len(egress)
        and rule_count(variant, HOST_CHAIN) == len(host)
    )


def remove_hooks(variant, keep=()):
    """Deletes every jump to our chains, except the specs in keep."""
    for chain, target in (("DOCKER-USER", EGRESS_CHAIN), ("INPUT", HOST_CHAIN)):
        out = run([f"iptables-{variant}", "-w", "-S", chain]).stdout
        for line in out.splitlines():
            if not (line.startswith(f"-A {chain} ") and line.endswith(f"-j {target}")):
                continue
            spec = line.split()[2:]
            if any(sorted(spec) == sorted(k.split()) for k in keep):
                continue
            run([f"iptables-{variant}", "-w", "-D", chain, *spec])


def apply(variant, subnet, egress, host):
    """Replaces both chains in one transaction: no moment without rules."""
    payload = ["*filter", f":{EGRESS_CHAIN} - [0:0]", f":{HOST_CHAIN} - [0:0]"]
    payload += [f"-A {EGRESS_CHAIN} {rule}" for rule in egress]
    payload += [f"-A {HOST_CHAIN} {rule}" for rule in host]
    for chain, _, spec in hooks(subnet):
        if not hooked(variant, chain, spec):
            payload.append(f"-I {chain} 1 {spec}")
    payload.append("COMMIT")
    result = run(
        [f"iptables-{variant}-restore", "-w", "--noflush"], "\n".join(payload) + "\n"
    )
    if result.returncode != 0:
        log(f"Applying rules failed: {result.stderr.strip()}")
        return False
    # Jumps for an older subnet or rule format
    remove_hooks(variant, keep=[spec for _, _, spec in hooks(subnet)])
    return True


def remove():
    variants = [detect_variant()] if detect_variant() else ["nft", "legacy"]
    for variant in variants:
        remove_hooks(variant)
        for chain in (EGRESS_CHAIN, HOST_CHAIN):
            run([f"iptables-{variant}", "-w", "-F", chain])
            run([f"iptables-{variant}", "-w", "-X", chain])
    log("Rules removed")


def traefik_ips(client, name, subnet):
    """Traefik's addresses on the user networks, None if it cannot be inspected."""
    try:
        networks = (
            client.api.inspect_container(name)["NetworkSettings"]["Networks"] or {}
        )
    except Exception as e:
        log(f"Traefik container {name} not readable: {e}")
        return None
    ips = {n.get("IPAddress") for n in networks.values()}
    found = [ip for ip in ips if ip and ipaddress.ip_address(ip) in subnet]
    return sorted(found, key=ipaddress.ip_address)


def main(argv):
    if argv[1:] == ["remove"]:
        remove()
        return 0

    # As PID 1 Python ignores SIGTERM without a handler. Exiting keeps the rules.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    subnet = ipaddress.ip_network(
        os.environ.get("USER_NETWORK_SUBNET", "10.213.0.0/16")
    )
    allow = parse_allow(os.environ.get("EGRESS_ALLOW", ""))
    interval = int(os.environ.get("EGRESS_CHECK_INTERVAL", "10"))
    traefik = os.environ.get("TRAEFIK_CONTAINER", "")
    client = docker.from_env() if traefik else None
    if not traefik:
        log("No Traefik container given: its ports stay reachable from user networks")

    ips, applied, problem = [], None, None
    while True:
        try:
            variant = detect_variant()
            if variant != "nft":
                reason = (
                    "Docker uses iptables-legacy, which is not supported: without the "
                    "host's lock our changes could overwrite Docker's own rules"
                    if variant == "legacy"
                    else "Chain DOCKER-USER not found: Docker is not using iptables"
                )
                if reason != problem:
                    log(f"INACTIVE. {reason}")
                    problem = reason
                applied = None
                time.sleep(interval)
                continue
            problem = None

            if client is not None:
                found = traefik_ips(client, traefik, subnet)
                if found is not None:
                    ips = found

            egress, host = egress_rules(subnet, allow, ips), host_rules()
            if (egress, host) != applied or not intact(variant, subnet, egress, host):
                if apply(variant, subnet, egress, host):
                    log(
                        f"Rules applied for {subnet} (Traefik addresses blocked: {len(ips)})"
                    )
                    applied = (egress, host)
                else:
                    applied = None
        except Exception as e:
            log(f"Check failed: {e}")
            applied = None
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
