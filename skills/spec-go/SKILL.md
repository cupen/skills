---
name: spec-go
description: "Spec change 执行编排（仅显式调用）：/spec-go 或点名调用，仅提到 openspec / spec change 不自动触发。用 openspec-explore 浏览 changes、分析合理性与依赖、画执行拓扑图定路线与并行档位（1–3），报告确认后按档位派 subagent 实现＋验收＋补测试（含 e2e），全部整体测试后转 git-finish 收尾；change 不自动归档，留待用户验收后决定。"
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.5.0"
---

# Spec Change 执行编排（spec-go）

目标：把 `openspec/changes/` 下的待办 spec change 按确认档位落地（1 = 串行 ～ 3 = 最多 3 个在飞）——浏览盘点 → 分析依赖 → 画执行拓扑图定路线 → 报告确认（含档位拍板）→ 逐个 change「subagent 实现 + 主 agent 验收 + subagent review 补测试」→ 整体验收 → git-finish 收尾。调用本 skill 即视为对后续提交与推送的授权沿 git-finish 生效。

前提：项目有 `openspec/` 目录且 `openspec` CLI 可用（跑 `openspec list --json` 验证）。`git status` 不作硬前提——spec change 的已提交/未提交状态都不阻塞流程；主线若有脏改动，并入确认门报告（见第 2 步），由用户决定先行处理或继续，不拒。

## 0. 浏览盘点（openspec-explore）

加载 openspec-explore 技能（会话中可发现时），按它的探索姿态完成本阶段；不可发现则直接用 CLI 等价完成。本阶段只读分析、不写代码——实现留给第 3 步的执行 subagent。

```bash
openspec list --json                      # 全部 change 与状态
openspec status --change "<name>" --json  # 工件路径与完成度
```

逐个 change 读 `proposal.md`（含 why/what/显式引用，是路由主输入），从 `tasks.md` 只数勾选比例（部分完成的**接着做**，不是重做）。`design.md` 与 `specs/` 增量**先不读全文**——改用零成本信号筛：

```bash
grep -l "<其他 change 名>" openspec/changes/*/design.md   # 显式引用（含 design 里点名）
ls -d openspec/changes/*/specs/*/                         # 每个 change 触及的 capability
```

记录：意图一句话、任务勾选比例、显式依赖列表、capability 集合。capability 交集非空的两两组合，定向精读交集子集的 `specs/` 增量做场景级冲突对照；无交集的直接跳过全文，留给第 3 步 subagent 按需加载。design 全文也留给 3a，本阶段只取 grep 命中的引用行。

## 1. 合理性与依赖分析

- **合理性**：proposal 与 `openspec/specs/` 既有规范、与代码现状是否矛盾；tasks 是否覆盖 What Changes 的全部要点；两个 change 范围重叠或要求冲突的明确标出。
- **依赖**三类：① 显式引用（proposal/design 点名依赖某 change）；② 同一 capability 的 specs 增量有先后；③ 常识序（数据模型/存储 → 服务/API → UI/CLI）。出现环 → 报告用户裁决，不硬排。
- **已完成未归档**：tasks 全勾但未 archive 的 change 视为已完成，不进执行路线，列入「待归档」清单——归档决策留给用户验收后（见第 5 步）。
- 没有待办 change（全部完成或仅剩待归档）→ 如实报告（附待归档清单），到此结束，不进后续步骤。

## 2. 定路线并报告（确认门）

报告的第一产出物是**执行路线表**：基于第 0/1 步的分析结果，在写任何实现代码之前先交付给用户，确认门围绕这份表进行（用户调用时已带「直接开始」类指示则跳过确认，但表仍要先出）。纯文本呈现，不画图：

```text
执行路线（档位 <N>，<串行/并行>）：
1. add-config-layer   0/8   依赖：无                 数据模型基础，其余 change 的前提
2. add-metrics-api    0/5   依赖：#1 [强耦合]      投影新字段依赖 #1 的配置结构
3. webui-console      ◐ 3/12 依赖：#1 #2 [强耦合]  消费前两者的 API；已勾 3 项续做
主线脏改动：3 个未提交文件（含 src/web.rs），不影响 spec change 本身
风险：#2/#3 都改 web.rs 投影，串行天然避让；#3 假设的 X 能力无 change 定义，需拍板。
```

路线表即确认门主体——档位、强耦合边、脏改动、风险一目了然。主线若有脏改动（`git status` 不净）也写在这，由用户决定先处理还是继续，不影响 spec-go 开发流程。

同时附上 capability 交集表（哪怕为空）——粗筛结论必须显性化，否则「延迟读取」退化成「跳过分析」。定下验收口径：每个 change 的门禁命令（从仓库 AGENTS.md / README / CI 推断；Rust 常为 `cargo test` + `cargo build`，Node 常为 `pnpm test` + `pnpm build`）。

拓扑定稿后报告**并行度 M**：两两无依赖且 capability 无交集的最大同时在飞 change 数（从路线表上数，封顶 3）。执行档位随确认门让用户三选一：**1 = 串行（默认，最稳妥）｜2｜3 = 最多 N 个在飞**——串行更简单可追踪，并行只在用户明确选择、风险已量化时启用，不推荐主动并行。推荐跟 M 走但压一档：M ≥ 3 推 2，M = 2 推 1，M ≤ 1 明说「并行无收益」推 1；用户带「直接开始」跳过确认时按推荐档位执行。

## 3. 执行：一个 change 三步走

按确认的档位执行。**串行（档位 1）**：上一个 change 的实现、验收、review 补测试全部完成并过渡提交后，才启动下一个。**并行（档位 2/3）**：最多 N 个 change 同时在飞，隔离与合入规则见 3.0。共同规则：前面 change 的落地可能让后面 change 的 proposal 细节过时——派发前把已知偏差写进 subagent prompt（「X 已在前一 change 落地，本 change 只需……」）。

### 3.0 并行隔离与合入（档位 ≥ 2 生效）

- 在飞集合两两**无依赖且 capability 无交集**；凑不满 N 个就空窗等合入，不硬凑。
- 每个在飞 change 独立 worktree + 分支（`git worktree add ../<repo>-<change> -b spec-go/<change>`，基于当前主线创建）；3a/3b/3c 全在 worktree 内做，prompt 的「repo 绝对路径」填 worktree 路径，门禁也在 worktree 跑。
- 3c 全绿 → 过渡提交在分支上 → 主 agent 按拓扑序**逐个** cherry-pick 回主线，每合入一个在主线重跑门禁。不 archive，归档统一推迟（见第 5 步）；通过后从就绪队列放行下一个候补，保持在飞数 ≤ N。
- 合入冲突或合入后门禁红 → 该 change 基于最新主线重建 worktree 回 3a 重做；其余在飞 change 不受影响。
- 某 change 走到硬停（3b 仍不过）→ 只停它自己、窗口空置等用户裁决，期间不补新 change；依赖它的 change 等裁决结果再定去留。

### 主 agent 硬停报告格式（串行/并行通用）

硬停时报告五段：**在飞集合｜各 change 进度（已完成任务数/任务总数）｜已合入主线的 change｜卡住项 + 卡点原因｜用户决策点**。并行档位此报告在主线汇报，串行档位此报告在单个 change 走出 3b 硬停时生成。

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

subagent 的汇报是输入，不是结论。亲自做三件事：① 核对 tasks.md 全勾；② 重跑门禁；③ 抽查 specs/ 增量中 1–2 条关键需求对照代码。不过关 → 先分类：prompt 可修的（上下文缺失、理解偏差）把具体失败点写进 prompt 重派（同一 change 最多重试 2 轮）；需要设计/需求裁决的（specs 自相矛盾、缺外部信息）不耗重试直接报告用户。重试后仍不过 → **硬停该 change**（串行档位即停止整个执行，并行档位按 3.0 只停它自己），报告五段式：**在飞集合｜各 change 进度（已完成任务数/任务总数）｜已合入主线的 change｜卡住项 + 卡点原因｜用户决策点**，等用户决策——后面的 change 可能依赖它，不跳过硬走。

### 3c. 派 review subagent 补测试

验收通过后立刻补一道独立 review，模板：

```text
你在 <repo 绝对路径> review 刚实现完的 openspec change「<name>」（未提交改动，git diff 可见）。
对照 openspec/changes/<name>/specs/ 增量逐条需求核验实现，找覆盖缺口并补测试：
单元 / 集成 / e2e，用项目自带测试框架与 e2e 通道；需要真实浏览器 GUI 操作的用例
不要自己执行，单独列出交回主 agent。
只加测试与报告，不改实现代码；发现实现问题原样上报，并附最小修复建议。
跑全部门禁。汇报：需求覆盖结论｜新增测试清单｜发现的问题｜门禁结果。
```

- review 报出实现问题 → 参考其附带的修复建议：小问题主 agent 直接修，大问题回 3a 重派。
- 需要真浏览器 GUI 的 e2e 由主 agent 自己执行（浏览器自动化技能为 main agent 专属，subagent 不得加载）。
- 测试全绿后收口该 change：`openspec validate --change <name>` 通过（只读校验），再过渡提交一个 conventional commit（如 `feat(<name>): <一句话>`，取自 proposal）。过渡提交让每个 change 可独立回滚与 bisect，最终集成交给 git-finish。**不做 `openspec archive`**——归档统一推迟到合回 main、用户亲自验收之后（见第 5 步）。

## 4. 整体验收

全部 change 走完后统一再验一遍——串行过程中每个门禁都绿不代表组合绿，后面的 change 建立在前面之上，可能静默回归：

- 跑全量门禁：构建 + 全部测试 + e2e 套件。
- 失败 → 定位归属（哪个 change 引入），修复补提交后重跑；修不动 → 停下报告，不带红进 git-finish。

## 5. 收尾

调用 git-finish 技能完成集成（rebase + `--no-ff` 合入）、验收、推送与总结——工作已在过渡提交里，git-finish 负责集成与推送。**归档推迟给用户**：合回 main 后 change 留在 `openspec/changes/`，由用户亲自测试验收后再决定——验收期间可能产生 update change。`openspec archive <name> --yes` 只在用户明确指示后执行。最终总结附**待归档清单**（change 名 + 各条 `openspec archive <name> --yes` 命令），供用户验收后自己执行或指令 agent 批量执行。
