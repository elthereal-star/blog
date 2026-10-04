#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取并自托管博客所需字体 —— 保持整站零第三方 CDN 请求。

为什么这么做
------------
Google Fonts 把中文字库切成上百个按 unicode-range 分片的子集，浏览器按需下载。
但自托管时如果照搬这套分片表，Noto Serif SC 会有「4 个权重 × 上百个分片」，
光这一项就 300+ 个文件、6MB 以上，仓库会被撑爆。

所以这里走的是「下载完整可变字体 → 本地一次性子集化」：

  1. 扫描仓库里所有会被渲染成文字的字符，得到站点实际用字
  2. 下载 4 款可变字体的完整源文件（含思源宋体 22MB 的 VF OTF）
  3. 用 fontTools 按「实际用字」裁出字形，输出为 woff2
  4. 生成 assets/css/extended/00-fonts.css

最终产物只有 5 个字体文件、总计约 1MB，且都是可变字体
（一个文件覆盖全部字重），页面加载时零外部请求。

用法
----
    # 需要先装好 fontTools 与 brotli
    pip install fonttools brotli

    python scripts/fetch-fonts.py

    # 国内直连 GitHub / Google 不通时走本地代理
    PROXY=http://127.0.0.1:65532 python scripts/fetch-fonts.py

源字体体积较大，会缓存在 .fontcache/src/ 下，重复执行不会重新下载。
"""

import os
import re
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_FONT_DIR = os.path.join(ROOT, "static", "fonts")
OUT_CSS = os.path.join(ROOT, "assets", "css", "extended", "00-fonts.css")
SRC_CACHE = os.path.join(ROOT, ".fontcache", "src")

PROXY = os.environ.get("PROXY", "").strip()

# ---------------------------------------------------------------
# 源字体（全部来自官方仓库的可变字体）
# ---------------------------------------------------------------
GF = "https://github.com/google/fonts/raw/main/ofl"

JOBS = [
    {
        "out": "inter-var.woff2",
        "url": GF + "/inter/Inter%5Bopsz,wght%5D.ttf",
        "src": "Inter-VF.ttf",
        "family": "Inter",
        "style": "normal",
        "charset": "latin",
        "features": "kern,liga,calt,ccmp,locl,tnum,case",
    },
    {
        "out": "newsreader-var.woff2",
        "url": GF + "/newsreader/Newsreader%5Bopsz,wght%5D.ttf",
        "src": "Newsreader-VF.ttf",
        "family": "Newsreader",
        "style": "normal",
        "charset": "latin",
        "features": "kern,liga,calt,ccmp,locl",
    },
    {
        "out": "newsreader-italic-var.woff2",
        "url": GF + "/newsreader/Newsreader-Italic%5Bopsz,wght%5D.ttf",
        "src": "Newsreader-Italic-VF.ttf",
        "family": "Newsreader",
        "style": "italic",
        "charset": "latin",
        "features": "kern,liga,calt,ccmp,locl",
    },
    {
        "out": "jetbrains-mono-var.woff2",
        "url": GF + "/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
        "src": "JetBrainsMono-VF.ttf",
        "family": "JetBrains Mono",
        "style": "normal",
        "charset": "latin",
        "features": "kern,liga,calt,ccmp,locl,zero",
    },
    {
        "out": "noto-serif-sc-var.woff2",
        "url": (
            "https://raw.githubusercontent.com/notofonts/noto-cjk/main/"
            "Serif/Variable/OTF/Subset/NotoSerifSC-VF.otf"
        ),
        "src": "NotoSerifSC-VF.otf",
        "family": "Noto Serif SC",
        "style": "normal",
        "charset": "site",  # 站点实际用字
        "features": "ccmp,locl,kern,liga,calt",
    },
]

# 拉丁文覆盖范围：ASCII + 西欧/中欧 + 标点 + 箭头 + 数学 + 几何 + 符号
# （图标、⌘K、→、±、✓ 这类字符也在其中）
LATIN_UNICODES = ",".join(
    [
        "U+0020-007E",
        "U+00A0-00FF",
        "U+0100-024F",
        "U+0250-02AF",
        "U+02B0-02FF",
        "U+0300-036F",
        "U+1E00-1EFF",
        "U+2000-206F",
        "U+2070-209F",
        "U+20A0-20BF",
        "U+2100-214F",
        "U+2150-218F",
        "U+2190-21FF",
        "U+2200-22FF",
        "U+2300-23FF",
        "U+2460-24FF",
        "U+2500-257F",
        "U+25A0-25FF",
        "U+2600-26FF",
        "U+2700-27BF",
        "U+2E00-2E7F",
        "U+FE00-FE0F",
        "U+FF00-FFEF",
    ]
)

# 扫描这些位置来收集站点会用到的字符
SCAN_TARGETS = [
    "content",
    "layouts",
    "i18n",
    "assets/js",
    "assets/svg",
    "static/slides",
    "themes/PaperMod/i18n",
    "themes/PaperMod/layouts",
    "hugo.yaml",
]
SCAN_EXT = {".md", ".html", ".yaml", ".yml", ".json", ".js", ".css", ".svg", ".txt"}

# 无论如何都要有的基础字符（界面文案、中文标点、图标字符）
EXTRA_CHARS = (
    "　、。〈〉《》「」『』【】〔〕・ー—–…‘’“”±×÷≈≠≤≥→←↑↓"
    "·°№§¶†‡•‰′″€£¥$¢©®™⌘⌥⇧⌫⌦⏎★☆✓✕"
)


def log(msg):
    print(msg, flush=True)


def curl(url, dest=None, timeout=900):
    cmd = ["curl", "-sSL", "--max-time", str(timeout), "-A", "Mozilla/5.0"]
    if PROXY:
        cmd += ["-x", PROXY]
    if dest:
        cmd += ["-o", dest, "-w", "%{http_code} %{size_download}"]
    else:
        cmd += ["-o", "-"]
    r = subprocess.run(cmd + [url], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("curl 失败: %s" % r.stderr.decode("utf-8", "replace")[:300])
    return r.stdout.decode("utf-8", "replace") if not dest else r.stdout.decode().strip()


def ensure_sources():
    os.makedirs(SRC_CACHE, exist_ok=True)
    for job in JOBS:
        path = os.path.join(SRC_CACHE, job["src"])
        if os.path.exists(path) and os.path.getsize(path) > 100000:
            job["srcpath"] = path
            continue
        log("· 下载源字体 %s …" % job["src"])
        out = curl(job["url"], dest=path)
        if not os.path.exists(path) or os.path.getsize(path) < 100000:
            raise RuntimeError("源字体下载失败：%s（%s）" % (job["src"], out))
        log("  %s → %.1f MB" % (job["src"], os.path.getsize(path) / 1048576))
        job["srcpath"] = path


def scan_site_chars():
    chars = set(EXTRA_CHARS)
    files = 0
    for target in SCAN_TARGETS:
        path = os.path.join(ROOT, target)
        if os.path.isfile(path):
            paths = [path]
        elif os.path.isdir(path):
            paths = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "public")]
                for fn in filenames:
                    if os.path.splitext(fn)[1].lower() in SCAN_EXT:
                        paths.append(os.path.join(dirpath, fn))
        else:
            continue
        for p in paths:
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    chars.update(f.read())
                files += 1
            except OSError:
                pass
    # 去掉控制字符
    chars = {c for c in chars if ord(c) >= 0x20}
    log("· 扫描 %d 个文件，站点用字 %d 个（其中汉字 %d 个）"
        % (files, len(chars), sum(1 for c in chars if 0x3400 <= ord(c) <= 0x9FFF)))
    return chars


def fvar_range(path, fallback):
    """读取可变字体的字重轴范围，写进 @font-face 的 font-weight。"""
    try:
        from fontTools.ttLib import TTFont

        font = TTFont(path, lazy=True)
        if "fvar" not in font:
            return fallback
        for axis in font["fvar"].axes:
            if axis.axisTag == "wght":
                return "%d %d" % (int(axis.minValue), int(axis.maxValue))
        return fallback
    except Exception:
        return fallback


def run_subset(job, chars):
    import tempfile

    font_dir = os.path.dirname(os.path.abspath(sys.executable))
    # 优先用 fontTools 的模块入口，避免依赖 Scripts/ 是否在 PATH
    args = [
        sys.executable,
        "-m",
        "fontTools.subset",
        job["srcpath"],
        "--output-file=" + os.path.join(OUT_FONT_DIR, job["out"]),
        "--flavor=woff2",
        "--layout-features=" + job["features"],
        "--name-IDs=*",
        "--drop-tables+=DSIG",
        "--no-hinting" if job["family"] != "Noto Serif SC" else "--hinting",
        "--recalc-bounds",
    ]
    if job["charset"] == "latin":
        args.append("--unicodes=" + LATIN_UNICODES)
    else:
        tmp = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write("".join(sorted(chars)))
        tmp.close()
        args.append("--text-file=" + tmp.name)
        job["_tmp"] = tmp.name

    r = subprocess.run(args, capture_output=True)
    if job.get("_tmp") and os.path.exists(job["_tmp"]):
        os.remove(job["_tmp"])
    if r.returncode != 0:
        raise RuntimeError(
            "子集化失败 %s:\n%s" % (job["out"], r.stderr.decode("utf-8", "replace")[-1500:])
        )


def write_css(jobs):
    header = """/* ============================================================
   自托管字体（由 scripts/fetch-fonts.py 生成，请勿手工编辑）

   全部字体文件位于 static/fonts/，整站不请求任何第三方字体服务。
   均为「可变字体」，一个文件覆盖全部字重；中文按站点实际用字做了子集化。
   若日后文章用到了新的生僻字，重新执行一次脚本即可补齐。
   ============================================================ */

"""
    # 重要：这个 CSS 会被 PaperMod 拼进 assets/css/stylesheet.css，
    # 也就是浏览器从 /assets/css/ 这个层级去解析相对地址，
    # 所以要回退两级才能指向站点根目录下的 /fonts/。这样写的好处是
    # 无论站点挂在域名根还是 /blog/ 子路径下都能正确解析。
    blocks = [header]
    for job in jobs:
        blocks.append(
            "@font-face {\n"
            "  font-family: '%s';\n"
            "  font-style: %s;\n"
            "  font-weight: %s;\n"
            "  font-display: swap;\n"
            "  src: url('../../fonts/%s') format('woff2');\n"
            "}\n\n" % (job["family"], job["style"], job["weight"], job["out"])
        )
    os.makedirs(os.path.dirname(OUT_CSS), exist_ok=True)
    with open(OUT_CSS, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(blocks))


def main():
    if not shutil.which("curl"):
        log("✗ 找不到 curl")
        return 1
    try:
        import fontTools  # noqa: F401
        import brotli  # noqa: F401
    except ImportError as e:
        log("✗ 缺少依赖（%s）。请先执行：pip install fonttools brotli" % e)
        return 1

    log("=== 抓取并自托管字体 ===")
    if PROXY:
        log("· 代理 %s" % PROXY)

    ensure_sources()
    chars = scan_site_chars()

    # --css-only：只按已缓存的源字体重新生成 CSS（改字体栈后快速重跑时用）
    if "--css-only" in sys.argv:
        for job in JOBS:
            job["weight"] = fvar_range(job["srcpath"], "400")
        write_css(JOBS)
        log("✓ 已按缓存源字体重新生成 %s" % os.path.relpath(OUT_CSS, ROOT))
        return 0

    if os.path.isdir(OUT_FONT_DIR):
        for fn in os.listdir(OUT_FONT_DIR):
            if fn.endswith(".woff2"):
                os.remove(os.path.join(OUT_FONT_DIR, fn))
    os.makedirs(OUT_FONT_DIR, exist_ok=True)

    total = 0
    for job in JOBS:
        log("· 子集化 %s …" % job["out"])
        run_subset(job, chars)
        size = os.path.getsize(os.path.join(OUT_FONT_DIR, job["out"]))
        total += size
        job["weight"] = fvar_range(job["srcpath"], "400")
        log("  → %s  %.0f KB  (weight %s)" % (job["out"], size / 1024, job["weight"]))

    write_css(JOBS)
    log("· 生成 %s" % os.path.relpath(OUT_CSS, ROOT))
    log("✓ 完成：static/fonts/ 共 %.2f MB（5 个文件）" % (total / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
