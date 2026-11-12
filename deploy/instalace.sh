#!/bin/bash
# Jednorázová příprava serveru (spouští se jako root na serveru, idempotentní).
# Kód pak nahrává ../deploy.sh. Hesla ani klíče sem nepatří — /opt/mpkral/env se zakládá prázdný.
set -euo pipefail
id mpkral >/dev/null 2>&1 || useradd --system --home-dir /opt/mpkral/data --shell /usr/sbin/nologin mpkral
mkdir -p /opt/mpkral/app /opt/mpkral/data /opt/mpkral/zalohy
chown mpkral:mpkral /opt/mpkral/data && chmod 750 /opt/mpkral/data
chmod 700 /opt/mpkral/zalohy
[ -x /opt/mpkral/venv/bin/python ] || python3 -m venv /opt/mpkral/venv
if [ ! -f /opt/mpkral/env ]; then
  printf '# Prostředí e-shopu (mimo git). TESTOVACI=1 = web skrytý před vyhledávači.\nTESTOVACI=1\n' > /opt/mpkral/env
fi
chmod 600 /opt/mpkral/env
install -m 644 /opt/mpkral/app/deploy/mpkral.service /etc/systemd/system/mpkral.service
install -m 644 /opt/mpkral/app/deploy/cron /etc/cron.d/mpkral
install -m 644 /opt/mpkral/app/deploy/traefik-mpkral.yaml /data/coolify/proxy/dynamic/mpkral.yaml
systemctl daemon-reload
systemctl enable mpkral
