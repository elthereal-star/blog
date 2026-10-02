---
title: "Offer Tracker 投递进度追踪器"
date: 2026-09-08
weight: 10
description: "管理校招和实习投递全流程的单体应用：公司库、投递看板、可自由调整的状态、面试轮次与数据统计。"
summary: "一个管理求职投递全流程的单体应用，一条 mvn package 出完整可运行 JAR，并提供免安装的 Windows 便携版。"
tags: ["Java", "Spring Boot", "Vue", "全栈"]
ShowToc: false
---

## 它是什么

管理校招和实习投递全流程的单体应用：公司库、投递看板、状态自由调整、面试轮次记录和数据统计。

解决的实际问题是——投递信息散落在 Excel、记事本和聊天记录里，状态更新不及时，进展全靠回忆。

- **源码**：https://github.com/elthereal-star/offer-tracker
- **状态**：可用，持续迭代中

## 技术栈

| 层 | 选型 |
| --- | --- |
| 语言与框架 | Java 21 · Spring Boot 3 · MyBatis-Plus |
| 数据库 | H2（默认）· MySQL 8（`mysql` profile） |
| 数据库迁移 | Flyway |
| 接口文档 | springdoc-openapi（Swagger UI） |
| 前端 | Vue 3 · TypeScript · Element Plus · Vite |
| 测试 | JUnit 5 · Testcontainers · Playwright |
| 构建部署 | Maven · GitHub Actions · Docker |

## 最有意思的三个设计

**1. 一条命令交付。**

`mvn package` 会自动下载项目专用的 Node.js、装前端依赖、跑测试、构建前端、把静态资源打进 JAR。产物是单个可执行文件：

```bash
java -jar target/offer-tracker-0.1.0.jar
```

**2. 状态可以自由流转。**

状态不是严格单向的状态机，而是**用户对现实的标注**。收藏着的公司可以直接进面试中，笔试挂了半年后复捞也不用改数据——系统不该比用户更懂发生了什么。

```text
SAVED / APPLIED / WRITTEN_TEST / INTERVIEWING / OFFER / REJECTED / WITHDRAWN
```

**3. 恢复备份前先预检。**

```text
POST /api/data/import/validate   → 检查引用完整性、重复轮次、主键冲突
POST /api/data/import            → 追加 或 清空后恢复
```

恢复备份是仅次于删除的危险操作，所以先让用户看清「会新增几条、覆盖几条、发现几处冲突」再动手。

## Windows 便携版

```powershell
.\packaging\package-windows.ps1
```

产物解压双击 `OfferTracker.exe` 即可运行，自带 Java 环境，目标机器**不需要装 JDK**。程序自动选择空闲端口、打开浏览器、通过系统托盘提供「打开 / 退出」，数据存在 `%LOCALAPPDATA%\OfferTracker\data`，不写安装目录。

## 快速开始

```bash
mvn package
java -jar target/offer-tracker-0.1.0.jar
```

打开 `http://localhost:8080`；接口文档在 `/swagger-ui.html`；H2 控制台在 `/h2-console`。

## 相关文章

[offer-tracker 复盘：把一个小系统从「能跑」推到「敢交付」](/blog/posts/offer-tracker-retrospective/)
