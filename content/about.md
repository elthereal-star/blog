---
title: "关于我"
layout: "about"
date: 2026-09-01
hidemeta: true
ShowToc: false
ShowBreadCrumbs: false
comments: false
---

## 你好 👋

我是 **elthereal-star**，一名正在往 Java 后端方向努力的学习者。

平时的主线是写业务代码和折腾工程化那套东西：把一个小项目从「能跑」推到「有测试、有 CI、有 Docker 镜像、有可撤销的数据操作」，这个过程比写 CRUD 有意思得多。

## 我在用什么

| 方向 | 技术栈 |
| --- | --- |
| 语言与框架 | Java 21 / Spring Boot 3 / MyBatis-Plus |
| 数据层 | MySQL 8 / H2 / Redis / Flyway 版本化迁移 |
| 前端 | Vue 3 / TypeScript / Element Plus / Vite |
| 工程化 | Maven / Docker 多阶段构建 / GitHub Actions |
| 测试 | JUnit 5 / Testcontainers / Playwright |
| 文档 | springdoc-openapi（Swagger UI） |

## 我关心的事

- **边界要清楚。** 谁负责计算、谁负责理解、谁负责持久化，想明白了再写代码。这套原则在后面几篇文章里反复出现。
- **操作要可回滚。** 批量移动文件也好、改数据库也好，先想清楚「搞砸了怎么退回去」。
- **交付要一条命令。** `mvn package` 能出完整产物、`docker compose up` 能起全套环境，这种确定性很值钱。
- **测试要能跑在 CI 里。** 只在我电脑上通过的测试，等于没有测试。

## 这个博客

用 [Hugo](https://gohugo.io/) + [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 搭建，托管在 GitHub Pages 上。写作流程就是往 `content/posts/` 里扔一个 Markdown 文件，push 上去，GitHub Actions 自动构建部署。

想了解具体怎么搭的，可以看这篇：[用 Hugo + PaperMod 搭一个「推 Markdown 就自动上线」的博客](/blog/posts/build-blog-with-hugo-papermod/)。

## 联系我

- GitHub：[@elthereal-star](https://github.com/elthereal-star)
- 邮箱：2838984524@qq.com

欢迎交流，尤其是 Spring Boot 工程化和测试相关的话题。
