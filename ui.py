"""Matnlar, tugmalar, premium emoji yordamchilari."""
import re

FALLBACK = "\u2b50"  # Telegram custom emoji ostida majburiy "o'rin to'ldiruvchi"; foydalanuvchiga premium emoji ko'rinadi
DEFAULT_EID = "5368324170671202286"  # vaqtincha; admin panel -> Emoji sozlash orqali o'zgartiring

SLOTS = {
    "short": "Qisqa nik", "long": "Uzun nik", "fonts": "Shriftlar", "guide": "Qo'llanma", "help": "Yordam",
    "profile": "Profil", "admin": "Admin panel", "copy": "Nusxa olish", "new": "Yangi nik", "menu": "Menyu",
    "back": "Orqaga", "ok": "Muvaffaqiyat", "warn": "Ogohlantirish", "bot": "Bot (salom)", "stats": "Statistika",
    "channel": "Kanal/obuna", "text": "Matn tahrirlash", "media": "Media", "btn": "Tugmalar", "send": "Xabar yuborish",
    "emoji": "Emoji sozlash", "users": "Foydalanuvchilar", "power": "Yoqish/o'chirish", "backup": "Zaxira",
    "add": "Qo'shish", "del": "O'chirish", "edit": "Tahrirlash", "view": "Ko'rish", "next": "Keyingi",
    "prev": "Oldingi", "settings": "Sozlamalar", "check": "Tekshirish",
}
EMO = {}
BTN = {}

MENU = {  # nom: (matn, emoji uyasi, rang)
    "short": ("Qisqa nik", "short", "blue"), "long": ("Uzun nik", "long", "green"),
    "fonts": ("Shriftlar", "fonts", "red"), "guide": ("Qo'llanma", "guide", "blue"),
    "help": ("Yordam", "help", "green"), "profile": ("Profilim", "profile", "red"),
    "admin": ("Admin panel", "admin", "red"),
}
STYLES = {"blue": "primary", "green": "success", "red": "danger"}

DEFAULTS = {
    "start": "{e:bot} <b>Salom, {name}!</b>\n\nBu bot orqali chiroyli nik (ism) yasashingiz mumkin. 800 xil shrift mavjud.\n\nBo'limni tanlang:",
    "help": "{e:help} <b>Yordam</b>\n\nSavollar bo'lsa adminga murojaat qiling.",
    "ask_short": "{e:short} <b>Qisqa nik</b>\n\nNik uchun matn yuboring (1–{max} ta belgi).",
    "ask_long": "{e:long} <b>Uzun nik</b>\n\nNik uchun matn yuboring (1–{max} ta belgi).",
    "ask_num": "{e:fonts} Endi shrift raqamini yuboring (1–800).\n\nNamunalarni «Shriftlar» bo'limida ko'rishingiz mumkin.",
    "err_len": "{e:warn} Matn uzunligi 1 dan {max} gacha bo'lishi kerak. Qayta yuboring.",
    "err_num": "{e:warn} 1 dan 800 gacha son yuboring.",
    "ready": "{e:ok} <b>Nik tayyor!</b> (shrift № {n})",
    "sub_need": "{e:warn} <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>",
    "banned": "{e:warn} Siz botdan foydalanishdan chetlatilgansiz.",
    "maint": "{e:warn} Bot vaqtincha ishlamayapti. Keyinroq urinib ko'ring.",
    "guides_title": "{e:guide} <b>Qo'llanmalar</b>\n\nKerakli bo'limni tanlang:",
    "no_guides": "{e:guide} Hozircha qo'llanmalar yo'q.",
}
LABELS = {
    "start": "Start matni", "help": "Yordam matni", "ask_short": "Qisqa nik so'rovi", "ask_long": "Uzun nik so'rovi",
    "ask_num": "Raqam so'rovi", "err_len": "Uzunlik xatosi", "err_num": "Raqam xatosi", "ready": "Nik tayyor sarlavhasi",
    "sub_need": "Obuna talabi", "banned": "Ban xabari", "maint": "Texnik ishlar xabari",
    "guides_title": "Qo'llanmalar sarlavhasi", "no_guides": "Qo'llanma yo'q xabari",
}
EDIT_TEXTS = [k for k in DEFAULTS if k not in ("start", "help")]


def load(db):
    EMO.clear()
    EMO.update({s: DEFAULT_EID for s in SLOTS})
    EMO.update(db.kvget("emoji", {}))
    BTN.clear()
    BTN.update(db.kvget("btn", {}))


def E(slot):
    eid = EMO.get(slot)
    return f'<tg-emoji emoji-id="{eid}">{FALLBACK}</tg-emoji>' if eid else ""


def render(t, **kw):
    t = re.sub(r"\{e:(\w+)\}", lambda m: E(m.group(1)), t)
    for k, v in kw.items():
        t = t.replace("{" + k + "}", str(v))
    return t


def B(text, cb=None, *, color=None, slot=None, url=None, copy=None):
    b = {"text": text}
    if cb:
        b["callback_data"] = cb
    if url:
        b["url"] = url
    if copy:
        b["copy_text"] = {"text": copy}
    if STYLES.get(color):
        b["style"] = STYLES[color]
    if slot and EMO.get(slot):
        b["icon_custom_emoji_id"] = EMO[slot]
    return b


def mb(name):
    t, slot, col = MENU[name]
    o = BTN.get(name, {})
    b = B(o.get("t", t), name, color=o.get("c", col), slot=slot)
    if o.get("e"):
        b["icon_custom_emoji_id"] = o["e"]
    return b


def nav_row():
    return [B("Menyu", "menu", color="blue", slot="menu")]
