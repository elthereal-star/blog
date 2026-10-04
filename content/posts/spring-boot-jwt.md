---
title: "SpringBoot整合JWT，登录认证原来这么简单？"
date: 2026-05-19
draft: false
categories: ["Spring"]
tags: ["Spring Boot", "JWT", "登录认证", "安全"]
summary: "嗨朋友们，好久不见（其实也就摸了两天鱼）！最近在搓一个前后端分离的小项目，然后嘛，登录认证这东西肯定绕不开的对吧？传统那种 Session + Cookie…"
ShowToc: true
---


嗨朋友们，好久不见（其实也就摸了两天鱼）！最近在搓一个前后端分离的小项目，然后嘛，登录认证这东西肯定绕不开的对吧？传统那种 Session + Cookie 的方式在分布式场景下就有点不太够看了，于是咱就盯上了 JWT 这个玩意儿。

刚开始接触 JWT 的时候我也是一脸懵逼——啥？Token 里面还能带数据？啥？不需要在服务端存 Session？听着就很玄乎啊喂！

不过实际整了一遍之后发现，嘿，也没那么难嘛。所以今天就跟大家分享一下，**如何在 SpringBoot 项目中使用 JWT 来实现登录认证**，保证看完你也能库库地整出来 (๑•̀ㅂ•́)و✧

---

## 咱先唠唠，JWT 到底是个啥？

在动手写代码之前，得先把概念搞明白，不然就是照着教程敲完也不知道自己在写啥（别问我怎么知道的）。

### 用大白话说

想象一下你去酒店开房（咳咳，别想歪），传统的 Session 模式是这样的：

- 你到前台登记身份证，前台小姐姐把你的信息记在一个**小本本**上，然后给你一张**房卡**，房卡上面只有一个编号
- 你每次要进房间，掏出房卡刷一下，前台就得翻开小本本查：编号 007 对应的是谁？住哪个房间？住多久？

这个过程里，**小本本就是 Session**，存服务器上的。来一百个客人，小本本就记一百条。要是哪天前台换了个人（服务器重启），小本本没了，所有房卡全废。

那 JWT 的模式呢？

- 你到前台登记身份证，前台小姐姐直接把你的信息**加密后印在房卡上**（token），根本不用小本本
- 你每次来，前台看一眼房卡上印的东西，解密一下就知道你是谁了，完全不用去翻什么小本本

**服务器不用存任何东西，全靠 token 本身携带的信息来验证身份**，这就是 JWT 的核心思想。是不是一下子就好理解了？

### 稍微专业一点说

JWT（JSON Web Token）本质上是一个字符串，由三部分组成，用 `.` 分隔：

```
header.payload.signature
```

- **Header**（头部）：标注了这个 token 用的是什么算法（一般是 HS256）
- **Payload**（载荷）：存数据的地方，比如用户 ID、用户名、过期时间等。**注意，这部分只是 Base64 编码，不是加密！** 所以千万别把密码之类的敏感信息塞进去
- **Signature**（签名）：用 Header 里指定的算法，把 Header + Payload + 一个只有服务器知道的密钥（secret）一起算出一个签名，用来防止 token 被篡改

{{< svg "jwt-structure" >}}

**整体流程大概是酱紫：**

1. 用户登录，服务器验证账号密码
2. 验证通过，服务器生成一个 JWT 返回给客户端
3. 客户端把这个 JWT 存起来（一般是 localStorage）
4. 以后每次请求，客户端在请求头里带上这个 JWT
5. 服务器拦截请求，解析 JWT 验证合法性
6. 合法就放行，不合法就返回 401

{{< svg "jwt-login-flow" >}}

好了，概念捋清楚了，咱开始整代码！

---

## 第一步：准备工作，搭个项目

咱直接用 Spring Initializr 整个空项目，需要的依赖如下：

```xml
<!-- pom.xml 核心依赖 -->
<dependencies>
    <!-- SpringBoot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>

    <!-- SpringBoot Security，做安全认证的核心 -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>

    <!-- JWT 工具库，咱用 jjwt，简单好使 -->
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.12.5</version>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId>
        <version>0.12.5</version>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-jackson</artifactId>
        <version>0.12.5</version>
        <scope>runtime</scope>
    </dependency>

    <!-- MyBatis-Plus，操作数据库猛猛的方便 -->
    <dependency>
        <groupId>com.baomidou</groupId>
        <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
        <version>3.5.7</version>
    </dependency>

    <!-- MySQL 驱动 -->
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <scope>runtime</scope>
    </dependency>

    <!-- Lombok，告别 getter/setter 地狱 -->
    <dependency>
        <groupId>org.projectlombok</groupId>
        <artifactId>lombok</artifactId>
        <optional>true</optional>
    </dependency>
</dependencies>
```

> **小贴士**：jjwt 从 0.12.x 版本开始把包拆成了 api、impl、jackson 三个，如果用旧版本（0.11.x）只需要一个依赖就行。如果你在网上看到只有一个依赖的教程，那大概率是老版本的写法，别慌，都能用！

配置文件 `application.yml` 先来个基础的：

```yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/your_database?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
    username: root
    password: your_password
    driver-class-name: com.mysql.cj.jdbc.Driver

# JWT 相关配置，集中管理好习惯
jwt:
  # 密钥，生产环境务必用一个又长又复杂的字符串！
  secret: b3d8a9f1c2e4d6a8b0c2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4c6d8e0f2a4b6
  # 过期时间，单位毫秒，这里设了 24 小时
  expiration: 86400000
```

**这里要重点提醒一下**：`jwt.secret` 这个密钥千万别用短的、也别提交到公共仓库！HS256 算法要求密钥至少 256 位（32 字节），太短的话 jjwt 会直接给你抛异常。上面那个是我随便搓的，你们自己换一个。

{{< svg "deploy-pipeline" >}}

---

## 第二步：整一个 JWT 工具类

这个工具类是整个 JWT 操作的核心，负责生成 token、解析 token、验证 token 三大操作。咱把它封装好，后面用起来就方便了。

```java
package com.example.demo.utils;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Map;

@Component
public class JwtUtils {

    // 从配置文件读取密钥和过期时间
    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration}")
    private long expiration;

    /**
     * 生成 JWT token
     * @param claims  要存进 token 的数据（用户ID、用户名啥的）
     * @return token 字符串
     */
    public String generateToken(Map<String, Object> claims) {
        SecretKey key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));

        return Jwts.builder()
                .claims(claims)                    // 设置载荷数据
                .issuedAt(new Date())              // 签发时间
                .expiration(new Date(System.currentTimeMillis() + expiration))  // 过期时间
                .signWith(key)                     // 签名
                .compact();                        // 打包成最终字符串
    }

    /**
     * 从 token 中解析出 claims 数据
     * @param token JWT token
     * @return claims 数据
     */
    public Claims parseToken(String token) {
        SecretKey key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));

        return Jwts.parser()
                .verifyWith(key)    // 用同一个密钥验证
                .build()
                .parseSignedClaims(token)  // 解析
                .getPayload();       // 拿到载荷
    }

    /**
     * 验证 token 是否合法（有没有被篡改、有没有过期）
     * @param token JWT token
     * @return true 表示合法，false 表示不合法
     */
    public boolean validateToken(String token) {
        try {
            parseToken(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            // JwtException：签名不对、过期等
            // IllegalArgumentException：token 为空等
            return false;
        }
    }
}
```

简单解释一下这几个方法在干啥：

- **generateToken**：咱们往里面传一个 Map，存上用户 ID、用户名这些信息，它给你生成一个 token 串，顺便设好过期时间
- **parseToken**：把 token 解开来，拿出里面的数据。如果 token 被篡改过或者过期了，这里会直接抛异常
- **validateToken**：就是判断 token 合不合法，本质上就是调 parseToken，能解析成功就合法，抛异常就不合法

> **踩坑预警**：jjwt 0.12.x 版本的 API 跟 0.11.x 变化挺大的！老版本用 `Jwts.parser().setSigningKey(key).parseClaimsJws(token)`，新版本变成了链式调用 `Jwts.parser().verifyWith(key).build().parseSignedClaims(token)`。如果你照着老教程写发现方法找不到，多半是版本问题 (╯‵□′)╯︵┻━┻

---

## 第三步：搞一个 JWT 过滤器

有了生成和解析 token 的能力之后，咱们需要搞一个**过滤器**，在每个请求到达 Controller 之前先拦截下来，看看请求里有没有带合法的 token。

这就好比每个进小区的人，保安大叔都要看一下你的门禁卡，卡有效才放行。

```java
package com.example.demo.filter;

import com.example.demo.utils.JwtUtils;
import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.ArrayList;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtUtils jwtUtils;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        // 从请求头里拿 token，一般是 "Authorization: Bearer xxx"
        String authHeader = request.getHeader("Authorization");

        // 没带 token，直接放行（后续 Security 配置会决定哪些接口必须认证）
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        // 把 "Bearer " 前缀去掉，拿到真正的 token
        String token = authHeader.substring(7);

        // 验证 token 合法性
        if (!jwtUtils.validateToken(token)) {
            filterChain.doFilter(request, response);
            return;
        }

        // 解析出用户信息
        Claims claims = jwtUtils.parseToken(token);
        String userId = claims.get("userId", String.class);
        String username = claims.get("username", String.class);

        // 把用户信息封装成 Spring Security 能识别的认证对象
        UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(userId, null, new ArrayList<>());

        // 塞到 Security 上下文里，这样后续的 Controller 就能拿到当前用户信息了
        SecurityContextHolder.getContext().setAuthentication(authentication);

        // 继续走下一个过滤器
        filterChain.doFilter(request, response);
    }
}
```

这个过滤器做这几件事：

1. 从请求头的 `Authorization` 字段里取出 token（格式是 `Bearer xxx`）
2. 验证 token 合不合法
3. 合法的话解析出用户信息，塞进 Spring Security 的上下文
4. 不管合不合法，都继续往下走（具体哪些接口需要认证，我们在 Security 配置里管）

> **这里有个容易踩的坑**：`OncePerRequestFilter` 确保一个请求只会经过这个过滤器一次，就算请求内部发生了转发也不会重复执行，比直接实现 `Filter` 接口更稳妥。

---

## 第四步：配置 Spring Security

Spring Security 这玩意儿配置起来确实有点绕，不过咱只做 JWT 登录认证的话，配置其实不复杂。核心思路就是：**关掉默认的表单登录和 Session，注册咱们自己写的 JWT 过滤器**。

```java
package com.example.demo.config;

import com.example.demo.filter.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 关闭 CSRF，前后端分离 + JWT 用不着
            .csrf(csrf -> csrf.disable())

            // 不创建 Session，JWT 本身就是无状态的
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

            // 配置接口权限
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/user/login", "/api/user/register").permitAll()  // 登录注册不需要认证
                .anyRequest().authenticated()  // 其他接口全部需要认证
            )

            // 把咱的 JWT 过滤器加到 UsernamePasswordAuthenticationFilter 前面
            .addFilterBefore(jwtAuthenticationFilter,
                             UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        // 密码加密器，BCrypt 是目前业界主流选择
        return new BCryptPasswordEncoder();
    }
}
```

这里有几个点说一下哈：

- **关 CSRF**：CSRF 攻击主要针对的是 Cookie + Session 模式，咱们用 JWT、token 放在请求头里，不存在 CSRF 的问题，关掉就完事了
- **STATELESS**：无状态策略，Spring Security 不会创建 HttpSession，也不会用 Session 来存 SecurityContext。每次请求都是独立的，全靠 JWT 来识别身份
- **addFilterBefore**：把咱们的 JWT 过滤器放在 `UsernamePasswordAuthenticationFilter` 之前执行，这样 JWT 认证完了之后，Spring Security 就知道当前用户是谁了
- **密码加密**：**千万千万不要明文存密码啊朋友们！** BCrypt 是目前最主流的选择，它自带盐值，同一个密码两次加密出来的结果都不一样，安全性杠杠的


---

## 第五步：写登录接口

终于到了大家最关心的部分——登录接口咋写！其实有了上面的铺垫，登录接口就特别简单了：

```java
package com.example.demo.controller;

import com.example.demo.entity.User;
import com.example.demo.service.UserService;
import com.example.demo.utils.JwtUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private JwtUtils jwtUtils;

    /**
     * 登录接口
     */
    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody Map<String, String> loginData) {
        String username = loginData.get("username");
        String password = loginData.get("password");

        Map<String, Object> result = new HashMap<>();

        // 查数据库，验证用户名密码
        User user = userService.login(username, password);

        if (user == null) {
            result.put("code", 401);
            result.put("message", "用户名或密码错误捏~");
            return result;
        }

        // 生成 JWT，把用户信息存进去
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", user.getId());
        claims.put("username", user.getUsername());
        String token = jwtUtils.generateToken(claims);

        result.put("code", 200);
        result.put("message", "登录成功！");
        result.put("token", token);

        return result;
    }
}
```

Service 层的登录逻辑也很直白：

```java
package com.example.demo.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.demo.entity.User;
import com.example.demo.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private PasswordEncoder passwordEncoder;

    public User login(String username, String password) {
        // 根据用户名查用户
        User user = userMapper.selectOne(
            new LambdaQueryWrapper<User>().eq(User::getUsername, username)
        );

        if (user == null) {
            return null;
        }

        // 用 BCrypt 比对密码（user.getPassword() 是数据库中加密后的密码）
        if (!passwordEncoder.matches(password, user.getPassword())) {
            return null;
        }

        return user;
    }
}
```

登录接口就是：接收用户名密码 → 查数据库验证 → 验证通过就生成 token 返回。逻辑清晰得很，没啥复杂的。

> **提醒一下**：返回给前端的 token，前端记得存在 `localStorage` 里，然后每次请求在请求头里带上 `Authorization: Bearer <token>`。如果是用 axios，可以直接配一个请求拦截器统一处理，就不用每个请求都手动加了。

---

## 第六步：注册接口也得整一个

光有登录不行啊，没有注册哪来的用户对吧？

```java
@PostMapping("/register")
public Map<String, Object> register(@RequestBody Map<String, String> registerData) {
    String username = registerData.get("username");
    String password = registerData.get("password");

    Map<String, Object> result = new HashMap<>();

    // 检查用户名是否已存在
    User existUser = userService.findByUsername(username);
    if (existUser != null) {
        result.put("code", 400);
        result.put("message", "这个用户名已经被占用了，换一个吧~");
        return result;
    }

    // 创建用户，密码加密存储
    User user = new User();
    user.setUsername(username);
    user.setPassword(passwordEncoder.encode(password));  // 加密！加密！加密！
    userService.save(user);

    result.put("code", 200);
    result.put("message", "注册成功，快去登录吧 (๑•̀ㅂ•́)و✧");
    return result;
}
```

**再次强调**：`passwordEncoder.encode(password)` 这步不能省！你要是直接 `user.setPassword(password)` 明文存进去，那数据库一泄露，全部用户的密码就都裸奔了，真的会谢 (；′⌒`)

---

## 第七步：搞一个获取当前用户信息的接口

用户登录之后，前端肯定需要展示一下"你好，xxx"之类的，咱得提供一个接口来获取当前登录用户的信息：

```java
@GetMapping("/info")
public Map<String, Object> getUserInfo() {
    Map<String, Object> result = new HashMap<>();

    // 从 Security 上下文中取出认证信息（就是咱们在过滤器里塞进去的那个）
    Object principal = SecurityContextHolder.getContext()
                            .getAuthentication().getPrincipal();

    // principal 就是咱们在过滤器里存进去的 userId
    String userId = (String) principal;

    User user = userService.getById(userId);

    result.put("code", 200);
    result.put("data", user);
    return result;
}
```

这样前端一调 `/api/user/info` 就能拿到当前用户的信息了。这个接口经过了 JWT 过滤器，Security 上下文里已经有用户 ID 了，直接取就行。

---

## 补充一些你可能关心的问题

### Token 过期了咋整？

咱们在配置文件里设了 `expiration: 86400000`（24 小时），过期之后 token 就失效了。一般来说有两种处理方式：

1. **简单粗暴型**：过期了就弹回登录页，让用户重新登录
2. **体验优化型**：搞个 refresh token 机制，access token 过期了用 refresh token 去换一个新的。这个方案更复杂一些，新手可以先不管，等后面有需要了再整

对于大多数小项目来说，24 小时过期够用了，大不了设长一点嘛。不过也别太久，token 一旦签发出去在过期之前是无法主动失效的（除非你引入黑名单机制），安全性和便利性总要有个权衡的。

### 用户登出怎么处理？

JWT 的一个"缺点"就是没法在服务端主动让一个 token 失效，因为服务器没存任何状态嘛。解决方案有几种：

- **前端直接删掉 token**：最简单的做法，用户点退出就把 localStorage 里的 token 清了。但这样 token 本身还是有效的（在过期时间之前），如果有人拿到了这个 token 还是能用
- **Redis 黑名单**：在服务端搞个 Redis，把要废弃的 token 存进去，过滤器里多一步检查 token 在不在黑名单中。这个方案比较稳妥，但引入了额外的复杂度

对于大部分项目，方案一就够用了。如果对安全性要求比较高的话（比如金融类应用），考虑方案二。

### 每次请求都解析 JWT 会不会很慢？

放心，JWT 解析只是做 Base64 解码和 HMAC 签名验证，速度是非常快的，基本不会成为性能瓶颈。除非你的 QPS 达到了非常恐怖的数量级（比如几十万），那时候你已经是架构师大佬了，不需要看我这篇文章了 (๑•́ ₃ •̀๑)

---

## 总结一下

好啦，到这里一个完整的 SpringBoot + JWT 登录认证就整完了。来捋一捋咱干了啥：

1. 引入 jjwt 依赖，准备好工具
2. 写了个 `JwtUtils` 工具类来生成和解析 token
3. 整了个 `JwtAuthenticationFilter` 过滤器拦截请求
4. 配置了 Spring Security，关掉 Session，注册 JWT 过滤器
5. 写了登录和注册接口
6. 搞了个获取当前用户信息的接口

整个流程其实不复杂，核心就是：**登录时发 token，请求时带 token，过滤器验证 token**，完事！

当然这只是最基础的实现，实际项目中可能还需要考虑角色权限控制、token 刷新、多端登录互踢等进阶需求，但万变不离其宗，把基础搞明白了，后面的都好说。

以上是个人的一些经验分享，如果有哪里有什么错误的地方也请大佬们指出，咱一起学习一起进步~

本文完结撒花！！！✿✿ヽ(°▽°)ノ✿

---

*文中图片链接需要自行替换为实际截图哦~*
