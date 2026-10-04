---
title: "新手如何使用IDEA在github上面上传自己的项目"
date: 2026-05-19
draft: false
categories: ["工具链"]
tags: ["IDEA", "Git", "GitHub", "新手教程"]
summary: "首先有一个前置条件就是要能够进入github才行，一般情况下科学上网进去会方便一些，所以我在这里说的是新手在科学上网的条件下，在IDEA中遇到github的…"
ShowToc: true
---


### 前置条件

首先有一个前置条件就是要能够进入github才行，一般情况下科学上网进去会方便一些，所以我在这里说的是新手在科学上网的条件下，在IDEA中遇到github的上传问题。

### 第一步

![示意图](/blog/images/idea-github-upload/01.png)
我这里使用的IDEA是2025.3的版本的， 在左上角有一个master的按钮，点击之后先选择commit把代码提交一下（这里还没有进行上传，上传是下一步的事情）。

或者左上角没有看到mastter这个按钮的也可以点击左上角那四条横线打开菜单，然后看到列表里面有一个Git，把鼠标放到那里之后也可以看到这些选项

![示意图](/blog/images/idea-github-upload/02.png)

然后就可以选择我们需要提交的内容了，一般情况下都是选择提交全部，如果是的话就直接点最上面那个框就好了（我这里提交过了，所以这里显示的是Changes）

![示意图](/blog/images/idea-github-upload/03.png)

当然如果都没有看到的话，那就应该会看到Version Control，这个时候点击第二个就可以选择需要添加的文件了

![示意图](/blog/images/idea-github-upload/04.png)

然后选择好之后进来也是大差不差的

![示意图](/blog/images/idea-github-upload/05.png)

左下角那个commit Message就是你提交时候的描述（可写可不写），然后就Commit就好了。这个时候使用了科学上网的同学可能就会遇到问题了，他可能会给你报错：

Failed to connect to 127.0.0.1 port 65533 after 2066 ms: Could not connect to server

这个就是Git尝试通过本地代理服务器去连接github，但是连接失败了。那是因为我们在科学上网的时候可能就把那个代理更改了。这个时候我们就需要去找到我们的科学上网的端口然后把端口给记住去替换掉上面报错的端口。（一般在设置之类的地方我们可以找到）

![示意图](/blog/images/idea-github-upload/06.png)

然后我们可以在cmd或者IDEA的Terminal（PoerShell）当中进行运行这两行代码

git config --
global
http.proxy http://127.0.0.1:7890

git config --global https.proxy http://127.0.0.1:7890

**注意！这两行是由区别的，一个是http，另一个是https，所以不要因为看走眼了觉得这俩是一样的就只改了一个就不太美妙了。**然后呢再把后面的7890换成直接更改查询到的端口号就好了。

弄完这个通常提交就没有问题了，然后我们再来解决上传的问题，是的，事情还并没有结束。

### 第二步

这个时候我们需要在github上面创建好一个仓库才行，然后完成之后它就会给你一个URL地址，这个时候我们再回到IDEA里面把代码选择PUSH（也就是上传）上去，通常点击之后会弹出一个让你登录github仓库的弹窗，然后就可以使用这个URL来进行提交了。

但是如果你是遇到了如下情况，那还得接着往下看一下

![示意图](/blog/images/idea-github-upload/07.jpeg)

![示意图](/blog/images/idea-github-upload/08.jpeg)

![示意图](/blog/images/idea-github-upload/09.jpeg)

这个时候我就得使用旁边那个koken来登录了（放心，不是消耗咨询额度的那种token）。

接下来要做的就是打开github然后点击个人头像，先找到
Settings

![示意图](/blog/images/idea-github-upload/10.png)

然后在左
侧边栏
里面找到Deceloper settings

![示意图](/blog/images/idea-github-upload/11.png)

再然后还是在左边的侧边栏找到Personal access tokens，选择Tokens（classic）

![示意图](/blog/images/idea-github-upload/12.png)

最后在右上角点击Generate new token 选择Generate new token（classic）

![示意图](/blog/images/idea-github-upload/13.png)

这里可能会要求你输入一下github的密码验证。

接下来就进入了配置页面：

Note（备注）:这个建议起一个形象点的名字，虽然后面可能不一定再回来看了，不过也是为了以防万一，养成好习惯总归是好的嘛。

Expiration（过期时间）：这个也是看你自己了，大概率就只用这一次，那么我们就可以把时间给设置的短一点。

Select scopes（选择权限）：这个的话找到并且勾选repo就够了，这个是给出仓库的读写权限，这样才可以提交代码上去，其他的就无所谓了，可以不选。

然后生成成功以后就直接给他复制下来，待会就要用到了，如果怕出现上面意外啥的也可以新建一个txt文档把这个存起来，但是后面记得删掉，不然安全性不太行。

再然后就回到IDEA当中选择使用token来登录，把刚刚得到的token放上去就好了。

当然，如果到了这一步还是出现问题的话，我们就得
开启
第三步了。比如像这样

![示意图](/blog/images/idea-github-upload/14.jpeg)

### 第三步

打开IDEA，然后直接在左上角搜索栏里面搜HTTP就能搜到这个了，然后我们选择下面这个Manual proxy configuration进行手动配置，可以选择HTTP或者SOCKS，后者要稳定一些，不过前者也能用，懒的话直接使用默认的前者就行，然后再把下面的Host name填上127.0.0.1（也就是自己的本机），下面那个Port number就填上面找到的那个四位数端口号就好了。接着就可以在左下角那个Check connection来进行测试 ，显示“Connection successful”的话就表示成功了，然后直接
Apply
再OK就好了。

![示意图](/blog/images/idea-github-upload/15.png)

**至此，一般来说也就没啥问题了，如果还有问题的话主播也没招了。次方法也是仅供参考，如果有更好的办法啥的大佬们也可以在评论区中指出哦**

{{< svg "deploy-pipeline" >}}
