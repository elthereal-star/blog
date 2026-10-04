---
title: "搓完项目没人看？手把手让你的项目\"上线接客\""
date: 2026-05-28
draft: false
categories: ["工程化"]
tags: ["部署", "Nginx", "云服务器", "上线"]
summary: "嗨朋友们！前两天刚跟大家聊完内网穿透，有些朋友就问了：\"我用内网穿透确实能让别人临时访问了，但每次都得开着电脑也太难受了吧？有没有一劳永逸的办法？\""
ShowToc: true
---


嗨朋友们！前两天刚跟大家聊完内网穿透，有些朋友就问了："我用内网穿透确实能让别人临时访问了，但每次都得开着电脑也太难受了吧？有没有一劳永逸的办法？"

问得好！内网穿透虽然方便，但本质上是"把本地服务临时暴露出去"，适合调测、演示、临时显摆（不是）。如果你想让项目 **24 小时都能被别人访问**，那就得正儿八经地**部署**了。

今天咱就来唠唠，**一个项目从你电脑上跑到能让全网访问，到底要走哪几步、有哪些路子可以选**。别怕，没你想的那么复杂，跟着咱一步一步来 (๑•̀ㅂ•́)و✧

---


{{< svg "nat-traversal" >}}
## 先整明白，部署到底是在干啥？

写代码的时候，咱的项目跑在 `localhost:8080` 上，只有咱自己电脑能访问。部署要做的事其实就一句话：**把项目放到一台有公网 IP 的电脑上跑起来**。

就这么简单！至于"这台电脑"是你自己买的云服务器、还是别人帮你管理好的平台、还是用 GitHub 提供的免费空间，那就是咱接下来要聊的各种方案了。

{{< svg "deploy-pipeline" >}}

---

## 方案一：云服务器部署 —— 最经典、最稳的路子

这是最传统也最灵活的方案，说白了就是：**去云厂商那租一台虚拟机，把它当成一台"永远不关机的远程电脑"，把你的项目扔上去跑**。

在这台"远程电脑"上，你可以装数据库、配环境、跑 jar 包、挂 nginx，跟操作自己电脑一样一样的，唯一的区别是——它有一个全世界都通得过的公网 IP。

### 第一步：搞一台云服务器

国内主流的云厂商就那几个：

- **阿里云**：老大哥，稳，贵一点，学生有优惠
- **腾讯云**：跟阿里云差不多，也有学生价
- **华为云**：起步比前两家晚，但也在库库追
- **京东云 / 百度云**：也有，但用户相对少

如果你还是学生，强烈建议走**学生优惠**，一年几十块就能搞一台最低配的，够你瞎折腾一整年了。不是学生的话，买个最低配的轻量应用服务器，一个月几十块钱，相比你喝的奶茶，真不算贵。


**买的时候注意几个点**：
- **地域**：选离你最近的，一般华北就选北京，华东选上海、杭州，华南选广州、深圳。延迟低，SSH 连上去操作的时候不卡。
- **系统**：新手强烈建议选 **CentOS 7.x**（虽然快停止维护了但还是教程最多）或者 **Ubuntu 20.04/22.04**。别手贱选 Windows Server，贵且不说了，远程桌面卡成 PPT 别怪我没提醒你 (￣▽￣)~*
- **带宽**：最低配的 1Mbps 其实也够新手用了，又不是要支撑千万并发对吧。

买完之后你会得到一个**公网 IP**（比如 `1.2.3.4`）和一个 **root 密码**，记好了，待会要用的。

### 第二步：连上服务器，整环境

你需要一个 SSH 工具来连上服务器。Windows 用户推荐：

- **Xshell + Xftp 组合**（免费版就够用）：前者敲命令，后者传文件，分工明确
- **Termius**：跨平台，界面好看，不过高级功能要钱
- **FinalShell**：国产良心软件，免费，还带可视化监控面板
- **Windows Terminal + 自带的 ssh 命令**：如果你喜欢极简风，Win10/11 自带的 ssh 也能用

随你选，咱这里用 Xshell 举例。新建连接，填上你的公网 IP、用户名 `root`、密码，点连接就好了。


连上之后，你就会看到一个黑乎乎的终端窗口，别慌，这就是你"远程电脑"的操作界面。接下来咱要在上面装 JDK、MySQL、Nginx 等环境。

#### 装 JDK（以 JDK 17 为例）

```bash
# 先更新一下软件源
yum update -y   # Ubuntu 的话用 apt update

# 搜索可用的 JDK 版本
yum search jdk   # Ubuntu: apt search jdk

# 安装 JDK 17
yum install -y java-17-openjdk java-17-openjdk-devel   # Ubuntu: apt install -y openjdk-17-jdk

# 装完检查一下
java -version
# 如果打印出类似 "openjdk version 17.0.x" 的信息，说明装好了
```

> **小提示**：如果你用的是 Ubuntu 系统或者想装其他版本的 JDK，这里有个坑要注意——部分老教程会让你安装 Oracle JDK，但那个现在下载要登录账号了，比较鸡贼。咱们直接用 **OpenJDK** 就行，一样的，没区别。

#### 装 MySQL

```bash
# 下载 MySQL 官方 yum 源（以 MySQL 8.0 为例）
wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm
# 安装 yum 源
rpm -ivh mysql80-community-release-el7-3.noarch.rpm
# 安装 MySQL
yum install -y mysql-community-server
# 启动 MySQL
systemctl start mysqld
# 看初始密码
grep 'temporary password' /var/log/mysqld.log
```

**这里有个大坑！** MySQL 8.0 默认密码策略比较严格，要求大小写字母 + 数字 + 特殊字符。你拿到初始密码后第一次登录，它会强制要求你改密码。如果你随便改个 `123456`，它会直接拒绝你，报一个 `Your password does not satisfy the current policy requirements`。解决方案：

```sql
-- 先用初始密码登录 MySQL
mysql -u root -p

-- 改密码策略，让它可以接受简单密码（开发环境可以这么干，生产环境就别了哈）
SET GLOBAL validate_password.policy = LOW;
SET GLOBAL validate_password.length = 6;

-- 然后再改密码
ALTER USER 'root'@'localhost' IDENTIFIED BY '你的新密码';
```

**另外**，MySQL 默认只能本机连，如果你想让本地电脑的 Navicat 啥的能连上去，还得开一下远程访问：

```sql
-- 创建一个可以从任何主机连接的 root 用户（开发环境专用，生产别这么搞！）
CREATE USER 'root'@'%' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

**还有，别忘了去云服务器安全组放行 3306 端口**，不然你 Navicat 死活连不上，白白怀疑人生半天（血的教训）。

#### 装 Nginx

```bash
# 安装
yum install -y nginx   # Ubuntu: apt install -y nginx

# 启动
systemctl start nginx

# 设置开机自启
systemctl enable nginx
```

装好 Nginx 之后，在浏览器里访问 `http://你的服务器IP`，如果看到 Nginx 的欢迎页，说明安装成功。这时候你的服务器已经是一个合格的"Web 服务器"了！

### 第三步：把项目扔上去

好了，环境整完了，该让咱们的项目"搬家"了。

首先在你本地把项目**打包**。如果你用的是 SpringBoot 项目，IDEA 里点右边的 Maven → 你的项目 → Lifecycle → `package`，然后等项目构建完成，在 `target` 目录下会有一个 `.jar` 文件。


然后用 Xftp 把这个 jar 包传到服务器上。传之前建议先在服务器上建个目录，方便管理：

```bash
# 在服务器上建一个项目目录
mkdir -p /www/wwwroot/my-project
```

用 Xftp 把 jar 包拖进这个目录就好。

接着，咱来启动它：

```bash
cd /www/wwwroot/my-project

# 直接运行试试
java -jar your-project.jar

# 看到 SpringBoot 的 banner 和 Started 就表示成功了
```

但是现在有个问题：你关了 SSH 窗口，jar 包就停了。这肯定不行啊！咱得让它在**后台**一直跑着。有几种办法：

**方式一：nohup（最简单）**

```bash
nohup java -jar your-project.jar > app.log 2>&1 &
```

`nohup` 就是"no hang up"的意思，你关了终端它也不会停。`> app.log` 是把日志写到文件里方便排查问题。

想停掉它的话：
```bash
# 找到进程 ID
ps -ef | grep your-project.jar
# 干掉它
kill -9 进程ID
```

**方式二：systemd（推荐，更专业）**

创一个服务配置文件：

```bash
vim /etc/systemd/system/my-project.service
```

写入以下内容：

```ini
[Unit]
Description=My Cool Project
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/www/wwwroot/my-project
ExecStart=/usr/bin/java -jar /www/wwwroot/my-project/your-project.jar
Restart=on-failure   # 挂了会自动重启，就很安逸

[Install]
WantedBy=multi-user.target
```

保存后：

```bash
# 重新加载 systemd 配置
systemctl daemon-reload
# 启动服务
systemctl start my-project
# 设置开机自启
systemctl enable my-project
# 查看状态
systemctl status my-project
```

这种方式的好处是可以用 `systemctl start/stop/restart` 管理服务，异常退出还会自动重启，比 nohup 高级多了。

### 第四步：配置 Nginx 反向代理

现在你的 SpringBoot 跑在服务器的 8080 端口上，别人得访问 `http://你的IP:8080` 才能看到。这多不优雅啊！咱用 Nginx 做个反向代理，让用户直接访问 `http://你的域名/` 就能到达你的项目，而且还能顺带做负载均衡、HTTPS 啥的。

编辑 Nginx 配置：

```bash
vim /etc/nginx/conf.d/my-project.conf
```

```nginx
server {
    listen       80;
    server_name  你的域名 你的服务器IP;   # 你的域名或者 IP

    location / {
        # 把请求转发给本地 8080 端口的 SpringBoot
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

然后重载 Nginx：

```bash
nginx -s reload
```

搞定！现在访问 `http://你的域名` 就直接到你的 SpringBoot 项目了。

**这里有个坑**：如果你有域名并且想把域名解析到服务器，需要先去你的域名服务商（阿里云、腾讯云、Cloudflare 等）那里，添加一条 **A 记录**，把域名指向你的服务器公网 IP。**还有，国内服务器用 80/443 端口是需要域名备案的**，没有备案的话运营商会拦截。不想备案可以用非标准端口（如 8080、8443），或者在服务器选购时直接选香港/海外节点。

### 第五步：（可选）整个 HTTPS

现在大家都是 `http://`，浏览器会显示一个"不安全"的锁，看着就难受。咱用 **certbot** 整一个免费的 HTTPS：

```bash
# 安装 certbot
yum install -y certbot python3-certbot-nginx   # Ubuntu: apt install -y certbot python3-certbot-nginx

# 一键申请并配置 SSL 证书
certbot --nginx -d 你的域名

# 按提示操作，输入邮箱啥的，完成后 certbot 会自动帮你改 Nginx 配置
```

搞定后你的网站就是 `https://` 了，浏览器里那个绿色的小锁看着就很舒服。证书有效期 90 天，到期前 certbot 会自动续期，不用你操心。

> **注意**：certbot 需要你的域名已经解析到了服务器 IP，而且 80 端口可访问。如果没备案用不了 80 端口，那 HTTPS 这条路就走不通了，先老老实实用 `http://IP:8080` 吧。

---

## 方案二：PaaS 平台 —— 不想折腾服务器的懒人福音

如果你觉得上面那些命令太劝退了——装 JDK、配 MySQL、改 Nginx、还要搞安全组，每一步都可能踩坑——那 PaaS 平台就是为你量身定做的。

**PaaS 是什么意思捏？** 你把它理解成"托管式部署"，你只需要把代码传上去，服务器、环境、数据库这些都帮你自动配好了，一行命令就上线。

### Vercel —— 前端/全栈项目的神

如果你的项目是前端（React、Vue、Next.js 这类），那 **Vercel** 简直不要太爽：

1. 打开 [vercel.com](https://vercel.com)，用 GitHub 账号登录
2. 导入你的 GitHub 仓库
3. 啥都不用配，点一下 Deploy，几十秒就上线了
4. 自动给你一个 `xxx.vercel.app` 的域名，还能绑自己的域名


**优点**：免费、自动 HTTPS、自动 CI/CD（你往 GitHub 推代码它自动部署）、全球 CDN 加速、部署速度巨快

**缺点**：主要是给前端/SSR 项目用的，纯 Java/SpringBoot 后端不太合适。免费版有流量和构建次数限制，个人小项目完全够用就是了。

### Railway —— 后端服务也能一键搞定

如果你的项目是 SpringBoot、Node.js、Python 这种后端服务，那 **Railway** 会是更好的选择：

1. 打开 [railway.app](https://railway.app)，用 GitHub 登录
2. 新建项目，选择"Deploy from GitHub repo"
3. Railway 会自动识别你的项目类型（比如检测到 `pom.xml` 就知道是 Java 项目）
4. 如果项目需要 MySQL/Redis/PostgreSQL，直接在 Railway 里点一下就能帮你创建一个数据库实例，还会自动把连接信息注入到你的环境变量里
5. 完成！给你一个公网地址，直接就能用

**优点**：支持各种后端语言，数据库一键创建，自带环境变量管理和自动部署。有免费额度，个人学习项目基本免费。

**缺点**：免费额度用完就要付费了，高性能场景也贵。国内访问速度看缘分（服务器在海外）。

### 国内 PaaS 替代方案

如果你觉得 Vercel/Railway 在海外太慢了，国内也有一些 PaaS 平台可以选：

- **阿里云 SAE / 腾讯云 CloudBase**：大厂出品，跟它们自己的云服务深度整合，大陆访问快，但价格相对高
- **Render**：Railway 的竞争对手，免费额度也不错，但同样服务器在海外

---

## 方案三：容器部署（Docker）—— 装个环境再也不求人

你是不是有这样的经历：在你电脑上跑得好好的，一放到服务器就各种报错——"我这里明明是 JDK 17 啊？""我这个 MySQL 版本跟你不一样啊？" 这些就是因为**环境不一致**导致的。

Docker 就是来解决这个问题的，你可以把它理解成一个"集装箱"：把你的代码、JDK、配置文件所有东西打包在一起，不管搬到哪台机器上，直接启动，环境一模一样。


### 搞一个 Docker 镜像

在你的 SpringBoot 项目根目录下创建一个 `Dockerfile`：

```dockerfile
# 基于 JDK 17 镜像
FROM openjdk:17-jdk-slim

# 设置工作目录
WORKDIR /app

# 把 jar 包复制进去（你需要先 mvn package 打好包）
COPY target/your-project.jar app.jar

# 暴露端口
EXPOSE 8080

# 启动命令
ENTRYPOINT ["java", "-jar", "app.jar"]
```

然后在服务器上：

```bash
# 安装 Docker（以 Ubuntu 为例）
curl -fsSL https://get.docker.com | bash

# 构建镜像
docker build -t my-project .

# 运行容器
docker run -d -p 8080:8080 --name my-project my-project
```

完事！项目就跑在 Docker 容器里了。停止、重启、删掉容器都非常方便：

```bash
docker stop my-project
docker start my-project
docker restart my-project
```

### Docker Compose —— 一键启动整个"全家桶"

真实项目往往不止一个 jar 包，还得有 MySQL、Redis、Nginx 对吧？一个个启动容器太麻烦，咱用 Docker Compose 把它们编排起来：

```yaml
# docker-compose.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: your_database
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  app:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - mysql
    environment:
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/your_database
      SPRING_DATASOURCE_USERNAME: root
      SPRING_DATASOURCE_PASSWORD: your_password

volumes:
  mysql_data:
```

然后一条命令全部启动：

```bash
docker compose up -d
```

MySQL + SpringBoot 一次性全跑起来了，很安逸对吧？

**Docker 虽好但有一个问题**：如果只是部署一个简单的个人项目，Docker 这套东西反而显得有点"杀鸡用牛刀"。要不要学取决于你的需求，如果你是奔着找工作的方向去的，Docker 必须会；如果只是自己玩个小项目，不学也没啥影响。

---

## 方案四：GitHub Pages —— 纯静态站点首选

如果你做的压根就没有后端（纯 HTML/CSS/JS，或者用 Vite/VuePress 生成的静态网站），那 GitHub Pages 是最省心的选择，**完全免费**：

1. 把代码推到 GitHub 仓库
2. 进入仓库 Settings → Pages
3. Source 选 `Deploy from a branch`，分支选 `main`，目录选 `/root`
4. 保存，等一两分钟，访问 `https://你的用户名.github.io/仓库名` 就能看到了

一个字：白嫖！两个字：真香！三个字：零成本！

---

## 最后，各种方案怎么选？一图流

| 方案 | 适合谁 | 花费 | 上手难度 | 适合场景 |
|------|--------|------|------|------|
| **云服务器** | 想完全掌控、顺便学运维 | 几十~几百/月 | ⭐⭐⭐ | 后端项目、全栈项目 |
| **Vercel / Railway** | 不想折腾服务器 | 免费额度够用 | ⭐ | 前端/Node/轻量后端 |
| **Docker** | 追求环境一致性 | 跟方案一一样 | ⭐⭐⭐⭐ | 微服务、团队协作 |
| **GitHub Pages** | 纯静态网站 | 免费 | ⭐ | 博客、文档站、个人主页 |
| **内网穿透** | 临时分享、调测 | 免费 | ⭐ | 临时演示、开发调试 |

**咱的建议**：
- 如果你只是想**让朋友看看效果**：先用内网穿透（Cpolar 一行命令的事），啥都不用买，详情可以看咱之前写的《[内网穿透的意义以及实现方式](/blog/posts/nat-traversal/)》
- 如果你是**学生党想学东西**：买台云服务器学生机，几十块一年，从 JDK 装到 Nginx，搞一遍什么都会了
- 如果你是**前端选手，项目没后端**：Vercel 或者 GitHub Pages，免费还快，爽到飞起
- 如果你想**认真做一个长期运营的项目**：云服务器 + Docker + Nginx + HTTPS 一条龙，稳得很
- 如果你觉得**云服务器手动配环境太烦人**：Railway 了解一下，GitHub 推上去自动部署

---

## 总结一下

部署这事儿说白了就三个核心步骤：

1. **找一台有公网 IP 的机器**（租云服务器 / 用 PaaS 平台 / 用 GitHub 的免费服务）
2. **把项目放上去跑起来**（打包 jar 丢上去 / Docker 镜像 / 平台自动部署）
3. **让别人能访问**（绑定域名 / 配置 Nginx / SSL 证书）

第一次动手部署的时候可能会觉得步骤多、容易错，这太正常了。咱第一次部署的时候一个安全组端口没开，愣是排查了俩小时，差点怀疑人生 (╯‵□′)╯︵┻━┻ 但搞过一次之后就会觉得：哦，就这？也就那回事嘛。

**部署这个技能，不是你看一篇文章就能学会的，得亲自动手。** 建议你今天就找个最简单的项目（哪怕就一个 Hello World 的 SpringBoot），跟着上面的步骤，租台服务器或者用 Railway 整一次。当我们看到自己写的页面从一个 `http://公网IP` 的地址加载出来的那一刻，那种成就感，真的拉满 (๑•̀ㅂ•́)و✧

以上是个人的一些经验分享，希望能帮到正在为"怎么让别人看到我项目"而苦恼的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起学习一起进步！

对了，如果在部署过程中遇到了啥奇奇怪怪的报错也不要慌，90% 的问题都能在搜索引擎找到答案。剩下 10% 嘛……就祝你好运了 (￣▽￣)~*

本文完结撒花！！！✿✿ヽ(°▽°)ノ✿

---

*文中图片链接需要自行替换为实际截图哦~*
