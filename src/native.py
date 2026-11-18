import math
from PIL import Image
GRID = {"01": (4, 0, 0), "02": (4, 0, 0), "03": (4, 0, 0), "06": (4, 0, 0), "09": (4, 0, 0), "12": (4, 0, 0),
        "18": (3, 2, 0), "24": (3, 2, 1), "30": (3, 2, 1), "36": (3, 2, 0), "42": (3, 2, 2), "48": (3, 2, 0),
        "54": (2, 0, 0)}
def geom(n):
    k, ox, oy = GRID[n]
    x0 = ox - k * math.ceil(ox / k); y0 = oy - k * math.ceil(oy / k)
    nw = math.ceil((72 - x0) / k); nh = math.ceil((72 - y0) / k)
    return k, x0, y0, nw, nh
def to_native(n, im):
    k, x0, y0, nw, nh = geom(n)
    px = im.load(); out = Image.new("RGBA", (nw, nh)); o = out.load()
    for cy in range(nh):
        for cx in range(nw):
            # 셀 안에서 캔버스 안쪽인 픽셀 하나 샘플
            x = min(71, max(0, x0 + cx * k + k - 1)) if x0 + cx * k < 0 else min(71, x0 + cx * k)
            y = min(71, max(0, y0 + cy * k + k - 1)) if y0 + cy * k < 0 else min(71, y0 + cy * k)
            o[cx, cy] = px[x, y]
    return out
def to72(n, nat):
    k, x0, y0, nw, nh = geom(n)
    big = nat.resize((nw * k, nh * k), Image.NEAREST)
    return big.crop((-x0, -y0, -x0 + 72, -y0 + 72))
