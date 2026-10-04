---
title: "SpringBoot 的简化开发，爽到飞起！"
date: 2026-05-23
draft: false
categories: ["Spring"]
tags: ["Spring Boot", "自动配置", "starter", "约定优于配置"]
summary: "不知道朋友们刚学 Spring 的时候有没有被各种 XML 配置文件支配过（笑）。我还记得当年为了整一个 SSM 项目，光配置就得搞半天——web.xml、…"
ShowToc: true
---


不知道朋友们刚学 Spring 的时候有没有被各种 XML 配置文件支配过（笑）。我还记得当年为了整一个 SSM 项目，光配置就得搞半天——web.xml、applicationContext.xml、springmvc-servlet.xml……各种 xml 堆在一起，看的人都麻了。更别说还要手动配置 Tomcat、手动管理依赖版本、手动搞各种 Bean 的注入，简直像是在玩拼图游戏，还是那种没有参考图的那种。

所以捏，今天咱就聊聊 SpringBoot 是怎么把我们从配置地狱里捞出来的，让开发变得跟喝水一样简单嘿嘿。

## 啥是 SpringBoot？简单唠唠

如果把传统的 Spring 开发比作自己生火做饭——你得劈柴（搭项目结构）、生火（配各种 xml）、洗菜切菜（管理依赖）、炒菜（写代码），一顿操作猛如虎，一看进度零点五。

那 SpringBoot 就像是外卖——你只需要点菜（告诉它你要啥），它就给你送到嘴边了。开箱即用、约定大于配置、内置服务器、自动装配……说白了，就是 Spring 全家桶的"一键启动"版本。

## 第一步：项目的快速创建

以前创建 Spring 项目要么手动搭目录结构，要么用 Maven 的 archetype 一顿生成，出来可能还不是自己想要的。SpringBoot 这边儿直接给咱整了个 [Spring Initializr](https://start.spring.io/)，打开网页就能"搓"一个项目出来。


在页面上选好：

- **构建工具**：Maven 或 Gradle（新手朋友咱就选 Maven，稳）
- **语言**：Java 就完事了
- **Spring Boot 版本**：选个稳定版，别追最新，容易崴脚
- **项目元数据**：包名、项目名啥的，这个就不多说了
- **依赖**：这一步最舒服，你想用啥直接点点点——Web、JPA、MySQL、Redis……跟逛超市似的

点一下 Generate，一个完整的 SpringBoot 项目就下载下来了，导入 IDEA 就能直接跑，目录结构整整齐齐的，看着就舒坦！

> 当然，如果你用的是 IDEA Ultimate 版，直接在 IDE 里面也能创建 SpringBoot 项目，路径是 **File → New → Project → Spring Initializr**，连浏览器都不用开，更方便嗷。

## 第二步：不用再配 Tomcat 了！

传统 Spring 项目你得先把 Tomcat 下好、配好端口、配好部署路径，然后才能跑起来。新手朋友光这一步就能劝退不少人（别问我怎么知道的 TAT）。

SpringBoot 直接把 Tomcat（或者 Jetty、Undertow）打包进了项目里，你啥都不用配，运行一下 main 方法：

```java
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}
```

就这么几行代码，一个 Web 服务就起来了，默认 8080 端口，打开浏览器访问 `http://localhost:8080` 就能看到效果。想换端口？配置文件里加一行：

```properties
server.port=9090
```

搞定！不用在什么 server.xml 里面翻来翻去，爽不爽？

**这一步其实有个坑得注意：** 如果你之前电脑上跑过一个 8080 端口的程序没关，启动会报端口占用的错。新手朋友别慌，要么把之前的程序关了，要么换个端口就行。

## 第三步：依赖管理，一个 Starter 搞定一切

回忆一下传统 Spring 项目引入一个功能的流程：Google 搜依赖 → 找版本号 → 粘贴到 pom.xml → 启动报错 → 哦原来是版本不兼容 → 继续 Google → ……（此处省略一万步）。

SpringBoot 用 **Starter** 这个概念把这件事简化到了极致。啥是 Starter？你可以把它理解成一个"套餐"——想用 Redis？加个 `spring-boot-starter-data-redis` 就齐了，Redis 客户端、连接池、序列化器全都给你配好，版本也帮你协调好了。

```xml
<!-- 想用 Web 功能？一句话 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- 想用 MyBatis？也是一句话 -->
<dependency>
    <groupId>org.mybatis.spring.boot</groupId>
    <artifactId>mybatis-spring-boot-starter</artifactId>
    <version>3.0.3</version>
</dependency>
```

常用的 Starter 给大家列一哈：

| Starter | 干啥用 |
|---|---|
| spring-boot-starter-web | Web 开发（SpringMVC + Tomcat） |
| spring-boot-starter-data-jpa | JPA 数据库操作 |
| spring-boot-starter-data-redis | Redis 操作 |
| spring-boot-starter-security | 安全框架 |
| spring-boot-starter-test | 测试 |
| spring-boot-starter-validation | 参数校验 |
| spring-boot-starter-mail | 发邮件 |

**友情提示：** 官方 Starter 的命名规则是 `spring-boot-starter-xxx`，第三方的通常是 `xxx-spring-boot-starter`，记着这个规律以后找依赖不容易搞混。

## 第四步：自动配置，Bean 不用手动注册了

这个功能真的绝，必须得好好夸夸。

以前咱们用 Spring，想用个 RedisTemplate？自己写配置类。想用个 RestTemplate？自己写配置类。想用个 DataSource？更是要写一堆配置。每一个 Bean 都得手动注册，跟办证似的，一个窗口跑一趟。

SpringBoot 的自动配置（Auto-Configuration）就是——你只要引入了对应的 Starter，SpringBoot 直接帮你在启动的时候自动把相关 Bean 都注册好。用的时候直接 `@Autowired` 就完了，啥配都不用写。

```java
@RestController
public class HelloController {
    
    // RestTemplate 直接注入，不用自己配
    @Autowired
    private RestTemplate restTemplate;
    
    // DataSource 直接注入，不用自己配
    @Autowired
    private DataSource dataSource;
    
    @GetMapping("/hello")
    public String hello() {
        return "Hello, SpringBoot!";
    }
}
```

这背后的原理呢，就是 SpringBoot 的 `@EnableAutoConfiguration` 注解在启动时会扫描 classpath 下所有 jar 包里的 `spring.factories` 文件，根据你引入的依赖动态决定哪些配置要生效。理解不了的没关系哈，你只需要知道——**SpringBoot 帮你把活干了，你安心写业务就行**。

**不过捏，自动配置虽然省事，也有一个容易被忽视的问题：** 当你引入一个不熟悉的 Starter 时，可能自动注册了很多你根本不知道的 Bean，出问题的时候一脸懵逼。建议朋友们平时多看看 `spring-boot-autoconfigure` 包里的源码，知道啥被自动配了、怎么关掉不需要的自动配置：

```java
// 排除某个自动配置
@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})
public class MyApplication {
    // ...
}
```

## 第五步：配置文件大一统

传统 Spring 开发里面，数据库配置写一个文件、日志配置写一个文件、SpringMVC 配置再写一个文件……东一个西一个，找个配置跟寻宝似的。

SpringBoot 用 **application.properties**（或者 application.yml）一个文件把所有配置全管起来了。数据库、缓存、端口、日志、自定义参数……全塞一块儿，清晰明了，找啥都不用翻文件夹。

```yaml
# application.yml —— 我个人更喜欢用 yml，层级感更强
server:
  port: 9090

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/my_db
    username: root
    password: 123456
    driver-class-name: com.mysql.cj.jdbc.Driver
  
  redis:
    host: localhost
    port: 6379

# 自己定义的参数也能放这里
my-app:
  name: 我的第一个SpringBoot项目
  version: 1.0.0
```

读取自定义配置也超级简单，`@Value` 或者 `@ConfigurationProperties` 随便选：

```java
// 方式一：单个取值
@Value("${my-app.name}")
private String appName;

// 方式二：批量映射（推荐，更优雅）
@Component
@ConfigurationProperties(prefix = "my-app")
public class AppConfig {
    private String name;
    private String version;
    // getter/setter 略
}
```

> 不知道朋友们有没有纠结过 properties 和 yml 选哪个？简单说说：properties 是平铺结构，简单直接，适合配置项不多的情况；yml 是层级结构，看着更清爽，适合配置项多的时候。咱新手用哪个都行，效果一样，看自己习惯。

## 第六步：热部署，改了代码不用重启

这个功能怎么说呢，属于"有了才知道有多爽"系列。

以前开发的时候，改一行代码 → 重启项目 → 等 10 秒 → 看到效果 → 发现还要改 → 再重启 → 再等 10 秒……来来回回，时间全浪费在重启上了。

SpringBoot 的 DevTools 可以让你改了代码之后自动重启，而且这个重启比手动重启快得多，因为它是双类加载器的机制，只重新加载你写的代码，第三方依赖的 jar 不用重新加载。具体配置如下：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-devtools</artifactId>
    <scope>runtime</scope>
    <optional>true</optional>
</dependency>
```

引入之后，在 IDEA 里还需要做两件事：

1. **File → Settings → Build, Execution, Deployment → Compiler**，勾上 `Build project automatically`
2. 按 `Ctrl + Shift + Alt + /`，选 `Registry`，勾上 `compiler.automake.allow.when.app.running`

之后你每次保存代码（IDEA 里是 Ctrl+S 或者自动保存），项目就会自动重启，你只管刷新浏览器就完事了。

**不过这玩意儿也有个鸡贼的地方：** 当你的项目比较大的时候，自动重启虽然快但架不住频繁触发，CPU 库库转。这时候可以在 `application.yml` 里排除掉不需要触发重启的目录：

```yaml
spring:
  devtools:
    restart:
      exclude: static/**, public/**
```

## 第七步：Actuator，项目的体检报告

项目跑起来之后，总有一天你会想：我项目到底在跑啥？占了多少内存？有哪些 Bean 被加载了？数据库连上没？

传统做法得加日志、加监控组件，有时候还得自己写接口来看。SpringBoot 的 Actuator 直接给你整好了，加一个依赖就完事：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

启动后访问 `/actuator` 就能看到一堆监控端点，常用的有：

| 端点 | 说明 |
|---|---|
| /actuator/health | 健康检查，看项目活着没 |
| /actuator/info | 项目信息 |
| /actuator/beans | 所有加载的 Bean |
| /actuator/env | 环境配置 |
| /actuator/mappings | 所有接口映射 |

这些端点默认只开放了 health，想在开发环境全部打开的话加个配置就行：

```yaml
management:
  endpoints:
    web:
      exposure:
        include: "*"   # 开发环境全开，生产环境别这么整哈
```

**安全提醒：** 生产环境千万千万别把所有端点都暴露出去，不然敏感信息就泄露了。建议生产环境只开放 health 和 info，其他的一律关掉。

## 结尾：也就这些了

总的来说，SpringBoot 就是一个字——**懒**。它把各种繁琐的配置全帮你做了，让你能把精力集中在业务代码上，而不是在配置文件和依赖管理上反复横跳。对于新手朋友来说，SpringBoot 基本就是现在学 Java 后端开发的"必经之路"了，不像以前还得先啃一堆 XML 配置。

当然捏，SpringBoot 的简化开发远不止上面这些，还有统一异常处理、拦截器配置、定时任务、异步任务……篇幅有限就不一个一个展开说了，以后有机会再跟朋友们唠。

以上是个人的一些经验分享，如果哪里有写的不对的地方还请大佬们指正，毕竟咱也是边学边总结嘛！

本文完结撒花！！！🎉
