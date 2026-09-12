---
name: domain-modeling
description: "Build and sharpen a project's domain model: challenge terms, stress-test scenarios, cross-check with code, maintain the CONTEXT.md glossary and ADRs. Use when discussing terminology, writing/editing CONTEXT.md, or recording an ADR."
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
  source: "https://github.com/mattpocock/skills (MIT)"
---

# 领域建模（domain-modeling）

设计的同时**主动**构建并打磨项目的领域模型：挑战术语、发明边界场景、在概念结晶的一刻就把词汇表与决策写下来。（仅为查词汇而**读** `CONTEXT.md` 不算本技能——那是一行习惯，任何技能都能做。本技能用于**改动**模型的时刻，而非消费它。）

## 文件结构

大多数仓库只有一个 context：

```text
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

若根目录存在 `CONTEXT-MAP.md`，说明仓库有多个 context。map 指明各 context 的位置：

```text
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 全系统级决策
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← 该 context 自己的决策
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

文件**按需惰性创建**：有东西可写才建。不存在 `CONTEXT.md` 时，第一个术语敲定即创建；不存在 `docs/adr/` 时，第一份 ADR 需要时再建。

## 会话进行中

### 对照词汇表挑战术语

用户用词与 `CONTEXT.md` 既有语言冲突时，当场指出：「你的词汇表把『取消』定义为 X，但你现在说的像是 Y。到底是哪个？」

### 打磨模糊语言

用户用词含糊或一词多义时，提出精确的规范术语：「你说的『账户』，是 Customer 还是 User？这是两个东西。」

### 用具体场景压测

讨论领域关系时，用具体场景做压力测试。主动发明能探到边界情况、逼用户把概念边界说清楚的场景。

### 与代码交叉核对

用户陈述某处如何运作时，核对代码是否同意。发现矛盾就摆出来：「代码是整单取消，你刚说的却是支持部分取消。哪个是对的？」

### 就地更新 CONTEXT.md

术语敲定的那一刻就更新 `CONTEXT.md`，不要攒批：随发生随记录。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。

`CONTEXT.md` 里**绝不出现实现细节**。它不是 spec、不是草稿本、不堆放实现决策。它是词汇表，仅此而已。

### 克制地提供 ADR

三条全真才提议写 ADR：

1. **难以逆转**：事后改主意的代价实打实
2. **缺了上下文会让人费解**：未来的读者会问「为什么这么做？」
3. **真实权衡的结果**：确实存在别的选项，你因具体理由选了其一

缺任何一条就不写。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。
