"""2개월 후보 4종 렌더: candidates/02A~D.gif (최종은 C 뿅망치를 다듬어 animate2.py에 넣음)."""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from animate2 import *  # noqa
from PIL import Image

OUTC = os.path.join(HERE, "candidates")
os.makedirs(OUTC, exist_ok=True)
SKIN = (183, 248, 255, 255)


def gum(b, i, n):
    """A 껌 풍선: 질겅질겅 → 풍선 부풀림 → 팡! → 얼굴에 껌 → 원래대로."""
    t = i / n
    f = b.copy()
    if t < 0.2:
        if (i // 2) % 2:
            rect(f, 8, 14, 13, 16, SKIN)
            rect(f, 9, 14, 12, 15, (241, 162, 162, 255))
        return f
    if t < 0.6:
        r = 0.8 + 4.2 * win(t, 0.2, 0.6)
        cx, cy = 10, 14.5
        for y in range(18):
            for x in range(18):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    c = (255, 150, 190, 255) if d <= r - 1 else (210, 80, 130, 255)
                    put(f, x, y, c)
        put(f, round(cx - r * 0.5), round(cy - r * 0.5), WHITE)
        return f
    if t < 0.66:
        f = sparkle(f, 10, 14, 2, WHITE, (255, 180, 210, 255))
        for (x, y) in ((4, 12), (15, 12), (6, 16), (14, 16), (3, 15), (16, 15)):
            put(f, x, y, (255, 150, 190, 255))
        return f
    if t < 0.85:
        for (x, y) in ((7, 13), (8, 12), (11, 12), (12, 13), (6, 14), (13, 14), (9, 15), (10, 15), (8, 14), (11, 14)):
            put(f, x, y, (255, 150, 190, 255))
        return f
    return f


CONF = [(255, 80, 90, 255), (255, 210, 60, 255), (90, 200, 255, 255), (120, 230, 120, 255), (200, 120, 255, 255), WHITE]


def confetti(b, i, n):
    """B 축하 꽃가루: 펑! → 색색 꽃가루가 흩날리며 떨어짐 + 신나서 통통."""
    t = i / n
    f = squash(b, [11]) if (i // 3) % 2 else b.copy()
    if t < 0.12:
        f = sparkle(f, 9, 2, 2 if t < 0.06 else 1, (255, 240, 120, 255), (255, 120, 80, 255))
    rnd = random.Random(5)
    for k in range(16):
        x0 = rnd.uniform(0, 17)
        vy = rnd.uniform(14, 22)
        ph = rnd.uniform(0, 6.28)
        c = CONF[k % len(CONF)]
        tt = (t - 0.05 + rnd.uniform(0, 0.15)) % 1
        y = -1 + vy * tt
        x = x0 + 1.5 * math.sin(tt * 12 + ph)
        if 0 <= y < 18:
            put(f, round(x), round(y), c)
    return f


HAMMER_UP = ["...RRR", "..RYYR", ".RRYRR", ".RRR..", "B.....", "B....."]
HAMMER_HIT = ["RRRRRR", "YYYYYY", "RRRRRR", "..BB..", "..B...", ".B...."]


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


def hammer(b, i, n):
    """C 뿅망치: 뿅망치가 들렸다가 → 뿅! 머리 때림 → 납작 + 별 빙글 → 띠용 복귀."""
    t = i / n
    pal = {"R": (240, 50, 60, 255), "Y": (255, 220, 70, 255), "B": (150, 90, 40, 255)}
    if t < 0.3:
        f = b.copy()
        if t >= 0.12:
            f = stamp(f, ol(HAMMER_UP, pal), 11, -1)
        return f
    if t < 0.36:
        f = squash(b, [9, 10, 11])
        f = stamp(f, ol(HAMMER_HIT, pal), 5, -1)
        return sparkle(f, 12, 1, 2)
    if t < 0.7:
        f = squash(b, [9, 10, 11]) if t < 0.55 else squash(b, [10])
        a = (t - 0.36) * 2 * math.pi * 3
        for k in range(3):
            x = round(9 + 6 * math.cos(a + k * 2.1))
            y = round(3 + 1.5 * math.sin(a + k * 2.1))
            put(f, x, y, (255, 230, 70, 255))
        return f
    if t < 0.8:
        return pinch(b, [3, 14])
    return b.copy()


BULB = [".YYY.", "YWYYY", "YYYYY", ".YYY.", ".GGG.", "..G.."]


def bulb(b, i, n):
    """D 전구 번쩍: 웅크림 → 띵! 머리 위 전구 켜짐 + 빛 + 쭉 솟음 → 원래대로."""
    t = i / n
    if t < 0.25:
        return b.copy()
    if t < 0.35:
        return squash(b, [11])
    if t >= 0.85:
        return b.copy()
    f = pinch(b, [3, 14]) if t < 0.45 else b.copy()
    on = t >= 0.4
    pal = {"Y": (255, 230, 80, 255) if on else (120, 110, 70, 255), "W": WHITE if on else (160, 160, 140, 255),
           "G": (150, 150, 160, 255)}
    f = stamp(f, ol(BULB, pal), 12, -1)
    if on and (i // 2) % 2 == 0:
        for (x, y) in ((11, 0), (17, 0), (11, 4), (17, 4)):
            put(f, x, y, (255, 245, 150, 255))
    return f


if __name__ == "__main__":
    b = native("02")
    for tag, fn, n, ms in (("A_gum", gum, 28, 65), ("B_confetti", confetti, 30, 60),
                           ("C_hammer", hammer, 28, 60), ("D_bulb", bulb, 24, 65)):
        frames = [to72("02", fn(b, i, n)) for i in range(n)]
        big = []
        for fr in frames:
            bg = Image.new("RGBA", (72, 72), (40, 42, 46, 255))
            bg.alpha_composite(fr)
            big.append(bg.resize((288, 288), Image.NEAREST).convert("RGB"))
        big[0].save(os.path.join(OUTC, f"02{tag}.gif"), save_all=True, append_images=big[1:], duration=ms, loop=0)
        print(tag)
