---
name: git-update
description: "Explicit invocation ONLY: /git-update or ask by name; never auto-trigger on 更新 / 同步 / git pull mentions. Run git pull --rebase=merges --autostash on the current branch, resolve conflicts in place; report pulls, resolutions, autostash. Never pushes."
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.1.0"
---

# Git 更新当前分支（git-update）

把当前分支更新到它的上游最新：`git pull --rebase=merges --autostash`——rebase 式拉取并保留本地合并提交结构（`merges` = `--rebase-merges`，git 没有 `mertes` 这个值），未提交改动由 autostash 自动收放。出冲突就地解决。**仅显式调用激活**；用户调用即视为对 rebase（改写提交哈希）的显式授权，但**不推送**。只管当前分支对自己 upstream 的更新；批量把各 worktree 对齐 main 用 git-worktree-update，收尾集成推送用 git-finish。

## 0. 摸清现场

```bash
git status              # 未提交改动快照（收尾核对 autostash 用）；"You are currently rebasing" = 上次 rebase 未完
git branch --show-current   # 空 = detached HEAD，直接停
git remote -v               # 无远端 → 无可拉取，停
git rev-parse --abbrev-ref --symbolic-full-name @{u}   # 无上游 → 停
git log --oneline -3
```

- detached HEAD / 无远端 / 分支没设 upstream → 停下报告原因；要设 upstream（`git branch --set-upstream-to=...`）由用户决定，不擅自设。
- 有未提交改动 → 正是 autostash 的用途，不用手动 stash；但**未跟踪文件不受 autostash 保护**：上游新增同名路径文件时 pull 会报 `untracked working tree files would be overwritten` 并干净中止——列出文件停给用户，绝不删除或覆盖本地未跟踪文件。
- 上一次 rebase 还没结束 → 停，先让用户决定 continue / abort，不叠加操作。
- 记下当前 HEAD 短哈希与未提交改动清单：收尾核对 autostash 是否原样恢复、报告拉入量。

## 1. 执行更新

```bash
git pull --rebase=merges --autostash
```

- 干净完成 → 记下拉入的提交与 `Applied autostash.`，`git diff --stat <第0步旧哈希>..HEAD` 概览拉入改了什么，跳到第 3 步。
- `dropping <hash> <subject> -- patch contents already upstream` → 正常行为：该本地提交内容已在上游（如被 cherry-pick 过）被自动丢弃，不是错误；总结里如实记一笔。
- 冲突（输出 `CONFLICT`，rebase 停住）→ 第 2 步。
- 其他报错（autostash 创建失败、网络、认证）→ 原样报告，不硬绕。

## 2. 解冲突

**先认方向再动手**——rebase 里的 ours / theirs 与 merge 相反，极易搞反：

- `<<<<<<< HEAD`（ours）= 已重放好的新基线，含上游改动；`>>>>>>> <hash> (<提交主题>)`（theirs）= **正在重放的本地提交**，这是要保住的意图。
- 拿不准就 `git log -1 --format='%h %s'` 看基线顶，结合标记行尾的提交主题确认哪边是谁。

逐个解决：

```bash
git diff --name-only --diff-filter=U    # 冲突文件清单
```

- **默认保住被重放提交的意图**（theirs 侧）；只有上游改动明显是刻意修正（配置基线、版本号、安全修复）才取上游。两边业务逻辑各改各的、意图拿不准 → 停下问用户，摆出两边改动与建议，不擅自定夺。
- **机械合过 ≠ 语义正确**：上游可能改了签名、加了枚举 case、重构了模块——把本地改动重放到新结构上，补齐新增分支。
- **lockfile / 生成物不手合**（pnpm-lock.yaml、Cargo.lock、go.sum、*.pb.go…）：先解到任一边，再用工具重新生成（`pnpm install` / `cargo build` / `go mod tidy`）。
- 逐个 `git add <文件>`，然后：

```bash
git -c core.editor=true rebase --continue
```

  **必须带 `-c core.editor=true`**：continue 会请求确认提交信息，交互式编辑器在无头会话里直接卡死。
- `--rebase=merges` 连本地合并提交一起重放，同一文件可能冲突多轮，逐轮解完继续，同类冲突沿用同一解法。
- **冲突期间脏改动不在工作区、也不在 `git stash list`**：它们被收进 autostash（pull 输出里的 `Created autostash: <hash>`），continue 成功或 abort 后自动回来。现场看不到 ≠ 丢了。
- 只有被重放提交的内容已在上游（如被 cherry-pick）才考虑 `git rebase --skip`，拿不准先问。
- 卡死解不掉 / 风险高 → `git rebase --abort`：整体回到 pull 前原样，autostash 自动恢复（输出打 `Applied autostash.`），如实报告卡点收场，不硬撑。

## 3. 收尾核对

```bash
git status --short        # 与第 0 步快照对比
git log --oneline -5      # 新基线 + 重放的本地提交
```

- autostash 恢复正常 → 工作区与快照一致（该脏的还脏），`git stash list` 无残留。
- `git stash list` 多出条目、或该回来的改动没回来 → autostash 恢复异常，如实报告并让用户手动处理，不擅自 `stash pop` 硬解。
- abort 收场的同样核对：分支指向 pull 前哈希、改动原样在。

## 4. 总结

```text
git-update 完成：<分支> 已更新到 <上游>，<旧哈希> → <新哈希>，拉入 N 个提交。
- 拉入内容：<一句话概述>
- 本地提交：重放了 M 个（合并结构已保留）/ 无本地提交，纯快进 / 被自动 drop K 个（已在上游）
- 冲突：<解了 X 处：<一句话解法> / 无冲突 / abort 回滚（原因）>
- autostash：<N 个文件的未提交改动已原样恢复 / 无未提交改动 / 恢复异常：<现象>>
- 后续：哈希已改写，推送需 --force-with-lease；本 skill 不推送。
```
