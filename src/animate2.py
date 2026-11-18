"""조하구 2티어 움직이는 구독뱃지 v2 - 원본 도트 격자에 맞춰서 움직임.

원본마다 도트 한 칸 크기가 다름 (1~12개월·54개월: 4px, 18~48개월: 3px).
그래서 각 뱃지를 '도트 한 칸 = 1픽셀'인 작은 그림으로 줄여서 거기서 움직이고,
마지막에 원래 배율로 키움 -> 모든 움직임/이펙트가 원본 도트 크기와 딱 맞음.

originals/NN.png -> apng/NN.png (치지직 업로드용 72x72 APNG)
                 -> preview/NN.gif (4배 확대 미리보기)
실행: python src/animate2.py [개월 ...]   (예: python src/animate2.py 02 48)
"""
import math, os, random, sys
from PIL import Image, ImageDraw

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
HERE = os.path.dirname(SRC_DIR)  # 저장소 루트
sys.path.insert(0, SRC_DIR)
from native import to_native, to72  # noqa: E402

OUT_APNG = os.path.join(HERE, "apng")
OUT_PREV = os.path.join(HERE, "preview")
os.makedirs(OUT_APNG, exist_ok=True)
os.makedirs(OUT_PREV, exist_ok=True)

CLEAR = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)


def orig(n):
    return Image.open(os.path.join(HERE, "originals", f"{n}.png")).convert("RGBA")


# 54개월: 2티어 표시용 별·노란 구슬을 지우고 커비만 남긴 18x18 도트 (가려진 부분은 좌우대칭으로 복원)
KIRBY_PAL = {"A": "#1a5992", "B": "#53b8ff", "C": "#3191e7", "D": "#aadafc", "F": "#000000", "G": "#c4eeff",
             "H": "#d9f9ff", "J": "#ffffff", "K": "#7ab1f1", "L": "#ffd1d6", "M": "#9197b3", "N": "#3a3a50",
             "O": "#5387d6", "P": "#a02363", "Q": "#ff6e93"}
KIRBY = ["....AA......AA....",
         "...ABBAAAAAABBA...",
         "..ACBBDDDDDDBBCA..",
         ".ABBCGGGGGGGGCBBA.",
         ".ABBGGGHHHHGGGBBA.",
         "..AGGGFJHHFJGGGA..",
         ".AKGLLFFHHFFLLGKA.",
         ".ADGLLMNGGNMLLGDA.",
         ".ADGGGGGKKGGGGGDA.",
         ".ADDGGGGGGGGGGDDA.",
         "AGDDDGGGGGGGGDDDGA",
         "ADDDDDDDDDDDDDDDDA",
         "ADKDDDDDDDDDDDDKDA",
         ".AAKDDDDDDDDDDKAA.",
         "...AOKKKKKKKKOA...",
         "....PQQQPPQQQP....",
         "....PQQP..PQQP....",
         ".....PP....PP....."]


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def kirby_native():
    im = Image.new("RGBA", (18, 18), CLEAR)
    for y, row in enumerate(KIRBY):
        for x, ch in enumerate(row):
            if ch != ".":
                im.putpixel((x, y), hexc(KIRBY_PAL[ch]))
    return im


def native(n):
    return kirby_native() if n == "54" else to_native(n, orig(n))


# ---------------------------------------------------------------- 도트 도구 (모두 '칸' 단위)
def blank(im):
    return Image.new("RGBA", im.size, CLEAR)


def shift(im, dx=0, dy=0):
    out = blank(im)
    out.paste(im, (dx, dy), im)
    return out


def squash(im, rows):
    """지정한 줄들을 빼고 위쪽을 아래로 내림 (바닥 고정)."""
    W, H = im.size
    keep = [y for y in range(H) if y not in rows]
    out = blank(im)
    off = H - len(keep)
    for j, y in enumerate(keep):
        out.paste(im.crop((0, y, W, y + 1)), (0, j + off))
    return out


def pinch(im, cols):
    """지정한 열들을 빼고 가운데로 모음 (세로로 길쭉해 보임)."""
    W, H = im.size
    keep = [x for x in range(W) if x not in cols]
    out = blank(im)
    off = (W - len(keep)) // 2
    for j, x in enumerate(keep):
        out.paste(im.crop((x, 0, x + 1, H)), (j + off, 0))
    return out


def near(c, ref, tol=24):
    return abs(c[0] - ref[0]) + abs(c[1] - ref[1]) + abs(c[2] - ref[2]) <= tol


def recolor(im, pairs, box=None):
    out = im.copy()
    px = out.load()
    W, H = im.size
    x0, y0, x1, y1 = box or (0, 0, W, H)
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            c = px[x, y]
            if c[3]:
                for src, dst in pairs:
                    if near(c, src):
                        px[x, y] = tuple(dst[:3]) + (255,)
                        break
    return out


def lerp(c1, c2, k):
    return tuple(round(a + (b - a) * k) for a, b in zip(c1, c2))


def put(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), c)


def rect(im, x0, y0, x1, y1, c):
    for y in range(y0, y1):
        for x in range(x0, x1):
            put(im, x, y, c)


def sprite(rows, pal):
    h, w = len(rows), max(len(r) for r in rows)
    im = Image.new("RGBA", (w, h), CLEAR)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                im.putpixel((x, y), pal[ch])
    return im


def stamp(im, spr, x, y):
    out = im.copy()
    tmp = blank(im)
    tmp.paste(spr, (int(round(x)), int(round(y))), spr)
    out.alpha_composite(tmp)
    return out


def behind(im, layer):
    out = layer.copy()
    out.alpha_composite(im)
    return out


def outer_outline(im):
    """바깥 테두리 칸 (어두운 칸 중 투명/가장자리와 닿은 것)."""
    W, H = im.size
    px = im.load()
    pts = []
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if c[3] and sum(c[:3]) < 200:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or px[xx, yy][3] == 0:
                        pts.append((x, y))
                        break
    return pts


def dist_out(im, maxd=6):
    """투명 칸 -> 캐릭터까지 거리(칸)."""
    W, H = im.size
    a = im.getchannel("A").load()
    d = {}
    for y in range(H):
        for x in range(W):
            if a[x, y] == 0:
                best = 99
                for yy in range(y - maxd, y + maxd + 1):
                    for xx in range(x - maxd, x + maxd + 1):
                        if 0 <= xx < W and 0 <= yy < H and a[xx, yy]:
                            best = min(best, max(abs(xx - x), abs(yy - y)))
                if best <= maxd:
                    d[(x, y)] = best
    return d


PLUS = ([".W.", "WCW", ".W."], ["..W..", "..W..", "WWCWW", "..W..", "..W.."])


def sparkle(im, x, y, size, color=WHITE, core=(255, 250, 200, 255)):
    if size <= 0:
        return im
    rows = PLUS[min(size, 2) - 1]
    spr = sprite(rows, {"W": color, "C": core})
    return stamp(im, spr, x - spr.width // 2, y - spr.height // 2)


def tri(t):
    return 1 - abs(2 * (t % 1) - 1)


def win(t, a, b):
    return (t - a) / (b - a) if a <= t < b else None


def cloud(W, H, blobs, fill=(240, 240, 248, 255), shade=(190, 190, 210, 255), line=(70, 70, 95, 255)):
    """도트 연기 구름 (칸 단위 원 여러 개)."""
    im = Image.new("RGBA", (W, H), CLEAR)
    inside = set()
    for (cx, cy, r) in blobs:
        for y in range(H):
            for x in range(W):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    inside.add((x, y))
    for (x, y) in inside:
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        lower = (x, y + 1) not in inside or (x, y + 2) not in inside
        im.putpixel((x, y), line if edge else shade if lower else fill)
    return im


# ---------------------------------------------------------------- 캐릭터별 (칸 좌표)
def a01(b, i, n):
    """로봇 부팅: 빨간 LED 눈 맥동, 귀 램프 교차 점멸, 스캔라인, 지지직 글리치."""
    t = i / n
    k = tri(t * 2)
    f = recolor(b, [((255, 0, 0), lerp((110, 0, 0), (255, 70, 70), k))])
    if k > 0.6:
        put(f, 4, 9, (255, 200, 200, 255))
        put(f, 12, 9, (255, 200, 200, 255))
    dim = [((56, 198, 255), (25, 75, 115)), ((60, 114, 210), (20, 45, 90))]
    f = recolor(f, dim, (0, 0, 9, 18) if (i // (n // 4)) % 2 else (9, 0, 18, 18))
    r = (i * 22 // n) % 22 - 2
    px = f.load()
    for x in range(18):
        if 0 <= r < 18:
            c = px[x, r]
            if c[3] and sum(c[:3]) > 300:
                px[x, r] = (min(255, c[0] + 40), min(255, c[1] + 50), min(255, c[2] + 50), 255)
    if i in (n - 5, n - 3):
        g = f.copy()
        for (y, dx) in ((6, 1), (7, 1), (11, -1), (14, 1)):
            row = f.crop((0, y, 18, y + 1))
            rect(g, 0, y, 18, y + 1, CLEAR)
            g.paste(row, (dx, y), row)
        f = recolor(g, [((209, 215, 219), (170, 250, 255))], (0, 6, 18, 8))
    return f


HAMMER = ["YYYY.....",   # 세로로 선 뿅망치: 아래 노란 끝면으로 때림, 손잡이는 오른쪽
          "RRRR.....",
          "DDDDHHHHH",
          "RRRR.....",
          "YYYY....."]


def ol(rows, pal):
    """도트에 검은 테두리 한 칸."""
    spr = sprite(rows, pal)
    W, H = spr.width + 2, spr.height + 2
    out = Image.new("RGBA", (W, H), CLEAR)
    a = spr.getchannel("A").load()
    for y in range(H):
        for x in range(W):
            if any(0 <= x - 1 + dx < spr.width and 0 <= y - 1 + dy < spr.height and a[x - 1 + dx, y - 1 + dy]
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                out.putpixel((x, y), (15, 15, 20, 255))
    out.alpha_composite(spr, (1, 1))
    return out


FLAT = [3, 4, 5, 6, 7, 10, 11, 12, 16]  # 뿅! 맞을 때 빼는 줄 (머리카락은 위 3줄 남김 + 얼굴)


HAMMER_POS = {50: (14.5, 1.5), 25: (11.5, 3), 15: (9, 4.5), 0: (8.5, 5.5)}  # 1시 방향 -> 정수리, 머리 가운데 위치


def draw_hammer(f, deg):
    """deg만큼 오른쪽 위로 들린 뿅망치 (손잡이는 손 쪽 오른쪽 아래). 0도 = 세로로 서서 아래 끝면으로 정수리 때림."""
    th = math.radians(deg)
    hx, hy = math.cos(th), math.sin(th)           # 망치 머리 -> 손 방향
    cx, cy = HAMMER_POS[deg]                       # 망치 머리 가운데
    sx, sy = -hy, hx                               # 때리는 끝면 방향
    cells = {}
    for k in range(-10, 11):
        u = k / 4
        for m in range(-7, 8):
            v = m / 4
            x, y = round(cx + u * sx + v * hx), round(cy + u * sy + v * hy)
            if abs(u) >= 1.9:
                c = (255, 220, 70, 255)
            else:
                c = (235, 45, 60, 255) if int(math.floor(u + 2.5)) % 2 == 0 else (170, 20, 40, 255)
            cells[(x, y)] = c
    for k in range(8, 25):
        r = k / 4
        cells.setdefault((round(cx + r * hx), round(cy + r * hy)), (255, 190, 60, 255))
    for (x, y) in list(cells):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in cells:
                    put(f, x + dx, y + dy, (15, 15, 20, 255))
    for (x, y), c in cells.items():
        put(f, x, y, c)
    return f


def a02(b, i, n):
    """뿅망치: 1시 방향에서 호를 그리며 내려와 → 끝면으로 정수리 뿅!(얼굴까지 납작·충격선) → 별 빙글 → 띠용."""
    t = i / n
    if t < 0.15:
        return b.copy()
    if t < 0.32:  # 1시 방향에서 휘둘러 내려옴
        return draw_hammer(b.copy(), 50 if t < 0.24 else 25)
    if t < 0.45:  # 뿅!
        f = squash(b, FLAT)
        f = draw_hammer(f, 0)
        for (x, y) in ((1, 9), (0, 8), (16, 9), (17, 8), (2, 12), (15, 12)):
            put(f, x, y, WHITE)
        return f
    if t < 0.72:
        rows = FLAT if t < 0.55 else [4, 5, 6, 11, 12] if t < 0.6 else [4, 5, 12] if t < 0.65 else [4, 12] if t < 0.69 else [4]
        f = squash(b, rows)
        if t < 0.52:
            f = draw_hammer(f, 15)
        a = (t - 0.45) * 2 * math.pi * 3
        for k in range(3):
            x = round(9 + 6 * math.cos(a + k * 2.1))
            y = round(len(rows) + 1 + 1.5 * math.sin(a + k * 2.1))
            put(f, x, y, (255, 230, 70, 255))
        return f
    if t < 0.8:
        return pinch(b, [3, 14])
    return b.copy()


def a03(b, i, n):
    """티라노 조랭이 캭!: 가만히 → 웅크림 → 캭! 발톱 세운 손 번쩍 + 입 쩍 + 눈 > < → 원래대로."""
    t = i / n
    skin = (183, 248, 255, 255)
    if t < 0.4:
        return b.copy()
    if t < 0.48:
        return squash(b, [10])
    if t >= 0.88:
        return b.copy()
    f = b.copy()
    # 눈 > <
    for x0 in (3, 11):
        rect(f, x0, 8, x0 + 4, 12, skin)
    for (x, y) in ((3, 8), (4, 8), (5, 9), (3, 10), (4, 10), (13, 8), (14, 8), (12, 9), (13, 10), (14, 10)):
        put(f, x, y, BLACK)
    # 입 쩍 + 송곳니
    rect(f, 7, 12, 11, 14, BLACK)
    rect(f, 8, 13, 10, 14, (150, 20, 40, 255))
    put(f, 8, 12, WHITE)
    put(f, 9, 12, WHITE)
    # 발톱 세운 손
    rise = 2 if t < 0.53 else 0
    paw = (110, 225, 75, 255)
    for x0 in (1, 13):
        y0 = 12 + rise
        core = {(x0 + 1 + dx, y0 + 1 + dy) for dx in range(3) for dy in range(3)}
        claws = {(x0 + 1, y0), (x0 + 2, y0 - 1), (x0 + 3, y0)}
        for (x, y) in core | claws:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) not in core | claws:
                        put(f, x + dx, y + dy, BLACK)
        for (x, y) in core:
            put(f, x, y, paw)
        put(f, x0 + 2, y0 + 2, (70, 180, 55, 255))
        for (x, y) in claws:
            put(f, x, y, WHITE)
    return f


def a06(b, i, n):
    """안경 번뜩 (メガネ キラーン): 렌즈가 하얗게 빛나며 눈을 가리고 반짝."""
    t = i / n
    f = squash(b, [13]) if t < 0.3 and (i // 3) % 2 else b.copy()
    lens = [(255, 175, 164), (255, 145, 155)]
    p = win(t, 0.35, 0.8)
    if p is not None:
        # 렌즈를 흰 반사광으로
        glare = (235, 250, 255)
        f = recolor(f, [(lens[0], glare), (lens[1], (200, 235, 255))])
        # 흰 줄이 대각선으로 지나감
        s = round(p * 26) - 4
        px = f.load()
        for y in range(7, 12):
            for x in range(18):
                c = px[x, y]
                if c[3] and (x + y) in (s, s + 1) and (near(c, glare) or near(c, (200, 235, 255))):
                    px[x, y] = WHITE
        # 빨간 테 반짝
        f = recolor(f, [((255, 0, 0), (255, 110, 110)), ((199, 0, 25), (255, 40, 60))])
        if p > 0.35:
            f = sparkle(f, 16, 6, 2 if p < 0.7 else 1, WHITE, (255, 230, 240, 255))
        if 0.45 < p < 0.75:
            f = sparkle(f, 2, 7, 1, WHITE, (255, 230, 240, 255))
    return f


GO = ["....M.M",
      "MMMM...",
      "...M...",
      "...M...",
      "MMMM..."]


def a09(b, i, n):
    """ゴゴゴ 위압감 + 모자 금장식 빛줄기."""
    t = i / n
    f = b.copy()
    s = int(t * 2 * 22) % 22
    px = f.load()
    for y in range(2, 8):
        for x in range(18):
            c = px[x, y]
            if c[3] and c[0] > 190 and c[2] < 80 and (x + y) in (s, s + 1):
                px[x, y] = (255, 255, 210, 255)
    go = sprite(GO, {"M": (220, 70, 230, 255)})
    sh = sprite(GO, {"M": (40, 0, 60, 255)})
    spots = [(0.0, 11, 0), (0.22, -1, 9), (0.44, 11, 12)]
    for start, x, y in spots:
        age = (t - start) % 1
        if age < 0.7:
            jx = (0, 1, 0, -1)[(i + x) % 4] if age > 0.08 else 0
            f = stamp(f, sh, x + jx + 1, y + 1)
            f = stamp(f, go, x + jx, y)
    return f


DROP = [".K.", "KWK", "KBK", ".K."]


def a12(b, i, n):
    """봇치 불안: 식은땀 → 이마 그늘 + 보라 우울선 + 덜덜 → 도트가 우수수 무너져 녹아내림 → 뿅 복원."""
    t = i / n
    drop = ol([".W.", "WWB", "WBB"], {"W": (235, 250, 255, 255), "B": (110, 190, 240, 255)})
    pale = min(1, t / 0.25)
    f = recolor(b, [((183, 248, 255), lerp((183, 248, 255), (170, 180, 235), pale)),
                    ((120, 212, 238), lerp((120, 212, 238), (125, 135, 205), pale))])
    if t < 0.25:
        return stamp(f, drop, 13, 4 + round(6 * t / 0.25))
    if t < 0.58:
        # 이마 그늘 (윗얼굴 어둡게) + 보라 우울선
        f = recolor(f, [((170, 180, 235), (120, 120, 190)), ((125, 135, 205), (95, 95, 165)),
                        ((255, 193, 199), (190, 140, 190))], (0, 6, 18, 12))
        gl = (120, 70, 190, 255)
        for x in (4, 6, 8, 10, 12, 14):
            for y in range(4, 11):
                if (y + x // 2 + i) % 3 != 0:
                    put(f, x, y, gl)
        f = stamp(f, drop, 13, 9)
        f = stamp(f, drop, 1, 7 + (i % 3))
        return pinch(f, [4, 13]) if i % 2 else f
    if t < 0.84:
        # 우수수 무너짐: 아래쪽부터 도트가 떨어지며 녹아내림
        p = win(t, 0.58, 0.84)
        src = f.load()
        out = blank(f)
        rnd = random.Random(3)
        for y in range(18):
            for x in range(18):
                c = src[x, y]
                r = rnd.random()
                if not c[3]:
                    continue
                if r < p * 0.35:
                    continue
                fall = round(p * (2 + r * 9) * (0.4 + y / 17))
                put(out, x + (1 if r > 0.8 else -1 if r < 0.2 else 0) * round(p * 2), y + fall, c)
        return out
    if t < 0.9:
        return sparkle(squash(b, [10]), 9, 9, 2)
    return b.copy()


def spin(b, deg):
    """칸 단위 회전 (가운데 기준). 90도 배수는 도트 그대로."""
    W, H = b.size
    S2 = max(W, H)
    sq = Image.new("RGBA", (S2, S2), CLEAR)
    sq.paste(b, ((S2 - W) // 2, (S2 - H) // 2))
    k = deg % 360
    r = sq.transpose({90: Image.ROTATE_90, 180: Image.ROTATE_180, 270: Image.ROTATE_270}[k]) if k in (90, 180, 270)         else sq if k == 0 else sq.rotate(k, resample=Image.NEAREST)
    return r.crop(((S2 - W) // 2, (S2 - H) // 2, (S2 - W) // 2 + W, (S2 - H) // 2 + H))


def a18(b, i, n):
    """포치타 공중제비: 헥헥 → 웅크림 → 빙글 한 바퀴 → 쿵 착지 → 헥헥."""
    tongue = (255, 192, 205, 255)

    def tg(f):
        put(f, 12, 20, tongue)
        put(f, 12, 21, tongue)
        return f

    # 0-7 헥헥, 8-9 웅크림, 10-17 회전(45도씩), 18-19 착지, 20-23 헥헥
    if i < 8:
        f = b.copy()
        if (i // 2) % 2:
            put(f, 12, 20, tongue)
        return f
    if i < 10:
        return tg(squash(b, [9, 10]))
    if i < 18:
        k = i - 10
        f = spin(tg(b.copy()), -45 * (k + 1) if k < 7 else 0)
        return shift(f, 0, -1) if 1 <= k <= 5 else f
    if i < 20:
        return tg(squash(b, [10]))
    f = b.copy()
    if (i // 2) % 2:
        put(f, 12, 20, tongue)
    return f


def a24(b, i, n):
    """나루토 변신술: 펑! → 티라노 조랭이(3개월)로 변신 → 펑! → 나루토 복귀."""
    t = i / n
    W, H = b.size

    def poof(p):
        r = 2 + 6 * min(1, p / 0.5)
        return cloud(W, H, [(12, 12, r), (12 - r * 0.7, 13, r * 0.7), (12 + r * 0.7, 13, r * 0.7),
                            (12, 12 - r * 0.6, r * 0.7), (12 - r * 0.5, 9, r * 0.5), (12 + r * 0.5, 16, r * 0.5)])

    frog = native("03")
    if t < 0.25:
        f = squash(b, [14]) if (i // 2) % 2 else b.copy()
        p = win(t, 0.05, 0.22)
        if p is not None:
            s = 8 + round(p * 9)
            px = f.load()
            for y in (10, 11):
                for x in (s, s + 1):
                    c = px[x, y]
                    if c[3] and abs(c[0] - c[2]) < 30 and c[0] > 120:
                        px[x, y] = WHITE
        return f
    if t < 0.38:
        p = win(t, 0.25, 0.38)
        f = stamp(b, poof(p), 0, 0)
        return to72("24", f)
    if t < 0.66:
        p = win(t, 0.38, 0.66)
        fr = frog.copy()
        if 0.45 < p < 0.6:
            for x0 in (3, 11):
                rect(fr, x0 + 1, 8, x0 + 3, 12, (183, 248, 255, 255))
                rect(fr, x0, 10, x0 + 4, 11, BLACK)
        if p < 0.3:
            fr = squash(fr, [10])
        big = to72("03", fr)
        if p < 0.25:
            c = poof(1 - p * 2)
            big.alpha_composite(to72("24", c))
        return big
    if t < 0.76:
        p = win(t, 0.66, 0.76)
        big = to72("03", frog)
        big.alpha_composite(to72("24", poof(p)))
        return big
    p = win(t, 0.76, 1.0)
    f = b.copy()
    if p < 0.3:
        f = stamp(f, poof(1 - p * 3), 0, 0) if p < 0.25 else f
    f = sparkle(f, 3, 3, 2 if p < 0.5 else 1)
    f = sparkle(f, 22, 3, 1 if p < 0.3 else 2 if p < 0.7 else 0)
    f = sparkle(f, 22, 21, 1 if 0.3 < p < 0.8 else 0)
    return f


HEART = [".DD.DD.", "DPPDRRD", "DPRRRRD", "DRRRRRD", ".DRRRD.", "..DRD..", "...D..."]


def a30(b, i, n):
    """키타~ン: 윙크 + 하트 + 핑크 오오라 외곽선 + 반짝반짝."""
    t = i / n
    f = b.copy()
    wink = 0.3 <= t < 0.7
    if wink:
        # 눈동자 칸(검정·흰 하이라이트·파랑)만 피부색으로 지우고 앞머리는 그대로 둠
        px = f.load()
        skin = (196, 238, 253, 255)
        eye = [(0, 0, 0), (0, 1, 2), (255, 255, 255), (85, 162, 196)]
        for y in range(15, 20):
            for x in range(15, 19):
                if any(near(px[x, y], e, 6) for e in eye):
                    px[x, y] = skin
        for (x, y) in ((15, 18), (16, 17), (17, 17), (18, 18)):  # ^ 윙크
            put(f, x, y, BLACK)
        p = win(t, 0.3, 0.7)
    k = tri(t * 2)
    glow = lerp((0, 0, 0), (255, 120, 170), k) + (255,)
    for (x, y) in OUT["30"]:
        if not (wink and x >= 15 and y <= 11):  # 하트 올라가는 오른쪽 위는 오오라 끔
            f.putpixel((x, y), glow)
    if wink:
        heart = sprite(HEART, {"R": (235, 50, 100, 255), "P": (255, 200, 220, 255), "D": (120, 10, 45, 255)})
        f = stamp(f, heart, 17, 8 - round(8 * p))
    for j, (x, y) in enumerate(((2, 2), (22, 2), (2, 22), (22, 22))):
        if wink and x == 22 and y == 2:
            continue
        s = tri(t * 2 + j * 0.25)
        f = sparkle(f, x, y, 2 if s > 0.66 else 1 if s > 0.33 else 0, WHITE, (255, 200, 230, 255))
    return f


NOTE = [".KKK", ".K.K", ".K..", "KK..", "KK.."]
LEEK_1 = ["...GG",
          "...G.",
          "..GG.",
          "..W..",
          "..W..",
          ".W...",
          ".W...",
          "K...."]
LEEK_11 = [r[::-1] for r in LEEK_1]
LEEK_1230 = [".G.G",
             ".GG.",
             "..G.",
             "..W.",
             "..W.",
             ".W..",
             ".W..",
             ".K.."]
LEEK_1130 = [r[::-1] for r in LEEK_1230]
LEEK_12 = ["G.G",
           "GGG",
           ".G.",
           ".W.",
           ".W.",
           ".W.",
           ".W.",
           ".K."]
LEEK_UP = ["......G", ".....GG", "....GG.", "...WG..", "..WW...", ".WW....", "WK....."]
LEEK_MID = [".......", ".......", ".......", "WWWWGGG", "KWWWGGG", ".......", "......."]
LEEK_DN = ["WK.....", ".WW....", "..WW...", "...WG..", "....GG.", ".....GG", "......G"]


def a36(b, i, n):
    """미쿠 리듬타기: 박자마다 크게 통통 + 테두리 두른 파 와이퍼 + 큰 음표들."""
    t = i / n
    beat = i % 9
    f = squash(b, [13, 14]) if beat < 2 else squash(b, [14]) if beat < 3 else b.copy()
    pose = (0, 1, 3, 4, 3, 1)[(i // 3) % 6]
    rows, (rx, ry) = ((LEEK_11, (4, 7)), (LEEK_1130, (2, 7)), (LEEK_12, (1, 7)),
                      (LEEK_1230, (1, 7)), (LEEK_1, (0, 7)))[pose]
    leek = ol(rows, {"W": (245, 248, 240, 255), "G": (60, 185, 85, 255), "K": (200, 210, 190, 255)})
    f = stamp(f, leek, 20 - rx - 1, 22 - ry - 1)
    teal = {"K": (110, 235, 235, 255)}
    pink = {"K": (255, 150, 195, 255)}
    for j, (x, pal) in enumerate(((0, teal), (20, pink), (2, pink), (19, teal))):
        q = (t * 2 + j * 0.25) % 1
        if q < 0.8:
            note = ol(NOTE, pal)
            f = stamp(f, note, x + (1 if (q * 4) % 2 > 1 else 0), 6 - round(8 * q))
    return f


QMARK = ["WWW", "..W", ".WW", ".W.", "...", ".W."]
EMARK = ["W", "W", "W", ".", "W"]


def a42(b, i, n):
    """코난 돋보기 수색: 돋보기로 얼굴 앞을 훑음(렌즈 속은 진짜 2배 확대) + ? → 딱 멈추고 ! → 퇴장."""
    t = i / n
    f = b.copy()
    if t < 0.1 or t >= 0.92:
        return f
    # 렌즈 중심 경로
    if t < 0.55:
        p = win(t, 0.1, 0.55)
        cx = 7 + round(10 * p)
        cy = 15 + round(math.sin(p * math.pi * 3))
    elif t < 0.8:
        cx, cy = 17, 14
    else:
        p = win(t, 0.8, 0.92)
        cx, cy = 17 + round(5 * p), 14 + round(9 * p)
    src = b.load()
    px = f.load()
    W, H = f.size
    R = 5
    for y in range(cy - R - 1, cy + R + 2):
        for x in range(cx - R - 1, cx + R + 2):
            if not (0 <= x < W and 0 <= y < H):
                continue
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= (R - 0.5) ** 2:  # 렌즈 속: 2배 확대
                sx, sy = cx + (x - cx) // 2, cy + (y - cy) // 2
                c = src[min(W - 1, max(0, sx)), min(H - 1, max(0, sy))]
                c = c if c[3] else (175, 205, 225, 255)
                px[x, y] = (min(255, c[0] + 15), min(255, c[1] + 25), min(255, c[2] + 35), 255)
            elif d2 <= (R + 0.6) ** 2:  # 테두리
                px[x, y] = (40, 25, 10, 255) if d2 > (R + 0.1) ** 2 else (215, 170, 60, 255)
    put(f, cx - 2, cy - 3, WHITE)  # 렌즈 반사광
    put(f, cx - 3, cy - 2, WHITE)
    for k in range(1, 5):  # 손잡이
        put(f, cx + R + k - 1, cy + R + k - 1, (110, 60, 25, 255))
        put(f, cx + R + k, cy + R + k - 1, (40, 25, 10, 255))
    if t < 0.55:
        q = sprite(QMARK, {"W": WHITE})
        f = stamp(f, q, 21, 0 if (i // 3) % 2 else 1)
    elif t < 0.8:
        p = win(t, 0.55, 0.8)
        f = stamp(f, sprite(EMARK, {"W": (255, 230, 60, 255)}), 22, 0 if p > 0.1 else 1)
        if p < 0.4:
            f = sparkle(f, cx - 2, cy - 3, 2 if p < 0.2 else 1)
    return f


BOLTS = [["...W",
          "..W.",
          ".WWW",
          "..W.",
          ".W..",
          "W..."],
         ["W...",
          ".W..",
          ".WW.",
          "..WW",
          "..W.",
          ".W.."],
         ["..W.",
          ".W..",
          "WWW.",
          ".WW.",
          "..W.",
          "...W"]]
BOLT_SPOTS = [(0, 6), (21, 6), (1, 0), (20, 0), (0, 15), (21, 15)]


def bolt(f, shape, x0, y0, bright):
    """날카로운 도트 번개: 흰 심 + 하늘색 빛 (bright=False면 사라지는 잔광)."""
    rows = BOLTS[shape]
    core = {(x0 + x, y0 + y) for y, r in enumerate(rows) for x, ch in enumerate(r) if ch == "W"}
    if bright:
        for (x, y) in core:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in core:
                    put(f, x + dx, y + dy, (90, 190, 255, 255))
    for (x, y) in core:
        put(f, x, y, WHITE if bright else (150, 215, 255, 255))
    return f


def a48(b, i, n):
    """초사이어인: 크게 일렁이는 황금 오오라 + 몸을 가르는 번개 → 기 모아서 번쩍 폭발."""
    t = i / n
    k = tri(t * 3)
    burst = False  # 번쩍 폭발은 뺌
    f = recolor(b, [((253, 242, 138), lerp((253, 242, 138), (255, 255, 230), k)),
                    ((255, 221, 39), lerp((255, 221, 39), (255, 248, 170), k))])
    aura = blank(f)
    grow = 1.3 if burst else 1.0
    for (x, y), d in AURA["48"].items():
        h = grow * (1.5 + 2.2 * (0.5 + 0.5 * math.sin(x * 0.9 - y * 0.5 + t * 2 * math.pi * 4)))
        if d <= h:
            c = (255, 250, 210, 255) if d <= 1 else (255, 205, 40, 255) if d <= h - 1.5 else (230, 110, 20, 255)
            aura.putpixel((x, y), c)
    f = behind(f, aura)
    for (x, y) in OUT["48"]:
        f.putpixel((x, y), lerp((110, 60, 0), (230, 160, 0), k) + (255,))
    if burst:  # 번쩍
        f = recolor(f, [((196, 238, 253), (255, 255, 220)), ((113, 157, 190), (255, 240, 160))])
        f = sparkle(f, 12, 12, 2, WHITE, (255, 240, 120, 255))
        f = sparkle(f, 3, 3, 2, WHITE, (255, 240, 120, 255))
        f = sparkle(f, 21, 3, 2, WHITE, (255, 240, 120, 255))
    # 번개: 가장자리 두 곳에서 탁! 쳤다가 다음 프레임에 잔광으로 사라짐
    rnd = random.Random(i // 2)
    spots = rnd.sample(BOLT_SPOTS, 3 if burst else 2)
    for k, (x0, y0) in enumerate(spots):
        f = bolt(f, (i // 2 + k) % 3, x0, y0, bright=(i % 2 == 0) or burst)
    return f


def a54(b, i, n):
    """커비: 통통 대기·깜빡 → 크게 빨아들이기(바람이 입으로) → 볼 빵빵 → 꿀꺽."""
    t = i / n
    f = b.copy()
    if t < 0.35:
        if (i // 3) % 2:
            f = squash(f, [9])
        if 0.2 <= t < 0.26:
            for x0 in (6, 10):
                rect(f, x0, 5, x0 + 2, 8, (196, 238, 255, 255))
                rect(f, x0, 6, x0 + 2, 7, BLACK)
        return f
    p = win(t, 0.35, 0.72)
    if p is not None:
        # 입 크게 벌림
        mouth = (58, 58, 80, 255)
        rect(f, 7, 8, 11, 11, mouth)
        rect(f, 8, 9, 10, 11, (160, 35, 99, 255))
        rect(f, 8, 10, 10, 11, (255, 110, 147, 255))
        # 눈 꽉 (> <)
        for x0 in (6, 10):
            rect(f, x0, 5, x0 + 2, 8, (196, 238, 255, 255))
        for (x, y) in ((6, 5), (7, 6), (6, 7), (11, 5), (10, 6), (11, 7)):
            put(f, x, y, BLACK)
        # 바람 줄기 + 빨려드는 반짝이
        wind = (235, 250, 255, 255)
        for j in range(4):
            q = (p * 3 + j / 4) % 1
            for side in (-1, 1):
                x = 9 + side * round(9 - 8 * q) - (1 if side < 0 else 0)
                y = 9 + (j % 2 * 2 - 1) * round(4 * (1 - q))
                put(f, x, y, wind)
                put(f, x + side, y, (170, 220, 255, 255))
        if p > 0.2:
            f = sparkle(f, 9 + round(8 * (1 - (p * 2 % 1))), 2, 1)
        return f
    p = win(t, 0.72, 1.0)
    # 볼 빵빵 (^ ^) -> 꿀꺽
    f = squash(f, [9]) if p < 0.6 else f
    for x0 in (6, 10):
        rect(f, x0, 5 if p >= 0.6 else 6, x0 + 2, 8 if p >= 0.6 else 9, (196, 238, 255, 255))
    ey = 6 if p >= 0.6 else 7
    for (x, y) in ((6, ey + 1), (7, ey), (10, ey), (11, ey + 1)):  # ^ ^
        put(f, x, y, BLACK)
    if p < 0.6:
        rect(f, 3, 8, 5, 10, (255, 209, 214, 255))
        rect(f, 13, 8, 15, 10, (255, 209, 214, 255))
    else:
        f = sparkle(f, 15, 3, 1 if p < 0.85 else 0)
    return f


ANIMS = {
    "01": (a01, 24, 60), "02": (a02, 28, 60), "03": (a03, 24, 60), "06": (a06, 24, 60),
    "09": (a09, 24, 70), "12": (a12, 28, 65), "18": (a18, 24, 60), "24": (a24, 40, 60),
    "30": (a30, 24, 60), "36": (a36, 36, 60), "42": (a42, 36, 60), "48": (a48, 24, 60),
    "54": (a54, 32, 60),
}

OUT = {k: outer_outline(native(k)) for k in ("30", "42", "48")}
AURA = {"48": dist_out(native("48"), 4)}


def save(name, frames, ms):
    frames[0].save(os.path.join(OUT_APNG, f"{name}.png"), save_all=True, append_images=frames[1:],
                   duration=ms, loop=0, disposal=1, blend=0, optimize=True)
    big = []
    for f in frames:
        bg = Image.new("RGBA", (72, 72), (40, 42, 46, 255))
        bg.alpha_composite(f)
        big.append(bg.resize((288, 288), Image.NEAREST).convert("RGB"))
    big[0].save(os.path.join(OUT_PREV, f"{name}.gif"), save_all=True, append_images=big[1:],
                duration=ms, loop=0)


if __name__ == "__main__":
    only = sys.argv[1:] or list(ANIMS)
    for name in only:
        fn, n, ms = ANIMS[name]
        b = native(name)
        frames = []
        for i in range(n):
            r = fn(b, i, n)
            frames.append(r if r.size == (72, 72) else to72(name, r))
        save(name, frames, ms)
        print(name, f"{n}f x {ms}ms", f"{os.path.getsize(os.path.join(OUT_APNG, name + '.png')) / 1024:.1f}KB")
