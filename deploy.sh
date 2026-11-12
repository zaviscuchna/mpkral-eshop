#!/bin/bash
# Nasazení e-shopu na server (https://mpkral.46.225.180.130.sslip.io, později mpkral.cz).
# Posílá jen soubory z gitu (HEAD) — žádná databáze, hesla ani .venv.
# Data na serveru (/opt/mpkral/data: databáze, fotky od mamky, objednávky) zůstávají.
#   ./deploy.sh            nasadit
#   ./deploy.sh --prvni    poprvé: založí uživatele, službu, Traefik a zálohy (deploy/instalace.sh)
set -euo pipefail
cd "$(dirname "$0")"
SERVER=root@46.225.180.130
ADRESA=https://mpkral.46.225.180.130.sslip.io
if [ -n "$(git status --porcelain)" ]; then
  echo "Nejdřív commitni změny (nasazuje se HEAD z gitu)."; exit 1
fi
PRVNI=0; [ "${1:-}" = "--prvni" ] && PRVNI=1
git archive --format=tar HEAD | ssh -o BatchMode=yes "$SERVER" "set -e
  mkdir -p /opt/mpkral/app
  find /opt/mpkral/app -mindepth 1 -delete
  tar -x -C /opt/mpkral/app && chown -R root:root /opt/mpkral/app
  [ $PRVNI = 1 ] && bash /opt/mpkral/app/deploy/instalace.sh
  /opt/mpkral/venv/bin/pip install -q --disable-pip-version-check -r /opt/mpkral/app/requirements.txt
  systemctl restart mpkral
  for i in \$(seq 1 40); do [ \"\$(curl -s -o /dev/null -m 3 -w '%{http_code}' http://127.0.0.1:5068/)\" = 200 ] && break; sleep 1; done
  echo \"služba: \$(systemctl is-active mpkral)\""
echo "web: $(curl -s -o /dev/null -m 20 -w '%{http_code}' $ADRESA/)"
