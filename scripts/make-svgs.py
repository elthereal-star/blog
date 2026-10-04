#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成博客文章里的 SVG 示意图（输出到 assets/svg/）

用法：
    python scripts/make-svgs.py

图形由 svgkit.py 提供的 DSL 绘制，颜色全部走 CSS 变量，
样式定义在 assets/css/extended/custom.css 第 13 节。
文章里用 {{< svg "文件名" "图注" >}} 内联引用。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svgkit import Fig  # noqa: E402

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "assets", "svg"
)


# ======================================================================
# 1. HTTP vs HTTPS
# ======================================================================
def f_http_vs_https():
    f = Fig("http-vs-https", "HTTP 明文传输与 HTTPS 加密传输的对比", 400)
    f.head("HTTP 明文传输 vs HTTPS 加密传输", "同一段账号密码，走两条路的结果完全不同")

    hops = ["浏览器", "路由器", "骨干网", "服务器"]
    xs = [24, 192, 360, 528]
    bw, bh = 144, 46

    # ---- 第一行：HTTP 明文 ----
    f.text(24, 84, "① HTTP：数据一路裸奔", cls="sf-t-warn", anchor="start", mid=False, d=0.05)
    for i, (x, name) in enumerate(zip(xs, hops)):
        f.box(x, 96, bw, bh, name, d=0.1 + i * 0.08)
    for x in (168, 336, 504):
        f.line([(x, 119), (x + 24, 119)], marker="warn", d=0.35)
    f.text(264, 174, "password=123456", cls="sf-t-warn sf-mono", mid=False, d=0.5)
    f.text(432, 174, "password=123456", cls="sf-t-warn sf-mono", mid=False, d=0.58)
    f.text(348, 156, "每一跳都能直接读到明文", cls="sf-t-sm", mid=False, d=0.45)

    # ---- 第二行：HTTPS 密文 ----
    f.text(24, 220, "② HTTPS：全程密文 + 证书验明正身", cls="sf-t-ok", anchor="start", mid=False, d=0.7)
    for i, (x, name) in enumerate(zip(xs, hops)):
        f.box(x, 232, bw, bh, name, kind="sf-box-a", d=0.75 + i * 0.08)
    for x in (168, 336, 504):
        f.line([(x, 255), (x + 24, 255)], marker="ok", d=1.0)
    f.text(264, 310, "a8f3c1…9e7b", cls="sf-t-ok sf-mono", mid=False, d=1.15)
    f.text(432, 310, "冒充 / 篡改都会被证书发现", cls="sf-t-sm", mid=False, d=1.22)

    f.text(24, 366, "结论：中间人拿到的只是一串密文；证书保证你连的确实是那台真服务器。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.35)
    return f


# ======================================================================
# 2. TLS 握手四步
# ======================================================================
def f_tls_handshake():
    f = Fig("tls-handshake", "HTTPS 建立连接的四个步骤", 320)
    f.head("HTTPS 建立连接的四步", "前两步用非对称加密交换密钥，之后全部改走对称加密")

    cards = [
        ("① ClientHello", ["客户端先打招呼", "带上支持的算法"]),
        ("② ServerHello", ["服务端选定算法", "并出示证书"]),
        ("③ 生成会话密钥", ["验证证书真伪", "双方算出同一把"]),
        ("④ 加密通话", ["改用对称加密", "之后快得多"]),
    ]
    xs = [24, 198, 372, 546]
    for i, ((title, lines), x) in enumerate(zip(cards, xs)):
        f.card(x, 94, 150, 96, title, [(t, "sf-t-sm") for t in lines], d=0.08 + i * 0.14)
    for x in (174, 348, 522):
        f.line([(x, 142), (x + 24, 142)], d=0.7)

    f.line([(24, 226), (348, 226)], kind="sf-line-dim", marker=None, draw=False, dash="4 4")
    f.line([(372, 226), (696, 226)], kind="sf-line-ok", marker=None, draw=False, dash="4 4")
    f.text(186, 246, "非对称加密（慢）——只用来交换密钥", cls="sf-t-dim", mid=False, d=0.85)
    f.text(534, 246, "对称加密（快）——之后所有数据都走它", cls="sf-t-ok", mid=False, d=0.95)

    f.text(24, 292, "对称加密的钥匙必须让对方知道，但明文传钥匙等于没加密 —— "
                    "非对称加密就是用来解决这个「先有鸡还是先有蛋」的问题。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.1)
    return f


# ======================================================================
# 3. 非对称只用来换密钥
# ======================================================================
def f_key_exchange():
    f = Fig("key-exchange", "非对称加密只负责交换会话密钥", 360)
    f.head("为什么不能全程用非对称加密？", "非对称很安全但很慢，所以只让它干一件事：交换密钥")

    f.text(24, 96, "阶段一", cls="sf-t-sm", anchor="start", mid=False, d=0.05)
    f.box(24, 106, 216, 78, "非对称加密", "RSA / ECC：安全但慢", kind="sf-box-a", d=0.1)
    f.line([(240, 145), (292, 145)], d=0.3)
    f.text(266, 132, "只传密钥", cls="sf-t-sm", mid=False, d=0.35)
    f.box(292, 106, 168, 78, "会话密钥", "Session Key", kind="sf-box-solid",
          tcls="sf-t-inv", subcls="sf-t-inv", d=0.25)

    f.text(24, 218, "阶段二", cls="sf-t-sm", anchor="start", mid=False, d=0.5)
    f.line([(376, 184), (376, 232)], d=0.55)
    f.box(24, 232, 660, 80, "对称加密：AES / ChaCha20",
          "之后所有数据都用这把会话密钥加解密，速度是非对称的上百倍",
          kind="sf-box-ok", tcls="sf-t-ok", d=0.65)

    f.text(24, 344, "结论：非对称负责「安全地交换」，对称负责「高效地传输」，两者分工，不是二选一。",
           cls="sf-t-dim", anchor="start", mid=False, d=0.85)
    return f


# ======================================================================
# 4. Kafka 四大天王
# ======================================================================
def f_kafka_roles():
    f = Fig("kafka-roles", "Kafka 中 Broker、Topic、Partition、Replica 的关系", 430)
    f.head("Kafka 的四大天王到底啥关系", "一个 Topic 拆成多个 Partition，每个 Partition 在多个 Broker 上存多份 Replica")

    x0, cw, gap = 184, 126, 20
    cols = [x0 + i * (cw + gap) for i in range(3)]
    centers = [x + cw / 2.0 for x in cols]
    span = cw * 3 + gap * 2

    f.box(x0, 64, span, 50, "Topic：订单消息", "逻辑上的消息分类",
          kind="sf-box-strong", d=0.05)
    for i, c in enumerate(centers):
        f.line([(c, 114), (c, 132)], d=0.25)
        f.text(c, 144, "P%d" % i, cls="sf-t-acc", mid=False, d=0.35)

    rows = [160, 222, 284]
    leaders = {0: 0, 1: 1, 2: 2}   # Broker i 上哪个 Partition 是 Leader
    for r, ry in enumerate(rows):
        f.box(24, ry, 140, 46, "Broker %d" % r, kind="sf-box-strong", d=0.45 + r * 0.1)
        for c in range(3):
            is_leader = (leaders[r] == c)
            f.box(cols[c], ry, cw, 46,
                  "Leader" if is_leader else "Follower",
                  kind="sf-box-solid" if is_leader else "sf-box-a",
                  tcls="sf-t-inv" if is_leader else "sf-t-acc",
                  d=0.55 + r * 0.1 + c * 0.06)

    f.text(24, 368, "Broker = 一台跑 Kafka 进程的服务器　　Topic = 消息的逻辑分类",
           cls="sf-t-dim", anchor="start", mid=False, d=1.1)
    f.text(24, 392, "Partition = Topic 的物理分片，决定并行度　　Replica = 分片的副本，决定可靠性",
           cls="sf-t-dim", anchor="start", mid=False, d=1.2)
    return f


# ======================================================================
# 5. Kafka 常见场景
# ======================================================================
def f_kafka_scenarios():
    f = Fig("kafka-scenarios", "Kafka 的四类常见使用场景", 340)
    f.head("Kafka 最常见的四类场景", "本质都是同一件事：把「直接调用」换成「经消息中转」")

    f.frame(24, 92, 400, 200, "削峰填谷", d=0.05)

    prod = [(60, 240), (90, 168), (120, 236), (150, 150), (180, 238), (210, 158),
            (240, 240), (270, 152), (300, 236), (330, 164), (360, 240), (400, 232)]
    cons = [(60, 240), (120, 224), (180, 204), (240, 188), (300, 174), (360, 165), (400, 160)]
    f.line([(56, 250), (404, 250)], kind="sf-line-dim", marker=None, draw=False)
    f.line([(56, 250), (56, 126)], kind="sf-line-dim", marker=None, draw=False)
    f.line(prod, kind="sf-line-warn sf-flow", marker=None, draw=False, dash="5 5", d=0.2)
    f.line(cons, kind="sf-line-ok", marker=None, draw=True, d=0.7)

    f.dot(66, 130, 3.4, "var(--sf-warn)", d=0.3)
    f.text(76, 130, "生产者：瞬时流量尖峰", cls="sf-t-warn", anchor="start", mid=False, d=0.3)
    f.dot(66, 152, 3.4, "var(--sf-ok)", d=0.8)
    f.text(76, 152, "消费者：按自己的节奏稳稳消费", cls="sf-t-ok", anchor="start", mid=False, d=0.8)
    f.text(216, 282, "中间这段差值，就是 Kafka 帮你扛下的峰值",
           cls="sf-t-dim", mid=False, d=1.0)

    box = [
        ("异步解耦", "下单后只发条消息，不等人"),
        ("延迟消息", "订单 30 分钟未支付自动关闭"),
        ("消息积压", "消费者扛不住时先堆在队列里"),
    ]
    for i, (t, s) in enumerate(box):
        f.box(440, 92 + i * 68, 256, 58, t, s, kind="sf-box-a", d=0.4 + i * 0.12)
    return f


# ======================================================================
# 6. 分布式锁
# ======================================================================
def f_distributed_lock():
    f = Fig("distributed-lock", "分布式锁：多台服务器抢一把全局锁", 420)
    f.head("分布式锁：为什么 synchronized 不够用",
           "锁必须放在所有机器都能看到的地方，JVM 内部的东西别人看不见")

    sx = [85, 275, 465]
    sc = [x + 85 for x in sx]
    for i, (x, c) in enumerate(zip(sx, sc)):
        f.box(x, 88, 170, 50, "服务器 %s" % "ABC"[i], "各自一个 JVM", d=0.08 + i * 0.1)

    f.line([(sc[0], 138), (230, 194)], d=0.4)
    f.line([(sc[1], 138), (360, 194)], d=0.45)
    f.line([(sc[2], 138), (490, 194)], d=0.5)

    f.box(140, 196, 440, 62, "Redis 小黑板", "SETNX 抢锁 → 业务执行 → DEL 释放",
          kind="sf-box-solid", tcls="sf-t-inv", subcls="sf-t-inv", d=0.6)
    f.ring(360, 227, 84, d=0.9)

    for i, c in enumerate(sc):
        f.line([(c, 258), (c, 288)], kind="sf-line-dim", marker=None, draw=False, dash="4 4", d=0.8)
    f.box(sx[0], 292, 170, 48, "抢到锁 ✓", kind="sf-box-ok", tcls="sf-t-ok", d=0.9)
    f.box(sx[1], 292, 170, 48, "抢锁失败，稍后重试", kind="sf-box", tcls="sf-t-dim", d=0.98)
    f.box(sx[2], 292, 170, 48, "抢锁失败，稍后重试", kind="sf-box", tcls="sf-t-dim", d=1.06)

    f.text(24, 378, "关键：锁的「可见范围」必须大于被保护资源的范围。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.2)
    fs = "Zookeeper 分布式锁、数据库乐观锁解决的是同一件事，只是「小黑板」换了个地方。"
    f.text(24, 400, fs, cls="sf-t-dim", anchor="start", mid=False, d=1.3)
    return f


# ======================================================================
# 7. 看门狗续期 vs 主从切换丢锁
# ======================================================================
def f_lock_watchdog():
    f = Fig("lock-watchdog", "看门狗续期与主从切换丢锁的对比", 410)
    f.head("锁提前没了，可能是两种完全不同的原因",
           "同样是「锁失效」，一种能救，一种只能靠更强的机制兜底")

    f.frame(24, 84, 330, 254, "① 看门狗续期（业务没跑完）", d=0.05)
    f.box(44, 130, 290, 42, "加锁：TTL = 30 秒", d=0.15)
    f.line([(189, 172), (189, 198)], d=0.3)
    f.box(44, 198, 290, 42, "看门狗每 10 秒续期一次", kind="sf-box-ok", tcls="sf-t-ok", d=0.35)
    f.line([(189, 240), (189, 266)], d=0.45)
    f.box(44, 266, 290, 42, "业务跑完 → 主动释放", d=0.5)

    f.frame(366, 84, 330, 254, "② 主从切换丢锁（锁同步丢了）", d=0.1)
    f.box(386, 130, 290, 42, "客户端 A 在 Master 上加锁", d=0.2)
    f.line([(531, 172), (531, 198)], marker="warn", d=0.35)
    f.box(386, 198, 290, 42, "Master 宕机，锁还没同步到 Slave",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.4)
    f.line([(531, 240), (531, 266)], marker="warn", d=0.5)
    f.box(386, 266, 290, 42, "Slave 升为 Master → B 也拿到锁",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.55)

    f.text(24, 374, "看门狗治的是「业务没跑完锁就过期」；主从切换丢锁要靠 RedLock 或 fencing token 兜底。",
           cls="sf-t-dim", anchor="start", mid=False, d=0.75)
    return f


# ======================================================================
# 8. 缓存击穿
# ======================================================================
def f_cache_breakdown():
    f = Fig("cache-breakdown", "缓存击穿：热点 key 过期瞬间请求全部打到数据库", 420)
    f.head("缓存击穿：一个热点 key 过期，数据库被打爆",
           "和「穿透」「雪崩」的区别：击穿的关键词是「热点 key 刚好过期」")

    f.text(24, 96, "正常情况：热点数据都在 Redis 里，DB 几乎没压力。问题只出在过期的那一瞬间。",
           cls="sf-t-dim", anchor="start", mid=False, d=0.05)

    for i in range(3):
        f.box(24, 122 + i * 56, 120, 42, "请求 %d" % (i + 1), kind="sf-box", d=0.15 + i * 0.08)
        f.line([(144, 143 + i * 56), (218, 182 + i * 5)], marker="dim", d=0.45 + i * 0.06)

    f.box(220, 150, 170, 80, "Redis", "热点 key 刚好过期",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.5)
    f.line([(390, 190), (498, 190)], marker="warn", kind="sf-line-warn sf-flow",
           dash="5 5", draw=False, d=0.7)
    f.text(444, 176, "全部穿透", cls="sf-t-warn", mid=False, d=0.75)
    f.box(500, 150, 170, 80, "MySQL", "瞬间扛下全部并发",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.6)
    f.ring(585, 190, 58, d=0.95)

    f.text(24, 288, "常见解法", cls="sf-t-dim", anchor="start", mid=False, d=1.0)
    f.chip(24, 302, 200, 44, "互斥锁重建：只放一个请求进 DB", rx=10, d=1.05)
    f.chip(240, 302, 216, 44, "逻辑过期：旧值先顶着，异步重建", rx=10, d=1.15)
    f.chip(472, 302, 200, 44, "热点 key 干脆不设过期时间", rx=10, d=1.25)

    f.text(24, 384, "注意：不设过期时间只适合确定的热点数据，否则容易变成「脏数据永不失效」。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.35)
    return f


# ======================================================================
# 9. 缓存穿透
# ======================================================================
def f_cache_penetration():
    f = Fig("cache-penetration", "缓存穿透：查询不存在的数据导致每次都打到数据库", 400)
    f.head("缓存穿透：查一个根本不存在的数据",
           "缓存和数据库都没有，于是每次请求都打到 DB —— 被人刷时数据库必挂")

    f.box(24, 118, 180, 64, "请求 id = -1", "不存在的数据",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.05)
    f.line([(204, 150), (228, 150)], marker="warn", kind="sf-line-warn", d=0.3)
    f.box(230, 118, 180, 64, "Redis", "永远查不到，不会缓存",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.15)
    f.line([(410, 150), (434, 150)], marker="warn", kind="sf-line-warn", d=0.4)
    f.box(436, 118, 260, 64, "MySQL", "也查不到 → 返回空结果",
          kind="sf-box-warn", tcls="sf-t-warn", d=0.25)

    f.curve("M566 184 L566 242 L114 242 L114 186",
            kind="sf-line-warn sf-flow", marker="warn", draw=False, dash="5 5")
    f.text(340, 266, "查不到就什么都不写 → 下一个同样的请求，完整重复一遍",
           cls="sf-t-warn", mid=False, d=0.6)

    f.text(24, 306, "三种常见解法", cls="sf-t-dim", anchor="start", mid=False, d=0.7)
    f.chip(24, 320, 206, 44, "布隆过滤器：先挡掉肯定不存在的", rx=10, d=0.75)
    f.chip(244, 320, 206, 44, "缓存空值：查不到也写个空对象", rx=10, d=0.85)
    f.chip(464, 320, 208, 44, "参数校验：非法 id 直接拒掉", rx=10, d=0.95)
    return f


# ======================================================================
# 10. 缓存雪崩
# ======================================================================
def f_cache_avalanche():
    f = Fig("cache-avalanche", "缓存雪崩：大量 key 同时过期", 440)
    f.head("缓存雪崩：大量 key 同一时刻集体过期",
           "请求瞬间全落到 DB 上。和击穿的区别是：击穿是「一个热点」，雪崩是「量大面广」")

    f.frame(24, 84, 660, 140, "① 没打散：过期时间撞在一起", d=0.05)
    for i in range(8):
        y = 116 + i * 13
        f.box(60, y, 340, 8, "", kind="sf-box-a", rx=4, d=0.15 + i * 0.05)
    f.line([(400, 108), (400, 218)], kind="sf-line-warn", marker=None, draw=True)
    f.text(414, 164, "同一秒全过期 → DB 出现尖峰", cls="sf-t-warn", anchor="start", mid=False, d=0.6)

    f.frame(24, 244, 660, 140, "② 打散后：过期时间错开", d=0.4)
    widths = [180, 240, 200, 292, 232, 320, 262, 340]
    for i, w in enumerate(widths):
        y = 276 + i * 13
        f.box(60, y, w, 8, "", kind="sf-box-ok", rx=4, d=0.5 + i * 0.05)
    f.text(414, 322, "过期时刻被摊开 → DB 压力平缓", cls="sf-t-ok", anchor="start", mid=False, d=1.0)

    f.text(24, 416, "解法：过期时间加随机抖动、多级缓存、热点数据永不过期、过期时刻加互斥锁。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.1)
    return f


# ======================================================================
# 11. 随机 TTL 防抖
# ======================================================================
def f_ttl_jitter():
    f = Fig("ttl-jitter", "随机 TTL 打散过期时间", 380)
    f.head("随机 TTL 防抖：把过期时间打散",
           "雪崩的根因是「同时过期」，最便宜的解法就是给 TTL 加一个随机偏移")

    f.box(24, 84, 660, 62, "", kind="sf-box-strong", d=0.05)
    f.text(354, 108, "TTL = BASE_TTL + random(0, JITTER)", cls="sf-t sf-mono", mid=False, d=0.1)
    f.text(354, 132, "例：基础 30 分钟 + 随机 0~5 分钟", cls="sf-t-sm", mid=False, d=0.2)

    f.frame(24, 166, 320, 140, "无抖动", d=0.3)
    f.line([(40, 290), (324, 290)], kind="sf-line-dim", marker=None, draw=False)
    f.box(168, 200, 30, 90, "", kind="sf-box-warn", rx=4, d=0.4)
    f.text(183, 194, "所有 key 同一秒过期", cls="sf-t-sm", mid=False, d=0.5)

    f.frame(376, 166, 320, 140, "加抖动", d=0.55)
    f.line([(392, 290), (676, 290)], kind="sf-line-dim", marker=None, draw=False)
    heights = [30, 52, 38, 64, 44, 58, 36, 66, 46, 54, 34, 50]
    for i, h in enumerate(heights):
        f.box(400 + i * 24, 290 - h, 16, h, "", kind="sf-box-ok", rx=4, d=0.65 + i * 0.04)
    f.text(536, 194, "过期时刻被均匀摊开", cls="sf-t-sm", mid=False, d=1.1)

    f.text(24, 348, "抖动只改变「什么时候过期」，不影响数据本身的缓存时长设计。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.25)
    return f


# ======================================================================
# 12. JWT 三段结构
# ======================================================================
def f_jwt_structure():
    f = Fig("jwt-structure", "JWT 的三段结构与各自内容", 380)
    f.head("JWT 长什么样：三段式，用点号连接",
           "header.payload.signature —— 前两段只是 Base64Url 编码，不是加密")

    segs = [
        (40, "header", "sf-box-a", "sf-t-acc"),
        (256, "payload", "sf-box", "sf-t"),
        (472, "signature", "sf-box-ok", "sf-t-ok"),
    ]
    for i, (x, name, kind, tcls) in enumerate(segs):
        f.box(x, 90, 200, 48, name, kind=kind, tcls=tcls, d=0.08 + i * 0.12)
    f.dot(248, 114, 3.6, "var(--sf-accent)", d=0.3)
    f.dot(464, 114, 3.6, "var(--sf-accent)", d=0.42)

    f.card(40, 160, 200, 118, "Header",
           [('{"alg":"HS256",', "sf-mono"), ('"typ":"JWT"}', "sf-mono")], d=0.6)
    f.card(256, 160, 200, 118, "Payload",
           [('{"sub":"1001",', "sf-mono"), ('"exp":1735689600}', "sf-mono")], d=0.72)
    f.card(472, 160, 200, 118, "Signature",
           [("HMAC(", "sf-mono"), ("base64(h)+'.'+", "sf-mono"),
            ("base64(p), secret)", "sf-mono")], d=0.84)

    f.text(24, 312, "① 前两段只是 Base64Url 编码 —— 任何人都能解开看内容，别往 payload 里放敏感信息。",
           cls="sf-t-warn", anchor="start", mid=False, d=1.0)
    f.text(24, 336, "② 签名用服务端密钥算出来 —— 改动任意一个字符，验签立刻失败。",
           cls="sf-t-ok", anchor="start", mid=False, d=1.1)
    return f


# ======================================================================
# 13. JWT 登录流程
# ======================================================================
def f_jwt_login_flow():
    f = Fig("jwt-login-flow", "JWT 登录认证的完整流程", 400)
    f.head("JWT 登录认证的完整流程", "登录只发生一次，之后每次请求都靠 token 自己证明身份")

    xs = [24, 250, 476]
    w = 200

    f.card(xs[0], 100, w, 84, "① 提交账号密码",
           [("POST /login", "sf-mono"), ("password 不明文存", "sf-t-sm")], d=0.05)
    f.card(xs[1], 100, w, 84, "② 校验并签发",
           [("查库比对密码", "sf-t-sm"), ("生成 JWT", "sf-t-sm")], d=0.17)
    f.card(xs[2], 100, w, 84, "③ 客户端保存",
           [("localStorage", "sf-mono"), ("或 HttpOnly Cookie", "sf-t-sm")], d=0.29)
    f.line([(224, 142), (248, 142)], d=0.4)
    f.line([(450, 142), (474, 142)], d=0.45)

    f.line([(124, 186), (124, 212)], d=0.55)
    f.text(132, 202, "之后每次请求，都带上这个 token", cls="sf-t-sm", anchor="start", mid=False, d=0.6)

    f.card(xs[0], 216, w, 84, "④ 带上 token",
           [("Authorization:", "sf-mono"), ("Bearer <token>", "sf-mono")], d=0.7)
    f.card(xs[1], 216, w, 84, "⑤ 过滤器验签",
           [("验签名 + 查过期", "sf-t-sm"), ("不查数据库", "sf-t-sm")], d=0.8)
    f.card(xs[2], 216, w, 84, "⑥ 放行或拒绝",
           [("通过 → 正常返回", "sf-t-ok"), ("失败 → 401", "sf-t-warn")], d=0.9)
    f.line([(224, 258), (248, 258)], d=0.95)
    f.line([(450, 258), (474, 258)], d=1.0)

    f.text(24, 340, "① 服务端不保存会话 —— JWT 是自包含的，验签通过即认为身份有效。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.1)
    f.text(24, 364, "② 代价是「注销」变难：token 一旦签发，过期前一直有效，需要额外的黑名单机制。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.2)
    return f


# ======================================================================
# 14. ThreadLocal
# ======================================================================
def f_threadlocal():
    f = Fig("threadlocal", "ThreadLocal 为每个线程保存独立副本", 420)
    f.head("ThreadLocal：每个线程一份自己的副本",
           "同一个 ThreadLocal 对象当 key，但 value 分别存在各自的线程里")

    f.box(24, 150, 160, 80, "ThreadLocal", "通常 static final",
          kind="sf-box-solid", tcls="sf-t-inv", subcls="sf-t-inv", d=0.05)

    ys = [94, 188, 282]
    for i, y in enumerate(ys):
        f.box(280, y, 400, 84, "", kind="sf-box", d=0.15 + i * 0.12)
        f.text(298, y + 24, "Thread-%d" % (i + 1), cls="sf-t", anchor="start", mid=False,
               d=0.2 + i * 0.12)
        f.box(298, y + 34, 364, 38, "", kind="sf-box-a", rx=8, d=0.25 + i * 0.12)
        f.text(480, y + 53, 'key = ThreadLocal  →  value = "用户%s"' % "ABC"[i],
               cls="sf-mono", mid=False, d=0.3 + i * 0.12)

    for y in ys:
        f.line([(184, 190), (276, y + 53)], marker="acc", d=0.5)
    f.text(230, 158, "作为 key", cls="sf-t-sm", anchor="start", mid=False, d=0.6)

    f.text(24, 396, "Entry 的 key 是弱引用：ThreadLocal 对象被回收后 value 还留在 Map 里 —— 所以用完记得 remove()。",
           cls="sf-t-dim", anchor="start", mid=False, d=0.8)
    return f


# ======================================================================
# 15. 快慢指针找环
# ======================================================================
def f_fast_slow_pointer():
    f = Fig("fast-slow-pointer", "快慢指针找链表环的入口", 400)
    f.head("快慢指针找环入口",
           "快指针每次两步、慢指针一步；相遇后再让一个指针回到起点同速前进，再次相遇就是入口")

    cxs = [70, 160, 250, 340, 430, 520]
    for i, cx in enumerate(cxs):
        f.box(cx - 20, 120, 40, 40, str(i + 1), rx=20, kind="sf-box-a", tcls="sf-t-acc",
              d=0.05 + i * 0.07)
    for a, b in zip(cxs, cxs[1:]):
        f.line([(a + 22, 140), (b - 22, 140)], d=0.5)

    f.curve("M520 162 Q520 232 385 232 Q250 232 250 162", marker="acc", d=0.9)
    f.text(385, 250, "环", cls="sf-t-sm", mid=False, d=1.0)

    f.text(250, 186, "slow（每次 1 步）", cls="sf-t-ok", mid=False, d=1.05)
    f.text(430, 110, "fast（每次 2 步）", cls="sf-t-warn", mid=False, d=1.05)
    f.ring(340, 140, 32, d=1.15)
    f.text(340, 100, "相遇点", cls="sf-t-warn", mid=False, d=1.2)

    cards = [
        ("① 同时出发", [("slow 走 1 步", "sf-t-sm"), ("fast 走 2 步", "sf-t-sm")]),
        ("② 在环内相遇", [("fast 追上 slow", "sf-t-sm"), ("说明链上有环", "sf-t-sm")]),
        ("③ 定位入口", [("一个指针回起点", "sf-t-sm"), ("同速再遇即入口", "sf-t-sm")]),
    ]
    for i, (t, lines) in enumerate(cards):
        f.card(24 + i * 226, 300, 200, 84, t, lines, d=1.25 + i * 0.1)
    f.line([(224, 342), (248, 342)], d=1.5)
    f.line([(450, 342), (474, 342)], d=1.55)
    return f


# ======================================================================
# 16. RAG 流程
# ======================================================================
def f_rag_pipeline():
    f = Fig("rag-pipeline", "RAG 的离线索引与在线问答两阶段流程", 370)
    f.head("RAG 的核心流程", "先把知识切块存进向量库，回答时先检索、再让模型基于检索结果生成")

    f.text(24, 90, "离线：把知识装进去", cls="sf-t-sm", anchor="start", mid=False, d=0.05)
    xs1 = [24, 199, 374, 549]
    step1 = [("文档", "原始资料"), ("切块", "按语义切分"),
             ("向量化", "变成向量"), ("向量库", "存储 + 索引")]
    for i, (x, (a, b)) in enumerate(zip(xs1, step1)):
        f.box(x, 100, 144, 56, a, b, d=0.1 + i * 0.1)
    for x in (168, 343, 518):
        f.line([(x, 128), (x + 31, 128)], d=0.5)

    f.text(24, 206, "在线：用户提问之后", cls="sf-t-sm", anchor="start", mid=False, d=0.7)
    xs2 = [24, 163, 302, 441, 580]
    step2 = ["提问", "向量化", "检索 top-k", "拼 Prompt", "LLM 生成"]
    for i, (x, t) in enumerate(zip(xs2, step2)):
        f.box(x, 216, 112, 56, t, d=0.8 + i * 0.08)
    for x in (136, 275, 414, 553):
        f.line([(x, 244), (x + 27, 244)], d=1.1)

    f.line([(621, 158), (621, 192), (358, 192), (358, 214)], marker="acc", d=1.25)
    f.text(490, 184, "检索最相似的 N 块", cls="sf-t-sm", mid=False, d=1.35)

    f.text(24, 340, "RAG 的关键不是「让模型记住」，而是「每次回答前，把相关资料现查现给」。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.45)
    return f


# ======================================================================
# 17. SingleFlight
# ======================================================================
def f_singleflight():
    f = Fig("singleflight", "SingleFlight 把并发请求合并成一次查询", 390)
    f.head("SingleFlight：把并发请求合成一次",
           "缓存失效那一瞬间涌来一堆同样的请求，只应该有一个真正去查数据库")

    ys = [110, 160, 210, 260]
    for i, y in enumerate(ys):
        f.box(24, y, 150, 42, "请求 %d" % (i + 1), kind="sf-box", d=0.05 + i * 0.08)
        f.line([(174, y + 21), (216, 190 + i * 6)], marker="dim", d=0.5 + i * 0.05)

    f.frame(220, 104, 190, 206, "SingleFlight", d=0.4)
    f.line([(410, 207), (466, 205)], marker="ok", kind="sf-line-ok", d=0.75)
    f.text(438, 196, "只查 1 次", cls="sf-t-ok", mid=False, d=0.8)
    f.box(470, 170, 220, 70, "MySQL", "不会被并发打爆", kind="sf-box-ok", tcls="sf-t-ok", d=0.7)

    f.curve("M315 314 L315 336 L99 336 L99 306", kind="sf-line sf-flow", marker="acc",
            draw=False, dash="5 5")
    f.text(207, 358, "结果回传给所有等待的请求", cls="sf-t-dim", mid=False, d=0.9)
    return f


# ======================================================================
# 18. PO / BO / DTO / VO 分层
# ======================================================================
def f_pojo_layers():
    f = Fig("pojo-layers", "PO、BO、DTO、VO 在各层之间的流动", 380)
    f.head("PO / BO / DTO / VO 到底谁是谁",
           "同一份数据在不同层穿不同衣服，各层只依赖自己需要的那件")

    xs = [24, 163, 302, 441, 580]
    w = 116

    f.text(24, 88, "写入：前端表单 → 数据库", cls="sf-t-sm", anchor="start", mid=False, d=0.05)
    row1 = [("DTO", "接收前端入参"), ("BO", "业务校验加工"), ("PO", "与表结构对应"),
            ("DAO", "只负责读写"), ("MySQL", "最终落库")]
    for i, (x, (a, b)) in enumerate(zip(xs, row1)):
        f.box(x, 98, w, 62, a, b, d=0.1 + i * 0.08)
    for x in (140, 279, 418, 557):
        f.line([(x, 129), (x + 23, 129)], d=0.6)

    f.text(24, 206, "读取：数据库 → 前端展示", cls="sf-t-sm", anchor="start", mid=False, d=0.7)
    row2 = [("MySQL", "查出原始行"), ("PO", "映射成对象"), ("BO", "业务加工"),
            ("VO", "裁剪展示字段"), ("前端页面", "渲染成界面")]
    for i, (x, (a, b)) in enumerate(zip(xs, row2)):
        f.box(x, 216, w, 62, a, b, kind="sf-box-a", d=0.75 + i * 0.08)
    for x in (140, 279, 418, 557):
        f.line([(x, 247), (x + 23, 247)], d=1.2)

    f.text(24, 312, "PO 贴着表结构走，BO 贴着业务走，DTO 贴着接口走，VO 贴着页面走 —— 谁都不用迁就谁。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.35)
    f.text(24, 336, "好处：改表结构不用改接口，改页面不用改业务。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.45)
    return f


# ======================================================================
# 19. HTTP 轮询 vs WebSocket
# ======================================================================
def f_websocket_vs_http():
    f = Fig("websocket-vs-http", "HTTP 轮询与 WebSocket 长连接的对比", 450)
    f.head("HTTP 轮询 vs WebSocket",
           "同样是「服务端有新消息就推给我」，两种做法的代价差很多")

    f.frame(24, 84, 660, 160, "① HTTP 轮询：反复建连，大量空响应", d=0.05)
    f.box(48, 140, 120, 56, "客户端", d=0.1)
    f.box(556, 140, 120, 56, "服务端", d=0.1)
    pairs = [(150, 162, "无新数据"), (186, 198, "无新数据"), (222, 234, "有新数据 ✓")]
    for i, (ry, sy, label) in enumerate(pairs):
        f.line([(168, ry), (552, ry)], marker="acc", d=0.2 + i * 0.1)
        f.line([(552, sy), (168, sy)], marker="dim", d=0.25 + i * 0.1)
        f.text(360, ry - 8, label, cls="sf-t-ok" if "✓" in label else "sf-t-sm",
               mid=False, d=0.3 + i * 0.1)

    f.frame(24, 268, 660, 160, "② WebSocket：一次握手，之后双向随时推", d=0.6)
    f.box(48, 310, 120, 56, "客户端", kind="sf-box-a", d=0.65)
    f.box(556, 310, 120, 56, "服务端", kind="sf-box-a", d=0.65)
    f.line([(168, 338), (552, 338)], marker="acc", d=0.8)
    f.text(360, 328, "① 握手升级协议（只这一次）", cls="sf-t-sm", mid=False, d=0.85)
    f.line([(168, 372), (552, 372)], kind="sf-line-ok sf-flow", marker=None,
           draw=False, dash="5 5", d=0.95)
    f.line([(552, 388), (168, 388)], kind="sf-line-ok sf-flow", marker=None,
           draw=False, dash="5 5", d=1.0)
    f.text(360, 410, "② 之后任何时候，双方都能直接推", cls="sf-t-ok", mid=False, d=1.1)

    f.text(24, 448, "轮询实现简单但浪费连接和带宽；WebSocket 一次连接长期复用，代价是要自己处理断线重连。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.2)
    return f


# ======================================================================
# 20. 内网穿透
# ======================================================================
def f_nat_traversal():
    f = Fig("nat-traversal", "内网穿透：内网机器主动连出去建立隧道", 380)
    f.head("内网穿透：让没有公网 IP 的服务也能被访问",
           "内网机器主动连出去，在有公网 IP 的服务器上开一个入口")

    f.frame(24, 96, 260, 210, "内网（没有公网 IP）", d=0.05)
    f.box(44, 130, 220, 50, "frp 客户端", "始终主动连出去", d=0.1)
    f.box(44, 216, 220, 50, "本地服务 :8080", "真正干活的程序", kind="sf-box-a", d=0.2)
    f.line([(154, 214), (154, 184)], d=0.4)

    f.box(330, 140, 180, 110, "云服务器", "frp 服务端 + Nginx",
          kind="sf-box-solid", tcls="sf-t-inv", subcls="sf-t-inv", d=0.5)
    f.box(556, 160, 140, 70, "外部用户", "访问你的域名", d=0.6)

    f.line([(264, 156), (326, 178)], d=0.7)
    f.text(292, 140, "① 注册隧道", cls="sf-t-sm", mid=False, d=0.75)
    f.line([(552, 188), (514, 188)], d=0.85)
    f.text(533, 178, "② 请求", cls="sf-t-sm", mid=False, d=0.9)
    f.line([(330, 228), (268, 246)], d=1.0)
    f.text(300, 262, "③ 转发到内网", cls="sf-t-sm", mid=False, d=1.05)

    f.text(24, 348, "对外的入口只有一个公网地址，内网机器始终是主动连出去的 —— 不用改路由器，也不要公网 IP。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.2)
    return f


# ======================================================================
# 21. Fencing Token
# ======================================================================
def f_fencing_token():
    f = Fig("fencing-token", "Fencing Token 用递增编号拒绝旧客户端写入", 380)
    f.head("Fencing Token：挡住「睡醒的老客户端」",
           "存储端记住见过的最大编号，编号比它小的写入一律拒绝")

    f.box(24, 104, 200, 56, "客户端 A", "拿到 token = 33", d=0.05)
    f.box(24, 254, 200, 56, "客户端 B", "拿到 token = 34", d=0.15)
    f.card(300, 164, 170, 96, "存储端",
           [("记住见过的最大编号", "sf-t-sm"), ("max token = 34", "sf-mono")], d=0.3)
    f.box(520, 96, 176, 68, "✗ 拒绝", "33 < 34", kind="sf-box-warn", tcls="sf-t-warn", d=0.45)
    f.box(520, 248, 176, 68, "✓ 接受", "34 ≥ 34", kind="sf-box-ok", tcls="sf-t-ok", d=0.55)

    f.line([(224, 128), (296, 178)], marker="warn", kind="sf-line-warn", d=0.65)
    f.text(238, 146, "写 token=33", cls="sf-t-warn", anchor="start", mid=False, d=0.7)
    f.line([(470, 188), (516, 134)], marker="warn", kind="sf-line-warn", d=0.8)
    f.line([(224, 286), (296, 246)], marker="ok", kind="sf-line-ok", d=0.75)
    f.text(238, 300, "写 token=34", cls="sf-t-ok", anchor="start", mid=False, d=0.82)
    f.line([(470, 232), (516, 278)], marker="ok", kind="sf-line-ok", d=0.9)

    f.text(24, 344, "关键：锁服务和存储端要共享同一个单调递增计数器，否则「老客户端」根本无法被识别。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.05)
    return f


# ======================================================================
# 22. 懒加载与渐进式披露
# ======================================================================
def f_lazy_progressive():
    f = Fig("lazy-progressive", "一次性全量展示与渐进式披露的对比", 330)
    f.head("懒加载与渐进式披露：别一上来就全塞给用户",
           "先给最小可用信息，剩下的按需展开 —— 加载性能和信息消化都是这个道理")

    f.frame(24, 92, 320, 180, "一次性全部展示", d=0.05)
    widths = [240, 200, 260, 180, 230, 210, 250, 190]
    for i, w in enumerate(widths):
        f.box(48, 128 + i * 15, w, 8, "", kind="sf-box-warn", rx=4, d=0.15 + i * 0.04)
    f.text(184, 256, "认知负担大，重点被淹没", cls="sf-t-warn", mid=False, d=0.6)

    f.frame(376, 92, 320, 180, "先给主干，按需展开", d=0.7)
    for i, w in enumerate([240, 200, 220]):
        f.box(400, 128 + i * 24, w, 8, "", kind="sf-box-ok", rx=4, d=0.8 + i * 0.08)
    f.box(400, 204, 200, 34, "展开更多 ▾", kind="sf-box-ghost", tcls="sf-t-dim", d=1.0)
    f.text(536, 256, "先看懂主线，细节随时展开", cls="sf-t-ok", mid=False, d=1.1)
    return f


# ======================================================================
# 23. 乐观锁
# ======================================================================
def f_optimistic_lock():
    f = Fig("optimistic-lock", "乐观锁用版本号解决超卖", 390)
    f.head("乐观锁：用版本号解决超卖",
           "不提前加锁，更新时校验版本号 —— 谁改动了数据，谁的更新就会落空")

    f.box(24, 104, 190, 56, "用户 A", "读出 version = 1", d=0.05)
    f.box(24, 254, 190, 56, "用户 B", "也读出 version = 1", d=0.15)
    f.box(290, 164, 180, 86, "库存行", "version = 1", kind="sf-box-strong", d=0.3)
    f.box(520, 96, 176, 68, "✓ 更新成功", "version 1 → 2", kind="sf-box-ok",
          tcls="sf-t-ok", d=0.45)
    f.box(520, 248, 176, 68, "✗ 影响 0 行", "需要重新读再试", kind="sf-box-warn",
          tcls="sf-t-warn", d=0.55)

    f.line([(214, 128), (286, 180)], marker="dim", d=0.65)
    f.line([(214, 286), (286, 234)], marker="dim", d=0.7)
    f.line([(470, 186), (516, 136)], marker="ok", kind="sf-line-ok", d=0.8)
    f.line([(470, 228), (516, 276)], marker="warn", kind="sf-line-warn", d=0.85)

    f.text(24, 336, "UPDATE stock SET count = count - 1, version = version + 1",
           cls="sf-t sf-mono", anchor="start", mid=False, d=1.0)
    f.text(24, 358, "WHERE id = 1 AND version = 1;", cls="sf-t sf-mono",
           anchor="start", mid=False, d=1.05)
    f.text(24, 382, "影响行数 = 1 → 抢到；= 0 → 期间被别人改过，重新读取再试一次。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.15)
    return f


# ======================================================================
# 24. 部署流程
# ======================================================================
def f_deploy_pipeline():
    f = Fig("deploy-pipeline", "从本地代码到域名可访问的部署流程", 370)
    f.head("把一个项目部署到别人也能访问",
           "从本地代码到域名可访问，每一步都在解决一个具体问题")

    xs1 = [24, 198, 372, 546]
    step1 = [("本地代码", "开发完成"), ("git push", "推到远程仓库"),
             ("服务器拉取", "git pull"), ("Maven 打包", "mvn package")]
    for i, (x, (a, b)) in enumerate(zip(xs1, step1)):
        f.box(x, 100, 150, 62, a, b, d=0.05 + i * 0.1)
    for x in (174, 348, 522):
        f.line([(x, 131), (x + 24, 131)], d=0.5)

    xs2 = [24, 254, 484]
    step2 = [("启动 JAR", "nohup java -jar"), ("Nginx 反向代理", "80 端口 → 8080"),
             ("域名访问", "浏览器打开站点")]
    for i, (x, (a, b)) in enumerate(zip(xs2, step2)):
        f.box(x, 232, 204, 62, a, b, kind="sf-box-a", d=0.7 + i * 0.1)
    f.line([(228, 263), (252, 263)], d=1.0)
    f.line([(458, 263), (482, 263)], d=1.05)

    f.line([(621, 164), (621, 200), (126, 200), (126, 228)], marker="acc", d=1.15)
    f.text(374, 192, "打包产物在服务器上跑起来", cls="sf-t-sm", mid=False, d=1.25)

    f.text(24, 336, "如果只是想让别人看到，还有更省事的路线：Vercel / Netlify 直接连仓库，push 完自动部署。",
           cls="sf-t-dim", anchor="start", mid=False, d=1.35)
    return f


FIGURES = [
    f_http_vs_https,
    f_tls_handshake,
    f_key_exchange,
    f_kafka_roles,
    f_kafka_scenarios,
    f_distributed_lock,
    f_lock_watchdog,
    f_cache_breakdown,
    f_cache_penetration,
    f_cache_avalanche,
    f_ttl_jitter,
    f_jwt_structure,
    f_jwt_login_flow,
    f_threadlocal,
    f_fast_slow_pointer,
    f_rag_pipeline,
    f_singleflight,
    f_pojo_layers,
    f_websocket_vs_http,
    f_nat_traversal,
    f_fencing_token,
    f_lazy_progressive,
    f_optimistic_lock,
    f_deploy_pipeline,
]


def main():
    out = os.path.normpath(OUT)
    os.makedirs(out, exist_ok=True)
    total = 0
    for fn in FIGURES:
        fig = fn()
        path = os.path.join(out, fig.name + ".svg")
        data = fig.render()
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
        size = len(data.encode("utf-8"))
        total += size
        print("  %-28s %7s bytes" % (fig.name + ".svg", format(size, ",")))
    print("  %-28s %7s bytes" % ("合计 %d 张" % len(FIGURES), format(total, ",")))


if __name__ == "__main__":
    main()
