---
title: "配置明明改对了，Codex 还报 503？扒到最后才发现模型有三层优先级"
date: 2026-10-13
draft: false
categories: ["工具链"]
tags: ["Codex", "AI 编程", "排错", "配置文件", "踩坑"]
summary: "凌晨两点，我盯着屏幕上那个红色的报错，开始了深深的自我怀疑——"
ShowToc: true
---


凌晨两点，我盯着屏幕上那个红色的报错，开始了深深的自我怀疑。

```text
上游 HTTP 503: No available channel for model claude-opus-5-5 under group ...
```

不是，哥们儿。我配置文件里明明写的是 `gpt-6.1-sol` 啊？我十分钟前才刚改的，改完还 `grep` 确认过，怎么就……

更邪门的是——**同一个工具里那个"发个 hi 测一下连通性"的按钮，点下去是绿的，秒回。**

面板说没问题，聊天窗口说不行。这谁顶得住啊 (╯‵□′)╯︵┻━┻

今天咱就来盘一盘这个坑到底是怎么挖出来的，保证你看完也能在自己机器上三分钟定位同类的问题。


## 先把今天的主角交代一下

咱说的这个东西，是给 AI 编程 CLI 挂第三方模型服务用的。官方的模型额度嘛……懂的都懂，所以不少朋友会选择走第三方的 API 中转，再配一个本地代理，把两边协议的差异抹平。

配置大概长这样，改的是 `~/.codex/config.toml`：

```toml
model_provider = "custom"
model = "gpt-6.1-sol"                    # ← 我改的就是这一行

[model_providers.custom]
name = "My Codex"
base_url = "http://127.0.0.1:15721/v1"   # 指向本地代理
wire_api = "responses"                   # 注意这个，后面要考
requires_openai_auth = true
```

看起来人畜无害对吧？就这么一个文件，让我折腾了大半宿 (￣▽￣)~


## 第一反应：肯定是配置写错了

我一开始的想法特别朴素：报错说 `claude-opus-5-5` 没有可用渠道，那**大概率是我配置里还残留着 claude 的模型名没改干净**。

于是我把 `config.toml` 从头翻到尾，`grep` 了三遍：

```bash
grep -rn "claude" ~/.codex/config.toml
# 无输出
```

干干净净，一个 claude 都没有。文件里明明白白写着 `model = "gpt-6.1-sol"`，文件修改时间也确实是十分钟前。

**配置是对的。** 那问题就不在配置上——**它一定在别的地方**。


## 那这个 claude-opus-5-5 到底从哪儿冒出来的？

既然配置文件没问题，那就只能看**数据实际流出去的时候长什么样**了。

本地代理的日志里，每转发一次都会打印一行目标地址和模型名：

```bash
grep "请求目标" ~/代理目录/logs/cc-switch.log | tail -5
```

```text
[01:35:53] >>> 请求目标: https://<中转网关>/v1/responses (model=claude-opus-5-5)
[01:35:54] >>> 请求目标: https://<中转网关>/v1/responses (model=claude-opus-5-5)
[01:35:56] >>> 请求目标: https://<中转网关>/v1/responses (model=claude-opus-5-5)
```

注意了，**请求在离开我机器之前，模型名就已经是 `claude-opus-5-5` 了**。配置里的 `gpt-6.1-sol` 压根没派上用场。

还有个细节挺有意思：从 `01:35:12` 到 `01:35:56`，**44 秒里连着重试了 30 次**，每次都是一个结果。这是客户端自己的自动重试在疯狂加班，跟网络抖动没关系，纯属白给。

那么问题就变成了一个非常具体的问题：**Codex 是从哪儿读到这个 `claude-opus-5-5` 的？**


## 破案第一现场：会话自己记着模型

Codex 每开一次会话，都会落一份 rollout 记录（就是个 jsonl 文件），路径长这样：

```text
~/.codex/sessions/<年>/<月>/<日>/rollout-<时间>-<会话ID>.jsonl
```

翻出来一看，第一行的 `session_meta` 记着这次会话的 `cwd`、`model_provider`、`cli_version`；之后**每一次交互**都会写一条 `turn_context`，里面明明白白记着这一轮用的模型。

一条命令就能把它全列出来：

```bash
# 把最近一个会话里每一轮用的模型打印出来
F=$(ls -t ~/.codex/sessions/*/*/*/rollout-*.jsonl | head -1)

python -c "
import json, io, sys
for line in io.open(sys.argv[1], encoding='utf-8'):
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get('type') == 'turn_context':
        p = o['payload']
        cm = (p.get('collaboration_mode') or {}).get('settings', {})
        print(o['timestamp'], '| model =', p.get('model'), '| 模式内的模型 =', cm.get('model'))
" "$F"
```

我的输出是这样：

```text
2026-10-11T16:33:24Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
2026-10-11T16:33:54Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
2026-10-11T17:17:00Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
2026-10-11T17:19:54Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
2026-10-11T17:21:17Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
2026-10-11T17:35:07Z | model = claude-opus-5-5 | 模式内的模型 = claude-opus-5-5
```

六轮交互，六轮全是 `claude-opus-5-5`。最后那一条是 UTC 时间的 `17:35:07`，换算成北京时间正好是 **01:35:07**——跟日志里那波 503 完全对上了。

到这一步其实已经八九不离十：**这个会话把模型钉在了自己身上。**


## 破案第二现场：数据库那张线程表

为了确认不是巧合，我又去翻了 Codex 的状态库。`~/.codex/state_5.sqlite` 里有张 `threads` 表，每个会话一行，而且**带着 `model` 和 `reasoning_effort` 两个列**：

```bash
python -c "
import sqlite3, os
con = sqlite3.connect(os.path.expanduser('~/.codex/state_5.sqlite'))
for row in con.execute('select id, title, model, reasoning_effort from threads order by updated_at desc limit 10'):
    print(row)
"
```

```text
('01a12c0d-...', 'hi',                'gpt-6.1-sol',      'xhigh')   # 我新建的测试会话
('01a12bcf-...', '你好',               'claude-opus-5-5',  'high')    # ← 报 503 的就是它
('01a12bd7-...', '你好',               'claude-opus-5-5',  'none')
('01a12b87-...', '你好',               'claude-opus-5-5',  'high')
('01a12aba-...', '生成循环动画SVG...',  'gpt-5.6-sol',      'high')
```

对上了。每个会话都记着自己那一份模型，而且**新建的会话是 `gpt-6.1-sol`，老会话还是 `claude-opus-5-5`**。

两个完全独立的地方互相印证，案子基本就结了。


## 所以 Codex 的模型优先级到底是啥？

{{< svg "codex-model-priority" "模型优先级：config.toml 只影响新建会话，已存在的会话沿用自己钉住的模型" >}}

一句话说清：**`config.toml` 里的 `model` 只在"会话创建的那一刻"被读一次，读完就写进这个会话自己的记录里。之后这个会话每次发消息，用的都是它自己记着的那个值，压根不会回头再看 `config.toml`。**

换成生活里的例子就好理解了——

> 你在购物软件里改了默认收货地址，但你**已经下好的那一单**，该寄哪儿还寄哪儿。默认地址只对**下一单**生效。

我这个会话是前一天深夜建的，那会儿我正用着 claude 系的模型；第二天我把 `config.toml` 改成了 gpt 系，**但那个会话根本不理我**，继续攥着它自己记住的 `claude-opus-5-5` 往上冲。

而我那把 API key 在中转服务商那边是绑了分组的，**这个分组里只有 gpt 系列**。于是就成了这样：

```text
客户端: 我要 claude-opus-5-5
网关:   你这把 key 没这个模型 → 503
客户端: 我要 claude-opus-5-5（重试 1）
网关:   503
客户端: 我要 claude-opus-5-5（重试 2）
网关:   503
... 44 秒，30 次，完美闭环 ...
```

搞清楚了之后再看那个报错，简直亲切得不行 (￣▽￣)


## 那为啥"hi 测试"是绿的？

这是整件事里最迷惑人的地方，也是我一度真的开始怀疑人生的原因。

因为**那根本是两条不同的路**：

| | 面板里的 hi 测试 | 聊天窗口发消息 |
| --- | --- | --- |
| 模型从哪儿来 | 当前 provider 的配置 | **会话自己钉住的值** |
| 受 `config.toml` 影响 | 是 | **否**（老会话） |
| 实际结果 | 200，秒回 | 503，重试到自闭 |

面板那个测试，本质是一次**连通性探测**——它只验证"这把 key + 这个地址，通不通"。它压根不关心你那个会话一路走来用的是哪个模型。所以它绿得理直气壮。

**"面板通了"，不等于"聊天能用了"**。这个认知差，坑了我整整一晚上。


## 遇到同类问题，怎么三分钟定位

把上面这套流程固化下来，其实就是三步：

**第一步，看请求实际带了什么模型。** 别信配置文件，信日志。本地代理一般会把转发目标打出来：

```bash
grep "请求目标" ~/代理目录/logs/*.log | tail -5
# 里面 model=xxx 才是真正发出去的那个
```

**第二步，看这个会话自己记着什么。** 就是上面那段 python，或者直接查 `threads` 表。

**第三步，改的时候记住：改 `config.toml` 只对新会话生效。**

- **最快的办法是新建一个会话。** 新会话会读当前 `config.toml`，一步到位。
- **想救老会话，就在界面上把模型选择器切一下。** 这一下会把该会话钉住的值改掉。

我最后就是用"新建会话"解决战斗的——新会话上来就是 `gpt-6.1-sol`，一次通过。


## 顺带踩到的另外三个坑

既然翻了一晚上，把路上其他几个坑也一并记下来，给后来人省点时间。

**坑一：`wire_api = "chat"` 已经不能用了。**

我第一反应是把协议从 `responses` 改成 `chat`（因为报错看着像是"少了个 messages 字段"），结果 Codex 直接拒绝启动：

```text
wire_api = "chat" is no longer supported
```

新版 Codex 只认 `responses`。所以正确的思路不是改协议，而是**让本地代理去做 `responses` ↔ `messages` 的转换**，配置文件里老老实实写 `responses` 就行。

**坑二：报错信息会把你往沟里带。**

我当时看到的是这么一句：

```text
HTTP 400: field messages is required
```

"缺 messages 字段？那我补上不就完了？"——但真相是：**这是协议层面的错配**。客户端说的是 Responses 协议（请求体里的字段叫 `input`），而网关那个端点实现的是 Messages 协议（要的是 `messages`）。字段名根本对不上，你补什么都是白搭。

所以记住：**看到"字段缺失"类的报错，先怀疑是协议没对上，而不是真去补那个字段。**

**坑三：带工具调用的多轮对话，是另一道坎。**

就算协议对上了，某些中转链路在处理**带工具调用的历史**时还是会翻车——因为上游返回的思考块是空的，回放的时候拼不出可签名的思考内容，于是直接 400。

单轮聊天能过，一进工具调用就挂。这个坑我目前是用"**claude 系的模型就走原生的 Claude Code，不进这条路**"绕开的，想彻底解决得看中转链路那边怎么补。


## 写在最后

回头看，这个坑其实特别典型：**我一直在改一个"只对下一个会话生效"的开关，然后纳闷为什么当前这个会话不听话。**

配置文件这种东西，太容易让人产生"我改了全局，所以一切都该听我的"这种错觉了。但很多工具的真实设计是——**全局配置只是"初始值"，一旦落到某个具体实例上，那个实例就有了自己的记忆。**

`config.toml` 是初始值，会话是实例，老会话有自己的记忆。

所以以后再遇到"配置明明改对了却不起作用"，先别急着怀疑人生，按这个顺序问自己三句：

1. 我改的这个东西，是"默认值"还是"当前值"？
2. 当前真正生效的那个值，存在哪儿？
3. 改完之后，需不需要重启 / 新建 / 重新触发一下才生效？

三句话问完，大部分玄学故障都能落地。

以上是个人的一些观察，如果有哪里说得不对的地方也请大佬们指出！

本文完结撒花！！！ 🎉

---

*PS：写完这篇我又回去看了一眼那个报 503 的老会话，它还躺在那儿，钉着 claude-opus-5-5 一动不动……算了，就当留个纪念吧。先溜了溜了*
