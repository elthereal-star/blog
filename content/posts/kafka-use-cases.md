---
title: "Kafka：消息队列界的\"瑞士军刀\"，这些场景你不会还没用过吧？"
date: 2026-06-12
draft: false
categories: ["中间件"]
tags: ["Kafka", "消息队列", "削峰填谷", "异步解耦"]
summary: "咱就是说，现在搞后端开发，谁还没听说过 Kafka 嘞？但很多刚开始接触的朋友，对 Kafka 到底能干啥、该用在哪，其实还是一脸懵的——\"不就是个消息队列…"
ShowToc: true
---


咱就是说，现在搞后端开发，谁还没听说过 Kafka 嘞？但很多刚开始接触的朋友，对 Kafka 到底能干啥、该用在哪，其实还是一脸懵的——"不就是个消息队列嘛，我用 Redis 发个消息不也行？"

嘿嘿，今天咱就来聊聊 Kafka 那些常见的使用场景，从入门到实战，把 Kafka 这张王牌彻底整明白！

---

## 一、异步解耦——让微服务学会"各玩各的"

想象一下这个场景：用户注册后，我们需要做三件事——发短信通知、送新用户优惠券、把数据同步到数据仓库。

如果咱写成一个同步链路：

```
用户注册 → 发短信 → 送优惠券 → 同步数仓 → 返回"注册成功"
```

这用户得等多久嘞？万一发短信的服务挂了，整个注册流程都得跟着炸，这谁能忍啊！

**异步解耦**的思路就很简单粗暴了：注册服务干完自己的活（写入数据库），往 Kafka 丢一条消息就完事了，剩下的爱谁谁。

```java
// 注册服务：干完活直接发消息，潇洒走人
@Service
public class RegisterService {
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void register(User user) {
        // 1. 写入数据库，这个是我的核心职责
        userMapper.insert(user);
        
        // 2. 丢一条消息出去，剩下的我不管了 😎
        kafkaTemplate.send("user-register-topic", JSON.toJSONString(user));
    }
}
```

然后短信服务、优惠券服务、数仓服务各自订阅这个 topic，各玩各的，互不影响：

```java
// 短信服务：我只关心发短信
@KafkaListener(topics = "user-register-topic")
public void sendSMS(String message) {
    User user = JSON.parseObject(message, User.class);
    smsService.send(user.getPhone(), "欢迎注册！");
}

// 优惠券服务：我只关心发券
@KafkaListener(topics = "user-register-topic")
public void sendCoupon(String message) {
    User user = JSON.parseObject(message, User.class);
    couponService.grant(user.getId(), "新人券");
}
```

这样一来，**注册服务根本不需要知道下游有哪些消费者**，下游新增一个消费者也完全不用改动注册服务的代码。这就是"解耦"的魅力——各个服务高内聚低耦合，今天我们想把短信服务换成推送通知，直接换个消费者就行，上游连一行代码都不带改的。

> **小提示**：这里不同的消费者最好用不同的 `groupId`，这样每条消息每个组都能收到。如果用了同一个 groupId，那一条消息只会被组内一个消费者拿到，其他服务就收不到了嗷！

{{< svg "kafka-scenarios" >}}

---

## 二、削峰填谷——别让流量把数据库"冲烂了"

每年的双十一、618，秒杀活动的流量那是相当吓人的。假设咱的数据库每秒能抗 2000 QPS，结果大促的时候瞬间来了 20000 QPS，数据库直接就"去二次元了"（炸了）。

这时候怎么办呢？**不能让所有请求都直接打到数据库上**。

Kafka 削峰填谷的逻辑是：把请求先全部扔进 Kafka，然后消费者按自己能消化的速度慢慢消费。流量还是那个流量，但消费速度从"一秒钟灌进去"变成"慢慢喝"，数据库压力就稳住了。

```java
// 秒杀接口：请求来了我照单全收，但不是直接操作数据库
@PostMapping("/seckill")
public Result seckill(Long productId, Long userId) {
    OrderMessage msg = new OrderMessage(productId, userId, System.currentTimeMillis());
    // 直接扔进 Kafka，接口轻松应对高并发
    kafkaTemplate.send("seckill-order-topic", JSON.toJSONString(msg));
    return Result.ok("排队中，请稍后查看结果");  // 异步返回，不阻塞用户
}

// 消费者：慢慢处理订单，数据库完全扛得住
@KafkaListener(topics = "seckill-order-topic", concurrency = "3")
public void processOrder(String message) {
    OrderMessage msg = JSON.parseObject(message, OrderMessage.class);
    orderService.createOrder(msg.getProductId(), msg.getUserId());
}
```

你看看，本来一秒来两万的请求，经过 Kafka 一缓冲，消费者每秒处理一千条，数据库稳如老狗。

**用 Kafka 做削峰填谷，和直接限流的区别在于**：限流是直接拒绝多余请求（用户看到"系统繁忙"），削峰填谷是所有请求都能受理，就是处理慢点，体验好太多了。


---

## 三、延迟消息——该来的总会来，但可以晚点来

有些场景是这样的：用户下单后 30 分钟内如果不支付，咱要自动取消订单。

这个 30 分钟的延迟，咋搞嘞？

传统的做法可能是弄个定时任务，每隔几分钟扫一遍数据库——这方案也不是不行，但订单表动不动就上千万行，你扫一个我看看？扫一次数据库就哭一次，而且定时任务的精度也跟不上。

其实 Kafka 没有原生的延迟消息功能（RocketMQ 有），但我们可以绕个弯子——**多级时间轮**的思想，把消息按延迟时间丢到不同的 topic 里，用一个调度器来转发：

```java
// 下单后发延迟消息到 30min 级别
public void orderCreated(Order order) {
    DelayMessage msg = new DelayMessage();
    msg.setOrderId(order.getId());
    msg.setExpireTime(System.currentTimeMillis() + 30 * 60 * 1000);
    // 先写到一个外部存储，比如 Redis，存下消息体
    redisTemplate.opsForValue().set("delay:" + order.getId(), JSON.toJSONString(msg));
    // 同时写到一个有定时触发的 topic
    kafkaTemplate.send("delay-order-topic", JSON.toJSONString(msg));
}

// 延迟调度器：轮询检查哪些消息该投递了
@Scheduled(fixedDelay = 5000)
public void delayDispatcher() {
    // 从 Redis 扫出到期的消息
    Set<String> keys = redisTemplate.keys("delay:*");
    for (String key : keys) {
        DelayMessage msg = JSON.parseObject(redisTemplate.opsForValue().get(key), DelayMessage.class);
        if (msg.getExpireTime() <= System.currentTimeMillis()) {
            // 时间到了，投到目标 topic
            kafkaTemplate.send("order-cancel-topic", JSON.toJSONString(msg));
            redisTemplate.delete(key);
        }
    }
}
```

不过说实话，如果是 Kafaka 做延迟消息，咱不建议搞得太复杂。Kafka 其实可以通过 **时间戳索引** 来实现类似效果——在 `Consumer` 消费时判断消息的延迟时间是否到了，没到就 `pause()` 一下分区，等时间差不多了再 `resume()`。

**如果延迟消息是你们的刚需，还是直接上 RocketMQ 更省心**，Kafka 在这方面确实不是原生的优势。毕竟人家 RocketMQ 原生就带了 18 个延迟等级，开箱即用，这个咱得承认嘞（狗头）。


---

## 四、事务消息——要么全做，要么全不做

事务消息听起来很高大上，其实说白了就一句话：**保证"发消息"和"执行本地业务"这两个操作要么都成功，要么都失败。**

典型的场景就是下单扣库存：订单创建成功 + 发消息通知扣库存，这两个操作不能出现"订单已经创建了，但扣库存的消息没发出去"的情况。

传统的做法是在数据库里建一张"本地消息表"，用同一个本地事务包裹：

```java
@Transactional
public void createOrder(Order order) {
    // 1. 写订单表
    orderMapper.insert(order);
    // 2. 写本地消息表（和订单在同一个数据库事务里）
    MessageLog log = new MessageLog();
    log.setTopic("order-created");
    log.setPayload(JSON.toJSONString(order));
    log.setStatus("PENDING");
    messageLogMapper.insert(log);
    // 只要事务提交成功，这两条记录一定都存在
}
```

然后另开一个定时任务，把消息表中 `PENDING` 的消息发到 Kafka，成功发送后更新状态为 `SENT`：

```java
@Scheduled(fixedDelay = 3000)
public void sendPendingMessages() {
    List<MessageLog> pending = messageLogMapper.findByStatus("PENDING");
    for (MessageLog log : pending) {
        try {
            kafkaTemplate.send(log.getTopic(), log.getPayload()).get();
            log.setStatus("SENT");
            messageLogMapper.update(log);
        } catch (Exception e) {
            // 失败了没事，下次定时任务再捞起来重试
            log.warn("消息发送失败，等待重试: {}", log.getId());
        }
    }
}
```

这套方案在很多公司里都在用，稳得很。

**那 Kafka 原生的"事务"是啥呢？** 其实 Kafka 的事务主要是保证**生产者幂等 + 跨分区原子写入**，跟我们常说的"分布式事务"不是一回事。Kafka 的事务更像是在说："放心吧，你发的这坨消息要么全部被 consumer 看见，要么一条都看不见，不会出现只看见一半的情况。"

如果真要做分布式事务，Kafka 事务 + 本地消息表一起上会比较稳：

```java
// Kafka 事务消息示例（生产者端）
producer.initTransactions();
try {
    producer.beginTransaction();
    // 发多条消息
    producer.send(new ProducerRecord<>("topic-A", "msg1"));
    producer.send(new ProducerRecord<>("topic-B", "msg2"));
    // 本地业务也一起提交
    localService.doBusiness();
    producer.commitTransaction();  // 一起成功
} catch (Exception e) {
    producer.abortTransaction();   // 一起回滚
}
```

> **划重点**：Kafka 事务不能跨系统回滚你本地的数据库事务，千万别以为 `producer.abortTransaction()` 能把 MySQL 的 insert 也给回滚了，那是想多了嗷！


---

## 五、消息积压——你的队列堵车了，怎么办？

消息积压是线上最常见的问题之一了。咱就是说，哪个搞 Kafka 的没遇到过几次"消费跟不上生产"的紧急情况捏？

### 怎样定位积压

第一步当然是看看积压到底有多严重：

```bash
# 查看消费者组的消费情况
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --group your-group --describe
```

看 `LAG` 那一列，如果动不动就几十万上百万，那恭喜你，喜提积压大礼包一份 🎁。

### 积压的几种常见原因和解决套路

**1. 消费者太慢了**

最直接的原因就是消费逻辑里面有慢操作，比如一条消息处理要 5 秒钟，那一个 consumer 一秒就处理 0.2 条，不积压才见鬼了。

解决：**加消费者数量**。Kafka 一个 topic 有多少分区，最多就有多少个消费者并行消费。所以如果分区数是 3，那你开 10 个消费者也没用，只有 3 个在干活。

```bash
# 先把分区数扩上去（这个操作要注意，已经存在的 key 路由可能会变）
kafka-topics.sh --bootstrap-server localhost:9092 \
    --alter --topic your-topic --partitions 10
```

然后 consumer 开够 10 个，理论上处理能力就翻了 3 倍多。

```java
// 增加消费者并发线程数
@KafkaListener(topics = "your-topic", concurrency = "10")
public void consume(String msg) {
    // 处理逻辑
}
```

**2. 消费逻辑里有锁竞争或 IO 瓶颈**

有些朋友写的消费逻辑里面，每条消息都要去查一次外部 API，而那个 API 每秒只能处理 100 个请求——那你开 10 个 consumer 也没用，瓶颈在那边。

这时候要做的就是**优化消费逻辑本身**：
- 批量查询代替逐条查询（攒够一批消息一起查）
- 能加缓存的地方加个缓存
- 没必要的同步操作改成异步

```java
// 不好的写法：每条消息都查一次数据库
@KafkaListener(topics = "order-topic")
public void consume(String msg) {
    User user = userMapper.selectById(msg.getUserId());  // 每次都查！
    // ...
}

// 改进：攒一批批量查
@KafkaListener(topics = "order-topic")
public void consume(List<String> messages) {
    List<Long> userIds = messages.stream()
        .map(m -> JSON.parseObject(m, OrderMsg.class).getUserId())
        .collect(Collectors.toList());
    // 一次批量查询
    List<User> users = userMapper.selectBatchIds(userIds);
    // 然后在内存里做匹配处理
    // ...
}
```

**3. 数据倾斜，某个分区特别忙**

如果你发现大多数消费者都很闲，就一两个跑满了，那大概率是数据倾斜了——某个分区的消息特别多。

这时候得检查一下生产者的分区策略，看是不是 key 设得有问题：

```java
// 如果以 userId 作为 key，某个大客户的请求量特别大，那消息就全堆一个分区了
producer.send(new ProducerRecord<>("topic", userId.toString(), message));

// 如果消息之间没有严格的顺序要求，可以不设 key，让它轮询均匀分布
producer.send(new ProducerRecord<>("topic", null, message));
```

**4. 终极方案：紧急情况下跳过非关键处理**

如果线上已经炸了，先止损再说。临时写个快速消费者把积压的消息吞掉，只做最关键的处理：

```java
@KafkaListener(topics = "your-topic")
public void emergencyConsume(String msg) {
    // 只做必须的操作，能跳过的全跳过
    OrderMsg orderMsg = JSON.parseObject(msg, OrderMsg.class);
    // 只记录关键字段到数据库，别的不干了
    orderEmergencyMapper.insertMinimal(orderMsg);
    // 日志、通知、统计等先全砍掉
}
```

等积压消掉了再切回正常的消费者。

### 积压预防比救火更重要

平时就得搭好监控：

```java
// 日常监控 LAG 指标，设置告警阈值
// 比如 LAG > 10000 并且持续 5 分钟就告警
// 这个可以在 Prometheus + Grafana 里搞定
```

平时多盯着，别等用户投诉了才发现队列炸了——那时候黄花菜都凉了。


---

## 总结

Kafka 作为一个老牌消息队列，在这些经典场景下还是相当能打的：

- **异步解耦**：让服务之间各玩各的，新增下游不改上游
- **削峰填谷**：用缓冲应对瞬时高并发，保护后端脆弱的数据库
- **延迟消息**：有点勉强，但能绕弯子实现（真刚需建议上 RocketMQ）
- **事务消息**：配合本地消息表做最终一致性，稳如老狗
- **积压处理**：加分区加消费力 + 批量优化 + 监控告警，三件套走起

当然，上面很多方案是走"最终一致性"路线的，如果你的业务要求强一致性（比如银行转账），那就得多掂量掂量了，不能啥都往 Kafka 里怼。

以上是个人的一些经验分享，如果哪里有错误的地方也请大佬们指出，咱一起进步！

本文完结撒花！！！🎉

---

*觉得有用的话，点个赞呗～*
