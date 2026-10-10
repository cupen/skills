---
name: git-commit-style
description: "Git 提交信息规范（Conventional Commits）：scope 只写最简模块名（如 auth 不写 auth-config、ui 不写 ui-server-deploy，openspec 写 spec）；标题一句话不超过 20 字，正文空一行后只笼统概述 3~5 件要事。凡是要 git commit、拟写提交信息、整理或 review 提交历史时使用；用户提到提交规范 / commit message / conventional commits 也触发。"
metadata:
  author: "cupen <xcupen@gmail.com>"
  version: "0.2.1"
---

# Git 提交信息规范（Conventional Commits）

遵循 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：

```text
<type>(<scope>): <subject>
```

type 用 feat / fix / chore / docs / refactor / test / perf / build / ci / revert；分支合入 main 的 merge commit 用 `merge:`（随仓库既有风格）。

## 规则一：scope 只写最简模块名

scope 表示改动所属的功能模块，**取模块主干名，尽量简写**：

- 不带具体信息、不要有修饰后缀——写 `auth`，不写 `auth-config`
- 不写部署形态——写 `ui`，不写 `ui-server-deploy`
- 规格类工具（openspec）相关一律写 `spec`，不写 `openspec`——它的主体就是 spec

原因：scope 让人一眼看出改的是哪一块就够了，细节属于 subject 和正文；塞进 scope 只会让 `git log --oneline` 又长又难读。各仓库的具体模块名对照可补充在该仓库的 AGENTS.md 里，本 skill 只定通用规则。

## 规则二：标题一句话，正文只概述

- 标题 `<subject>` 只用一句话说清做了什么，**不超过 20 字**，越短越好，不堆细节。
- 通常只有标题、不写正文；内容实在多才加正文：标题后**空一行**，第三行起笼统概述，只列重要的 **3～5 件事**，不写实现细节——细节在 diff 里，提交日志是给人扫一眼的索引，不是变更说明书。

```text
feat(auth): 支持凭证自动轮换

1. 新增轮换调度与手动触发入口
2. 过期前自动预轮换
```

## 示例：scope 对照

```text
feat(auth): 新增凭证轮换接口              # ✅
feat(auth-config): 新增凭证轮换接口        # ❌ 后缀多余
feat(ui): 修复登录态丢失                 # ✅
feat(ui-server-deploy): 修复登录态丢失     # ❌ 写成了部署形态
chore(spec): 计划 add-xxx 变更            # ✅（openspec → spec）
```

拿不准时选更短、更上层的那个名字；确实要区分的细节放进正文说明，不动 scope。

语言等其他细节跟随仓库既有提交风格；完整收尾提交流程见 git-finish skill。
