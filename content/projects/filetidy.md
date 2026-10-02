---
title: "filetidy 文件整理 CLI"
date: 2026-09-15
weight: 20
description: "一条命令把下载文件夹收拾整齐：按 YAML 规则自动归类，支持 --dry-run 预览、--watch 监听、undo 一键撤销。"
summary: "一个 jar 包 + 一份 YAML，把整理规则固化下来，并且永远可撤销。"
tags: ["Java", "CLI", "picocli", "工具"]
ShowToc: false
---

## 它是什么

一条命令把乱七八糟的下载文件夹收拾整齐：按可配置的 YAML 规则把文件自动归类到子文件夹，支持预览、持续监听和一键撤销。

- **源码**：https://github.com/elthereal-star/filetidy
- **状态**：可用

## 为什么写这个

下载文件夹是大多数人电脑里最乱的角落。同类工具要么闭源要么过重，而且**大多不可撤销**——批量移动文件是破坏性操作，出错只能手动翻回来。

这个项目的目标是：

> 一个 jar 包 + 一份 YAML，就能把整理规则固化下来，并且永远可撤销。

## 核心设计：撤销是地基，不是附加功能

每次移动都往 `.filetidy-history.jsonl` **追加**一行，带上批次 ID：

```json
{"batchId":"20260915-143022-7f3a","from":"Downloads/a.pdf","to":"Downloads/02-文档/a.pdf","ts":"2026-09-15T14:30:22+08:00"}
```

三个刻意的选择：

- **JSONL 而不是 JSON 数组**——追加写不需要读全文，中途崩溃最多丢最后一行，不会把整个历史写坏。
- **带 `batchId`**——`undo` 按批次整体回滚，符合「把刚才那次整理撤掉」的心智模型。
- **记录 `to` 而不是重新推算**——文件可能已经被改过名，重新跑规则推算必然出错。直接记录事实。

因为记录了事实，「可撤销」才有了真正的语义边界，而不是只能做「撤销最近一步」。

## 其他关键决定

**永不覆盖。** 目标位置有同名文件时自动追加 ` (1)`、` (2)`，不覆盖也不报错。整理文件应该是无损操作。

**只扫描目录第一层。** 子目录被声明为「已归档区」，天然幂等，避免第二次运行时把归好类的文件再挪一遍、产生 `01-图片/01-图片/` 套娃。

**watch 模式用全量重扫而非事件增量。** 浏览器下载会先创建 `.crdownload` 临时文件、分块写入触发多次事件，按事件处理就会撞上「文件没写完就被移走」。全量重扫只多花毫秒级，却天然规避重复事件和半截文件。

## 用法

```bash
# 预览整理计划（不移动任何文件）
java -jar target/filetidy.jar organize ~/Downloads --dry-run

# 实际整理
java -jar target/filetidy.jar organize ~/Downloads

# 自定义规则
java -jar target/filetidy.jar organize ~/Downloads -c my-rules.yml

# 监听模式
java -jar target/filetidy.jar organize ~/Downloads --watch

# 撤销上一次整理
java -jar target/filetidy.jar undo ~/Downloads
```

规则配置：

```yaml
rules:
  - name: images
    target: 01-图片
    extensions: [jpg, jpeg, png, gif, webp]
  - name: documents
    target: 02-文档
    extensions: [pdf, doc, docx, xls, xlsx, md]
fallback: 99-其他
skipHidden: true
```

## 相关文章

[filetidy：用 Java 21 + picocli 写一个「永远可撤销」的文件整理 CLI](/blog/posts/filetidy-reversible-cli-design/)
