# agent-kit

Agent 随身工具箱：跨项目可复用的技能（skills）与一键安装脚本（python）。

技能格式遵循 [Agent Skills Specification](https://agentskills.io/specification)：
每个技能是一个目录，必含 `SKILL.md`（YAML frontmatter + Markdown 正文），
frontmatter 必填 `name` 与 `description`。

## 布局

```text
agent-kit/
├── skills/       # 公开技能：每个子目录一个 <name>/SKILL.md
└── scripts/      # 一键安装/配置脚本（python）
```

## 技能

- [git-finish](skills/git-finish/SKILL.md) — worktree 收尾：conventional commits、合回 main、重新验收、推送、总结。
- [git-worktree](skills/git-worktree/SKILL.md) — 开工区（仅显式调用）：入参功能名与分支名，在旁边建 `../<仓库名>-<功能名>` worktree；分支已存在则复用、不存在则 fork，创建前交互预览。

## 安装技能

### 方式一：`npx skills` 一行安装（使用者）

用 [skills CLI](https://skills.sh) 直接从 GitHub 安装，自动处理各 agent 的
技能目录与链接：

```bash
npx skills add cupen/skills                      # 交互式挑技能、选 agent
npx skills add cupen/skills -s git-finish -g     # 只装 git-finish，装到全局（~/）
npx skills add cupen/skills --all -y -g          # 全部技能、免确认、全局
npx skills update git-finish                     # 之后更新；remove 卸载、list 查看
```

默认以 symlink 安装（单一真源，易更新）；要独立副本加 `--copy`。

### 方式二：本仓库真源 + Python 脚本链接（维护者）

克隆本仓库后，把 `skills/` 链接进 `~/.agents/skills/`，改完即时生效、无需重装。
脚本纯标准库、跨平台，不依赖平台特有 shell；按自身位置定位仓库，任何目录可执行：

```bash
python scripts/install.py                # add：链接 skills/ 下全部技能（幂等，默认命令）
python scripts/install.py add git-finish # 只链接指定技能
python scripts/install.py status         # 查看各技能链接状态（全部已链 exit 0，否则 1）
python scripts/install.py remove         # 撤掉本仓库链接（只删链接本身）
python scripts/install.py remove --force # 连指向别处的链接一并移除
python scripts/install.py add -n         # dry-run：只演示将做什么，不改动
```

- Windows 优先建 junction（无需管理员/开发者模式），不可用时退回 symlink；
  Linux/macOS 建 symlink。
- 各子命令通用 flags：`-t/--target DIR` 自定义技能目录（默认 `~/.agents/skills`）、
  `-n/--dry-run` 预览（`status` 无此选项）。
- 目标位置若已是指向本仓库的链接 → 跳过；指向别处的旧链接 → 重建；
  **实体目录（私有技能）→ 一律不动**。

## 与 ~/.agents 的关系（真源在这里）

`~/.agents/skills/` 下的公开技能是**指向本仓库的链接**，改这里的内容即时生效于
所有 agent，无需复制：

- 公开技能：真源在本仓库，`~/.agents/skills/<name>` 是链接。
- 私有技能：**实体目录直接放在 `~/.agents/skills/<name>`**，不链接、不进任何
  公开仓库 —— `~/.agents` 本身不是 git 仓库，私有内容只存在本机。

## 约定

- 技能格式遵循 [Agent Skills 规范](https://agentskills.io/specification)：`SKILL.md`
  frontmatter 必填 `name`、`description`；`name` 为 kebab-case、长度 ≤64、
  不以连字符开头/结尾、不含连续连字符，且**必须与目录名一致**。
- `description` 承载「做什么 + 何时触发」，控制在 ≤250 字符（部分客户端只向模型
  展示前 ~250 字符，超出即不可见）；仅主动调用的技能在开头写明
  `Explicit invocation ONLY`。
- 技能目录名 = SKILL.md frontmatter 里的 `name`（kebab-case）。
- 私有技能若要避免与未来脚本混淆，目录名可用 `x-` 前缀。
