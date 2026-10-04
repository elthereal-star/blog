---
title: "分布式锁三巨头掰手腕：Redis vs Zookeeper vs 数据库乐观锁，你的项目到底该用谁？"
date: 2026-06-08
draft: false
categories: ["中间件"]
tags: ["Redis", "Zookeeper", "分布式锁", "乐观锁"]
summary: "嗨朋友们！之前咱不是分别聊过 Redis 分布式锁和数据库乐观锁嘛，然后就有朋友在后台问我：\"你光说它们各自咋用，那我实际项目里到底选哪个啊？\""
ShowToc: true
---


嗨朋友们！之前咱不是分别聊过 Redis 分布式锁和数据库乐观锁嘛，然后就有朋友在后台问我："你光说它们各自咋用，那我实际项目里到底选哪个啊？"

嘿，这问题问得好。分布式锁这东西吧，有点像买手机——有人要性价比，有人要稳定性，有人就图个省事儿。三种方案各有各的好处，也各有各的坑，**没有绝对的谁好谁坏，只有合不合适**。

所以今天这篇，咱就把 Redis 分布式锁、Zookeeper 分布式锁、数据库乐观锁这哥仨拉到一起，从原理到代码、从性能到可靠性，一条条掰扯清楚。看完这篇你再选方案，心里就有谱了 (๑•̀ㅂ•́)و✧

---

## 先整个场景，不然干聊没意思

咱假设一个场景：你负责的电商项目要做一个**秒杀活动**，茅台 1499 随便抢（梦里啥都有）。库存就 100 瓶，结果活动一开始涌进来 10 万个请求。

这时候你要解决的问题就是：**怎么保证这 100 瓶茅台不被超卖？**

三种锁都能解决这个问题，但方案完全不同。咱一个个来。

---

## 方案一：数据库乐观锁——最"佛系"的选手

乐观锁的思路在 [上一篇关于乐观锁的文章]() 里咱已经细聊过了，这里快速回顾一下核心操作：

```sql
-- 关键就是 UPDATE 的时候带上 version 条件
UPDATE product
SET stock = stock - 1, version = version + 1
WHERE id = 1 AND version = 5;
-- 如果 version 已经不是 5 了，影响行数就是 0，说明被人抢先了
```

```java
public Result seckill(Long productId) {
    Product product = productMapper.selectById(productId);
    if (product.getStock() <= 0) {
        return Result.fail("来晚了，抢光了！");
    }
    
    int rows = productMapper.deductStock(productId, product.getVersion());
    if (rows == 0) {
        // 版本号变了，说明被人抢先改过了，重试
        return Result.fail("手速不够，再试一次~");
    }
    // 扣减成功，创建订单...
    return Result.ok("恭喜抢到茅台！");
}
```

### 乐观锁的脾气

**优点：**
- 实现简单到飞起，不需要引入任何额外中间件，数据库自带的能力
- 不会死锁，因为根本没加锁，只是 CAS 的思想用在数据库层面了
- 对于冲突不频繁的场景，性能杠杠的

**缺点：**
- 高并发冲突下，大量 UPDATE 返回 0，需要不停重试，用户体验差（用户：我明明点了，你告诉我重试？）
- 重试次数得控制好，不然可能变成死循环，CPU 狂飙

**一句话总结：适合冲突不频繁、对一致性要求不那么极端的场景。** 比如常规的商品下单，不太适合秒杀这种请求密度爆炸的场景。

---

## 方案二：Redis 分布式锁——最"能打"的选手

Redis 分布式锁的进化之路咱在 [上一篇 Redis 分布式锁的文章]() 里从头撸到尾了，从手搓 SETNX 到 Redisson 全家桶。这里咱直接上目前业界最主流的方案——**Redisson**：

```java
@Autowired
private RedissonClient redissonClient;

public Result seckill(Long productId) {
    String lockKey = "lock:seckill:" + productId;
    RLock lock = redissonClient.getLock(lockKey);
    
    try {
        // 尝试加锁，最多等 3 秒，锁 10 秒后自动释放
        if (!lock.tryLock(3, 10, TimeUnit.SECONDS)) {
            return Result.fail("人太多了，请稍后再试~");
        }
        
        // 拿到锁了，查库存、扣库存
        Product product = productMapper.selectById(productId);
        if (product.getStock() <= 0) {
            return Result.fail("抢光了！");
        }
        productMapper.deductStock(productId, product.getVersion());
        
        return Result.ok("恭喜抢到茅台！");
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        return Result.fail("系统异常");
    } finally {
        // 重点！一定在 finally 里释放锁
        lock.unlock();
    }
}
```

### Redisson 帮咱解决了啥？

自己手搓 Redis 锁有几个经典大坑：锁过期了业务还没跑完怎么办？主节点挂了锁丢了怎么办？Redisson 都帮咱处理好了：

- **看门狗机制**：锁默认 30 秒过期，但 Redisson 会每 10 秒自动续期，只要你的业务在跑，锁就永远不会自己过期
- **红锁（RedLock）**：多个独立的 Redis 节点同时加锁，大多数加锁成功才算成功，大幅降低单节点故障丢锁的风险

### Redis 锁的脾气

**优点：**
- 性能最高，Redis 天生就是内存操作，加锁释锁快到飞起
- 生态成熟，Redisson 封装得相当好，API 跟 Java 的 Lock 接口几乎一样，上手成本极低
- 自带过期机制，不用担心死锁

**缺点：**
- 单节点 Redis 存在丢锁风险（主节点挂了，从节点还没同步到锁数据）
- 红锁能解决但运维复杂度上升，得维护多个独立 Redis 实例
- **不适合对一致性要求极度苛刻的场景**（比如金融扣款）

**一句话总结：适合高并发、对性能要求高、可以容忍极低概率的锁丢失的场景。** 比如秒杀、抢购、防重复提交，Redis 是首选。

---

## 方案三：Zookeeper 分布式锁——最"稳"的选手

好了，现在该请出今天的主角之一了——Zookeeper。很多朋友可能只听说过它，没用过它，更不知道它还能当分布式锁使。

### Zookeeper 是啥？先打个比方

Redis 咱们比作楼下的**公告黑板**，大家看一眼写上去就行，速度快但偶尔粉笔字被擦了就麻烦了。

Zookeeper 呢？它就像**政府机关的档案室**。你进去查一份档案，必须先登记，查完了销登记。档案室的管理制度极其严格——**顺序编号、不允许插队、谁登记了必须登记到底**。哪怕档案室的电脑断电了，重启后登记信息还在（持久化）。慢是慢了点，但稳得一批。

### Zookeeper 的节点特性，天然适合做锁

Zookeeper 的数据结构有点像文件系统，是一棵树。它有几个关键特性让它特别适合干锁这个活儿：

1. **临时顺序节点**：可以创建"临时的、带编号的"节点。临时意味着客户端断开连接后节点自动删除（不怕死锁），顺序意味着节点名称带递增数字（天然排队）
2. **Watch 机制**：可以监听一个节点的变化，节点被删除了你马上能感知到（不用轮询）

### 上代码，用 Curator 实现 Zookeeper 分布式锁

直接手搓 Zookeeper 的原生 API 那是真的痛苦，好在有 Curator 这个库帮咱封装好了：

```java
// 引入 Curator
@Configuration
public class ZkConfig {
    @Bean
    public CuratorFramework curatorFramework() {
        CuratorFramework client = CuratorFrameworkFactory
            .builder()
            .connectString("127.0.0.1:2181")  // Zookeeper 地址
            .sessionTimeoutMs(60000)
            .connectionTimeoutMs(15000)
            .retryPolicy(new ExponentialBackoffRetry(1000, 3))
            .build();
        client.start();
        return client;
    }
}

@Service
public class SeckillService {
    
    @Autowired
    private CuratorFramework curatorClient;
    
    public Result seckill(Long productId) {
        String lockPath = "/lock/seckill/" + productId;
        InterProcessMutex lock = new InterProcessMutex(curatorClient, lockPath);
        
        try {
            // 尝试加锁，最多等 3 秒
            if (!lock.acquire(3, TimeUnit.SECONDS)) {
                return Result.fail("人太多了，请稍后再试~");
            }
            
            // 拿到锁，执行业务逻辑
            Product product = productMapper.selectById(productId);
            if (product.getStock() <= 0) {
                return Result.fail("抢光了！");
            }
            productMapper.deductStock(productId, product.getVersion());
            
            return Result.ok("恭喜抢到茅台！");
            
        } catch (Exception e) {
            return Result.fail("系统异常");
        } finally {
            // 释放锁
            try {
                lock.release();
            } catch (Exception e) {
                // 日志记录
            }
        }
    }
}
```

### Zookeeper 锁的工作原理，比 Redis 有意思

咱结合刚才说的"档案室"比喻来看看底层的流程：

1. 每个请求过来，都在 Zookeeper 的 `/lock/seckill/1` 路径下创建一个**临时顺序节点**，比如 `lock-0001`、`lock-0002`、`lock-0003`
2. 大家都去看看自己是不是兄弟里编号最小的那个
3. **编号最小的拿到锁**，进去干活
4. 没拿到锁的也不闲着，他们 **Watch 排在自己前面的那个节点**
5. 拿到锁的干完活了，删除自己的节点（或者客户端挂了，临时节点自动删除）
6. 后面的节点发现自己 Watch 的节点没了，**立刻被唤醒**，再去检查自己是不是最小的

注意这里有个巧妙的设计：**只 Watch 前一个节点**，而不是 Watch 所有人。这样锁释放的时候不会出现"惊群效应"——100 个人排队，锁释放了只唤醒第 2 个人，而不是 100 个人全醒了然后抢，抢不过继续睡。

{{< svg "distributed-lock" >}}

### Zookeeper 锁的脾气

**优点：**
- **强一致性**，锁信息被 Zookeeper 集群中多数节点确认后才返回成功，不会丢锁
- 临时节点机制天然防死锁，客户端挂了、网络断了，节点自动删除，锁自动释放
- Watch 机制比轮询优雅，不用一直去问"锁好了没锁好了没"

**缺点：**
- **性能不如 Redis**，Zookeeper 的强一致性依赖 ZAB 协议，加锁释锁的延迟比 Redis 高一两个数量级
- 需要额外维护 Zookeeper 集群，运维成本比 Redis 高（大部分项目本来就有 Redis，不一定有 Zookeeper）
- 在高并发场景下，Zookeeper 集群可能成为瓶颈

**一句话总结：适合对一致性要求极高、可以接受一定性能损耗的场景。** 比如分布式任务调度（保证一个任务只在一台机器上跑）、配置管理、分布式协调等。

---

## 终极对比，一张表看清楚

| 对比维度 | 数据库乐观锁 | Redis 分布式锁 | Zookeeper 分布式锁 |
|---------|------------|--------------|------------------|
| **实现复杂度** | 简单，改 SQL 就行 | 中等，引入 Redisson | 较高，需要 ZK 集群 + Curator |
| **性能** | 一般（依赖数据库） | 很高（内存操作） | 中等（ZAB 协议有开销） |
| **一致性** | 依赖数据库 | 单节点有丢锁风险，红锁可缓解 | 强一致性，不丢锁 |
| **死锁风险** | 无（无锁） | 有（靠过期时间兜底） | 低（临时节点自动删除） |
| **额外依赖** | 无 | 需要 Redis | 需要 Zookeeper 集群 |
| **并发冲突处理** | 重试（用户体感差） | 阻塞等待 | 顺序排队（公平锁） |
| **可重入** | 需手动实现 | Redisson 自带 | Curator 自带 |
| **公平性** | 不公平 | 默认不公平，可实现 | **天然公平锁** |

---

## 到底咋选？给你一个决策指南

别头疼，咱直接把场景跟方案对号入座：

### 选 Redis 分布式锁，当你的场景是：

- 秒杀、抢购、红包等**高并发业务**
- 防止接口重复提交
- 分布式定时任务（需要用锁保证同一时刻只有一台机器执行）
- **项目里本来就有 Redis**，不想引入新中间件
- 能接受极低概率的锁丢失（可以加个数据库兜底：扣库存前 `UPDATE ... WHERE stock > 0`）

### 选 Zookeeper 分布式锁，当你的场景是：

- 分布式系统的**主节点选举**（只有一台机器能当 master）
- 分布式任务调度（保证任务绝对不重复执行）
- **对数据一致性要求极高**的扣款、转账等
- 项目已经有 Zookeeper 集群（比如用了 Dubbo、Kafka）
- 需要公平锁（排队等待，先来先服务）

### 选数据库乐观锁，当你的场景是：

- **并发量不高**，冲突不频繁
- 不想引入任何额外中间件，架构越简单越好
- 只是常规的 CRUD 更新，捎带手做下并发控制
- 比较适合在已有业务上做"锦上添花"，而不是"雪中送炭"

---

## 其实还有个组合拳打法

在实际项目里，这三种锁其实不是"三选一"的关系，很多时候它们是**搭档**：

```
秒杀请求
    │
    ▼
Redis 分布式锁（第一道防线，挡掉 90% 的并发）
    │
    ▼
数据库乐观锁（第二道防线，兜底，确保库存绝对安全）
    │
    ▼
下单成功
```

Redis 锁在前面扛住海量并发，乐观锁在数据库层面做最后一道兜底。**就算 Redis 锁出了问题，数据库乐观锁也能保你库存不超卖。** 这是我个人做秒杀类业务最推荐的方式。

---

## 补充一点：Redis 红锁到底要不要用？

可能有大佬会说："Redis 红锁不是被业界喷过嘛，很多大佬说不推荐用。"

确实，Redis 作者提出的 RedLock 算法在分布式系统圈引发过激烈讨论。但我觉得这事儿得辩证地看：

- **如果你的业务能容忍极低概率的锁丢失**（比如上面的组合拳方案，数据库乐观锁兜底），单节点 Redis 锁就够用了，没必要上红锁
- **如果你的业务绝对不能丢锁**（比如金融扣款），那直接上 Zookeeper 吧，别在 Redis 上折腾了

说到底还是那句话：**没有银弹，只有合适的方案。**

---

好了，这篇把分布式锁三巨头的对比给盘完了。从原理、代码、优缺点到选型决策，希望能帮你在实际项目中少走点弯路。

以上是个人在实际项目中摸爬滚打的一些经验分享，不一定全对。如果哪里讲得有毛病，还请大佬们评论区指正，一起交流进步 (･ω･)ﾉ

本文完结撒花！！！
