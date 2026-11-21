#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Draws one uncaptioned open passport spread for the invented Republic of
Talveria, using only the Python standard library. The program is fully
deterministic: fixed data, no randomness, no time, no network, no external
input. It writes a single PNG to <output>/entry.png (output dir overridable
with the MAKEFUN_OUTPUT_DIR environment variable, default /output).
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Every glyph is 7 rows of 5 bits. All text is rendered in
# capitals (passports print their data in capitals), so lowercase letters map
# to the same glyphs. Only real words are ever drawn.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
PAPER = (246, 241, 227)      # cream passport paper
PAPER_DARK = (238, 231, 212)
INK = (31, 42, 68)           # navy ink for text and rules
INK_SOFT = (90, 96, 110)     # grey-navy for field labels
BURGUNDY = (122, 34, 48)
GOLD = (176, 141, 74)
PHOTO_BG = (207, 216, 221)
SKIN = (217, 169, 134)
HAIR = (74, 50, 38)
GARMENT = (42, 58, 92)
MRZ_BG = (226, 222, 208)
STAMP_BLUE = (42, 77, 143)
STAMP_GREEN = (46, 107, 79)
STAMP_PURPLE = (91, 58, 117)


def text_width(s, scale):
    """Pixel width of a string at the given scale (float allowed)."""
    return int(round(len(s) * 6 * scale))


# ---------------------------------------------------------------------------
# Canvas: plain RGB bytearray with simple drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        for i in range(0, len(self.buf), 3):
            self.buf[i] = bg[0]
            self.buf[i + 1] = bg[1]
            self.buf[i + 2] = bg[2]

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def blend(self, x, y, color, alpha):
        """Alpha-blend a colour over the canvas (alpha 0..255)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            a = alpha / 255.0
            self.buf[i] = int(round(self.buf[i] * (1 - a) + color[0] * a))
            self.buf[i + 1] = int(round(self.buf[i + 1] * (1 - a) + color[1] * a))
            self.buf[i + 2] = int(round(self.buf[i + 2] * (1 - a) + color[2] * a))

    def fill_rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                i = base + (xx - max(0, x)) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def blend_rect(self, x, y, w, h, color, alpha):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.blend(xx, yy, color, alpha)

    def line(self, x0, y0, x1, y1, color, width=1):
        """Bresenham line, optionally thickened."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            if width <= 1:
                self.px(x, y, color)
            else:
                r = width // 2
                for yy in range(y - r, y + r + 1):
                    for xx in range(x - r, x + r + 1):
                        self.px(xx, yy, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def rect_outline(self, x, y, w, h, color, width=1):
        self.line(x, y, x + w, y, color, width)
        self.line(x, y + h, x + w, y + h, color, width)
        self.line(x, y, x, y + h, color, width)
        self.line(x + w, y, x + w, y + h, color, width)

    def ellipse_fill(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            t = (yy - cy) / ry
            if abs(t) > 1:
                continue
            dx = int(round(rx * math.sqrt(1 - t * t)))
            for xx in range(cx - dx, cx + dx + 1):
                self.px(xx, yy, color)

    def ellipse_outline(self, cx, cy, rx, ry, color, width=1):
        steps = max(64, int(2 * math.pi * max(rx, ry)))
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            p = (int(round(cx + rx * math.cos(a))),
                 int(round(cy + ry * math.sin(a))))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], color, width)
            prev = p

    def poly_fill(self, points, color):
        """Scanline polygon fill."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for xx in range(int(round(xs[j])), int(round(xs[j + 1])) + 1):
                    self.px(xx, yy, color)

    # -- text ---------------------------------------------------------------
    def text(self, s, x, y, scale, color, angle=0.0):
        """Draw a string. scale may be a float. angle rotates clockwise in
        degrees around the string's top-left corner. Returns pixel width."""
        rad = math.radians(angle)
        ca, sa = math.cos(rad), math.sin(rad)
        adv = 6 * scale
        cell = max(1, int(round(scale)))
        ox = 0.0
        for ch in s.upper():
            glyph = FONT.get(ch)
            if glyph:
                for gy, row in enumerate(glyph):
                    for gx, bit in enumerate(row):
                        if bit == "1":
                            lx = ox + gx * scale
                            ly = gy * scale
                            rx = lx * ca - ly * sa
                            ry = lx * sa + ly * ca
                            self.fill_rect(int(round(x + rx)),
                                           int(round(y + ry)),
                                           cell, cell, color)
            ox += adv
        return int(round(ox))

    def text_centered(self, s, cx, cy, scale, color, angle=0.0):
        w = text_width(s, scale)
        return self.text(s, cx - w // 2, cy, scale, color, angle)

    # -- rotated rectangles (stamps) ----------------------------------------
    def rotated_rect_outline(self, cx, cy, w, h, angle, color, width=2):
        rad = math.radians(angle)
        ca, sa = math.cos(rad), math.sin(rad)

        def rot(dx, dy):
            return (int(round(cx + dx * ca - dy * sa)),
                    int(round(cy + dx * sa + dy * ca)))

        hw, hh = w // 2, h // 2
        corners = [rot(-hw, -hh), rot(hw, -hh), rot(hw, hh), rot(-hw, hh)]
        for i in range(4):
            a = corners[i]
            b = corners[(i + 1) % 4]
            self.line(a[0], a[1], b[0], b[1], color, width)

    def rotated_text(self, s, cx, cy, scale, color, angle):
        """Draw text centred on (cx, cy), rotated by angle degrees."""
        w = text_width(s, scale)
        h = int(round(7 * scale))
        # start from top-left of the unrotated box, then rotate about centre
        rad = math.radians(angle)
        ca, sa = math.cos(rad), math.sin(rad)
        sx = -w / 2.0 * ca + h / 2.0 * sa
        sy = -w / 2.0 * sa - h / 2.0 * ca
        self.text(s, cx + int(round(sx)), cy + int(round(sy)), scale, color, angle)


# ---------------------------------------------------------------------------
# Machine-readable zone (ICAO 9303) with real check digits.
# ---------------------------------------------------------------------------
def mrz_check(s):
    values = {c: i for i, c in enumerate("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
    total = 0
    for i, ch in enumerate(s):
        v = 0 if ch == "<" else values[ch]
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = ("P<TAL" + "VARKOVA<<ELIN").ljust(44, "<")
    doc = "TV1234567"
    dob = "910314"
    exp = "330612"
    personal = "<" * 14
    body = (doc + mrz_check(doc) + "TAL" + dob + mrz_check(dob) + "F"
            + exp + mrz_check(exp) + personal + mrz_check(personal))
    line2 = body + mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44
    return line1, line2


# ---------------------------------------------------------------------------
# Drawing helpers for the spread
# ---------------------------------------------------------------------------
def draw_emblem(c, cx, top):
    """Talveria's arms: a burgundy shield, a gold star, three white waves."""
    # shield outline
    pts = [(cx - 22, top), (cx + 22, top), (cx + 22, top + 26),
           (cx, top + 46), (cx - 22, top + 26)]
    c.poly_fill(pts, BURGUNDY)
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        c.line(a[0], a[1], b[0], b[1], INK, 2)
    # gold star
    star = []
    for i in range(10):
        r = 7 if i % 2 == 0 else 3
        a = -math.pi / 2 + i * math.pi / 5
        star.append((int(round(cx + r * math.cos(a))),
                     int(round(top + 12 + r * math.sin(a)))))
    c.poly_fill(star, GOLD)
    # three waves
    for k, wy in enumerate((top + 26, top + 31, top + 36)):
        for xx in range(cx - 15, cx + 16):
            yy = wy + int(round(2 * math.sin((xx - (cx - 15)) / 5.0 + k)))
            c.px(xx, yy, (250, 246, 236))


def draw_portrait(c, x, y, w, h):
    """Stylised line portrait of Elin Varkova: dark hair in a bun, navy dress,
    plain light background with a faint guilloche."""
    c.fill_rect(x, y, w, h, PHOTO_BG)
    # faint diagonal guilloche
    for d in range(-h, w, 12):
        c.line(x + d, y, x + d + h, y + h, (196, 206, 212), 1)
    cx = x + w // 2
    # shoulders / garment
    c.poly_fill([(x + 8, y + h), (x + w - 8, y + h),
                 (x + w - 28, y + h - 52), (x + 28, y + h - 52)], GARMENT)
    # white collar
    c.poly_fill([(cx - 14, y + h - 54), (cx, y + h - 38), (cx + 14, y + h - 54)],
                (245, 243, 236))
    # neck
    c.fill_rect(cx - 9, y + h - 78, 18, 28, SKIN)
    # hair mass behind the face, plus bun
    c.ellipse_fill(cx, y + 62, 40, 46, HAIR)
    c.ellipse_fill(cx, y + 22, 15, 14, HAIR)
    # face
    c.ellipse_fill(cx, y + 68, 31, 38, SKIN)
    # hair fringe across the forehead
    c.poly_fill([(cx - 31, y + 52), (cx + 31, y + 52), (cx + 30, y + 38),
                 (cx + 18, y + 46), (cx, y + 40), (cx - 18, y + 46),
                 (cx - 30, y + 38)], HAIR)
    # side locks
    c.fill_rect(cx - 34, y + 46, 7, 52, HAIR)
    c.fill_rect(cx + 27, y + 46, 7, 52, HAIR)
    # brows, eyes, nose, mouth
    c.line(cx - 20, y + 60, cx - 8, y + 58, HAIR, 2)
    c.line(cx + 8, y + 58, cx + 20, y + 60, HAIR, 2)
    c.fill_rect(cx - 17, y + 64, 7, 2, (40, 32, 26))
    c.fill_rect(cx + 10, y + 64, 7, 2, (40, 32, 26))
    c.line(cx, y + 68, cx - 2, y + 80, (150, 105, 80), 2)
    c.line(cx - 8, y + 90, cx + 8, y + 90, (150, 80, 70), 2)
    # frame
    c.rect_outline(x, y, w, h, INK, 2)


def field(c, x, y, label, value, label_scale=1.5, value_scale=2.0):
    """One labelled data field: small grey label above a navy value."""
    c.text(label, x, y, label_scale, INK_SOFT)
    c.text(value, x, y + 12, value_scale, INK)


def draw_stamp(c, cx, cy, w, h, angle, color, lines, alpha=200):
    """A rotated rectangular ink stamp with centred lines of text."""
    # translucent ink wash inside the stamp
    rad = math.radians(angle)
    ca, sa = math.cos(rad), math.sin(rad)
    for yy in range(-h // 2, h // 2 + 1):
        for xx in range(-w // 2, w // 2 + 1):
            rx = cx + int(round(xx * ca - yy * sa))
            ry = cy + int(round(xx * sa + yy * ca))
            c.blend(rx, ry, color, 26)
    c.rotated_rect_outline(cx, cy, w, h, angle, color, 2)
    c.rotated_rect_outline(cx, cy, w - 10, h - 10, angle, color, 1)
    n = len(lines)
    for i, (txt, scale) in enumerate(lines):
        ly = cy + (i - (n - 1) / 2.0) * (7 * scale + 6) - 7 * scale / 2
        c.rotated_text(txt, cx, int(round(ly)), scale, color, angle)


def draw_date_stamp(c, cx, cy, r, angle, color, top, mid, bot):
    """A circular date stamp with three short lines of text."""
    c.ellipse_outline(cx, cy, r, r, color, 2)
    c.ellipse_outline(cx, cy, r - 6, r - 6, color, 1)
    c.rotated_text(top, cx, cy - r + 12, 1.0, color, angle)
    c.rotated_text(mid, cx, cy - 4, 1.0, color, angle)
    c.rotated_text(bot, cx, cy + r - 20, 1.0, color, angle)


def draw_signature(c, x, y):
    pts = [(x, y + 8), (x + 14, y), (x + 24, y + 12), (x + 36, y + 2),
           (x + 48, y + 10), (x + 62, y), (x + 74, y + 8), (x + 88, y + 4),
           (x + 102, y + 8)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], INK, 2)


# ---------------------------------------------------------------------------
# Build the spread
# ---------------------------------------------------------------------------
W, H = 1024, 640


def build():
    c = Canvas(W, H, PAPER)
    # outer double border and centre spine
    c.rect_outline(8, 8, W - 16, H - 16, INK, 2)
    c.rect_outline(14, 14, W - 28, H - 28, INK, 1)
    c.line(W // 2, 14, W // 2, H - 14, INK, 2)

    # ============================ LEFT PAGE: DATA ==========================
    # header: arms + country name
    draw_emblem(c, 66, 30)
    c.text("REPUBLIC OF TALVERIA", 104, 36, 3.0, INK)
    c.text("PASSPORT", 104, 62, 2.0, BURGUNDY)
    c.text("TALVERIAN TRAVEL DOCUMENT", 240, 64, 1.5, INK_SOFT)
    c.line(24, 92, 488, 92, INK, 2)

    # portrait
    draw_portrait(c, 36, 110, 150, 185)

    # data fields beside the portrait
    field(c, 206, 110, "TYPE", "P")
    field(c, 262, 110, "CODE", "TAL")
    field(c, 330, 110, "PASSPORT NO.", "TV1234567")
    field(c, 206, 150, "SURNAME", "VARKOVA")
    field(c, 206, 190, "GIVEN NAMES", "ELIN MARA")
    field(c, 206, 230, "NATIONALITY", "TALVERIAN")
    field(c, 206, 270, "DATE OF BIRTH", "14 MAR 1991")
    field(c, 400, 270, "SEX", "F")
    field(c, 206, 305, "PLACE OF BIRTH", "VORNAK, TALVERIA")

    # holder's signature under the portrait
    draw_signature(c, 40, 306)
    c.text("HOLDER'S SIGNATURE", 40, 330, 1.5, INK_SOFT)

    # issue block
    c.line(24, 356, 488, 356, INK, 1)
    field(c, 36, 372, "DATE OF ISSUE", "12 JUN 2023")
    field(c, 260, 372, "DATE OF EXPIRY", "12 JUN 2033")
    field(c, 36, 412, "AUTHORITY", "MINISTRY OF THE INTERIOR, VORNAK")
    field(c, 36, 452, "PLACE OF ISSUE", "VORNAK, TALVERIA")

    # machine-readable zone
    c.fill_rect(24, 500, 464, 62, MRZ_BG)
    c.rect_outline(24, 500, 464, 62, INK, 1)
    line1, line2 = mrz_lines()
    c.text(line1, 32, 512, 1.5, INK)
    c.text(line2, 32, 532, 1.5, INK)
    c.text("2", 30, 592, 2.0, INK_SOFT)
    c.text("THIS PASSPORT REMAINS THE PROPERTY OF THE REPUBLIC OF TALVERIA",
           120, 594, 1.0, INK_SOFT)

    # =========================== RIGHT PAGE: VISAS =========================
    c.text("VISAS", 536, 36, 3.0, INK)
    c.text("ENDORSEMENTS AND STAMPS", 640, 42, 1.5, INK_SOFT)
    c.line(536, 92, 1000, 92, INK, 2)

    # Trip 1 - Kessaria, March 2024
    draw_stamp(c, 660, 158, 220, 92, -7, STAMP_BLUE,
               [("KESSARIA", 2.0), ("ENTRY - 04 MAR 2024", 1.5),
                ("PORT OF LERIN", 1.5)])
    draw_stamp(c, 890, 158, 190, 92, 5, STAMP_BLUE,
               [("KESSARIA", 2.0), ("EXIT - 18 MAR 2024", 1.5),
                ("PORT OF LERIN", 1.5)])

    # Trip 2 - Drenovia, July-August 2025
    draw_stamp(c, 660, 292, 220, 92, 6, STAMP_GREEN,
               [("DRENOVIA", 2.0), ("ENTRY - 22 JUL 2025", 1.5),
                ("VISA FREE - 30 DAYS", 1.5)])
    draw_stamp(c, 890, 292, 190, 92, -5, STAMP_GREEN,
               [("DRENOVIA", 2.0), ("EXIT - 05 AUG 2025", 1.5),
                ("BORDER POST KARA", 1.5)])

    # Trip 3 - Kessaria, January 2026
    draw_stamp(c, 660, 426, 220, 92, -6, STAMP_PURPLE,
               [("KESSARIA", 2.0), ("ENTRY - 09 JAN 2026", 1.5),
                ("PORT OF LERIN", 1.5)])
    draw_stamp(c, 890, 426, 190, 92, 7, STAMP_PURPLE,
               [("KESSARIA", 2.0), ("EXIT - 27 JAN 2026", 1.5),
                ("PORT OF LERIN", 1.5)])

    # Circular date stamps drawn last, so they sit on top of the stamp
    # edges instead of being washed out by them.
    draw_date_stamp(c, 782, 150, 28, -7, STAMP_BLUE, "KESSARIA", "04 MAR", "2024")
    draw_date_stamp(c, 782, 284, 28, 6, STAMP_GREEN, "DRENOVIA", "22 JUL", "2025")
    draw_date_stamp(c, 782, 418, 28, -6, STAMP_PURPLE, "KESSARIA", "09 JAN", "2026")

    # Telling paperwork detail: conditions of entry + departure tax.
    # Talveria is a small island state: its citizens travel visa-free, but
    # the republic itself taxes every departure.
    c.rect_outline(536, 496, 464, 78, BURGUNDY, 2)
    c.text("CONDITIONS OF ENTRY", 552, 508, 2.0, BURGUNDY)
    c.text("TALVERIAN PASSPORTS: VISA FREE 30 DAYS.", 552, 534, 1.5, INK)
    c.text("EMPLOYMENT PROHIBITED. STAY MAY NOT", 552, 550, 1.5, INK)
    c.text("EXCEED 30 DAYS WITHOUT A PERMIT.", 552, 566, 1.5, INK)
    draw_stamp(c, 838, 606, 250, 40, -8, BURGUNDY,
               [("DEPARTURE TAX 25 TAL - PAID", 1.5)], alpha=200)
    c.text("3", 984, 592, 2.0, INK_SOFT)

    return c


# ---------------------------------------------------------------------------
# PNG encoding (pure stdlib: zlib + struct, filter 0)
# ---------------------------------------------------------------------------
def encode_png(canvas):
    raw = bytearray()
    row_bytes = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter type 0 (None)
        start = y * row_bytes
        raw += canvas.buf[start:start + row_bytes]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
