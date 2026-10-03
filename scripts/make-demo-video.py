# -*- coding: utf-8 -*-
"""
生成「Spring Boot 2 vs 3」讲解视频（mp4）
=========================================================
用法：
    python make-demo-video.py

输出：
    static/videos/spring-boot-2-vs-3.mp4

原理：
    用 Pillow 逐帧渲染 PNG（深色科技风），再用 ffmpeg 编码成 H.264 mp4。
    不依赖任何在线素材，脚本可重复执行，改文案只改下面的 ITEMS。

依赖：
    pillow（必需）、ffmpeg（可用环境变量 FFMPEG 指定路径）
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- 规格
W, H, FPS = 1280, 720, 30
DUR_OPEN, DUR_ITEM, DUR_END = 3.0, 1.8, 3.2

ITEMS = [
    ("Java 基线", "Java 8 起步", "Java 17 起步"),
    ("命名空间", "javax.*", "jakarta.*"),
    ("框架内核", "Spring Framework 5.3", "Spring Framework 6.0"),
    ("自动配置", "spring.factories", "AutoConfiguration.imports"),
    ("原生镜像", "Spring Native（实验）", "GraalVM AOT 内置"),
    ("可观测性", "Spring Cloud Sleuth", "Micrometer Observation"),
]

TOTAL = DUR_OPEN + DUR_ITEM * len(ITEMS) + DUR_END

ROOT = Path(__file__).resolve().parent.parent
OUT_MP4 = ROOT / "static" / "videos" / "spring-boot-2-vs-3.mp4"

FFMPEG_CANDIDATES = [
    os.environ.get("FFMPEG", ""),
    r"C:\Users\baishanxing\.workbuddy\binaries\ffmpeg\ffmpeg.exe",
    "ffmpeg",
]

# ---------------------------------------------------------------- 配色
C_BG_TOP = (22, 25, 48)
C_BG_BOT = (9, 10, 18)
C_TEXT = (238, 240, 250)
C_MUTED = (150, 157, 192)
C_DIM = (98, 104, 138)
C_OLD_CARD = (30, 33, 54)
C_OLD_LINE = (54, 59, 92)
C_OLD_TEXT = (150, 157, 192)
C_NEW_CARD = (32, 44, 96)
C_NEW_LINE = (79, 108, 240)
C_NEW_TEXT = (235, 240, 255)

BRAND = [(79, 108, 240), (124, 92, 235), (224, 93, 190)]

# ---------------------------------------------------------------- 字体
FONT_REG = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhl.ttc",
            r"C:\Windows\Fonts\simhei.ttf"]
FONT_BOLD = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
             r"C:\Windows\Fonts\simhei.ttf"]

_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    for path in (FONT_BOLD if bold else FONT_REG):
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                _font_cache[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def fit_font(text, max_width, base=32, min_size=16, bold=False):
    """按可用宽度自动缩字号，避免长英文串溢出卡片"""
    size = base
    while size > min_size:
        f = font(size, bold)
        if f.getlength(text) <= max_width:
            return f
        size -= 1
    return font(min_size, bold)


# ---------------------------------------------------------------- 工具
def clamp01(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def seg(t, start, dur):
    """把时间轴切段并归一化到 0..1"""
    if dur <= 0:
        return 1.0
    return clamp01((t - start) / dur)


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t):
    return 4 * t ** 3 if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def blend_stops(stops, t):
    if t <= 0:
        return stops[0]
    if t >= 1:
        return stops[-1]
    n = len(stops) - 1
    i = int(t * n)
    local = t * n - i
    return lerp_color(stops[i], stops[min(i + 1, n)], local)


def rgba(color, alpha):
    return (color[0], color[1], color[2], int(clamp01(alpha) * 255))


# ---------------------------------------------------------------- 预渲染背景
def make_background():
    """竖直渐变 + 中心柔光，只算一次，每帧 copy"""
    small = Image.new("RGB", (16, 16))
    px = small.load()
    for y in range(16):
        c = lerp_color(C_BG_TOP, C_BG_BOT, y / 15)
        for x in range(16):
            px[x, y] = c
    bg = small.resize((W, H), Image.BICUBIC)

    # 中心柔光：小图径向渐变后放大，省掉逐像素计算
    g = Image.new("L", (64, 64), 0)
    gp = g.load()
    for y in range(64):
        for x in range(64):
            dx = (x - 32) / 32.0
            dy = (y - 32) / 32.0
            d = min(1.0, (dx * dx + dy * dy) ** 0.5)
            gp[x, y] = int((1 - d) ** 2.2 * 62)
    glow = g.resize((W, H), Image.BICUBIC)
    tint = Image.new("RGB", (W, H), (79, 108, 240))
    bg.paste(tint, (0, 0), glow)
    return bg


def make_gradient():
    """品牌横向渐变。刻意把蓝→紫→粉三色变化压在画布中间 70% 宽度内，
       这样居中排版的标题才能跨过完整的渐变色域，而不是只取到中间一段紫色。"""
    small = Image.new("RGB", (64, 64))
    px = small.load()
    for y in range(64):
        for x in range(64):
            t = clamp01((x / 63.0 - 0.15) / 0.70)
            px[x, y] = blend_stops(BRAND, t)
    return small.resize((W, H), Image.BICUBIC)


def draw_gradient_text(img, grad, xy, text, fnt, alpha=1.0, anchor="mm"):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt,
                              fill=int(clamp01(alpha) * 255), anchor=anchor)
    img.paste(grad, (0, 0), mask)


def draw_star(d, cx, cy, r, color):
    """四角星徽标（和站点 favicon 同一形状）"""
    k = r * 0.30
    d.polygon([
        (cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
        (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k),
    ], fill=color)


# ---------------------------------------------------------------- 场景：开场
def render_open(t, img, grad):
    d = ImageDraw.Draw(img, "RGBA")
    out = 1.0 - seg(t, DUR_OPEN - 0.5, 0.5)          # 末段整体淡出
    if out <= 0:
        return
    shift = (1.0 - out) * -26                         # 淡出时向上飘

    a_logo = ease_out(seg(t, 0.10, 0.55))
    if a_logo > 0:
        draw_star(d, 640, 232 + shift, 40 * (0.85 + 0.15 * a_logo),
                  rgba(blend_stops(BRAND, 0.5), a_logo * out))

    a_title = ease_out(seg(t, 0.45, 0.6))
    if a_title > 0:
        f = font(58, True)
        draw_gradient_text(img, grad, (640, 338 + shift),
                           "Spring Boot 2 → 3", f, a_title * out)

    a_sub = ease_out(seg(t, 0.85, 0.6))
    if a_sub > 0:
        d.text((640, 404 + shift), "六项必须知道的变更", font=font(26),
               fill=rgba(C_MUTED, a_sub * out), anchor="mm")

    a_foot = ease_out(seg(t, 1.15, 0.6))
    if a_foot > 0:
        d.text((640, 632 + shift), "elthereal-star.github.io/blog",
               font=font(19), fill=rgba(C_DIM, a_foot * out), anchor="mm")


# ---------------------------------------------------------------- 场景：逐条对比
def render_item(u, idx, img, grad):
    d = ImageDraw.Draw(img, "RGBA")

    env = min(clamp01(u / 0.28), clamp01((DUR_ITEM - u) / 0.30))
    if env <= 0:
        return

    dim, old_val, new_val = ITEMS[idx]

    # 顶部进度点
    n = len(ITEMS)
    for i in range(n):
        cx = 640 + (i - (n - 1) / 2) * 34
        if i < idx:
            col, rad = rgba(BRAND[2], 0.75 * env), 5
        elif i == idx:
            col, rad = rgba(BRAND[0], 1.0 * env), 7
        else:
            col, rad = rgba(C_DIM, 0.35 * env), 5
        d.ellipse([cx - rad, 76 - rad, cx + rad, 76 + rad], fill=col)

    # 维度名
    a_dim = ease_out(seg(u, 0.18, 0.45))
    if a_dim > 0:
        f = fit_font(dim, 620, base=36, bold=True)
        d.text((640, 228), dim, font=f,
               fill=rgba(C_TEXT, a_dim * env), anchor="mm")

    # 左卡（旧版）：从左滑入
    a_old = ease_out(seg(u, 0.30, 0.45))
    if a_old > 0:
        dx = (1 - a_old) * -34
        box = [90 + dx, 296, 540 + dx, 428]
        d.rounded_rectangle(box, radius=18,
                            fill=rgba(C_OLD_CARD, a_old * env),
                            outline=rgba(C_OLD_LINE, a_old * env), width=2)
        d.text((315 + dx, 330), "Spring Boot 2.x", font=font(19),
               fill=rgba(C_DIM, a_old * env), anchor="mm")
        fv = fit_font(old_val, 400, base=31, min_size=17)
        d.text((315 + dx, 388), old_val, font=fv,
               fill=rgba(C_OLD_TEXT, a_old * env), anchor="mm")

    # 中间箭头：从左往右长出来
    a_arrow = ease_out(seg(u, 0.55, 0.4))
    if a_arrow > 0:
        x0, x1, y = 556, 724, 362
        xe = x0 + (x1 - x0) * a_arrow
        col = rgba(BRAND[1], a_arrow * env)
        d.line([x0, y, xe, y], fill=col, width=3)
        if a_arrow > 0.85:
            head = (a_arrow - 0.85) / 0.15
            tip = x1
            d.polygon([(tip, y), (tip - 16, y - 9 * head),
                       (tip - 16, y + 9 * head)],
                      fill=rgba(BRAND[1], head * env))

    # 右卡（新版）：从右滑入
    a_new = ease_out(seg(u, 0.70, 0.45))
    if a_new > 0:
        dx = (1 - a_new) * 34
        box = [740 + dx, 296, 1190 + dx, 428]
        d.rounded_rectangle(box, radius=18,
                            fill=rgba(C_NEW_CARD, a_new * env),
                            outline=rgba(C_NEW_LINE, a_new * env), width=2)
        d.text((965 + dx, 330), "Spring Boot 3.x", font=font(19),
               fill=rgba(BRAND[0], a_new * env), anchor="mm")
        fv = fit_font(new_val, 400, base=31, min_size=17, bold=True)
        d.text((965 + dx, 388), new_val, font=fv,
               fill=rgba(C_NEW_TEXT, a_new * env), anchor="mm")


# ---------------------------------------------------------------- 场景：结尾
def render_end(t, img, grad):
    d = ImageDraw.Draw(img, "RGBA")
    env = min(clamp01(t / 0.4), clamp01((DUR_END - t) / 0.5))
    if env <= 0:
        return

    a1 = ease_out(seg(t, 0.15, 0.6))
    if a1 > 0:
        f = fit_font("javax.* → jakarta.*", 900, base=64, bold=True)
        draw_gradient_text(img, grad, (640, 306),
                           "javax.* → jakarta.*", f, a1 * env)

    a2 = ease_out(seg(t, 0.55, 0.6))
    if a2 > 0:
        d.text((640, 386), "六项里唯一的全量改名", font=font(28),
               fill=rgba(C_MUTED, a2 * env), anchor="mm")

    a3 = ease_out(seg(t, 0.95, 0.6))
    if a3 > 0:
        d.text((640, 448), "其余属于依赖升级与机制换代", font=font(22),
               fill=rgba(C_DIM, a3 * env), anchor="mm")
        draw_star(d, 640, 556, 22, rgba(blend_stops(BRAND, 0.5), a3 * env))
        d.text((640, 612), "elthereal-star 的技术笔记", font=font(19),
               fill=rgba(C_DIM, a3 * env), anchor="mm")


# ---------------------------------------------------------------- 主流程
def find_ffmpeg():
    for c in FFMPEG_CANDIDATES:
        if not c:
            continue
        if c == "ffmpeg":
            if shutil.which("ffmpeg"):
                return "ffmpeg"
            continue
        if os.path.exists(c):
            return c
    raise SystemExit("找不到 ffmpeg，请设置环境变量 FFMPEG 指向可执行文件")


def main():
    ffmpeg = find_ffmpeg()
    total_frames = int(round(TOTAL * FPS))
    print(f"[1/3] 渲染 {total_frames} 帧  {W}x{H} @ {FPS}fps  时长 {TOTAL:.1f}s")

    bg = make_background()
    grad = make_gradient()
    frames_dir = Path(tempfile.mkdtemp(prefix="sbvideo_"))

    item_span = DUR_ITEM * len(ITEMS)
    try:
        for i in range(total_frames):
            t = i / FPS
            img = bg.copy()
            if t < DUR_OPEN:
                render_open(t, img, grad)
            elif t < DUR_OPEN + item_span:
                u = t - DUR_OPEN
                idx = min(int(u // DUR_ITEM), len(ITEMS) - 1)
                render_item(u - idx * DUR_ITEM, idx, img, grad)
            else:
                render_end(t - DUR_OPEN - item_span, img, grad)
            img.save(frames_dir / f"f_{i:05d}.png")
            if i % 90 == 0:
                print(f"      {i}/{total_frames}")

        print("[2/3] ffmpeg 编码中…")
        OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error",
             "-framerate", str(FPS),
             "-i", str(frames_dir / "f_%05d.png"),
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-crf", "23", "-preset", "slow",
             "-movflags", "+faststart",
             str(OUT_MP4)],
            check=True,
        )
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)

    size_mb = OUT_MP4.stat().st_size / 1048576
    print(f"[3/3] 完成 → {OUT_MP4}")
    print(f"      体积 {size_mb:.2f} MB  时长 {TOTAL:.1f}s")


if __name__ == "__main__":
    main()
