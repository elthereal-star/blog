---
title: "快慢指针是什么鬼？刷题刷到链表题，十个有九个都在考它"
date: 2026-06-09
draft: false
categories: ["算法"]
tags: ["算法", "链表", "双指针", "题解"]
summary: "朋友们好呀！不知道你们刚开始刷 LeetCode 的时候有没有这种感觉——链表题翻来覆去就是那几种花样，但你一看到\"双指针\"、\"快慢指针\"就心里发怵，总感觉…"
ShowToc: true
---


朋友们好呀！不知道你们刚开始刷 LeetCode 的时候有没有这种感觉——链表题翻来覆去就是那几种花样，但你一看到"双指针"、"快慢指针"就心里发怵，总感觉这玩意儿很高大上，自己搞不定。

别慌！今天咱就把快慢指针从头到尾给它盘个明明白白。看完之后你会发现：**原来这玩意儿就这么简单？我之前在怕啥？** (￣▽￣)~*

---

## 一、先搞明白啥是快慢指针

### 一个生活中的比喻

什么叫快慢指针捏？咱先不讲代码，讲个故事。

想象你和朋友在操场上跑步，你跑得**快**，朋友跑得**慢**。跑着跑着，如果操场是个**圆圈**，那你肯定会从后面追上朋友对吧？但如果操场是个**直线**，那你就永远追不上，只会越拉越远。

快慢指针就是这个道理——搞两个指针：
- **快指针**：每次走两步（或者多步），跑得快
- **慢指针**：每次走一步（或者少步），跑得慢

通过观察它俩的关系（是不是相遇了、距离是多大），我们能搞出各种骚操作。

### 代码长这样

```java
// 最基础的快慢指针
ListNode slow = head;   // 慢指针，一次走一步
ListNode fast = head;   // 快指针，一次走两步

while (fast != null && fast.next != null) {
    slow = slow.next;         // 慢指针步进 1
    fast = fast.next.next;    // 快指针步进 2
}
```

就这么简单，没了！就这！接下来咱看看这个简单的东西能干出什么花样来。

---

## 二、经典应用场景，一个比一个实用

### 场景一：判断链表有没有环（最经典的用法）

**问题是这样的**：给你一个链表，它可能某个节点的 next 指回了前面的某个节点，形成一个环。判断它有没有环。

{{< svg "fast-slow-pointer" >}}

这就回到操场跑圈那个例子里了：
- 如果链表是直的（没环），快指针跑到终点（null）就停了，它俩永远不会相遇
- 如果链表有环，快指针迟早会从后面追上慢指针，它俩会在环里的某个节点碰头

```java
public boolean hasCycle(ListNode head) {
    if (head == null) {
        return false;
    }

    ListNode slow = head;
    ListNode fast = head;

    while (fast != null && fast.next != null) {
        slow = slow.next;        // 慢指针走一步
        fast = fast.next.next;   // 快指针走两步

        if (slow == fast) {      // 它俩碰面了！！
            return true;         // 铁定有环
        }
    }

    // 快指针走到头了都没碰上，说明是直线
    return false;
}
```

**注意一个小细节**：while 循环条件里必须同时判断 `fast != null` 和 `fast.next != null`，因为快指针一次走两步，如果 `fast.next` 是空的还去访问 `fast.next.next`，直接给你空指针异常，原地爆炸 💥

---

### 场景二：找到环的入口节点（判断环的升级版）

上面只是判断有没有环，现在难度升级——不仅要判断有环，还要找到**环是从哪个节点开始的**。

这题的推导过程比较复杂，但**结论特别简单**：

1. 还是用快慢指针，先让它俩在环里相遇
2. 相遇之后，把慢指针（或者快指针也行）扔回头节点
3. 然后**俩指针都改成一次走一步**
4. 它俩再次相遇的那个节点，就是环的入口


```java
public ListNode detectCycle(ListNode head) {
    if (head == null) {
        return null;
    }

    ListNode slow = head;
    ListNode fast = head;

    // 第一步：找相遇点
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;

        if (slow == fast) {
            // 第二步：慢指针扔回头节点
            slow = head;

            // 第三步：俩指针都走一步，再次相遇就是入口
            while (slow != fast) {
                slow = slow.next;
                fast = fast.next;
            }
            return slow;  // 这就是环的入口！
        }
    }

    return null;  // 没环
}
```

为啥这么巧？咱不推导数学公式了哈（网上一搜一大把），你只需要记住结论就行：**相遇后，一个指针回起点，俩人都走一步，再相遇就是入口**。记住这个套路，面试的时候直接写，面试官会觉得你贼熟练 (｡･ω･｡)

---

### 场景三：找链表的中间节点

**问题是这样的**：给你一个链表，怎么一次遍历就找到中间节点？

不用快慢指针的时候你可能会想：先遍历一遍数长度，再走一半。这得遍历两次，太 low 了。

用快慢指针就优雅多了——快指针到终点的时候，慢指针刚好在中间：

```java
public ListNode findMiddle(ListNode head) {
    ListNode slow = head;
    ListNode fast = head;

    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
    }

    // fast 到末尾了，slow 正好在中间
    return slow;
}
```

**这就好比**：你和你朋友一起出发，他跑步你先走路。等他跑到终点的时候，你刚好走到一半。他的速度是你的两倍嘛，完美！

不过这里有个小坑：**当链表长度为奇数或偶数时，中间节点的定义不太一样**。上面的写法在偶数长度时会返回**靠右的中间节点**。如果你想要靠左的那个，可以让 fast 初始化为 `head.next`：

```java
// 偶数长度时返回靠左的中间节点
ListNode slow = head;
ListNode fast = head.next;  // 注意这里改成 head.next

while (fast != null && fast.next != null) {
    slow = slow.next;
    fast = fast.next.next;
}
```

在做题的时候看清楚题目要求，别搞反了哈。

---

### 场景四：删除链表的倒数第 N 个节点

这是 LeetCode 19 题，也是快慢指针的经典玩法。

思路很巧妙：让快指针**先走 N 步**，然后快慢指针一起走。等快指针走到头了，慢指针刚好在倒数第 N 个节点的**前一个**位置，删起来就方便了。


```java
public ListNode removeNthFromEnd(ListNode head, int n) {
    // 搞个哑节点，防止删的是头节点
    ListNode dummy = new ListNode(0);
    dummy.next = head;

    ListNode fast = dummy;
    ListNode slow = dummy;

    // 快指针先走 n+1 步（多走一步是为了让 slow 停在要删节点的前面）
    for (int i = 0; i <= n; i++) {
        fast = fast.next;
    }

    // 一起走，fast 到头了 slow 就在正确的位置
    while (fast != null) {
        slow = slow.next;
        fast = fast.next;
    }

    // 删掉 slow 后面的那个节点
    slow.next = slow.next.next;

    return dummy.next;
}
```

**dummy 节点是个好东西**，很多链表题的边界问题（比如删的是头节点），加个 dummy 就全解决了。咱做链表题的时候，想不清楚边界就直接上 dummy，省心省力 (￣▽￣)ノ

---

### 场景五：判断回文链表

**问题是这样的**：判断一个链表是不是回文的（正着读反着读一样，比如 1→2→2→1）。

这道题是快慢指针的一个综合应用，集合了"找中间节点"和"反转链表"两个操作：

1. 用快慢指针**找到中间节点**
2. **反转后半部分**链表
3. 前后两半**逐一比较**
4. （可选）把后半部分**反转回来**，还原链表

```java
public boolean isPalindrome(ListNode head) {
    if (head == null || head.next == null) {
        return true;
    }

    // 第一步：快慢指针找中间
    ListNode slow = head;
    ListNode fast = head;
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
    }

    // 第二步：反转后半部分
    ListNode secondHalf = reverse(slow);

    // 第三步：前后比较
    ListNode p1 = head;
    ListNode p2 = secondHalf;
    while (p2 != null) {
        if (p1.val != p2.val) {
            return false;
        }
        p1 = p1.next;
        p2 = p2.next;
    }

    return true;
}

// 反转链表的经典写法
private ListNode reverse(ListNode head) {
    ListNode prev = null;
    ListNode curr = head;
    while (curr != null) {
        ListNode next = curr.next;
        curr.next = prev;
        prev = curr;
        curr = next;
    }
    return prev;
}
```

一道题把快慢指针和反转链表都给考察了，面试超爱出这题，建议背下来（不是）——建议反复练到肌肉记忆！

---

## 三、快慢指针的各种变形玩法

好了，上面那些是基础操作，咱接下来看看快慢指针还能怎么玩。这些变形主要是**改速度**、**改起点**、**改判断条件**。

### 变形一：快指针速度不是 2，而是 k

有些题里快指针的速度不一定是 2，可能是 3、4，甚至是可变的 k。

```java
// 快指针每次走 3 步（不太常用，但确实存在）
ListNode slow = head;
ListNode fast = head;

while (fast != null && fast.next != null && fast.next.next != null) {
    slow = slow.next;
    fast = fast.next.next.next;  // 走 3 步
}
```

不过说实话，**这种题很少见**，绝大部分情况步进 2 就够了。如果你遇到需要找"1/3 位置"的题，把速度改成 3 就行。

### 变形二：快指针先走 N 步（追赶型）

删除倒数第 N 个节点就是这种变形——快指针不一定是"一次走两步"，而是"先出发走 N 步"。这种变形在需要**定位到某个相对位置**的时候特别好用。

```java
// 通用模板：快指针先走 K 步，然后一起走
ListNode fast = head;
ListNode slow = head;

// 快指针先走 K 步
for (int i = 0; i < k; i++) {
    if (fast == null) {
        return null;  // 链表长度不够 K
    }
    fast = fast.next;
}

// 然后一起走
while (fast != null) {
    slow = slow.next;
    fast = fast.next;
}

// slow 现在在某个"倒数"位置
```

### 变形三：快慢指针 + 哈希表（混合打法）

有些场景下光快慢指针不够用，得配合哈希表来一发：

```java
// 找到环的长度
public int cycleLength(ListNode head) {
    ListNode slow = head;
    ListNode fast = head;

    // 先找到相遇点
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) {
            // 相遇了，算环长
            int length = 1;
            ListNode p = slow.next;
            while (p != slow) {
                p = p.next;
                length++;
            }
            return length;
        }
    }
    return 0;  // 没环
}
```

这个变形就是在相遇之后，让一个指针再绕一圈，数一下走了多少步回到原处，就是环的长度。

### 变形四：双慢指针（滑动窗口型）

严格来说这不算快慢指针了，更像是"左右双指针"或者"滑动窗口"。但思想是相通的——两个指针以**不同节奏**移动：

```java
// 移动零到末尾（LeetCode 283）
// 一个指针扫数组，一个指针标记"该填非零值的位置"
public void moveZeroes(int[] nums) {
    int slow = 0;  // 标记"下一个非零元素该放的位置"

    for (int fast = 0; fast < nums.length; fast++) {
        if (nums[fast] != 0) {
            // 非零元素，搬到 slow 的位置
            int temp = nums[slow];
            nums[slow] = nums[fast];
            nums[fast] = temp;
            slow++;
        }
    }
}
```

这种"读指针/写指针"的变形在数组题里用得特别多，本质上和链表的快慢指针是一个思路——**一个负责探路，一个负责记录结果**。

---

## 四、快慢指针的通用解题思路（重点来了！）

好了朋友们，上面看了那么多例子，咱来总结一下遇到一道题该怎么想。掌握了这个思路，以后看到新题也能快速想到快慢指针。

### 思路一：问自己"我需要找到哪个位置？"

快慢指针本质上就是一把**定位尺**。遇到链表题，先想清楚：**我想要找到链表的哪个位置？**

- 需要找**中点**？→ 快指针两倍速，到头时慢指针在中点
- 需要找**倒数第 N 个**？→ 快指针先走 N 步，然后一起走
- 需要找**环的入口**？→ 先相遇，再一个指针回起点，一起走
- 需要找**1/3 位置**？→ 快指针三倍速

说白了，**控制两个指针的速度差和起步时间差，就能定位到各种位置**。

### 思路二：问自己"我关心的是相遇还是距离？"

快慢指针有两类核心逻辑：

**相遇型**：关注"两个指针会不会碰到一起"
- 判断环：如果相遇就有环
- 找环的入口：两次相遇

**距离型**：关注"快指针到头时，慢指针在什么位置"
- 找中点
- 找倒数第 N 个
- 删除倒数第 N 个

想清楚你关心的是"相遇"还是"距离"，基本就能确定用哪种快慢指针了。

### 思路三：dummy 节点是链表题的万能止痛药

做链表题，特别是涉及到**删除、插入、改头节点**的情况，上来就加个 dummy：

```java
ListNode dummy = new ListNode(0);
dummy.next = head;
// 然后从 dummy 开始操作，最后 return dummy.next 就行
```

加了 dummy 之后，头节点不再是特殊节点，不用单独判断了。这个习惯越早养成越好哈。

### 思路四：while 循环条件的记忆技巧

很多新手朋友写快慢指针最头疼的就是循环条件——到底该写 `fast != null` 还是 `fast.next != null`？

记住一个口诀：**快指针一次走几步，就要保证每次挪的时候前面有这么多步的空位**。

- 快指针走 2 步 → 需要确保 `fast != null && fast.next != null`
- 快指针走 3 步 → 需要确保 `fast != null && fast.next != null && fast.next.next != null`

为啥呢？因为如果 `fast.next` 是 null 你还去访问 `fast.next.next`，直接 NPE（空指针异常），程序就崩了。就像你想跑两步，结果第一步就踩坑里了，第二步直接就摔了 (。-ω-)zzz

---

## 五、刷题推荐（从易到难，跟着练就完事了）

光看不练假把式，给大家整一个快慢指针的刷题清单，按难度排好了，咱一个一个啃下来：

| 题号 | 题目 | 考啥 | 难度 |
|------|------|------|------|
| LeetCode 141 | 环形链表 | 判断有没有环 | 简单 |
| LeetCode 876 | 链表的中间节点 | 找中点 | 简单 |
| LeetCode 234 | 回文链表 | 找中点 + 反转链表 | 简单 |
| LeetCode 19 | 删除链表的倒数第 N 个节点 | 快指针先走 N 步 | 中等 |
| LeetCode 142 | 环形链表 II | 找环的入口 | 中等 |
| LeetCode 143 | 重排链表 | 找中点 + 反转 + 合并 | 中等 |
| LeetCode 287 | 寻找重复数 | 快慢指针在数组上的应用 | 中等 |
| LeetCode 202 | 快乐数 | 判断循环，快慢指针的巧妙应用 | 简单 |

建议按这个顺序刷，前两道练手感，后面逐渐加难度。尤其是 287 和 202 这两题，**把快慢指针从链表用到了数组上**，属于思维跃迁，刷完你会突然感觉"卧槽还能这么玩" (๑•̀ㅂ•́)و✧

---

## 六、补充几个常踩的坑

1. **空链表和单节点链表别忘了处理**：很多题在开头加一句 `if (head == null || head.next == null) return ...;` 就能避免一堆边界问题。

2. **快指针的循环条件必须同时判两个**：`while (fast != null && fast.next != null)` 而不是 `while (fast.next != null)`，因为如果 fast 已经是 null 了，访问 `fast.next` 就会空指针——注意短路求值的顺序哈。

3. **注意快慢指针的初始位置**：大部分题都是从 head 开始，但有些题需要微调（比如找中点靠左版本，fast 从 head.next 开始）。看清楚题目要求再下笔。

4. **在环中相遇后，别瞎改指针**：找环的入口那题，相遇后记得把一个指针扔回头节点，然后两个都改成走一步。**千万别忘了改速度**，不然又跑偏了。

5. **操作完链表记得还原**：像回文链表那题，面试官可能会问你"能不能不改动链表结构"，能还原的尽量还原一下，显得你考虑周全。

---

## 写在最后

快慢指针说到底就是一句话——**用两个不同速度或不同起点的指针，通过它们之间的位置关系来推导链表的结构信息**。

它没有什么高深的理论，就是几个固定的套路反复用。刚开始觉得绕很正常，多写几遍，写到肌肉记忆的时候，再看到链表题你就会条件反射："这不就是快慢指针嘛，秒了！"

以上是个人的一些刷题经验和理解，希望能帮到正在和链表题较劲的朋友们。如果有哪里有什么错误的地方也请大佬们指出，咱一起进步嘛~

本文完结撒花！！！ ✿✿ヽ(°▽°)ノ✿
