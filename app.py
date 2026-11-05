import asyncio
import html
import logging
import time

from . import admin, fonts, ui
from .db import DB
from .tg import TG
from .ui import B, render

log = logging.getLogger("app")
FONT_N = fonts.FONT_COUNT
MEDIA = {"photo": "sendPhoto", "video": "sendVideo", "voice": "sendVoice", "video_note": "sendVideoNote"}
SAMPLE = "Nickname 2025"


def u16(s):
    return len(s.encode("utf-16-le")) // 2


def split16(s, n=3500):
    out, cur, c = [], "", 0
    for ch in s:
        w = u16(ch)
        if c + w > n:
            out.append(cur)
            cur, c = "", 0
        cur += ch
        c += w
    return out + [cur] if cur else out


class App:
    def __init__(self, token, admin_id, db_path):
        self.tg = TG(token)
        self.db = DB(db_path)
        self.admin_id = admin_id
        self.locks = {}
        ui.load(self.db)

    # ---------- yordamchilar ----------
    def is_admin(self, uid):
        return uid == self.admin_id or uid in self.db.kvget("admins", [])

    def get_msg(self, key):
        o = self.db.kvget("msg:" + key)
        if o:
            return o
        return {"html": ui.DEFAULTS[key]} if key in ui.DEFAULTS else {"text": ""}

    def save_msg(self, key, msg):
        self.db.kvset("msg:" + key, msg)

    def max_len(self, kind):
        return self.db.kvget("max_" + kind, 40 if kind == "short" else 2000)

    def resolve(self, msg, fmt):
        if "html" in msg:
            return render(msg["html"], **fmt), None, "HTML"
        return msg.get("text") or "", msg.get("entities") or None, None

    async def send(self, chat, msg, kb=None, **fmt):
        text, ent, pm = self.resolve(msg, fmt)
        mt, mf = msg.get("mt"), msg.get("mf")
        rm = {"inline_keyboard": kb} if kb else None
        if mt in ("photo", "video", "voice") and len(text) <= 1024:
            return await self.tg.call(MEDIA[mt], chat_id=chat, **{mt: mf}, caption=text or None,
                                      caption_entities=ent, parse_mode=pm, reply_markup=rm)
        if mt:
            await self.tg.call(MEDIA[mt], chat_id=chat, **{mt: mf})
        return await self.tg.call("sendMessage", chat_id=chat, text=text or "—", entities=ent, parse_mode=pm,
                                  reply_markup=rm, link_preview_options={"is_disabled": True})

    async def say(self, chat, t, kb=None, **fmt):
        return await self.send(chat, {"html": t}, kb, **fmt)

    async def nav(self, q, msg, kb, **fmt):
        m = q["message"]
        chat, mid = m["chat"]["id"], m["message_id"]
        if not msg.get("mt") and "text" in m:
            text, ent, pm = self.resolve(msg, fmt)
            r = await self.tg.call("editMessageText", chat_id=chat, message_id=mid, text=text or "—", entities=ent,
                                   parse_mode=pm, reply_markup={"inline_keyboard": kb or []},
                                   link_preview_options={"is_disabled": True})
            if r:
                return
        await self.tg.call("deleteMessage", chat_id=chat, message_id=mid)
        await self.send(chat, msg, kb, **fmt)

    def menu_kb(self, uid):
        n = ["short", "long", "fonts", "guide", "help", "profile"]
        rows = [[ui.mb(n[i]), ui.mb(n[i + 1])] for i in range(0, 6, 2)]
        if self.is_admin(uid):
            rows.append([ui.mb("admin")])
        return rows

    # ---------- obuna / ruxsat ----------
    async def unsub(self, uid):
        if not self.db.kvget("sub_on", True):
            return []
        out = []
        for ch in self.db.kvget("channels", []):
            r = await self.tg.call("getChatMember", chat_id=ch["id"], user_id=uid)
            if not r:
                continue
            if r["status"] in ("left", "kicked") or (r["status"] == "restricted" and not r.get("is_member", True)):
                out.append(ch)
        return out

    async def gate(self, uid, chat):
        if self.is_admin(uid):
            return True
        row = self.db.one("SELECT banned FROM users WHERE id=?", uid)
        if row and row["banned"]:
            await self.send(chat, self.get_msg("banned"))
            return False
        if self.db.kvget("maint", False):
            await self.send(chat, self.get_msg("maint"))
            return False
        bad = await self.unsub(uid)
        if bad:
            kb = [[B(c["title"], url=c["link"], color="blue", slot="channel")] for c in bad]
            kb.append([B("Tekshirish", "chk", color="green", slot="check")])
            await self.send(chat, self.get_msg("sub_need"), kb)
            return False
        return True

    # ---------- asosiy oqim ----------
    async def start(self, u, chat):
        self.db.setstate(u["id"], None)
        await self.send(chat, self.get_msg("start"), self.menu_kb(u["id"]), name=html.escape(u.get("first_name", "")))

    async def ask(self, uid, chat, kind, q=None):
        self.db.setstate(uid, "n:text", {"kind": kind})
        kb = [ui.nav_row()]
        msg = self.get_msg("ask_" + kind)
        if q:
            await self.nav(q, msg, kb, max=self.max_len(kind))
        else:
            await self.send(chat, msg, kb, max=self.max_len(kind))

    async def make_nick(self, uid, chat, text, num):
        nick = fonts.apply(text, num)
        self.db.setstate(uid, None)
        self.db.x("INSERT INTO lastnick VALUES(?,?) ON CONFLICT(uid) DO UPDATE SET t=excluded.t", uid, nick)
        self.db.x("UPDATE users SET nicks=nicks+1 WHERE id=?", uid)
        chunks = split16(nick)
        for i, ch in enumerate(chunks):
            last = i == len(chunks) - 1
            head = ui.render(ui.DEFAULTS["ready"], n=num) + "\n\n" if i == 0 else ""
            if self.db.kvget("msg:ready"):  # admin o'zgartirgan bo'lsa
                head = (render(self.get_msg("ready").get("html", ui.DEFAULTS["ready"]), n=num) + "\n\n") if i == 0 else ""
            kb = None
            if last:
                cp = B("Nusxa olish", copy=nick, color="green", slot="copy") if u16(nick) <= 256 \
                    else B("Nusxa olish", "cp", color="green", slot="copy")
                kb = [[cp], [B("Yangi nik yasash", "new2", color="blue", slot="new"),
                             B("Menyu", "menu2", color="red", slot="menu")]]
            await self.tg.call("sendMessage", chat_id=chat, text=f"{head}<code>{html.escape(ch)}</code>",
                               parse_mode="HTML", reply_markup={"inline_keyboard": kb} if kb else None)

    def fonts_msg(self, page):
        pages = (FONT_N + 9) // 10
        page = max(1, min(pages, page))
        lines = [f"<b>{n}.</b> {html.escape(fonts.apply(SAMPLE, n))}" for n in range((page - 1) * 10 + 1, min(FONT_N, page * 10) + 1)]
        t = "{e:fonts} <b>Shriftlar namunasi</b>\n\n" + "\n".join(lines) + "\n\nRaqamni eslab qoling va nik yasashda yuboring."
        kb = [[B("Oldingi", f"fp:{max(1, page - 1)}", color="blue", slot="prev"), B(f"{page}/{pages}", "noop"),
               B("Keyingi", f"fp:{min(pages, page + 1)}", color="blue", slot="next")], ui.nav_row()]
        return {"html": t}, kb

    async def guides_screen(self, q):
        gs = self.db.all("SELECT id,title FROM guides ORDER BY id")
        cols = ["blue", "green", "red"]
        kb = [[B(g["title"], f"g:{g['id']}", color=cols[i % 3], slot="guide")] for i, g in enumerate(gs)]
        kb.append(ui.nav_row())
        await self.nav(q, self.get_msg("guides_title" if gs else "no_guides"), kb)

    async def on_cb(self, q):
        u, uid = q["from"], q["from"]["id"]
        d = q.get("data", "")
        chat = q["message"]["chat"]["id"]
        await self.tg.call("answerCallbackQuery", callback_query_id=q["id"])
        self.db.touch(u)
        if d == "noop":
            return
        if d.startswith("a:"):
            if self.is_admin(uid):
                await admin.on_cb(self, q, d[2:])
            return
        if not await self.gate(uid, chat):
            return
        kb = self.menu_kb(uid)
        name = html.escape(u.get("first_name", ""))
        if d == "chk":
            await self.tg.call("deleteMessage", chat_id=chat, message_id=q["message"]["message_id"])
            await self.start(u, chat)
        elif d == "menu":
            self.db.setstate(uid, None)
            await self.nav(q, self.get_msg("start"), kb, name=name)
        elif d == "menu2":
            await self.start(u, chat)
        elif d in ("new", "new2"):
            kb2 = [[ui.mb("short"), ui.mb("long")], ui.nav_row()]
            m = {"html": "{e:new} <b>Yangi nik</b>\n\nBo'limni tanlang:"}
            await (self.nav(q, m, kb2) if d == "new" else self.send(chat, m, kb2))
        elif d in ("short", "long"):
            await self.ask(uid, chat, d, q)
        elif d == "fonts":
            m, k = self.fonts_msg(1)
            await self.nav(q, m, k)
        elif d.startswith("fp:"):
            m, k = self.fonts_msg(int(d[3:]))
            await self.nav(q, m, k)
        elif d == "guide":
            await self.guides_screen(q)
        elif d.startswith("g:"):
            await self.nav(q, self.get_msg("g" + d[2:]), [[B("Orqaga", "guide", color="blue", slot="back"), ui.nav_row()[0]]])
        elif d == "help":
            await self.nav(q, self.get_msg("help"), [ui.nav_row()])
        elif d == "profile":
            r = self.db.one("SELECT * FROM users WHERE id=?", uid)
            t = (f"{{e:profile}} <b>Profilingiz</b>\n\nID: <code>{uid}</code>\n"
                 f"Qo'shilgan: {time.strftime('%d.%m.%Y', time.gmtime(r['joined']))}\nYasalgan niklar: <b>{r['nicks']}</b>")
            await self.nav(q, {"html": t}, [ui.nav_row()])
        elif d == "cp":
            r = self.db.one("SELECT t FROM lastnick WHERE uid=?", uid)
            for ch in split16(r["t"]) if r else []:
                await self.tg.call("sendMessage", chat_id=chat, text=ch)

    async def on_msg(self, m):
        if m["chat"]["type"] != "private" or "from" not in m:
            return
        u, uid, chat = m["from"], m["from"]["id"], m["chat"]["id"]
        self.db.touch(u)
        text = m.get("text") or ""
        if text.startswith("/"):
            cmd = text.split()[0].split("@")[0].lower()
            if cmd in ("/start", "/menu", "/cancel"):
                if await self.gate(uid, chat):
                    await self.start(u, chat)
                return
            if cmd == "/admin" and self.is_admin(uid):
                self.db.setstate(uid, None)
                msg, kb = await admin.screen(self, ["main"])
                await self.send(chat, msg, kb)
                return
        st, data = self.db.state(uid)
        if st and st.startswith("a:") and self.is_admin(uid):
            return await admin.on_msg(self, m, st)
        if not await self.gate(uid, chat):
            return
        if st == "n:text":
            kind = data["kind"]
            if not text or not 1 <= len(text.strip()) <= self.max_len(kind):
                return await self.send(chat, self.get_msg("err_len"), max=self.max_len(kind))
            self.db.setstate(uid, "n:num", {"kind": kind, "text": text.strip()})
            return await self.send(chat, self.get_msg("ask_num"), [ui.nav_row()])
        if st == "n:num":
            t = text.strip()
            if not (t.isdigit() and 1 <= int(t) <= FONT_N):
                return await self.send(chat, self.get_msg("err_num"))
            return await self.make_nick(uid, chat, data["text"], int(t))
        await self.start(u, chat)

    # ---------- tsikl ----------
    async def safe(self, uid, coro):
        lock = self.locks.setdefault(uid, asyncio.Lock())
        async with lock:
            try:
                await coro
            except Exception:
                log.exception("handler xatosi")

    async def run(self):
        await self.tg.open()
        me = await self.tg.call("getMe")
        log.info("Bot ishga tushdi: @%s", me and me.get("username"))
        await self.tg.call("deleteWebhook")
        offset = None
        while True:
            ups = await self.tg.call("getUpdates", offset=offset, timeout=50, allowed_updates=["message", "callback_query"])
            if ups is None:
                await asyncio.sleep(3)
                continue
            for up in ups:
                offset = up["update_id"] + 1
                if "message" in up:
                    asyncio.create_task(self.safe(up["message"]["chat"]["id"], self.on_msg(up["message"])))
                elif "callback_query" in up:
                    asyncio.create_task(self.safe(up["callback_query"]["from"]["id"], self.on_cb(up["callback_query"])))
