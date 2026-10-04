# elthereal-star 的技术笔记

个人技术博客的源码，基于 **Hugo + PaperMod**，通过 **GitHub Actions** 自动构建并部署到 **GitHub Pages**。

- 线上地址：https://elthereal-star.github.io/blog/
- 文章目录：`content/posts/`（37 篇，其中 22 篇带内联 SVG 示意图）
- 项目介绍：`content/projects/`
- 图库：`assets/svg/`（24 张自绘 SVG，主题自适配深浅色）

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
├── hugo.yaml                     # 站点主配置（菜单、参数、搜索等）
├── archetypes/default.md         # 新建文章模板
├── assets/
│   ├── css/extended/custom.css   # 自定义样式（不改主题源码）
│   ├── js/custom.js              # 自定义交互脚本
│   └── svg/                      # SVG 示意图图库（shortcode 内联使用）
├── layouts/
│   ├── _partials/
│   │   ├── home_info.html        # 首页 Hero 区块
│   │   ├── extend_head.html      # <head> 注入点
│   │   └── extend_footer.html    # </body> 前注入点（进度条 + 脚本）
│   └── shortcodes/
│       ├── svg.html              # 通用 SVG 图库：{{< svg "名字" >}}
│       └── sb-compare.html       # Spring Boot 2 vs 3 对比动画
├── i18n/zh-cn.yaml               # 中文界面文案
├── content/
│   ├── about.md                  # 关于我
│   ├── search.md                 # 搜索页
│   ├── archives.md               # 归档页
│   ├── posts/                    # 文章
│   └── projects/                 # 项目介绍
├── scripts/                      # 内容生成脚本（Python，非构建依赖）
│   ├── svgkit.py                 # SVG 生成 DSL 工具包
│   ├── make-svgs.py              # 批量生成 assets/svg/*.svg
│   ├── migrate-posts.py          # 把 Markdown 素材迁移成 Hugo 文章
│   └── make-demo-video.py        # Pillow 逐帧渲染 + ffmpeg 编码演示视频
├── static/
│   ├── favicon*.png / .ico       # 站点图标
│   ├── images/<slug>/            # 文章配图（本地化，不再依赖图床）
│   ├── videos/                   # 演示视频（mp4 + poster）
│   └── slides/                   # 零依赖 HTML 幻灯片
└── themes/PaperMod/              # 主题（已内置进仓库）
```

> `scripts/` 只在**内容制作时**手动跑，CI 构建不需要 Python —— 生成的成品（SVG / 图片 / 视频 / 幻灯片）都已提交进仓库。

## 视觉与交互定制

站点的「豪华感」来自这几处，都集中在上面标出的文件里，改起来互不干扰：

| 想改什么 | 改哪里 |
| --- | --- |
| 品牌主色 / 渐变色 | `custom.css` 顶部的 `--brand-1/2/3` |
| 深浅色主题的底色、文字色 | `custom.css` 里的 `:root` 与 `:root[data-theme="dark"]` |
| 极光背景的浓度 | `custom.css` 里 `body::before` 的 `rgba(...)` 透明度 |
| 首页徽章 / 打字机文案 / 技能标签 | `hugo.yaml` 的 `params.hero` |
| 首页问候语和简介正文 | `hugo.yaml` 的 `params.homeInfoParams` |
| 动效速度、开关 | `assets/js/custom.js` 顶部的 `TYPE_SPEED` / `HOLD_TIME` / `MAX_TILT` |
| SVG 图库样式（描边、动画节奏） | `custom.css` 第 13 节「通用 SVG 示意图图库」 |
| 图库内容本身 | `assets/svg/*.svg`（由 `scripts/make-svgs.py` 生成） |

已经实现的动效清单：

- 缓慢漂浮的极光渐变背景（纯 CSS，无 canvas、无第三方库）
- 顶部滚动进度条
- 吸顶毛玻璃导航栏（滚动后出现分割线与投影）
- 导航项 hover 渐变下划线、logo 渐变流光、主题按钮旋转
- 首页 Hero：旋转光环的星形徽标、渐变动画大标题、挥手 emoji、打字机副标题、可悬停的技能标签、圆形社交图标
- 列表卡片：滚动进场错峰淡入、hover 上浮 + 渐变描边 + 高光扫过 + 鼠标跟随的 3D 倾斜
- 文章页：二级标题渐变竖条、目录卡片与 scrollspy 当前位置高亮、代码块 hover 上浮、表格渐变表头

> 所有动效都遵循 `prefers-reduced-motion`：系统里关闭动画后会自动降级为静态显示。
> 全部动效只用 CSS 与少量原生 JS 实现，整站**不请求任何第三方 CDN 或字体**。

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
