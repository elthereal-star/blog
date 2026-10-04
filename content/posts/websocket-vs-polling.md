---
title: "还在用HTTP轮询？WebSocket让你前后端实时\"贴贴\"不香吗？"
date: 2026-05-25
draft: false
categories: ["网络"]
tags: ["WebSocket", "长连接", "实时通信", "轮询"]
summary: "咱就是说，做Web开发的朋友肯定都遇到过这种需求：聊天消息要实时推送、股票数据要实时刷新、多人在线协作要实时同步……这时候如果你还搁那用HTTP轮询疯狂发请…"
ShowToc: true
---


咱就是说，做Web开发的朋友肯定都遇到过这种需求：聊天消息要实时推送、股票数据要实时刷新、多人在线协作要实时同步……这时候如果你还搁那用HTTP轮询疯狂发请求，服务端估计已经在后台骂骂咧咧了（笑）。

今天咱就来聊聊这个让前后端能"随时随地保持通话"的狠角色——**WebSocket**。

## WebSocket到底是个啥？一个接地气的比喻

打个比方哈：

- **HTTP** 就像是你给快递站打电话——"喂？我的快递到了没？"（发送请求），快递站说"还没"（返回响应），你就得挂了。过一会你又打过去问，反反复复...每次都得你先主动打电话，对方才能告诉你东西。你要是忘了问，人家也不会主动通知你。

- **WebSocket** 就像是加了个微信好友——互加好友之后，你想起来了就发条消息问问，快递站有消息了也能直接推给你，**双方随时都能给对方发消息**，不用每次都"重新认识"一遍。

说白了，WebSocket就是一个**全双工通信协议**，让浏览器和服务器之间建立一个持久连接，两边都可以随时给对方发消息，不用再"你问我答"那么死板。

{{< svg "websocket-vs-http" >}}

## 没有WebSocket之前，我们都是怎么凑合的？

在WebSocket出现之前，咱想搞实时通信，就只有这几种"歪门邪道"：

### 轮询（Polling）

说白了就是**疯狂骚扰服务器**。前端每隔几秒发一个HTTP请求问"有新消息吗？"，不管有没有新消息都得发。这就像你每隔5秒打电话问快递站"到了吗到了吗到了吗"，快递员怕不是想顺着网线过来打你。

```javascript
// 轮询：每隔3秒问一次，服务器想打人
setInterval(() => {
  fetch('/api/messages')
    .then(res => res.json())
    .then(data => {
      // 有新消息就更新页面
    });
}, 3000);
```

问题也很明显：
- **浪费流量**：大部分请求都返回"没有新消息"
- **延迟高**：消息实时性取决于轮询间隔，间隔短了服务器压力大，间隔长了消息延迟高
- **连接开销大**：每次请求都要建立TCP连接、带上一大堆HTTP头

### 长轮询（Long Polling）

这个稍微聪明点了，请求发过去之后，服务器**hold住不回复**，等有消息了再回复。但本质上还是HTTP，连接断了之后还得重新建立。

**这俩方案都有个致命问题**：服务器不能主动给前端发消息，必须等前端先来问。这在实际场景中有多蛋疼，做过实时聊天的朋友都懂。

## WebSocket：让前后端"双向奔赴"

WebSocket的连接建立过程其实蛮有意思的，它是从HTTP"升级"过来的：

### 第一步：握手——先走个HTTP过场

客户端先发一个HTTP请求，但这个请求比较特殊，头上写着"我想升级成WebSocket"：

```javascript
// 前端发起WebSocket连接，就这么简单
const socket = new WebSocket('ws://localhost:8080/chat');

socket.onopen = () => {
  console.log('连接上了！咱可以开始唠了');
};

socket.onmessage = (event) => {
  console.log('服务器发来消息：', event.data);
};

socket.onclose = () => {
  console.log('连接断了，可能是网不好或者服务器关了');
};

socket.onerror = (error) => {
  console.log('出错了捏：', error);
};
```

浏览器会在背后发这么一个HTTP请求：

```http
GET /chat HTTP/1.1
Host: localhost:8080
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
```

服务器一看这个请求，"哦，你小子想升级成WebSocket是吧"，如果支持WebSocket就会返回：

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

看到那个 **101 Switching Protocols** 了吗？这代表握手成功，协议升级完毕！从此以后，这条连接就不再是HTTP了，变成了WebSocket，两边可以自由通信。


### 第二步：消息互通——想发就发

握手完了之后，连接就一直保持着。前端可以主动发消息：

```javascript
// 发送消息给服务器
socket.send(JSON.stringify({
  type: 'chat',
  content: '你好呀服务器！',
  to: 'user123'
}));
```

服务器也能随时主动推给前端，不用等前端先问。这就是**全双工**的魅力。

### 服务端怎么整？以SpringBoot为例

后端这边也不复杂，咱拿Java的SpringBoot来演示：

```java
// WebSocket配置类
@Configuration
public class WebSocketConfig {
    @Bean
    public ServerEndpointExporter serverEndpointExporter() {
        return new ServerEndpointExporter();
    }
}

// WebSocket服务类
@Component
@ServerEndpoint("/chat/{userId}")
public class WebSocketServer {

    // 存所有在线用户的连接
    private static ConcurrentHashMap<String, Session> onlineUsers = new ConcurrentHashMap<>();

    @OnOpen
    public void onOpen(@PathParam("userId") String userId, Session session) {
        onlineUsers.put(userId, session);
        System.out.println("用户 " + userId + " 上线啦！当前在线人数：" + onlineUsers.size());
    }

    @OnMessage
    public void onMessage(String message, Session session) {
        // 收到前端消息，处理一下
        System.out.println("收到消息：" + message);
        // 可以转发给其他用户，实现聊天功能
    }

    @OnClose
    public void onClose(@PathParam("userId") String userId, Session session) {
        onlineUsers.remove(userId);
        System.out.println("用户 " + userId + " 下线了~");
    }

    @OnError
    public void onError(Session session, Throwable error) {
        System.out.println("出错了：" + error.getMessage());
    }

    // 服务器主动推消息给指定用户
    public void sendToUser(String userId, String message) {
        Session session = onlineUsers.get(userId);
        if (session != null) {
            session.getAsyncRemote().sendText(message);
        }
    }
}
```

代码不长吧？就几个注解的事儿。不过这里有个**小坑**要提醒一下：

**如果WebSocket服务类里用了Spring注入的Bean（比如@Service），直接@Autowired是行不通的**，因为WebSocket是多实例的。解决办法是通过ApplicationContext去拿，或者把需要用的Bean在配置类里初始化好传进去。

## 实际开发中，更推荐用STOMP

说实话，原生WebSocket虽然简单，但直接用起来还是有点"原始"——消息格式得自己定、订阅分发得自己写、重连机制也得自己策。咱在正经项目里更推荐用**STOMP协议**，做一层封装。

STOMP（Simple Text Oriented Messaging Protocol）就是在WebSocket之上又加了一层消息协议，支持**发布-订阅模式**，用起来特别爽：

```javascript
// 前端使用STOMP（配合stomp.js和sockjs）
const socket = new SockJS('/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({}, () => {
  // 订阅某个频道，像关注UP主一样
  stompClient.subscribe('/topic/chatroom', (message) => {
    console.log('收到群聊消息：', JSON.parse(message.body));
  });

  // 订阅私聊频道
  stompClient.subscribe('/user/queue/private', (message) => {
    console.log('收到私聊消息：', JSON.parse(message.body));
  });

  // 发消息
  stompClient.send('/app/chat', {}, JSON.stringify({
    content: '大家好呀！',
    roomId: 'room001'
  }));
});
```

```java
// 后端SpringBoot + STOMP配置
@Configuration
@EnableWebSocketMessageBroker
public class StompConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // 客户端订阅的前缀，服务器会广播到这些路径
        config.enableSimpleBroker("/topic", "/queue");
        // 客户端发送消息的前缀，会路由到@MessageMapping
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .withSockJS();  // 兼容不支持WebSocket的浏览器
    }
}

// 消息处理Controller，跟写普通Controller一样简单
@Controller
public class ChatController {

    @MessageMapping("/chat")
    @SendTo("/topic/chatroom")  // 广播到所有订阅者
    public ChatMessage broadcast(ChatMessage message) {
        return message;  // 直接广播出去
    }

    @MessageMapping("/private-chat")
    public void privateChat(ChatMessage message, SimpMessageHeaderAccessor headerAccessor) {
        // 通过SimpMessagingTemplate发给指定用户
        messagingTemplate.convertAndSendToUser(
            message.getTo(), "/queue/private", message
        );
    }
}
```

用STOMP之后，发送消息就像写Controller接口一样爽。**点对点聊天、群聊广播、消息确认**这些功能全都给你安排得明明白白的。

不过得注意一点：**STOMP是基于帧的消息格式**，如果你对接的不是STOMP客户端（比如第三方设备用原生WebSocket），就会有不兼容的问题。这个要看具体场景选择。

## 心法口诀

| 特性 | HTTP轮询 | WebSocket |
|------|----------|-----------|
| 通信方向 | 只能客户端主动 | 双向通信 |
| 连接方式 | 每次请求新建连接 | 建立后保持连接 |
| 实时性 | 看轮询间隔脸色 | 毫秒级 |
| 服务器压力 | 每次都要握手，累死 | 一次握手长期保持 |
| 适用场景 | 普通的增删改查、表单提交 | 聊天、推送、实时协作、游戏 |

## WebSocket也会掉链子——咱得兜底

WebSocket虽好，但它不是万能的：

1. **网络断了怎么办？** —— 前端一定要做**心跳检测 + 自动重连**机制。隔一段时间发个ping，要是pong没回来就得重连。

```javascript
// 简单的心跳检测示例
let heartbeatInterval;

socket.onopen = () => {
  // 每30秒发个心跳
  heartbeatInterval = setInterval(() => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000);
};

socket.onclose = () => {
  clearInterval(heartbeatInterval);
  // 自动重连
  setTimeout(() => reconnect(), 3000);
};
```

2. **代理/防火墙可能拦截** —— 有些公司的网络环境会干掉WebSocket连接，这时候可以用**SockJS**降级成HTTP长轮询，保证基本可用。

3. **服务器重启所有连接都会断** —— 这个比较鸡贼啊，得做好断线重连的体验优化。消息可以先存本地，连上了再发。

4. **分布式部署时Session不共享** —— WebSocket连接是跟服务器实例绑定的，如果有多台服务器，A服务器上的用户要给B服务器上的用户发消息就走不通了。这时候就需要引入**消息中间件**（比如RabbitMQ、Redis Pub/Sub）来做跨服务器的消息传递。

## 总结

WebSocket这个技术，说白了就是让HTTP从"一问一答"进化成了"随时交流"。它最大的贡献就是让服务器也能主动找前端搭话，这样才能做出真正实时交互的Web应用。

在实际项目中，咱一般不会裸写原生WebSocket，而是套一层STOMP，配合SpringBoot的`@MessageMapping`，写起来跟普通接口差别不大，很轻松。

以上是个人的一些经验分享，希望能帮到正在捣腾实时通信的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起进步！

本文完结撒花！！！
