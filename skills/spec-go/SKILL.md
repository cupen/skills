---
name: spec-go
description: "Spec change 串行执行编排（仅显式调用）：/spec-go 或点名调用，仅提到 openspec / spec change 不自动触发。用 openspec-explore 浏览 changes、分析合理性与依赖、定串行路线，报告确认后逐个派 subagent 实现＋验收＋补测试（含 e2e），全部整体测试后转 git-finish 收尾。"
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
---

# Spec Change 串行执行（spec-go）

目标：把 `openspec/changes/` 下的待办 spec change **串行**落地——浏览盘点 → 分析依赖定路线 → 报告确认 → 逐个 change「subagent 实现 + 主 agent 验收 + subagent review 补测试」→ 整体验收 → git-finish 收尾。调用本 skill 即视为对后续提交与推送的授权沿 git-finish 生效。

前提：项目有 `openspec/` 目录且 `openspec` CLI 可用（跑 `openspec list --json` 验证）；`git status` 干净——有脏改动先报告用户处理，不混装。

## 0. 浏览盘点（openspec-explore）

加载 openspec-explore 技能（会话中可发现时），按它的探索姿态完成本阶段；不可发现则直接用 CLI 等价完成。本阶段只读分析、不写代码——实现留给第 3 步的执行 subagent。

```bash
openspec list --json                      # 全部 change 与状态
openspec status --change "<name>" --json  # 工件路径与完成度
```

逐个 change 读 `proposal.md` / `design.md` / `tasks.md` / `specs/` 增量（status JSON 的 `artifactPaths` 给路径），记录：意图一句话、任务勾选比例（部分完成的**接着做**，不是重做）、触及的 capability、proposal 里显式引用的其他 change。

## 1. 合理性与依赖分析

- **合理性**：proposal 与 `openspec/specs/` 既有规范、与代码现状是否矛盾；tasks 是否覆盖 What Changes 的全部要点；两个 change 范围重叠或要求冲突的明确标出。
- **依赖**三类：① 显式引用（proposal/design 点名依赖某 change）；② 同一 capability 的 specs 增量有先后；③ 常识序（数据模型/存储 → 服务/API → UI/CLI）。出现环 → 报告用户裁决，不硬排。
- 没有待办 change（或全部完成归档）→ 如实报告，到此结束，不进后续步骤。

## 2. 规划路线并报告（确认门）

产出串行执行路线，报告用户并等确认后再动手（用户调用时已带「直接开始」类指示则跳过确认）。路线示例：

```text
执行路线（串行）：
1. add-config-layer   0/8   依赖：无       数据模型基础，其余 change 的前提
2. add-metrics-api    0/5   依赖：#1       投影新字段依赖 #1 的配置结构
3. webui-console      3/12  依赖：#1 #2    消费前两者的 API；已勾 3 项续做
风险：#2/#3 都改 web.rs 投影，串行天然避让；#3 假设的 X 能力无 change 定义，需拍板。
```

同时定下验收口径：每个 change 的门禁命令（从仓库 AGENTS.md / README / CI 推断；Rust 常为 `cargo test` + `cargo build`，Node 常为 `pnpm test` + `pnpm build`）。

## 3. 串行执行：一个 change 三步走，走完再下一个

严格串行：上一个 change 的实现、验收、review 补测试全部完成并过渡提交后，才启动下一个。前面 change 的落地可能让后面 change 的 proposal 细节过时——派发前把已知偏差写进 subagent prompt（「X 已在前一 change 落地，本 change 只需……」）。

### 3a. 派执行 subagent（一次一个）

prompt 必须自包含，模板：

```text
你在 <repo 绝对路径> 实现 openspec change「<name>」。
先读 openspec/changes/<name>/ 下的 proposal.md、design.md、tasks.md 与 specs/ 增量，
specs/ 增量是验收合同，逐条对照实现；按 tasks.md 顺序逐项做并勾选。
补充上下文：<已知偏差 / 前置 change 落地情况>。
门禁：<命令>，全绿才算完成。
不 git 提交、不动其他 change 的工件、不改 openspec/ 其他文件（勾选 tasks.md 除外）。
汇报格式：已完成任务编号｜未完成与原因｜门禁结果｜偏离设计的决策｜风险。
```

### 3b. 主 agent 验收

subagent 的汇报是输入，不是结论。亲自做三件事：① 核对 tasks.md 全勾；② 重跑门禁；③ 抽查 specs/ 增量中 1–2 条关键需求对照代码。不过关 → 把具体失败点写进 prompt 重派（同一 change 最多重试 2 轮）；仍不过 → **停止整个执行**，报告已完成 / 卡住 / 未开始清单与卡点，等用户决策——后面的 change 可能依赖它，不跳过硬走。

### 3c. 派 review subagent 补测试

验收通过后立刻补一道独立 review，模板：

```text
你在 <repo 绝对路径> review 刚实现完的 openspec change「<name>」（未提交改动，git diff 可见）。
对照 openspec/changes/<name>/specs/ 增量逐条需求核验实现，找覆盖缺口并补测试：
单元 / 集成 / e2e，用项目自带测试框架与 e2e 通道；需要真实浏览器 GUI 操作的用例
不要自己执行，单独列出交回主 agent。
只加测试与报告，不改实现代码；发现实现问题原样上报。
跑全部门禁。汇报：需求覆盖结论｜新增测试清单｜发现的问题｜门禁结果。
```

- review 报出实现问题 → 小问题主 agent 直接修，大问题回 3a 重派。
- 需要真浏览器 GUI 的 e2e 由主 agent 自己执行（浏览器自动化技能为 main agent 专属，subagent 不得加载）。
- 测试全绿后收口该 change：`openspec validate --change <name>` 通过 → `openspec archive <name> --yes`，再过渡提交一个 conventional commit（如 `feat(<name>): <一句话>`，取自 proposal）。过渡提交让每个 change 可独立回滚与 bisect，最终集成交给 git-finish。

## 4. 整体验收

全部 change 走完后统一再验一遍——串行过程中每个门禁都绿不代表组合绿，后面的 change 建立在前面之上，可能静默回归：

- 跑全量门禁：构建 + 全部测试 + e2e 套件。
- 失败 → 定位归属（哪个 change 引入），修复补提交后重跑；修不动 → 停下报告，不带红进 git-finish。

## 5. 收尾

调用 git-finish 技能完成集成（rebase + `--no-ff` 合入）、验收、推送与总结——工作已在过渡提交里，git-finish 负责集成与推送。最终总结按 change 逐个列出：做了什么、验收结论、新增测试、遗留风险。
