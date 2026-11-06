#!/bin/bash
# Denní záloha e-shopu M+P Král: databáze (konzistentní kopie i za běhu) + nahrané fotky.
# Spouští cron (/etc/cron.d/mpkral). Nemaže nic kromě vlastních záloh starších 30 dní.
# Databázi čte uživatel mpkral — kdyby ji otevřel root, mohl by vytvořit -wal/-shm soubory,
# které by pak aplikace nesměla číst.
set -euo pipefail
CIL=/opt/mpkral/zalohy
DATA=/opt/mpkral/data
DNES=$(date +%Y-%m-%d_%H%M)
TMP="$DATA/.zaloha-$DNES.db"
mkdir -p "$CIL" && chmod 700 "$CIL"
sudo -u mpkral /opt/mpkral/venv/bin/python -I - "$DATA/eshop.db" "$TMP" <<'PY'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1], timeout=30)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity_check selhal"
dst.close()
PY
gzip -c "$TMP" > "$CIL/eshop-$DNES.db.gz" && rm -f "$TMP"
[ -d "$DATA/nahrane" ] && tar -czf "$CIL/nahrane-$DNES.tar.gz" -C "$DATA" nahrane
chmod 600 "$CIL"/*-"$DNES".*
find "$CIL" -maxdepth 1 -type f \( -name 'eshop-*.db.gz' -o -name 'nahrane-*.tar.gz' \) -mtime +30 -delete
echo "$(date '+%F %T') ok, zalohy celkem $(du -sh "$CIL" | cut -f1)"
