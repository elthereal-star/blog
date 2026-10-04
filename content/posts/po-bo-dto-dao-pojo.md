---
title: "O_o，PO , BO , DTO , DAO , POJO 到底什么O是什么什么O?o_O（Java中这些对象的设计思想）"
date: 2026-05-19
draft: false
categories: ["Java"]
tags: ["POJO", "DTO", "VO", "分层设计"]
summary: "首先，Oo 和 oO 是大眼瞪小眼的意思，用来皮一下的，嘿嘿oO。"
ShowToc: true
---


首先，**O_o** 和 **o_O **是大眼瞪小眼的意思，用来皮一下的，嘿嘿o_O。

好了，现在正儿八经的说了。先来一个笼统的概念，这些 O 都是 object 的意思，也就是对象，是用来承担Java项目当中不同的作用和功能的，以此来降低程序的耦合性（没有很大必要的重复部分）和安全性，实现各司其职的效果。就好比在社会当中不同的人会扮演不同的角色，实现不同的作用。

### 概念拆解

#### PO（Persistent Object）

也就是持久化对象的意思，持久化一般都是跟数据库对接相关的。这里的PO就是一个对象，其中包含了与数据库相对应的结构，一般就是由MyBatis这
类
的框架来进行驱动。这里来举一个例子：就比如说我们的数据库里面有一张表 user ,里面的字段有 id , username , password , email , age ,create_time。然后这个时候我们要设计一个PO对象，就应该是这样的

```java
//PO对象，用于与数据中的表对应

public class UserPO {
private Long id;
private String username;
private String password;
private String email;
private Integer age;
private LocalDateTime createTime;

//后面就是对应的get方法和set方法了
}
```

可以看到，PO对象里面的元素跟数据库表中的字段是一一对应的，只是一个用的驼峰命名法，另一个用的是下划线命名法。

其实简单点来说，PO也就是数据库某张表的一个代码上的复制品，方便我们跟数据库对应上然后使用，是数据库表的一种体现，所以不要在这个里面写业务逻辑（比如说去判断这个人成年了没有，万一啥时候修改了成年的定义，又得回来动这个表，就没有办法保证他的纯净），需要保证他的干净。

#### DAO（Data
Access
Object）

也就是数据访问对象的意思，我们主要在里面写一些对于数据库增删改查的逻辑，一些业务逻辑也不在这里进行书写。这里我们还是基于刚刚举的那张表为例子。

```java
public interface UserDAO {
//插入一个持久化对象
int insert(UserPO userPO);

//根据id来进行查询
/*在这些方法的上面可以使用@Select,@Delete等注解来在声明函数的性质
（比如是查询操作还是删除操作），然后在注解当中书写SQL语句，到时候
程序就可以通过执行里面的SQL语句来对数据库进行操作并且返回结果。
*/
UserPO selectById(Long id)
}
```

我们可以使用传统的MyBatis方法，通过在这个 selectById 的函数上面使用@Select注解的方式来对这个函数进行实现，也可以通过 xml 文件来映射这个对象，然后在里面书写这个对象里面方  法的具体实现。

同时，我们也可以使用 MyBatis-Plus 来进行更快捷的处理方式，只需要让这个对象继承       BaseMapper <UserPO> ，来自动拥有 selectById , insert , update等十余种方法，但是需要对PO对象先进行注解之后，才能够让MyBatis-Plus发挥这个作用，这里我们避免显得文章复杂冗长，我想就把它再另写一篇小的文章吧

#### DTO（Data Transfer Object）

也就是数据传输对象，用于在不同的层级之间进行数据的传输，通常来说会把如密码或者一些隐私信息给过滤掉，相当于是一个尽职尽责的保安，只给需要的东西。这里我们还是基于前面说的那张表来作为例子。

```java
// 用户注册时，前端传来的数据
public class UserRegisterDTO {
private String username;
private String password;
private String email;
// 注册时不需要传 ID 和 createTime，所以 DTO 不包含它们
}

// Service层返给Controller的信息
public class UserDTO {
private Long id;
private String username;
private String email;
// 过滤掉了 password，保证了安全
}
```

可以看到，DTO就是非常的抠搜，要啥就只给啥，不会多给，这样也能确保我们数据的安全性。

#### BO（Business Object）

也就是业务对象，我们在这里来封装我们的业务逻辑，一个业务逻辑里面可能包含多个PO（持久化对象），算是起到一个零件组装的作用，通过一些逻辑对一个或者多个PO进行操作，实现我们想要的功能。

```java
public class UserBO {
private UserPO userPO;

// 业务逻辑：判断用户是否成年
public boolean isAdult() {
return userPO.getAge() >= 18;
}

// 业务逻辑：计算用户账号等级
public String getRank() {
// 根据 createTime 计算它是“老玩家”还是“新萌”
return "黄金会员";
}
}
```

#### VO（View Object）

也就是试图对象。我们通过这个试图对象来让前端展示我们的一些数据，同时可以在里面进行一些对前端友好化的操作（比如说把日期给格式化）

```java
public class UserVO {
private String name;    // 对应 username
private String email;
private String userRank; // 这是从 BO 计算出来的，数据库里没有这个字段
private String joinDate; // 将 LocalDateTime 格式化为 "2023年5月" 这种字符串
}
```

这样数据传输到前端的时候，通过前端界面看起来就舒服多了，所以VO也可以说就是拿来讨好前端的。

####
POJO
（Plain Old Java Object）

这个也就是一个简单的Java对象，有点像老农民的的感觉，就很淳朴，很干净。跟前面的PO有点像，但是PO是对数据库上面的数据层面的，这个POJO就是对于Java对象层面的。其实上面举的例子当中的 UserPO ,UserDTO ,UserVO, 也都可以算是POJO，只要他们不去继承一些特殊的框架( 比如Hibernate的专用基类 )，那也是一个干净的POJO了。

### 小总结

其实如果是一个很小的项目，倒是没有必要去划分的那么细，这样子搞这么多种对象反而是浪费时间精力，一个 User 类就可以一直从头用到尾了（当然，一般是指的就是之间搓着玩的小玩意儿）。但是如果是一个正儿八经的项目的话，确实还挺有这个必要的，我们可以从下面这些角度来看一下。

从安全性来说：咱们数据库当中还有password的字段，这总不能就库库的也给前端都发过去了吧，那还要那密码干啥捏，而且这玩意儿你哪怕是加密了再发出来瞅着也不好看呐，所以这就有扯到下一个问题了

从网络和性能开销上面来说：数据库里面那么多字段，咱也总不能全给人家不管三七二十一的就一股脑全怼屏幕上了吧，要人本来就只需要显示3个就够了，你猛猛的把几十上百个全干出去了，那也是不是不太中，而且这多费劲儿呐。

从耦合性角度上面来说：要万一哪天突然灵
光
一现，想着把数据库里面的哪个字段名改了，那前端不得崩溃，但是咱分层之后，只要把PO到DTO上面的映射修改一些就完事儿了，这不快活多了。

从美观角度上面来说：像咱后端存时间基本就是一个 Long 的一大长串，也就咱自己看看还好，这要放前端那不难为人家吗，是吧，那这个时候我们分出来的 VO 也就派上用场了，人瞅感觉还整挺好，不光咱能看明白，让别人也能看明白。

好了，以上就是我个人的一些理解，也就把概念稍微捋了一捋，当然可能还是会存在言辞表达的可能不是很好的地方，请各位大佬们多多包涵，如果有更好的理解的话也可以分享出来我们一起学习哈**o_O**


{{< svg "pojo-layers" >}}
