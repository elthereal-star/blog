---
title: "Health AI Assistant 健康管理平台"
date: 2026-07-13
description: "AI 增强的个人健康管理平台，模块化单体架构：用文字记录饮食和运动，生成可持续的健康分析与个性化建议。"
summary: "一个模块化单体应用：用户用自然语言记录饮食和运动，系统产出健康分析与个性化建议。核心理念是「AI 是分析师，不是计算器」。"
tags: ["Java", "Spring Boot", "Vue", "AI", "全栈"]
ShowToc: false
---

## 它是什么

AI 增强的个人健康管理平台。用户通过文字记录饮食和运动，系统生成可持续的健康数据分析和个性化建议。

- **源码**：https://github.com/elthereal-star/health-ai-assistant
- **状态**：可用，文档齐全

**核心理念：AI 是分析师，不是计算器。**

## 架构

一个模块化单体（modular monolith）：

```text
表现层      Vue 3 + TypeScript
    ↓
应用层      REST API
    ↓
业务能力层  Identity / Nutrition / Exercise / Analytics
    ↓
支撑服务层  AI / OCR / Notification
    ↓
基础设施层  MySQL / Redis / MinIO
```

刻意不拆微服务：这个体量下，拆开带来的分布式事务、链路追踪、部署复杂度远大于收益。**先把模块边界划清楚，等真的需要再拆。**

## 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 · TypeScript · Element Plus · Vite |
| 后端 | Spring Boot 3 · Java 21 · Maven |
| 数据库 | MySQL 8 · Redis 7 |
| ORM | MyBatis-Plus |
| 对象存储 | MinIO |
| AI | DeepSeek（OpenAI 兼容）+ 本地 Mock 降级 |
| 部署 | Docker Compose |

## 最有意思的设计：AI 降级策略

系统默认跑 `MockAIService`——**不需要任何 API Key**，用内置的中英文食物/运动词典做识别，给出基于规则的建议。整套链路（记录 → 计算 → 统计 → 展示）完全离线可用。

设置 `AI_API_KEY` 之后自动切换到 `DeepSeekAIService`。

这样做的好处：

1. **新人 clone 下来就能跑完整功能**，不用先申请 API Key。
2. **AI 挂了或者欠费，产品不会挂**，只是建议质量下降。
3. **强制架构分层正确**——如果核心链路依赖了模型，Mock 模式根本跑不起来，这会立刻暴露设计问题。

同时，AI **不碰数据库、不算热量、不改业务规则**。它的输出必须结构化成 JSON，由业务层完成所有计算。这样同一份数据算两次的结果永远一致，也能回答用户「这个数字怎么来的」。

## 快速开始

零依赖方式（H2 内存库，不需要 Docker / MySQL / Redis）：

```bash
cd backend && mvn clean package -DskipTests
java -jar target/health-ai-assistant-0.0.1-SNAPSHOT.jar --spring.profiles.active=local,h2

cd frontend && npm install && npm run dev
```

打开 `http://localhost:3000`，注册账号后即可记录饮食、运动并查看看板。

一键起全套环境（MySQL + Redis + MinIO + 前后端）：

```bash
docker compose up --build -d
```

## 文档

仓库 `docs/` 目录下有完整的工程设计文档：

- 工程规范（Engineering Rules）
- 项目愿景（Project Vision）
- 系统规格说明（System Specification）
- 数据库设计（Database Design）
- 接口规范（API Specification）
- AI 规范（AI Specification）
- 前端规范（Frontend Specification）
- 部署说明（Deployment）

## 相关文章

[AI 不负责计算：一次关于「谁该干什么」的架构取舍](/blog/posts/ai-analyst-not-calculator/)
