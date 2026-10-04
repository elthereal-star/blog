#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 D:\\AI\\博客\\markdown 下的文章迁移成 Hugo 文章

做四件事：
  1. 从 H1 提取标题，按文件时间生成 date，补上 categories / tags / summary
  2. 把「占位符图片引用」换成对应的内联 SVG 短代码（assets/svg/*.svg）
  3. 把 CSDN 图床的真图下载到 static/images/<slug>/，改成本地路径
  4. 把指向同目录其它 .md 的相对链接改成 Hugo 文章地址

用法：
    python scripts/migrate-posts.py            # 正式迁移
    python scripts/migrate-posts.py --dry-run  # 只看报告，不写文件
"""

import os
import re
import sys
import glob
import shutil
import subprocess
from datetime import datetime

DRY = "--dry-run" in sys.argv

SRC_DIR = r"D:\AI\博客\markdown"
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
IMG_DIR = os.path.join(ROOT, "static", "images")

# 跳过：这是同一篇文章的 CSDN 排版版（开头有大段发布说明注释、
# 正文里还有 CSDN 专有的 @[toc] 指令，且去掉了文内互链）
SKIP = {
    "不会聊天的AI火了？Jev：比ChatGPT快200倍、便宜400倍的'做选择'模型（Java实战）-CSDN版.md",
}

# ----------------------------------------------------------------------
# 文章清单：源文件 → slug / 分类 / 标签 / 必备示意图
# 必备示意图指「即使正文里没有对应占位符，也要放一张」的核心概念图
# ----------------------------------------------------------------------
ARTICLES = [
    ("HTTP和HTTPS到底有啥区别？给新手掰开揉碎讲明白.md", "http-vs-https-explained",
     "网络", ["HTTP", "HTTPS", "TLS", "网络安全"],
     ["http-vs-https", "tls-handshake", "key-exchange"]),

    ("HTTPClient的介绍以及应用场景.md", "http-client-guide",
     "网络", ["HTTP", "HTTPClient", "Java", "网络编程"], []),

    ("MapStruct-vs-BeanUtils.md", "mapstruct-vs-beanutils",
     "Java", ["MapStruct", "BeanUtils", "对象映射", "性能"],
     ["pojo-layers"]),

    ("MyBatisPlus介绍以及带来的简化开发效果.md", "mybatis-plus-simplify",
     "数据库", ["MyBatis-Plus", "ORM", "持久层", "Spring Boot"], []),

    ("O_o，PO , BO , DTO , DAO , POJO 到底什么O是什么什么O_o_O（Java中这些对象的设计思想）.md",
     "po-bo-dto-dao-pojo", "Java", ["POJO", "DTO", "VO", "分层设计"],
     ["pojo-layers"]),

    ("RAG核心工作流程，给大模型装上你的私房知识库.md", "rag-core-workflow",
     "AI", ["RAG", "向量数据库", "大模型", "检索增强"],
     ["rag-pipeline"]),

    ("Redis中fencing token设计的巧妙之处以及应用场景.md", "redis-fencing-token",
     "中间件", ["Redis", "分布式锁", "Fencing Token", "分布式一致性"],
     ["fencing-token", "lock-watchdog"]),

    ("Redis分布式锁-vs-Zookeeper分布式锁-vs-数据库乐观锁.md", "distributed-lock-comparison",
     "中间件", ["Redis", "Zookeeper", "分布式锁", "乐观锁"],
     ["distributed-lock"]),

    ("Redis分布式锁的各种实现方式以及原理.md", "redis-distributed-lock",
     "中间件", ["Redis", "分布式锁", "Redisson", "高并发"],
     ["distributed-lock", "lock-watchdog"]),

    ("Redis实现消息队列的方式以及场景.md", "redis-message-queue",
     "中间件", ["Redis", "消息队列", "Stream", "异步"],
     ["kafka-scenarios"]),

    ("SpringBoot整合JWT，登录认证原来这么简单？.md", "spring-boot-jwt",
     "Spring", ["Spring Boot", "JWT", "登录认证", "安全"],
     ["jwt-structure", "jwt-login-flow"]),

    ("SpringBoot的简化开发，爽到飞起.md", "spring-boot-simplify",
     "Spring", ["Spring Boot", "自动配置", "starter", "约定优于配置"], []),

    ("SpringTask的介绍以及应用场景.md", "spring-task",
     "Spring", ["Spring Task", "定时任务", "cron"], []),

    ("ThreadLocal的作用以及实际应用场景.md", "threadlocal",
     "Java", ["ThreadLocal", "并发", "线程隔离", "内存泄漏"],
     ["threadlocal"]),

    ("WebSocket对前后端建立的联系以及作用.md", "websocket-vs-polling",
     "网络", ["WebSocket", "长连接", "实时通信", "轮询"],
     ["websocket-vs-http"]),

    ("codex-free-quota-monthly-refresh.md", "codex-free-quota-monthly-refresh",
     "工具链", ["Codex", "AI 工具", "订阅", "随笔"], []),

    ("kafka-topic-partition-replica-broker.md", "kafka-topic-partition-replica",
     "中间件", ["Kafka", "Partition", "Replica", "消息队列"],
     ["kafka-roles"]),

    ("kafka_常见使用场景.md", "kafka-use-cases",
     "中间件", ["Kafka", "消息队列", "削峰填谷", "异步解耦"],
     ["kafka-scenarios"]),

    ("不会聊天的AI火了？Jev：比ChatGPT快200倍、便宜400倍的'做选择'模型（Java实战）.md",
     "jev-choice-model", "AI", ["Jev", "Spring AI", "大模型", "Java"], []),

    ("乐观锁与悲观锁的介绍以及在超卖等问题上的应用.md", "optimistic-vs-pessimistic-lock",
     "数据库", ["乐观锁", "悲观锁", "超卖", "并发控制"],
     ["optimistic-lock"]),

    ("内网穿透的意义以及实现方式.md", "nat-traversal",
     "工具链", ["内网穿透", "frp", "Cpolar", "部署"],
     ["nat-traversal"]),

    ("分布式SingleFlight设计的巧妙之处以及SingleFlight的讲解应用场景（Java实现）.md",
     "singleflight", "架构设计", ["SingleFlight", "缓存击穿", "并发合并"],
     ["singleflight"]),

    ("快慢指针的常见应用以及各类变形和通用思路.md", "fast-slow-pointer",
     "算法", ["算法", "链表", "双指针", "题解"],
     ["fast-slow-pointer"]),

    ("懒加载与渐进式披露的设计思想以及应用场景.md", "lazy-loading-progressive-disclosure",
     "架构设计", ["懒加载", "渐进式披露", "用户体验", "性能优化"],
     ["lazy-progressive"]),

    ("新手如何使用IDEA在github上面上传自己的项目.md", "idea-github-upload",
     "工具链", ["IDEA", "Git", "GitHub", "新手教程"],
     ["deploy-pipeline"]),

    ("新手要使用Redis不想折腾Docker,WSL，这里有办法.md", "redis-without-docker",
     "工具链", ["Redis", "Windows", "Memurai", "环境搭建"], []),

    ("缓存击穿问题的原因以及解决方案.md", "cache-breakdown",
     "中间件", ["缓存击穿", "Redis", "缓存", "高并发"],
     ["cache-breakdown", "cache-penetration", "cache-avalanche"]),

    ("老版JDK下载不了？让我们来邪修（bush）下载JDK11.md", "download-jdk11",
     "工具链", ["JDK", "OpenJDK", "环境搭建"], []),

    ("随机TTL防抖(Redis实现).md", "redis-random-ttl",
     "中间件", ["Redis", "TTL", "接口防抖", "缓存雪崩"],
     ["ttl-jitter", "cache-avalanche"]),

    ("项目的部署方式及流程，让别人也能访问到你的项目.md", "deploy-project",
     "工程化", ["部署", "Nginx", "云服务器", "上线"],
     ["deploy-pipeline", "nat-traversal"]),
]

# ----------------------------------------------------------------------
# 占位符图片 → SVG 示意图
# 左边是原文里的图片路径（或路径里的关键词），右边是 assets/svg 下的图名
# ----------------------------------------------------------------------
SVG_MAP = [
    # HTTP / HTTPS
    ("http-request-response", "http-vs-https"),
    ("http-plaintext", "http-vs-https"),
    ("http-three-problems", "http-vs-https"),
    ("https-tls-layer", "tls-handshake"),
    ("tls-handshake", "tls-handshake"),
    ("ssl-handshake-exception", "tls-handshake"),
    ("ca-certificate", "tls-handshake"),
    ("symmetric-encryption", "key-exchange"),
    ("asymmetric-encryption", "key-exchange"),
    # WebSocket
    ("websocket-vs-http", "websocket-vs-http"),
    ("websocket-handshake", "websocket-vs-http"),
    # Kafka
    ("kafka-architecture", "kafka-roles"),
    ("kafka-async-decouple", "kafka-scenarios"),
    ("kafka-peak-clipping", "kafka-scenarios"),
    ("kafka-delay-message", "kafka-scenarios"),
    ("kafka-transaction-message", "kafka-scenarios"),
    ("kafka-backlog-solution", "kafka-scenarios"),
    # 分布式锁
    ("分布式锁比喻示意图", "distributed-lock"),
    ("Zookeeper分布式锁排队示意图", "distributed-lock"),
    ("看门狗机制示意图", "lock-watchdog"),
    ("删错锁示意图", "lock-watchdog"),
    ("主从切换丢锁", "lock-watchdog"),
    # JWT
    ("JWT结构示意图", "jwt-structure"),
    ("JWT登录流程图", "jwt-login-flow"),
    ("SpringSecurity配置示意图", "jwt-login-flow"),
    # RAG
    ("RAG整体流程图_占位", "rag-pipeline"),
    ("文档切块示意图_占位", "rag-pipeline"),
    ("向量数据库存储示意图_占位", "rag-pipeline"),
    ("相似度检索示意图_占位", "rag-pipeline"),
    # 缓存
    ("缓存击穿示意图", "cache-breakdown"),
    ("缓存穿透示意图", "cache-penetration"),
    ("缓存雪崩示意图", "cache-avalanche"),
    ("Redis防抖示意图", "ttl-jitter"),
    # 算法
    ("判断链表是否有环示意图", "fast-slow-pointer"),
    ("找环的入口示意图", "fast-slow-pointer"),
    ("删除倒数第N个节点示意图", "fast-slow-pointer"),
    # 设计
    ("懒加载示意图", "lazy-progressive"),
    ("渐进式披露示意图", "lazy-progressive"),
    # 锁与并发
    ("秒杀乐观锁流程图", "optimistic-lock"),
    # 部署
    ("项目结构截图", "deploy-pipeline"),
    ("部署原理示意图", "deploy-pipeline"),
    ("Maven打包截图", "deploy-pipeline"),
    # 内网穿透
    ("frp架构图", "nat-traversal"),
    ("内网穿透示意图", "nat-traversal"),
    ("ZeroTier虚拟局域网示意图", "nat-traversal"),
]

# 这些是「操作截图」类占位，没有对应示意图，直接去掉引用
DROP_PATTERNS = [
    "云服务器选购截图", "Xshell连接截图", "Vercel部署截图",
    "cpolar-webui截图", "frp-dashboard截图", "Docker容器示意图",
    "placeholder-spring-initializr", "yourname/blog-images",
    "placehold.co",
]

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(\./([^)]+)\.md\)")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.M)


def yaml_str(s):
    """YAML 双引号字符串，转义反斜杠和双引号"""
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def to_slug_map():
    """源文件名 → slug，用于把相对链接转成文章地址"""
    m = {}
    for src, slug, _c, _t, _s in ARTICLES:
        m[src] = slug
        m[os.path.splitext(src)[0]] = slug
    return m


SLUG_OF = to_slug_map()


def download(url, dest):
    """用 curl 下载（绕开环境里可能存在的死代理）"""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    cmd = ["curl", "-sL", "-x", "", "--max-time", "90", "-o", dest, url]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=120)
        ok = r.returncode == 0 and os.path.getsize(dest) > 0
        if not ok and os.path.exists(dest):
            os.remove(dest)
        return ok
    except Exception:
        return False


def first_paragraph(body):
    """取第一段像样的正文作为 summary"""
    for block in re.split(r"\n\s*\n", body):
        t = block.strip()
        if not t or t.startswith("#") or t.startswith("---"):
            continue
        if t.startswith("!") or t.startswith("{{") or t.startswith("```"):
            continue
        if t.startswith("<") or t.startswith(">"):
            continue
        t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"[*`_>#]", "", t)
        t = t.replace("\n", "").strip()
        if len(t) < 12:
            continue
        return t[:78] + ("…" if len(t) > 78 else "")
    return ""


def insert_after_intro(body, snippet):
    """把示意图插在导语之后（第一个 --- 分隔线后，或第一个二级标题前）"""
    m = re.search(r"\n-{3,}\s*\n", body)
    if m:
        i = m.end()
        return body[:i] + "\n" + snippet + "\n" + body[i:]
    m = re.search(r"\n##\s", body)
    if m:
        i = m.start()
        return body[:i] + "\n" + snippet + "\n" + body[i:]
    return body + "\n\n" + snippet + "\n"


def process(entry):
    src_name, slug, cat, tags, need_svg = entry
    src_path = os.path.join(SRC_DIR, src_name)
    text = open(src_path, encoding="utf-8").read().replace("\r\n", "\n")

    # ---- 1. 去掉开头的 HTML 注释块 ----
    text = re.sub(r"^\s*<!--.*?-->\s*", "", text, flags=re.S)

    # ---- 2. 提取 H1 作为标题，并从正文里删掉 ----
    m = H1_RE.search(text)
    title = m.group(1).strip() if m else os.path.splitext(src_name)[0]
    if m:
        text = text[: m.start()] + text[m.end():]
    text = text.lstrip("\n")

    # ---- 3. 处理图片引用 ----
    used_svg = []          # 本文件已插入的示意图（避免重复）
    removed = []
    img_seq = {}
    counter = [0]

    def handle_img(mo):
        alt, path = mo.group(1), mo.group(2).strip()

        # CSDN 真图 → 下载到本地
        if "csdnimg.cn" in path:
            if path not in img_seq:
                counter[0] += 1
                ext = ".jpeg" if path.lower().endswith((".jpeg", ".jpg")) else ".png"
                name = "%02d%s" % (counter[0], ext)
                img_seq[path] = name
                dest = os.path.join(IMG_DIR, slug, name)
                if not DRY:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    ok = download(path, dest)
                    if not ok:
                        removed.append(("下载失败", path))
                        return ""
            local = "/blog/images/%s/%s" % (slug, img_seq[path])
            return "![%s](%s)" % (alt or "示意图", local)

        # 占位符 → 有对应示意图就换成短代码，否则去掉
        return handle_svg(path)

    # 先处理单独成行的图片（占大多数），保持段落结构干净
    # 注意：代码块里出现的 ![]() 和 <img> 是示例代码，一律不动
    lines = []
    fence_re = re.compile(r"^\s*(```|~~~)")
    in_fence = False
    dup = [0]

    def handle_svg(path):
        """占位符 → 示意图短代码；同一张图全篇只放一次"""
        for key, svg in SVG_MAP:
            if key in path:
                if svg in used_svg:
                    dup[0] += 1
                    return ""
                used_svg.append(svg)
                return '\n{{< svg "%s" >}}\n' % svg
        removed.append(("无对应图", path))
        return ""

    for line in text.split("\n"):
        if fence_re.match(line):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue

        s = line.strip()
        mo = IMG_RE.fullmatch(s) if s.startswith("![") else None
        if mo:
            lines.append(handle_img(mo).strip())
        elif s.startswith("<img"):
            removed.append(("HTML img（正文，非代码块）", s[:60]))
            lines.append("")
        else:
            lines.append(IMG_RE.sub(lambda m: handle_img(m).strip(), line))
    text = "\n".join(lines)
    if in_fence:
        print("    ! 警告：%s 的代码围栏数量不是偶数，可能有未闭合的代码块" % slug)

    # ---- 4. 相对链接 → Hugo 文章地址 ----
    def fix_link(mo):
        label, target = mo.group(1), mo.group(2)
        s = SLUG_OF.get(target)
        if s:
            return "[%s](/blog/posts/%s/)" % (label, s)
        return label

    text = LINK_RE.sub(fix_link, text)

    # ---- 5. 补齐必备示意图 ----
    added = []
    missing = [s for s in need_svg if s not in used_svg]
    for s in missing:
        snippet = '{{< svg "%s" >}}' % s
        text = insert_after_intro(text, snippet)
        used_svg.append(s)
        added.append(s)

    # ---- 6. 清理多余空行 ----
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip() + "\n"

    # ---- 7. front matter ----
    mtime = datetime.fromtimestamp(os.path.getmtime(src_path))
    summary = first_paragraph(text)
    fm = [
        "---",
        "title: %s" % yaml_str(title),
        "date: %s" % mtime.strftime("%Y-%m-%d"),
        "draft: false",
        "categories: [%s]" % yaml_str(cat),
        "tags: [%s]" % ", ".join(yaml_str(t) for t in tags),
        "summary: %s" % yaml_str(summary),
        "ShowToc: true",
        "---",
        "",
    ]
    return "".join(x + "\n" for x in fm) + "\n" + text, {
        "slug": slug, "title": title, "svg": used_svg,
        "added": added, "removed": removed, "date": mtime.strftime("%Y-%m-%d"),
    }


def main():
    if not DRY:
        os.makedirs(POSTS_DIR, exist_ok=True)
    report = []
    total_svg = 0
    for entry in ARTICLES:
        if entry[0] in SKIP:
            continue
        out, info = process(entry)
        path = os.path.join(POSTS_DIR, info["slug"] + ".md")
        if not DRY:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
        total_svg += len(info["svg"])
        report.append(info)
        print("  ✓ %-42s %s  %2d 图  %5d 字" % (
            info["slug"], info["date"], len(info["svg"]), len(out)))

    print()
    print("  共迁移 %d 篇，内联示意图 %d 处" % (len(report), total_svg))
    drops = [(r["slug"], p) for r in report for k, p in r["removed"]]
    if drops:
        print()
        print("  ---- 去掉的图片引用 ----")
        for slug, p in drops:
            print("    %-38s %s" % (slug[:36], p[:70]))


if __name__ == "__main__":
    main()
