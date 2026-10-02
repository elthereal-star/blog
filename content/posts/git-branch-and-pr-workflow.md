---
title: "新手踩坑记：Git 分支与 PR 的最小可用流程"
date: 2026-09-28
draft: false
description: "从只会 git add/commit/push，到能独立跑完一个分支 + PR 的完整流程，以及四个让我卡了半天的坑。"
summary: "分支不是给大佬准备的仪式，它解决的是一个很具体的问题：我改了一半的代码，不想让 main 变成半成品。这篇是我从零跑通分支 + PR 流程的完整记录。"
tags: ["Git", "GitHub", "版本控制", "新手向"]
categories: ["工具链"]
ShowToc: true
---

## 我最初的困惑

一开始我的工作流只有三条命令：

```bash
git add .
git commit -m "改了点东西"
git push
```

能跑，但有两个问题越来越难受：

1. **改到一半的代码直接进了 `main`。** 别人（或者三天后的我）拉下来的就是半成品。
2. **没有任何审查环节。** 我自己看一遍和提个 PR 让别人看一遍，代码质量差别很大。

分支就是为了解决第一个问题的。

## 分支解决了什么问题

用一句话概括：**`main` 分支永远是可用的，所有实验性改动都发生在别的分支上。**

```text
main        ──●────────────●────────────●──►   始终可用
               \          / \          /
feature/login   ●───●────●   ●────●───●         写坏了就丢掉，不影响别人
```

真出了事的场景很常见：写了两天的功能发现方向不对，直接删掉分支就行；`main` 上一个字都没被污染。

## 一套够用的命名约定

不用记太多，能看懂就够了：

| 前缀 | 用途 | 例子 |
| --- | --- | --- |
| `feature/` | 新功能 | `feature/user-login` |
| `fix/` | 修 bug | `fix/login-timeout` |
| `docs/` | 只改文档 | `docs/readme-quickstart` |
| `refactor/` | 重构，不改行为 | `refactor/extract-service` |

## 完整流程：从建分支到合并

假设要加一个登录功能。

**第一步，先确认自己在 `main` 且是最新的：**

```bash
git switch main
git pull
```

这两步很重要。如果从过期的 `main` 切分支，后面合并时冲突会多很多。

**第二步，建并切换到新分支：**

```bash
git switch -c feature/user-login
```

`-c` 是 create。这条命令等于 `git branch feature/user-login` + `git switch feature/user-login`。

**第三步，正常写代码，正常提交：**

```bash
git add src/main/java/.../LoginController.java
git commit -m "feat: 新增登录接口"
```

提交信息建议带前缀，和分支命名保持一致的风格：

```text
feat:     新增功能
fix:      修复缺陷
docs:     文档变更
refactor: 重构
test:     测试相关
chore:    构建/依赖等杂项
```

**第四步，推到远端并建立跟踪关系：**

```bash
git push -u origin feature/user-login
```

`-u` 是 `--set-upstream`，设置一次之后，以后在这个分支上直接 `git push` 就行。

**第五步，在 GitHub 上提 Pull Request。**

推完之后 GitHub 会在仓库首页弹一个黄色的 "Compare & pull request" 按钮，点进去填标题和描述。描述里我一般写三段：

```markdown
## 做了什么
- 新增 /api/auth/login 接口
- 密码用 BCrypt 存储

## 怎么验证
1. mvn spring-boot:run
2. curl -X POST localhost:8080/api/auth/login -d '{"username":"a","password":"b"}'
3. 期望返回 {"code":0,...}

## 还没做的
- 登录失败次数限制（下个 PR）
```

**第六步，合并。**

PR 页面上点 **Merge pull request**，然后本地把分支清理掉：

```bash
git switch main
git pull
git branch -d feature/user-login          # 删本地分支
git push origin --delete feature/user-login  # 删远端分支
```

## 四个让我卡了半天的坑

### 坑 1：`git log` 之后终端「卡死」了

执行 `git log` 或者 `git diff` 之后，屏幕底部出现一个 `:`，怎么按都没反应，Ctrl+C 也不好使。

**这不是卡死，是进了分页器（pager）。** 它把长输出分成一页一页让你翻。

| 按键 | 作用 |
| --- | --- |
| `空格` / `f` | 下一页 |
| `b` | 上一页 |
| `q` | **退出**（记住这个就行） |

按 `q` 立刻回到命令行。

如果你和我一样讨厌这个行为，可以永久关掉分页器：

```bash
git config --global core.pager cat
```

### 坑 2：提交上去了，但 GitHub 贡献图不亮

现象：`git push` 成功，仓库里能看到提交，但**个人主页的贡献格子是灰的**，点进仓库看提交，作者头像也不是自己的。

原因：**提交用的邮箱和 GitHub 账号里登记的邮箱对不上。**

查一下当前配置：

```bash
git config --global user.name
git config --global user.email
```

再看看某次提交实际用的邮箱：

```bash
git log -1 --format="%an <%ae>"
```

如果这里显示的是 `175216767+elthereal-star@users.noreply.github.com` 这种形式，而你又没在 GitHub 设置里绑定过它，那这次提交就不会算到你头上。

**解决办法**，统一成一个 GitHub 认得的邮箱：

```bash
git config --global user.name "elthereal-star"
git config --global user.email "你的QQ邮箱@qq.com"
```

> 用 GitHub 提供的 noreply 邮箱也可以，但要去 `Settings → Emails` 里确认那个地址确实是分配给你的。
> 另外：**改配置只影响之后的提交**，之前那些灰格子不会补亮。

### 坑 3：把不该提交的东西提交了

比如 IDE 的 `.idea/`、编译产物 `target/`、本地的 `application-local.yml`、还有各种存密码的 txt。

预防靠 `.gitignore`，在仓库根目录建一个：

```gitignore
# 构建产物
target/
dist/
*.class
*.jar

# IDE
.idea/
*.iml
.vscode/

# 本地配置与日志
*.log
application-local.yml

# 系统
.DS_Store
Thumbs.db
```

如果已经提交了，先让 Git 停止跟踪（文件本身不删）：

```bash
git rm -r --cached .idea
git commit -m "chore: 停止跟踪 IDE 配置"
```

### 坑 4：推错了分支，想撤回

分两种情况：

**已经 push 了，但只是想把改动挪到别的分支：**

```bash
git switch 目标分支
git cherry-pick <那个提交的哈希>
```

**只是想撤销最近一次提交（还没 push）：**

```bash
git reset --soft HEAD~1   # 撤销提交，改动保留在工作区
```

`--soft` 是保住改动，`--hard` 是连改动一起扔——**`--hard` 很危险，用之前想清楚。**

## 一个练习用的仓库

光看没用，我自己是开了一个专门的练习仓库反复练这套流程的：建分支、改文件、提交、推送、提 PR、合并、删分支。跑通两三轮就形成肌肉记忆了。

建议你也开一个，别拿正经项目练手。
