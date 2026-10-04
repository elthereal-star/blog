# elthereal-star 的技术笔记

个人技术博客的源码，基于 **Hugo + PaperMod**，通过 **GitHub Actions** 自动构建并部署到 **GitHub Pages**。
视觉上是一套叫「墨序」的极简风格：纸白 / 玄黑 / 羊皮纸三态配色、衬线标题、发丝边框、零渐变零发光。

- 线上地址：https://elthereal-star.github.io/blog/
- 文章目录：`content/posts/`（36 篇，其中 22 篇带内联 SVG 示意图）
- 项目介绍：`content/projects/`（5 篇）
- 图库：`assets/svg/`（24 张自绘 SVG，主题自适配深浅色）
- 字体：`static/fonts/`（5 个自托管子集 woff2，共约 1.3 MB）

## 它是怎么工作的

```text
本地写 Markdown  →  git push  →  GitHub Actions 构建  →  GitHub Pages 上线
                                      (hugo --minify)
```

整站是纯静态文件，不依赖任何后端服务；主题自带的搜索、图标等资源全部打包在仓库内，**不请求任何第三方 CDN**。

## 本地开发

需要 Hugo **extended** 版本，且 >= 0.146.0（PaperMod 使用新版模板系统）：

```bash
# Windows 安装（二选一）
winget install --id Hugo.Hugo.Extended -e

# 检查版本
hugo version
```

安装依赖并启动本地预览：

```bash
hugo server -D
```

浏览器打开 http://localhost:1313/blog/ —— 修改文件会自动热重载。

> `-D` 表示连草稿（`draft: true`）一起渲染，方便边写边看。

## 写一篇新文章

```bash
hugo new content posts/你的文章标题.md
```

模板在 `archetypes/default.md`，生成的文件头部已经带好必要字段：

| 字段 | 说明 |
| --- | --- |
| `title` | 文章标题 |
| `date` | 发布日期，**未来时间不会渲染**（`buildFuture: false`） |
| `draft` | `true` 时本地能看到、线上不发布 |
| `description` | 用于 SEO 和分享卡片 |
| `summary` | 列表页摘要；不填则自动截取正文前若干字 |
| `tags` / `categories` | 分类，会出现在标签页 |
| `ShowToc` | 是否显示右侧目录，长文建议 `true` |

写完提交推送即可：

```bash
git add .
git commit -m "post: 新增文章 xxx"
git push
```

推送到 `main` 后 Actions 会自动构建部署，一般 1～2 分钟上线。可以在仓库的 **Actions** 标签页查看构建日志。

## 目录结构

```text
blog/
├── .github/workflows/hugo.yml    # 自动部署流水线
├── hugo.yaml                     # 站点主配置（品牌、菜单、Hero、搜索等）
├── archetypes/default.md         # 新建文章模板
├── assets/
│   ├── css/extended/
│   │   ├── 00-fonts.css          # @font-face（由 fetch-fonts.py 生成，勿手改）
│   │   └── custom.css            # 「墨序」样式表，分 0~15 节
│   ├── js/custom.js              # 交互脚本，分 14 个模块
│   └── svg/                      # SVG 示意图图库（shortcode 内联使用）
├── layouts/                      # 项目级模板覆盖（优先于主题）
│   ├── baseof.html               # 页面骨架：三态主题初值 + 页头页脚挂载
│   ├── list.html                 # 列表页覆盖：卡片 + 带页码的分页导航
│   ├── _partials/
│   │   ├── header.html           # 顶部导航（品牌 / 菜单 / 搜索胶囊 / 图标组）
│   │   ├── footer.html           # 页脚 + 移动端标签栏 + 两个弹窗
│   │   ├── home_info.html        # 首页 Hero 区块
│   │   ├── post_card.html        # 文章卡片（列表页复用）
│   │   ├── icon.html             # 内联 Lucide 图标字典
│   │   ├── deploy_guide.html     # 部署指南弹窗内容
│   │   ├── extend_head.html      # <head> 注入点：主题预置 + js-reveal
│   │   └── extend_footer.html    # </body> 前注入点：进度条 + 指纹化脚本
│   └── shortcodes/
│       ├── svg.html              # 通用 SVG 图库：{{< svg "名字" >}}
│       └── sb-compare.html       # Spring Boot 2 vs 3 对比动画
├── i18n/zh-cn.yaml               # 中文界面文案
├── content/
│   ├── about.md                  # 关于我
│   ├── search.md                 # 搜索页
│   ├── archives.md               # 归档页
│   ├── posts/                    # 文章（36 篇）
│   └── projects/                 # 项目介绍（5 篇）
├── scripts/                      # 内容生成脚本（Python，非构建依赖）
│   ├── fetch-fonts.py            # 字体抓取 + 子集化 + 生成 00-fonts.css
│   ├── svgkit.py                 # SVG 生成 DSL 工具包
│   ├── make-svgs.py              # 批量生成 assets/svg/*.svg
│   ├── migrate-posts.py          # 把 Markdown 素材迁移成 Hugo 文章
│   └── make-demo-video.py        # Pillow 逐帧渲染 + ffmpeg 编码演示视频
├── static/
│   ├── fonts/                    # 自托管子集字体（5 个 woff2，约 1.3 MB）
│   ├── favicon*.png / .ico       # 站点图标
│   ├── images/<slug>/            # 文章配图（本地化，不再依赖图床）
│   ├── videos/                   # 演示视频（mp4 + poster）
│   └── slides/                   # 零依赖 HTML 幻灯片
└── themes/PaperMod/              # 主题（已内置进仓库）
```

> `scripts/` 只在**内容制作时**手动跑，CI 构建不需要 Python —— 生成的成品（字体 / SVG / 图片 / 视频 / 幻灯片）都已提交进仓库。

## 设计语言：「墨序」

整站视觉由一套叫「墨序」的极简体系控制，核心是**零渐变、零发光、零玻璃拟态**：

- **三态配色**：纸白 `#faf9f6`（默认）→ 玄黑 `#111113` → 羊皮纸 `#f7f3e8`（护眼）。点导航栏右侧的主题按钮循环切换，移动端底部标签栏也有入口。
- **字型分工**：衬线标题（Newsreader + Noto Serif SC）、无衬线正文（Inter）、等宽元信息（JetBrains Mono）。
- **发丝边框**：分隔线是 `rgba(23,23,23,.09)` 级别的极淡线；卡片靠 1px 边框分层，而不是投影。
- **克制的强调色**：只在状态点、置顶标记、下载、安全提示等处用一点绿 / 琥珀 / 玫红。

### 三态主题是怎么落地的

三态色板定义在 `custom.css` 的 `:root`（纸白）、`:root[data-mz-theme="dark"]`（玄黑）、`:root[data-mz-theme="sepia"]`（羊皮纸）三块里，统一用 `--mz-*` 前缀。

这一套值再**反向映射**回 PaperMod 自己的变量（`--theme` / `--entry` / `--primary` / `--secondary` / `--content` / `--border` / `--code-bg` …），于是主题自带的目录、代码块、表格、归档、搜索这些组件**一行都不用改就自动换装**。

主题初值写在 `layouts/baseof.html`，真正的取值由 `layouts/_partials/extend_head.html` 里的内联脚本在 `<body>` 解析前定下来（优先级：`?theme=` 参数 → `localStorage` → 系统偏好），所以刷新不会闪色。带 `?theme=sepia` 的链接可以直接分享某个主题。

### 字体：自托管 + 按需子集化

不请求任何 CDN，也不用 Google Fonts 的按 unicode-range 分片方案（357 个分片、约 6.3 MB）。做法是**下载完整可变字体 → 本地一次性子集化**：

```bash
python scripts/fetch-fonts.py             # 抓源字体 + 子集化 + 重新生成 CSS
python scripts/fetch-fonts.py --css-only  # 只重生成 @font-face
```

脚本会扫描 `content/ layouts/ i18n/ assets/ static/` 里**真正出现过**的字符：中文按实际用字生成 Noto Serif SC 子集（约 1761 字），拉丁字符按 Unicode 区段生成。产出 5 个 woff2，共约 1.3 MB：

| 文件 | 用途 | 体积 |
| --- | --- | --- |
| `noto-serif-sc-var.woff2` | 中文衬线标题 | ~603 KB |
| `newsreader-italic-var.woff2` | 拉丁衬线斜体 | ~212 KB |
| `inter-var.woff2` | 正文无衬线 | ~198 KB |
| `newsreader-var.woff2` | 拉丁衬线标题 | ~190 KB |
| `jetbrains-mono-var.woff2` | 等宽元信息 | ~55 KB |

`@font-face` 由脚本写到 `assets/css/extended/00-fonts.css`，用 `font-weight: 100 900` 一行覆盖全部字重。

> 路径细节：`assets/css/extended/*.css` 会被主题拼进主样式表，运行时位于 `/blog/assets/css/` 下，所以字体地址必须写成 `url('../../fonts/xxx.woff2')`（回退两级到站点根），写成 `url('fonts/...')` 会 404。

### 想改什么，改哪里

| 想改什么 | 改哪里 |
| --- | --- |
| 三态底色 / 文字色 / 边框 | `custom.css` 第 0 节「设计令牌」的 `--mz-*` |
| 品牌方块字与副行 | `hugo.yaml` 的 `params.brand` |
| 首页状态胶囊 / 大标题 / 金句 | `hugo.yaml` 的 `params.hero` |
| 主题按钮的三态图标 | `custom.css` 里 `.mz-theme-btn [data-icon=...]` 那几条 |
| 首页实时时钟 | `assets/js/custom.js` 第 5 模块 `initClock()` |
| 书签存储键 / 触感音效 | `assets/js/custom.js` 第 7 / 8 模块 |
| SVG 图库样式（描边、动画节奏） | `custom.css` 第 13 / 14 节 |
| 图库内容本身 | `assets/svg/*.svg`（由 `scripts/make-svgs.py` 生成） |
| 每页显示几条 | `hugo.yaml` 的 `pagination.pagerSize`（当前 10） |
| 分页页码外观 | `custom.css` 第 9 节「分页页码导航」 |
| 分页文案（首页/末页/第 N 页） | `i18n/zh-cn.yaml` 的 `first_page` / `last_page` / `page_counter` |

### 已实现的交互

- 顶部滚动进度条；吸顶导航栏滚动后压深分割线
- **三态主题循环切换**（导航栏 / 底部标签栏两处入口），选择记在 `localStorage`，未手动选过时跟随系统偏好实时变化
- Hero 区：呼吸状态点、**实时时钟**、可点击换一句的金句卡、真实统计（文章数 / 项目数 / 总字数 / 最近更新）
- 文章卡片：置顶优先排序、元信息行（日期 / 阅读时长 / 分类）、衬线标题 + hover 露出箭头、两行摘要、标签与字数
- **书签收藏**：卡片右上角一键收藏，存 `localStorage`，导航栏角标显示数量
- **触感音效**：切换主题 / 收藏 / 复制代码时用 Web Audio 合成一声轻响，可一键静音
- 文章页：目录卡片 + scrollspy 当前位置高亮、代码块一键复制
- 移动端底部标签栏（文章 / 项目 / 搜索 / 归档 / 主题）+ 抽屉式导航
- 部署指南弹窗、下载源码提示、⌘K / Ctrl+K / `/` 唤起搜索

> 所有动效都遵循 `prefers-reduced-motion`：系统里关闭动画后会自动降级为静态显示。
> 全部动效只用 CSS 与原生 JS 实现，整站**不请求任何第三方 CDN 或字体**。

## 分页导航：可以直接点页码跳转

列表页（首页 / 文章列表 / 标签页）底部的分页换成了带页码的版本，不必再一页页点「下一页」：

```text
««   « 上一页   [1] [2] [3] [4] [5]   下一页 »   »»
第 3 / 5 页
```

- 当前页用品牌渐变常亮；「首页 / 末页」是双箭头，方便来回跳。
- 首尾页会自动把对应的按钮**置灰**（`is-disabled`），而不是藏起来，避免按钮位置跳动。
- 页数多时自动折叠：只显示第 1 页、最后一页和当前页前后各 2 页，中间用 `…` 占位；**总页数 ≤ 7 时全部列出**。
- 窄屏（≤ 560px）隐藏两个双箭头按钮，只留「上一页 + 页码 + 下一页」。

### 它是怎么实现的

PaperMod 把分页内联写死在 `themes/PaperMod/layouts/list.html` 里（不是独立 partial），所以这里用**项目级模板覆盖**：`layouts/list.html` 是主题该文件的副本，只改了末尾的 `<footer class="page-footer">` 那段。Hugo 的查找顺序里项目 `layouts/` 优先于主题，所以覆盖生效，**完全没碰主题源码**。

> 升级主题时，记得比对主题新版 `list.html` 除分页外是否还有其它改动，再同步到本项目这份副本里。

样式在 `custom.css` 第 9 节。有个细节值得记：主题 `main.css` 里有一条 `.pagination a { background: var(--primary) }`，会把所有分页链接涂成实心胶囊；它的选择器权重是 `(0,1,1)`，比单个类名 `.page-num` 的 `(0,1,0)` 高，所以自定义样式统一写成 `.pagination .page-num`（`(0,2,0)`）才压得住。

## 动态内容：三种形态

除了普通图文，文章里还能放三种动态元素，完整示例见 `content/posts/spring-boot-2-vs-3-three-formats.md`。

### 1. 内联 SVG 示意图（主力形态）

24 张自绘图放在 `assets/svg/`，正文里一行短代码即可调用：

```markdown
{{< svg "cache-breakdown" >}}
{{< svg "cache-breakdown" "缓存击穿：热点 key 过期的瞬间" >}}
```

- 第一个参数是文件名（不带 `.svg`），第二个是可选的图注。
- **内联而非 `<img>`**：SVG 里的元素直接继承页面 CSS 变量，所以**一套图自动适配深浅色**，不用出两套。
- 元素默认可见，只有 JS 可用时才隐藏并等滚进视口再播放 —— **禁用 JS 也能完整阅读**。
- 找不到图时会渲染一个「缺图」占位块，并在构建日志里 `warnf` 报警，不会静默吞掉。

生成方式：`python scripts/make-svgs.py`（内部用 `scripts/svgkit.py` 提供的 `box/line/text/ring/curve` 等 DSL）。改文案只改 `make-svgs.py`。

### 2. 演示视频

`static/videos/` 存放 mp4 + 封面图，文章里用原生 `<video>` 标签引用：

```html
<video controls preload="metadata" poster="/blog/videos/xxx-poster.jpg">
  <source src="/blog/videos/xxx.mp4" type="video/mp4">
</video>
```

生成脚本 `scripts/make-demo-video.py`：Pillow 逐帧渲染 PNG → ffmpeg 编码。编码参数 `-crf 23 -preset slow -pix_fmt yuv420p -movflags +faststart`，17 秒 720p 成品只有 **0.28 MB**。

### 3. HTML 幻灯片

`static/slides/` 下是**零依赖手写**的 HTML 幻灯片（约 8 KB，不引任何框架）。支持键盘方向键 / 空格 / 触摸滑动 / 滚轮翻页、`F` 全屏、URL hash 定位。文章里用 iframe 嵌入：

```html
<iframe src="/blog/slides/xxx.html" style="width:100%;aspect-ratio:16/9;border:0;border-radius:14px" allowfullscreen loading="lazy"></iframe>
```

> 这三种形态都要求 `hugo.yaml` 里开启 `markup.goldmark.renderer.unsafe: true`，否则正文里的 HTML/SVG 会被转义成纯文本。

## 几个容易踩的坑

**1. `baseURL` 必须带子路径。**
本项目是 GitHub Pages 的**项目站点**，地址是 `https://elthereal-star.github.io/blog/`，所以配置里必须写成：

```yaml
baseURL: "https://elthereal-star.github.io/blog/"
```

漏掉 `/blog/` 会导致页面能打开但 CSS、图片全部 404。
（CI 里会用 `configure-pages` 输出的地址覆盖它，所以换仓库名或绑自定义域名时不用改配置。）

**2. 仓库设置里要选一次构建来源。**
`Settings → Pages → Build and deployment → Source` 必须选 **GitHub Actions**，而不是 "Deploy from a branch"。这是仓库级设置，改 YAML 不会生效。

**3. 主题是内置的，不是 submodule。**
`themes/PaperMod/` 直接提交进了仓库，好处是 clone 下来即可构建，不需要 `--recursive`。
升级主题时重新下载覆盖即可：

```bash
curl -L https://github.com/adityatelange/hugo-PaperMod/archive/refs/heads/master.tar.gz | tar xz
rm -rf themes/PaperMod && mv hugo-PaperMod-master themes/PaperMod && rm -rf themes/PaperMod/.git themes/PaperMod/images
```

**4. 中文字体与语言包。**
语言代码是 `zh-cn`，所以项目自己的 `i18n/zh-cn.yaml` 必须存在（内容来自主题的 `zh.yaml`）。
缺了它，页面上的「上一页 / 目录 / 复制」会显示成英文 key 名。

**5. 别用带引号的模式去 grep 构建产物。**
`hugo --minify` 会**去掉 HTML 属性的引号**，产物里是 `class=sb-compare` 而不是 `class="sb-compare"`。
用带引号的模式去 `grep` 会误判成「shortcode 没渲染」，实际上渲染得好好的。验证时改成 `grep -o 'class=[a-z-]*'`。

**6. 无头 Chrome 不能用来判断移动端是否溢出。**
无头 Chrome 的窗口有**最小宽度**，`--window-size=390` 截出来的图是被裁切过的，看起来「溢出」其实是假象。
要测窄屏布局，得在同源页面里放个 iframe 探针量 `scrollWidth`。

**7. 别复用 `data-theme` 这个属性名。**
PaperMod 自己也用 `<html data-theme="auto|light|dark">`，而且是在 `:root[data-theme="dark"]` 里整块重定义 `--theme` / `--entry` / `--code-bg` 等变量。
本项目一开始把三态也挂在 `data-theme` 上，结果撞了两个坑：`auto` 这个初值在两边的取值集合里含义不同；服务端渲染出 `auto` 时，主题的 `prefers-color-scheme` 规则会先把 `body` 刷成深色，而页头还是浅色，出现半截错色。
现在的做法是：**三态色板挂独立属性 `data-mz-theme`**，`data-theme` 只由脚本同步成 `light` / `dark`（羊皮纸算浅色系）给主题组件用，并且把选择器的值写回主题认的 `pref-theme` 键，两边始终一致。

**8. 自定义变量映射要压住主题的权重。**
主题的暗色变量是写在 `:root[data-theme="dark"]`（权重 `0,2,0`）里的，如果映射只写 `:root`（`0,1,0`），自定义值会被静默盖掉。
现象很隐蔽：`body` 和 `.main` 之间出现一条对不上的色缝（`#1d1e20` vs `#111113`）。
所以映射块写成 `html:root, html:root[data-mz-theme]`（`0,2,1`），确保任何一态下都赢。

## 从旧 Markdown 素材迁移文章

早期素材（无 front matter 的纯 Markdown + 图床图片）可以用脚本批量转成 Hugo 文章：

```bash
python scripts/migrate-posts.py --dry-run   # 先看报告，不写文件
python scripts/migrate-posts.py             # 正式迁移
```

脚本做四件事：

1. 从 H1 提取标题，按文件时间生成 `date`，补上 `categories` / `tags` / `summary`；
2. 把「占位符图片引用」替换成对应的 `{{< svg >}}` 短代码；
3. 把图床真图下载到 `static/images/<slug>/` 并改成本地路径（摆脱外链）；
4. 把指向同目录其它 `.md` 的相对链接改成 Hugo 文章地址。

> 脚本会跟踪 Markdown **代码围栏**状态：代码块里出现的 `<img>` 是示例代码，**不会被改写**。

## 主题与主题修改

- 主题：PaperMod (MIT) —— https://github.com/adityatelange/hugo-PaperMod
- 自定义样式放在 `assets/css/extended/`，PaperMod 会自动合并该目录下所有 CSS，**不需要修改主题文件**。
- 站点配置全部集中在 `hugo.yaml`，改标题、菜单、社交链接看这一个文件就够。

## License

博客内容（`content/`）版权归作者所有；站点配置与构建脚本可自由参考。
主题 PaperMod 遵循其自身的 MIT 协议。
