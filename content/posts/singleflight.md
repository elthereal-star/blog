---
title: "SingleFlight 到底是个啥玩意儿？为啥它能成为缓存击穿的\"救世主\"？"
date: 2026-06-09
draft: false
categories: ["架构设计"]
tags: ["SingleFlight", "缓存击穿", "并发合并"]
summary: "咱就是说，各位朋友在写后端的时候，有没有遇到过这么一个场景："
ShowToc: true
---


咱就是说，各位朋友在写后端的时候，有没有遇到过这么一个场景：

服务里有个热点数据，每次请求都要去查数据库。平时还好，突然流量一上来——几百上千个请求同时打到数据库，数据库直接**库库的**冒烟告警，运维大佬拎着键盘就冲过来了（bush）。

你说加个缓存不就完了嘛？嘿，加了缓存之后更鬼畜了——缓存刚好过期的那一瞬间，所有请求直接绕过缓存全部砸到数据库上，这就是传说中的**缓存击穿**。

那咋整捏？今天咱就来聊聊一个贼精巧的设计——**SingleFlight**，以及它在分布式场景下的骚操作。用 Java 给你整得明明白白的！

---


{{< svg "singleflight" >}}
## SingleFlight 是个啥？

先给大伙儿一个直觉上的理解：

> 想象一下，你在一家公司上班，老板发了个任务，需要某个数据。好家伙，全组十个人同时跑去找 DBA 查同一张表。DBA 直接裂开。  
> 这时候你站出来说："兄弟们别急，你们都等着，我一个人去查，查完给你们一人复印一份。"
> 
> 这就是 **SingleFlight** —— **同一个"请求"同时只允许一个在执行，其他相同请求等着拿结果就行**。

从专业角度讲，SingleFlight 是一个**请求合并/去重机制**：对于同一个 key 的并发请求，只让第一个请求真正去执行，其他请求阻塞等待，等第一个请求拿到结果后，所有请求共享这个结果。

听着是不是很简单？但里面有几个细节蛮有意思的，咱接着往下聊。

---

## 手搓一个 Java 版 SingleFlight

别光说不练，咱直接上代码整一个。

### 第一步：定义核心数据结构

我们要存啥捏？一个正在进行中的请求，以及它的结果。其他相同 key 的请求来了之后，等着这个结果就行。

```java
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;

/**
 * 单机版 SingleFlight
 * 核心思路：同一个 key 的并发请求，只让第一个去实际执行，其他请求共享结果
 */
public class SingleFlight<T> {

    // 用来存每个 key 对应的"正在执行中的请求"
    private final Map<String, Call<T>> callMap = new ConcurrentHashMap<>();
    private final Object lock = new Object();

    /**
     * 执行一个操作，同一个 key 保证只有一个在执行
     *
     * @param key  请求的唯一标识（比如缓存 key）
     * @param func 真正要执行的逻辑（比如查数据库）
     * @return 执行结果
     */
    public T doCall(String key, ThrowableFunction<T> func) throws Exception {
        // 先看看是不是已经有正在执行的请求了
        Call<T> existingCall = callMap.get(key);
        if (existingCall != null) {
            // 有人已经在执行了，咱等着就行
            return existingCall.await();
        }

        // 没人执行，那咱来当这个"天选之子"
        Call<T> newCall = new Call<>();
        // 用 synchronized 保证 putIfAbsent 的原子性，防止两个请求同时创建 Call
        synchronized (lock) {
            existingCall = callMap.get(key);
            if (existingCall != null) {
                // 双重检查，可能在等锁的时候别人已经创建了
                return existingCall.await();
            }
            callMap.put(key, newCall);
        }

        try {
            // 真正执行业务逻辑
            T result = func.apply();
            newCall.resolve(result);  // 通知所有等待者
            return result;
        } catch (Exception e) {
            newCall.fail(e);  // 失败了也要通知，不然等待的请求会一直卡着
            throw e;
        } finally {
            // 执行完毕，从 map 中移除，别占着坑位
            callMap.remove(key);
        }
    }

    /**
     * 内部类：代表一个"正在执行的请求"
     */
    private static class Call<T> {
        private final CountDownLatch latch = new CountDownLatch(1);
        private T result;
        private Exception exception;

        void resolve(T result) {
            this.result = result;
            latch.countDown();  // 开门！放行所有等待的请求
        }

        void fail(Exception e) {
            this.exception = e;
            latch.countDown();  // 失败了也得开门，不能让人家干等着
        }

        T await() throws Exception {
            latch.await();  // 阻塞，等结果出来
            if (exception != null) {
                throw exception;
            }
            return result;
        }
    }

    /**
     * 函数式接口，允许抛受检异常
     */
    @FunctionalInterface
    public interface ThrowableFunction<T> {
        T apply() throws Exception;
    }
}
```

### 第二步：接入缓存，防止击穿

有了 SingleFlight 之后，缓存击穿的问题就好解决了。咱把查数据库的操作包在 SingleFlight 里就完事：

```java
public class CacheService {

    private final SingleFlight<String> singleFlight = new SingleFlight<>();
    private final Map<String, String> localCache = new ConcurrentHashMap<>();

    /**
     * 获取用户信息，带 SingleFlight 防护
     */
    public String getUserInfo(String userId) throws Exception {
        // 先查缓存
        String cached = localCache.get(userId);
        if (cached != null) {
            return cached;
        }

        // 缓存没命中，走 SingleFlight 查数据库
        // 同一时刻，同一个 userId 只有一个请求会真正去查 DB
        String dbResult = singleFlight.doCall(userId, () -> {
            System.out.println("[" + Thread.currentThread().getName() + "] 缓存没命中，我去查数据库了...");
            Thread.sleep(200); // 模拟数据库查询耗时
            return "用户信息_" + userId + "_来自数据库";
        });

        // 查到后塞回缓存
        localCache.put(userId, dbResult);
        return dbResult;
    }
}
```

### 第三步：写个测试验证一下

```java
public class SingleFlightTest {

    public static void main(String[] args) throws Exception {
        CacheService cacheService = new CacheService();

        // 模拟 20 个线程同时查同一个 userId
        Thread[] threads = new Thread[20];
        for (int i = 0; i < 20; i++) {
            threads[i] = new Thread(() -> {
                try {
                    String result = cacheService.getUserInfo("123");
                    System.out.println(Thread.currentThread().getName() + " 拿到结果: " + result);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }, "线程-" + i);
        }

        // 同时启动！
        for (Thread t : threads) {
            t.start();
        }
        for (Thread t : threads) {
            t.join();
        }

        System.out.println("=================================");
        System.out.println("你瞅瞅上面的日志，只有一条'我去查数据库了'，其他线程都是直接拿结果");
        System.out.println("这就是 SingleFlight 的魅力！");
    }
}
```

运行之后你会发现：**20 个线程同时请求，但数据库只被查了一次**，其他的 19 个线程都乖乖等着拿结果。是不是很爽！

---

## SingleFlight 设计的巧妙之处

好，代码看完了，咱来聊聊这个设计到底妙在哪里。

### 巧妙点一：用 CountDownLatch 做"广播通知"

一个线程执行完，怎么通知所有等待的线程捏？SDK 里刚好有个 `CountDownLatch`，完美匹配这个场景。`countDown()` 一下，所有 `await()` 的线程同时被唤醒，干净利落。

有朋友可能会说："我用 `wait/notifyAll` 不行吗？" 当然可以，但 `CountDownLatch` 的语义更清晰——**一次性的门闩，打开就再也关不上**。这个"一次性"恰好和 SingleFlight 的语义对上：一个请求执行完，结果就定死了。

### 巧妙点二：双重检查 + synchronized，防并发创建

注意看 `doCall` 方法里有个 `synchronized` 块，里面又做了一次检查：

```java
if (existingCall != null) {
    callMap.put(key, newCall);
    // ...
}

synchronized (lock) {
    existingCall = callMap.get(key);  // 二次检查！
    if (existingCall != null) {
        return existingCall.await();
    }
    callMap.put(key, newCall);
}
```

为啥要这样？因为 `ConcurrentHashMap` 的 `get` 和 `put` 不是原子操作。线程 A 和线程 B 可能同时发现 `callMap.get(key)` 为 null，然后两个线程都准备创建新的 `Call`。加了 `synchronized` + 双重检查，就能保证**有且只有一个** `Call` 被创建。

这其实和单例模式里的双重检查锁定是一个思路，只不过这里是保证"同一个 key 只有一个 Call"。

### 巧妙点三：失败也要通知，不能让人家白等

```java
} catch (Exception e) {
    newCall.fail(e);  // 失败了也要 countDown！
    throw e;
}
```

这个比较容易被忽略哈。你想啊，如果第一个请求执行失败了，它不通知等待的那些线程，那些线程不就一直卡在那了吗？所以**无论成功还是失败，都得 `countDown()`**，让等待的线程能拿到异常然后自行处理。

---

## 分布式场景下的 SingleFlight

上面咱写的是单机版的，那在分布式环境下怎么办捏？

假设你有 10 个服务实例，每个实例上都有 100 个请求在查同一个 key。单机版 SingleFlight 只能管住自己机器上的，10 台机器还是会有 10 个请求同时打到数据库。

### 方案一：Redis 实现分布式 SingleFlight

思路很简单：把那个"标记"从内存移到 Redis。利用 Redis 的 `SETNX`（set if not exists）来做分布式锁：

```java
import redis.clients.jedis.Jedis;
import redis.clients.jedis.params.SetParams;

public class DistributedSingleFlight {

    private final Jedis jedis;  // Redis 连接

    public DistributedSingleFlight(Jedis jedis) {
        this.jedis = jedis;
    }

    /**
     * 分布式 SingleFlight
     * 利用 Redis SET NX EX 来实现"谁先抢到谁执行"
     */
    public String doCall(String key, long timeoutSeconds, 
                         ThrowableSupplier<String> func) throws Exception {
        String lockKey = "sf:lock:" + key;
        String resultKey = "sf:result:" + key;

        // 第一步：看看是不是已经有结果了（别的实例可能已经执行完了）
        String cachedResult = jedis.get(resultKey);
        if (cachedResult != null) {
            return cachedResult;
        }

        // 第二步：尝试抢锁，SET key value NX EX timeout
        // NX = 不存在才设置，EX = 设置过期时间
        String lockValue = "locked";
        SetParams params = new SetParams().nx().ex(timeoutSeconds);
        String setResult = jedis.set(lockKey, lockValue, params);

        if ("OK".equals(setResult)) {
            // 抢到锁了！咱来当"天选之子"
            try {
                // 再查一次结果，双重检查（可能在抢锁期间别人已经执行完了）
                cachedResult = jedis.get(resultKey);
                if (cachedResult != null) {
                    return cachedResult;
                }

                // 真正执行
                String result = func.apply();
                // 把结果存 Redis，让其他实例也能拿到
                jedis.setex(resultKey, (int) timeoutSeconds * 2, result);
                return result;
            } finally {
                // 释放锁（用 Lua 脚本保证原子性，防止误删别人的锁）
                String luaScript = 
                    "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "    return redis.call('del', KEYS[1]) " +
                    "else " +
                    "    return 0 " +
                    "end";
                jedis.eval(luaScript, 
                    java.util.Collections.singletonList(lockKey),
                    java.util.Collections.singletonList(lockValue));
            }
        } else {
            // 没抢到锁，别人在查，咱轮询等结果
            return waitForResult(resultKey, timeoutSeconds);
        }
    }

    /**
     * 轮询等待结果
     * 有点憨憨的，但简单好用
     */
    private String waitForResult(String resultKey, long timeoutSeconds) 
            throws InterruptedException {
        long deadline = System.currentTimeMillis() + timeoutSeconds * 1000;
        while (System.currentTimeMillis() < deadline) {
            String result = jedis.get(resultKey);
            if (result != null) {
                return result;
            }
            Thread.sleep(50); // 50ms 轮询一次
        }
        throw new RuntimeException("等待结果超时了捏，要不咱自己查吧？");
    }

    @FunctionalInterface
    public interface ThrowableSupplier<T> {
        T apply() throws Exception;
    }
}
```

### 方案二：用 Redisson 更省事

如果觉得上面手搓 Redis 太麻烦，咱直接上 Redisson，API 更友好：

```java
import org.redisson.api.RLock;
import org.redisson.api.RBucket;
import org.redisson.api.RedissonClient;

public class RedissonSingleFlight {

    private final RedissonClient redisson;

    public RedissonSingleFlight(RedissonClient redisson) {
        this.redisson = redisson;
    }

    public String doCall(String key, ThrowableSupplier<String> func) 
            throws Exception {
        String resultKey = "sf:result:" + key;
        
        // 先看结果缓存
        RBucket<String> bucket = redisson.getBucket(resultKey);
        String cached = bucket.get();
        if (cached != null) {
            return cached;
        }

        // 加分布式锁
        RLock lock = redisson.getLock("sf:lock:" + key);
        lock.lock();
        try {
            // 双重检查
            cached = bucket.get();
            if (cached != null) {
                return cached;
            }
            
            // 执行并缓存结果
            String result = func.apply();
            bucket.set(result, java.time.Duration.ofMinutes(5));
            return result;
        } finally {
            lock.unlock();
        }
    }

    @FunctionalInterface
    public interface ThrowableSupplier<T> {
        T apply() throws Exception;
    }
}
```

**这里有个小坑提醒一下**：Redisson 的 `RLock` 默认是看门狗自动续期的，如果你希望锁能自动过期防止死锁，记得设置 `lock.lock(30, TimeUnit.SECONDS)`。

---

## SingleFlight 的经典应用场景

### 场景一：缓存击穿防护（最常见的用法）

{{< svg "cache-breakdown" >}}

缓存热点 key 刚好过期，大量请求涌入数据库。直接用 SingleFlight 包一层，**同一个 key 只查一次数据库**，完美解决。

前面已经写了代码示例，这里就不重复了。

### 场景二：防止重复提交

用户手抖，一个"下单"按钮点了好几次。用 `订单ID` 作为 SingleFlight 的 key，后端保证同一个订单的创建逻辑只执行一次：

```java
public Order createOrder(String orderId, OrderRequest request) throws Exception {
    return singleFlight.doCall("order:" + orderId, () -> {
        // 检查订单是否已存在
        Order exist = orderMapper.selectById(orderId);
        if (exist != null) {
            return exist;
        }
        // 创建订单
        Order newOrder = doCreateOrder(request);
        orderMapper.insert(newOrder);
        return newOrder;
    });
}
```

### 场景三：批量查询的去重

比如一个页面里有多个组件，都依赖同一个用户信息。每个组件独立发起请求，但到后端这边可以用 SingleFlight 合并掉，减少对下游的调用：

```java
// 组件A调用
getUserInfo("userId-123");  // → SingleFlight 拦下
// 组件B调用
getUserInfo("userId-123");  // → 发现已经在查了，等着
// 组件C调用
getUserInfo("userId-123");  // → 也等着

// 最终用户服务只被调用了一次！
```

### 场景四：防止缓存预热时的惊群效应

系统刚启动，缓存是空的，所有请求都去查数据库做缓存预热。这时候如果没有 SingleFlight，数据库直接被打爆。有了 SingleFlight，同一个 key 的预热只会触发一次数据库查询，其他请求排队等结果就行。

---

## Go 语言里的 SingleFlight 参考

其实 SingleFlight 这个设计最早是 Go 语言官方包 `golang.org/x/sync/singleflight` 带火的。如果你用过 Go，大概见过这段代码：

```go
var g singleflight.Group

func getUserInfo(userId string) (string, error) {
    v, err, _ := g.Do(userId, func() (interface{}, error) {
        return queryFromDB(userId)
    })
    if err != nil {
        return "", err
    }
    return v.(string), nil
}
```

Go 的实现比咱的 Java 版多了一个特性：**Forget 机制**。啥意思捏？就是你可以主动把某个 key 从"进行中"的状态移除，允许下一次请求重新触发执行。在某些场景下（比如某个 key 的请求特别慢，你想允许重试），这个机制挺有用的。

Java 里咱也可以加一个：

```java
public void forget(String key) {
    callMap.remove(key);
}
```

但是要小心，**别在请求还在执行的时候瞎 forget**，不然等待的线程就永远收不到通知了。一般只在超时重试的场景下才用这个。

---

## 注意事项 & 踩坑记录

这几个坑都是咱实战中踩过的，提前告诉你免得你重蹈覆辙：

- **SingleFlight 适合读多写少、幂等的场景**。如果操作不是幂等的（比如扣库存），就别用 SingleFlight 了，用分布式锁更合适。
- **key 的设计要够细粒度**。比如缓存 key 是 `user:123`，SingleFlight 的 key 也应该是 `user:123`，别直接用一个全局的固定字符串，那样会把所有请求都串行化了。
- **注意超时问题**。如果第一个请求执行特别慢（比如数据库连接池满了），其他请求也跟着一起等，可能会拖垮整个系统。建议给 `latch.await()` 加个超时：`latch.await(5, TimeUnit.SECONDS)`。
- **分布式版本要考虑 Redis 挂了的情况**。Redis 要是挂了，咱得有降级策略，比如直接走数据库（虽然压力大但至少服务不挂）。
- **结果缓存要设过期时间**。特别是分布式版本里存在 Redis 的结果，一定要设过期时间，不然永久缓存一个错误的结果就尴尬了。

---

## 总结

SingleFlight 的设计真的是**短小精悍**——代码没几行，但解决了一个很实际的问题。核心思想就是"同一个请求，一个人干，其他人等"，用 `CountDownLatch` 做同步，用 `ConcurrentHashMap` 做状态管理，配上双重检查锁定防止并发问题，整个设计干净利落。

在分布式场景下，借助 Redis 的 `SETNX` 或者 Redisson 的分布式锁，也能把这个思路搬到集群环境下，让跨实例的相同请求也能合并。

当然啦，SingleFlight 不是万能药。它有它的适用场景——读多写少的幂等操作。如果你的场景是扣库存、抢红包这种"只能成功一次"的操作，还是老老实实用分布式锁 + 事务吧。

以上是个人的一些经验分享，如果哪里有错误的地方也请大佬们指出，咱一起交流进步！

本文完结撒花！！！ 🎉

---

**附：文中完整代码可以在本地直接跑，依赖只需要 JDK 8+，单机版不需要任何第三方依赖，分布式版需要引入 Jedis 或 Redisson。**
