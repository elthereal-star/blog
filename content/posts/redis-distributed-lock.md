---
title: "一个分布式锁把面试官整emo了，Redis的锁原来这么多花样？"
date: 2026-06-04
draft: false
categories: ["中间件"]
tags: ["Redis", "分布式锁", "Redisson", "高并发"]
summary: "嗨朋友们！不知道你们在搞分布式项目的时候有没有碰到过这种蛋疼的情况——用户手一抖连点了两下提交按钮，结果订单就生成了两份？或者更惨的，定时任务在多台服务器上…"
ShowToc: true
---


嗨朋友们！不知道你们在搞分布式项目的时候有没有碰到过这种蛋疼的情况——用户手一抖连点了两下提交按钮，结果订单就生成了两份？或者更惨的，定时任务在多台服务器上同时跑，数据被重复处理了 N 遍？

这时候你一拍大腿："加个锁不就完事了嘛！"

然后你美滋滋地在代码里写了个 `synchronized`，部署上去发现——**根本锁不住啊！** 原因也很简单，你那 `synchronized` 是 JVM 级别的锁，只能锁住当前这台机器的线程，隔壁那台服务器上的请求照样大摇大摆地进来了 (￣▽￣)~*

这就是分布式锁的用武之地了。今天咱就来盘一盘 Redis 分布式锁的那些花式玩法，从最简陋的手搓版本一路升级到 Redisson 全家桶，保证你看完就能去面试的时候侃侃而谈！

---

## 啥是分布式锁？先整个通俗的比喻

在开整之前，先给新手朋友整明白分布式锁到底是啥。

打个比方哈：咱公司只有一个厕所（共享资源），以前公司就一层楼，大家都认识，去厕所之前吼一嗓子"我进去了哈"就行，别人听到就等着——这就是 `synchronized`，单机锁，管一层楼没问题。

后来公司扩张了，搬到了三层楼的写字楼。这时候你在三楼吼一嗓子，一楼的人根本听不见啊！结果就可能出现你三楼的人进去蹲坑，一楼的人也进去了——**两个人在同一时间用同一个厕所**，这就尴尬了...

这时候你就需要一个**整栋楼都能看到的东西**来协调——比如在门口挂一个小黑板，谁要上厕所就在黑板上写"我在里面"，出来就擦掉。所有人都看这块黑板行事。

**这块黑板就是 Redis**。大家都能访问它，所以它上面记录的信息（锁）对所有机器都生效。这就是分布式锁的核心思想：**用一个所有服务都能访问到的中间件来协调谁可以访问共享资源**。

{{< svg "distributed-lock" >}}

---

## 手搓一个最简陋的分布式锁

咱先从最原始版本开始，一步步看看这玩意儿是怎么进化的。

### 第一版：SETNX 一把梭

Redis 里有个命令叫 `SETNX`（SET if Not eXists），意思是"如果 key 不存在就设置成功，如果 key 已经存在就啥也不干"。这不就天然是个锁嘛！

```java
public String placeOrder(Long userId, Long productId) {
    String lockKey = "lock:order:" + productId;

    // 尝试获取锁，setIfAbsent 就是 SETNX 命令
    Boolean gotLock = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1");

    if (Boolean.FALSE.equals(gotLock)) {
        return "有人在抢，等会儿再试~";
    }

    try {
        // 拿到锁了，执行业务逻辑
        // 查库存、扣库存、创建订单...
        orderService.doCreateOrder(userId, productId);
    } finally {
        // 用完了，释放锁
        redisTemplate.delete(lockKey);
    }

    return "下单成功！";
}
```

看起来很完美对吧？其实这玩意儿埋了好几个大坑，咱一个个盘。

---

### 这锁有啥毛病？一死死一窝的那种

**坑一：没设过期时间，锁可能永远不释放**

假设你拿到锁之后，业务代码抛了个异常，`finally` 块没执行到……或者服务器直接宕机了。那这把锁就**永久留在 Redis 里了**，所有人都在外面排队，谁也别想进去。

你可能会说："我加个过期时间不就行了？"

好，那咱加一个：

```java
// 设置锁，并给它一个 10 秒的过期时间
Boolean gotLock = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
```

这样就算程序崩了，10 秒后 Redis 自动把锁删了，不会一直卡死。

**坑二：过期时间设短了，业务没跑完锁就没了**

但新问题又来了——你的业务逻辑要是超过 10 秒怎么办？

比如你设了 10 秒过期，结果查库存花了 2 秒，扣库存花了 3 秒，创建订单花了 6 秒（第三方接口慢），总共 11 秒。那最后 1 秒，你的锁其实已经被 Redis 自动删掉了，别人的请求这时候已经拿到了锁，然后你俩就在那儿同时操作同一条数据……

**这就是"锁过期导致并发"的问题**，超级恶心。

你可能会说："那我过期时间设长一点嘛，设个 30 秒！"

但问题是——业务执行时间是不确定的，有时候快有时候慢。设长了万一崩了要等 30 秒才自动释放，这个等待时间就太长了，用户体验不好。设短了又怕没跑完就过期。

**坑三：把别人的锁给删了**

再来一个经典 BUG：线程 A 获取了锁，设了 10 秒过期。但是业务跑得慢，15 秒才跑完。10 秒的时候锁就自动过期消失了，线程 B 立刻拿到了锁。然后线程 A 在 15 秒跑完了，执行 `redisTemplate.delete(lockKey)`——

**它把线程 B 的锁给删了！**

线程 B 还一脸懵逼："我刚拿到锁，怎么就没了？？？"

这时候线程 C 又拿到了锁，线程 B 和 C 又开始打架了……

{{< svg "lock-watchdog" >}}

**怎么解决？** 给锁的值设一个唯一标识（比如 UUID），删除之前检查一下是不是自己的锁：

```java
String lockKey = "lock:order:" + productId;
String lockValue = UUID.randomUUID().toString(); // 每个线程一个唯一ID

// 加锁，value 设成自己的 UUID
Boolean gotLock = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, lockValue, 10, TimeUnit.SECONDS);

if (Boolean.FALSE.equals(gotLock)) {
    return "有人在抢，等会儿再试~";
}

try {
    orderService.doCreateOrder(userId, productId);
} finally {
    // 判断是不是自己的锁，是才删除
    String currentValue = redisTemplate.opsForValue().get(lockKey);
    if (lockValue.equals(currentValue)) {
        redisTemplate.delete(lockKey);
    }
}
```

嘶……看起来好像没问题了？别急，这个判断和删除是**两步操作**，中间还是有个时间窗口。判断完之后、删除之前，锁刚好过期了，另一个线程拿到了锁——你又把别人的锁给删了。虽然概率很低，但在高并发下是可能发生的。

要彻底解决删除原子性的问题，得祭出 Lua 脚本了：

```java
// Lua 脚本保证判断+删除是原子操作
String luaScript =
    "if redis.call('get', KEYS[1]) == ARGV[1] then " +
    "    return redis.call('del', KEYS[1]) " +
    "else " +
    "    return 0 " +
    "end";

redisTemplate.execute(
    new DefaultRedisScript<>(luaScript, Long.class),
    Collections.singletonList(lockKey),
    lockValue
);
```

Lua 脚本在 Redis 里是原子执行的，中间不会被打断，彻底解决了删错锁的问题。

---

## 锁续期问题：Redisson 来救场

上面吭哧吭哧写了那么多代码，其实只是实现了一个**还凑合的分布式锁**。有三个核心问题手工解决起来很麻烦：

1. **锁过期时间不好定**：设长了怕死锁，设短了怕没跑完
2. **删锁需要 Lua 脚本保证原子性**：每次都要写 Lua 脚本有点烦
3. **锁续期（watchdog）**：业务没跑完的时候需要自动续期

好在有大佬们帮咱造好轮子了——**Redisson**，一个 Redis 的 Java 客户端，把分布式锁的各种细节都封装好了，用起来贼舒服。

### Redisson 的看门狗机制

Redisson 最骚的操作就是**看门狗（Watchdog）机制**。它是干啥的呢？

默认情况下，Redisson 给你的锁设一个 30 秒的过期时间，然后每隔 10 秒（内部看门狗的检查间隔）检查一下——"嘿，你还在用这把锁吗？还在用？那我帮你续到 30 秒！"

**这样锁就不会因为业务没跑完而过期了。** 同时，如果程序真的崩了，看门狗线程也没了，锁 30 秒后自动失效，不会死锁。


来看看代码有多简单：

```java
// 1. 引入依赖
// <dependency>
//     <groupId>org.redisson</groupId>
//     <artifactId>redisson-spring-boot-starter</artifactId>
//     <version>3.24.3</version>
// </dependency>

// 2. 配置 RedissonClient（Spring Boot 自动配置之后直接注入就行）
@Autowired
private RedissonClient redissonClient;

public String placeOrder(Long userId, Long productId) {
    String lockKey = "lock:order:" + productId;
    RLock lock = redissonClient.getLock(lockKey);

    try {
        // 尝试加锁，最多等 10 秒，锁 30 秒后自动过期（看门狗会自动续期）
        boolean gotLock = lock.tryLock(10, 30, TimeUnit.SECONDS);

        if (!gotLock) {
            return "抢购太火爆了，等会儿再试~";
        }

        // 执行业务逻辑，不用怕锁过期，看门狗帮你续着
        orderService.doCreateOrder(userId, productId);

    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
        return "系统繁忙~";
    } finally {
        // 释放锁（Redisson 内部用 Lua 脚本保证原子性删锁）
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }

    return "下单成功！";
}
```

就这么几行代码，之前那些坑全帮你填完了：
- **自动续期**：不用纠结过期时间设多少
- **原子删锁**：内部 Lua 脚本保证
- **可重入**：同一个线程可以多次获取同一把锁（底层用 hash 记录重入次数）
- **自动释放**：程序崩了看门狗没了，锁最多 30 秒就自动释放

说实话，看到 Redisson 的源码的时候我都快哭了，之前手写的那些 Lua 脚本在它面前就是弟中弟 (´；ω；`)

**需要注意的是**，如果你给 `tryLock` 指定了 `leaseTime`（过期时间），那看门狗就不生效了，Redis 会在指定时间后直接把锁过期。所以如果你想用看门狗自动续期，就别传 `leaseTime` 参数，或者用 `lock.lock()` 不带参的版本。

```java
// 看门狗生效：不指定过期时间，看门狗默认 30 秒续一次
lock.lock();

// 看门狗不生效：指定了 20 秒过期，到点就释放
lock.lock(20, TimeUnit.SECONDS);
```

---

## Redisson 分布式锁的底层原理

有些朋友可能好奇 Redisson 到底是怎么实现这些骚操作的，咱稍微扒一扒。

### 锁的数据结构

Redisson 的锁在 Redis 里其实是一个 **Hash** 结构，不是简单的 String：

```
Key: lock:order:1001
Hash:
  field: "线程ID:连接ID"  →  value: 重入次数（1 表示第一次获取）
```

为什么用 Hash？因为要支持**可重入**。同一个线程多次 `lock()` 的时候，重入次数就 +1，`unlock()` 的时候 -1，减到 0 才真正释放锁。

### 加锁的 Lua 脚本

Redisson 加锁的时候执行的 Lua 脚本核心逻辑是这样的：

```lua
-- KEYS[1]: 锁的 key
-- ARGV[1]: 锁的过期时间（默认30秒）
-- ARGV[2]: Hash 的 field（线程ID:连接ID）

-- 如果锁不存在，或者已经是自己持有的，就加锁/重入
if (redis.call('exists', KEYS[1]) == 0) or
   (redis.call('hexists', KEYS[1], ARGV[2]) == 1) then
    redis.call('hincrby', KEYS[1], ARGV[2], 1);
    redis.call('pexpire', KEYS[1], ARGV[1]);
    return nil;  -- 加锁成功
end

-- 锁被别人拿着，返回剩余过期时间
return redis.call('pttl', KEYS[1]);
```

看门狗续期的 Lua 脚本就简单了：

```lua
-- 检查锁是不是还在自己手里，在的话就续期
if (redis.call('hexists', KEYS[1], ARGV[2]) == 1) then
    redis.call('pexpire', KEYS[1], ARGV[1]);
    return 1;
end
return 0;
```

### 看门狗的 Java 实现

看门狗本质上是 Redisson 内部的一个**定时任务调度器**。拿到锁之后，它会注册一个定时任务，每隔 10 秒（`internalLockLeaseTime / 3`，即 30/3=10 秒）执行一次续期 Lua 脚本。`unlock()` 的时候取消这个定时任务。

```java
// Redisson 源码简化版（大概长这样）
private void renewExpiration() {
    // 看门狗续期任务
    Timeout task = commandExecutor.getConnectionManager()
        .newTimeout(timeout -> {
            // 执行续期 Lua 脚本
            Long result = evalWriteAsync(key, ...);
            if (result == 1) {
                // 续期成功，10 秒后再来一次
                renewExpiration();
            }
            // result != 1 说明锁已经没了，不用续了
        }, internalLockLeaseTime / 3, TimeUnit.MILLISECONDS);
}
```

是不是感觉没那么神秘了？说白了就是用定时任务 + Lua 脚本反复续命而已。不过能把细节做得这么完善，还是值得给 Redisson 大佬们鼓个掌的 (。・ω・。)ノ

---

## 多节点 Redis 的锁：RedLock 是个啥？

上面的方案在**单机 Redis** 下工作得很好。但如果 Redis 是主从架构呢？

想象一下：你在 Redis 主节点上拿到了一把锁，还没同步到从节点，主节点突然挂了！哨兵把从节点升级为新主节点——但新主节点上**没有你的锁记录**。这时候另一个请求就能在新主节点上拿到同一把锁……分布式锁失效了。


**RedLock（红锁）** 就是为这种场景设计的。它的思想是：**不在单个 Redis 节点上加锁，而是向多个独立的 Redis 节点（通常是 5 个）同时加锁，半数以上加锁成功才算拿到锁。**

Redisson 也封装了 RedLock：

```java
// 创建多个独立的 Redis 连接
RLock lock1 = redissonClient1.getLock("lock:order:1001");
RLock lock2 = redissonClient2.getLock("lock:order:1001");
RLock lock3 = redissonClient3.getLock("lock:order:1001");
RLock lock4 = redissonClient4.getLock("lock:order:1001");
RLock lock5 = redissonClient5.getLock("lock:order:1001");

// 组装成红锁
RedissonRedLock redLock = new RedissonRedLock(lock1, lock2, lock3, lock4, lock5);

try {
    // 尝试加锁，最多等 10 秒，锁 30 秒过期
    boolean gotLock = redLock.tryLock(10, 30, TimeUnit.SECONDS);

    if (!gotLock) {
        return "锁没拿到，先溜了~";
    }

    // 业务逻辑
    orderService.doCreateOrder(userId, productId);

} finally {
    redLock.unlock();
}
```

**不过要提醒一下**：RedLock 这个东西在业界争议不小。Redis 的作者 Antirez 推荐用它，但分布式系统大佬 Martin Kleppmann 觉得这玩意儿不靠谱。争论的点在于——RedLock 依赖时钟同步，如果某个 Redis 节点的时钟跳变了，锁就可能出问题。

**咱的实用建议**：大部分业务场景用单机 Redis + 主从做高可用就够够的了。除非你的业务对一致性的要求高得离谱（比如金融交易），而且还不想用 ZooKeeper 那种重量级方案——那可以考虑 RedLock。但说实话，大多数项目根本不需要纠结到这个程度，单节点 Redisson 锁已经能覆盖 99% 的场景了。

---

## 还有别的选择吗？简单对比一下

Redis 不是分布式锁的唯一选择，咱快速看看还有啥：

| 方案 | 优点 | 缺点 | 适合场景 |
|------|------|------|----------|
| **Redis（Redisson）** | 性能高、部署简单、社区活跃 | 极端情况可能丢锁 | 99% 的业务场景 |
| **ZooKeeper** | 强一致性、天然支持临时节点 | 性能不如 Redis、运维重 | 对一致性要求极高的场景 |
| **数据库乐观锁** | 不需要额外组件 | 性能差、不适合高并发 | 并发量小的老系统 |

ZooKeeper 实现分布式锁的思路和 Redis 不太一样。ZK 利用的是**临时顺序节点**：

1. 所有请求在 ZK 的某个路径下创建一个**临时顺序节点**
2. 序号最小的节点获得锁
3. 拿不到锁的请求，**监听前一个节点的删除事件**
4. 前一个节点释放锁（删除节点），下一个节点收到通知，获得锁

这种机制的好处是：**不需要轮询，没有惊群效应，而且客户端断开连接后临时节点自动删除（天然防死锁）。**

```java
// ZK 分布式锁的大概思路（伪代码）
String lockPath = "/locks/order-lock";

// 创建临时顺序节点
String myNode = zk.create(lockPath + "/lock-",
    data, ZooDefs.Ids.OPEN_ACL_UNSAFE,
    CreateMode.EPHEMERAL_SEQUENTIAL);

// 获取所有子节点
List<String> children = zk.getChildren(lockPath, false);
Collections.sort(children);

// 是不是最小的？
if (myNode.equals(lockPath + "/" + children.get(0))) {
    // 最小就是我，拿到锁！
} else {
    // 我不是最小，监听排在我前面的那个节点
    String prevNode = ...; // 找到前一个节点
    zk.exists(prevNode, watcher); // 等前一个节点删了通知我
}
```

看起来比 Redisson 复杂不少吧？所以一般情况还是推荐 Redis，省心。

---

## 实战中的踩坑记录

说了这么多理论，来点实战中亲（踩）身（过）经（的）历（坑）：

**1. 锁的粒度别搞太粗**

```java
// 错误做法：所有下单请求都用同一把锁
String lockKey = "lock:order";  // 所有用户抢同一把锁！

// 正确做法：按商品 ID 加锁
String lockKey = "lock:order:" + productId;  // 不同商品用不同锁
```

锁粒度太粗的话，用户 A 买手机和用户 B 买电脑都会互相阻塞，完全没有必要。锁的粒度要尽量细，只锁住真正需要互斥的资源。

**2. 不要直接在 Controller 层加锁**

```java
// 不推荐：Controller 层加锁，锁范围太大
@PostMapping("/order")
public Result order(@RequestBody OrderDTO dto) {
    lock.lock();
    try {
        // 参数校验、业务逻辑、调第三方接口全在锁里...
        return orderService.createOrder(dto);
    } finally {
        lock.unlock();
    }
}
```

锁的范围要尽量小，**锁外的事情锁外做**。参数校验、数据转换这些操作不用锁。锁只保护真正需要互斥的那一小段代码，比如查库存 + 扣库存。

**3. 锁要设等待超时，别傻等**

```java
// 不推荐：一直等到死
lock.lock();  // 拿不到锁就永远阻塞

// 推荐：设个等待超时
boolean gotLock = lock.tryLock(3, 30, TimeUnit.SECONDS);
if (!gotLock) {
    // 友好地告诉用户，别让用户傻等
    return Result.fail("抢购人数过多，请稍后重试");
}
```

用户等个 3 秒已经不耐烦了，你再让他等 30 秒他直接关 APP 走人了。**设个合理的等待超时，拿不到就快速失败。**

**4. 小心锁的 key 冲突**

不同业务模块如果用了一样的锁 key，会导致互相之间莫名其妙地阻塞。建议锁 key 加上业务前缀：

```java
// 不同业务用不同前缀，泾渭分明
String orderLockKey = "lock:order:" + orderId;
String paymentLockKey = "lock:payment:" + orderId;
String stockLockKey = "lock:stock:" + productId;
```

---

## 面试常见追问：你能扛住吗？

这一趴是专门为面试准备的，看完前面内容再加上这几个问答，分布式锁这块基本就圆满了 (。-`ω´-)✧

**Q1：Redisson 的看门狗具体是怎么工作的？**

A：加锁的时候不指定过期时间，Redisson 默认给你设 30 秒，然后启动一个后台定时任务，每隔 10 秒（internalLockLeaseTime/3）检查锁是否还被当前线程持有，如果是就续期到 30 秒。`unlock()` 时取消定时任务。如果程序崩了，看门狗线程也没了，锁最多 30 秒自动过期。

**Q2：可重入是怎么实现的？**

A：Redisson 的锁在 Redis 里是个 Hash，field 是客户端 ID+线程 ID，value 是重入次数。同一个线程每次 `lock()` 就 `hincrby` 一次（+1），`unlock()` 就 -1，减到 0 才真正删 key。

**Q3：Redis 分布式锁能保证绝对安全吗？**

A：不能。在主从切换、网络分区等极端情况下可能丢锁。如果要求绝对安全，得上 ZooKeeper 或者 etcd 这类强一致性的方案。但大多数业务场景下 Redisson 够用了。

**Q4：锁超时了怎么办，有哪些处理方式？**

A：要么用看门狗续期（推荐），要么设一个足够大的过期时间（但要注意宕机后锁会长时间不释放），要么把业务做成幂等的——即便没锁住，重复执行也不会出问题（治本之策）。

---

## 收尾总结

今天我们从一个简陋的 `SETNX` 开始，一路升级到 Redisson 全家桶 + RedLock，把 Redis 分布式锁的进化历程捋了一遍。核心要点记住这几个就行：

1. **单机锁管不了分布式环境**，必须用中间件来协调
2. **手写分布式锁坑太多**：过期时间、删错锁、原子性、续期……没点功力真兜不住
3. **Redisson 是版本答案**：看门狗续期 + 可重入 + Lua 原子操作，开箱即用
4. **RedLock 存在争议**，大多数场景不需要
5. **锁粒度要细、范围要小、超时要设**

锁这种东西就像程序里的安全气囊，平时你可能感觉不到它的存在，但关键时刻它能救你一条命。希望这篇文章能帮你在需要用分布式锁的时候不用再从头造轮子了，直接上 Redisson，梭哈就完事了！

以上是个人的一些理解和踩坑经验，希望能帮到正在研究分布式锁的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起进步嘛 (๑•̀ㅂ•́)و✧

**本文完结撒花！！！** 🎉

---

*小贴士：Redisson 除了分布式锁之外，还提供了布隆过滤器、限流器、分布式集合等一系列实用的功能。如果你项目里已经用了它，不妨看看文档挖掘一下其他功能，一个客户端解决一堆分布式场景的问题，血赚~*
