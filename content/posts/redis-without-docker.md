---
title: "新手要使用Redis不想折腾Docker,WSL，这里有办法"
date: 2026-05-19
draft: false
categories: ["工具链"]
tags: ["Redis", "Windows", "Memurai", "环境搭建"]
summary: "我们在进行一些自己的开发或者测试项目的时候，通常需要用到Redis，但是在Redis官网提供的方式是使用Docker来进行下载，可能对于部分新手或者不想多折…"
ShowToc: true
---


我们在进行一些自己的开发或者测试项目的时候，通常需要用到Redis，但是在Redis官网提供的方式是使用Docker来进行下载，可能对于部分新手或者不想多折腾的人来说并不太友好，这里给大家推荐一个windows的平替版——Memurai。这是Redis官方认可的Windows元素兼容实现，安装方法也很简单快捷，适合普通开发和生产测试。

### 下载地址

这里依旧直接先给到地址：[https://www.memurai.com/](https://www.memurai.com/)，然后进来之后我们就会看到这样一个界面

![示意图](/blog/images/redis-without-docker/01.png)

然后我们直接选择这个红色的
GET
MEMURAI就好了，点进来之后我们又会看到

![示意图](/blog/images/redis-without-docker/02.png)

上面的哪个choose version就不用改了，然后下面那个Develop Edition推荐选择
LTS
就好了，，这个是长期支持版本，也是比较稳定的版本，当然比起RC的这个发布候选版来说可能会缺少一些尝鲜功能，如果没有这方面的需求的话还是建议LTS求稳比较好一些。

下载好之后我们就得到了这样一个MSI的安装程序，这里可能有些朋友的电脑安装了压缩程序然后自动给他判成压缩包了，这个适合我们只需要右击然后选择使用window安装程序来进行安装就好了，这个的安装过程还是很简单的，就不多做赘述了

![示意图](/blog/images/redis-without-docker/03.png)

### 测试是否安装成功

在通过这个安装程序安装了以后，我们需要如何检查电脑里面是不是真的有这个东西了呢？这个适合我们就可以**使用管理员身份打开cmd**，然后输入这个代码：net start memurai，如果看到“请求的服务已经启动”，那这个安装据没有问题了，不过还有下一步嘞

![示意图](/blog/images/redis-without-docker/04.png)

上一步如果没有问题的话我们就来到第二步，来测试看看这个是否可用，我们依旧输入新的代码来进行测试：memurai-cli ping，如果返回PONG，就代表没什么问题了，可用安心使用了

### 密码的设置

这个也是一个数据库，数据库不进行加密说实话多少感觉有点心痒痒，所以这里我们就来对Redis进行密码配置。

我们在找到在安装的适合选择的文件夹，然后点击这个conf文件进去

![示意图](/blog/images/redis-without-docker/05.png)

进来之后我们直接按住Ctrl+F执行查找功能，找到# requirepass foobared，然后把后面的foobared给删掉，换成我们向设置的密码，再把前面的注释#给删掉，最后保存一下就好了。

![示意图](/blog/images/redis-without-docker/06.png)

之后我们就可用重启一下服务，还是在cmd里面先后运行net stop memurai 和 net start memurai

，然后再测运行普通连接，输入：memurai-cli ping，这个时候应该会报错了，然后我们就可用输入memurai-cli --askpass ping，让他弹出输入密码的提示来输入我们刚刚设置的密码，如果返回PONG就算是成功了

![示意图](/blog/images/redis-without-docker/07.png)

### 图形化操作界面

这个就感觉使用Redis官网给的Redis Insight就挺好的，只需要在官网登录运行就可以下载就好了。

![示意图](/blog/images/redis-without-docker/08.png)

选择这个Try Redis for free，然后登录进去点击右上角那几排点，选择Download Center

![示意图](/blog/images/redis-without-docker/09.png)

再然后来到下载界面选择自己需要的版本就好了，Windows用户就在下面选择第一个就行了

![示意图](/blog/images/redis-without-docker/10.png)

然后就能下载成功了

当然，如果有朋友感觉有点麻烦的话，依旧附上下载连接，直接点击下载就好了

[https://s3.amazonaws.com/redisinsight.download/public/latest/Redis-Insight-win-installer.exe](https://s3.amazonaws.com/redisinsight.download/public/latest/Redis-Insight-win-installer.exe)

不过这个只是刚刚这个图片里面的Windows用户的哈，后面的连接的话就直接把端口号跟密码放进去就好了，默认端口号就是6379，如果有修改了Redis的端口号的话改成这个修改后的端口号就好了哈

### 后言

其实有空的时候琢磨一下Docker跟WSL也挺好的，只是说如果不是程序员或者只是想单纯测试使用一下的话这样子偷懒这样子倒是方便了不少。不过这个有一些限制，需要告知一下

1.每运行10天会自动关掉（需要手动重启）

2.最多连接10个不同的IP

3.最多使用系统内存的50%

4.只能用于开发/测试，不能用于生产

以上是个人的一些经验分享，囊括的情况不一定完整，然后如果有哪里有上什么错误的地方的话也请大佬们指出原理一下哈，本文完结撒花！！！
