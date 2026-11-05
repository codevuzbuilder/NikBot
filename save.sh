#!/usr/bin/env bash
# DB ni xavfsiz nusxalaydi, shifrlaydi va "data" branchga push qiladi.
set -u
cd "$(dirname "$0")"
[ -f work/bot.db ] || exit 0
python3 - <<'PY'
import sqlite3
s = sqlite3.connect("work/bot.db"); d = sqlite3.connect("work/snap.db"); s.backup(d); d.close(); s.close()
PY
H=$(sha256sum work/snap.db | cut -d' ' -f1)
[ "$H" = "$(cat work/last.sha 2>/dev/null)" ] && exit 0
openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:KEY -in work/snap.db -out storage/bot.db.enc || exit 1
cd storage
git add bot.db.enc
git commit -q --amend -m "data" 2>/dev/null || git commit -q -m "data"
git push -q -f origin HEAD:data && echo "$H" > ../work/last.sha
