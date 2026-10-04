---
title: "面试官问我缓存击穿是啥，我反手就是一个比喻把他整笑了"
date: 2026-05-29
draft: false
categories: ["中间件"]
tags: ["缓存击穿", "Redis", "缓存", "高并发"]
summary: "嗨朋友们！不知道你们有没有遇到过这种场景——系统平时跑得好好的，突然某个热门数据缓存过期了，一瞬间海量请求直接砸到数据库上，然后数据库就...挂了 (￣▽￣…"
ShowToc: true
---


嗨朋友们！不知道你们有没有遇到过这种场景——系统平时跑得好好的，突然某个热门数据缓存过期了，一瞬间海量请求直接砸到数据库上，然后数据库就...挂了 (￣▽￣)~*

然后你一脸懵逼地看着报警短信疯狂弹出，心里只有一个念头：**我明明加了缓存的啊，怎么还能崩？**

别慌，今天咱就来好好唠唠缓存击穿这档子事。不止是击穿，什么"穿透"、"雪崩"，这些面试八股文里的常客，咱一次性给它整明白。看完之后保证你也能在面试的时候反手一个比喻把面试官逗乐！

---

## 咱先唠唠，啥是缓存？

在开整之前，先给新手朋友快速科普一下缓存是个啥玩意儿。

打个比方：你是一个小卖部老板（数据库），每天要应付几百个客人来买东西。但你一个人忙不过来啊，于是你雇了一个**收银员小妹**（缓存）站在你前面。

客人来了先问收银员小妹："还有可乐没？"
- 小妹一看手里有，直接给了客人，不用来烦你 → **缓存命中**
- 小妹一看手里没有，跑来问你："老板，可乐还有没？"你告诉她有/没有，她记下来再告诉客人 → **缓存未命中 + 回源查询**

有了收银员小妹之后，你大部分时间都在摸鱼（数据库压力小），爽不爽？

**但问题来了**——收银员小妹也不是万能的，她手里的信息会过期（缓存过期时间 TTL），一旦过期了就得重新来问你。这个过期的时间点，就可能出各种幺蛾子。

---

## 缓存三大坑，一个一个盘

### 缓存击穿——最经典的"热key过期"事故

**啥是缓存击穿？**

想象一下，你的小卖部有个爆款商品——**限定版奥特曼卡片**，每天有一百个小朋友来问。收银员小妹一直记着"有货有货"，直接回答就行，根本不用惊动你。

突然有一天，小妹手里的记录过期了！她把"奥特曼卡片有没有"这条信息给忘了！

这时候**一百个小朋友同时冲进来问**："奥特曼卡片还有没有？？？" 小妹慌了，只能挨个跑来问你。你一个老板同时被一百个人问同一个问题，当场就累趴了（数据库宕机）。

**这就是缓存击穿**：某个**热点 key** 在过期的一瞬间，大量并发请求同时打到数据库上，直接给数据库干崩。

{{< svg "cache-breakdown" >}}

**专业一点说**：缓存击穿是指某个热点 key（被超高并发访问的缓存数据）在过期的瞬间，大量请求因为缓存中没有数据，直接穿透缓存层打到数据库，导致数据库瞬时压力过大甚至宕机。

#### 解决方案一：加互斥锁（最常用）

思路很简单：**只有一个小朋友能进去问老板，其他人都在外面等着**。

```java
public String getData(String key) {
    // 先查缓存
    String value = redis.get(key);
    if (value != null) {
        return value;
    }

    // 缓存没命中，加锁，只让一个线程去查数据库
    String lockKey = "lock:" + key;
    try {
        // setIfAbsent = SETNX，抢到锁的才能去查数据库
        boolean gotLock = redis.setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
        
        if (gotLock) {
            // 抢到锁了，去查数据库
            value = database.query(key);
            // 把结果写回缓存，设置过期时间
            redis.set(key, value, 30, TimeUnit.MINUTES);
            return value;
        } else {
            // 没抢到锁，睡一小会儿，然后重试（此时缓存大概率已经有了）
            Thread.sleep(100);
            return getData(key); // 递归重试
        }
    } finally {
        // 记得释放锁
        redis.delete(lockKey);
    }
}
```

**优点**：实现简单，保证只有一个线程去查库，其他线程等着  
**缺点**：抢到锁的那个线程要等它查完库才能释放锁，如果查库慢，其他线程也得跟着等

#### 解决方案二：逻辑过期（永不过期 + 异步更新）

思路更骚：**缓存根本不设过期时间，由后台线程偷偷更新数据**。

```java
public class CacheData {
    private Object data;       // 实际数据
    private Long expireTime;   // 逻辑过期时间戳
}

public String getData(String key) {
    CacheData cacheData = redis.get(key);
    
    // 缓存压根不存在（第一次查）
    if (cacheData == null) {
        String lockKey = "lock:" + key;
        if (redis.setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS)) {
            cacheData = database.query(key);
            redis.set(key, cacheData); // 设置逻辑过期时间为30分钟后
            return cacheData.getData();
        }
    }
    
    // 缓存存在，检查逻辑过期了没
    if (cacheData.getExpireTime() > System.currentTimeMillis()) {
        // 没过期，直接返回
        return cacheData.getData();
    }
    
    // 逻辑过期了，异步更新
    String lockKey = "lock:" + key;
    if (redis.setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS)) {
        // 开个新线程去更新缓存，当前请求先用旧数据兜底
        threadPool.execute(() -> {
            CacheData newData = database.query(key);
            newData.setExpireTime(System.currentTimeMillis() + 30 * 60 * 1000);
            redis.set(key, newData);
            redis.delete(lockKey);
        });
    }
    
    // 直接返回旧数据，管它过没过期，总比没数据强
    return cacheData.getData();
}
```

**优点**：用户永远不会因为缓存过期而等待，体验好  
**缺点**：实现复杂，需要维护逻辑过期时间戳，还得开线程池

#### 解决方案三：缓存预热 + 过期时间打散

有些热点数据（比如首页的热门商品），咱们可以在项目启动的时候就**提前加载到缓存里**，这叫缓存预热。

另外，如果一堆 key 同时过期也很危险（这就涉及到下面要讲的"雪崩"了），所以过期时间得**加个随机偏移量**：

```java
// 不要把过期时间设成一模一样的！
// 错误做法：
redis.set("hot_data_1", value, 30, TimeUnit.MINUTES);
redis.set("hot_data_2", value, 30, TimeUnit.MINUTES);
redis.set("hot_data_3", value, 30, TimeUnit.MINUTES);

// 正确做法：每个 key 的过期时间加个随机尾巴
int baseExpire = 30; // 基础过期 30 分钟
int randomExtra = ThreadLocalRandom.current().nextInt(0, 10); // 随机 0~10 分钟
redis.set("hot_data_1", value, baseExpire + randomExtra, TimeUnit.MINUTES);
redis.set("hot_data_2", value, baseExpire + randomExtra, TimeUnit.MINUTES);
redis.set("hot_data_3", value, baseExpire + randomExtra, TimeUnit.MINUTES);
```

**这就好比**：不要把三个闹钟都定在同一分钟响，你定7:00、7:03、7:07，这样早上起来不至于被三个闹钟一起轰炸 (。-ω-)zzz

---

### 缓存穿透——来了一万个不存在的key

**啥是缓存穿透？**

接着用小卖部的例子。有一群**捣蛋鬼**，不买东西，专门问一些不存在的东西："老板，有灭霸手套吗？""老板，有孙悟空的金箍棒吗？""老板，有无穷无尽的数学公式吗？"

收银员小妹每次都跑来问你，你每次都回答"没有"。时间长了你也烦死了对吧？关键是这些捣蛋鬼也是你的客户，你不能不理他们。

更可怕的是——**这些"不存在"的东西根本不会进缓存**（缓存里存的是"没有"还叫啥缓存），所以每次都会直接打到数据库上。

**这就是缓存穿透**：用户大量请求缓存和数据库中**都不存在的数据**，每次请求都直接打到数据库，相当于缓存形同虚设。

{{< svg "cache-penetration" >}}

#### 解决方案一：布隆过滤器

布隆过滤器是个啥呢？它就是一个**提前判断"这东西肯定不存在"的筛子**。

好比你在小卖部门口贴了一张**商品清单**（布隆过滤器），上面列了所有你卖过的东西。有人来问，小妹先看清单：
- 清单上有 → 可能是真有，也可能是误判（布隆过滤器会有小概率误判），再去问老板确认
- 清单上没有 → **100%确定没有**，直接说"没有"，不用打扰老板

```java
// 引入 Redisson 的布隆过滤器（也可以手写，但建议用现成的）
RBloomFilter<String> bloomFilter = redisson.getBloomFilter("productBloom");

// 初始化布隆过滤器：预计10万条数据，误判率0.01（1%）
bloomFilter.tryInit(100000L, 0.01);

// 缓存预热时把所有商品ID塞进去
for (Product product : allProducts) {
    bloomFilter.add(product.getId());
}

// 查询时先过布隆过滤器
public Product getProduct(String productId) {
    // 布隆过滤器说没有，直接返回 null，不用查缓存也不用查库
    if (!bloomFilter.contains(productId)) {
        return null;
    }
    
    // 布隆过滤器说可能有，正常走缓存查库流程
    Product product = redis.get(productId);
    if (product != null) {
        return product;
    }
    return database.query(productId);
}
```

**优点**：内存占用极小（几MB能存几千万条数据），判断速度快得飞起  
**缺点**：有极小概率误判（说"有"其实是"没有"），但不能删除元素（删不掉）

#### 解决方案二：缓存空值

更简单的办法：**即使查不到，也把"没有"这个结果记下来**。

```java
public String getData(String key) {
    String value = redis.get(key);
    
    if (value != null) {
        // 判断是不是空值标记
        if ("NULL_VALUE".equals(value)) {
            return null; // 就是没数据，直接返回
        }
        return value;
    }
    
    // 查数据库
    String dbValue = database.query(key);
    
    if (dbValue == null) {
        // 数据库也没有，缓存一个空值标记，过期时间短一点
        redis.set(key, "NULL_VALUE", 5, TimeUnit.MINUTES);
        return null;
    }
    
    // 有数据，正常缓存
    redis.set(key, dbValue, 30, TimeUnit.MINUTES);
    return dbValue;
}
```

**注意**：空值的过期时间要设短一些（比如5分钟），防止万一数据库突然有数据了，缓存还说是空的。

**优点**：实现简单，一行代码的事儿  
**缺点**：如果攻击者用海量不同ID轰炸（比如随机生成不存在的用户ID），缓存里会塞满空值垃圾，浪费内存

#### 解决方案三：接口层做参数校验

在请求还没进业务逻辑之前，先拦一道：

```java
// 给 ID 加个基础校验，明显非法的直接打回去
@GetMapping("/product/{id}")
public Result getProduct(@PathVariable String id) {
    // ID长度不对直接返回
    if (id.length() < 5 || id.length() > 20) {
        return Result.fail("参数非法");
    }
    // ID格式不符合规范直接返回
    if (!id.matches("^[A-Za-z0-9]+$")) {
        return Result.fail("参数非法");
    }
    // 正常走业务逻辑
    return Result.ok(productService.getById(id));
}
```

**这层校验配合缓存空值一起用**，基本能挡住 90% 的穿透攻击。

---

### 缓存雪崩——集体过期的灾难

**啥是缓存雪崩？**

回到小卖部。这次不是你**一个**商品记录过期了，而是**所有商品的记录都在同一时刻过期了**！

收银员小妹瞬间失忆："可乐有没有来着？奥利奥还有几包来着？农夫山泉还卖不卖来着？"

然后几百个客人就看着小妹疯狂往你办公室跑，你办公室门口排起了长队，整个小卖部直接瘫痪。

**这就是缓存雪崩**：大量缓存 key **在同一时间集中过期**，或者缓存服务器**直接宕机**，导致海量请求打到数据库，引发系统级崩溃。

{{< svg "cache-avalanche" >}}

#### 解决方案一：过期时间加随机值（治标）

```java
// 批量设置缓存时，不要用同一个过期时间
int baseExpireMin = 60; // 基础1小时
Random random = new Random();

for (Product product : products) {
    // 过期时间 = 基础时间 + 随机0~20分钟
    int randomExtra = random.nextInt(20);
    redis.set(product.getId(), product, baseExpireMin + randomExtra, TimeUnit.MINUTES);
}
```

这样即使一起设置的缓存，过期时间也被打散了，不会同时失效。

#### 解决方案二：缓存高可用 + 多级缓存（治本）

单机 Redis 挂了整个缓存层就没了？那咱就搞个**集群**嘛！

- **Redis 主从 + 哨兵**：主节点挂了，从节点自动顶上
- **Redis Cluster**：数据分片，一个节点挂了不影响其他节点
- **本地缓存兜底**：Redis 全挂了，咱还有 JVM 本地缓存（Caffeine、Guava Cache）顶一会儿

```java
// 多级缓存思路：先查本地缓存，再查Redis，最后查数据库
public String getDataWithMultiCache(String key) {
    // 第一级：本地缓存（Caffeine，内存级，最快）
    String value = caffeineCache.getIfPresent(key);
    if (value != null) {
        return value;
    }
    
    // 第二级：Redis（分布式缓存）
    value = redis.get(key);
    if (value != null) {
        // 回填本地缓存
        caffeineCache.put(key, value);
        return value;
    }
    
    // 第三级：数据库
    value = database.query(key);
    if (value != null) {
        redis.set(key, value, 30, TimeUnit.MINUTES);
        caffeineCache.put(key, value);
    }
    return value;
}
```

#### 解决方案三：限流 + 熔断降级（最后一道防线）

就算缓存全挂了，数据库也不能被打死。加个**限流和熔断**，保命用的：

```java
// 使用 Sentinel 或者 Resilience4j 做熔断降级
@SentinelResource(value = "getProduct", fallback = "getProductFallback")
public Product getProduct(String id) {
    // 正常查缓存 -> 查数据库的逻辑
}

// 降级方法：数据库扛不住的时候返回兜底数据
public Product getProductFallback(String id, Throwable t) {
    log.warn("数据库扛不住了，返回兜底数据！key={}", id);
    // 返回一个默认对象或者从本地缓存取
    return Product.builder()
        .id(id)
        .name("商品加载中...")
        .price(new BigDecimal("0"))
        .build();
}
```

**这就好比**：小卖部门口排队的人太多了，保安直接拉警戒线："一次只能进来5个人！"，虽然慢了点，但小卖部至少不会塌。

---

## 一张表帮你看清三大坑的区别

很多朋友容易把这三个概念搞混，咱来一张表给它们整得明明白白：

| 维度 | 缓存击穿 | 缓存穿透 | 缓存雪崩 |
|------|---------|---------|---------|
| **触发条件** | 单个热点key过期 | 查询不存在的数据 | 大量key同时过期 或 Redis宕机 |
| **缓存状态** | key有，但刚过期 | 根本没有这个key | 一堆key同时过期 |
| **数据库压力** | 针对某一条数据的高并发 | 大量不存在的key打到DB | 全线崩溃式压力 |
| **比喻** | 一百个人抢一张奥特曼卡片 | 来一万个问灭霸手套的 | 所有商品记录同时失忆 |
| **核心解法** | 互斥锁 / 逻辑过期 | 布隆过滤器 / 缓存空值 | 过期时间打散 / 高可用集群 |

---

## 实战建议：项目中到底怎么整？

讲了一堆理论，咱来点实际的。在你的项目里，不需要把所有方案都堆上去，那是过度设计。根据场景选组合：

**中小项目（QPS < 1000）**：
- 缓存空值（防穿透）+ 互斥锁（防击穿）+ 过期时间加随机（防雪崩）
- 三件套齐活，简单够用

**高并发项目（QPS 5000+）**：
- 布隆过滤器（防穿透）+ 逻辑过期（防击穿）+ Redis Cluster + 本地缓存（防雪崩）+ 限流熔断兜底
- 多级防护，层层兜底

**没必要一上来就上布隆过滤器**，如果你的项目就几千用户，缓存空值够用了。等技术债堆上去了再慢慢优化嘛 (｡･ω･｡)

---

## 补充几个踩过的坑

1. **互斥锁一定要设超时时间**：`setIfAbsent` 的时候不设超时，万一拿到锁的线程挂了，整个系统一起陪葬。**设个 5~10 秒的超时，死了也能自动释放。**

2. **双重检查别忘了**：拿到锁之后别忘了**再查一次缓存**，因为可能在你等锁的时候，前面那个线程已经把数据写进缓存了。

3. **空值过期别设太久**：给不存在的 key 设空值标记的时候，过期时间设短点（2~5 分钟），否则数据新增了你缓存还说是 null。

4. **布隆过滤器要预热**：项目启动后别等流量进来再慢慢填充，**启动的时候就把数据库所有已有数据塞进布隆过滤器里**，不然刚开始就会漏数据。

5. **单体 Redis 别裸奔**：生产环境至少搞个**主从 + 哨兵**，自动故障转移。别问我怎么知道的，半夜爬起来修 Redis 的滋味不想再尝第二遍 (￣▽￣*)ゞ

---

## 收尾总结

缓存这东西吧，用好了是神兵利器，用不好就是定时炸弹。今天咱唠的这三个问题——**击穿、穿透、雪崩**，本质上都是"缓存和数据库之间的数据不一致导致请求打到了不该打的地方"。

记住核心思路就行：
- **击穿** → 只让一个人去查库，其他人排队等
- **穿透** → 查不到也记下来，或者直接筛掉明显不存在的请求
- **雪崩** → 别让它们同时过期，也别让缓存单点故障

掌握这几个武器，面试被问到缓存相关问题的时候，你也能侃侃而谈，顺便还能反手一个比喻把面试官逗笑 (๑•̀ㅂ•́)و✧

以上是个人的一些理解和经验分享，希望能帮到正在学习缓存的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起进步嘛~

本文完结撒花！！！ ✿✿ヽ(°▽°)ノ✿
