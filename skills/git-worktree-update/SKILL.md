---
name: git-worktree-update
description: "Explicit invocation ONLY: /git-worktree-update or ask by name; never auto-trigger on 更新 / 同步 main mentions. Rebase every non-main worktree branch onto latest main one by one, resolving conflicts in place; keep resolutions consistent across branches."
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
---

# Git Worktree 批量同步（git-worktree-update）

把仓库里除主 worktree 外每个 worktree 的分支 **rebase 到最新 main 之上**，就地解决冲突，让所有工作区站在同一条最新基线上。**仅显式调用激活**（`/git-worktree-update` 或点名 git-worktree-update），不因对话里出现 更新 / 同步 main 等字样自动触发。用户调用本 skill 即视为对 rebase 的显式授权——rebase 会改写分支提交哈希；但**不合入 main、不推送**，集成分支是 git-worktree-finish 的职责。

必须**串行**处理。各分支的 rebase 基点是同一个 main，先做后做不影响结果；串行是为了让后面分支解冲突时能参考前面分支的解法，保证同类冲突在所有分支上解法一致。并行处理会丢掉这层一致性。

## 0. 摸清现场

```bash
git remote -v                   # 没有远端 → 跳过 fetch 与快进，直接用本地 main
git fetch origin                # 有远端才执行
git worktree list --porcelain   # 全部 worktree；第一条是主 worktree
```

**基点准备**：统一以本地 `main` 为基点。有远端且 origin/main 领先本地 main → 先在检出 main 的 worktree 快进上来（`git -C <主worktree路径> merge --ff-only origin/main`）；快进不动（主 worktree 有未提交改动）→ 沿用本地 main，并在计划里标注「main 未更新到远端最新」。本地没有 main（主分支检出名不同）→ 以实际主分支为准，先向用户确认。

对每个非主 worktree 分类：

```bash
git -C <路径> status --short                  # 有输出 = 有未提交改动
git -C <路径> branch --show-current           # 空 = detached HEAD
git -C <路径> rev-list --count <分支>..main    # behind：main 有、该分支没有的提交数
git -C <路径> rev-list --count main..<分支>    # ahead：该分支独有的提交数
```

| behind | ahead | 分类 |
|---|---|---|
| >0 | >0 | 进入同步清单：rebase 会重放 ahead 个提交 |
| >0 | =0 | 已并入 main（无独有提交），无需同步——rebase 是空操作 |
| =0 | 任意 | 已是最新，跳过 |

- 有未提交改动 → 默认跳过并在计划里标注；用户点名要同步才处理：先 `git stash push -u`，rebase 完 `git stash pop`，pop 出冲突如实报告、不硬解。
- detached HEAD → 跳过并标注。

## 1. 预览计划（必做）

动手前展示计划，等用户确认。默认按 `git worktree list` 的输出顺序排，用户可剔除某项、调整顺序；未获确认不执行：

```text
基点：main @ a1b2c3d（已快进到 origin/main 最新）
按顺序同步：
  1. ../agent-kit-login   feat/login   落后 5 个提交，将重放 2 个提交，干净
  2. ../agent-kit-pay     feat/pay     落后 5 个提交，将重放 1 个提交，预计有冲突（两边都改了 config.ts）
  3. ../agent-kit-docs    feat/docs    已并入 main，跳过
  4. ../agent-kit-wip     feat/wip     有未提交改动，跳过
```

- 无远端时基点行写「无远端，直接用本地 main」。
- 「已是最新」的也列出来标注，让用户看到全貌；一条 worktree 有多个跳过原因（如已并入 main 且有未提交改动），合并在一行都标上。
- 预测是否冲突：`git merge-tree --write-tree main <分支>`（git 2.38+，退出码非 0 即有冲突）。它是 tip 对 tip 的合并预演，rebase 是逐提交重放——预测干净不保证逐个提交都不冲突，只作参考。
- 全部是跳过项时仍展示计划并等确认，计划里写明「确认后不会有任何变动」。
- 仓库只有一个 worktree → 没什么可同步，到此为止。

## 2. 逐个 rebase

按确认的顺序，在每个 worktree 里执行：

```bash
git -C <路径> rebase main
```

- 无冲突 → 记一行结果：「已同步（快进）」或「重放 N 个提交」。
- 出冲突 → 就地解决（处理细节见 resolving-merge-conflicts 技能）。rebase 是逐提交重放，同一处文件可能多次冲突，逐个解完 `git add` 再 `git rebase --continue`。
  - **解冲突的默认方向：保留分支的值**——rebase 的本质是重放分支工作，取 main 的值等于让这个提交变空、被丢弃。只有上游改动明显是刻意修正（配置基线、版本号、安全修复）时才优先上游；拿不准就停下来问用户，不擅自定夺。
  - **语义漂移**：main 可能新增枚举变体、改签名、重构了该分支依赖的模块。冲突标记机械合过 ≠ 语义正确——把分支改动重放到 main 的新结构上，补齐新增 case。
  - **跨分支一致**：前面分支解过的同类冲突，沿用同一解法；新类型的冲突解完后记下解法，后面分支遇到直接套用。
  - 卡住解不掉 → `git rebase --abort` 回到 rebase 前原样，标「同步失败（原因）」，跳到下一个，不让一个卡点堵死整批；失败的原地保留，最后统一报告。
- rebase 改写提交哈希，推送过的分支会与远端分叉。本 skill **不推送**；用户之后要推工作分支，须其明确同意 `--force-with-lease`。

## 3. 总结

```text
批量同步完成：<共 N 个 worktree，同步 M 个，失败 K 个>，基线 main @ <短哈希>。
- <worktree 名>：<分支> 重放 N 个提交（解了 X 处冲突：<一句话解法>）
- <worktree 名>：已是最新 / 已并入 main，跳过
- <worktree 名>：同步失败（原因），已回滚原样
- 一致性：<同类冲突各分支解法是否一致；哪些 worktree 因未提交改动没动>
- 后续：分支哈希已改写，推工作分支需 --force-with-lease；集成进 main 用 /git-worktree-finish
```

N / M / K 只统计非主 worktree。不主动跑测试门禁：rebase 后各分支是否还绿，留给各自的收尾流程（git-finish）验收；总结里如实标注「未重新验收」。
