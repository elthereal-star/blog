---
title: "HTTP Client 到底是个啥？让咱的 Java 也能丝滑地发送网络请求"
date: 2026-05-31
draft: false
categories: ["网络"]
tags: ["HTTP", "HTTPClient", "Java", "网络编程"]
summary: "不知道大伙儿刚开始学 Java 的时候有没有经历过这种尴尬——想调用一个第三方 API 接口，去网上搜\"Java 发送 HTTP 请求\"，出来的结果五花八门…"
ShowToc: true
---


不知道大伙儿刚开始学 Java 的时候有没有经历过这种尴尬——想调用一个第三方 API 接口，去网上搜"Java 发送 HTTP 请求"，出来的结果五花八门：有 `HttpURLConnection` 的、有 `HttpClient`（Apache 那个老古董）的、有 `RestTemplate` 的、有 `OkHttp` 的……好家伙，到底用哪个啊？！

更要命的是，点开一看 `HttpURLConnection` 的示例代码，光是打开连接、设置请求头、读取响应流、关闭连接这一套操作就二十几行，还是那种又臭又长的样板代码 (_)

```
URL url = new URL("https://api.example.com/data");
HttpURLConnection conn = (HttpURLConnection) url.openConnection();
conn.setRequestMethod("GET");
conn.setRequestProperty("Accept", "application/json");
conn.setConnectTimeout(5000);
conn.setReadTimeout(5000);
int responseCode = conn.getResponseCode();
BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
String inputLine;
StringBuilder response = new StringBuilder();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
// 还得各种 try-catch 和 finally 关流...要老命了 (꒦ິ⌓꒦ີ)
```

十几行代码就为了发一个 GET 请求，咱是来写业务的，不是来写网络底层通信的好吗！

于是乎，**Java 11 之后，Oracle 终于看不下去这种乱象了，直接把一个现代化的 `java.net.http.HttpClient` 塞进了 JDK！**

---

## HttpClient 是个啥？

用一句话概括：**`java.net.http.HttpClient` 是 JDK 11 开始内置的一个现代化 HTTP 通信库，让我们能用极简的 API 去发送同步/异步的 HTTP 请求。**

它有啥牛皮的地方？咱掰指头数一数：

- **JDK 原生自带**，不用引入任何第三方依赖
- **支持 HTTP/2 和 WebSocket**
- **内置同步和异步两种模式**，想咋玩就咋玩
- **链式调用**，代码读起来跟说话似的
- **响应式 Stream 支持**，处理大文件下载不费劲
- **原生支持 JSON/XML/文本** 等各种格式

如果说以前用 `HttpURLConnection` 发请求像是在手摇拖拉机，那用 `HttpClient` 就像开特斯拉——踩油门就走，还带自动驾驶的那种～ ヾ(≧▽≦*)o

> Java 11 之前的 `java.net.HttpURLConnection` 是上世纪的设计，API 设计反人类（单连接默认不能复用、异常处理一坨、还不支持 HTTP/2），而 Apache 的 `HttpClient` 虽然功能强但太重了。Oracle 痛定思痛，终于在 JDK 9 孵化 `jdk.incubator.httpclient`，JDK 11 正式转正为 `java.net.http.HttpClient`。咱现在用的就是它！

---

## 先来感受一下它的丝滑

话不多说，直接上一个最简单的 GET 请求：

```java
// JDK 11+ 自带的，不用加任何依赖！
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

// 创建一个 HttpClient 实例
HttpClient client = HttpClient.newHttpClient();

// 构建一个请求
HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.github.com/users/octocat"))
        .header("Accept", "application/json")
        .GET()
        .build();

// 发送请求并拿到响应
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

System.out.println("状态码：" + response.statusCode());
System.out.println("响应体：" + response.body());
```

十来行代码，整个过程清清爽爽——**创建客户端 → 构建请求 → 发送 → 拿到响应**，每一步在干啥一眼就能看懂，还要啥自行车？

跟前面 `HttpURLConnection` 那一大坨比起来，是不是瞬间感觉世界美好了？(。-`ω′-)

---

## 咱来细品 HttpClient 的三大核心

HttpClient 的 API 设计围绕着三个核心类展开，它们仨配合起来就是一个完整的"发请求流水线"：

### HttpRequest —— "你要发给谁，带什么话"

`HttpRequest` 负责定义你的请求长啥样——URL、请求方法、请求头、请求体，它全管了。用的是经典的 **Builder 模式**，一路 `.` 到底：

```java
HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/users"))
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer your-token-here")
        .timeout(Duration.ofSeconds(10))  // 超时时间，超了10秒还没响应该抛异常就抛
        .POST(HttpRequest.BodyPublishers.ofString(jsonBody))  // POST请求带JSON体
        .build();
```

支持的方法：
- `.GET()` —— 查
- `.POST(body)` —— 增
- `.PUT(body)` —— 改
- `.DELETE()` —— 删
- `.method("PATCH", body)` —— 自定义方法（比如 PATCH）

### HttpClient —— "谁来帮你传话"

`HttpClient` 就是那个跑腿的。它管理着底层的连接池、线程、超时、代理、认证这些脏活累活：

```java
HttpClient client = HttpClient.newBuilder()
        .version(HttpClient.Version.HTTP_2)   // 优先用 HTTP/2
        .connectTimeout(Duration.ofSeconds(5)) // 连接超时
        .followRedirects(HttpClient.Redirect.NORMAL) // 自动跟随重定向
        .proxy(ProxySelector.of(new InetSocketAddress("proxy.company.com", 8080))) // 代理
        .authenticator(Authenticator.getDefault()) // 认证
        .build();
```

**重要的是，`HttpClient` 是线程安全的，整个应用共用一个实例就行**，不用每次发请求都 new 一个，它会自动管理连接池和复用连接，性能拉满。

### HttpResponse —— "对方回了啥话"

`HttpResponse` 就是你拿到的回信——状态码、响应头、响应体，该有的都有：

```java
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

System.out.println(response.statusCode());   // 200, 404, 500...
System.out.println(response.headers().map()); // 响应头
System.out.println(response.body());          // 响应体（字符串）
System.out.println(response.uri());           // 最终请求的URI（可能有重定向）
```

`BodyHandlers` 提供了好几种处理响应体的方式：

| BodyHandler | 返回类型 | 适用场景 |
|---|---|---|
| `ofString()` | `String` | 响应体不大的文本/JSON |
| `ofByteArray()` | `byte[]` | 二进制数据，比如图片缩略图 |
| `ofFile(Path)` | `Path` | 直接把响应体写到磁盘文件 |
| `ofInputStream()` | `InputStream` | 大文件流式处理 |
| `ofLines()` | `Stream<String>` | 逐行处理响应体 |
| `discarding()` | `Void` | 不关心响应体，只关心状态码 |

这个 `ofFile()` 特别好用——下载文件直接一行代码把响应体怼到硬盘，不用自己开流写文件，真的爽到飞起 ヽ(✿ﾟ▽ﾟ)ノ

---

## 同步 vs 异步，两种打开方式

### 同步模式：先发了再说，等着拿结果

上面的例子都是同步的 `client.send()`，就是发完请求后**卡住当前线程**，等服务器回信了再继续往下走：

```java
// send() 是同步的，会阻塞等待
HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
// 这行代码要等上面拿到响应后才会执行
System.out.println(response.body());
```

**适用场景：** 那种需要拿到返回结果才能继续往下走的逻辑。比如查用户信息、调支付接口这种链路强依赖的。

### 异步模式：发出去就不管了，回了再说

`client.sendAsync()` 发完请求立马返回，不耽误当前线程继续干活。等响应回来了，自动触发回调处理：

```java
// sendAsync() 是异步的，不阻塞，返回 CompletableFuture
CompletableFuture<HttpResponse<String>> future = client.sendAsync(
        request,
        HttpResponse.BodyHandlers.ofString()
);

future.thenApply(HttpResponse::body)        // 拿到响应体
      .thenAccept(System.out::println)      // 打印出来
      .exceptionally(e -> {                 // 出了异常也有兜底
          System.err.println("请求炸了：" + e.getMessage());
          return null;
      });

// 这里的代码会立即执行，不会等请求回来
System.out.println("请求已发出，我先干别的去了...");

// 如果需要等异步请求完成，再调用 join()
future.join();
```

**适用场景：** 批量调用多个不相关的接口、发消息通知这种"发出去就行不急着拿结果"的场景。多个异步请求可以用 `CompletableFuture.allOf()` 组合，并发发出等全部回来再汇总处理，效率库库提升！

> 打个比方：**同步就是你打电话，对方没接你只能在电话这头干等着；异步就是你发微信语音，发完你可以继续打游戏，对面回复了你再看就行。**

---

## 实际应用场景：HttpClient 能帮咱干啥？

理论知识整得差不多了，来看看实际项目里 HttpClient 都能在哪些地方发光发热。

### 场景一：调用第三方 API

这是最最常见的使用场景——对接微信支付、阿里云短信、GitHub API、天气接口等各路第三方服务：

```java
@Component
public class WeChatService {

    private final HttpClient client = HttpClient.newHttpClient();

    public String getAccessToken(String appId, String appSecret) {
        String url = "https://api.weixin.qq.com/cgi-bin/token"
                + "?grant_type=client_credential"
                + "&appid=" + appId
                + "&secret=" + appSecret;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .GET()
                .timeout(Duration.ofSeconds(10))
                .build();

        try {
            HttpResponse<String> response = client.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );

            if (response.statusCode() == 200) {
                // 解析 JSON 拿到 access_token
                return parseAccessToken(response.body());
            }
            throw new RuntimeException("获取 token 失败，状态码：" + response.statusCode());
        } catch (Exception e) {
            throw new RuntimeException("请求微信接口异常", e);
        }
    }
}
```

### 场景二：微服务之间互相调用

在微服务架构里，服务 A 要调服务 B 的接口，如果不想引入 Feign/Dubbo 等重量级框架，HttpClient 就是最轻量的选择：

```java
@Service
public class OrderService {

    private final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    public UserDTO getUserInfo(Long userId) {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://user-service/api/users/" + userId))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();

        try {
            HttpResponse<String> response = client.send(
                    request,
                    HttpResponse.BodyHandlers.ofString()
            );
            // 把 JSON 字符串转成 UserDTO
            return objectMapper.readValue(response.body(), UserDTO.class);
        } catch (Exception e) {
            log.error("调用用户服务失败，userId={}", userId, e);
            return null; // 或者走降级逻辑
        }
    }
}
```

> 当然如果你们的服务间调用特别多，还是建议用 Feign 或者 Dubbo 这类专业的 RPC 框架，HttpClient 适合那种偶尔调一下的轻量场景，各有各的适用地儿，不用强行套～

### 场景三：并发批量请求

需要同时调好几个不相关的接口？异步模式走起，并发效率拉满：

```java
public Map<String, Object> aggregateData() {
    HttpClient client = HttpClient.newHttpClient();

    // 三个请求同时发出去
    CompletableFuture<String> userFuture = client.sendAsync(
            HttpRequest.newBuilder().uri(URI.create("http://api/users/123")).GET().build(),
            HttpResponse.BodyHandlers.ofString()
    ).thenApply(HttpResponse::body);

    CompletableFuture<String> orderFuture = client.sendAsync(
            HttpRequest.newBuilder().uri(URI.create("http://api/orders/123")).GET().build(),
            HttpResponse.BodyHandlers.ofString()
    ).thenApply(HttpResponse::body);

    CompletableFuture<String> productFuture = client.sendAsync(
            HttpRequest.newBuilder().uri(URI.create("http://api/products/hot")).GET().build(),
            HttpResponse.BodyHandlers.ofString()
    ).thenApply(HttpResponse::body);

    // 等三个都回来，汇总数据
    CompletableFuture.allOf(userFuture, orderFuture, productFuture).join();

    Map<String, Object> result = new HashMap<>();
    result.put("user", userFuture.join());
    result.put("orders", orderFuture.join());
    result.put("products", productFuture.join());
    return result;
}
```

**原来串行三次调用可能要 1.5 秒，并发发出只要 0.5 秒**，这就是异步的魅力！

### 场景四：文件下载

HttpClient 的 `ofFile()` 让文件下载变得贼简单：

```java
public void downloadFile(String fileUrl, String savePath) throws Exception {
    HttpClient client = HttpClient.newHttpClient();

    HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(fileUrl))
            .GET()
            .build();

    // 直接把响应体写到本地文件！一行代码！不需要手动开流！
    HttpResponse<Path> response = client.send(
            request,
            HttpResponse.BodyHandlers.ofFile(Path.of(savePath))
    );

    System.out.println("下载完毕，文件路径：" + response.body());
}
```

以前用 `HttpURLConnection` 下载文件得手写几十行的流拷贝代码，现在一行 `ofFile()` 直接带走，懒人狂喜 ٩(ˊᗜˋ*)و

### 场景五：发送 Webhook 通知

有些场景你只需要把消息推送出去，不需要等结果——异步发送，发完就走：

```java
public void sendWebhook(String webhookUrl, String message) {
    String jsonBody = "{\"content\": \"" + message + "\"}";

    HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(webhookUrl))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .build();

    HttpClient.newHttpClient().sendAsync(request, HttpResponse.BodyHandlers.discarding())
            .thenRun(() -> log.info("Webhook 发送成功"))
            .exceptionally(e -> {
                log.error("Webhook 发送失败", e);
                return null;
            });
    // 发完立马返回，不耽误主逻辑
}
```

---

## HttpClient vs 其他方案，到底该选哪个？

Java 生态里发 HTTP 请求的方案有好几种，可能有些朋友会懵——到底选哪个啊？

咱来盘一盘：

| 方案 | 优点 | 缺点 | 推荐场景 |
|---|---|---|---|
| **java.net.http.HttpClient** | JDK 自带零依赖，原生 HTTP/2，API 优雅，异步支持丝滑 | 需要 JDK 11+，生态不如老牌的丰富 | JDK 11+ 项目首选 |
| **RestTemplate** | Spring 自带，同步阻塞式，学习成本低 | Spring 5 后进入维护模式，不再更新了 | 老项目维护，新项目不建议 |
| **WebClient** | Spring 官方推荐的 RestTemplate 替代品，响应式，非阻塞 | 需要 Spring WebFlux 依赖，同步场景下有点小重 | Spring 响应式项目或新 Spring 项目 |
| **OkHttp** | 老牌健将，API 优雅，连接池强大，Android 首选 | 第三方依赖，多了一个 Jar | Android 开发、JDK 8 项目 |
| **Apache HttpClient** | 功能强大到爆炸，连接管理、重试策略、连接池…只有你想不到 | 太重了，API 不够直观，学习曲线陡峭 | 需要复杂 HTTP 特性的企业级项目 |

**一句话建议：JDK 11+ 的项目直接用 `java.net.http.HttpClient`，JDK 8 的用 OkHttp，Spring WebFlux 项目的用 WebClient。**

不过话说回来，如果是 Spring Boot 项目且你只需要简单地调一下 REST 接口，`RestTemplate` 虽然进维护模式了但其实还能用，也不用因为追新就非得换。还是那句话——**合适的才是最好的，不用强行追新** ～ (。-`ω´-)

---

## 小心这些坑！提前预警不翻车

### 坑一：记得设置超时时间

**默认情况下 HttpClient 是没有超时时间的！** 你没看错，如果你不手动设置 `timeout()`，一个请求可能永远卡在那等你到天荒地老。

```java
// 请求级别设置超时
HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://slow-api.com/data"))
        .timeout(Duration.ofSeconds(10))  // 就这一行，省心！
        .GET()
        .build();

// 客户端级别也建议设置连接超时
HttpClient client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(5))  // 连接超时
        .build();
```

**请求级别的 `timeout()` 管的是整个请求的响应超时，客户端级别的 `connectTimeout()` 只管 TCP 连接建立的超时**，两个都配上才靠谱。

### 坑二：HttpClient 要复用，不要每次 new

`HttpClient` 底层维护着连接池和线程池，它是设计成单例使用的。如果每次发请求都 `new` 一个，连接复用就废了，性能掉一大截。

```java
// 推荐：全局单例
@Component
public class HttpClientConfig {
    @Bean
    public HttpClient httpClient() {
        return HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }
}
```

### 坑三：异步请求不要忘记异常处理

`sendAsync()` 返回的是 `CompletableFuture`，如果你不 `.exceptionally()` 或者 `.join()` 之后不 `try-catch`，异常就被悄咪咪地吞掉了——任务失败了你还乐呵呵地以为成功了，这就很鸡贼啊！

```java
// 这样写异常会被静默吞掉
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
      .thenApply(HttpResponse::body)
      .thenAccept(System.out::println);
// 上面如果请求超时或者连不上，啥也不会打印，你都不知道出问题了

// 正确姿势：加上异常处理
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
      .thenApply(HttpResponse::body)
      .thenAccept(System.out::println)
      .exceptionally(e -> {
          log.error("异步请求炸了", e);
          return null;
      });
```

### 坑四：POST 请求别忘了设置 Content-Type

这个属于常见的疏忽——POST 请求带了 JSON 请求体但忘了设置 `Content-Type: application/json`，结果对面服务器解析不了（有些服务器甚至直接返回 415）。

```java
// 正确的 POST JSON 写法
HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/users"))
        .header("Content-Type", "application/json")  // 别忘了！别忘了！别忘了！
        .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
        .build();
```

---

## 总结一下

来盘一盘 `java.net.http.HttpClient` 给我们带来的好处：

1. **JDK 原生自带，零依赖开箱即用**：Java 11 以上直接用，不用纠结选哪个第三方库
2. **API 设计优雅**：Builder 模式 + 链式调用，读代码跟读句子一样流畅，再也不用写样板代码了
3. **同步异步双模式**：同步简单直接，异步性能拉满，想用哪个用哪个
4. **原生支持 HTTP/2 和 WebSocket**：跟上了时代，不再是老古董
5. **响应体处理灵活**：String、byte[]、File、Stream……各种姿势都能接住

说白了，以前咱 Java 发 HTTP 请求是一件让人头疼的事——要么用 `HttpURLConnection` 写一堆样板代码，要么引入第三方的重量级库。Java 11 的 `HttpClient` 把这个痛处直接治好了，让发 HTTP 请求变成了一件轻松愉快的事。

当然，如果你是 JDK 8 的项目还不打算升级，那就老老实实上 OkHttp 吧，那个在 JDK 8 之下是体验最好的选择了～

---

以上是个人的一些经验分享，希望能帮到正在跟 HTTP 请求斗智斗勇的朋友们 (〃'▽'〃)

如果哪里有写的不对的地方也请大佬们指出，大家一起学习进步！

**本文完结撒花！！！🎉🌸**
