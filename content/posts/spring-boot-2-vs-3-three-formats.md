---
title: "Spring Boot 2 → 3：同一份内容，三种动态呈现"
date: 2026-10-04
draft: false
description: "把「Spring Boot 2 与 3 的差异」这一个话题，分别做成 SVG 动画、自托管视频和嵌入式幻灯片，并附上三种方式的完整写法与取舍。"
summary: "静态图文讲不清的「变化」，动起来就一目了然。这一篇既是 Spring Boot 升级点的讲解，也是一次关于「动态内容怎么放进博客」的完整实验。"
tags: ["Spring Boot", "Java", "SVG", "Hugo", "前端"]
categories: ["技术笔记"]
ShowToc: true
---

## 这一篇本身就是个实验

下面三节讲的是**同一个话题**——Spring Boot 从 2.x 升到 3.x 到底变了什么。但每一节用的呈现方式都不一样：SVG 动画、视频、幻灯片。

如果你也在纠结「博客里想放点动态的东西，到底该用哪种」，看完这三节基本就有答案了。技术实现我都写在每节后面了，代码可以直接抄。

---

## 一、SVG 动画：最轻，最适合嵌在正文里

先看效果——往下滚到它进入视野时，六行对比会依次浮现：

{{< sb-compare >}}

这个东西的全部成本是 **约 6 KB 的 SVG 代码**，没有图片、没有视频、没有任何外部请求。它不是 GIF，是把二十来行 `<rect>` 和 `<text>` 加上 CSS 动画做出来的，所以放大到任何尺寸都清晰，深色模式下颜色还会自动跟着变。

### 关键做法

**① 用 CSS 变量取色，就能自动适配深浅色主题。** 卡片和文字都不写死颜色：

```css
.sb-compare .sc-card-old { fill: var(--code-bg); stroke: var(--border); }
.sb-compare .sc-val-new  { fill: var(--primary); }
```

主题切换时 `--primary` 这类变量会变，SVG 跟着就变了，一行额外代码都不用写。

**② 只有 JS 可用时才先隐藏元素。** 这是最容易被忽略的一步。如果你直接写 `opacity: 0` 然后靠 JS 加类来显示，那么脚本加载失败的用户会看到一片空白。正确做法是先给 `<html>` 打个标记，再基于这个标记隐藏：

```js
// 在 <head> 里尽早执行
document.documentElement.classList.add("js-reveal");
```

```css
.js-reveal .sb-compare .sc-row { opacity: 0; }          /* 仅 JS 可用时隐藏 */
.js-reveal .sb-compare.is-playing .sc-row {             /* 进入视口后才播 */
    animation: sc-enter 0.5s var(--ease-out) forwards;
}
```

**③ 滚进视口才播，并且只播一次。** 用 `IntersectionObserver` 加个 `is-playing` 类就够了，播完自动 `unobserve`：

```js
var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
        if (entry.isIntersecting) {
            entry.target.classList.add("is-playing");
            observer.unobserve(entry.target);
        }
    });
}, { threshold: 0.2 });
```

**④ 一定要给「关掉动画」的用户留活路。** 系统里开了 `prefers-reduced-motion` 的用户（晕动症人群），动画要整体降级成静态：

```css
@media (prefers-reduced-motion: reduce) {
    .sb-compare .sc-row { opacity: 1 !important; animation: none !important; }
}
```

### 适合什么 / 不适合什么

**适合**：流程图、架构对比、时间线、数据关系——这类「结构本身就能说明问题」的内容。

**不适合**：需要真实画面（录屏、产品演示）、内容很长需要分页讲、或者你已经有一份现成的 PPT / 视频。

---

## 二、视频：观感最像「讲解」，但要管住体积

同上内容，做成了 17 秒的动画视频：

<video controls preload="metadata" playsinline
       poster="/blog/videos/spring-boot-2-vs-3-poster.jpg"
       style="width:100%;border-radius:14px;display:block;margin:0 auto">
  <source src="/blog/videos/spring-boot-2-vs-3.mp4" type="video/mp4">
  你的浏览器不支持 video 标签，<a href="/blog/videos/spring-boot-2-vs-3.mp4">点此下载视频</a>。
</video>

**17 秒 / 1280×720 / 只有 0.28 MB。** 这个体积意味着：直接扔进 Git 仓库毫无压力，也不会拖慢页面。

### 关键做法

**视频是这个脚本生成的**，`scripts/make-demo-video.py`，用 Pillow 逐帧渲染 PNG，再交给 ffmpeg 编码：

```bash
# 核心就两步
python scripts/make-demo-video.py
# 内部流程：[1] 渲染 510 帧 PNG  →  [2] ffmpeg 编码成 mp4
```

几个让体积这么小的关键点：

| 做法 | 作用 |
|---|---|
| `-crf 23` | H.264 的恒定质量参数，23 是「肉眼无损」和体积的甜点值 |
| `-preset slow` | 编码慢一点，换来更小的文件 |
| `-pix_fmt yuv420p` | **必须加**，否则 Safari / 部分播放器不认 |
| `-movflags +faststart` | 把元数据挪到文件头，页面里能边下边播，不用等下完 |

**如果是真人录屏或者现成视频**，那就压缩后再传。别用 GIF——同一段内容 GIF 比 MP4 大 5 到 10 倍，而且颜色只有 256 色。

**实在太大就传 B 站再嵌入**，仓库一兆都不占：

```html
<iframe src="//player.bilibili.com/player.html?bvid=BV1xx411c7mD&autoplay=0"
        scrolling="no" frameborder="no" allowfullscreen="true"
        style="width:100%;aspect-ratio:16/9;border:0;border-radius:14px"></iframe>
```

### 那个绕不过去的体积红线

| 限制 | 数值 |
|---|---|
| GitHub 单个文件上限 | **100 MB**（超了直接拒绝 push） |
| 仓库 / Pages 站点建议 | < 1 GB |
| Pages 月流量软限制 | 100 GB |

最后提醒一句：**视频一旦提交进 Git，就算之后删掉，历史包里还是留着**，仓库会永久变大。大文件宁可走外链。

---

## 三、幻灯片：适合按页讲的东西

同样的话题，这次做成可翻页的幻灯片：

<iframe src="/blog/slides/spring-boot-2-vs-3.html"
        style="width:100%;aspect-ratio:16/9;border:0;border-radius:14px;display:block"
        allowfullscreen loading="lazy"
        title="Spring Boot 2 vs 3 幻灯片"></iframe>

操作方式：**← →** 翻页，**空格**下一页，**F** 全屏，手机可以左右滑。也可以直接点上面的圆点跳页。

如果这里显示不出来，[点开全屏看](/blog/slides/spring-boot-2-vs-3.html)。

### 关键做法

我没有引 Reveal.js，而是手写了一个**零依赖**的轻量版——总共不到 200 行，加载零延迟，样式还能完全跟着博客的品牌配色走。

核心机制其实非常简单：**所有页都绝对定位叠在一起，只让当前页 `opacity: 1`。**

```css
.slide {
    position: absolute; inset: 0;
    opacity: 0;
    transform: translateY(26px);
    pointer-events: none;
    transition: opacity .46s var(--ease), transform .46s var(--ease);
}
.slide.is-active {
    opacity: 1; transform: none; pointer-events: auto;
}
```

翻页就是切一下类名：

```js
slides.forEach(function (s, i) {
    s.classList.toggle("is-active", i === n);
});
```

再补上键盘、触摸滑动、滚轮（记得加节流，否则一滚跳好几页）和 `#3` 这样的 URL 定位就好了。

**iframe 的两个坑**：

1. **高度一定要显式给**，否则会塌成一条线。推荐用 `aspect-ratio: 16/9` 而不是写死像素，这样窄屏也能等比缩放。
2. **想全屏就必须加 `allowfullscreen`**，不然幻灯片里的全屏按钮是死的。

### 和 Reveal.js 比

| | 手写轻量版 | Reveal.js |
|---|---|---|
| 体积 | 约 8 KB | 约 250 KB |
| 效果 | 淡入淡出 + 位移 | 3D 翻转、演讲者视图、导出 PDF |
| 依赖 | 零 | 需要引 CSS/JS |
| 定制 | 完全自由 | 要按它的主题体系来 |

**结论很简单**：只是想在文章里嵌几页讲解，手写就够了；要做正式的技术分享、需要演讲者视图和 PDF 导出，那就用 Reveal.js。

---

## 三种方式怎么选

| | SVG 动画 | 视频 | 幻灯片 |
|---|---|---|---|
| **体积** | KB 级 | MB 级 | KB 级 |
| **可复制文字** | ✅ 能选中文案 | ❌ | ✅ |
| **跟随深色模式** | ✅ 自动 | ❌ 固定画面 | 需自己处理 |
| **能放真实录屏** | ❌ | ✅ | ❌ |
| **适合长度** | 一屏 | 1~3 分钟 | 多页 |
| **搜索引擎收录** | ✅ 文字可索引 | ❌ | ⚠️ iframe 内不易收录 |

我自己的判断顺序是这样：

1. **能用 SVG 讲清的，就用 SVG。** 它是唯一既轻、又能跟着主题变色、文字还能被搜索引擎收录的方案。
2. **需要真实画面（录屏、操作演示）才上视频**，并且务必先压缩。
3. **内容天然是「一页一页」的，用幻灯片**，并且优先手写轻量版。

有一件事三种方式都一样：**别让内容依赖 JavaScript 才能被看见**。加动画是锦上添花，不是雪中送炭——脚本挂了，文章也得能读。

---

## 附：三个可复制的片段

**SVG 动画**——把 SVG 存成 `layouts/shortcodes/你的名字.html`，文章里一行调用：

```markdown
{{</* sb-compare */>}}
```

**本地视频**：

```html
<video controls preload="metadata" playsinline
       poster="/blog/videos/xxx-poster.jpg"
       style="width:100%;border-radius:14px;display:block">
  <source src="/blog/videos/xxx.mp4" type="video/mp4">
</video>
```

**幻灯片**（`static/slides/xxx.html` 放好之后）：

```html
<iframe src="/blog/slides/xxx.html"
        style="width:100%;aspect-ratio:16/9;border:0;border-radius:14px"
        allowfullscreen loading="lazy"></iframe>
```

⚠️ 最后提醒一个本站踩过的老坑：**路径一定要带 `/blog/` 前缀**。因为这是 GitHub Pages 的**项目站点**，根路径是 `elthereal-star.github.io`，写 `/videos/x.mp4` 会跑到根域名下变成 404，必须写成 `/blog/videos/x.mp4`。
