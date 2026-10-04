#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG 示意图绘制工具包 —— 供 scripts/make-svgs.py 使用

设计约定
--------
- 画布宽固定 720，高按内容自定
- 颜色一律走 CSS 变量（--sf-* 系列，定义在 assets/css/extended/custom.css
  第 13 节），所以同一张图在浅色 / 深色主题下都能看清，不用出两套图
- 动效类（样式在 custom.css 第 13 节，触发逻辑在 custom.js 第 7 模块）：
    sf-pop    入场淡入上浮，错峰靠元素上的 --d 变量
    sf-draw   描边逐段生长，需要 pathLength="1" 归一化
    sf-flow   虚线流动，提示数据流向
    sf-pulse  透明度呼吸，用于强调
    sf-ring   扩散光圈，标记「出问题的地方」
- 无 JS 时这些元素静态可见；prefers-reduced-motion 下也整体静态化
"""

W = 720

# 箭头颜色 → 对应 CSS 变量
MARKER_KINDS = {
    "acc": "var(--sf-accent)",
    "warn": "var(--sf-warn)",
    "ok": "var(--sf-ok)",
    "dim": "var(--border)",
}


def esc(s):
    """XML 转义"""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _sty(d):
    return ' style="--d:%gs"' % d if d is not None else ""


class Fig:
    """一张 SVG 示意图的构建器"""

    def __init__(self, name, label, height):
        self.name = name          # 文件名（不含扩展名），同时用作 id 前缀
        self.label = label        # 无障碍标题
        self.h = height
        self.parts = []

    # ---------- 底层 ----------
    def raw(self, s):
        self.parts.append(s)
        return self

    def wrap(self, content, d):
        """按需把内容包进带动画的组；d=None 表示静态"""
        if d is None:
            return content
        return '<g class="sf-pop"%s>%s</g>' % (_sty(d), content)

    def _marker_id(self, kind):
        return "%s-ah-%s" % (self.name, kind)

    def _defs(self):
        out = ["<defs>"]
        for kind, color in MARKER_KINDS.items():
            out.append(
                '<marker id="%s" viewBox="0 0 10 10" refX="8.6" refY="5" '
                'markerWidth="4.6" markerHeight="4.6" orient="auto">'
                '<path d="M1.9 1.7 L7.4 5 L1.9 8.3" fill="none" stroke="%s" '
                'stroke-width="1.8" stroke-linecap="round" '
                'stroke-linejoin="round"/></marker>' % (self._marker_id(kind), color)
            )
        out.append("</defs>")
        return "".join(out)

    # ---------- 标题区 ----------
    def head(self, title, sub=None):
        self.raw('<text class="sf-title" x="24" y="26">%s</text>' % esc(title))
        if sub:
            self.raw('<text class="sf-sub" x="24" y="48">%s</text>' % esc(sub))
        return self

    # ---------- 文字 ----------
    def text(self, x, y, s, cls="sf-t", anchor="middle", mid=True, d=None):
        c = cls + (" sf-mid" if mid else "")
        el = '<text class="%s" x="%g" y="%g" text-anchor="%s">%s</text>' % (
            c, x, y, anchor, esc(s),
        )
        self.raw(self.wrap(el, d))
        return self

    # ---------- 盒子 ----------
    def box(
        self,
        x,
        y,
        w,
        h,
        label,
        sub=None,
        kind="sf-box",
        tcls="sf-t",
        subcls="sf-t-sm",
        rx=10,
        d=None,
        pop=True,
    ):
        ry = h / 2.0
        body = '<rect class="%s" x="%g" y="%g" width="%g" height="%g" rx="%g"/>' % (
            kind, x, y, w, h, rx,
        )
        cx = x + w / 2.0
        if sub:
            body += (
                '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
                % (tcls, cx, y + ry - 8, esc(label))
            )
            body += (
                '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
                % (subcls, cx, y + ry + 10, esc(sub))
            )
        else:
            body += (
                '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
                % (tcls, cx, y + ry, esc(label))
            )
        self.raw(self.wrap(body, d) if pop else body)
        return self

    def card(self, x, y, w, h, title, lines, kind="sf-box", tcls="sf-t", d=None, rx=10):
        """带多行说明的卡片：标题 + 若干行小字"""
        body = '<rect class="%s" x="%g" y="%g" width="%g" height="%g" rx="%g"/>' % (
            kind, x, y, w, h, rx,
        )
        n = len(lines) + 1
        line_h = 16
        top = y + h / 2.0 - (n - 1) * line_h / 2.0 - 1
        body += (
            '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
            % (tcls, x + w / 2.0, top, esc(title))
        )
        for i, (t, c) in enumerate(lines):
            body += (
                '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
                % (c, x + w / 2.0, top + (i + 1) * line_h, esc(t))
            )
        self.raw(self.wrap(body, d))
        return self

    def chip(self, x, y, w, h, label, kind="sf-box-a", tcls="sf-t-acc", d=None, rx=None):
        """小药丸标签"""
        if rx is None:
            rx = h / 2.0
        body = '<rect class="%s" x="%g" y="%g" width="%g" height="%g" rx="%g"/>' % (
            kind, x, y, w, h, rx,
        )
        body += (
            '<text class="%s sf-mid" x="%g" y="%g" text-anchor="middle">%s</text>'
            % (tcls, x + w / 2.0, y + h / 2.0, esc(label))
        )
        self.raw(self.wrap(body, d))
        return self

    def frame(self, x, y, w, h, label=None, d=None, rx=14, anchor="start"):
        """虚线分组框"""
        body = (
            '<rect class="sf-box-ghost" x="%g" y="%g" width="%g" height="%g" rx="%g"/>'
            % (x, y, w, h, rx)
        )
        if label:
            lx = x + 14 if anchor == "start" else x + w / 2.0
            body += (
                '<text class="sf-t-sm" x="%g" y="%g" text-anchor="%s">%s</text>'
                % (lx, y + 16, anchor, esc(label))
            )
        self.raw(self.wrap(body, d))
        return self

    # ---------- 连线 ----------
    def line(self, pts, kind="sf-line", marker="acc", d=None, draw=True, dash=None,
             width=None, opacity=None, tail=None):
        dstr = "M%g %g" % pts[0] + "".join(" L%g %g" % p for p in pts[1:])
        cls = kind + (" sf-draw" if draw else "")
        attrs = ""
        if draw:
            attrs += ' pathLength="1"'
        if marker:
            attrs += ' marker-end="url(#%s)"' % self._marker_id(marker)
        if dash:
            attrs += ' stroke-dasharray="%s"' % dash
        if width:
            attrs += ' stroke-width="%g"' % width
        if opacity is not None:
            attrs += ' stroke-opacity="%g"' % opacity
        el = '<path class="%s" d="%s"%s%s/>' % (cls, dstr, attrs, _sty(d))
        self.raw(el)
        return self

    def curve(self, path, kind="sf-line", marker="acc", d=None, draw=True, dash=None):
        """任意曲线（贝塞尔等），path 为原始 d 属性字符串"""
        cls = kind + (" sf-draw" if draw else "")
        attrs = ' pathLength="1"' if draw else ""
        if marker:
            attrs += ' marker-end="url(#%s)"' % self._marker_id(marker)
        if dash:
            attrs += ' stroke-dasharray="%s"' % dash
        self.raw('<path class="%s" d="%s"%s%s/>' % (cls, path, attrs, _sty(d)))
        return self

    def ring(self, cx, cy, r, d=None, kind="warn"):
        """扩散光圈，标记问题点"""
        color = "var(--sf-%s)" % kind
        self.raw(
            '<circle class="sf-ring" cx="%g" cy="%g" r="%g" fill="none" '
            'stroke="%s" stroke-width="1.6"%s/>' % (cx, cy, r, color, _sty(d))
        )
        return self

    def dot(self, cx, cy, r=3.4, color="var(--sf-accent)", d=None, cls=""):
        self.raw(
            '<circle class="%s" cx="%g" cy="%g" r="%g" fill="%s"%s/>'
            % (cls, cx, cy, r, color, _sty(d))
        )
        return self

    # ---------- 输出 ----------
    def render(self):
        return (
            '<svg viewBox="0 0 %g %g" role="img" aria-labelledby="%s-t">\n'
            '<title id="%s-t">%s</title>\n%s\n%s\n</svg>\n'
            % (
                W,
                self.h,
                self.name,
                self.name,
                esc(self.label),
                self._defs(),
                "\n".join(self.parts),
            )
        )
