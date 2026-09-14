---
name: spec-new
description: "新 spec change 立项（仅显式调用）：/spec-new 或点名调用，仅提到新需求 / 提案 / openspec 不自动触发。围绕主题用 grill-me 持续拷问直到完全理解需求，再执行 openspec-propose 流程落地 proposal/design/specs/tasks 全套规划工件；只规划不实现，实现交给 spec-go。"
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
---

# 新 spec change 立项（spec-new）

目标：把一个新需求从一句话想法带到可执行的 spec change——先顺着主题持续拷问直到需求完全理解，再走 openspec-propose 流程生成全部规划工件。只规划不实现：实现与验收是 spec-go 的活。

前提：项目有 `openspec/` 目录且 `openspec` CLI 可用（跑 `openspec list --json` 验证）。没有 → 报告用户先 `openspec init`，到此结束。

## 0. 定主题

入参带了主题或一句话描述 → 记下直接进第 1 步。没带 → 开放式问用户「想做什么变更？描述要构建或修复的东西」。此刻不建 change 目录、不定名——名字等拷问完从共识里提炼。

## 1. 拷问（grill-me）

加载 grill-me 技能（会话中可发现时），把对话连同主题交给它，由 grilling 引擎按设计树／轮次连环追问，并把本技能的完成标准带进去；不可发现则提示用户用 skills-install 的 grill-me 预设装整组（入口壳依赖 grilling 引擎，裸装是坏的），用户不想装就按简化规则内联执行：

- 把需求映射成设计树，按轮次抛出**当前可答集**（前置决策已全部敲定的问题），逐个编号并附推荐答案，停下等用户回答再进下一轮。
- 查事实是自己的活：代码库、`openspec/specs/` 既有规范、相关 change 自己读，不问用户；**决策才是用户的**，逐个摆上待拍板。
- 可答集清空、用户确认共识，拷问才结束。

理解完成的验收线：**不编造任何重要事实**就能填满四类工件——proposal 的 why/what、design 的关键决策、specs 增量的需求与场景、tasks 的步骤。够不着这条线就继续追问，不降标准收口。

本阶段只谈不写：不建目录、不写文件、不动代码。

拷问收束时在对话里产出**需求共识摘要**（不落盘）：已敲定决策（含被否掉的备选及否因）、范围边界、验收要点、留作合理假设的次要细节。

## 2. 落地工件（openspec-propose）

加载 openspec-propose 技能（会话中可发现时），把共识摘要作为完整输入交给它，并说明其自带的「澄清重大歧义」步骤已由拷问满足、剩余次要细节按该技能规则记为假设；不可发现则按 CLI 等价执行同一步骤：

```bash
openspec new change "<name>"                              # kebab-case 名，从共识提炼（如 add-user-auth）
openspec status --change "<name>" --json                  # 拿 applyRequires 与各工件 requires 依赖序
openspec instructions <artifact> --change "<name>" --json # 逐工件取 template / instruction / resolvedOutputPath
```

按依赖序逐个工件：按 `instruction` 与 `template` 写到 `resolvedOutputPath`（instruction 指定交给特定技能/命令生成的，照办），每写完一个重读盘上的依赖工件并重跑 status，直到 `applyRequires` 传递闭包全部 done。条件性工件（如 design）只在其 `instruction` 声明可跳过时跳过并告知用户。

共识摘要分发去向：why/what → proposal；关键决策与被否备选 → design；需求与场景 → specs 增量；实现步骤 → tasks。

planning boundary：只写 `openspec/` 下的工件，不碰项目代码——哪怕需求里说「顺手实现了」，也留给下一步。

## 3. 收口

```bash
openspec status --change "<name>"   # 确认工件齐全
openspec validate "<name>"          # 结构校验，红了按提示修工件
```

总结报告：change 名与路径、工件清单、从拷问带出的关键决策、记录在案的假设。收尾提示：工件可供评审，要实现走 `/spec-go`（或项目内的 openspec-apply-change）。
