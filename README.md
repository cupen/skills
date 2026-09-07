# agent-kit

Agent 随身工具箱：跨项目可复用的技能（skills）、subagent 定义（subagents/）与一键安装脚本（python）。

技能格式遵循 [Agent Skills Specification](https://agentskills.io/specification)：
每个技能是一个目录，必含 `SKILL.md`（YAML frontmatter + Markdown 正文），
frontmatter 必填 `name` 与 `description`。

Subagent 采用 Claude Code 的
[subagent 格式](https://code.claude.com/docs/en/sub-agents)（业界事实标准，Cursor 直接兼容）：
`subagents/<name>.md`，YAML frontmatter 必填 `name` 与 `description`，Markdown 正文即系统提示词。
安装时由脚本**按目标工具转换格式**（Claude Code / ZCode / Codex / Gemini CLI / OpenCode / Copilot），
同一份真源分发到所有工具。

## 布局

```text
agent-kit/
├── skills/       # 公开技能：每个子目录一个 <name>/SKILL.md
├── subagents/    # subagent 定义：每个文件一个 <name>.md（Claude Code 格式）
└── scripts/      # 一键安装/配置脚本（python）
```

## 技能

- [git-finish](skills/git-finish/SKILL.md) — worktree 收尾：conventional commits、rebase 后 `--no-ff` 合入 main 保留分支历史、重新验收、推送、总结。
- [git-worktree](skills/git-worktree/SKILL.md) — 开工区（仅显式调用）：入参功能名与分支名，在旁边建 `../<仓库名>-<功能名>` worktree；分支已存在则复用、不存在则 fork，创建前交互预览。
- [git-worktree-update](skills/git-worktree-update/SKILL.md) — 批量同步（仅显式调用）：把每个 worktree 的分支依次 rebase 到最新 main，就地解决冲突并保持各分支解法一致；不合入、不推送。
- [git-worktree-finish](skills/git-worktree-finish/SKILL.md) — 批量收尾（仅显式调用）：对每个 worktree 依次执行 git-finish，完成后列出全部 worktree，让用户挑选删除。
- [devenv-install](skills/devenv-install/SKILL.md) — 开发环境安装（仅显式调用）：逐个工具从官网取证、生成安装命令供逐个审阅后执行；下载不通时询问是否大陆用户，提供镜像备选。

## Subagents

- [rust-web-engineer](subagents/rust-web-engineer.md) — Rust + Web 前端全栈工程师：涉及 Rust（tokio / wasm / axum）、Web UI（TypeScript / React / Vue）或两者集成（Tauri / WASM / REST）的任务主动委派给它。

## 安装技能

### 方式一：`npx skills` 一行安装（使用者）

用 [skills CLI](https://skills.sh) 直接从 GitHub 安装，自动处理各 agent 的
技能目录与链接（只覆盖技能；**subagents 走方式二**）：

```bash
npx skills add cupen/skills                      # 交互式挑技能、选 agent
npx skills add cupen/skills -s git-finish -g     # 只装 git-finish，装到全局（~/）
npx skills add cupen/skills --all -y -g          # 全部技能、免确认、全局
npx skills update git-finish                     # 之后更新；remove 卸载、list 查看
```

默认以 symlink 安装（单一真源，易更新）；要独立副本加 `--copy`。

### 方式二：本仓库真源 + Python 脚本安装（维护者）

克隆本仓库后运行脚本：`skills/` 逐个**链接**进 `~/.agents/skills/`（各工具共享的
技能根目录，改完即时生效）；`subagents/` 按目标工具**转换格式后写入**各工具的 agents
目录（改源文件后重跑安装命令同步，status 会提示内容漂移）。脚本纯标准库、跨平台，
不依赖平台特有 shell；按自身位置定位仓库，任何目录可执行：

```bash
python scripts/install.py                          # 一键：全部技能 + 全部 subagent（幂等，默认命令）
python scripts/install.py skill git-finish         # 只装指定技能
python scripts/install.py subagent rust-web-engineer  # 只装指定 subagent
python scripts/install.py subagent --to codex,gemini  # subagent 装到指定目标
python scripts/install.py status                   # 查看状态（全部就位 exit 0，否则 1）
python scripts/install.py remove             # 卸载（只删本脚本生成的链接/文件）
python scripts/install.py remove --force     # 内容不一致时也强制移除
python scripts/install.py -n                 # dry-run：只演示将做什么，不改动
```

- subagent 目标（`--to`，可重复、可逗号分隔、`all` = 全部，默认 `claude,zcode`）：

  | 目标 | 写入位置 | 转换 |
  |---|---|---|
  | `claude` | `~/.claude/agents/<name>.md` | 原样（Claude Code 格式） |
  | `zcode` | `~/.zcode/agents/<name>.md` | camelCase frontmatter |
  | `codex` | `~/.codex/agents/<name>.toml` | OpenAI agent role，正文 → `developer_instructions` |
  | `gemini` | `~/.gemini/agents/<name>.md` | snake_case 键（如 `max_turns`） |
  | `opencode` | `~/.config/opencode/agents/<name>.md` | 文件名即身份，强制 `mode: subagent` |
  | `copilot` | `~/.copilot/agents/<name>.agent.md` | VS Code / Copilot 自定义 agent |

- 技能链接：Windows 优先 junction（无需管理员/开发者模式），退回 symlink；
  Linux/macOS 建 symlink。
- flags 只有三个：`-n` 预览不改动；`--to` 指定 subagent 目标；`--force` 卸载兜底
  （`status`/`remove` 可加 `skill` 或 `subagent` 只处理一类）。
- 目标处若已是指向本仓库的技能链接 → 跳过；指向别处的旧链接 → 重建；
  subagents 只覆盖本脚本生成的同名文件，**实体目录/他人文件一律不动**。

## 真源与分发（改这里即时生效 / 重跑同步）

- 公开技能：真源在本仓库，`~/.agents/skills/<name>` 是链接，改完即时生效于所有 agent；
  skills CLI 与 DeepSeek Harness (dsh) 也读这一目录。
- 私有技能：**实体目录直接放在 `~/.agents/skills/<name>`**，不链接、不进任何
  公开仓库 —— `~/.agents` 本身不是 git 仓库，私有内容只存在本机。
- subagent：真源在本仓库 `subagents/`（Claude Code 格式），各工具目录里是**转换后的副本**，
  改源文件后重跑 `python scripts/install.py` 同步；Cursor 另会直接读 `.claude/agents`。
  私有 subagent 放 `subagents/x-*.md`（`.gitignore` 已排除），同样参与分发。

## 约定

- 技能格式遵循 [Agent Skills 规范](https://agentskills.io/specification)：`SKILL.md`
  frontmatter 必填 `name`、`description`；`name` 为 kebab-case、长度 ≤64、
  不以连字符开头/结尾、不含连续连字符，且**必须与目录名一致**。
- `description` 承载「做什么 + 何时触发」，控制在 ≤250 字符（部分客户端只向模型
  展示前 ~250 字符，超出即不可见）；仅主动调用的技能在开头写明
  `Explicit invocation ONLY`。
- 技能目录名 = SKILL.md frontmatter 里的 `name`（kebab-case）。
- 私有技能若要避免与未来脚本混淆，目录名可用 `x-` 前缀。
- subagent 文件名 = frontmatter 里的 `name`（kebab-case）；`description` 写清
  「做什么 + 何时委派」，同样 ≤250 字符；正文即系统提示词。
- subagent 基础 frontmatter 只写**交集字段**（`name`、`description`，可选 `model`/
  `tools`/`maxTurns` 等，`author`/`version` 会透传给除 codex 外的目标）；某目标独有的配置写进 `targets:` 段（键用目标原生拼写，
  安装时按目标注入），映射不到目标的基础字段会被丢弃并在安装时警告。
  例：`targets: { codex: { sandbox_mode: workspace-write } }`。
- `model` 省略时用各工具默认模型；Codex 目标按官方 agent role 校验（未知键会拒绝），
  转换器只输出其合法键。
- 私有 subagent 文件名用 `x-` 前缀（`.gitignore` 已排除 `subagents/x-*`）。
