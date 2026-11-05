"""Admin panel: barcha ekranlar va kiritish holatlari."""
import asyncio
import html
import os
import re
import time

from . import ui
from .ui import B

COL = ["blue", "green", "red"]
MEDIA_T = {"photo": "Rasm", "video": "Video", "video_note": "Dumaloq video", "voice": "Ovozli xabar"}
BTN_NAMES = list(ui.MENU)


def label(app, key):
    if re.fullmatch(r"g\d+", key):
        r = app.db.one("SELECT title FROM guides WHERE id=?", int(key[1:]))
        return f"Qo'llanma: {r['title']}" if r else key
    return ui.LABELS.get(key, key)


def back_of(key):
    if key in ("start", "help"):
        return "main"
    return "guides" if re.fullmatch(r"g\d+", key) else "texts"


def bk(to="main"):
    return B("Orqaga", "a:" + to, color="blue", slot="back")


def custom_ids(m):
    return [e["custom_emoji_id"] for e in (m.get("entities") or []) if e.get("type") == "custom_emoji"]


def media_of(m, typ):
    if typ == "photo" and m.get("photo"):
        return m["photo"][-1]["file_id"]
    return (m.get(typ) or {}).get("file_id") if typ != "photo" else None


def back_route(act, p):
    if act in ("mt", "mm"):
        return ["me", p[1]]
    if act == "gren":
        return ["me", "g" + p[1]]
    if act in ("bt", "bem"):
        return ["be", p[1]]
    return {"gadd": ["guides"], "subadd": ["sub"], "es": ["emojis"], "cast": ["main"], "uban": ["users"],
            "uunban": ["users"], "uinfo": ["users"], "maxs": ["set"], "maxl": ["set"], "admadd": ["set"],
            "admdel": ["set"]}.get(act, ["main"])


PROMPTS = {
    "mt": "{e:text} Yangi matnni yuboring.\n<i>Formatlash va premium emojilar saqlanadi.</i>",
    "mm": "{e:media} Endi shu turdagi faylni yuboring.",
    "gadd": "{e:add} Yangi qo'llanma sarlavhasini yuboring.",
    "gren": "{e:edit} Yangi sarlavhani yuboring.",
    "subadd": "{e:channel} Kanal @username yoki ID sini yuboring (bot kanalda admin bo'lishi shart).",
    "bt": "{e:edit} Tugma uchun yangi matn yuboring.",
    "bem": "{e:emoji} Tugma uchun <b>premium emoji</b> yuboring (faqat 1 ta).",
    "es": "{e:emoji} Shu uyaga <b>premium emoji</b> yuboring (1 ta) yoki emoji ID raqamini yozing.",
    "cast": "{e:send} Hammaga yuboriladigan xabarni yuboring (matn, rasm, video — istalgan).",
    "uban": "{e:users} Ban qilinadigan foydalanuvchi ID sini yuboring.",
    "uunban": "{e:users} Bandan chiqariladigan foydalanuvchi ID sini yuboring.",
    "uinfo": "{e:users} Foydalanuvchi ID yoki @username yuboring.",
    "maxs": "{e:settings} Qisqa nik uchun maksimal belgilar sonini yuboring (1–500).",
    "maxl": "{e:settings} Uzun nik uchun maksimal belgilar sonini yuboring (1–5000).",
    "admadd": "{e:add} Yangi admin ID sini yuboring.",
    "admdel": "{e:del} O'chiriladigan admin ID sini yuboring.",
}


async def screen(app, p):
    db, a = app.db, p[0]
    if a == "main":
        r = [("Statistika", "stats", "stats", "blue"), ("Majburiy obuna", "sub", "channel", "green"),
             ("Start matni", "me:start", "text", "red"), ("Yordam matni", "me:help", "help", "blue"),
             ("Qo'llanmalar", "guides", "guide", "green"), ("Tugmalar", "btns", "btn", "red"),
             ("Matnlar", "texts", "edit", "blue"), ("Emoji sozlash", "emojis", "emoji", "green"),
             ("Xabar yuborish", "cast", "send", "red"), ("Foydalanuvchilar", "users", "users", "blue"),
             ("Sozlamalar", "set", "settings", "green"), ("Zaxira (DB)", "backup", "backup", "red")]
        kb = [[B(r[i][0], "a:" + r[i][1], color=r[i][3], slot=r[i][2]),
               B(r[i + 1][0], "a:" + r[i + 1][1], color=r[i + 1][3], slot=r[i + 1][2])] for i in range(0, len(r), 2)]
        kb.append(ui.nav_row())
        return {"html": "{e:admin} <b>Admin panel</b>\n\nBo'limni tanlang:"}, kb
    if a == "stats":
        now = int(time.time())
        c = lambda w, *x: db.one(f"SELECT COUNT(*) n FROM users WHERE {w}", *x)["n"]
        nicks = db.one("SELECT COALESCE(SUM(nicks),0) n FROM users")["n"]
        t = ("{e:stats} <b>Statistika</b>\n\n"
             f"Jami foydalanuvchi: <b>{c('1=1')}</b>\n24 soatda yangi: <b>{c('joined>?', now - 86400)}</b>\n"
             f"7 kunda yangi: <b>{c('joined>?', now - 7 * 86400)}</b>\n24 soatda faol: <b>{c('seen>?', now - 86400)}</b>\n"
             f"Ban qilingan: <b>{c('banned=1')}</b>\nYasalgan niklar: <b>{nicks}</b>\n"
             f"Kanallar: <b>{len(db.kvget('channels', []))}</b>")
        return {"html": t}, [[bk()]]
    if a == "sub":
        chs, on = db.kvget("channels", []), db.kvget("sub_on", True)
        t = "{e:channel} <b>Majburiy obuna</b>\n\nHolat: <b>" + ("yoqilgan" if on else "o'chirilgan") + "</b>\n"
        t += "\n".join(f"{i + 1}. {html.escape(c['title'])} — <code>{c['id']}</code>" for i, c in enumerate(chs)) or "Kanallar yo'q."
        kb = [[B("O'chirish: " + c["title"][:25], f"a:subdel:{i}", color="red", slot="del")] for i, c in enumerate(chs)]
        kb.append([B("Kanal qo'shish", "a:subadd", color="green", slot="add"),
                   B("O'chirish" if on else "Yoqish", "a:subtoggle", color="blue", slot="power")])
        kb.append([bk()])
        return {"html": t}, kb
    if a == "me":
        key = p[1]
        msg = app.get_msg(key)
        txt = msg.get("text") if "text" in msg else msg.get("html", "")
        t = (f"{{e:edit}} <b>{html.escape(label(app, key))}</b>\n\nMatn: <b>{len(txt or '')}</b> belgi\n"
             f"Media: <b>{MEDIA_T.get(msg.get('mt'), 'yo`q')}</b>")
        kb = [[B("Matnni o'zgartirish", f"a:mt:{key}", color="green", slot="text")],
              [B("Rasm", f"a:mm:{key}:photo", color="blue", slot="media"), B("Video", f"a:mm:{key}:video", color="blue", slot="media")],
              [B("Dumaloq video", f"a:mm:{key}:video_note", color="blue", slot="media"),
               B("Ovozli xabar", f"a:mm:{key}:voice", color="blue", slot="media")],
              [B("Medianı o'chirish", f"a:md:{key}", color="red", slot="del"), B("Ko'rish", f"a:mv:{key}", color="green", slot="view")]]
        if key in ui.DEFAULTS:
            kb.append([B("Standart holatga", f"a:mdef:{key}", color="red", slot="back")])
        if re.fullmatch(r"g\d+", key):
            kb.append([B("Sarlavha", f"a:gren:{key[1:]}", color="blue", slot="edit"),
                       B("Qo'llanmani o'chirish", f"a:gdel:{key[1:]}", color="red", slot="del")])
        kb.append([bk(back_of(key))])
        return {"html": t}, kb
    if a == "guides":
        gs = db.all("SELECT id,title FROM guides ORDER BY id")
        kb = [[B(g["title"], f"a:me:g{g['id']}", color=COL[i % 3], slot="guide")] for i, g in enumerate(gs)]
        kb += [[B("Qo'llanma qo'shish", "a:gadd", color="green", slot="add")], [bk()]]
        return {"html": "{e:guide} <b>Qo'llanmalar</b>\n\nTahrirlash uchun tanlang yoki yangisini qo'shing."}, kb
    if a == "gdel":
        return ({"html": "{e:warn} Qo'llanma o'chirilsinmi?"},
                [[B("Ha, o'chirish", f"a:gdelok:{p[1]}", color="red", slot="del"), B("Yo'q", f"a:me:g{p[1]}", color="green", slot="back")]])
    if a == "btns":
        kb = [[B(ui.BTN.get(n, {}).get("t", ui.MENU[n][0]), f"a:be:{n}", color=ui.BTN.get(n, {}).get("c", ui.MENU[n][2]),
                 slot=ui.MENU[n][1])] for n in BTN_NAMES] + [[bk()]]
        return {"html": "{e:btn} <b>Menyu tugmalari</b>\n\nTahrirlash uchun tugmani tanlang:"}, kb
    if a == "be":
        n = p[1]
        o = ui.BTN.get(n, {})
        t = (f"{{e:btn}} <b>Tugma: {html.escape(o.get('t', ui.MENU[n][0]))}</b>\n\nRang: <b>{o.get('c', ui.MENU[n][2])}</b>\n"
             f"Emoji: <b>{'maxsus' if o.get('e') else 'standart'}</b>")
        kb = [[B("Matn", f"a:bt:{n}", color="green", slot="edit"), B("Emoji", f"a:bem:{n}", color="green", slot="emoji")],
              [B("Ko'k", f"a:bcol:{n}:blue", color="blue"), B("Yashil", f"a:bcol:{n}:green", color="green"),
               B("Qizil", f"a:bcol:{n}:red", color="red")],
              [B("Standart", f"a:ber:{n}", color="red", slot="back")], [bk("btns")]]
        return {"html": t}, kb
    if a == "texts":
        kb = [[B(ui.LABELS[k], f"a:me:{k}", color=COL[i % 3], slot="text")] for i, k in enumerate(ui.EDIT_TEXTS)] + [[bk()]]
        return {"html": "{e:edit} <b>Bot matnlari</b>\n\nTahrirlash uchun tanlang:"}, kb
    if a == "emojis":
        sl = list(ui.SLOTS)
        kb = [[B(ui.SLOTS[sl[i]], f"a:es:{sl[i]}", color=COL[i % 3], slot=sl[i])] + (
            [B(ui.SLOTS[sl[i + 1]], f"a:es:{sl[i + 1]}", color=COL[(i + 1) % 3], slot=sl[i + 1])] if i + 1 < len(sl) else [])
            for i in range(0, len(sl), 2)] + [[bk()]]
        return {"html": "{e:emoji} <b>Emoji sozlash</b>\n\nUyani tanlang va o'sha uchun premium emoji yuboring:"}, kb
    if a == "users":
        kb = [[B("Ban", "a:uban", color="red", slot="users"), B("Bandan chiqarish", "a:uunban", color="green", slot="users")],
              [B("Ma'lumot", "a:uinfo", color="blue", slot="view"), B("Oxirgi 10 ta", "a:ulist", color="blue", slot="users")], [bk()]]
        return {"html": "{e:users} <b>Foydalanuvchilar</b>"}, kb
    if a == "ulist":
        rows = app.db.all("SELECT id,name,username FROM users ORDER BY joined DESC LIMIT 10")
        t = "{e:users} <b>Oxirgi foydalanuvchilar</b>\n\n" + "\n".join(
            f"<code>{r['id']}</code> {html.escape(r['name'] or '')} {('@' + r['username']) if r['username'] else ''}" for r in rows)
        return {"html": t}, [[bk("users")]]
    if a == "set":
        t = (f"{{e:settings}} <b>Sozlamalar</b>\n\nBot: <b>{'TEXNIK ISHLAR' if db.kvget('maint', False) else 'ishlayapti'}</b>\n"
             f"Qisqa nik: 1–<b>{app.max_len('short')}</b>\nUzun nik: 1–<b>{app.max_len('long')}</b>\n"
             f"Qo'shimcha adminlar: <b>{len(db.kvget('admins', []))}</b>")
        kb = [[B("Texnik ishlar", "a:power", color="red", slot="power")],
              [B("Qisqa nik limiti", "a:maxs", color="blue", slot="edit"), B("Uzun nik limiti", "a:maxl", color="blue", slot="edit")],
              [B("Admin qo'shish", "a:admadd", color="green", slot="add"), B("Admin o'chirish", "a:admdel", color="red", slot="del")],
              [bk()]]
        return {"html": t}, kb
    return await screen(app, ["main"])


async def on_cb(app, q, route):
    uid, chat = q["from"]["id"], q["message"]["chat"]["id"]
    db, p = app.db, route.split(":")
    a = p[0]
    db.setstate(uid, None)
    fresh = False
    if a == "subtoggle":
        db.kvset("sub_on", not db.kvget("sub_on", True)); p = ["sub"]
    elif a == "subdel":
        ch = db.kvget("channels", [])
        if int(p[1]) < len(ch):
            ch.pop(int(p[1])); db.kvset("channels", ch)
        p = ["sub"]
    elif a == "gdelok":
        db.x("DELETE FROM guides WHERE id=?", int(p[1])); db.kvdel("msg:g" + p[1]); p = ["guides"]
    elif a == "md":
        m = app.get_msg(p[1]); m.pop("mt", None); m.pop("mf", None); app.save_msg(p[1], m); p = ["me", p[1]]
    elif a == "mdef":
        db.kvdel("msg:" + p[1]); p = ["me", p[1]]
    elif a == "mv":
        await app.send(chat, app.get_msg(p[1]), name="Foydalanuvchi", max=40, n=1); p = ["me", p[1]]; fresh = True
    elif a in ("bcol", "ber", "bem_reset"):
        o = ui.BTN.setdefault(p[1], {})
        if a == "bcol":
            o["c"] = p[2]
        else:
            ui.BTN.pop(p[1], None)
        db.kvset("btn", ui.BTN); p = ["be", p[1]]
    elif a == "power":
        db.kvset("maint", not db.kvget("maint", False)); p = ["set"]
    elif a == "backup":
        os.makedirs("work", exist_ok=True)
        db.snapshot("work/backup.db")
        await app.tg.upload("sendDocument", "document", "work/backup.db", chat_id=chat, caption="DB zaxira nusxasi")
        return
    elif a in PROMPTS:
        if a in ("admadd", "admdel") and uid != app.admin_id:
            return
        db.setstate(uid, "a:" + route)
        back = "a:" + ":".join(back_route(a, p))
        kb = [[B("Bekor qilish", back, color="red", slot="back")]]
        txt = PROMPTS[a]
        if a == "mm":
            txt = f"{{e:media}} <b>{MEDIA_T[p[2]]}</b> yuboring."
        return await app.nav(q, {"html": txt}, kb)
    msg, kb = await screen(app, p)
    if fresh:
        await app.send(chat, msg, kb)
    else:
        await app.nav(q, msg, kb)


async def broadcast(app, chat, ids, mid):
    ok = 0
    for i in ids:
        if await app.tg.call("copyMessage", chat_id=i, from_chat_id=chat, message_id=mid):
            ok += 1
        await asyncio.sleep(0.05)
    await app.say(chat, f"{{e:ok}} Yuborildi: <b>{ok}</b> / {len(ids)}")


async def on_msg(app, m, state):
    uid, chat = m["from"]["id"], m["chat"]["id"]
    db, route = app.db, state[2:]
    p = route.split(":")
    a = p[0]
    text = (m.get("text") or "").strip()
    bad = lambda: app.say(chat, "{e:warn} Noto'g'ri format. Qayta yuboring yoki /cancel.")
    if a == "mt":
        if "text" not in m:
            return await bad()
        msg = app.get_msg(p[1]); msg.pop("html", None)
        msg["text"], msg["entities"] = m["text"], m.get("entities") or []
        app.save_msg(p[1], msg)
    elif a == "mm":
        fid = media_of(m, p[2])
        if not fid:
            return await bad()
        msg = app.get_msg(p[1]); msg["mt"], msg["mf"] = p[2], fid
        app.save_msg(p[1], msg)
    elif a == "gadd":
        if not text:
            return await bad()
        cur = db.x("INSERT INTO guides(title) VALUES(?)", text[:60])
        p = ["gadd", str(cur.lastrowid)]
        app.save_msg("g" + p[1], {"text": "Qo'llanma matnini tahrirlang."})
    elif a == "gren":
        if not text:
            return await bad()
        db.x("UPDATE guides SET title=? WHERE id=?", text[:60], int(p[1]))
    elif a == "subadd":
        ref = text if text.lstrip("-").isdigit() else ("@" + text.lstrip("@/").split("/")[-1])
        chat_info = await app.tg.call("getChat", chat_id=int(ref) if ref.lstrip("-").isdigit() else ref)
        if not chat_info:
            return await app.say(chat, "{e:warn} Kanal topilmadi yoki bot u yerda emas.")
        link = chat_info.get("invite_link") or (f"https://t.me/{chat_info['username']}" if chat_info.get("username") else None)
        if not link:
            link = await app.tg.call("exportChatInviteLink", chat_id=chat_info["id"])
        if not link:
            return await app.say(chat, "{e:warn} Havola olinmadi. Botni kanalga admin qiling.")
        chs = db.kvget("channels", [])
        chs.append({"id": chat_info["id"], "title": chat_info.get("title", "Kanal"), "link": link})
        db.kvset("channels", chs)
    elif a == "bt":
        if not text:
            return await bad()
        ui.BTN.setdefault(p[1], {})["t"] = text[:30]; db.kvset("btn", ui.BTN)
    elif a == "bem":
        ids = custom_ids(m)
        if not ids:
            return await app.say(chat, "{e:warn} Premium emoji yuborilmadi. Qayta urinib ko'ring.")
        ui.BTN.setdefault(p[1], {})["e"] = ids[0]; db.kvset("btn", ui.BTN)
    elif a == "es":
        ids = custom_ids(m) or ([text] if text.isdigit() else [])
        if not ids:
            return await app.say(chat, "{e:warn} Premium emoji yuborilmadi. Qayta urinib ko'ring.")
        ui.EMO[p[1]] = ids[0]
        db.kvset("emoji", {k: v for k, v in ui.EMO.items() if v != ui.DEFAULT_EID})
    elif a == "cast":
        ids = [r["id"] for r in db.all("SELECT id FROM users WHERE banned=0")]
        db.setstate(uid, None)
        asyncio.create_task(broadcast(app, chat, ids, m["message_id"]))
        return await app.say(chat, f"{{e:send}} Yuborish boshlandi: <b>{len(ids)}</b> ta foydalanuvchi.")
    elif a in ("uban", "uunban"):
        if not text.isdigit():
            return await bad()
        db.x("UPDATE users SET banned=? WHERE id=?", 1 if a == "uban" else 0, int(text))
    elif a == "uinfo":
        r = db.one("SELECT * FROM users WHERE id=?", int(text)) if text.isdigit() else db.one(
            "SELECT * FROM users WHERE username=?", text.lstrip("@"))
        if not r:
            return await app.say(chat, "{e:warn} Topilmadi.")
        db.setstate(uid, None)
        return await app.say(chat, f"{{e:users}} <b>{html.escape(r['name'] or '')}</b>\nID: <code>{r['id']}</code>\n"
                             f"Username: @{r['username']}\nNiklar: {r['nicks']}\nBan: {'ha' if r['banned'] else 'yo`q'}",
                             [[bk("users")]])
    elif a in ("maxs", "maxl"):
        lim = 500 if a == "maxs" else 5000
        if not (text.isdigit() and 1 <= int(text) <= lim):
            return await bad()
        db.kvset("max_" + ("short" if a == "maxs" else "long"), int(text))
    elif a in ("admadd", "admdel"):
        if not text.isdigit() or uid != app.admin_id:
            return await bad()
        ad = db.kvget("admins", [])
        if a == "admadd" and int(text) not in ad:
            ad.append(int(text))
        if a == "admdel" and int(text) in ad:
            ad.remove(int(text))
        db.kvset("admins", ad)
    db.setstate(uid, None)
    await app.say(chat, "{e:ok} Saqlandi.")
    back = ["me", "g" + p[1]] if a == "gadd" else back_route(a, p)
    msg, kb = await screen(app, back)
    await app.send(chat, msg, kb)
