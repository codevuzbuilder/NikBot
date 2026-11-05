import json
import os
import sqlite3
import time


class DB:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.c = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.c.row_factory = sqlite3.Row
        self.c.executescript("""
        PRAGMA journal_mode=DELETE;
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, username TEXT,
            joined INTEGER, seen INTEGER, banned INTEGER DEFAULT 0, nicks INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS guides(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT);
        CREATE TABLE IF NOT EXISTS state(uid INTEGER PRIMARY KEY, s TEXT, d TEXT);
        CREATE TABLE IF NOT EXISTS lastnick(uid INTEGER PRIMARY KEY, t TEXT);
        """)

    def x(self, sql, *a):
        return self.c.execute(sql, a)

    def all(self, sql, *a):
        return self.c.execute(sql, a).fetchall()

    def one(self, sql, *a):
        return self.c.execute(sql, a).fetchone()

    # --- kv ---
    def kvget(self, k, d=None):
        r = self.one("SELECT v FROM kv WHERE k=?", k)
        return json.loads(r["v"]) if r else d

    def kvset(self, k, v):
        self.x("INSERT INTO kv VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", k, json.dumps(v, ensure_ascii=False))

    def kvdel(self, k):
        self.x("DELETE FROM kv WHERE k=?", k)

    # --- holat ---
    def state(self, uid):
        r = self.one("SELECT s,d FROM state WHERE uid=?", uid)
        return (r["s"], json.loads(r["d"] or "{}")) if r else (None, {})

    def setstate(self, uid, s, d=None):
        if s is None:
            self.x("DELETE FROM state WHERE uid=?", uid)
        else:
            self.x("INSERT INTO state VALUES(?,?,?) ON CONFLICT(uid) DO UPDATE SET s=excluded.s,d=excluded.d",
                   uid, s, json.dumps(d or {}, ensure_ascii=False))

    # --- foydalanuvchi ---
    def touch(self, u):
        now = int(time.time())
        name = (u.get("first_name", "") + " " + u.get("last_name", "")).strip()
        self.x("INSERT OR IGNORE INTO users(id,name,username,joined,seen) VALUES(?,?,?,?,?)",
               u["id"], name, u.get("username"), now, now)
        self.x("UPDATE users SET name=?,username=?,seen=? WHERE id=?", name, u.get("username"), now, u["id"])

    def snapshot(self, path):
        import sqlite3 as s3
        d = s3.connect(path)
        self.c.backup(d)
        d.close()
