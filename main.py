# ai-excited-01: "The Wave Escapes" — a giant Hokusai-style ukiyo-e wave bursts
# out of its framed painting in a quiet museum gallery, real water flooding the
# floor, tiny visitors leaping back, a small wooden boat riding the crest out of
# the frame toward the viewer. Python 3.13, standard library only, fully
# deterministic (fixed seed): two runs write byte-identical PNGs.
#
# One specific impossible moment, extreme scale, motion out of frame toward the
# viewer, one focal point (the crest + boat), bold limited palette (deep indigo,
# white foam, gold, warm wood), strong diagonal, reads at 300px.

import math
import os
import random
import struct
import zlib

W = H = 1024
SEED = 20261116

# ---- palette ---------------------------------------------------------------
WALL_TOP = (246, 236, 212)
WALL_BOT = (233, 217, 182)
FLOOR_TOP = (169, 116, 63)
FLOOR_BOT = (110, 69, 37)
PLANK = (94, 58, 30)
GOLD = (201, 162, 39)
GOLD_DARK = (140, 109, 31)
GOLD_LIGHT = (232, 201, 90)
SKY_TOP = (22, 50, 79)
SKY_BOT = (46, 90, 122)
HORIZON = (242, 230, 201)
SEA = (30, 74, 110)
SEA2 = (46, 110, 150)
WAVE_DARK = (18, 41, 77)
WAVE = (27, 58, 107)
WAVE_MID = (46, 110, 166)
WAVE_LIGHT = (127, 184, 217)
FOAM = (255, 255, 255)
FOAM_SH = (220, 233, 242)
WOOD = (122, 74, 33)
WOOD_LIGHT = (169, 116, 63)
SILH = (26, 35, 64)
SUN = (232, 84, 47)
GLOW = (255, 196, 90)

buf = bytearray(W * H * 3)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def blend(x, y, c, a):
    """Alpha-blend colour c over the pixel (a in 0..1)."""
    if 0 <= x < W and 0 <= y < H and a > 0.0:
        i = (y * W + x) * 3
        if a >= 1.0:
            buf[i], buf[i + 1], buf[i + 2] = c
        else:
            buf[i] = int(buf[i] + (c[0] - buf[i]) * a)
            buf[i + 1] = int(buf[i + 1] + (c[1] - buf[i + 1]) * a)
            buf[i + 2] = int(buf[i + 2] + (c[2] - buf[i + 2]) * a)


def hline(x0, x1, y, c):
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    if x1 < x0:
        return
    i = (y * W + x0) * 3
    n = x1 - x0 + 1
    buf[i:i + n * 3] = bytes(c) * n


def rect(x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hline(x0, x1, y, c)


def vgrad(y0, y1, top, bot):
    for y in range(max(0, y0), min(H, y1 + 1)):
        t = (y - y0) / max(1, y1 - y0)
        c = tuple(int(top[k] + (bot[k] - top[k]) * t) for k in range(3))
        hline(0, W - 1, y, c)


def circle(cx, cy, r, c, alpha=1.0):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        if alpha >= 1.0:
            hline(cx - dx, cx + dx, cy + dy, c)
        else:
            for x in range(cx - dx, cx + dx + 1):
                blend(x, cy + dy, c, alpha)


def ellipse(cx, cy, rx, ry, c, alpha=1.0):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t < 0:
            continue
        dx = int(rx * math.sqrt(t))
        if alpha >= 1.0:
            hline(cx - dx, cx + dx, cy + dy, c)
        else:
            for x in range(cx - dx, cx + dx + 1):
                blend(x, cy + dy, c, alpha)


def poly(pts, c):
    """Scanline fill of a simple polygon (even-odd)."""
    pts = [(int(x), int(y)) for (x, y) in pts]
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    n = len(pts)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            x0, yy0 = pts[i]
            x1, yy1 = pts[(i + 1) % n]
            if yy0 == yy1:
                continue
            if (y >= min(yy0, yy1)) and (y < max(yy0, yy1)):
                xs.append(x0 + (y - yy0) * (x1 - x0) / (yy1 - yy0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            hline(int(math.ceil(xs[k])), int(math.floor(xs[k + 1])), y, c)


def thick_line(x0, y0, x1, y1, w, c):
    """A line drawn as a chain of filled circles."""
    dist = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(dist / max(1, w // 2)))
    for s in range(steps + 1):
        t = s / steps
        circle(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), w // 2, c)


def ring(cx, cy, r0, r1, c, alpha=1.0):
    for dy in range(-r1, r1 + 1):
        outer = int(math.sqrt(max(0, r1 * r1 - dy * dy)))
        inner = int(math.sqrt(max(0, r0 * r0 - dy * dy))) if abs(dy) < r0 else -1
        if alpha >= 1.0:
            hline(cx - outer, cx - inner - 1, cy + dy, c)
            hline(cx + inner + 1, cx + outer, cy + dy, c)
        else:
            for x in list(range(cx - outer, cx - inner)) + list(range(cx + inner + 1, cx + outer + 1)):
                blend(x, cy + dy, c, alpha)


# ---- scene -----------------------------------------------------------------

def draw_wall_and_floor():
    vgrad(0, 700, WALL_TOP, WALL_BOT)
    # dado rail
    rect(0, 688, W - 1, 700, (198, 172, 128))
    rect(0, 700, W - 1, 706, (120, 84, 48))
    # floor boards with slight perspective
    vgrad(706, H - 1, FLOOR_TOP, FLOOR_BOT)
    for k in range(1, 7):
        y = 706 + k * k * 6 + k * 18
        if y < H:
            thick_line(0, y, W - 1, y + 26, 2, PLANK)
    for k in range(9):
        x = k * 128
        thick_line(x, 706, x - 90, H - 1, 2, PLANK)


def draw_frame_and_painting():
    # gold frame
    rect(140, 60, 780, 640, GOLD)
    rect(148, 68, 772, 632, GOLD_DARK)
    rect(156, 76, 764, 624, GOLD_LIGHT)
    rect(164, 84, 756, 616, GOLD_DARK)
    # painting: indigo sky to pale horizon
    for y in range(88, 380):
        t = (y - 88) / 292.0
        c = tuple(int(SKY_TOP[k] + (SKY_BOT[k] - SKY_TOP[k]) * t) for k in range(3))
        hline(168, 752, y, c)
    rect(168, 380, 752, 396, HORIZON)
    # sea
    for y in range(396, 613):
        t = (y - 396) / 217.0
        c = tuple(int(SEA[k] + (SEA2[k] - SEA[k]) * t) for k in range(3))
        hline(168, 752, y, c)
    # vermilion sun
    circle(300, 175, 42, SUN)
    circle(300, 175, 34, (240, 110, 70))
    # Mount Fuji, small and distant
    poly([(180, 396), (300, 250), (420, 396)], (38, 68, 96))
    poly([(272, 282), (300, 250), (330, 284), (312, 296), (288, 292)], FOAM)
    # small painted waves inside the picture: thin ukiyo-e arc strokes
    for (bx, by, s) in [(230, 470, 40), (380, 520, 54), (540, 460, 46),
                        (630, 540, 58), (270, 570, 50), (480, 580, 42)]:
        for a in range(0, 181, 12):
            t = math.radians(a)
            x0 = int(bx + math.cos(t) * s)
            y0 = int(by - math.sin(t) * s * 0.45)
            x1 = int(bx + math.cos(t + 0.21) * s)
            y1 = int(by - math.sin(t + 0.21) * s * 0.45)
            thick_line(x0, y0, x1, y1, 4, WAVE_LIGHT if (bx // 100) % 2 else FOAM_SH)


def draw_glow():
    # warm halo behind the crest so the focal point burns
    for r in range(130, 0, -4):
        a = 0.08 * (1.0 - r / 130.0)
        circle(862, 232, r, GLOW, a)


def band_poly(center, widths):
    """A thick curved band polygon: centerline points + half-width per point."""
    left, right = [], []
    n = len(center)
    for i, (x, y) in enumerate(center):
        x0, y0 = center[max(0, i - 1)]
        x1, y1 = center[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        hw = widths[i] / 2.0
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    return left + list(reversed(right))


WAVE_CENTER = [(250, 600), (300, 520), (372, 438), (462, 360), (562, 298),
               (668, 254), (762, 232), (838, 246), (884, 296), (898, 378),
               (890, 460), (872, 545), (868, 630), (884, 715), (900, 795),
               (892, 865)]
WAVE_WIDTHS = [200, 180, 165, 152, 142, 132, 124, 116, 104, 96,
               92, 92, 96, 94, 88, 70]


def outer_edge():
    """Leading (upper-left) edge of the tube, base -> crest, in order."""
    full = band_poly(WAVE_CENTER, WAVE_WIDTHS)
    return list(reversed(full[len(WAVE_CENTER):]))


def draw_wave():
    # the wave is one sweeping tube, not a continent: wall and floor stay
    # visible on both sides of it so it reads as an object in the room
    body = band_poly(WAVE_CENTER, WAVE_WIDTHS)
    poly(body, WAVE)
    # dark under-shadow on the trailing (lower-right) side of the tube's top
    shadow = band_poly([(x + 34, y + 26) for (x, y) in WAVE_CENTER[6:11]],
                       [w * 0.35 for w in WAVE_WIDTHS[6:11]])
    poly(shadow, WAVE_DARK)
    # racing bands down the middle of the tube
    poly(band_poly(WAVE_CENTER[:10], [w * 0.30 for w in WAVE_WIDTHS[:10]]), WAVE_MID)
    poly(band_poly(WAVE_CENTER[:6], [w * 0.15 for w in WAVE_WIDTHS[:6]]), WAVE_LIGHT)
    # the crest hooks over: a tapered tongue curling inward and down,
    # foam-tipped, so the top reads as a breaking curl, not a ring
    hook = [(884, 296), (872, 330), (846, 348), (820, 344), (806, 322)]
    poly(band_poly(hook, [72, 62, 48, 32, 12]), WAVE)
    circle(806, 322, 12, FOAM)
    circle(818, 336, 8, FOAM)
    # foam lip along the outer (leading) edge, upper half only
    edge = outer_edge()
    for i in range(0, 8):
        x0, y0 = edge[i]
        x1, y1 = edge[i + 1]
        thick_line(int(x0), int(y0), int(x1), int(y1), 10 if i % 2 else 13, FOAM)
    # splash where the wave tears out of the painting, at the frame's bottom
    for (sx, sy, sr) in [(258, 612, 13), (286, 624, 10), (238, 628, 8),
                         (300, 606, 8), (268, 640, 7), (224, 606, 6)]:
        circle(sx, sy, sr, FOAM)


def draw_foam_claws(rng):
    """Hokusai foam claws: a few thick curved fingers of foam tearing off the
    crest and the outer edge — each a chain of shrinking circles, so they read
    as spray, not sticks."""
    edge = outer_edge()

    def finger(bx, by, nx, ny, size):
        steps = 4
        for s in range(steps):
            t = s / (steps - 1)
            # curve sideways as the finger grows
            px = int(bx + nx * size * t + ny * size * 0.35 * t * t)
            py = int(by + ny * size * t - nx * size * 0.30 * t * t)
            circle(px, py, max(4, int(13 * (1.0 - t * 0.65))), FOAM)

    for i, size in [(5, 78), (6, 92), (7, 84), (8, 62), (4, 58)]:
        x, y = edge[i]
        x1, y1 = edge[i + 1]
        dx, dy = x1 - x, y1 - y
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        if ny > 0:
            nx, ny = -nx, -ny
        finger(int(x), int(y), nx, ny, size)


def draw_spray(rng):
    # droplets tearing off the crest, flying toward the viewer — kept clear
    # of the boat so the focal point reads
    for _ in range(90):
        t = rng.random()
        x = int(820 + t * 200 + rng.gauss(0, 20))
        y = int(90 + t * 180 + rng.gauss(0, 40))
        if 750 <= x <= 900 and 140 <= y <= 270:
            continue
        r = rng.choice([2, 2, 3, 3, 4])
        circle(x, y, r, FOAM if rng.random() < 0.8 else FOAM_SH)


def draw_boat():
    # wooden boat riding the crest slope, big enough to read, tilted with
    # the wave, heading out of the frame toward the viewer
    cx, cy = 798, 208
    ang = -0.35
    ca, sa = math.cos(ang), math.sin(ang)
    sc = 1.6

    def rot(px, py):
        px, py = px * sc, py * sc
        return (int(cx + px * ca - py * sa), int(cy + px * sa + py * ca))

    hull = [rot(-52, -6), rot(52, -14), rot(44, 12), rot(-40, 14)]
    poly(hull, WOOD)
    poly([rot(-52, -6), rot(52, -14), rot(44, -6), rot(-40, 0)], WOOD_LIGHT)
    thick_line(*rot(-30, -6), *rot(-30, -52), 5, WOOD)
    # small cream sail, bellied by the wind
    poly([rot(-30, -52), rot(-30, -8), rot(18, -10)], (250, 240, 205))
    poly([rot(-30, -52), rot(6, -34), rot(18, -10)], (242, 228, 180))
    # tiny sailor, arms up
    circle(*rot(-6, -26), 8, SILH)
    thick_line(*rot(-6, -20), *rot(-2, -2), 6, SILH)
    thick_line(*rot(-4, -16), *rot(-18, -30), 4, SILH)
    thick_line(*rot(-2, -16), *rot(12, -32), 4, SILH)


def draw_visitors():
    # three tiny visitors leaping back from the flood, bottom-left
    def person(x, y, s, lean, arm_up):
        head = (x, int(y - 34 * s))
        circle(head[0], head[1], int(11 * s), SILH)
        # torso leaning away from the wave
        poly([(x - int(9 * s), y - 24 * s), (x + int(9 * s), y - 24 * s),
              (x + int(13 * s) + lean, y + 6 * s),
              (x - int(5 * s) + lean, y + 6 * s)], SILH)
        # arms
        if arm_up:
            thick_line(x, int(y - 20 * s), x - int(20 * s), int(y - 44 * s), 4, SILH)
            thick_line(x, int(y - 20 * s), x + int(18 * s), int(y - 46 * s), 4, SILH)
        else:
            thick_line(x, int(y - 20 * s), x - int(22 * s), int(y - 8 * s), 4, SILH)
            thick_line(x, int(y - 20 * s), x + int(20 * s), int(y - 30 * s), 4, SILH)
        # legs, mid-leap
        thick_line(x + lean // 2, y + 4 * s, x - int(14 * s), y + int(26 * s), 5, SILH)
        thick_line(x + lean // 2, y + 4 * s, x + int(18 * s), y + int(20 * s), 5, SILH)
        # shadow
        ellipse(x + 6, y + int(30 * s), int(26 * s), int(6 * s), (60, 40, 20), 0.55)

    person(215, 812, 1.0, -14, True)
    person(345, 852, 1.15, -10, True)
    person(480, 828, 0.9, -12, False)
    # a dropped guidebook and a fallen hat, small storytelling details
    poly([(560, 900), (592, 894), (596, 912), (564, 918)], (232, 84, 47))
    ellipse(150, 906, 22, 8, SILH, 0.9)


def draw_broken_frame():
    # gold shards where the wave smashed through the frame's top-right corner
    for (cx, cy, ang, ln) in [(800, 92, 0.6, 46), (782, 130, -0.4, 34),
                              (830, 150, 1.1, 28), (760, 78, 0.2, 30)]:
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for px, py in [(-ln // 2, -5), (ln // 2, -5), (ln // 2, 5), (-ln // 2, 5)]:
            pts.append((int(cx + px * ca - py * sa), int(cy + px * sa + py * ca)))
        poly(pts, GOLD_LIGHT if ang > 0 else GOLD_DARK)


def draw_flood(rng):
    # water sheet flooding the polished floor where the wave's tongue lands
    for k in range(9):
        y = 880 + k * 15
        x0 = 700 + k * 22
        x1 = 1024 - k * 6
        for x in range(x0, x1, 3):
            blend(x, y + rng.randint(-2, 2), WAVE_LIGHT if k % 2 else SEA2, 0.35)
    ellipse(890, 925, 150, 42, (210, 228, 240), 0.5)
    ellipse(890, 925, 118, 30, (160, 200, 225), 0.45)
    # reflection of the wave tongue in the wet floor
    for k in range(10):
        y = 886 + k * 8
        wdt = 130 - k * 7
        for x in range(880 - wdt, 880 + wdt, 4):
            blend(x, y, WAVE_MID, 0.28)
    # foam where the wave meets the floor, bridging tongue to puddle
    for _ in range(90):
        x = int(rng.gauss(900, 80))
        y = int(rng.gauss(845, 45))
        circle(x, y, rng.choice([2, 3, 3, 4, 6]), FOAM)


def render():
    rng = random.Random(SEED)
    draw_wall_and_floor()
    draw_frame_and_painting()
    draw_glow()
    draw_wave()
    draw_foam_claws(rng)
    draw_spray(rng)
    draw_broken_frame()
    draw_boat()
    draw_visitors()
    draw_flood(rng)


# ---- PNG encoder (deterministic) -------------------------------------------

def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: None
        raw += buf[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 6)
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    render()
    n = write_png(os.path.join(outdir, "entry.png"))
    print(f"wrote {os.path.join(outdir, 'entry.png')} ({n} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
