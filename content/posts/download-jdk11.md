---
title: "老版JDK下载不了？让我们来邪修（bush）下载JDK11"
date: 2026-05-19
draft: false
categories: ["工具链"]
tags: ["JDK", "OpenJDK", "环境搭建"]
summary: "虽然说是邪修方法，实际上也就是换了员工途径而已，也是官方的，只不过不是oracle官方的。"
ShowToc: true
---


## 前言

虽然说是邪修方法，实际上也就是换了员工途径而已，也是官方的，只不过不是oracle官方的。

### 官网下载

一般来说，我们下载JDK就是直接去oracle官网进行下载，这里为了方便大家查找，我就直接给出连接了，如果同时也需要下载新版的朋友可以在官网下载

[Java Downloads | Oracle 中国](https://www.oracle.com/cn/java/technologies/downloads/#java11)

然后我们往下滑，就会看到Java11了，点击之后就会看到JDK11了

![示意图](/blog/images/download-jdk11/01.png)

但是我们发现这个是锁住的，想要下载需要同意协议，然后还需要
注册
员工oracle账号，主要这个账号注册起来还很麻烦，我试了好几次都注册失败了。嗯...如果大家能注册的话可以止步于此了（应该吧，因为我也不知道后续还有啥了）

![示意图](/blog/images/download-jdk11/02.png)

![示意图](/blog/images/download-jdk11/03.png)

如果注册失败或者怕麻烦的朋友可以继续往下看一下

## 献上焚决

我们直接去 Amazon 下载 Corretto 11，这个是基于OpenJDK 11进行构建的，对于普通开发者来说与JDK11并无二样。（感谢亚马逊大大！！！）

这里依旧给到链接

[https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/windows-install.html#windows-install-instruct](https://docs.aws.amazon.com/corretto/latest/corretto-11-ug/windows-install.html#windows-install-instruct)

但是这个比较鸡贼啊，我感觉它有点小藏了，不过也可能是我以小人之心度君子之腹了。我们仍然是接受小饼干，然后点击屏幕中间的那个PDF按钮，是的，它在这个里面，左边那一栏一看一个懵

![示意图](/blog/images/download-jdk11/04.png)

然后我们进来以后就可以看到左边的菜单栏了，直接瞄准最后一个关键词Downloads，一般应该都有这个导航栏的，如果没有的话那只能托右边那个进度条拖到快最后的地方了

![示意图](/blog/images/download-jdk11/05.png)

点进来之后先显示的是Linnux的，再往下滑滑就看到Windows了，然后下载就可以了，至此，大功告成，Win ! ! !     然后如果还需要
部署
环境变量的朋友还可以接着往下看

## 环境变量的部署

### 第一步

这个就比较简单一些了，但是有个注意事项就是：**切记存放的路径不能够有中文！！！**

![示意图](/blog/images/download-jdk11/06.png)

我是直接在D盘新建了应该文件夹放进去然后再解压到这个文件夹里面，解压之后我们就直接进入文件夹里面，然后再进入bin目录里面，这里是要点进去bin目录哈

![示意图](/blog/images/download-jdk11/07.png)

### 第二步

进来之后我们就点击上面的那个路径，Ctrl+C给它复制下来，待会要用到

![示意图](/blog/images/download-jdk11/08.png)

### 第三步

返回桌面，**右击**此电脑，然后选择属性，就会弹出右边这个窗口，一般这个就算是不同牌子也大差不差的

![示意图](/blog/images/download-jdk11/09.png)

然后我们点击右边的那个高级系统设置，会又弹出应该窗口，这个时候我们就选择环境变量就好了

![示意图](/blog/images/download-jdk11/10.png)

进来之后我们再在下面找到path这个变量，点进去新建一个路径然后把我们刚刚复制的路径放上去

![示意图](/blog/images/download-jdk11/11.png)

如果安装了其他版本的JDK的话就得看你想用哪一个了，把想用的选择上移到上面，这样在系统寻找全局路径（也就是哪怕不是在那个文件夹的bin目录里面依旧可以运行JDK11）就会优先找到那个版本的JDK

放好之后呢不要急着叉掉，我们得先点击当前弹窗的确定，然后再点击刚刚弹出的环境变量的弹窗的确定，最后回到系统属性那里我们再点击应用才算是完成配置。完成了配置之后我们可以按windows然后输入cmd进入命令行，输入：java -version，能查看到当前的Java版本就算是成功了，恭喜恭喜！
