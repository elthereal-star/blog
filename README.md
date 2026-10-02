# Star-Bai 的技术笔记

个人技术博客的源码，基于 **Hugo + PaperMod**，通过 **GitHub Actions** 自动构建并部署到 **GitHub Pages**。

- 线上地址：https://elthereal-star.github.io/blog/
- 文章目录：`content/posts/`
- 项目介绍：`content/projects/`

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
├── assets/css/extended/custom.css# 自定义样式（不改主题源码）
├── i18n/zh-cn.yaml               # 中文界面文案
├── content/
│   ├── about.md                  # 关于我
│   ├── search.md                 # 搜索页
│   ├── archives.md               # 归档页
│   ├── posts/                    # 文章
│   └── projects/                 # 项目介绍
├── static/                       # favicon 等静态文件
└── themes/PaperMod/              # 主题（已内置进仓库）
```

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

## 主题与主题修改

- 主题：PaperMod (MIT) —— https://github.com/adityatelange/hugo-PaperMod
- 自定义样式放在 `assets/css/extended/`，PaperMod 会自动合并该目录下所有 CSS，**不需要修改主题文件**。
- 站点配置全部集中在 `hugo.yaml`，改标题、菜单、社交链接看这一个文件就够。

## License

博客内容（`content/`）版权归作者所有；站点配置与构建脚本可自由参考。
主题 PaperMod 遵循其自身的 MIT 协议。
