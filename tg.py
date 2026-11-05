"""Telegram Bot API uchun yupqa aiohttp mijoz (button style va premium emoji qo'llab-quvvatlanadi)."""
import asyncio
import json
import logging
import re

import aiohttp

log = logging.getLogger("tg")
TGE = re.compile(r"<tg-emoji[^>]*>.*?</tg-emoji>", re.S)


def _strip_emoji(p):
    """Premium emoji xato bersa, ularsiz qayta urinish uchun. O'zgargan bo'lsa True."""
    changed = False
    rm = p.get("reply_markup")
    if isinstance(rm, dict):
        for row in rm.get("inline_keyboard", []):
            for b in row:
                if b.pop("icon_custom_emoji_id", None):
                    changed = True
    for k in ("text", "caption"):
        if isinstance(p.get(k), str) and "<tg-emoji" in p[k]:
            p[k] = TGE.sub("", p[k])
            changed = True
    return changed


class TG:
    def __init__(self, token):
        self.base = f"https://api.telegram.org/bot{token}/"
        self.s = None

    async def open(self):
        self.s = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=80))

    async def call(self, method, **p):
        p = {k: v for k, v in p.items() if v is not None}
        retried = False
        for _ in range(5):
            data = {k: v if isinstance(v, str) else json.dumps(v, ensure_ascii=False) for k, v in p.items()}
            try:
                async with self.s.post(self.base + method, data=data) as r:
                    j = await r.json(content_type=None)
            except Exception as e:  # tarmoq xatosi
                log.warning("net %s: %s", method, e)
                await asyncio.sleep(3)
                continue
            if j.get("ok"):
                return j["result"]
            code, desc = j.get("error_code"), j.get("description", "")
            if code == 429:
                await asyncio.sleep(j.get("parameters", {}).get("retry_after", 2) + 1)
                continue
            if code == 400 and not retried:
                retried = True
                if _strip_emoji(p):
                    log.warning("%s: %s -> premium emojisiz qayta uriniladi", method, desc)
                    continue
            if "not modified" not in desc:
                log.warning("%s: %s", method, desc)
            return None
        return None

    async def upload(self, method, field, path, **p):
        fd = aiohttp.FormData()
        for k, v in p.items():
            if v is not None:
                fd.add_field(k, v if isinstance(v, str) else json.dumps(v))
        fd.add_field(field, open(path, "rb"), filename=path.split("/")[-1])
        try:
            async with self.s.post(self.base + method, data=fd) as r:
                return (await r.json(content_type=None)).get("result")
        except Exception as e:
            log.warning("upload: %s", e)
