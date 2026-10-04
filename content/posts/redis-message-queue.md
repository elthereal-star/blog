---
title: "Redis能做消息队列？不仅能，还能整出好几种姿势！"
date: 2026-06-07
draft: false
categories: ["中间件"]
tags: ["Redis", "消息队列", "Stream", "异步"]
summary: "大家在日常搬砖的时候，应该经常听到一句话：\"消息队列？上 RabbitMQ、Kafka 啊！\" 这话没毛病，但问题是——有时候咱的项目体量就那么一丢丢，为了…"
ShowToc: true
---


大家在日常搬砖的时候，应该经常听到一句话："消息队列？上 RabbitMQ、Kafka 啊！" 这话没毛病，但问题是——有时候咱的项目体量就那么一丢丢，为了一个简单的异步任务就整一套 RabbitMQ，属实有点大炮打蚊子了。更何况，光搭建和维护的成本就够你喝一壶的。

这时候咱瞅一眼旁边正在勤勤恳恳干活的 Redis，心想：这玩意儿我本来就有啊，能不能让它顺便把消息队列的活也给干了？

答案是：**能！而且方式还不少！** 今天咱就来盘一盘 Redis 实现消息队列的几种姿势，以及每种方式适合啥场景。

## 一、List 队列——最朴素的"排队买包子"模型

Redis 的 List 数据结构，天然就是一个队列。LPUSH 往左边塞消息，RPOP 从右边取消息，这不就是最经典的 FIFO（先进先出）队列嘛！

```
生产者：LPUSH queue "消息内容"
消费者：RPOP queue
```

用起来简单得一批，先引入 Jedis 依赖（Maven）：

```xml
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>4.4.6</version>
</dependency>
```

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;

JedisPool pool = new JedisPool("localhost", 6379);

// 生产者：往队列里丢消息
try (Jedis jedis = pool.getResource()) {
    jedis.lpush("task_queue", "给用户发邮件", "生成报表", "清理日志");
    // 一次 LPUSH 多条也行，左边先进后出，最终顺序是 清理日志 -> 生成报表 -> 给用户发邮件
}

// 消费者：从队列里拿消息
try (Jedis jedis = pool.getResource()) {
    while (true) {
        String task = jedis.rpop("task_queue");
        if (task != null) {
            System.out.println("处理任务：" + task);
            // 干正事...
        } else {
            Thread.sleep(1000); // 没消息就歇一会，别把自己累死
        }
    }
}
```

但这有个问题：**RPOP 是非阻塞的**，队列空了它就返回 None，消费者只能在那儿死循环 + sleep，看着就很蠢 (╯▔皿▔)╯

于是 Redis 贴心地提供了 **BRPOP**（Blocking RPOP），队列空了就乖乖等着，有消息了立马醒来：

```java
// 阻塞等待，最多等 5 秒
try (Jedis jedis = pool.getResource()) {
    while (true) {
        List<String> result = jedis.brpop(5, "task_queue");
        if (result != null) {
            // result.get(0) 是队列名，result.get(1) 才是消息内容
            String task = result.get(1);
            System.out.println("处理任务：" + task);
        }
    }
}
```

**注意事项：**
- List 队列的消息**只能被一个消费者消费**，没法搞发布订阅那一套。想要多个消费者分摊压力？多个消费者并发 BRPOP 就行，一条消息只会被一个人拿走，天然负载均衡。
- **消息可靠性全靠自己**，消费者崩了消息就没了——List 队列不帮你记着谁拿走了没处理完。

### 适用场景
- 简单的异步任务处理（发邮件、写日志、切图）
- 工作队列模式，多个 worker 分摊任务
- 对消息可靠性要求不高的场景

## 二、Pub/Sub 发布订阅——"大喇叭广播"模型

如果你需要一条消息同时发给好几个人——比如聊天室里有人发了条消息，所有在线的人都要收到——那 List 就不够用了。这时候该 **Pub/Sub** 出场了。

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPubSub;

// 消费者：订阅 chat_room 频道
Jedis subJedis = new Jedis("localhost", 6379);
// subscribe 是阻塞方法，一般开个新线程跑
new Thread(() -> {
    subJedis.subscribe(new JedisPubSub() {
        @Override
        public void onMessage(String channel, String message) {
            System.out.println("收到消息：" + message);
        }
    }, "chat_room");
}).start();

// 生产者发一条：
try (Jedis pubJedis = new Jedis("localhost", 6379)) {
    pubJedis.publish("chat_room", "大家好，我进来了！");
}
```

Pub/Sub 的精髓在于三个字：**即发即忘**。消息发出去的时候，谁在线谁就收到，不在线的就当无事发生。

**这是个巨大的坑！** 我刚学的时候就在这里栽过跟头——消费者重启一下，重启期间的消息全都丢了，一条都补不回来。所以 Pub/Sub 用来做**实时通知**很香，用来做**重要业务消息**那是要出事的。

**注意事项：**
- **消息不持久化**：没有消费者在线时发出的消息，直接消失，追都追不回来
- **消费者挂了不重连**：需要自己处理重连逻辑
- **没有 ACK 机制**：消息发出去了就算成功，消费者处没处理成，生产者根本不 care

### 适用场景
- 实时聊天消息推送
- 系统通知广播（"服务器要重启了，各位赶紧保存"）
- WebSocket 消息分发
- 配置热更新通知

## 三、Stream——Redis 5.0 的"王炸"消息队列

Stream 是 Redis 5.0 引入的数据结构，可以说就是冲着"正经消息队列"去设计的。它几乎补齐了 List 和 Pub/Sub 的所有短板，堪称 Redis 消息队列的集大成者。

核心命令长这样：

```bash
# 生产者：往 Stream 里加消息
XADD mystream * field1 value1 field2 value2
#           ↑ 这个 * 表示让 Redis 自动生成消息 ID

# 消费者：读消息
XREAD COUNT 2 STREAMS mystream 0
#                              ↑ 从第一条开始读
```

Java 里用 Jedis 搓起来也不复杂：

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.StreamEntryID;
import redis.clients.jedis.StreamEntry;
import redis.clients.jedis.params.XReadParams;
import java.util.Map;
import java.util.HashMap;
import java.util.List;

// 生产者：往 Stream 里塞消息
try (Jedis jedis = pool.getResource()) {
    Map<String, String> fields = new HashMap<>();
    fields.put("order_id", "12345");
    fields.put("user_id", "666");
    fields.put("amount", "99.9");
    jedis.xadd("order_stream", StreamEntryID.NEW_ENTRY, fields);
}

// 消费者——基础版：从 Stream 开头读取最多 10 条消息
try (Jedis jedis = pool.getResource()) {
    Map<String, StreamEntryID> streams = new HashMap<>();
    streams.put("order_stream", StreamEntryID.LAST_ENTRY); // 相当于 "0"，从头开始
    List<Map.Entry<String, List<StreamEntry>>> messages = jedis.xread(
        XReadParams.xReadParams().count(10), streams
    );
    for (Map.Entry<String, List<StreamEntry>> entry : messages) {
        for (StreamEntry msg : entry.getValue()) {
            System.out.println("消息ID: " + msg.getID() + " -> " + msg.getFields());
        }
    }
}

// 消费者——阻塞版（这才是日常用的）
try (Jedis jedis = pool.getResource()) {
    Map<String, StreamEntryID> streams = new HashMap<>();
    streams.put("order_stream", StreamEntryID.UNRECEIVED_ENTRY); // 相当于 "$"，只读新消息
    List<Map.Entry<String, List<StreamEntry>>> messages = jedis.xread(
        XReadParams.xReadParams().count(10).block(5000), streams
    );
}
```

### Stream 最骚的四个特性

**① 消息持久化**
跟 List 不一样，Stream 的消息是持久化的，写到磁盘上，服务器重启也不会丢。

**② 消费者组**
这是 Stream 的杀手级功能。多个消费者可以组成一个"消费者组"，同组内的消费者分摊消息，跟 Kafka 的消费者组一个概念：

```bash
# 创建消费者组
XGROUP CREATE mystream mygroup $ MKSTREAM

# 组内消费者1读取
XREADGROUP GROUP mygroup consumer1 COUNT 1 STREAMS mystream >

# 组内消费者2读取（不会拿到消费者1已经拿到的那条）
XREADGROUP GROUP mygroup consumer2 COUNT 1 STREAMS mystream >
```

**③ ACK 确认机制**
消息被消费者组里的某个消费者拿走之后，不会立刻删除，而是进入"pending"状态。消费者处理完了需要手动 ACK：

```bash
XACK mystream mygroup 消息ID
```

如果消费者挂了没来得及 ACK，这条消息还在 pending 里，可以交给同组的其他消费者重新处理——这就实现了**消息的可靠性投递**。

**④ 消息回溯**
Pub/Sub 丢了的消息找不回来，Stream 可以。你可以指定从某个时间点、某条消息之后开始消费，想回溯就回溯。

### Stream 实战完整代码

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.StreamEntryID;
import redis.clients.jedis.StreamEntry;
import redis.clients.jedis.params.XReadGroupParams;
import redis.clients.jedis.params.XGroupCreateParams;
import redis.clients.jedis.resps.StreamGroupInfo;
import redis.clients.jedis.exceptions.JedisDataException;
import java.util.Map;
import java.util.HashMap;
import java.util.List;

// ===== 生产者 =====
public void producer() {
    try (Jedis jedis = pool.getResource()) {
        for (int i = 0; i < 10; i++) {
            Map<String, String> fields = new HashMap<>();
            fields.put("task", "处理第" + i + "个任务");
            fields.put("create_time", String.valueOf(System.currentTimeMillis()));
            StreamEntryID msgId = jedis.xadd("mystream", StreamEntryID.NEW_ENTRY, fields);
            System.out.println("发送消息: " + msgId);
        }
    }
}

// ===== 消费者（消费者组模式）=====
public void consumer() {
    try (Jedis jedis = pool.getResource()) {
        // 确保消费者组存在（不存在就创建）
        try {
            jedis.xgroupCreate("mystream", "mygroup",
                StreamEntryID.LAST_ENTRY, // 从 Stream 开头开始消费
                true  // MKSTREAM：没有 Stream 时自动创建
            );
        } catch (JedisDataException e) {
            // 消费者组已存在，不用管
        }

        while (true) {
            Map<String, StreamEntryID> streams = new HashMap<>();
            streams.put("mystream", StreamEntryID.UNRECEIVED_ENTRY); // ">" 只读新消息

            List<Map.Entry<String, List<StreamEntry>>> msgs = jedis.xreadGroup(
                "mygroup", "consumer1",
                XReadGroupParams.xReadGroupParams().count(1).block(5000),
                streams
            );

            for (Map.Entry<String, List<StreamEntry>> entry : msgs) {
                for (StreamEntry msg : entry.getValue()) {
                    Map<String, String> fields = msg.getFields();
                    System.out.println("消费者1 收到: " + msg.getID() + " -> " + fields.get("task"));
                    // 干完活，确认！
                    jedis.xack("mystream", "mygroup", msg.getID());
                }
            }
        }
    }
}
```

**注意事项：**
- Stream 需要 Redis 5.0+，老版本请先升级再玩
- 消费者组模式下，**消息处理完一定要 XACK**，不然 pending 列表会越来越长，最后 OOM 警告
- 可以用 `XPENDING` 命令定期检查 pending 消息，及时处理积压
- Stream 的消息长度可以通过 `MAXLEN` 参数限制，防止无限增长

### 适用场景
- **正经的异步任务队列**（比 List 靠谱多了）
- 需要消费者组分摊压力的场景
- 需要消息回溯的场景（比如新上线了一个消费者，想补消费历史消息）
- 对消息可靠性有要求的业务场景

## 四、三种方式横评，一张表给你整明白

| 特性 | List (BRPOP) | Pub/Sub | Stream |
|------|-------------|---------|--------|
| 消息持久化 | ❌ | ❌ | ✅ |
| 消息确认(ACK) | ❌ | ❌ | ✅ |
| 消费者组 | ❌ | ❌ | ✅ |
| 一对多广播 | ❌ | ✅ | ❌（可用多个消费者组曲线救国） |
| 消息回溯 | ❌ | ❌ | ✅ |
| 使用复杂度 | ⭐ 极低 | ⭐ 极低 | ⭐⭐⭐ 中等 |
| Redis 版本要求 | 远古版本就支持 | 远古版本就支持 | 5.0+ |

## 五、选型建议——别纠结，看需求！

- **"我就想做个异步发邮件的功能，整个项目就我一个人用"** → 无脑 List + BRPOP，三行代码搞定
- **"我需要广播消息，有客户端不在线也没关系"** → Pub/Sub，轻量又好用
- **"消息一条都不能丢，还能多人协作消费"** → Stream，就是你了！

简单来说：活越小越用 List，实时性要求高用 Pub/Sub，正经业务用 Stream。别杀鸡用牛刀，也别拿鸡刀去砍牛，工具选对了，写代码才能猛猛的！

---


{{< svg "kafka-scenarios" >}}
以上是个人的一些经验分享，在实际项目中我也是从 List 一路用到 Stream，每种方式都有它最适合的场景。如果有哪里写的有问题或者大佬们有更好的实践，也欢迎指出来，一起交流进步！

本文完结撒花！！！ ✿✿ヽ(°▽°)ノ✿
