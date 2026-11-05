FROM alpine:3.22

RUN apk add --no-cache iptables iptables-legacy

COPY firewall.sh /usr/local/bin/firewall.sh

ENTRYPOINT ["sh", "/usr/local/bin/firewall.sh"]
