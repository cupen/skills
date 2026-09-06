---
name: git-finish
description: "Git worktree wrap-up: conventional commits, rebase onto latest main then merge --no-ff into main (keeps branch history), re-verify, push, summarize. Explicit invocation ONLY: /git-finish or ask by name; never auto-trigger on 收尾 / 收工 / wrap up alone."
---

# Git 工作目录收尾（git-finish）

目标：会话结束时把工作区整理成**已提交、已集成（rebase + `--no-ff` merge）、已验收、已推送**的状态，以简短总结收束。调用本 skill 即视为对提交与推送的显式授权（覆盖默认保守 git 策略），但仅限本次摸清的工作。

## 0. 摸清现场

```bash
git status --short                          # 改动与未跟踪文件
git branch --show-current                   # 当前分支
git log --oneline -5                        # 最近提交（提交风格）
git rev-parse --git-dir --git-common-dir    # 两者不同 = 在 worktree 里
```

- 看仓库的 AGENTS.md / CLAUDE.md / README / CI 配置，确认**提交信息规范**（conventional commits、语言）与**验证命令**（第 3 步门禁）。
- worktree 中 main 通常由主 worktree 持有，合入 main 须在检出 main 的 worktree 执行（`git worktree list` 确认）。

## 1. 提交已完成的工作

- 浏览 `git diff` 与未跟踪文件，确认改动归属。构建产物、依赖目录、秘密文件（.env、密钥、凭据）**不提交**；与本会话无关的陌生改动单独成提交、总结中标注，不混装。
- 按逻辑层拆分 conventional commits（语言随仓库风格），通常 1–4 个：后端、内核/服务、前端、文档各成一体。拆分便于 review 与回滚，但不为拆而拆。
- 提交信息**默认只有主题行**：`<type>: <一句话说清做了什么>`。内容实在太多才加正文：主题行后空一行，第三行起编号列表——

  ```text
  refactor: 统一配置加载，拆出 env 解析模块

  1. 配置统一走 config 模块，废弃直读 os.environ
  2. 修复启动时重复读取 .env
  ```

  列表只说重点，不陷细节；尽量 ≤3 条，绝不超过 5 条；有重要说明时次要问题省略。
- 没有改动 → 直接跳到第 2 步。

## 2. 集成（rebase 到最新 main，分支再 `--no-ff` 合入）

目标：把工作重放到最新 main 之上。工作在 main 上，rebase 完即集成完毕；在 feature 分支上，rebase 后以 `--no-ff` 合入 main——merge commit 把分支工作作为完整单元留在 main 历史，分出点与合入点一目了然，review 与回滚都以分支为单位。

**工作在 main 上**：

```bash
git fetch origin
git rebase origin/main
```

rebase 完 → 集成结束，直接进入第 3 步验收。

**工作在分支或 worktree**：

```bash
git fetch origin
git rebase origin/main   # 分支重放到最新 main 之上；无远端时用本地 main
```

rebase 后合入 main：检出 main（或到主 worktree），执行

```bash
git merge --no-ff <branch> -m "merge: <一句话概述该分支的工作>"
```

- merge 信息一句话说明集成了什么，跟随仓库风格；不便拟写时用 `--no-edit`。
- main 又前进了（本地落后 origin/main）→ 先快进本地 main，回分支重新 rebase 再合并，不在旧基线上合并。
- 仓库明确约定线性历史（CI 强制 fast-forward / squash）或用户点名时，才改用 `git merge --ff-only`。
- 解冲突警惕上游**语义漂移**：上游可能新增枚举变体、改签名、重构你的模块。标记机械合过 ≠ 语义正确——把改动重放到上游新结构上，补齐新增 case。
- rebase 改写提交哈希，推送过的分支会与远端分叉；本流程只推集成分支（第 4 步），不受影响。要推工作分支须用户明确同意 `--force-with-lease`。
- rebase 出问题 `git rebase --abort` 回起点重来，不硬撑。

## 3. 测试验收

集成后**必须重新验收**——rebase 前的绿不代表 rebase 后的绿，上游语义变化可能静默破坏行为。

- 跑第 0 步确定的门禁（Rust：`cargo test` + `cargo build`；Node：`pnpm test` + `pnpm build`；无门禁时至少构建通过）。
- 失败 → 修复补提交，回第 2 步看是否需再 rebase。
- 无法修复 → **停下**报告卡点，不推送；带红测试推送比不推送更糟。

## 4. 推送

```bash
git push
```

- 被拒（non-fast-forward）→ `git fetch && git rebase origin/main` 后重试一次；再失败停下报告。
- **不 force-push**，除非用户明说。
- 只推集成分支（通常 main），不顺手推无关分支。

## 5. 总结

简练、按重要性排列、结论先行，工作 3–5 条，如实记录边界：

```text
收尾完成，已推送 main（<commit 范围概述>）。
- <最重要的工作，一句话>
- <次重要的工作>
- <再其次>
- 验证：<门禁结果；什么没验到，为什么>
- 遗留：<已知问题 / 后续建议，没有则不写>
```

边界如实记：哪些只被测试覆盖、哪些要真实环境才能验证、哪些是当场拍的——下一会话或下一个人靠这段接手。
