---
title: "MyBatis-Plus 到底是个啥？为什么用了之后 CRUD 写得我想哭（感动的那种）"
date: 2026-05-24
draft: false
categories: ["数据库"]
tags: ["MyBatis-Plus", "ORM", "持久层", "Spring Boot"]
summary: "不知道大伙儿有没有过这种体验——刚进公司接手一个项目，打开 Mapper XML，好家伙，密密麻麻的 SQL 标签铺满屏幕，光一个简单的用户查询就写了十几行…"
ShowToc: true
---


不知道大伙儿有没有过这种体验——刚进公司接手一个项目，打开 Mapper XML，好家伙，密密麻麻的 SQL 标签铺满屏幕，光一个简单的用户查询就写了十几行 XML。更离谱的是，每个表都要来一遍 `selectById`、`insert`、`updateById`、`deleteById`，写到后面感觉自己在流水线拧螺丝，毫无灵魂 (꒦ິ⌓꒦ີ)

咱就是说，这些增删改查的逻辑90%都是一毛一样的，只是表名和字段不同，为什么每次都要重新写一遍呢？

于是乎，**MyBatis-Plus** 闪亮登场！

---

## MyBatis-Plus 是个啥？

用一句话概括：**MyBatis-Plus（简称 MP）是 MyBatis 的一个增强工具包，专门用来帮我们干掉那些无聊的重复 CRUD 代码。**

它和 MyBatis 的关系就好比——你买了个毛坯房（MyBatis），MP 直接帮你把基础装修整好了，家具家电配齐了，你拎包入住就行。但如果你想自己搞个性化装修（复杂 SQL），原来的墙和管道还在，你随时可以动手改，完全不冲突。

官方自己说的理念是"**只做增强，不做改变**"，翻译成人话就是：你原来怎么写 MyBatis 现在还怎么写，MP 不会动你原来的代码，只是额外给你塞了一堆好用的工具，用了就回不去的那种 (≧∇≦)ﾉ

---

## 先搭个环境瞅瞅

话不多说，咱直接上手感受一下。

### 导入依赖

Spring Boot 项目的话，一个 starter 搞定：

```xml
<dependency>
    <groupId>com.baomidou</groupId>
    <artifactId>mybatis-plus-boot-starter</artifactId>
    <version>3.5.16</version>  <!-- 当前最新版，2026年1月出的 -->
</dependency>
```

> 偷偷说一句，如果你是 Spring Boot 4.0 的项目，MP 从 3.5.15 开始就已经支持了，跟得那是相当紧，生态这块没得黑。

### 配置文件

在 `application.yml` 里配上数据库连接和 MP 的基本设置：

```yaml
spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://localhost:3306/your_db?characterEncoding=utf-8&serverTimezone=Asia/Shanghai
    username: root
    password: your_password

mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true   # 数据库下划线自动转实体驼峰，必开！
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl  # 开发时打开，SQL打印到控制台
  global-config:
    db-config:
      id-type: auto   # 主键自增，后面还会聊
```

配到这里，环境就算整好了，是不是比想象中简单？( ᖛ ̫ ᖛ )

---

## BaseMapper：真正的"母胎 CRUD"

这是 MP 最核心、最灵魂的东西——**一个接口帮你搞定所有单表增删改查**。

### 创建实体类

先整个实体类，对着数据库表建就行：

```java
@Data
@TableName("t_user")  // 如果表名和类名不一样，用这个指定
public class User {
    @TableId(type = IdType.AUTO)  // 主键自增，MP还支持雪花ID等好几种策略
    private Long id;
    private String name;
    private Integer age;
    private String email;
    @TableLogic  // 逻辑删除标记，后面细聊
    private Integer deleted;
}
```

### 创建 Mapper

接下来是见证奇迹的时刻——你的 Mapper 只需要继承一个接口：

```java
@Mapper
public interface UserMapper extends BaseMapper<User> {
    // 啥也不用写！BaseMapper 已经把活全干完了
}
```

就这？就这？？对，就这。

来瞅一眼 `BaseMapper` 白送给你的方法清单（只是常用的一部分）：

| 方法 | 干啥的 |
|------|--------|
| `insert(entity)` | 插入一条记录 |
| `deleteById(id)` | 根据ID删除 |
| `deleteBatchIds(idList)` | 批量删除 |
| `updateById(entity)` | 根据ID更新 |
| `selectById(id)` | 根据ID查询 |
| `selectBatchIds(idList)` | 批量ID查询 |
| `selectList(wrapper)` | 条件查询（wrapper传null查全表） |
| `selectPage(page, wrapper)` | 分页查询 |
| `selectCount(wrapper)` | 条件统计数量 |

一共 17+ 个方法，覆盖了日常开发 80% 以上的单表操作。说白了就是——**以前你吭哧吭哧写半天 XML 才能搞定的活，现在一行代码都不用写了**。

### 实际使用

```java
// 新增用户
User user = new User();
user.setName("张三");
user.setAge(25);
user.setEmail("zhangsan@example.com");
userMapper.insert(user);  // 就这么简单

// 查一个
User found = userMapper.selectById(1L);

// 改一下
found.setAge(26);
userMapper.updateById(found);

// 删掉（如果有@TableLogic，会自动变成逻辑删除）
userMapper.deleteById(1L);

// 批量查
List<User> users = userMapper.selectBatchIds(Arrays.asList(1L, 2L, 3L));
```

看到这里可能有朋友会问：那我想按名字查用户呢？`selectById` 搞不定啊！

问得好，接下来就是 MP 另一个大杀器——**条件构造器**。

---

## 条件构造器：告别手写 WHERE 子句

用原生 MyBatis 的时候，每次加个条件查询就要去 XML 里加标签，或者写个注解 SQL 拼字符串，字段名一改还得全局搜索，一个不留神就 SQL 注入。MP 的条件构造器就是来解决这个痛点的。

MP 给我们准备了四兄弟：

- **QueryWrapper**：通用的查询/删除/更新条件构造器，用字符串表示字段名
- **UpdateWrapper**：专门搞更新的，可以直接 set 字段值
- **LambdaQueryWrapper**：Lambda 版本，用 `实体::getXxx` 的方式指定字段，**类型安全不怕字段名写错**
- **LambdaUpdateWrapper**：Lambda 版的更新构造器

> 日常强烈建议用 Lambda 系列！因为字段名是编译器帮你检查的，重构的时候改实体字段名，这里会跟着变，不会出现字段名改了但字符串没改导致运行时炸锅的尴尬情况 ( ´•̥̥̥ω•̥̥̥` )

### 基础用法

```java
// 查询年龄等于18，名字里带"张"，且邮箱不为空的所有用户
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(User::getAge, 18)
       .like(User::getName, "张")
       .isNotNull(User::getEmail)
       .orderByDesc(User::getId);
List<User> users = userMapper.selectList(wrapper);
```

生成的 SQL 大概长这样：

```sql
SELECT * FROM t_user
WHERE age = 18
  AND name LIKE '%张%'
  AND email IS NOT NULL
ORDER BY id DESC;
```

链式调用，一路点到底，读起来跟说话一样自然——"年龄等于18，名字像张，邮箱不为空，按ID倒序排"，谁还愿意回去拼字符串啊 (╯‵□′)╯︵┻━┻

### 动态条件查询

实际开发中经常遇到：前端传来一堆筛选条件，有些有值有些没值。老写法得 if 判空一顿套，看的人都麻了。

MP 的做法贼优雅——条件方法的第一个参数直接传 boolean：

```java
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.like(StringUtils.hasText(keyword), User::getName, keyword)  // keyword没值就跳过这个条件
       .ge(minAge != null, User::getAge, minAge)                     // minAge没传也跳过
       .le(maxAge != null, User::getAge, maxAge);                    // maxAge同理
List<User> users = userMapper.selectList(wrapper);
```

一行一行流畅到底，不用写一堆 if-else，代码直接清清爽爽～

### 嵌套条件

遇到 `(A AND B) OR (C AND D)` 这种复杂组合的时候，用 `and` 和 `or` 嵌套：

```java
wrapper.and(w -> w
    .like(User::getName, keyword)   // 名字包含关键字
    .or()                           // 或者
    .like(User::getEmail, keyword)  // 邮箱包含关键字
);
// 生成的 WHERE: AND (name LIKE '%keyword%' OR email LIKE '%keyword%')
```

### 更新也不用写 SQL

```java
// 把名字里带"张"的所有用户年龄改成30
LambdaUpdateWrapper<User> updateWrapper = new LambdaUpdateWrapper<>();
updateWrapper.set(User::getAge, 30)
             .like(User::getName, "张");
userMapper.update(null, updateWrapper);
```

**注意：update 的第一个参数可以是实体（把实体里的非空字段 set 进去），也可以传 null 只按 UpdateWrapper 里 set 的来。**

---

## 分页插件：就这？我还没发力呢

以前写 MyBatis 分页，要么用 RowBounds（物理分页效率低），要么手动在 XML 里拼 LIMIT，要么引入 PageHelper。现在有了 MP，一个插件搞定，而且还是物理分页，性能杠杠的。

### 第一步：注册插件

```java
@Configuration
@MapperScan("com.example.mapper")
public class MybatisPlusConfig {

    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        // 分页插件，MYSQL可以换成ORACLE、POSTGRESQL等，MP自动适配
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.MYSQL));
        return interceptor;
    }
}
```

### 第二步：直接开查

```java
// 第1页，每页10条
Page<User> page = new Page<>(1, 10);

// 带条件分页
LambdaQueryWrapper<User> wrapper = new LambdaQueryWrapper<>();
wrapper.eq(User::getAge, 18)
       .orderByDesc(User::getCreateTime);

Page<User> result = userMapper.selectPage(page, wrapper);

// 分页数据都在 result 里了：
System.out.println("总记录数：" + result.getTotal());
System.out.println("总页数：" + result.getPages());
System.out.println("当前页：" + result.getCurrent());
System.out.println("每页大小：" + result.getSize());
System.out.println("数据列表：" + result.getRecords());
```

就这么简单！两行初始化 + 一行调用，分页数据全出来了。

**这里有个小坑提醒一下：分页插件必须注册，不然 `selectPage` 会退化成全量查询，你传的 Page 参数会被无视掉。** 这是新手最容易踩的坑之一，别问我是怎么知道的 (ಥ_ಥ)

---

## Service 层也给你安排明白了

可能有些朋友已经发现了，光 Mapper 用起来爽还不够，Service 层还得包一层。MP 连这都替你想好了——`IService` 和 `ServiceImpl`：

```java
// Service 接口
public interface UserService extends IService<User> {
    // 复杂业务方法自己加就行
}

// Service 实现
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User>
        implements UserService {
    // 可以直接用 save()、remove()、update()、get()、list()、page() 等等
    // 还能用 lambdaQuery()、lambdaUpdate() 链式操作
}
```

继承之后，Service 层直接拥有了一大波方法：

```java
// 批量保存
userService.saveBatch(userList);

// 链式查询
List<User> list = userService.lambdaQuery()
        .eq(User::getAge, 18)
        .like(User::getName, "张")
        .list();

// 链式更新
userService.lambdaUpdate()
        .set(User::getAge, 30)
        .eq(User::getName, "张三")
        .update();
```

直接从 Service 层发起链式调用，不用 inject Mapper 来回倒腾，CRUD 写到飞起 ヾ(≧▽≦*)o

---

## 还有这些好用的"小玩意儿"

除了上面这些重头戏，MP 还塞了一堆锦上添花的功能，一个个说：

### 逻辑删除

数据不想真的删掉，只是标记一个"已删除"的状态。在实体字段上加个 `@TableLogic`：

```java
@TableLogic
private Integer deleted;  // 0=正常, 1=已删除
```

然后你调 `deleteById()` 的时候，MP 自动帮你把 `DELETE` 语句换成 `UPDATE ... SET deleted=1`，查数据的时候自动拼上 `WHERE deleted=0`，全程无感，真就"假装删了"（笑）

### 自动填充

创建时间和更新时间这种每个表都有的字段，每次都要手动 `set` 烦都烦死了。MP 用 `@TableField` 的 `fill` 属性 + 一个处理器直接自动化：

```java
// 实体里
@TableField(fill = FieldFill.INSERT)
private LocalDateTime createTime;

@TableField(fill = FieldFill.INSERT_UPDATE)
private LocalDateTime updateTime;
```

```java
// 搞一个处理器
@Component
public class MyMetaObjectHandler implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        this.strictInsertFill(metaObject, "createTime", LocalDateTime.class, LocalDateTime.now());
        this.strictInsertFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        this.strictUpdateFill(metaObject, "updateTime", LocalDateTime.class, LocalDateTime.now());
    }
}
```

配好之后，每次 insert/update 这些字段自动填值，再也不用一个个手动 `.setCreateTime(new Date())` 了，懒人福音！

### 乐观锁

并发场景下防止数据被覆盖的老大难问题，MP 一个 `@Version` 注解帮你搞定：

```java
@Version
private Integer version;
```

更新的时候自动帮你检查和自增版本号，比自己手写 CAS 逻辑靠谱多了 (。-`ω´-)

### 代码生成器

如果你不想手动建实体类、写 Mapper、写 Service、写 Controller——MP 提供了一个代码生成器，直接连数据库表，一键生成全部代码。`FastAutoGenerator` 用起来：

```java
FastAutoGenerator.create("jdbc:mysql://localhost:3306/your_db", "root", "password")
    .globalConfig(builder -> {
        builder.author("你的名字").outputDir("D://output");
    })
    .packageConfig(builder -> {
        builder.parent("com.example");
    })
    .strategyConfig(builder -> {
        builder.addInclude("t_user", "t_order"); // 指定要生成哪些表
    })
    .execute();
```

嗖的一下，Entity、Mapper、Service、Controller 全出来了，**猛猛的效率提升**！

---

## 总结一下

我们来盘一盘 MyBatis-Plus 到底给我们带来了啥：

1. **单表 CRUD 零代码**：BaseMapper 一把梭，增删改查一个接口全包了，再也不用写无聊的重复 XML
2. **条件构造器**：类型安全的 Lambda 链式调用，动态条件优雅到不像写 Java
3. **分页开箱即用**：一个插件注册，物理分页自动搞定
4. **Service 层封装**：链式查询一路点到底
5. **各种插件**：逻辑删除、乐观锁、自动填充、防全表更新……全是实际开发中高频用到的东西

说白了，MyBatis-Plus 的思路就是——**让简单的事情变得极其简单，复杂的事情保持足够灵活**。单表操作用 MP 的内置方法一步到位，复杂的多表关联 SQL 照样可以用原来的 XML 或注解方式自定义，没有任何冲突。

不过话说回来，如果你项目中用的不是 MyBatis 而是 JPA/Hibernate，那 MP 就帮不上忙了哈～技术选型还是得看具体场景。

---

以上是个人的一些经验分享，如果能帮你少敲几行 CRUD 代码，那这篇文章就没白写 (〃'▽'〃)

如果哪里有写的不对的地方也请大佬们指出，毕竟技术这东西日新月异，说不定过几天 MP 又出新版本加了更猛的 feature 呢～

**本文完结撒花！！！🎉🌸**
