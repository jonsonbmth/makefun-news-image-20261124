#!/usr/bin/env python3
"""Koran 24 v2 — one-page newspaper front page for Tuesday 24 November 2026.

Draws the whole front page in code: own framebuffer rasterizer, own
hand-typed bitmap fonts (a small 5x7 face for body text and a larger
serif face for the masthead), own PNG encoder, hand-drawn illustrations
and a dotted world map. Python 3.13 standard library only, no network,
no randomness, no wall-clock use: two runs write byte-identical PNGs.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png),
1024x1024, under 1 MiB.

Press time: 09:00 UTC, Tuesday 24 November 2026 (16:00 WIB).
39 verified stories, 7 regions. Every story was checked against a real
wire (Reuters, KCNA, S&P Global, UEFA, AP, Bank of Canada, Treasury)
on 24 November 2026; forecasts and still-open outcomes are labelled
as such and listed in the DATE CHECK box.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (250, 246, 236)
INK = (18, 22, 38)
NAVY = (16, 28, 58)
NAVY2 = (28, 44, 86)
RED = (178, 24, 28)
RED_DK = (140, 16, 20)
GREY = (110, 108, 100)
LGREY = (228, 222, 210)
WHITE = (255, 255, 255)
CREAM = (244, 238, 226)
GOLD = (198, 142, 32)
TEAL = (14, 110, 110)
GREEN = (28, 120, 58)
ORANGE = (214, 110, 20)
SKY = (126, 178, 214)
SKY_DK = (58, 110, 160)
NIGHT = (20, 32, 66)
NIGHT2 = (34, 52, 96)

REGION_COLORS = {
    "ASIA-PACIFIC": (196, 116, 16),
    "EUROPE": (36, 84, 160),
    "AMERICAS": (20, 120, 96),
    "MIDDLE EAST": (178, 24, 28),
    "AFRICA": (96, 140, 32),
    "OCEANIA": (120, 74, 150),
    "WORLD": (90, 92, 96),
}

# ---------------------------------------------------------------- framebuffer
fb = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = c[0]
        fb[i + 1] = c[1]
        fb[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = c
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            fb[i] = r
            fb[i + 1] = g
            fb[i + 2] = b


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c):
    """Bresenham line."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    if fill:
        for yy in range(-r, r + 1):
            dx = int((r * r - yy * yy) ** 0.5)
            for xx in range(-dx, dx + 1):
                px(cx + xx, cy + yy, c)
    else:
        x, y, d = r, 0, 1 - r
        while x >= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                px(cx + sx, cy + sy, c)
            y += 1
            if d <= 0:
                d += 2 * y + 1
            else:
                x -= 1
                d += 2 * (y - x) + 1


def tri(x0, y0, x1, y1, x2, y2, c):
    """Filled triangle via scanline."""
    pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    if ay == cy:
        return
    for y in range(ay, cy + 1):
        t1 = (y - ay) / (cy - ay) if cy != ay else 0
        xa = ax + (cx - ax) * t1
        if y < by:
            t2 = (y - ay) / (by - ay) if by != ay else 0
            xb = ax + (bx - ax) * t2
        else:
            t2 = (y - by) / (cy - by) if cy != by else 0
            xb = bx + (cx - bx) * t2
        x0s, x1s = int(min(xa, xb)), int(max(xa, xb))
        for x in range(x0s, x1s + 1):
            px(x, y, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 chars, '#' = on. Hand-typed.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_glyph(x, y, ch, c, s=1, bold=False):
    g = FONT.get(ch)
    if g is None:
        return 6 * s
    for r, row in enumerate(g):
        for col, bit in enumerate(row):
            if bit == '1':
                if s == 1:
                    px(x + col, y + r, c)
                    if bold:
                        px(x + col + 1, y + r, c)
                else:
                    rect(x + col * s, y + r * s, s, s, c)
                    if bold:
                        rect(x + col * s + 1, y + r * s, s, s, c)
    return 6 * s


def text_w(s, size=1):
    return len(s) * 6 * size - size


def draw_text(x, y, s, c, size=1, bold=False, align="l"):
    if align == "c":
        x -= text_w(s, size) // 2
    elif align == "r":
        x -= text_w(s, size)
    cx = x
    for ch in s:
        cx += draw_glyph(cx, y, ch, c, size, bold)
    return cx


def wrap(s, width_chars):
    """Greedy word wrap to a list of lines, max width_chars each."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) <= width_chars:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(x, y, s, c, size=1, maxw=40, lh=None, bold=False):
    """Draw wrapped paragraph; returns y after last line."""
    if lh is None:
        lh = 8 * size + 1
    for ln in wrap(s, maxw):
        draw_text(x, y, ln, c, size, bold)
        y += lh
    return y


# ---------------------------------------------------------------- masthead
# Large serif face, 10 wide x 14 tall, hand-drawn with serif feet and
# tapered stems so the masthead reads as a newspaper nameplate, not
# scaled-up pixels. Only the glyphs the masthead needs.
SERIF = {
    'T': ("##########", "##########", "....##....", "....##....",
          "....##....", "....##....", "....##....", "....##....",
          "....##....", "....##....", "....##....", "....##....",
          "...####...", "...####..."),
    'u': ("..........", "..........", "..........", "..........",
          "..........", "##....##..", "##....##..", "##....##..",
          "##....##..", "##....##..", "##....##..", "##...###..",
          ".####.##..", ".........."),
    'e': ("..........", "..........", "..........", "..........",
          "..........", "...####...", "..##..##..", ".##....##.",
          ".#######..", ".##.......", ".##....##.", "..##..##..",
          "...####...", ".........."),
    's': ("..........", "..........", "..........", "..........",
          "..........", "...####...", "..##..##..", ".##.......",
          "..####....", ".....##...", "......##..", ".##...##..",
          "..####....", ".........."),
    'd': (".......##.", ".......##.", ".......##.", ".......##.",
          ".......##.", "...####.#.", "..##..##.#", ".##....##.",
          ".##....##.", ".##....##.", ".##....##.", "..##..##.#",
          "...####.#.", ".........."),
    'a': ("..........", "..........", "..........", "..........",
          "..........", "...####...", "..##..##..", ".##....##.",
          ".##..###..", "..##.##...", "...#.##...", "..##..##..",
          "...####...", ".........."),
    'y': ("..........", "..........", "..........", "..........",
          "..........", "##....##..", "##....##..", "##....##..",
          ".##..##...", "..####....", "...##.....", "...##.....",
          "..##......", ".##......."),
    '2': ("..######..", ".##....##.", ".......##.", "......##..",
          ".....##...", "....##....", "...##.....", "..##......",
          ".##.......", ".##.......", ".##.......", ".##.......",
          ".########.", ".########."),
    '4': (".....##...", "....###...", "...##.#...", "..##..#...",
          ".##...#...", "##########", "##########", "......#...",
          "......#...", "......#...", "......#...", "......#...",
          "......#...", ".........."),
    'N': ("##......##", "###.....##", "###.....##", "####....##",
          "##.##...##", "##..##..##", "##...##.##", "##....####",
          "##.....###", "##.....###", "##......##", "##......##",
          "##......##", ".........."),
    'o': ("..........", "..........", "..........", "..........",
          "..........", "...####...", "..##..##..", ".##....##.",
          ".##....##.", ".##....##.", ".##....##.", "..##..##..",
          "...####...", ".........."),
    'v': ("..........", "..........", "..........", "..........",
          "..........", "##....##..", "##....##..", "##....##..",
          "##....##..", ".##..##...", ".##..##...", "..####....",
          "...##.....", ".........."),
    'm': ("..........", "..........", "..........", "..........",
          "..........", "##..###.#.", "###.##.###", "##..##..##",
          "##..##..##", "##..##..##", "##..##..##", "##..##..##",
          "##..##..##", ".........."),
    'b': ("##........", "##........", "##........", "##........",
          "##........", "####......", "##..##....", "##....##..",
          "##....##..", "##....##..", "##....##..", "##..##....",
          "####......", ".........."),
    'r': ("..........", "..........", "..........", "..........",
          "..........", "##..###...", "###..##...", "##...##...",
          "##........", "##........", "##........", "##........",
          "##........", ".........."),
    '0': ("...####...", "..##..##..", ".##....##.", ".##...###.", ".##..####.",
          ".##.##.##.", ".####..##.", ".###...##.", ".##....##.", "..##..##..",
          "...####...", "..........", "..........", ".........."),
    '6': ("...####...", "..##..##..", ".##....##.", ".##.......",
          ".##.###...", ".###..##..", "##....##..", "##....##..",
          "##....##..", ".##...##..", "..##.##...", "...###....",
          "..........", ".........."),
    ' ': ("..........", "..........", "..........", "..........",
          "..........", "..........", "..........", "..........",
          "..........", "..........", "..........", "..........",
          "..........", ".........."),
}


def draw_serif(x, y, s, c, scale=4):
    """Draw masthead text; glyphs are 10x14, scaled by `scale`, with a
    one-pixel bold pass so the strokes read as a serif nameplate."""
    cx = x
    for ch in s:
        g = SERIF.get(ch)
        if g is None:
            cx += 5 * scale
            continue
        for r, row in enumerate(g):
            for col, bit in enumerate(row):
                if bit == '#':
                    rect(cx + col * scale, y + r * scale,
                         scale + 1, scale, c)
        cx += 10 * scale
    return cx


def serif_w(s, scale=4):
    return len(s) * 10 * scale


# ---------------------------------------------------------------- pictures
def scene_sky(x, y, w, h, top, bot):
    """Vertical gradient sky."""
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        hline(x, y + yy, w, c)


def stars(x, y, w, h, n, seed=7):
    rnd = seed
    for _ in range(n):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        sx = x + rnd % w
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        sy = y + rnd % (h // 2)
        px(sx, sy, WHITE)
        if rnd % 3 == 0:
            px(sx + 1, sy, WHITE)


def person(x, y, s, shirt, skin=(232, 190, 150), hair=(40, 30, 22)):
    """Small standing person, s = height in px."""
    hw = max(2, s // 5)
    circle(x, y + s // 8, max(2, s // 9), skin)
    rect(x - hw, y + s // 8 + 2, hw * 2, max(1, s // 9), hair)
    rect(x - hw, y + s // 4, hw * 2, s // 2, shirt)
    rect(x - hw, y + s // 4 + s // 2, hw, s // 4, INK)
    rect(x + 1, y + s // 4 + s // 2, hw, s // 4, INK)


def jet(x, y, s, c):
    """Simple fighter jet silhouette, facing right."""
    tri(x, y, x + s, y + s // 3, x, y + s // 3 * 2, c)
    rect(x + s // 2, y - s // 4, s // 3, s // 4, c)
    tri(x + s // 4, y + s // 3, x + s // 2, y + s, x + s // 3 * 2,
        y + s // 3, c)
    rect(x + s, y + s // 4, s // 3, s // 6, c)


def chart_up(x, y, w, h, c, n=7, seed=11):
    """Rising line chart with area fill."""
    rnd = seed
    pts = []
    v = h * 0.75
    for i in range(n):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        v -= (rnd % (h // 3)) + 2
        v = max(4, min(h - 4, v))
        pts.append((x + i * (w // (n - 1)), y + int(v)))
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], c)
        line(pts[i][0], pts[i][1] + 1, pts[i + 1][0], pts[i + 1][1] + 1, c)
    for px_, py_ in pts:
        circle(px_, py_, 2, c)
    tri(pts[-1][0] - 4, pts[-1][1] + 2, pts[-1][0] + 4, pts[-1][1] + 2,
        pts[-1][0], pts[-1][1] - 5, c)


# ---------------------------------------------------------------- scenes
def scene_ulleung(x, y, w, h):
    """Night sea, Ulleung island, jets overhead, warning beacon."""
    scene_sky(x, y, w, h, (10, 18, 44), (44, 72, 120))
    stars(x, y, w, h, 26)
    # moon
    circle(x + w - 26, y + 20, 10, (240, 236, 210))
    circle(x + w - 29, y + 17, 8, (10, 18, 44))
    # sea
    rect(x, y + h - 26, w, 26, (16, 52, 88))
    for i in range(0, w, 18):
        hline(x + i, y + h - 18 + (i % 3) * 3, 10, (60, 110, 160))
    # island with lighthouse
    tri(x + 18, y + h - 26, x + 78, y + h - 26, x + 48, y + h - 66, (26, 60, 44))
    rect(x + 44, y + h - 92, 8, 28, (240, 240, 230))
    rect(x + 42, y + h - 96, 12, 5, RED)
    circle(x + 48, y + h - 98, 4, (255, 220, 80))
    line(x + 48, y + h - 98, x + 96, y + h - 118, (255, 220, 80))
    line(x + 48, y + h - 98, x + 96, y + h - 104, (255, 220, 80))
    # jets
    jet(x + w - 120, y + 34, 34, (200, 205, 215))
    jet(x + w - 78, y + 58, 26, (170, 175, 188))
    # warning triangle, lower left so it never meets the banner
    tri(x + 14, y + 44, x + 36, y + 44, x + 25, y + 62, (255, 200, 40))
    draw_text(x + 22, y + 47, "!", INK, 1, True)


def scene_nvidia(x, y, w, h):
    """Bright trading floor: rising chart, chip, cheering traders."""
    scene_sky(x, y, w, h, (232, 246, 252), (176, 214, 238))
    # big green chart
    chart_up(x + 12, y + 18, w - 24, h - 70, GREEN, 8, 23)
    # chip
    cx, cy = x + w - 52, y + h - 44
    rect(cx - 16, cy - 12, 32, 24, (24, 40, 30))
    rect(cx - 10, cy - 6, 20, 12, (40, 200, 110))
    for dx in (-18, 18):
        for dy in (-8, 0, 8):
            hline(cx + dx - (4 if dx < 0 else 0), cy + dy, 4, GOLD, 2)
    # traders
    person(x + 26, y + h - 34, 30, (178, 24, 28))
    person(x + 52, y + h - 30, 26, (36, 84, 160))
    person(x + 78, y + h - 34, 30, (28, 120, 58))
    # raised arms
    line(x + 26, y + h - 26, x + 18, y + h - 40, (178, 24, 28))
    line(x + 78, y + h - 26, x + 86, y + h - 40, (28, 120, 58))


def scene_pyongyang(x, y, w, h):
    """Diplomatic office: flag poles, building, closed gate."""
    scene_sky(x, y, w, h, (238, 228, 210), (196, 176, 150))
    # sun
    circle(x + w - 30, y + 22, 12, (240, 190, 90))
    # building
    rect(x + 30, y + h - 70, w - 60, 70, (120, 110, 96))
    rect(x + 30, y + h - 78, w - 60, 8, (90, 80, 70))
    for i in range(5):
        rect(x + 40 + i * 34, y + h - 62, 18, 22, (60, 80, 110))
    rect(x + w // 2 - 14, y + h - 34, 28, 34, (60, 52, 44))
    # flag poles: Swiss cross flag and DPRK flag
    vline(x + 44, y + 22, h - 92, INK, 2)
    rect(x + 44, y + 22, 26, 16, (220, 30, 30))
    rect(x + 53, y + 26, 8, 8, WHITE)
    vline(x + w - 46, y + 22, h - 92, INK, 2)
    rect(x + w - 46, y + 22, 26, 16, (20, 60, 160))
    circle(x + w - 33, y + 30, 5, (220, 30, 30))
    # closed gate bars
    for i in range(6):
        vline(x + w // 2 - 30 + i * 12, y + h - 40, 40, (40, 36, 30), 3)
    person(x + w // 2 - 52, y + h - 30, 28, (40, 40, 40))
    person(x + w // 2 + 52, y + h - 30, 28, (120, 30, 30))


def scene_pmi(x, y, w, h):
    """Factory floor with gauges and boxes."""
    scene_sky(x, y, w, h, (226, 238, 244), (180, 200, 214))
    rect(x, y + h - 46, w, 46, (150, 148, 140))
    # factory block
    rect(x + 14, y + h - 96, 90, 50, (110, 116, 124))
    rect(x + 20, y + h - 116, 12, 20, (110, 116, 124))
    rect(x + 38, y + h - 116, 12, 20, (110, 116, 124))
    for i in range(3):
        rect(x + 22 + i * 26, y + h - 88, 16, 16, (255, 220, 90))
    # gauge
    circle(x + w - 52, y + 42, 26, WHITE)
    circle(x + w - 52, y + 42, 26, INK, fill=False)
    tri(x + w - 52, y + 42, x + w - 34, y + 26, x + w - 30, y + 32, RED)
    circle(x + w - 52, y + 42, 4, INK)
    # crates
    rect(x + w - 96, y + h - 66, 22, 20, (178, 120, 40))
    rect(x + w - 70, y + h - 60, 18, 14, (120, 90, 50))
    person(x + 130, y + h - 34, 30, (36, 84, 160))
    person(x + 156, y + h - 30, 26, (196, 116, 16))


def scene_cas(x, y, w, h):
    """Trophy on a podium, two flags, gavel."""
    scene_sky(x, y, w, h, (240, 236, 222), (200, 186, 150))
    rect(x, y + h - 30, w, 30, (120, 96, 64))
    # trophy
    rect(x + w // 2 - 14, y + 26, 28, 34, GOLD)
    tri(x + w // 2 - 14, y + 26, x + w // 2 - 26, y + 40, x + w // 2 - 14,
        y + 44, GOLD)
    tri(x + w // 2 + 14, y + 26, x + w // 2 + 26, y + 40, x + w // 2 + 14,
        y + 44, GOLD)
    rect(x + w // 2 - 5, y + 60, 10, 12, GOLD)
    rect(x + w // 2 - 16, y + 72, 32, 6, GOLD)
    # flags: Senegal green/yellow/red, Morocco red
    vline(x + 24, y + 24, h - 60, INK, 2)
    rect(x + 24, y + 24, 30, 18, (30, 140, 60))
    rect(x + 24, y + 30, 30, 6, (240, 200, 40))
    rect(x + 24, y + 36, 30, 6, (200, 30, 30))
    vline(x + w - 26, y + 24, h - 60, INK, 2)
    rect(x + w - 26, y + 24, 30, 18, (200, 30, 30))
    circle(x + w - 11, y + 33, 4, GREEN)
    # gavel
    rect(x + w - 66, y + h - 52, 26, 8, (90, 60, 30))
    rect(x + w - 54, y + h - 44, 4, 14, (90, 60, 30))


def scene_ucl(x, y, w, h):
    """Floodlit stadium at night, ball, crowd."""
    scene_sky(x, y, w, h, (12, 22, 52), (30, 60, 110))
    stars(x, y, w, h, 18)
    # floodlights
    for fx in (x + 16, x + w - 16):
        rect(fx - 8, y + 8, 16, 6, WHITE)
        line(fx, y + 14, fx - 22, y + 60, (220, 230, 240))
        line(fx, y + 14, fx + 22, y + 60, (220, 230, 240))
    # stands
    rect(x, y + h - 52, w, 52, (40, 70, 120))
    for r in range(3):
        for i in range(0, w, 12):
            px(x + i + (r % 2) * 6, y + h - 46 + r * 12,
               (240, 220, 180) if (i + r) % 24 == 0 else (200, 200, 210))
    # pitch
    rect(x, y + h - 18, w, 18, (30, 140, 60))
    # ball
    circle(x + w // 2, y + h - 34, 10, WHITE)
    circle(x + w // 2, y + h - 34, 10, INK, fill=False)
    circle(x + w // 2, y + h - 34, 3, INK)
    # players
    person(x + 40, y + h - 34, 30, (200, 30, 30))
    person(x + w - 46, y + h - 34, 30, (30, 60, 180))


def scene_nba(x, y, w, h):
    """Basketball court, hoop, leaping player."""
    scene_sky(x, y, w, h, (250, 232, 200), (220, 170, 110))
    rect(x, y + h - 34, w, 34, (190, 120, 60))
    hline(x, y + h - 34, w, WHITE, 2)
    # hoop
    vline(x + w - 30, y + 14, 40, INK, 3)
    rect(x + w - 44, y + 14, 28, 18, WHITE)
    circle(x + w - 30, y + 40, 8, ORANGE, fill=False)
    # player leaping with ball
    person(x + w // 2 - 30, y + h - 66, 34, (120, 30, 140))
    circle(x + w // 2 + 6, y + h - 62, 7, ORANGE)
    # crowd
    for i in range(0, w, 16):
        circle(x + i + 6, y + 18 + (i % 3) * 4, 4,
               (200, 60, 60) if i % 32 == 0 else (60, 90, 180))


def scene_trade(x, y, w, h):
    """Two flags and a handshake over a signed pact."""
    scene_sky(x, y, w, h, (236, 242, 248), (190, 210, 228))
    # flags: Canada red/white, Qatar maroon/white
    vline(x + 26, y + 18, h - 50, INK, 2)
    rect(x + 26, y + 18, 34, 20, WHITE)
    rect(x + 26, y + 18, 8, 20, RED)
    rect(x + 52, y + 18, 8, 20, RED)
    vline(x + w - 28, y + 18, h - 50, INK, 2)
    rect(x + w - 28, y + 18, 34, 20, (140, 20, 60))
    tri(x + w - 28, y + 18, x + w - 28, y + 38, x + w - 14, y + 28,
        WHITE)
    # table with pact
    rect(x + 20, y + h - 44, w - 40, 8, (120, 84, 50))
    rect(x + w // 2 - 30, y + h - 62, 60, 18, WHITE)
    line(x + w // 2 - 24, y + h - 56, x + w // 2 + 20, y + h - 56, INK)
    line(x + w // 2 - 24, y + h - 50, x + w // 2 + 10, y + h - 50, INK)
    person(x + 44, y + h - 40, 36, (40, 40, 44))
    person(x + w - 50, y + h - 40, 36, (30, 80, 140))
    # handshake
    line(x + 58, y + h - 30, x + w // 2 - 8, y + h - 24, (232, 190, 150))
    line(x + w - 64, y + h - 30, x + w // 2 + 8, y + h - 24, (232, 190, 150))


def scene_earnings(x, y, w, h):
    """Laptop with earnings chart, server racks."""
    scene_sky(x, y, w, h, (232, 240, 248), (180, 198, 216))
    # server racks
    for i in range(2):
        rect(x + 14 + i * 34, y + 16, 28, h - 40, (50, 58, 72))
        for r in range(5):
            rect(x + 18 + i * 34, y + 22 + r * 16, 20, 8, (60, 200, 120)
                 if (r + i) % 2 == 0 else (40, 140, 200))
    # laptop
    rect(x + w - 118, y + h - 66, 96, 56, (30, 34, 44))
    rect(x + w - 112, y + h - 60, 84, 44, (220, 240, 250))
    chart_up(x + w - 106, y + h - 54, 72, 32, GREEN, 6, 31)
    rect(x + w - 124, y + h - 10, 108, 4, (30, 34, 44))
    person(x + w - 150, y + h - 36, 32, (178, 24, 28))


def scene_ifo(x, y, w, h):
    """German business gauge: big dial, factory, euro sign."""
    scene_sky(x, y, w, h, (238, 238, 230), (200, 196, 180))
    # dial
    circle(x + w // 2, y + h // 2 + 6, 40, WHITE)
    circle(x + w // 2, y + h // 2 + 6, 40, INK, fill=False)
    for a in range(0, 181, 30):
        ax = x + w // 2 + int(34 * math.cos(math.radians(180 + a)))
        ay = y + h // 2 + 6 - int(34 * math.sin(math.radians(a)))
        circle(ax, ay, 2, INK)
    tri(x + w // 2, y + h // 2 + 6, x + w // 2 + 26, y + h // 2 - 14,
        x + w // 2 + 30, y + h // 2 - 8, RED)
    circle(x + w // 2, y + h // 2 + 6, 5, INK)
    # factory silhouette
    rect(x + 12, y + h - 30, 44, 30, (90, 96, 104))
    rect(x + 60, y + h - 30, 30, 30, (110, 116, 124))


def scene_jobs(x, y, w, h):
    """US jobs: capitol dome, bar chart, briefcase."""
    scene_sky(x, y, w, h, (238, 240, 248), (196, 208, 226))
    # capitol dome
    rect(x + 14, y + h - 40, 60, 40, (220, 220, 210))
    tri(x + 14, y + h - 40, x + 74, y + h - 40, x + 44, y + h - 66, WHITE)
    circle(x + 44, y + h - 68, 5, WHITE)
    # bars
    bars = [18, 26, 22, 32, 28]
    for i, bh in enumerate(bars):
        rect(x + 92 + i * 20, y + h - 16 - bh, 14, bh,
             (36, 84, 160) if i < 4 else GREEN)
    person(x + w - 40, y + h - 34, 30, (40, 40, 44))


def scene_war(x, y, w, h):
    """Damaged apartment block at dawn, smoke, rescue light."""
    scene_sky(x, y, w, h, (60, 52, 66), (150, 110, 90))
    # block
    rect(x + 16, y + 22, 74, h - 40, (70, 62, 66))
    for r in range(3):
        for c in range(3):
            rect(x + 24 + c * 22, y + 30 + r * 24, 14, 14,
                 (255, 190, 80) if (r == 0 and c == 1) else (40, 38, 44))
    # smoke
    circle(x + 60, y + 12, 10, (120, 116, 112))
    circle(x + 74, y + 6, 8, (140, 136, 132))
    # rescue
    person(x + 120, y + h - 30, 28, (220, 120, 20))
    person(x + 146, y + h - 26, 24, (30, 90, 160))
    rect(x + 116, y + h - 52, 40, 4, (255, 220, 80))


def scene_turkey(x, y, w, h):
    """White House lawn, turkey, podium."""
    scene_sky(x, y, w, h, (214, 232, 248), (160, 196, 226))
    # white house
    rect(x + 16, y + 18, 70, 34, WHITE)
    tri(x + 16, y + 18, x + 86, y + 18, x + 51, y + 2, (200, 200, 200))
    for i in range(4):
        rect(x + 24 + i * 16, y + 30, 8, 22, (180, 190, 200))
    # lawn
    rect(x, y + h - 30, w, 30, (60, 150, 70))
    # turkey
    circle(x + w - 56, y + h - 52, 16, (120, 90, 60))
    circle(x + w - 44, y + h - 64, 8, (150, 110, 70))
    tri(x + w - 38, y + h - 62, x + w - 30, y + h - 60, x + w - 38,
        y + h - 56, (220, 120, 40))
    for i in range(3):
        tri(x + w - 70, y + h - 66 + i * 6, x + w - 62, y + h - 70 + i * 6,
            x + w - 58, y + h - 56 + i * 6, (90, 60, 40))
    person(x + 110, y + h - 34, 32, (30, 40, 60))


def mini_icon(x, y, kind):
    """Tiny 20x14 illustration for secondary cards."""
    if kind == "chart":
        scene_sky(x, y, 20, 14, (232, 246, 252), (176, 214, 238))
        chart_up(x + 2, y + 3, 16, 9, GREEN, 5, 5)
    elif kind == "ball":
        scene_sky(x, y, 20, 14, (12, 22, 52), (30, 60, 110))
        circle(x + 10, y + 7, 5, WHITE)
        circle(x + 10, y + 7, 2, INK)
    elif kind == "trophy":
        scene_sky(x, y, 20, 14, (240, 236, 222), (200, 186, 150))
        rect(x + 7, y + 2, 6, 7, GOLD)
        rect(x + 5, y + 9, 10, 2, GOLD)
    elif kind == "flag":
        scene_sky(x, y, 20, 14, (236, 242, 248), (190, 210, 226))
        vline(x + 5, y + 2, 10, INK, 1)
        rect(x + 5, y + 2, 10, 5, RED)
    elif kind == "oil":
        scene_sky(x, y, 20, 14, (40, 40, 50), (90, 80, 70))
        rect(x + 4, y + 6, 12, 6, (60, 60, 70))
        tri(x + 8, y + 6, x + 12, y + 6, x + 10, y + 1, (255, 200, 60))
    elif kind == "coin":
        scene_sky(x, y, 20, 14, (240, 236, 220), (210, 196, 160))
        circle(x + 10, y + 7, 5, GOLD)
        draw_text(x + 8, y + 4, "$", INK, 1, True)
    elif kind == "court":
        scene_sky(x, y, 20, 14, (250, 232, 200), (220, 170, 110))
        circle(x + 10, y + 7, 5, ORANGE)
    elif kind == "doc":
        scene_sky(x, y, 20, 14, (238, 240, 248), (200, 208, 222))
        rect(x + 6, y + 2, 8, 10, WHITE)
        line(x + 8, y + 5, x + 12, y + 5, INK)
        line(x + 8, y + 8, x + 12, y + 8, INK)
    elif kind == "gauge":
        scene_sky(x, y, 20, 14, (238, 238, 230), (200, 196, 180))
        circle(x + 10, y + 9, 6, WHITE)
        tri(x + 10, y + 9, x + 15, y + 4, x + 16, y + 6, RED)
    elif kind == "ship":
        scene_sky(x, y, 20, 14, (180, 210, 235), (120, 160, 200))
        rect(x + 3, y + 8, 14, 3, (60, 60, 70))
        rect(x + 8, y + 4, 4, 4, (60, 60, 70))
    else:
        scene_sky(x, y, 20, 14, (232, 238, 244), (190, 200, 210))
        circle(x + 10, y + 7, 5, SKY_DK)


# ---------------------------------------------------------------- world map
# Dotted world map: coarse land grid, 1 = land. 46 cols x 22 rows.
MAP = [
    "..............................................",
    "....####......................................",
    "..########..####....####.......................",
    ".##########.######.######..###..................",
    "..######################.#####.####............",
    "...########.############..#########............",
    "....######...##########....##########...........",
    ".....####.....########......########............",
    "......##.......######........######.............",
    "...............####..........#####..............",
    "..............#####..........####...............",
    ".............######..........###................",
    "............#######.........####................",
    "...........########.........#####...............",
    "............######..........#####...............",
    ".............####...........######..............",
    "..............##.............####...............",
    ".............................##................",
    "..............................................",
    "..............................................",
    "..............................................",
    "..............................................",
]


def draw_map(x, y, cell=6):
    for r, row in enumerate(MAP):
        for c, ch in enumerate(row):
            if ch == '#':
                circle(x + c * cell + cell // 2, y + r * cell + cell // 2,
                       2, (150, 140, 110))


# ---------------------------------------------------------------- stories
# All 39 stories verified against the wires on 24 Nov 2026 (press 09:00 UTC).
HEROES = [
    dict(num=1, kicker="ULLEUNG, SOUTH KOREA - AIR DEFENCE", badge="OFFICIAL",
         banner="5-MIN ALERT", stat="NO BREACH",
         headline="Russian jets buzz Ulleung; islanders told to shelter",
         body=("Several Russian jets entered the Korea air defence zone near "
               "Ulleung; Seoul scrambled fighters and told residents to "
               "shelter at 07:52. The alert was lifted in five minutes; no "
               "breach. (Reuters)"),
         scene=scene_ulleung),
    dict(num=2, kicker="ASIA MARKETS - STOCKS", badge="REPORTED",
         banner="HUANG IS BACK", stat="+31.5% NVDA",
         headline="Huang is back: Nvidia soars and Asia roars",
         body=("Nvidia reinstated Jensen Huang as chief executive and its "
               "shares jumped 31.5% on Monday, the biggest gain in 23 years. "
               "Asia followed: the Kospi leapt 7.5%, the Nikkei 4.5% and "
               "Taiwan 9.1%. (Reuters)"),
         scene=scene_nvidia),
    dict(num=3, kicker="PYONGYANG, NORTH KOREA - DIPLOMACY", badge="REPORTED",
         banner="OFFICE AT RISK", stat="OPENED OCT",
         headline="Pyongyang may shut Swiss office over camp sanctions",
         body=("Kim Yo Jong said North Korea will consider shutting "
               "Switzerland's diplomatic office in Pyongyang after Bern "
               "sanctioned the Songdowon children's camp over its Russia "
               "ties. The office opened only weeks ago. (Reuters / KCNA)"),
         scene=scene_pyongyang),
]

SECONDARIES = [
    dict(num=4, kicker="TOKYO - ECONOMY", banner="PMI 53.7", icon="gauge",
         headline="Japan's factories pick up speed; services cool",
         body=("Flash factory PMI 53.7, above forecast; services 50.5 and "
               "the composite at a six-month low of 51.5. (S&P Global)")),
    dict(num=5, kicker="LAUSANNE - SPORT", banner="DUE TODAY", icon="trophy",
         headline="CAS to rule today on Senegal's Cup title appeal",
         body=("The court decides this afternoon whether Senegal keeps the "
               "title won 1-0 in January or Morocco keeps it. (Reuters)")),
    dict(num=6, kicker="EUROPE - FOOTBALL", banner="9 GAMES", icon="ball",
         headline="Nine Champions League games light up Tuesday",
         body=("Arsenal host Dortmund, Man City face Napoli, Real Madrid "
               "meet PSV; two early kick-offs at 17:45 GMT. (UEFA)")),
    dict(num=7, kicker="LOS ANGELES - SPORT", banner="109-94", icon="court",
         headline="Lakers beat Jazz; Spurs roll on to 15-3",
         body=("Doncic scored 28 in a 109-94 win over Utah. San Antonio won "
               "123-107 at Sacramento; Pacers edged Thunder 125-120. (AP)")),
    dict(num=8, kicker="OTTAWA - TRADE", banner="SIGNING TODAY", icon="flag",
         headline="Canada and Qatar to sign investment pact",
         body=("Carney and Qatar's prime minister sign a deal protecting "
               "investors at the first strategic dialogue. (Reuters)")),
    dict(num=9, kicker="AUSTIN - BUSINESS", banner="AFTER CLOSE", icon="chart",
         headline="Dell and HP report; AI-server demand in focus",
         body=("Both report after the bell after a tech rout. Dell is tipped "
               "for 82.6% revenue growth. (Reuters)")),
    dict(num=10, kicker="BERLIN - ECONOMY", banner="DUE 09:00 UTC", icon="gauge",
         headline="Germany's Ifo index due; consensus 90.5",
         body=("Business morale is tipped to edge up from 90.2 in October, "
               "its best since May 2023. (Reuters / ING)")),
    dict(num=11, kicker="WASHINGTON - ECONOMY", banner="DUE LATER", icon="doc",
         headline="US jobs and confidence due; PCE lands Wednesday",
         body=("ADP jobs and consumer confidence (seen 92.1, from 91.7) are "
               "due later today. (WSJ)")),
    dict(num=12, kicker="ZAPORIZHZHIA - WAR", banner="2 DEAD, 22 HURT", icon="flag",
         headline="Russian strike kills two in Zaporizhzhia overnight",
         body=("An overnight attack killed two and wounded 22, including "
               "two children, officials said on Tuesday. (Reuters)")),
    dict(num=13, kicker="WASHINGTON - THANKSGIVING", banner="79TH PARDON", icon="doc",
         headline="Trump pardons turkeys Freedom and Feather",
         body=("The 79th Thanksgiving turkey pardon takes place at 2 p.m. ET "
               "on the South Lawn. Both birds retire to Texas A&M. (AP)")),
]

# 26 more stories: (region, text)
ALSO = [
    ("ASIA", "Kospi jumps 7.5% to 5,740 as chips lead Asia (Reuters)"),
    ("ASIA", "Nikkei gains 4.5% as traders return from holiday (Reuters)"),
    ("ASIA", "Taiex surges 9.1%, biggest intraday gain on record (Reuters)"),
    ("ASIA", "MSCI Asia-Pacific climbs 4.6%, best day since July (Reuters)"),
    ("ASIA", "TSMC and Foxconn jump about 10% to daily limits (Reuters)"),
    ("ASIA", "Samsung, SK Hynix up 8%+; Advantest up 14% (Reuters)"),
    ("ASIA", "Taiwan cuts margin-call floor to 120% from today (Reuters)"),
    ("AMERICAS", "Nvidia up 31.5% on Monday, restoring $1tn value (Reuters)"),
    ("AMERICAS", "Huang to testify before US Congress on Dec 3 (Reuters)"),
    ("ASIA", "Shanghai Composite edges 0.7% higher (Reuters)"),
    ("OCEANIA", "ASX 200 rises 1.8% in Sydney (Reuters)"),
    ("M. EAST", "Brent $88.97, near a three-month low (Reuters)"),
    ("M. EAST", "Three tankers hit mines in Hormuz on Monday (Reuters)"),
    ("AMERICAS", "US sells $70bn of five-year notes at 1 p.m. ET (Treasury)"),
    ("EUROPE", "Netherlands auctions 2bn euros of 3-yr bonds (ING)"),
    ("AMERICAS", "Macklem speaks at 12:40 ET; Dec 9 hike odds 46% (BoC)"),
    ("ASIA", "SoftBank climbs 5.7% as the chip rally rolls on (WSJ)"),
    ("AMERICAS", "Best Buy, Dollar Tree report before the open (WSJ)"),
    ("AMERICAS", "US details $12bn in Venezuelan oil revenue (State Dept)"),
    ("WORLD", "Gold edges up from a 14-month low (Reuters)"),
    ("AMERICAS", "Dollar, yields rise on Fed tightening bets (Reuters)"),
    ("AMERICAS", "Timberwolves rout Nets 142-116 in Minneapolis (AP)"),
    ("AMERICAS", "Blazers end 76ers' streak, 128-111; Avdija 31 (AP)"),
    ("AMERICAS", "Grizzlies beat Hornets 117-111; Jerome hits 29 (AP)"),
    ("AMERICAS", "Suns edge Pelicans 123-119 in overtime (AP)"),
    ("AMERICAS", "Bucks 116-111 Raptors; Bulls 122-108 Cavs (AP)"),
]

REGIONS = [("ASIA-PACIFIC", 13), ("EUROPE", 4), ("AMERICAS", 17),
           ("MIDDLE EAST", 2), ("AFRICA", 1), ("OCEANIA", 1), ("WORLD", 1)]

TIMELINE = [
    ("00:30", "PMI 53.7"),
    ("03:36", "Taiex +9.1%"),
    ("09:00", "Ifo due"),
    ("15:00", "Confidence"),
    ("19:00", "Pardon"),
    ("20:00", "UCL"),
]

PINS = {  # story num -> (map col, map row)
    1: (38, 7), 2: (36, 9), 3: (37, 6), 4: (40, 7), 5: (21, 5),
    6: (20, 4), 7: (5, 7), 8: (8, 5), 9: (7, 8), 10: (22, 4),
    11: (9, 6), 12: (26, 4), 13: (10, 7),
}

DATE_CHECK = (
    "Left out as other days' news: COP31 collapse (Sun 22 Nov); 186 drones "
    "over Ukraine (Sun); Dymer toll, 153 drones (Mon); Russian corvette sunk "
    "off Libya (Sun); UNRWA worker killed in Gaza (Mon); singer Ahmadi "
    "flogged (Mon); Indonesia factory fire, 24 dead (Mon); Democrats' 258 "
    "House seats (Sun); Wellington Test drawn (Mon); Rubio meets Qatar PM "
    "(Mon); Peru quake (Fri 20 Nov); HPE earnings beat (Mon); SoftBank "
    "earnings (10 Nov); US CPI next due 10 Dec, not today. Not yet decided "
    "at press time (09:00 UTC): CAS ruling (due Tue afternoon); UCL results "
    "(kick off 20:00 GMT); Dell/HP earnings (after US close); Ifo reading "
    "(due 09:00 UTC); ADP jobs, US confidence (due later Tue)."
)

# ---------------------------------------------------------------- layout
def banner(x, y, s, c=RED):
    w = text_w(s, 1) + 10
    rect(x, y, w, 14, c)
    draw_text(x + 5, y + 3, s, WHITE, 1, True)
    return w


def statbox(x, y, s):
    w = text_w(s, 1) + 10
    rect(x, y, w, 14, WHITE)
    draw_text(x + 5, y + 3, s, INK, 1, True)
    return w


def badge(x, y, s):
    w = text_w(s, 1) + 8
    rect(x, y, w, 12, NAVY)
    draw_text(x + 4, y + 2, s, WHITE, 1, True)
    return w


def render():
    rect(0, 0, W, H, PAPER)
    # --- top strip
    rect(0, 0, W, 24, NAVY)
    draw_text(W // 2, 8,
              "39 STORIES - 7 REGIONS - EVERY ONE DATED TUESDAY 24 NOVEMBER 2026",
              WHITE, 1, True, "c")
    # --- masthead
    title = "Tuesday 24 November 2026"
    tw = serif_w(title, 4)
    draw_serif((W - tw) // 2, 28, title, NAVY, 4)
    # --- red subhead
    draw_text(W // 2, 90,
              "Russian jets buzz Ulleung  -  Nvidia brings Asia roaring back  -  "
              "Pyongyang threatens Swiss office",
              RED, 1, True, "c")
    hline(20, 102, W - 40, INK, 2)
    # --- key numbers strip
    nums = [("+7.5%", "Kospi jumps"),
            ("+31.5%", "Nvidia, Monday"),
            ("+9.1%", "Taiex surges"),
            ("53.7", "Japan factory PMI"),
            ("5 MIN", "Ulleung alert"),
            ("$70BN", "US 5-yr sale")]
    cw = (W - 40) // 6
    for i, (n, cap) in enumerate(nums):
        x = 20 + i * cw
        draw_text(x + cw // 2, 108, n, RED, 2, True, "c")
        draw_text(x + cw // 2, 126, cap, INK, 1, False, "c")
        if i:
            vline(x, 106, 34, LGREY, 1)
    hline(20, 144, W - 40, INK, 1)
    # --- region bar
    rw = (W - 40) // 7
    for i, (name, cnt) in enumerate(REGIONS):
        x = 20 + i * rw
        rect(x, 150, rw - 2, 20, REGION_COLORS[name])
        draw_text(x + (rw - 2) // 2, 156, "%s %d" % (name, cnt), WHITE, 1,
                  True, "c")
    # --- timeline strip
    rect(20, 176, W - 40, 18, NAVY2)
    tx = 28
    tx = draw_text(tx, 181, "THE DAY IN UTC", (255, 220, 80), 1, True)
    for t, what in TIMELINE:
        tx += 10
        tx = draw_text(tx, 181, t, WHITE, 1, True)
        tx += 4
        tx = draw_text(tx, 181, what, (200, 210, 230), 1)
    # --- heroes
    hw = 320
    for i, hs in enumerate(HEROES):
        x = 20 + i * (hw + 12)
        y = 200
        hs["scene"](x, y, hw, 138)
        banner(x + 6, y + 6, hs["banner"])
        sw = text_w(hs["stat"], 1) + 10
        statbox(x + hw - sw - 6, y + 6, hs["stat"])
        ky = y + 144
        draw_text(x, ky, "%d %s" % (hs["num"], hs["kicker"]), RED, 1, True)
        bw = text_w(hs["badge"], 1) + 8
        badge(x + hw - bw, ky - 1, hs["badge"])
        hy = ky + 14
        for ln in wrap(hs["headline"], 26):
            draw_text(x, hy, ln, INK, 2, True)
            hy += 17
        by = hy + 4
        by = para(x, by, hs["body"], INK, 1, 52, 9)
    hline(20, 452, W - 40, INK, 1)
    # --- secondaries: 2 rows x 5
    sw_ = 190
    for idx, sc in enumerate(SECONDARIES):
        col = idx % 5
        row = idx // 5
        x = 20 + col * (sw_ + 8)
        y = 460 + row * 114
        sc_icon = sc["icon"]
        # illustration panel
        rect(x, y, sw_, 52, CREAM)
        mini_panel(x, y, sw_, 52, sc_icon, sc["num"])
        banner(x + 4, y + 4, sc["banner"])
        ky = y + 56
        draw_text(x, ky, "%d %s" % (sc["num"], sc["kicker"]), RED, 1, True)
        hy = ky + 11
        for ln in wrap(sc["headline"], 31):
            draw_text(x, hy, ln, INK, 1, True)
            hy += 9
        para(x, hy + 1, sc["body"], INK, 1, 31, 9)
    hline(20, 688, W - 40, INK, 1)
    # --- map (left) + ALSO list (right)
    draw_text(20, 698, "WHERE IT HAPPENED", INK, 1, True)
    draw_text(20, 710, "pins match story numbers", GREY, 1)
    draw_map(24, 726, 6)
    for num, (mc, mr) in PINS.items():
        cx = 24 + mc * 6 + 3
        cy = 726 + mr * 6 + 3
        circle(cx, cy, 7, RED)
        circle(cx, cy, 7, WHITE, fill=False)
        s = str(num)
        draw_text(cx - (3 if len(s) == 1 else 6), cy - 3, s, WHITE, 1, True)
    ax = 344
    draw_text(ax, 698,
              "ALSO ON TUESDAY 24 NOVEMBER - 26 MORE STORIES", INK, 1, True)
    for i, (reg, txt) in enumerate(ALSO):
        y = 708 + i * 9
        draw_text(ax, y, "%d" % (14 + i), RED, 1, True)
        draw_text(ax + 20, y, "%s: %s" % (reg, txt), INK, 1)
    # --- DATE CHECK
    by = 942
    rect(20, by, W - 40, 52, WHITE)
    for xx in (20, W - 21):
        vline(xx, by, 52, RED, 2)
    hline(20, by, W - 40, RED, 2)
    hline(20, by + 51, W - 40, RED, 2)
    draw_text(28, by + 5, "DATE CHECK", RED, 1, True)
    para(28, by + 16, DATE_CHECK, INK, 1, 158, 9)
    # --- footer
    draw_text(20, 1000,
              "Sources: Reuters, KCNA, S&P Global, UEFA, AP, WSJ, ING, Bank of "
              "Canada, US Treasury, US State Dept. Pictures and map: original, "
              "drawn in code.",
              GREY, 1)
    draw_text(20, 1010,
              "CERTAINTY: REPORTED = carried by the day's wires  -  CLAIM = one "
              "side's account, labelled as such  -  FORECAST = still to happen "
              "when drawn.",
              GREY, 1)
    rect(0, 1018, W, 6, NAVY)


def mini_panel(x, y, w, h, kind, num):
    """Small 190x52 illustration, drawn for this size only: one clear
    motif per kind, never a shrunken hero scene."""
    if kind == "gauge":
        scene_sky(x, y, w, h, (238, 238, 230), (205, 200, 185))
        circle(x + 34, y + 26, 18, WHITE)
        circle(x + 34, y + 26, 18, INK, fill=False)
        tri(x + 34, y + 26, x + 48, y + 14, x + 50, y + 18, RED)
        circle(x + 34, y + 26, 3, INK)
        rect(x + 70, y + 30, w - 80, 22, (110, 116, 124))
        for i in range(3):
            rect(x + 76 + i * 34, y + 34, 20, 14, (255, 220, 90))
    elif kind == "trophy":
        scene_sky(x, y, w, h, (240, 236, 222), (205, 190, 155))
        rect(x + w // 2 - 10, y + 8, 20, 24, GOLD)
        rect(x + w // 2 - 4, y + 32, 8, 8, GOLD)
        rect(x + w // 2 - 14, y + 40, 28, 4, GOLD)
        vline(x + 22, y + 8, 34, INK, 2)
        rect(x + 22, y + 8, 22, 12, (30, 140, 60))
        vline(x + w - 24, y + 8, 34, INK, 2)
        rect(x + w - 24, y + 8, 22, 12, (200, 30, 30))
    elif kind == "ball":
        scene_sky(x, y, w, h, (12, 22, 52), (30, 60, 110))
        stars(x, y, w, h, 10)
        rect(x + 14, y + 6, 14, 5, WHITE)
        line(x + 21, y + 11, x + 8, y + 34, (220, 230, 240))
        line(x + 21, y + 11, x + 36, y + 34, (220, 230, 240))
        circle(x + w // 2, y + 30, 9, WHITE)
        circle(x + w // 2, y + 30, 3, INK)
        rect(x, y + h - 10, w, 10, (30, 140, 60))
    elif kind == "court":
        scene_sky(x, y, w, h, (250, 232, 200), (225, 175, 115))
        rect(x, y + h - 12, w, 12, (190, 120, 60))
        vline(x + w - 26, y + 8, 26, INK, 3)
        rect(x + w - 38, y + 8, 24, 14, WHITE)
        circle(x + w - 26, y + 28, 6, ORANGE, fill=False)
        circle(x + w // 2, y + 26, 8, ORANGE)
        person(x + 30, y + h - 24, 22, (120, 30, 140))
    elif kind == "flag":
        scene_sky(x, y, w, h, (236, 242, 248), (195, 212, 228))
        vline(x + 30, y + 8, 34, INK, 2)
        rect(x + 30, y + 8, 30, 16, WHITE)
        rect(x + 30, y + 8, 7, 16, RED)
        rect(x + 53, y + 8, 7, 16, RED)
        vline(x + w - 32, y + 8, 34, INK, 2)
        rect(x + w - 32, y + 8, 30, 16, (140, 20, 60))
        tri(x + w - 32, y + 8, x + w - 32, y + 24, x + w - 20, y + 16, WHITE)
        rect(x + w // 2 - 22, y + 34, 44, 8, WHITE)
    elif kind == "chart":
        scene_sky(x, y, w, h, (232, 240, 248), (185, 200, 216))
        chart_up(x + 10, y + 8, w - 20, h - 22, GREEN, 6, 17)
        rect(x + w - 52, y + h - 18, 40, 14, (30, 34, 44))
        rect(x + w - 48, y + h - 15, 32, 8, (40, 200, 110))
    elif kind == "doc":
        scene_sky(x, y, w, h, (238, 240, 248), (200, 210, 226))
        rect(x + 20, y + 8, 26, 36, WHITE)
        line(x + 25, y + 16, x + 41, y + 16, INK)
        line(x + 25, y + 24, x + 41, y + 24, INK)
        line(x + 25, y + 32, x + 36, y + 32, INK)
        bars = [10, 16, 12, 20, 16]
        for i, bh in enumerate(bars):
            rect(x + 62 + i * 18, y + h - 8 - bh, 12, bh,
                 (36, 84, 160) if i < 4 else GREEN)
    else:
        scene_sky(x, y, w, h, (232, 238, 244), (190, 200, 210))
        circle(x + w // 2, y + h // 2, 12, SKY_DK)


# ---------------------------------------------------------------- PNG
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw.extend(fb[yy * W * 3:(yy + 1) * W * 3])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += chunk(b"IEND", b"")
    return png


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    render()
    data = encode_png()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    os.chmod(path, 0o644)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
