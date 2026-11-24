#!/usr/bin/env python3
"""news-image-20261124: one-page newspaper front page for Tuesday 24 Nov 2026.

Python 3.13, standard library only. Draws everything in code (own framebuffer
rasterizer, own hand-typed bitmap fonts, own PNG encoder), writes
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png). Deterministic: no clock,
no randomness, no network. 1024x1024, under 1 MiB.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER   = (250, 246, 236)   # warm newsprint
INK     = (22, 22, 30)      # near-black
NAVY    = (16, 32, 66)      # masthead bars
RED     = (178, 34, 34)     # brick red
DRED    = (140, 20, 20)
GREY    = (110, 110, 112)
LGREY   = (210, 206, 196)
WHITE   = (255, 255, 255)
SKY     = (168, 205, 232)
SKY2    = (120, 175, 215)
SEA     = (52, 110, 165)
SAND    = (232, 214, 170)
GRASS   = (96, 150, 80)
DARK    = (28, 34, 48)
GOLD    = (212, 160, 40)
TEAL    = (16, 110, 105)
ORANGE  = (224, 122, 40)
PURPLE  = (96, 64, 140)
GREEN   = (34, 120, 60)
BROWN   = (120, 84, 52)
PINK    = (220, 130, 150)
LBLUE   = (190, 220, 240)

# ---------------------------------------------------------------- framebuffer
fb = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i], fb[i + 1], fb[i + 2] = c


def rect(x, y, w, h, c):
    x0 = max(0, x); y0 = max(0, y)
    x1 = min(W, x + w); y1 = min(H, y + h)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        for xx in range(x0, x1):
            fb[i], fb[i + 1], fb[i + 2] = c
            i += 3


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                px(xx, yy, c)


def disc(cx, cy, r, c):
    circle(cx, cy, r, c)


def ring(cx, cy, r, c, t=2):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if (r - t) ** 2 <= d <= r * r:
                px(xx, yy, c)


def line(x0, y0, x1, y1, c, t=1):
    dx = x1 - x0; dy = y1 - y0
    steps = max(abs(dx), abs(dy), 1)
    for s in range(steps + 1):
        x = x0 + dx * s // steps
        y = y0 + dy * s // steps
        rect(x - t // 2, y - t // 2, t, t, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    minx = min(x0, x1, x2); maxx = max(x0, x1, x2)
    miny = min(y0, y1, y2); maxy = max(y0, y1, y2)
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
            b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
            cc = 1 - a - b
            if a >= 0 and b >= 0 and cc >= 0:
                px(xx, yy, c)


def ellipse(cx, cy, rx, ry, c):
    for yy in range(cy - ry, cy + ry + 1):
        for xx in range(cx - rx, cx + rx + 1):
            if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                px(xx, yy, c)


# ---------------------------------------------------------------- 5x7 font
# Hand-typed bitmap font. Each glyph: 7 rows of 5 chars, '#' = on.
F = {}


def _g(ch, rows):
    F[ch] = rows


_g('A', ("01110", "10001", "10001", "11111", "10001", "10001", "10001"))
_g('B', ("11110", "10001", "10001", "11110", "10001", "10001", "11110"))
_g('C', ("01110", "10001", "10000", "10000", "10000", "10001", "01110"))
_g('D', ("11110", "10001", "10001", "10001", "10001", "10001", "11110"))
_g('E', ("11111", "10000", "10000", "11110", "10000", "10000", "11111"))
_g('F', ("11111", "10000", "10000", "11110", "10000", "10000", "10000"))
_g('G', ("01110", "10001", "10000", "10111", "10001", "10001", "01111"))
_g('H', ("10001", "10001", "10001", "11111", "10001", "10001", "10001"))
_g('I', ("01110", "00100", "00100", "00100", "00100", "00100", "01110"))
_g('J', ("00111", "00010", "00010", "00010", "00010", "10010", "01100"))
_g('K', ("10001", "10010", "10100", "11000", "10100", "10010", "10001"))
_g('L', ("10000", "10000", "10000", "10000", "10000", "10000", "11111"))
_g('M', ("10001", "11011", "10101", "10101", "10001", "10001", "10001"))
_g('N', ("10001", "11001", "10101", "10011", "10001", "10001", "10001"))
_g('O', ("01110", "10001", "10001", "10001", "10001", "10001", "01110"))
_g('P', ("11110", "10001", "10001", "11110", "10000", "10000", "10000"))
_g('Q', ("01110", "10001", "10001", "10001", "10101", "10010", "01101"))
_g('R', ("11110", "10001", "10001", "11110", "10100", "10010", "10001"))
_g('S', ("01111", "10000", "10000", "01110", "00001", "00001", "11110"))
_g('T', ("11111", "00100", "00100", "00100", "00100", "00100", "00100"))
_g('U', ("10001", "10001", "10001", "10001", "10001", "10001", "01110"))
_g('V', ("10001", "10001", "10001", "10001", "10001", "01010", "00100"))
_g('W', ("10001", "10001", "10001", "10101", "10101", "11011", "10001"))
_g('X', ("10001", "10001", "01010", "00100", "01010", "10001", "10001"))
_g('Y', ("10001", "10001", "01010", "00100", "00100", "00100", "00100"))
_g('Z', ("11111", "00001", "00010", "00100", "01000", "10000", "11111"))
_g('a', ("00000", "00000", "01110", "00001", "01111", "10001", "01111"))
_g('b', ("10000", "10000", "10110", "11001", "10001", "10001", "11110"))
_g('c', ("00000", "00000", "01110", "10000", "10000", "10001", "01110"))
_g('d', ("00001", "00001", "01101", "10011", "10001", "10001", "01111"))
_g('e', ("00000", "00000", "01110", "10001", "11111", "10000", "01110"))
_g('f', ("00110", "01001", "01000", "11110", "01000", "01000", "01000"))
_g('g', ("00000", "01111", "10001", "10001", "01111", "00001", "01110"))
_g('h', ("10000", "10000", "10110", "11001", "10001", "10001", "10001"))
_g('i', ("00100", "00000", "01100", "00100", "00100", "00100", "01110"))
_g('j', ("00010", "00000", "00110", "00010", "00010", "00010", "10010"))
_g('k', ("10000", "10000", "10010", "10100", "11000", "10100", "10010"))
_g('l', ("01100", "00100", "00100", "00100", "00100", "00100", "01110"))
_g('m', ("00000", "00000", "11010", "10101", "10101", "10101", "10101"))
_g('n', ("00000", "00000", "10110", "11001", "10001", "10001", "10001"))
_g('o', ("00000", "00000", "01110", "10001", "10001", "10001", "01110"))
_g('p', ("00000", "00000", "11110", "10001", "11110", "10000", "10000"))
_g('q', ("00000", "00000", "01101", "10011", "01111", "00001", "00001"))
_g('r', ("00000", "00000", "10110", "11001", "10000", "10000", "10000"))
_g('s', ("00000", "00000", "01111", "10000", "01110", "00001", "11110"))
_g('t', ("01000", "01000", "11110", "01000", "01000", "01001", "00110"))
_g('u', ("00000", "00000", "10001", "10001", "10001", "10011", "01101"))
_g('v', ("00000", "00000", "10001", "10001", "10001", "01010", "00100"))
_g('w', ("00000", "00000", "10001", "10101", "10101", "10101", "01010"))
_g('x', ("00000", "00000", "10001", "01010", "00100", "01010", "10001"))
_g('y', ("00000", "00000", "10001", "10001", "01111", "00001", "01110"))
_g('z', ("00000", "00000", "11111", "00010", "00100", "01000", "11111"))
_g('0', ("01110", "10001", "10011", "10101", "11001", "10001", "01110"))
_g('1', ("00100", "01100", "00100", "00100", "00100", "00100", "01110"))
_g('2', ("01110", "10001", "00001", "00110", "01000", "10000", "11111"))
_g('3', ("11111", "00010", "00100", "00010", "00001", "10001", "01110"))
_g('4', ("00010", "00110", "01010", "10010", "11111", "00010", "00010"))
_g('5', ("11111", "10000", "11110", "00001", "00001", "10001", "01110"))
_g('6', ("00110", "01000", "10000", "11110", "10001", "10001", "01110"))
_g('7', ("11111", "00001", "00010", "00100", "01000", "01000", "01000"))
_g('8', ("01110", "10001", "10001", "01110", "10001", "10001", "01110"))
_g('9', ("01110", "10001", "10001", "01111", "00001", "00010", "01100"))
_g(' ', ("00000", "00000", "00000", "00000", "00000", "00000", "00000"))
_g('.', ("00000", "00000", "00000", "00000", "00000", "01100", "01100"))
_g(',', ("00000", "00000", "00000", "00000", "01100", "00100", "01000"))
_g(':', ("00000", "01100", "01100", "00000", "01100", "01100", "00000"))
_g(';', ("00000", "01100", "01100", "00000", "01100", "00100", "01000"))
_g('!', ("00100", "00100", "00100", "00100", "00100", "00000", "00100"))
_g('?', ("01110", "10001", "00001", "00110", "00100", "00000", "00100"))
_g("'", ("00100", "00100", "01000", "00000", "00000", "00000", "00000"))
_g('"', ("01010", "01010", "00000", "00000", "00000", "00000", "00000"))
_g('-', ("00000", "00000", "00000", "01110", "00000", "00000", "00000"))
_g('\u2013', ("00000", "00000", "00000", "01110", "00000", "00000", "00000"))
_g('\u2014', ("00000", "00000", "00000", "11111", "00000", "00000", "00000"))
_g('(', ("00010", "00100", "01000", "01000", "01000", "00100", "00010"))
_g(')', ("01000", "00100", "00010", "00010", "00010", "00100", "01000"))
_g('/', ("00001", "00010", "00010", "00100", "01000", "01000", "10000"))
_g('%', ("11001", "11010", "00010", "00100", "01000", "01011", "10011"))
_g('$', ("00100", "01111", "10100", "01110", "00101", "11110", "00100"))
_g('&', ("01100", "10010", "10100", "01000", "10101", "10010", "01101"))
_g('+', ("00000", "00100", "00100", "11111", "00100", "00100", "00000"))
_g('=', ("00000", "00000", "11111", "00000", "11111", "00000", "00000"))
_g('\u00d7', ("00000", "10001", "01010", "00100", "01010", "10001", "00000"))
_g('\u00b7', ("00000", "00000", "00000", "00000", "01100", "01100", "00000"))
_g('\u2022', ("00000", "01100", "11110", "11110", "11110", "01100", "00000"))
_g('#', ("01010", "01010", "11111", "01010", "11111", "01010", "01010"))
_g('@', ("01110", "10001", "10111", "10101", "10110", "10000", "01110"))
_g('_', ("00000", "00000", "00000", "00000", "00000", "00000", "11111"))
_g('*', ("00000", "00100", "10101", "01110", "10101", "00100", "00000"))
_g('<', ("00010", "00100", "01000", "10000", "01000", "00100", "00010"))
_g('>', ("01000", "00100", "00010", "00001", "00010", "00100", "01000"))
_g('[', ("01110", "01000", "01000", "01000", "01000", "01000", "01110"))
_g(']', ("01110", "00010", "00010", "00010", "00010", "00010", "01110"))
_g('\u2192', ("00000", "00100", "00010", "11111", "00010", "00100", "00000"))
_g('\u2191', ("00100", "01110", "10101", "00100", "00100", "00100", "00100"))
_g('~', ("00000", "00000", "01001", "10110", "00000", "00000", "00000"))
_g('\u00b0', ("01100", "10010", "10010", "01100", "00000", "00000", "00000"))
_g('\u2019', ("00100", "00100", "01000", "00000", "00000", "00000", "00000"))
_g('\u201c', ("01010", "01010", "00100", "00000", "00000", "00000", "00000"))
_g('\u201d', ("01010", "01010", "00100", "00000", "00000", "00000", "00000"))
_g('\u00e9', ("00010", "00100", "00000", "01110", "10001", "11111", "01110"))
_g('\u00e8', ("00100", "00010", "00000", "01110", "10001", "11111", "01110"))
_g('\u00fc', ("01010", "00000", "10001", "10001", "10001", "10011", "01101"))
_g('\u00f6', ("01010", "00000", "01110", "10001", "10001", "10001", "01110"))
_g('\u00e4', ("01010", "00000", "01110", "00001", "01111", "10001", "01111"))
_g('\u00df', ("01110", "10001", "10001", "01110", "10001", "10001", "10001"))


def text_w(s, sc=1):
    """Pixel width of a string at scale sc (6px advance per glyph)."""
    return len(s) * 6 * sc


def draw_text(x, y, s, c, sc=1):
    """Draw string s with its top-left at (x, y). Returns width used."""
    cx = x
    for ch in s:
        g = F.get(ch)
        if g is None:
            cx += 6 * sc
            continue
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == '1':
                    rect(cx + cc * sc, y + r * sc, sc, sc, c)
        cx += 6 * sc
    return cx - x


def draw_text_center(x, y, w, s, c, sc=1):
    tw = text_w(s, sc)
    draw_text(x + (w - tw) // 2, y, s, c, sc)


def wrap(s, maxch):
    """Greedy word wrap to a list of lines, each <= maxch chars."""
    lines, cur = [], ""
    for word in s.split(" "):
        if cur and len(cur) + 1 + len(word) > maxch:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word) if cur else word
    if cur:
        lines.append(cur)
    return lines


def para(x, y, w, s, c, sc=1, lh=None, max_lines=None):
    """Draw wrapped paragraph; returns y after last line."""
    if lh is None:
        lh = 8 * sc + 1
    maxch = max(1, w // (6 * sc))
    lines = wrap(s, maxch)
    if max_lines is not None:
        lines = lines[:max_lines]
    for ln in lines:
        draw_text(x, y, ln, c, sc)
        y += lh
    return y


# ---------------------------------------------------------------- PNG encoder
def png_bytes(rgb, w, h):
    raw = bytearray()
    stride = w * 3
    for yy in range(h):
        raw.append(0)
        raw += rgb[yy * stride:(yy + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", comp)
    out += chunk(b"IEND", b"")
    return out

# ---------------------------------------------------------------- serif masthead font
# Hand-drawn condensed serif capitals/lowercase, 8 wide x 16 tall.
# Only the glyphs needed for "Tuesday 24 November 2026".
MAST = {
'T': ("########", "########", "...##...", "...##...", "...##...", "...##...",
      "...##...", "...##...", "...##...", "...##...", "...##...", "...##...",
      "...##...", "...##...", "..######", "..######"),
'u': ("........", "........", "........", "........", "........", "........",
      ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.",
      ".##..##.", ".##..##.", ".###.##.", "..#####.."),
'e': ("........", "........", "........", "........", "........", "........",
      "..#####..", ".##...##.", ".##...##.", ".#######.", ".#######.", ".##......",
      ".##......", ".##...##.", ".##...##.", "..#####.."),
's': ("........", "........", "........", "........", "........", "........",
      "..#####..", ".##...##.", ".##......", ".##......", "..#####..", ".....##..",
      ".....##..", ".##...##.", ".##...##.", "..#####.."),
'd': (".....##.", ".....##.", ".....##.", ".....##.", ".....##.", ".....##.",
      "..####...", ".##..##..", ".##..##..", ".##..##..", ".##..##..", ".##..##..",
      ".##..##..", ".##..##..", ".##..##..", "..####..."),
'a': ("........", "........", "........", "........", "........", "........",
      "..#####..", "......##.", "..######.", ".##...##.", ".##...##.", ".##...##.",
      ".##...##.", ".##...##.", ".##...##.", "..#####.."),
'y': ("........", "........", "........", "........", "........", "........",
      ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", "..##.##..",
      "...###...", "....##...", "...##....", "..##....."),
'2': ("..#####..", ".##...##.", ".##...##.", "......##.", ".....##..", "....##...",
      "...##....", "..##.....", ".##......", ".##......", ".##......", ".##......",
      ".##......", ".##......", "########", "########"),
'4': ("....##..", "...###..", "..####..", ".##.##..", "##..##..", "##..##..",
      "########", "########", "....##..", "....##..", "....##..", "....##..",
      "....##..", "....##..", "...####.", "...####."),
'N': ("##....##", "###...##", "###...##", "####..##", "##.##.##", "##..####",
      "##...###", "##....##", "##....##", "##....##", "##....##", "##....##",
      "##....##", "##....##", "###..###", "###..###"),
'o': ("........", "........", "........", "........", "........", "........",
      "..#####..", ".##...##.", ".##...##.", ".##...##.", ".##...##.", ".##...##.",
      ".##...##.", ".##...##.", ".##...##.", "..#####.."),
'v': ("........", "........", "........", "........", "........", "........",
      ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.", ".##..##.",
      "..##.##..", "..##.##..", "...###...", "....##..."),
'm': ("........", "........", "........", "........", "........", "........",
      "########", "##.##.##.", "##.##.##.", "##.##.##.", "##.##.##.", "##.##.##.",
      "##.##.##.", "##.##.##.", "##.##.##.", "##.##.##."),
'b': ("##......", "##......", "##......", "##......", "##......", "##......",
      "##.###..", "##...##.", "##...##.", "##...##.", "##...##.", "##...##.",
      "##...##.", "##...##.", "##...##.", ".#####.."),
'r': ("........", "........", "........", "........", "........", "........",
      "##.###..", "##..##..", "##..##..", "##......", "##......", "##......",
      "##......", "##......", "##......", "##......"),
'0': ("..#####..", ".##...##.", ".##...##.", ".##...##.", ".##...##.", ".##...##.",
      ".##...##.", ".##...##.", ".##...##.", ".##...##.", ".##...##.", ".##...##.",
      ".##...##.", ".##...##.", ".##...##.", "..#####.."),
'6': ("...####..", "..##.....", ".##......", ".##......", ".##......", ".#####...",
      ".##..##..", ".##..##..", ".##..##..", ".##..##..", ".##..##..", ".##..##..",
      ".##..##..", ".##..##..", "..##.##..", "...###..."),
' ': ("........",) * 16,
}


def draw_masthead(x, y, s, c, sc=4):
    cx = x
    for ch in s:
        g = MAST.get(ch)
        if g is None:
            cx += 9 * sc
            continue
        for r in range(16):
            row = g[r]
            for cc in range(8):
                if row[cc] == '#':
                    rect(cx + cc * sc, y + r * sc, sc, sc, c)
        cx += 9 * sc
    return cx - x


# ---------------------------------------------------------------- illustration helpers
def person(x, y, h, shirt, skin=(232, 190, 150), pants=(40, 44, 60), s=1):
    """Simple standing figure, feet at (x, y+h)."""
    hw = max(2, 3 * s)
    rect(x - hw, y, hw * 2, h // 3, shirt)            # torso
    disc(x, y - max(2, h // 8), max(2, h // 8), skin)  # head
    rect(x - hw, y + h // 3, hw, h * 2 // 3, pants)    # legs
    rect(x + 1, y + h // 3, hw, h * 2 // 3, pants)


def building(x, y, w, h, c, win=(255, 230, 130)):
    rect(x, y, w, h, c)
    for wy in range(y + 5, y + h - 4, 9):
        for wx in range(x + 4, x + w - 4, 9):
            rect(wx, wy, 5, 5, win)


def skyline(x, y, w, h, base, cols):
    """Row of buildings rising from base y+h."""
    bx = x
    i = 0
    while bx < x + w - 8:
        bw = 14 + (i * 7) % 18
        bh = h // 2 + (i * 13) % (h // 2)
        building(bx, y + h - bh, min(bw, x + w - bx), bh, cols[i % len(cols)])
        bx += min(bw, x + w - bx) + 3
        i += 1


def sun(x, y, r, c=GOLD):
    disc(x, y, r, c)
    for k in range(8):
        ang = k * 3.14159 / 4
        import math
        x1 = x + int((r + 2) * math.cos(ang)); y1 = y + int((r + 2) * math.sin(ang))
        x2 = x + int((r + 6) * math.cos(ang)); y2 = y + int((r + 6) * math.sin(ang))
        line(x1, y1, x2, y2, c, 2)


def chart(x, y, w, h, pts, c, bg=None):
    if bg:
        rect(x, y, w, h, bg)
    n = len(pts)
    for i in range(n - 1):
        x0 = x + i * w // (n - 1); x1 = x + (i + 1) * w // (n - 1)
        y0 = y + h - int(pts[i] * h); y1 = y + h - int(pts[i + 1] * h)
        line(x0, y0, x1, y1, c, 2)
        disc(x0, y0, 2, c)
    disc(x + (n - 1) * w // (n - 1), y + h - int(pts[-1] * h), 3, c)


def plane(x, y, s, c, flip=False):
    """Small jet silhouette, nose to the right unless flip."""
    d = -1 if flip else 1
    body = [(0, 0), (10, -2), (26, -2), (30, 0), (26, 2), (10, 2)]
    for (ax, ay), (bx, by) in zip(body, body[1:]):
        line(x + ax * d * s // 2, y + ay * s // 2, x + bx * d * s // 2, y + by * s // 2, c, 2)
    line(x + 12 * d * s // 2, y, x + 16 * d * s // 2, y - 6 * s // 2, c, 2)
    line(x + 12 * d * s // 2, y, x + 16 * d * s // 2, y + 6 * s // 2, c, 2)
    line(x + 2 * d * s // 2, y, x + 5 * d * s // 2, y - 5 * s // 2, c, 2)


def ship(x, y, w, h, hull, deck):
    rect(x, y, w, h // 2, deck)
    tri(x, y + h // 2, x + w, y + h // 2, x + w // 2, y + h, hull)
    rect(x + w // 4, y - h // 3, 4, h // 3, hull)


def radar(x, y, r, c):
    ring(x, y, r, c, 2)
    ring(x, y, r * 2 // 3, c, 1)
    disc(x, y, 2, c)
    line(x, y, x + r, y - r // 2, c, 2)


def flagpole(x, y, h, flag_c):
    vline(x, y, h, INK, 2)
    tri(x, y, x + 16, y + 5, x, y + 10, flag_c)


def ball(x, y, r, c=WHITE, p=INK):
    disc(x, y, r, c)
    ring(x, y, r, p, 1)
    disc(x, y, max(1, r // 3), p)
    for k in range(5):
        import math
        ang = k * 1.2566
        line(x, y, x + int(r * 0.9 * math.cos(ang)), y + int(r * 0.9 * math.sin(ang)), p, 1)


def trophy(x, y, s, c=GOLD):
    rect(x, y, 12 * s, 4 * s, c)
    rect(x + 2 * s, y + 4 * s, 8 * s, 8 * s, c)
    rect(x + 4 * s, y + 12 * s, 4 * s, 4 * s, c)
    rect(x + 1 * s, y + 16 * s, 10 * s, 2 * s, c)

# ---------------------------------------------------------------- story data
# Every story verified against a real wire on 24 Nov 2026 (UTC dating; Asia
# items dated by their Tuesday local time). Sources named per story.
# Heroes: 3. Secondaries: 10. Also list: 23. Total 36 stories, 7 regions.
# Region counts: Asia-Pacific 14, Europe 7, Americas 11, Middle East 1,
# Africa 1, Oceania 1, World 1.

HEROES = [
    dict(num=1, place="ULLEUNG, SOUTH KOREA", cat="AIR DEFENCE", badge="OFFICIAL",
         banner="SEOUL: ALERT", tag="3 MIN",
         head="Seoul alert as aircraft enters its airspace",
         body=("South Korea briefly ordered Ulleung islanders to shelter on "
               "Tuesday after an aircraft entered its airspace. The alert "
               "was lifted three minutes later, the safety ministry said."),
         src="Reuters", illu="seoul"),
    dict(num=2, place="ASIA MARKETS", cat="STOCKS", badge="REPORTED",
         banner="ASIA: RALLY", tag="+4.3%",
         head="Asia shares rally as chip stocks lead the way",
         body=("Stocks across Asia rose sharply on Tuesday, with South "
               "Korea's Kospi up 4.3% and Japan's Nikkei up 2.8%, after "
               "Wall Street's best day in months. Oil eased as Iran "
               "tensions cooled."),
         src="Reuters", illu="markets"),
    dict(num=3, place="PYONGYANG, NORTH KOREA", cat="DIPLOMACY", badge="REPORTED",
         banner="PYONGYANG: WARNING", tag="KCNA",
         head="Pyongyang may shut Swiss office in the North",
         body=("North Korea said it will consider shutting Switzerland's "
               "diplomatic office in Pyongyang, state media said, after "
               "Bern sanctioned a children's camp over ties to Russia."),
         src="Reuters / KCNA", illu="office"),
]

SECONDARIES = [
    dict(num=4, place="OTTAWA", cat="TRADE", banner="PACT DUE",
         head="Canada and Qatar to sign investment pact today",
         body="Deal to unlock Gulf investment pledged in January.",
         src="Reuters", illu="pact"),
    dict(num=5, place="LAUSANNE", cat="SPORT", banner="CAS RULES",
         head="CAS to rule on Senegal's Cup title appeal",
         body="Court decides on Senegal's appeal over stripped Cup title.",
         src="Reuters", illu="trophy"),
    dict(num=6, place="EUROPE", cat="FOOTBALL", banner="9 GAMES",
         head="Champions League: nine games on Tuesday night",
         body="Arsenal host Dortmund; Man City face Napoli.",
         src="UEFA", illu="ucl"),
    dict(num=7, place="TOKYO", cat="ECONOMY", banner="PMI DUE",
         head="Japan flash PMI due as factories hold at 53.5",
         body="S&P Global releases November flash PMIs at 00:30 GMT; services seen at 51.7.",
         src="S&P Global", illu="factory"),
    dict(num=8, place="BERLIN", cat="ECONOMY", banner="IFO DUE",
         head="Germany's Ifo business index due today",
         body="November reading lands this morning.",
         src="Reuters", illu="factory"),
    dict(num=9, place="WASHINGTON", cat="MARKETS", banner="$70BN SALE",
         head="US Treasury sells $70bn of five-year notes",
         body="Auction due today as investors watch inflation data.",
         src="Reuters", illu="bank"),
    dict(num=10, place="OTTAWA", cat="ECONOMY", banner="SPEECH",
         head="Bank of Canada chief Macklem speaks today",
         body="Governor addresses markets a day after Wall Street's surge.",
         src="Reuters", illu="bank"),
    dict(num=11, place="LOS ANGELES", cat="SPORT", banner="NBA NIGHT",
         head="NBA tonight: Lakers host Jazz, Spurs at Kings",
         body="Lakers face Utah at 10pm ET; Spurs visit Kings.",
         src="Sportradar", illu="nba"),
    dict(num=12, place="AUSTIN", cat="BUSINESS", banner="EARNINGS",
         head="Dell and HP report earnings today",
         body="PC makers report after Monday's tech surge.",
         src="Newsquawk", illu="laptop"),
    dict(num=13, place="WASHINGTON", cat="ECONOMY", banner="CPI DUE",
         head="US inflation data due later today",
         body="Report in focus for Fed rate bets after Wall Street's rally.",
         src="Reuters", illu="prices"),
]

ALSO = [
    (14, "ASIA-PACIFIC", "Kospi jumps 4.3% to 5,235 as chip stocks lead Asia's rally", "Reuters"),
    (15, "ASIA-PACIFIC", "Nikkei gains 2.8% to 60,398 after Wall Street's best day in months", "Reuters"),
    (16, "ASIA-PACIFIC", "Tokyo Electron up 5.6%, Advantest up 3.4% in chip rebound", "Reuters"),
    (17, "ASIA-PACIFIC", "Taiex surges as much as 6.4% as Taiwan tech roars back", "Reuters"),
    (18, "ASIA-PACIFIC", "Hang Seng rises 0.4% in calmer Hong Kong trade", "Reuters"),
    (19, "ASIA-PACIFIC", "Shanghai Composite edges 0.4% higher", "Reuters"),
    (20, "OCEANIA", "ASX 200 rises 1.1% to 9,131 in Sydney", "Reuters"),
    (21, "ASIA-PACIFIC", "MSCI Asia-Pacific index climbs about 2%", "Reuters"),
    (22, "MIDDLE EAST", "Oil eases as Trump signals no fresh Iran strikes if talks progress", "Reuters"),
    (23, "ASIA-PACIFIC", "Taiwan cuts margin-call floor to 120% from today", "FXStreet"),
    (24, "AMERICAS", "US ADP weekly jobs data and Chicago Fed gauges due today", "Newsquawk"),
    (25, "AMERICAS", "US futures steady in Asia trade after Monday's rally", "Reuters"),
    (26, "AMERICAS", "Wall Street heads into a shortened Thanksgiving week", "FXStreet"),
    (27, "EUROPE", "Galatasaray host Aston Villa in early Champions League kick-off", "UEFA"),
    (28, "EUROPE", "Man City host Napoli; De Bruyne faces his old club", "TNT Sports"),
    (29, "EUROPE", "Real Madrid host PSV Eindhoven tonight", "UEFA"),
    (30, "AMERICAS", "NBA: Hornets host Grizzlies in Tuesday's early game", "Sportradar"),
    (31, "AMERICAS", "Spurs visit Kings; San Antonio are 14-3 this season", "Statz"),
    (32, "WORLD", "Bond supply due from Australia, the Netherlands and the US", "Newsquawk"),
    (33, "EUROPE", "Bodo/Glimt host LASK in Champions League early kick-off", "UEFA"),
    (34, "EUROPE", "Leipzig host Lens; Feyenoord face Porto tonight", "UEFA"),
    (35, "ASIA-PACIFIC", "SoftBank jumps 15% ahead of its earnings", "Reuters"),
    (36, "ASIA-PACIFIC", "TOPIX advances 2.2% in Tokyo", "Reuters"),
]

BADGE_C = {"OFFICIAL": (34, 120, 60), "REPORTED": (16, 110, 105),
           "CONFIRMED": (34, 120, 60), "CLAIM": (178, 34, 34),
           "FORECAST": (96, 64, 140)}

REGIONS = [("ASIA-PACIFIC", 14, (16, 110, 105)), ("EUROPE", 7, NAVY),
           ("AMERICAS", 11, (52, 110, 165)), ("MIDDLE EAST", 1, RED),
           ("AFRICA", 1, (34, 120, 60)), ("OCEANIA", 1, (96, 64, 140)),
           ("WORLD", 1, GREY)]

KEYNUMS = [("3 MIN", "Seoul alert lasted"), ("+4.3%", "Kospi jump"),
           ("+2.8%", "Nikkei gain"), ("9", "UCL games tonight"),
           ("$70BN", "US note sale"), ("15%", "SoftBank jump")]

TIMELINE = [("00:30", "Japan PMI due"), ("07:52 KST", "Seoul alert"),
            ("09:00 CET", "Ifo due"), ("14:00 CET", "CAS ruling"),
            ("17:45", "UCL early games"), ("20:00", "UCL main games")]

DATECHECK = ("Left out as other days' news: COP31 collapse (Sun 22 Nov) - "
             "186 drones over Ukraine (Sun 22 Nov) - 153 drones, Dymer toll "
             "(Mon 23 Nov) - Russian corvette sunk off Libya (Sun 22 Nov) - "
             "UNRWA worker killed in Gaza (Mon 23 Nov) - singer Ahmadi "
             "flogged (Mon 23 Nov) - Indonesia fire, 24 dead (Mon 23 Nov) - "
             "Democrats' 258 House seats (Sun 22 Nov) - Wellington Test "
             "drawn (Mon 23 Nov) - Rubio meets Qatar PM (Mon 23 Nov) - Peru "
             "quake (Fri 20 Nov). Not yet decided when drawn: CAS ruling, "
             "Japan PMI, Ifo, US inflation, UCL results, Kyiv's toll.")

MX = 14
CW = 996


def badge(x, y, label):
    c = BADGE_C.get(label, GREY)
    w = text_w(label, 1) + 8
    rect(x, y, w, 12, c)
    draw_text(x + 4, y + 2, label, WHITE, 1)
    return w


def banner(x, y, label):
    w = text_w(label, 1) + 10
    rect(x, y, w, 14, RED)
    draw_text(x + 5, y + 3, label, WHITE, 1)
    return w


def tagbox(x, y, label):
    w = text_w(label, 1) + 10
    rect(x, y, w, 14, WHITE)
    draw_text(x + 5, y + 3, label, INK, 1)
    return w


# ---------------------------------------------------------------- illustrations
def illu_seoul(x, y, w, h):
    rect(x, y, w, h, DARK)
    for i in range(40):
        px(x + (i * 97) % w, y + (i * 53) % (h // 2), (200, 210, 230))
    disc(x + 66, y + 22, 12, (240, 235, 200))
    rect(x, y + h - 34, w, 34, (30, 60, 50))
    for bx in range(x + 10, x + w - 20, 34):
        bh = 26 + ((bx * 7) % 22)
        building(bx, y + h - bh, 26, bh, (52, 66, 92), (255, 220, 110))
    radar(x + 52, y + h - 58, 16, (120, 220, 140))
    plane(x + w - 150, y + 34, 2, (240, 240, 240))
    tri(x + w // 2 - 14, y + h - 62, x + w // 2 + 14, y + h - 62, x + w // 2, y + h - 96, RED)
    rect(x + w // 2 - 11, y + h - 88, 22, 10, (255, 220, 60))
    draw_text(x + w // 2 - 9, y + h - 86, "!", INK, 1)


def illu_markets(x, y, w, h):
    rect(x, y, w, h, SKY)
    sun(x + w - 42, y + 24, 13)
    rect(x, y + h - 46, w, 46, GRASS)
    skyline(x + 6, y + 30, w - 12, h - 76, y + h - 46,
            [(90, 110, 140), (70, 90, 120), (110, 130, 160)])
    chart(x + 14, y + 14, w - 28, h - 90, [0.15, 0.3, 0.25, 0.5, 0.45, 0.75, 0.95],
          (34, 120, 60), None)
    person(x + 40, y + h - 46, 30, RED)
    person(x + 62, y + h - 46, 30, NAVY)
    person(x + w - 60, y + h - 46, 30, TEAL)


def illu_office(x, y, w, h):
    rect(x, y, w, h, LBLUE)
    sun(x + 36, y + 22, 12)
    rect(x, y + h - 30, w, 30, GRASS)
    building(x + w // 2 - 55, y + 26, 110, h - 56, (200, 200, 205), (70, 110, 160))
    rect(x + w // 2 - 55, y + 26, 110, 8, RED)
    rect(x + w // 2 - 14, y + 44, 28, 28, WHITE)
    rect(x + w // 2 - 3, y + 44, 6, 28, RED)
    rect(x + w // 2 - 14, y + 55, 28, 6, RED)
    flagpole(x + w - 60, y + 30, 46, RED)
    person(x + 46, y + h - 30, 26, NAVY)
    person(x + 66, y + h - 30, 26, RED)
    person(x + w - 100, y + h - 30, 26, TEAL)


def illu_small(kind, x, y, w, h):
    """Small 191x64 pictogram for secondaries."""
    if kind == "pact":
        rect(x, y, w, h, LBLUE)
        flagpole(x + 26, y + 8, 40, RED)
        rect(x + 40, y + 8, 34, 20, (140, 20, 40))
        rect(x + 40, y + 16, 34, 4, WHITE)
        flagpole(x + w - 70, y + 8, 40, (120, 30, 60))
        rect(x + w - 56, y + 8, 34, 20, (140, 30, 70))
        rect(x + w // 2 - 24, y + h - 22, 48, 16, WHITE)
        draw_text(x + w // 2 - 20, y + h - 18, "DEAL", INK, 1)
    elif kind == "trophy":
        rect(x, y, w, h, (30, 50, 90))
        trophy(x + w // 2 - 12, y + 6, 2)
        ball(x + 30, y + h - 16, 10)
        ball(x + w - 34, y + h - 16, 10)
        draw_text(x + w // 2 - 24, y + h - 14, "CAS", GOLD, 1)
    elif kind == "ucl":
        rect(x, y, w, h, (20, 40, 80))
        rect(x, y + h - 18, w, 18, GRASS)
        ball(x + w // 2, y + h - 34, 14)
        for fx in (20, w - 20):
            line(x + fx, y + 6, x + fx, y + 22, GOLD, 3)
            disc(x + fx, y + 6, 4, GOLD)
    elif kind == "factory":
        rect(x, y, w, h, SKY)
        rect(x, y + h - 26, w, 26, (120, 120, 125))
        building(x + 14, y + 18, 46, h - 30, (90, 90, 100), (255, 220, 110))
        tri(x + 70, y + 30, x + 78, y + 30, x + 74, y + 8, (70, 70, 80))
        rect(x + 96, y + 26, 40, h - 38, (110, 110, 120))
        chart(x + 130, y + 10, w - 146, 30, [0.3, 0.45, 0.4, 0.7, 0.9], GREEN, None)
    elif kind == "bank":
        rect(x, y, w, h, SAND)
        rect(x + 20, y + 14, w - 40, 8, (120, 90, 60))
        for cx in range(x + 30, x + w - 30, 26):
            rect(cx, y + 24, 8, h - 34, (200, 180, 140))
        rect(x + 16, y + h - 12, w - 32, 6, (120, 90, 60))
        draw_text(x + w // 2 - 6, y + 28, "$", (120, 90, 60), 2)
    elif kind == "nba":
        rect(x, y, w, h, (200, 90, 40))
        disc(x + w // 2, y + h // 2 + 4, 20, (230, 120, 40))
        ring(x + w // 2, y + h // 2 + 4, 20, INK, 1)
        line(x + w // 2 - 20, y + h // 2 + 4, x + w // 2 + 20, y + h // 2 + 4, INK, 1)
        line(x + w - 34, y + 8, x + w - 34, y + 26, WHITE, 3)
        rect(x + w - 46, y + 6, 24, 4, WHITE)
        ring(x + w - 34, y + 30, 7, WHITE, 2)
    elif kind == "laptop":
        rect(x, y, w, h, (40, 60, 90))
        rect(x + w // 2 - 44, y + 8, 88, 34, (20, 30, 50))
        chart(x + w // 2 - 38, y + 13, 76, 24, [0.2, 0.4, 0.35, 0.6, 0.85], (120, 220, 140), None)
        rect(x + w // 2 - 54, y + 44, 108, 5, (180, 180, 190))
        draw_text(x + 12, y + h - 14, "DELL  HP", WHITE, 1)
    elif kind == "prices":
        rect(x, y, w, h, (250, 240, 210))
        rect(x + 20, y + 12, 60, 26, WHITE)
        draw_text(x + 26, y + 18, "$", RED, 2)
        line(x + 96, y + 44, x + 150, y + 12, RED, 3)
        tri(x + 150, y + 12, x + 138, y + 12, x + 150, y + 24, RED)
        draw_text(x + w - 60, y + h - 14, "CPI", INK, 1)
    else:
        rect(x, y, w, h, LGREY)


# ---------------------------------------------------------------- header
def draw_header():
    rect(0, 0, W, 24, NAVY)
    draw_text(14, 8, "THE WORLD IN ONE DAY", WHITE, 1)
    draw_text_center(0, 8, W, "36 STORIES  \u00b7  7 REGIONS  \u00b7  EVERY ONE DATED "
                     "TUESDAY 24 NOVEMBER 2026", WHITE, 1)
    # masthead
    draw_masthead((W - 864) // 2, 30, "Tuesday 24 November 2026", INK, 4)
    hline(14, 100, CW, INK, 2)
    hline(14, 104, CW, INK, 1)
    draw_text_center(0, 110, W, "Seoul alert after airspace entry  \u00b7  "
                     "Asia shares rally  \u00b7  Pyongyang may shut Swiss office",
                     RED, 1)
    # key numbers
    y0 = 126
    for i, (num, cap) in enumerate(KEYNUMS):
        x0 = MX + i * 166
        if i:
            vline(x0, y0, 32, LGREY, 1)
        draw_text_center(x0, y0 + 2, 166, num, RED, 2)
        draw_text_center(x0, y0 + 22, 166, cap, GREY, 1)
    # region bar
    y0 = 168
    x0 = MX
    for name, n, c in REGIONS:
        wseg = int(round(n * CW / 36.0))
        rect(x0, y0, wseg, 18, c)
        if wseg >= 60:
            draw_text(x0 + 6, y0 + 5, "%s %d" % (name, n), WHITE, 1)
        elif wseg >= 26:
            draw_text(x0 + 4, y0 + 5, str(n), WHITE, 1)
        x0 += wseg
    # timeline strip
    y0 = 190
    rect(MX, y0, CW, 18, DARK)
    draw_text(MX + 6, y0 + 5, "THE DAY IN UTC", WHITE, 1)
    tx = MX + 108
    for t, what in TIMELINE:
        draw_text(tx, y0 + 5, t, GOLD, 1)
        tx += text_w(t, 1) + 4
        draw_text(tx, y0 + 5, what, WHITE, 1)
        tx += text_w(what, 1) + 14


def draw_hero(st, x, y, w):
    illu = {"seoul": illu_seoul, "markets": illu_markets, "office": illu_office}[st["illu"]]
    illu(x, y, w, 128)
    banner(x, y, st["banner"])
    tagbox(x + w - text_w(st["tag"], 1) - 10, y, st["tag"])
    ky = y + 136
    draw_text(x, ky, "%d %s \u00b7 %s" % (st["num"], st["place"], st["cat"]), RED, 1)
    bw = badge(x + w - text_w(st["badge"], 1) - 8, ky - 1, st["badge"])
    hy = ky + 14
    hy = para(x, hy, w, st["head"], INK, 2, lh=15, max_lines=3)
    by = hy + 4
    by = para(x, by, w, st["body"], INK, 1, lh=9, max_lines=5)
    draw_text(x, by + 2, "(%s)" % st["src"], GREY, 1)


def draw_secondary(st, x, y, w):
    illu_small(st["illu"], x, y, w, 60)
    banner(x, y, st["banner"])
    ky = y + 63
    draw_text(x, ky, "%d %s \u00b7 %s" % (st["num"], st["place"], st["cat"]), RED, 1)
    hy = ky + 11
    hy = para(x, hy, w, st["head"], INK, 1, lh=8, max_lines=2)
    by = hy + 2
    by = para(x, by, w, st["body"], (60, 60, 66), 1, lh=8, max_lines=2)
    draw_text(x, by + 1, "(%s)" % st["src"], GREY, 1)

# ---------------------------------------------------------------- world map
MAP_ROWS = [
    "............................................",
    "..#########...###.........################..",
    "..###########.##....#######################.",
    "...##########.......#######################.",
    "....########.........#####.###############..",
    "....#######...........###.#############.....",
    ".....#####...........#######.#########......",
    "......###............#######..#######.......",
    "..........####.......######......####.......",
    "..........#####.......#####.................",
    "..........#####.......####..................",
    "...........####........###..................",
    "...........###.........##...................",
    "...........##..........##.........######....",
    "............#.....................######....",
    "............#......................####.....",
    ".........................................#..",
    "..........................................#.",
    "............................................",
    "............................................",
    "............................................",
    "............................................",
]

# (story number, map col, map row) — one pin per place, spread so the
# numbered discs do not touch.
PINS = [
    (1, 37, 4), (2, 40, 3), (3, 35, 2), (4, 7, 4), (5, 22, 4),
    (6, 20, 3), (7, 41, 5), (8, 24, 2), (9, 8, 5), (11, 5, 5),
    (12, 6, 7), (20, 38, 14), (22, 27, 6), (27, 26, 5),
]


def draw_map(x, y, w, h):
    draw_text(x, y, "WHERE IT HAPPENED", INK, 1)
    draw_text(x + w - text_w("pins: main stories", 1), y,
              "pins: main stories", GREY, 1)
    mx, my = x + (w - 44 * 6) // 2, y + 20
    rect(mx - 6, my - 6, 44 * 6 + 12, 22 * 6 + 12, (235, 242, 248))
    for r, row in enumerate(MAP_ROWS):
        for cc, ch in enumerate(row):
            if ch == '#':
                rect(mx + cc * 6 + 1, my + r * 6 + 1, 4, 4, (150, 170, 150))
    for num, col, row in PINS:
        cx, cy = mx + col * 6 + 3, my + row * 6 + 3
        disc(cx, cy, 6, RED)
        ring(cx, cy, 6, WHITE, 1)
        s = str(num)
        draw_text(cx - text_w(s, 1) // 2, cy - 3, s, WHITE, 1)


def draw_also(x, y, w, h):
    draw_text(x, y, "ALSO ON TUESDAY 24 NOVEMBER \u2014 23 MORE STORIES",
              RED, 1)
    hline(x, y + 11, w, RED, 1)
    colw = (w - 16) // 2
    half = (len(ALSO) + 1) // 2
    for ci, items in enumerate((ALSO[:half], ALSO[half:])):
        cx = x + ci * (colw + 16)
        cy = y + 18
        for num, region, text, src in items:
            label = "%d %s: " % (num, region)
            full = label + text + " (%s)" % src
            lines = wrap(full, colw // 6)
            for li, ln in enumerate(lines[:2]):
                if li == 0:
                    draw_text(cx, cy, str(num), RED, 1)
                    draw_text(cx + text_w(str(num) + " ", 1), cy, ln[len(str(num)) + 1:],
                              INK, 1)
                else:
                    draw_text(cx, cy, ln, INK, 1)
                cy += 8
            cy += 1


def draw_datecheck(y):
    # red border
    hline(MX, y, CW, RED, 2)
    hline(MX, y + 54, CW, RED, 2)
    vline(MX, y, 56, RED, 2)
    vline(MX + CW - 2, y, 56, RED, 2)
    rect(MX + 2, y + 2, text_w("DATE CHECK", 1) + 10, 14, RED)
    draw_text(MX + 7, y + 5, "DATE CHECK", WHITE, 1)
    para(MX + 8, y + 20, CW - 16, DATECHECK, INK, 1, lh=9, max_lines=4)


def draw_footer(y):
    draw_text(MX, y, "Sources: Reuters, BBC, AFP, AP, Al Jazeera, S&P Global, "
              "UEFA, Sportradar, Newsquawk, FXStreet, Statz. Pictures and map: "
              "original, drawn in code.",
              GREY, 1)
    draw_text(MX, y + 10, "CERTAINTY: OFFICIAL = named authority  \u00b7  "
              "REPORTED = carried by the day's wires  \u00b7  FORECAST = still "
              "to happen when drawn  \u00b7  Wires read to 00:30 UTC.",
              GREY, 1)
    rect(0, 1008, W, 16, NAVY)
    draw_text(14, 1012, "THE WORLD IN ONE DAY", WHITE, 1)
    draw_text(W - 14 - text_w("TUESDAY 24 NOVEMBER 2026  \u00b7  ONE PAGE", 1),
              1012, "TUESDAY 24 NOVEMBER 2026  \u00b7  ONE PAGE", WHITE, 1)


def build():
    rect(0, 0, W, H, PAPER)
    draw_header()
    # heroes: y 212..466, three columns of 324
    for i, st in enumerate(HEROES):
        draw_hero(st, MX + i * 336, 212, 324)
    # secondaries: two rows of five, y 470 and 590
    for i, st in enumerate(SECONDARIES):
        row, col = divmod(i, 5)
        draw_secondary(st, MX + col * 201, 470 + row * 120, 191)
    # map + also list: y 706..928
    draw_map(MX, 706, 316, 222)
    draw_also(342, 706, 668, 222)
    draw_datecheck(932)
    draw_footer(991)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    build()
    data = png_bytes(bytes(fb), W, H)
    with open(os.path.join(outdir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
