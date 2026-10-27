---
name: spec-go
description: "Spec change 执行编排（仅显式调用）：/spec-go 或点名调用。主 agent 通读工件、分析依赖、定路线与档位（1–3），确认后派 subagent 实现；主 agent 验收并判集成面，有才派 review 补集成/e2e。小 change 可合并派，长 change 拆接力；门禁限 scope、日志落盘；转 git-finish 收尾，不自动归档。"
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.10.0"
---

# Spec Change 执行编排（spec-go）

按确认路线落地 `openspec/changes/` 中的待办 change。主 agent 负责理解规格、规划、分流与裁决；subagent 负责实现、集成补测与返修。调用本 skill 即授权沿 git-finish 提交与推送，但不自动归档。

上下文约定：规格预摘跨阶段复用；subagent 按需回读原文；长输出重定向落盘，只回看失败段；主 agent 不收全量日志、不逐任务追问、不亲自返修代码。

前提：项目有 `openspec/`，且 `openspec list --json` 可运行。已有脏改动不阻塞，但须在确认门报告。

## 0. 通读与预摘

可加载 openspec-explore 辅助探索；不可用时直接用 CLI：

```bash
openspec list --json
openspec status --change "<name>" --json
```

先从 `tasks.md` 统计进度，排除已完成、待归档的 change。**主 agent 随后完整通读每个待执行 change 的 proposal/design/specs；这是规划输入，不下沉给 subagent。**工件只通读这一次，代码现状与既有规范只在合理性分析需要时定向查看。

逐 change 产出预摘（≤25 行），供实现、验收、review 和接力复用；合并派发时逐 change 各一段，多次派发不要重新生成：

```text
意图：<一句话>｜capability：<集合>
需求清单：<Requirement 标题 + 一句概括；过长则列标题与原文位置>
依赖与冲突：<相关 change / 既有规范 / 代码现状>
关键路径：<包/文件>｜建议 L1：<命令与 scope>
```

记录 capability 交集与显式依赖；依赖分析需要场景对照时，直接利用已通读的 specs，不再重复精读。派发时传预摘及原文路径；proposal/design 只有预摘不足时才定向回读，specs 按当前任务逐条对照。

## 1. 合理性与依赖

- 检查 proposal 与既有规范、代码现状是否矛盾，tasks 是否覆盖 What Changes。
- 依赖分三类：工件显式引用、同一 capability 的先后关系、常识序（模型/存储 → 服务/API → UI/CLI）。有环则请用户裁决。
- 已完成未归档的 change 只进待归档清单；没有待办 change 时报告并结束。

## 2. 定路线与确认门

实现前先交付纯文本路线表：逐 change 列进度、依赖、强耦合理由和合并/拆分安排，并附 capability 非空交集、脏改动、风险与门禁。门禁从仓库 AGENTS/README/CI 推断。用户已说“直接开始”可跳过确认，但仍须先出表。

门禁分两层：

- **L1**：只覆盖实际改动涉及的 crate/package，含构建与单元测试；3a 执行，3b 默认只核对覆盖。推不出可靠 scope 时不要硬收窄，能确定的测试先跑，其余交最终 L2。
- **L2**：仓库默认的全量构建、测试与 e2e，只在第 5 步的最终集成代码上跑。同一代码状态不重复跑；修复或 rebase 改变代码后必须重跑。

3c 只跑新补集成/e2e 与受影响套件。3a 必须报告实际命令、覆盖范围及日志路径；3b 发现覆盖不足才扩 scope 复跑。

并行度 M 是路线上两两无依赖且 capability 无交集的最大在飞数，封顶 3。档位：**1 串行（默认）｜2｜3**；推荐 M≥3 用 2，M=2 用 1，否则明说并行无收益。只有用户明确选择才并行。

## 3. 执行

一个执行 subagent 负责一个 change 的全部未完成 task，中途只勾选 `tasks.md`，不逐项回报。两个粒度例外：

- 相邻依赖链上、每个 ≤3 task 且 capability 相交的小 change，可合并派发；验收与过渡提交仍逐 change 进行。
- 超过约 12 task 或改动面大的 change，按自然边界拆成 2–3 个串行接力；接力间只核对进度，不验收。上下文仍不足时，执行 agent 先把进度和下一步落进 `tasks.md` 临时备注，再压缩或请求接力。

串行时，上一 change 收口并过渡提交后才派下一个。派发后续 change 时，只追加前置落地造成的已知偏差，不重做预摘。

### 3.0 并行隔离（仅档位 ≥2）

- 在飞 change 必须两两无依赖、capability 无交集，各自使用独立 worktree 与 `spec-go/<change>` 分支。
- 3a/3b/3c 均在对应 worktree 完成；过渡提交后由主 agent 按拓扑序 cherry-pick 回主线。同批合入完成后按 scope 并集跑一次 L1，再放行候补。
- 冲突或门禁失败时，只重派受影响任务，不整包重做。某 change 硬停时只停它及其依赖，其余继续。

### 3a. 实现

派发 prompt 自包含，复用以下模板：

```text
在 <repo/worktree 绝对路径> 实现 openspec change「<name>」。
预摘：<既有预摘；合并派发逐 change 各一段>
补充偏差：<前置落地造成的影响；没有则省略>
先读 tasks.md 与预摘指向的 specs；proposal/design 仅按需定向回读。
完成全部未完成项并勾选，只写普通单测，不写集成/e2e，不中途汇报。
L1：<命令与 scope>；核对覆盖实际改动，日志写入 <日志路径>，只回看失败段。
不改其他 change，不提交。
完成后 ≤10 行回报：状态｜L1 命令与 scope｜集成面及依据｜偏差/风险｜日志路径。改动文件由主 agent 用 git 查询，不在回报中重复列。
```

接力或重派时追加已勾项有效、续做起始项及临时备注位置。执行 agent 遇到错误应自行处理；只有规格矛盾或缺外部信息才提前返回。

### 3b. 主 agent 验收

整个 change（或合并链）完成后一次验收：

1. 只搜索 `tasks.md` 中未勾的 checkbox（含缩进项）；无结果即全勾，有结果再读对应任务上下文，不读全文。
2. 用 `git diff --name-only` 获取改动文件清单，比对 L1 命令与 scope；不看全量 diff，仅在覆盖不足或代码变化时复跑，并只回看失败段。
3. 判集成面：API/CLI/UI/公共导出，存储/迁移/配置格式，specs 跨边界场景，或 tasks 含集成/e2e 项，任一命中即“有”。判“有”则由 3c 逐条核 specs；判“无”则主 agent 只抽查 1–2 条关键需求对应的实现片段，不读整份文件、不做全量 diff review。

未通过时，把具体失败点交给原执行 agent 返修（宿主不支持恢复时才新派）；恢复原 agent 时只传失败点，不重复预摘，新派时才补齐必要上下文。修后由主 agent 或 3c 复验；主 agent 不亲自改代码。最多两轮，规格问题直接请用户裁决。仍失败则硬停，报告：在飞集合｜任务进度｜已合入 change｜卡点｜用户决策点。

### 3c. 独立 review 与集成补测

仅 3b 判“有集成面”时派发；判“无”直接收口，不在第 4 步重复反查。

```text
在 <repo/worktree 绝对路径> review change「<name>」的未提交改动。
预摘：<既有预摘>。按需求清单核 specs，需要原文时定向回读；不通读 proposal/design。
先看 git diff --stat，再按规格触及文件看定向 diff。
只补集成/e2e 测试，不改实现；实现问题附最小修复建议交回主 agent。
运行新补测试与受影响套件，日志落盘，只回看失败段。
通过时 ≤5 行回报：覆盖结论｜门禁结果｜日志路径｜GUI 用例数。
有问题才附失败项、最小证据与新增测试清单；覆盖缺口才逐条列，通过项不展开。
```

实现问题交原执行 agent 返修，再由 review 复验。需真实浏览器 GUI 的用例只登记，留到第 4 步由主 agent 执行。

收口时清除 `tasks.md` 临时备注，运行 `openspec validate --change <name>`，逐 change 做 conventional 过渡提交；不 archive。

## 4. 收拢欠账

- 汇总各 change 的验收结论、测试缺口与 GUI 用例，由主 agent 集中完成浏览器验证；只保留最终结论，失败时才读关键错误与必要截图/DOM 片段，不保留完整页面状态。
- 不重复 3b 的集成面判断，不重读已验收 specs，不重跑已覆盖门禁。
- 遗留失败交原执行 agent 修复、对应验收者复验；修不动则停下报告，不带红进入收尾。

## 5. 集成与最终门禁

调用 git-finish，交接已确认的提交归属、验证命令与遗留项，避免重复摸排。将其集成后的第 3 步验收指定为 L2，直接复用该结果，不再另跑全量门禁；通过后推送。L2 后若又修复或改变基线，必须重新验收。

归档留给用户验收后决定。最终总结列验证结果、遗留项和待归档 change；多个 change 可合并为一条 `openspec archive <a> <b> --yes` 命令。
