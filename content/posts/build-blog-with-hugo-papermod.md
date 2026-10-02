---
title: "用 Hugo + PaperMod 搭一个「推 Markdown 就自动上线」的博客"
date: 2026-10-01
draft: false
description: "从零把 Hugo 博客部署到 GitHub Pages，包含项目站点与用户站点的区别、Actions 工作流逐行解释，以及我踩到的坑。"
summary: "整条链路只有一件事：往 content/posts/ 里扔一个 Markdown，push 上去，剩下的交给 GitHub Actions。这篇记录完整的搭建过程和我踩过的坑。"
tags: ["Hugo", "GitHub Pages", "CI/CD", "建站"]
categories: ["工程化"]
ShowToc: true
---

## 我想要的效果

先说清楚目标，不然后面选型会飘：

1. 写文章 = 新建一个 Markdown 文件，不需要动任何 HTML/CSS。
2. `git push` 之后自动上线，不用手动构建、不用手动上传。
3. 网址要能直接丢给别人打开，不依赖我的电脑开机。
4. 国内访问要正常，不能一打开就卡在某个境外 CDN 上。

## 选型：为什么是 Hugo + PaperMod + GitHub Pages

| 方案 | 判断 |
| --- | --- |
| Jekyll | GitHub Pages 原生支持，但构建慢、Ruby 环境在 Windows 上很折腾 |
| Hexo | 生态好，但主题与插件质量参差，Node 依赖树也重 |
| 现成平台（掘金/博客园等） | 省事，但域名不是自己的，样式不能改 |
| **Hugo + PaperMod** | 单个二进制、毫秒级构建、主题零外部依赖，产物是纯静态文件 |

最后一行 @ 是决定性因素：Hugo 是**一个可执行文件**，不需要运行时；PaperMod 把搜索用的 Fuse.js 直接打包进了主题，**整站不请求任何第三方 CDN**。

## 一个必须先搞清楚的坑：两种站点地址

GitHub Pages 有两套地址，很多人第一步就选错：

| 类型 | 仓库名必须是 | 网址 |
| --- | --- | --- |
| **用户站点** | `<用户名>.github.io` | `https://<用户名>.github.io/` |
| **项目站点** | 任意名字，例如 `blog` | `https://<用户名>.github.io/blog/` |

我选的是**项目站点**，仓库叫 `blog`，所以：

```text
https://elthereal-star.github.io/blog/
```

项目站点的关键点是 **`baseURL` 必须带上子路径**，这一步写错，上线后页面能打开但 CSS、图片全部 404：

```yaml
# hugo.yaml
baseURL: "https://elthereal-star.github.io/blog/"
```

## 目录结构

内置主题（而不是用 submodule）是我的刻意选择，理由在下一节。

```text
blog/
├── .github/workflows/hugo.yml   # 自动部署流水线
├── hugo.yaml                    # 站点主配置
├── archetypes/default.md        # 新建文章的模板
├── assets/css/extended/         # 追加自定义样式，不会动主题源码
│   └── custom.css
├── content/
│   ├── about.md                 # 关于我
│   ├── search.md                # 搜索页
│   ├── archives.md              # 归档页
│   ├── posts/                   # 文章
│   └── projects/                # 项目介绍
└── themes/PaperMod/             # 主题（已内置进仓库）
```

## 踩坑记录

### 1. 主题用 submodule 还是直接内置

PaperMod 官方文档推荐 `git submodule add`。我改用**直接把主题文件拷进 `themes/PaperMod/`**，原因：

- submodule 要求 CI 里 checkout 时必须带 `submodules: recursive`，少写一行就构建出一个没有样式的裸 HTML。
- 别人 clone 仓库时忘了 `--recursive`，同样得到裸 HTML，然后怀疑人生。
- 内置进去之后整个仓库是**自包含**的，任何环境 clone 下来直接能构建。

代价是主题更新要手动覆盖，考虑到博客主题基本不需要频繁升级，这笔交易很划算。主题总共只有 538 KB，其中 `images/` 目录（主题 README 的截图）可以直接删掉。

### 2. `min_version` 问题

PaperMod 的 `theme.toml` 里写着：

```toml
min_version = "0.146.0"
```

因为 Hugo 0.146 重构了模板查找规则（`layouts/_default/` 那一套变成了 `layouts/` 平铺 + `_partials/`）。所以**别用老版本 Hugo**，直接上最新的 extended 版：

```bash
hugo version   # 需要 >= 0.146.0
```

### 3. 中文语言包

主题自带 `i18n/zh.yaml`，但我配置里的语言代码是 `zh-cn`，Hugo 会去找 `i18n/zh-cn.yaml`。找不到的话，页面上「上一页」「目录」「复制」这些会变成英文 key 名。解决办法是把这个文件复制一份改名放到项目自己的 `i18n/` 目录：

```bash
cp themes/PaperMod/i18n/zh.yaml i18n/zh-cn.yaml
```

### 4. favicon 的五个默认路径

PaperMod 的 `head.html` 无条件输出五个 favicon 标签，即使你没有图片文件也会输出：

```html
<link rel="icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="mask-icon" href="/safari-pinned-tab.svg">
```

不提供文件的话，控制台就是五个 404。所以老老实实生成五个文件放进 `static/` 里。

## 自动部署流水线

整个部署由 `.github/workflows/hugo.yml` 完成，核心是官方那套 Pages Actions：

```yaml
name: 构建并部署博客到 GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:        # 也允许在网页上手动点一下触发

permissions:
  contents: read
  pages: write              # 允许部署到 Pages
  id-token: write           # deploy-pages 需要 OIDC 令牌

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.167.0
    steps:
      - name: 安装 Hugo
        run: |
          wget -O hugo.deb \
            https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb
          sudo dpkg -i hugo.deb

      - name: 检出仓库
        uses: actions/checkout@v5
        with:
          fetch-depth: 0     # 让 Hugo 能拿到完整的 Git 历史（用于 lastmod）

      - name: 配置 Pages
        id: pages
        uses: actions/configure-pages@v5

      - name: 构建站点
        env:
          HUGO_ENVIRONMENT: production
          TZ: Asia/Shanghai
        run: hugo --minify --gc --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: 上传产物
        uses: actions/upload-pages-artifact@v4
        with:
          path: ./public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: 部署
        id: deployment
        uses: actions/deploy-pages@v4
```

几个值得说的细节：

- `configure-pages` 会输出 `base_url`，构建时用它覆盖 `baseURL`，这样以后就算改仓库名或者换自定义域名，配置文件一个字都不用动。
- `fetch-depth: 0` 是为了让 Hugo 能读取 Git 提交历史，配合 `.GitInfo` 显示「最后更新时间」。
- `permissions` 里 `pages: write` 和 `id-token: write` 是 `deploy-pages` 的硬性要求，少一个就报权限错误。

还有一个**必须手动点一次**的地方：仓库 `Settings → Pages → Build and deployment → Source` 要选 **GitHub Actions**（而不是 "Deploy from a branch"）。这是仓库级设置，YAML 改不了它。

## 本地预览

Cloud Build 一次要等一两分钟，改样式时太慢，所以本地也装一份 Hugo：

```bash
winget install --id Hugo.Hugo.Extended -e
```

然后在站点目录下：

```bash
hugo server -D
```

打开 `http://localhost:1313/blog/`，改文件会实时刷新。

## 发一篇新文章

```bash
hugo new content posts/my-new-post.md
```

生成的文件头部已经带好模板：

```yaml
---
title: "My New Post"
date: 2026-10-01
draft: false
tags: []
categories: []
---

正文写这里。
```

写完三件事：

```bash
git add .
git commit -m "post: 新增文章 xxx"
git push
```

剩下的交给 Actions。去仓库的 **Actions** 标签页能看到构建日志。

## 小结

这套方案最舒服的地方是**写作和发布彻底解耦**：我只需要关心 Markdown 的内容，构建、部署、CDN、HTTPS 全是别人的事。整站是纯静态文件，打开速度也快。

如果你也想搭一个，按这篇的顺序走一遍大概半小时能跑通。有卡住的地方欢迎来 [GitHub](https://github.com/elthereal-star) 找我。
