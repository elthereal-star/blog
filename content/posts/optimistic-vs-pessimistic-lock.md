---
title: "库存超卖？别慌，乐观锁和悲观锁来救场了！"
date: 2026-06-01
draft: false
categories: ["数据库"]
tags: ["乐观锁", "悲观锁", "超卖", "并发控制"]
summary: "不知道朋友们在做电商项目的时候有没有遇到过这样的场景：商品库存就剩 1 件了，结果两个用户同时下单，啪的一下，库存扣成了 -1？嘿嘿，这就是大名鼎鼎的\"超卖…"
ShowToc: true
---


不知道朋友们在做电商项目的时候有没有遇到过这样的场景：商品库存就剩 1 件了，结果两个用户同时下单，啪的一下，库存扣成了 -1？嘿嘿，这就是大名鼎鼎的"超卖"问题。

我们在进行秒杀、抢购这类高并发业务开发的时候，超卖问题几乎是绕不开的一道坎。今天咱就来聊聊解决这类问题的两把利器——**乐观锁**和**悲观锁**，看看它们各自有啥本事，又该怎么选。

不过在开整之前，咱得先整明白一件事：这俩锁到底是啥玩意儿？

---

## 悲观锁和乐观锁到底是个啥？

### 悲观锁：我先锁上，你们排队等着

咱先来打个比方哈。想象一下，你去公共厕所，进去之后 **"咔哒"一声把门锁上**，外面的人就只能乖乖排队等着。你在里面干啥外面的人管不着，但你出来之前，谁也别想进来 —— 这就是悲观锁的思想。

悲观锁的态度就是：**"我总觉得会有人跟我抢，所以我一上来就把资源锁住，等我用完了你们再来。"**

在代码层面，悲观锁通常是通过数据库的行级锁或者 `synchronized`、`ReentrantLock` 这些机制来实现的。最经典的操作就是在 SQL 里加一个 `FOR UPDATE`：

```sql
-- 开启事务
BEGIN;

-- 查询库存，同时锁住这一行，别人碰不了
SELECT stock FROM product WHERE id = 1 FOR UPDATE;

-- 扣减库存
UPDATE product SET stock = stock - 1 WHERE id = 1;

-- 提交事务，释放锁
COMMIT;
```

这样一来，当一个事务拿着这行数据的锁的时候，别的事务想操作这行数据？不好意思， **堵着**，等前面的完事儿了再说。

**悲观锁的优点很明显**：简单粗暴，数据一致性杠杠的，不会出现超卖。

**缺点也摆在那儿**：并发量大的时候，大量请求排队等锁，吞吐量直接拉胯。而且如果锁没控制好，还有死锁的风险，那可就翻车了。

### 乐观锁：我先看看你有没有偷偷改过

接着用厕所的比喻，乐观锁的思路是：**不锁门！** 但每次进出之前，我瞅一眼厕所里的状态有没有被人动过。如果我知道进去前是啥样，出来后还是啥样，那就没问题。可要是中间有人来搞过事情了，那就得重新来一把。

乐观锁的态度就比较佛系了：**"我觉得没人会跟我抢，所以我先操作，操作完了检查一下有没有冲突。"**

在实际开发中，乐观锁最常见的实现方式就是 **版本号（version）机制**：

```sql
-- 先查出版本号
SELECT id, stock, version FROM product WHERE id = 1;
-- 假设查出来 version = 5, stock = 10

-- 更新的时候加上版本号条件
UPDATE product
SET stock = stock - 1, version = version + 1
WHERE id = 1 AND version = 5;
-- 如果 version 已经不是你查出来的那个 5 了，
-- 说明中间有人改过，这条 UPDATE 影响的行数就是 0
```

用 Java 代码配合 MyBatis-Plus 来实现的话，大概是这个味儿：

```java
@Service
public class ProductService {

    public Result buyProduct(Long productId) {
        // 1. 查出商品
        Product product = productMapper.selectById(productId);
        if (product.getStock() <= 0) {
            return Result.fail("库存不足，手慢了兄弟！");
        }

        // 2. 扣减库存，带上 version 条件
        int rows = productMapper.deductStock(productId, product.getVersion());
        if (rows == 0) {
            // 版本号对不上，说明有人抢在前面改了
            return Result.fail("抢购失败，请重试~");
        }

        // 3. 创建订单...
        return Result.success("恭喜，抢到了！");
    }
}
```

```java
// Mapper 里的 SQL
@Update("UPDATE product SET stock = stock - 1, version = version + 1 " +
        "WHERE id = #{id} AND version = #{version} AND stock > 0")
int deductStock(@Param("id") Long id, @Param("version") Integer version);
```

MyBatis-Plus 其实自带乐观锁支持，贼方便 —— 在实体类字段上打个 `@Version` 注解就完事儿了：

```java
@Data
@TableName("product")
public class Product {
    private Long id;
    private Integer stock;

    @Version  // 就这一行，MP 自动帮你处理版本号
    private Integer version;
}
```

**乐观锁的优点**：不阻塞，并发性能好，适合读多写少的场景。

**缺点**：如果冲突多，大量请求会被打回重试，用户体验不太美丽。而且如果多次重试都失败，那体验就更糟糕了，需要配合重试机制来用。

---

## 超卖问题，到底该选哪个？

好，现在两把锁咱都认识了，回到最开始的超卖问题。到底该用乐观锁还是悲观锁？这得看场景，不能一刀切。

### 场景一：秒杀、抢购 —— 选乐观锁

秒杀场景的特点是啥？**流量巨大、瞬间爆发、大部分请求都是失败的。**

在这种场景下用悲观锁，所有请求排队等行锁，数据库连接池直接被打满，整个服务可能就崩了。这谁顶得住啊？

所以秒杀咱一般上乐观锁，配合 Redis 做库存预扣减，挡掉大部分无效请求，数据库压力小很多。

{{< svg "optimistic-lock" >}}

不过乐观锁有个坑要注意：**冲突率高的时候，大量请求被驳回，部分用户可能反复重试都抢不到。** 咱可以加个重试次数限制，比如最多重试 3 次，还抢不到就提示"参与人数过多，下次再来吧"。

### 场景二：普通下单、账户余额扣减 —— 选悲观锁

普通的电商下单，虽然也有并发，但流量远没有秒杀那么夸张。而且这种场景**对数据一致性的要求更高**，用户不能接受"扣了钱没买到东西"或者"买了东西没扣钱"这种事。

这个时候用悲观锁就挺合适的，干净利落，数据绝对不会错。

```java
@Transactional
public Result createOrder(Long userId, Long productId) {
    // 悲观锁锁定库存行
    Product product = productMapper.selectForUpdate(productId);
    if (product.getStock() <= 0) {
        return Result.fail("已售罄");
    }

    // 扣库存
    productMapper.deductStock(productId, 1);

    // 创建订单
    orderMapper.insert(new Order(userId, productId));

    return Result.success("下单成功！");
}
```

### 场景三：扣减余额、积分这类操作 —— 乐观锁

像余额扣减这种操作，虽然一致性要求高，但并发冲突率通常不高（毕竟一个人不会同时从两个设备给自己转账吧）。用乐观锁刚好合适，性能又好又够安全。

顺带一提，这种场景如果用悲观锁，万一事务里调了外部接口比较慢，锁一直不释放，那就很尴尬了。乐观锁就没有这层顾虑。

---

## 进阶玩法：乐观锁 + 重试机制

前面说了，乐观锁冲突多的时候会有重试问题。那咱就给它整一个重试机制呗。

```java
@Service
public class ProductService {

    private static final int MAX_RETRY = 3;

    public Result buyWithRetry(Long productId) {
        for (int i = 0; i < MAX_RETRY; i++) {
            try {
                Result result = buyProduct(productId);
                if (result.isSuccess()) {
                    return result;
                }
                // 乐观锁冲突了，歇一会儿再试
                Thread.sleep(50);  // 别太急躁，给别的线程一点时间
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return Result.fail("系统繁忙，请重试");
            }
        }
        return Result.fail("抢购太火爆了，已经重试了" + MAX_RETRY + "次都没抢到，要不换个姿势再来？");
    }

    private Result buyProduct(Long productId) {
        // 乐观锁扣库存逻辑...
        return Result.success();
    }
}
```

**不过这里有个小坑**：重试次数别设太多，等待时间也别太短，不然就是无效的反复横跳，白白浪费系统资源。一般来说 3 次重试，每次间隔 50-100ms 就够用了。

---

## CAS：乐观锁背后的思想

聊到乐观锁，就不得不提一下 CAS（Compare And Swap，比较并交换）这个思想。其实咱前面用的 `WHERE version = #{version}` 就是一种 CAS 的落地方式。

CAS 的思想很简单：**"我先把原来的值记下来，更新的时候检查一下，如果原来的值没变过，说明没人动过，我就放心更新；如果变了，说明有人抢先了，那我就放弃。"**

这就好比你在图书馆占座，放了本书在桌上，回头来看看书还在不在——在的话说明没人动过你的位置，不在的话……那就只能另找地方了。

除了版本号，CAS 的另一个实现方式是用 **时间戳**，原理差不多：

```sql
UPDATE product SET stock = stock - 1, update_time = NOW()
WHERE id = 1 AND update_time = #{oldUpdateTime};
```

不过时间戳的方案不如版本号靠谱，毕竟时间戳有可能撞车（虽然概率很低），所以我个人更推荐用版本号。

---

## ABA 问题：乐观锁的一个坑

既然说到 CAS 了，那就得提一下 ABA 问题。啥意思呢？

假设线程 A 读到 version = 1，然后去做了一些耗时的计算。在这期间：
- 线程 B 把 version 从 1 改成了 2
- 线程 C 又把 version 从 2 改回了 1

等线程 A 回过神来，发现 version 还是 1，以为没人动过，美滋滋地执行了更新。

**但实际上这行数据已经被人改了两次了！** 这就是 ABA 问题。

不过在实际业务中，ABA 问题的危害因场景而异：
- **库存扣减**：影响不大，因为库存的值确实变了，但最终扣减逻辑还是能正常执行的
- **账户余额**：就要小心了，可能会导致金额计算错误

解决方案也有，就是给版本号加上一个 **"修改次数"** 的概念，version 只增不减，每次修改都 +1，这样就不会出现 A → B → A 的循环了。MyBatis-Plus 的 `@Version` 默认就是这么干的，所以其实不用太担心。

---

## 一句话总结：选锁指南

| 场景 | 推荐锁 | 原因 |
|------|--------|------|
| 秒杀/抢购 | 乐观锁 + Redis | 高并发、冲突多，悲观锁排队会崩 |
| 普通下单 | 悲观锁 | 一致性要求高，流量可控 |
| 余额/积分扣减 | 乐观锁 | 冲突少，性能好 |
| 配置修改 | 乐观锁 | 多管理员可能同时改，避免互相覆盖 |

---

## 写在最后

乐观锁和悲观锁这两个东西，说到底没有绝对的谁好谁坏，关键看你的业务场景适合哪个。就像出门穿衣服一样，大冬天穿短袖会冻死，大夏天穿羽绒服会热死——**合不合适要看实际情况**。

我们一般在项目里两个都会用到，不同的接口根据业务特点选择不同的锁方案。如果一个方案让系统变卡了或者数据不准了，那就果断换另一个试试，没必要死磕。

以上是个人的一些经验分享，希望能帮到正在跟超卖斗智斗勇的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起进步～

**本文完结撒花！！！** 🎉

---

*小贴士：如果你的项目刚好用到了 MyBatis-Plus，别忘了它自带的 `@Version` 乐观锁插件，配置简单到令人发指，比手写版本号判断省心太多了。另外 Redis + Lua 脚本做分布式锁也是一把好手，配合上面的方案食用风味更佳～*
