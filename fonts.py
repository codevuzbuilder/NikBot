"""800 xil shrift generatori (Unicode asosida). apply(matn, raqam) -> tayyor nik."""
import string
import unicodedata as ud

UP, LO, DG = string.ascii_uppercase, string.ascii_lowercase, "0123456789"
_DN = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
FONT_COUNT = 800


def _look(*names):
    for n in names:
        try:
            return ud.lookup(n)
        except KeyError:
            pass
    return None


def _math(style, dstyle=None):
    m, alt = {}, style.replace("FRAKTUR", "BLACK-LETTER")
    for c in UP:
        r = _look(f"MATHEMATICAL {style} CAPITAL {c}", f"{alt} CAPITAL {c}")
        if r:
            m[c] = r
    for c in LO:
        r = _look(f"MATHEMATICAL {style} SMALL {c.upper()}", f"{alt} SMALL {c.upper()}")
        if r:
            m[c] = r
    if style == "ITALIC":
        m["h"] = "\u210e"
    if dstyle:
        for d, n in zip(DG, _DN):
            r = _look(f"MATHEMATICAL {dstyle} DIGIT {n}")
            if r:
                m[d] = r
    return m


def _tbl(up=None, lo=None, dg=None):
    m = {}
    if up:
        m.update(zip(UP, up))
    if lo:
        m.update(zip(LO, lo))
    if dg:
        m.update(zip(DG, dg))
    return m


def _off(u, l, d=None):
    return _tbl([chr(u + i) for i in range(26)] if u else None,
                [chr(l + i) for i in range(26)] if l else None,
                [chr(d + i) for i in range(10)] if d else None)


def _mix(u, l):
    m = {c: u[c] for c in UP if c in u}
    m.update({c: l[c] for c in LO if c in l})
    m.update({c: u[c] for c in DG if c in u})
    return m


def _caps(m):
    r = dict(m)
    for a, b in zip(LO, UP):
        if b in m:
            r[a] = m[b]
    return r


_STYLES = [("BOLD", "BOLD"), ("ITALIC", None), ("BOLD ITALIC", None), ("SCRIPT", None),
           ("BOLD SCRIPT", None), ("FRAKTUR", None), ("DOUBLE-STRUCK", "DOUBLE-STRUCK"),
           ("BOLD FRAKTUR", None), ("SANS-SERIF", "SANS-SERIF"), ("SANS-SERIF BOLD", "SANS-SERIF BOLD"),
           ("SANS-SERIF ITALIC", None), ("SANS-SERIF BOLD ITALIC", None), ("MONOSPACE", "MONOSPACE")]
M = {s: _math(s, d) for s, d in _STYLES}

FULL = {**{c: chr(ord(c) + 0xFEE0) for c in UP + LO + DG}}
CIRC = _tbl([chr(0x24B6 + i) for i in range(26)], [chr(0x24D0 + i) for i in range(26)], "⓪①②③④⑤⑥⑦⑧⑨")
NCIRC = _tbl([chr(0x1F150 + i) for i in range(26)], [chr(0x1F150 + i) for i in range(26)], "⓿❶❷❸❹❺❻❼❽❾")
SQ = _tbl([chr(0x1F130 + i) for i in range(26)], [chr(0x1F130 + i) for i in range(26)])
PAR = _tbl([chr(0x1F110 + i) for i in range(26)], [chr(0x249C + i) for i in range(26)], "0⑴⑵⑶⑷⑸⑹⑺⑻⑼")
SC = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
SMALLCAP = _tbl(SC, SC)
SMALLCAP_L = _tbl(None, SC)
SUP = _tbl("ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻ", "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻ", "⁰¹²³⁴⁵⁶⁷⁸⁹")
FLIP = _tbl("∀qƆpƎℲפHIſʞ˥WNOԀQɹS┴∩ΛMX⅄Z", "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz")
CAN = _tbl("ᗩᗷᑕᗪᗴᖴᘜᕼIᒍKᒪᗰᑎOᑭᑫᖇՏTᑌᐯᗯ᙭Yᘔ", "ᗩᗷᑕᗪᗴᖴᘜᕼIᒍKᒪᗰᑎOᑭᑫᖇՏTᑌᐯᗯ᙭Yᘔ")
CJK = _tbl("卂乃匚刀乇下厶卄工丁长乚从ん口尸㔿尺丂丅凵リ山乂丫乙", "卂乃匚刀乇下厶卄工丁长乚从ん口尸㔿尺丂丅凵リ山乂丫乙")
GRC = _tbl("αв¢∂єƒgнιנкℓмησρqяѕтυνωxуz", "αв¢∂єƒgнιנкℓмησρqяѕтυνωxуz")
HOOK = _tbl("ɑɓƈɗɛʄɠɦɨʝƙɭɱɲɔƥʠɾʂƭʊʋʍxƴʐ".upper(), "ɑɓƈɗɛʄɠɦɨʝƙɭɱɲɔƥʠɾʂƭʊʋʍxƴʐ")

# (xarita, teskari_yozish)
_B = [(m, False) for m in M.values()]
_B += [(FULL, False), (CIRC, False), (NCIRC, False), (SQ, False), (PAR, False), (SMALLCAP, False),
       (SMALLCAP_L, False), (SUP, False), (FLIP, True), (CAN, False), (CJK, False), (GRC, False), (HOOK, False)]
_B += [(_mix(M["BOLD"], SMALLCAP), False), (_mix(M["SCRIPT"], {}), False),
       (_mix(M["FRAKTUR"], SMALLCAP), False), (_mix(M["DOUBLE-STRUCK"], {}), False),
       (_mix(M["BOLD ITALIC"], M["ITALIC"]), False), (_mix(M["BOLD SCRIPT"], SMALLCAP), False),
       (_mix(M["SANS-SERIF BOLD"], SMALLCAP), False), (_mix(CIRC, {}), False),
       (_mix(M["MONOSPACE"], SMALLCAP), False), (_mix(M["BOLD FRAKTUR"], M["ITALIC"]), False),
       (_mix(FULL, SMALLCAP), False), (_mix(CAN, SMALLCAP), False)]
_B += [(_caps(M[s]), False) for s in ("BOLD", "FRAKTUR", "SCRIPT", "DOUBLE-STRUCK", "MONOSPACE",
                                      "SANS-SERIF BOLD", "BOLD SCRIPT", "BOLD FRAKTUR")]
_B += [({}, True)]  # oddiy teskari yozuv
NB = len(_B)

MARKS = ["\u0336", "\u0332", "\u0333", "\u0338", "\u0305", "\u0323"]
WRAPS = [("꧁", "꧂"), ("༺", "༻"), ("『", "』"), ("【", "】"), ("「", "」"), ("《", "》"), ("✦ ", " ✦"),
         ("⋆ ", " ⋆"), ("✧ ", " ✧"), ("♡ ", " ♡"), ("ღ ", " ღ"), ("彡 ", " 彡"), ("◥ ", " ◤"),
         ("▓ ", " ▓"), ("★ ", " ★"), ("• ", " •")]
DECOS = [None] + [("m", x) for x in MARKS] + [("w", w) for w in WRAPS]
assert NB * len(DECOS) >= FONT_COUNT


def apply(text: str, num: int) -> str:
    i = (num - 1) % FONT_COUNT
    m, rev = _B[i % NB]
    d = DECOS[i // NB]
    s = "".join(m.get(c, c) for c in text)
    if rev:
        s = s[::-1]
    if d:
        kind, v = d
        if kind == "m":
            s = "".join(c if c.isspace() else c + v for c in s)
        else:
            s = v[0] + s + v[1]
    return s
