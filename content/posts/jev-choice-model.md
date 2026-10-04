---
title: "那个\"不会说话\"的 AI 火了！Jev：比 ChatGPT 快 200 倍、便宜 400 倍的\"选择困难症终结器\""
date: 2026-09-23
draft: false
categories: ["AI"]
tags: ["Jev", "Spring AI", "大模型", "Java"]
summary: "咱就是说，各位朋友在做后端的时候，有没有被这么一类需求折磨过："
ShowToc: true
---


咱就是说，各位朋友在做后端的时候，有没有被这么一类需求折磨过：

用户发来一条客服工单，你得判断它属于"支付问题"还是"技术故障"；用户写了一段留言，你得判断他"生不生气"；AI 生成了一段回答，你得判断它"有没有胡说八道"……

这些活儿吧，本质上都不是"生成内容"，而是**做个判断**。

但是捏，我们手上能用的大模型，全都是"话匣子"——你让它判断个分类，它非要先跟你唠两句：

```text
好的，我来帮你分析一下这条工单。
首先，用户提到了"Stripe 账户连接不上"，这属于支付相关的问题...
综合分析，这条工单应该归类为：billing
```

好家伙，为了拿到最后那个 `billing`，我们得写一大堆 prompt 约束格式、再写正则去解析 JSON、还得处理它偶尔抽风给你加个 markdown 代码块的情况。慢也就算了，这一来一回几百毫秒到几秒不等，钱还哗哗地流。

**如果有一个模型，它压根不跟你废话，你问它问题它直接给你答案和概率呢？**

这，就是今天的主角 —— **Jev**。2026 年 9 月刚出的新东西，火得那叫一个离谱。


---

## 先唠唠 Jev 是个啥来头

Jev 是 **TypeSafe AI** 在 2026 年 9 月 15 日发布的模型。这家公司的创始人叫 **Diogo Almeida** —— 这位大佬是前 OpenAI 研究员，参与过 ChatGPT、InstructGPT、GPT-4 的工作，**RLHF（人类反馈强化学习）就是他主导搞出来的**。听说过这个词的朋友应该知道，现在所有大模型的"对齐"几乎都建立在 RLHF 之上。

公司闷头干了大约两年，拿了 **DCVC 领投的 4000 万美元种子轮**。

那 Jev 跟现在的大模型有啥不一样捏？一句话：

> **Jev 不是语言模型，它不生成文本。**

你给它一段"状态"（`state`，可以是一条工单、一封邮件、一段日志、一份程序状态），再给它一组**预先定义好类型的问题**，它直接返回：

- 一个**答案**
- 这个答案的**完整概率分布**
- 一个**置信度**

没有"好的我来帮你分析一下"，没有流式输出，没有 tool call，甚至**没有 markdown 代码块**。

扎心的是，它因为不用一个字一个字往外蹦（不做自回归解码），快得有点离谱——官方给的数据是**端到端 70~500 毫秒**，比前沿大模型最快约 **194 倍**；价格是**输入每百万 token 0.042 美元，输出免费**，最便宜约 **445 倍**。

**注意一下哈**：这些倍数是 TypeSafe 自己的能力团队测的，官方自己都承认"这是实际收益的上限"。所以咱先听个热闹，具体还得看咱们自己的场景。

---

## 为啥它能这么快？打个比方你就懂了

咱们用考试来类比一下。

**传统大模型 = 写作文的考生。**
你问它一道选择题，它非要工工整整地把题干抄一遍、把 A 选项分析一遍、把 B 选项否定一遍、最后才写下"答案选 C"。写作文这事儿，你没法并行——第一个字没写完，第二个字就不知道写啥，只能一个字一个字往下挤。这就是**自回归解码**。

**Jev = 涂答题卡的考生。**
题目一拿到手，选项早就印好了，它做的只有一件事：**在 A、B、C、D 之间分配注意力，然后涂一个（顺便告诉你每个选项它有多想涂）**。输出的可能性空间是**提前定死**的，所以它可以并行采样、一次前向计算就出结果。

这就是它"快"和"便宜"的全部秘密：**不生成，所以不用解码；不解码，所以能并行。**

顺带一提，它对"幻觉"的定义也变了。因为你已经把答案选项锁死了，所以它**不可能**给你编出一个选项之外的东西（比如输出一个 JSON 里不存在的字段、或者多吐一段废话）。官方管这叫"零幻觉"。

**但是！** 这只是说它不会答到选项之外去，**不代表它一定选对**。这个坑后面细说，非常重要。

---

## 核心：三种"问题类型"，才是 Jev 的灵魂

Jev 的 API 里，你能问的问题只有三种类型。别看少，组合起来能覆盖特别多的场景。

### 一、Noul —— 是非题，给你一个概率

Noul 用来问"**这件事成立吗？**"，返回一个 0~1 的数值，也就是"是"的概率。

```text
noul = 0.98  →  几乎可以确定"是"
noul = 0.50  →  五五开，它也不知道
noul = 0.02  →  基本可以确定"不是"
```

**这里有个特别容易搞混的点**：`0.5` 不是"中等"，而是"**我完全没把握**"。它衡量的是"是的概率"，不是"强度"。

### 二、Choice —— 单选题，最多 255 个选项

Choice 用来问"**这几类里，它属于哪一类？**"，返回选中的选项、每个选项的概率、以及置信度。

```text
choice     = billing          # 它选了哪个
probabilities = {billing: 0.91, technical: 0.07, other: 0.02}
confidence = 0.91
```

注意这里有个**容易踩坑的细节**：`confidence`（置信度）和各个选项的 `probabilities`（概率）是**两个不同的字段**。

- `probabilities` 是"它认为各个选项分别是啥"，是一个分布
- `confidence` 是"这个分布有多集中"，也就是它对自己这次判断的整体把握

官方强调：**置信度是"路由决策的依据"，不是"质量分"**。两个字段别混着用。

### 三、Score —— 打分题，2~10 级有序标尺

Score 用来问"**在这把有顺序的尺子上，它落在哪儿？**"，返回概率加权后的位置（可以是小数）、各档位概率、置信度，还有一个 `legend`。

```text
score = 2.97 / 3
```

**写 Criteria 的时候有个很实用的建议**：把每一档描述成"**可检验的具体情况**"，而不是"模糊的程度"。比如：

- ✅ 好的写法：`["已有临时绕行方案", "本周内需要修复", "现在就得回复"]`
- ❌ 差的写法：`["低", "中", "高"]`

前者是能拿材料去对上的，后者纯靠模型猜，结果会飘。

---

## 上手实战：Java 里怎么接进来

好，铺垫完了，咱们整点实在的。这部分给三种方式，从"手搓"到"开箱即用"，朋友们按需取用。

### 方式一：手搓 HTTP 调用（适合先摸清楚它长啥样）

Jev 的接口非常简单，就三个顶层字段。官方端点是 `POST https://api.typesafe.ai/v1/systemone`：

```bash
curl -X POST https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jev-latest",
    "state": "我的 Stripe 收款连续三天失败了，一直连不上，急死了！",
    "questions": {
      "is_urgent": {
        "type": "noul",
        "instructions": "这条消息表达了紧急或时间敏感性吗？"
      },
      "team": {
        "type": "choice",
        "instructions": "这条工单该由哪个团队处理？",
        "criteria": {
          "billing": "支付、账单、退款相关",
          "technical": "Bug、故障、集成问题",
          "other": "以上都不是"
        }
      },
      "severity": {
        "type": "score",
        "instructions": "客户受到的影响有多严重？",
        "criteria": ["等一周也行", "本周内要处理", "今天就得出结果"]
      }
    }
  }'
```

返回长这样：

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_urgent": { "type": "noul", "noul": 0.99 },
    "team": {
      "type": "choice",
      "choice": "billing",
      "probabilities": { "billing": 0.91, "technical": 0.07, "other": 0.02 },
      "confidence": 0.91
    },
    "severity": { "type": "score", "score": 2.97, "confidence": 0.93 }
  },
  "usage": { "input_tokens": 671, "output_tokens": 39 }
}
```

你瞅瞅这个返回，**没有一句废话**，全是能被代码直接消费的结构化数据。`is_urgent` 拿去判断要不要升级、`team` 拿去路由工单、`severity` 拿去排序，一行 if 就完事。

顺手用咱之前聊过的 HttpClient 手搓一个 Java 版调用（JDK 11+ 自带，不用引任何依赖）：

```java
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;

public class JevRawDemo {

    private static final String ENDPOINT = "https://api.typesafe.ai/v1/systemone";
    private static final HttpClient CLIENT = HttpClient.newHttpClient();

    public static String evaluate(String apiKey, String state) throws Exception {
        // 注意：questions 里的每个问题都要带 type 和 instructions
        // criteria 的 key 就是 Choice 的候选选项
        String body = """
            {
              "model": "jev-latest",
              "state": %s,
              "questions": {
                "is_urgent": {
                  "type": "noul",
                  "instructions": "这条消息表达了紧急或时间敏感性吗？"
                },
                "team": {
                  "type": "choice",
                  "instructions": "这条工单该由哪个团队处理？",
                  "criteria": {
                    "billing": "支付、账单、退款相关",
                    "technical": "Bug、故障、集成问题",
                    "other": "以上都不是"
                  }
                }
              }
            }
            """.formatted(toJsonString(state));

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(ENDPOINT))
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();

        HttpResponse<String> response = CLIENT.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new RuntimeException("调用失败，状态码=" + response.statusCode()
                    + "，响应=" + response.body());
        }
        return response.body();
    }

    // 简单粗暴的字符串转义，生产环境请换 Jackson
    private static String toJsonString(String raw) {
        return "\"" + raw.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
}
```

**动手之前有两个坑要提前告诉你**：

**坑一：字段名不统一。** 不同网关的请求体字段名是不一样的。官方 / 部分网关用 `"type"` 加 `"criteria"`，而有些网关的适配层用的是 `"kind"`。**接之前先看一眼你调的那个端点文档**，不然会得到一个 400 然后对着代码发呆。

**坑二：中文准确率会掉。** Jev 主要用英文训练，中文虽然能识别，但准确率确实比英文弱一截。官方自己的建议就是：**做细腻的中文语义分析前，先用小样本测一下**。这个后面"坑点预警"里会展开说，有实测数据的。

### 方式二：用官方 / 社区 SDK（省事版）

如果觉得手搓太麻烦，社区和官方都提供了 SDK。

Python 那边是 `pip install typesafe-sdk`，Java 这边有个**社区维护的 JVM SDK**，纯 Java 17+，**唯一依赖只有 Jackson**，不绑 Spring AI 那套抽象：

```java
TypeSafeClient client = TypeSafeClient.fromEnv(); // 读 TYPESAFE_API_KEY

SystemOneResult result = client.evaluate(
        EvaluationRequest.of("我的收款连续三天失败了，急死了！")
                .noul("is_urgent", "这条消息表达了紧急或时间敏感性吗？")
                .choice("department", "该由哪个团队处理？", Map.of(
                        "billing", "支付、账单、退款相关",
                        "technical", "Bug、故障、集成问题"))
                .score("frustration", "客户有多生气？",
                        List.of("平静", "不满但克制", "非常愤怒")));

// 拿到结果后就能直接写业务分支了
if (result.noul("is_urgent").isYes(0.7)) {
    escalate(); // 紧急，升级处理
}

ChoiceAnswer dept = result.choice("department");
if (dept.confidenceOrZero() < 0.5) {
    routeToHuman(); // 置信度太低，别硬路由，转人工
}
```

**看到 `confidenceOrZero() < 0.5` 这个判断没？** 这就是 Jev 最正确的用法之一：**低置信度不当答案用，而是当"需要人工介入"的信号**。把它当成一个"我拿不准"的开关，比硬信一个 0.52 的结果靠谱多了。

Spring Boot 的话，有 starter 可以用，自动配置好客户端直接注入：

```xml
<!-- 官方 starter，自动配置 TypeSafeClient -->
<dependency>
  <groupId>io.typesafe</groupId>
  <artifactId>typesafe-ai-java-spring-boot-starter</artifactId>
</dependency>
```

配置里塞上 `jev.api-key` 就能直接注进 Service 里用了。

### 方式三：Spring AI 的 JevJudge（这套是真香）

Spring 官方博客在 9 月 21 日专门写了一篇 Jev 的集成介绍，社区也出了 `spring-ai-typesafe`（0.1.0）。它没把 Jev 硬塞进 `ChatModel` 抽象里（毕竟 Jev 没消息、没生成、没流式，硬套反而别扭），而是给了一个**"判据"构建器** `JevJudge`。

思路特别符合直觉：**每条判据 = 一个问题 + 它必须达到的阈值**。

```java
JevJudge judge = JevJudge.builder(typeSafeClient)
        .score("helpfulness", helpfulnessRubric, 2.0d)   // 有用性至少 2.0 分
        .noul("is_plausible", plausible, 0.8d)           // 可信度至少 0.8
        .noul("is_grounded", grounded, 0.8d)             // 有依据至少 0.8
        .build();

JevVerdict verdict = judge.judge(question, answer);
```

一次调用，**所有判据并行评估**，每条判据保留自己的阈值。跑出来大概是这样：

```text
answer   : It is currently -455 degrees Celsius in Paris.
passed   : false
  helpfulness    INCONCLUSIVE  0.83 (confidence 0.44)
  is_plausible   FAILED        0.02
  is_grounded    PASSED        0.89
```

这里有个设计我觉得挺妙的：**置信度低于默认下限 0.5 的时候，判据返回的是 `INCONCLUSIVE`（没法判定），而不是 `FAILED`（判负）**。

为啥要这样捏？因为"没把握"和"确定有问题"是两回事。虽然它们都能拦住答案，但语义完全不同。如果你希望**宁可错杀不可放过**，可以开 `failOnInconclusive(true)`，把"没验证成功"当成比"拒绝"更糟的结果。

更香的是它还能和 Spring AI 的 advisor 管道串起来，做成一个**自纠正循环** `JevSelfRefineAdvisor`：

```java
ChatClient chatClient = ChatClient.builder(chatModel)
        .defaultTools(new WeatherTools())
        .defaultAdvisors(JevSelfRefineAdvisor.builder()
                .judge(WeatherJudge.create(typeSafeClient))
                .build())
        .build();
```

它干的事特别简单粗暴但有效：

1. 模型先答一版
2. Jev 一次调用**并行检查所有判据**
3. 全过 → 直接返回答案
4. 有不过的 → 把失败判据的说明、分数、阈值**追加到原始 prompt**，重新问一次，最多重试 `maxRepeatAttempts` 次

跑起来日志是这样：

```text
WARN  Jev judgement failed on attempt 1: passed=false
      [helpfulness=INCONCLUSIVE, is_plausible=FAILED, is_grounded=PASSED]
      - is_plausible: 至少有一个数值是不可能的 ... (scored 0.02, needs at least 0.70)
INFO  Jev judgement passed on attempt 2: passed=true
      [helpfulness=PASSED, is_plausible=PASSED, is_grounded=PASSED]

FINAL ANSWER: It is currently 15 degrees Celsius and overcast in Paris.
model calls: 2
```

**第一次答了个 -455 摄氏度**（比绝对零度还低，物理上不可能），被 `is_plausible` 判据一票否决，然后带着反馈重答一次，第二次就对了。

以前我们要干这事，得自己写一个"裁判 prompt"、再调一次大模型、再解析 JSON。现在换成 Jev，**一次几百毫秒、成本几乎可以忽略、还是结构化的**。这就是它真正的价值所在。

---

## Jev 到底适合干啥？

唠完代码，咱们看看它实际能用在哪。说白了，**只要你的需求是"做判断"而不是"写内容"，大概率都能用**。

### 场景一：工单 / 消息的分类与路由

客服工单分派、邮件分类、意图识别、优先级排序。这是最典型的用法，前面代码演示的就是这个。

### 场景二：给 AI Agent 当"裁判"

这个是目前社区里最火的方向，**用 Jev 给 Agent 的输出打分**：

- 答案有没有事实依据？（`is_grounded`）
- 有没有物理上不可能的内容？（`is_plausible`）
- 有没有跑题、有没有危险内容？

LangChain 做过测试，在 500 次判断上 Jev 的评分和人类评分**基本一致**，而且分数方差远小于 GPT / Claude，成本更是低得多。

### 场景三：大模型路由（这一招很省钱）

不同的请求没必要都上最贵的模型。先用 Jev 判断一下"这问题简单还是复杂"，简单的走小模型，难的才上大模型：

```java
// 花 0.0000 几美元判断一下，可能省下一大笔
ChoiceAnswer complexity = result.choice("complexity");
ChatModel target = complexity.choice().equals("simple") ? smallModel : bigModel;
```

### 场景四：上下文压缩 / 长文本筛选

RAG 场景里，检索出来一堆文档片段，先让 Jev 判断"这段和问题相关吗"，把不相关的扔掉再喂给大模型，**既省钱又提高准确率**。

### 场景五：内容安全与风险筛查

判断一段内容是不是违规、是不是有风险。它返回的是**概率**而不是"是/否"，所以你可以自己定阈值，做分级处理。

### 场景六：浏览器自动化 / 表单填报

社区已经有人把它用在浏览器 Agent 上——"这个按钮点哪个""这个表单该填啥"，用本地小模型加 Jev 做决策。有个开源项目把它封装成了 Agent Skill，可以本地离线跑，一行命令接进 Claude Code、Codex。

---

## 坑点预警（重点！这一段建议反复看）

下面这些不是危言耸听，是官方文档自己都列出来、以及独立测评**实测出来**的短板。**在大家上手之前，一定要留意它目前非常明显的"偏科"**。

### 坑一：算数、数数、日期推算，它非常不靠谱

官方文档相当坦诚地承认了这一点：Jev 本质上是个"专科生"，**在数数、精确算数、日期先后推算上非常不可靠**；**长链条的多跳推理准确率也会肉眼可见地下滑**。

有媒体做过一组 190 次的实测（每道题重复 3~5 遍），结果挺说明问题的：

- 纯语义的题（行业事件判断、基本面定性）**多次全对**，表现很好
- 但**涉及计算**的题（比如"用两年收入和成本判断毛利率方向"），15 次只对了 4 次
- 有一道关于营业成本增速的题，**10 次全错，而且它的把握始终很高**

最要命的是最后那句——**它错得很自信**。

### 坑二：越靠近选项分界线，越容易翻车

同一组实测里有个很明显的规律：**贴着分界线的判断特别容易错**，而离分界线比较远的判断基本都对。

所以你写 Criteria 的时候，**别把两个相邻档位写得太接近**，不然模型就是在刀尖上跳舞。

### 坑三：没有正确答案的时候，它会硬选一个

**这个坑我觉得是最危险的。**

那组实测里有这么个案例：三家公司的备选描述，**全部与材料事实矛盾**，而且选项里**没有"以上都不对"这一项**。结果呢？**15 次它都选了一个，把握从六成到将近十成不等**。

换句话说：**它的"把握度"只衡量"在给定答案里的相对偏好"，不代表真的正确。** 把它心中的正确答案拿掉，它对错误选项一样能给出 80% 以上的把握。

**所以一定要记住：写 Choice 的时候，务必加一个"other / unclear / 以上都不对"的兜底选项！** 这是无数人踩过的坑换来的经验。

### 坑四：置信度（confidence）不是正确率

前面说过了，但值得再说一遍。**置信度只反映"分布有多集中"，不代表"它有多对"。** 概率接近 0.55 的时候，正确的做法是当成"**需要复核**"，而不是当成一个决定。

### 坑五：中文准确率确实会掉

模型主要以英文训练，中文能识别但准确率确实弱一截。有媒体用 **50 条中文客服消息**做过测试，Jev 的完整准确率大约在 **64% ~ 65.2%**，平均响应不到一秒，成本约 0.002 美元。

快是真快、便宜是真便宜，但**准确率并没有压过更强的通用模型**。

**所以如果你要做中文精细语义的场景，务必先拿几十条真实数据跑个小样本测试**，别直接把英文环境的参数照搬过来。

### 坑六：高风险操作，代码层的兜底不能省

Jev 不做生成，所以它**不能帮你完成交付**——不写文案、不写代码、不解释理由、不聊天。它更适合当**内部判断模块**嵌在流程里，而不是直接面对终端用户。

而且，**涉及退款、资金、删库这类高风险操作，底层的硬性权限校验和规则拦截该留还得留**。别指望一个概率值替你兜住安全底线。它是个好参谋，但不能当决策人。

### 坑七：Prompt 注入依然存在

虽然它不生成文本，但如果你在 `state` 里夹带诱导性指令，**它照样可能被带偏选错选项**。别以为它不是 LLM 就天然免疫。

### 坑八：区域与限额

- 有报道称**该服务尚未向中国大陆开放**，要用的话可能得走 OpenRouter 这类网关
- **限速**：官方给的是每秒最高 25 万 token、每分钟 1200 请求
- **上下文**：`state` 加上最长的问题**不超过 32K token**，超了会被直接拒收（有实测里整章中文原文就因为超限被拒）
- 只能吃**文本**，图片 / 音频 / 视频得先转成文本

---

## Jev vs 用大模型当裁判，到底差在哪？

给朋友们整个对比表，一眼就明白：

| 维度 | Jev | 传统 LLM 当裁判 |
| --- | --- | --- |
| 输出 | 结构化答案 + 概率 + 置信度 | 自然语言，要自己解析 |
| 延迟 | 70~500ms | 通常几秒 |
| 成本 | 输入 $0.042 / 1M token，输出免费 | 高出好几个数量级 |
| 方差 | 低（LangChain 实测 500 次判断方差远小于 GPT/Claude） | 较高，同样输入可能给不同结果 |
| 会不会跑出选项外 | 不会（输出空间提前定死） | 会，得靠 prompt 和解析兜着 |
| 会不会选错 | 会，而且可能错得很自信 | 会，但至少还能看到推理过程 |
| 能不能解释理由 | **不能** | 能 |
| 能不能算数 / 推日期 | **弱** | 相对强一些 |
| 适合干啥 | 分类、打分、判定、路由、护栏 | 需要解释、需要生成、需要多跳推理 |

**一句话总结**：**它不替代大模型，它是给大模型打下手、帮大模型省钱省时间的那一个。**

---

## 顺带一提：这名字起得有点东西

Jev 这个名字来自 19 世纪经济学家 **William Stanley Jevons**，指的就是那个著名的"**杰文斯悖论**"：

> 当某种资源的使用效率提高、成本下降时，**人们的总消耗量反而会增加**，而不是减少。

放到这儿就是：**当"智能"变得足够便宜，我们就会到处都用它**——以前觉得"为了一句分类判断就调一次大模型，太浪费了"，现在便宜到可以忽略，那就从"偶尔用"变成"处处用"。

这个起名，我给满分。😎

---

## 总结

回顾一下咱们今天唠的：

1. **Jev 的本质**：不生成文本的"判断模型"，输入状态 + 类型化问题，输出结构化答案 + 概率 + 置信度
2. **为什么快**：不做自回归解码，输出空间提前定死，能并行采样 —— 从"写作文"变成"涂答题卡"
3. **三种原语**：`Noul`（是非 + 概率）、`Choice`（单选，≤255 项）、`Score`（2~10 级打分）
4. **Java 接入**：手搓 HTTP → 社区 SDK → Spring Boot Starter → Spring AI 的 `JevJudge` + 自纠正循环
5. **最大的坑**：算数 / 日期推算 / 多跳推理很弱；**没正确答案时会自信地硬选一个**；中文准确率会掉；**高风险操作必须代码兜底**
6. **最正确的姿势**：把置信度当"是否需要人工介入"的信号用，并且**永远记得给 Choice 加一个"以上都不对"的兜底选项**

Jev 这个东西吧，说实话，它让我有点小激动。它不是又一个"更会聊天的 AI"，而是**换了个思路**——把"判断"这件事从对话里拆出来，做成一个又快又便宜、还能被代码直接消费的零件。

以前我们让大模型做分类，是在用牛刀杀鸡；现在终于有人专门造了把"杀鸡刀"，而且还挺锋利。

当然啦，它偏科也是真的偏，**别神化它，也别急着什么活儿都往上套**。先想清楚你的场景到底是"生成"还是"判断"，再决定要不要用它。

以上是个人的一些经验分享，Jev 毕竟是个刚出没多久的新东西，网上的资料我也只能搜个大概，**如果有哪里写错了、或者大佬们有更准的实践数据，欢迎在评论区指出来**～

本文完结撒花！！！🎉✨

---

*相关阅读：*
- [HTTPClient的介绍以及应用场景](/blog/posts/http-client-guide/)
- [SpringBoot的简化开发，爽到飞起](/blog/posts/spring-boot-simplify/)
- [RAG核心工作流程，给大模型装上你的私房知识库](/blog/posts/rag-core-workflow/)
- [懒加载与渐进式披露的设计思想以及应用场景](/blog/posts/lazy-loading-progressive-disclosure/)

---

**参考来源：**

- [Jev Documentation - TypeSafe Decision Model on OpenRouter](https://openrouter.ai/docs/guides/community/jev)
- [Jev Tutorial - Make Your First Decision Call on OpenRouter](https://openrouter.ai/docs/guides/community/jev-tutorial)
- [Spring AI and TypeSafe Jev: Fast, Cheap, Structured Decisions](https://spring.io/blog/2026/09/21/spring-ai-typesafe-structured-judgment)
- [How to Use Jev in Python: Choice, Noul, Score + OpenAI Comparison](https://mljar.com/blog/jev-python/)
- [爆火的Jev 是什么：前 OpenAI 研究员做的"不说话"模型](https://news.qiniu.com/archives/1789895633449)
- [Jev 使用完整指南：从申请 API Key 到置信度路由](https://news.qiniu.com/archives/1789969178302)
- [实测Jev：没那么强，但足够给有些乏味的AI圈带来新刺激 - 品玩](https://www.pingwest.com/a/317597)
- [我们用190次财报任务实测了Jev：当AI判断被卖成零件 - 36氪](https://www.36kr.com/p/3992972828097536)
- [刷屏全球AI新顶流Jev全攻略 零语言交互玩法深度解析 - 36氪](https://eu.36kr.com/zh/p/3991613388241920)
- [A new kind of AI model from a ChatGPT inventor is thrilling developers](https://tech.yahoo.com/ai/chatgpt/articles/kind-ai-model-chatgpt-inventor-184930808.html)
- [jev-capability-atlas：Jev 能力边界独立实测](https://github.com/Zaious/jev-capability-atlas)
- [golang 客户端 jev-sdk-go](https://github.com/ajayk/jev-go-sdk)

**附：文中数据均来自公开报道与官方文档，其中延迟 / 成本倍数（约 194 倍、约 445 倍）为 TypeSafe 官方自评数据，官方承认"是实际收益的上限"；模型权重、架构与论文尚未公开，基准测试也以官方自评为主，朋友们上手前建议先用自己的数据小样本实测一遍。**
