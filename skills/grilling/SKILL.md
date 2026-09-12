---
name: grilling
description: "Grill the user relentlessly about a plan, decision, or idea: work a design tree in rounds, asking every currently-answerable question with a recommended answer. Use when the user wants to stress-test their thinking or says 拷问我 / grill me."
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
  source: "https://github.com/mattpocock/skills (MIT)"
---

# 拷问式访谈（grilling）

对用户的方案、决策或想法发起**连环追问**，直到双方达成共识。把方案映射成一棵**设计树（design tree）**：每个决策下面挂着由它派生的子决策。

按**轮次（round）**推进这棵树。**当前可答集（frontier）**= 前置条件已全部敲定的问题——不需要对尚未听到的答案做任何猜测就能问的那些。每轮把整个可答集一次性抛出：逐个编号，并附上你的**推荐答案**；然后停下等用户回答，再进下一轮。

一轮长这样：

```text
❓ **Q1** - **<问题标题>**: <问题正文，可多段，可含多个选项>

➡️ <你的推荐答案>

---

❓ **Q2** - **<问题标题>**: <问题正文>

➡️ <你的推荐答案>
```

用户每轮的回答都会重塑这棵树：已敲定的决策把可答集向外推，解锁原本被卡住的问题。重新计算可答集，进入下一轮。答案依赖本轮其他未敲定问题的，属于**后续轮次**，不放进本轮。

**查事实是你自己的活，永远不是用户的活。**可答集中的问题需要环境里的事实（文件系统、工具等）时，派 sub-agent 去查；凡是自己能查到的，不要问用户。但也不要因此整体卡住：一次还在跑的探索只是一个未敲定的前置——只有它下游的问题等它回报，可答集的其余部分照常发问。**决策才是用户的**：逐个摆到用户面前，等待拍板。

可答集清空即会话结束：设计树每个分支都走过了，没有留下任何默会假设。在用户确认达成共识之前，**不要动手实施**。
