# agent-kit

Agent 随身工具箱：跨项目可复用的技能（skills）与一键安装脚本（python）。

## 布局

```text
agent-kit/
├── skills/       # 公开技能：每个子目录一个 <name>/SKILL.md
└── scripts/      # 一键安装/配置脚本（python）
```

## 与 ~/.agents 的关系（真源在这里）

`~/.agents/skills/` 下的公开技能是**指向本仓库的 junction**（Windows 目录联接），
改这里的内容即时生效于所有 agent，无需复制：

```powershell
# 新增公开技能后，在 ~/.agents/skills/ 建一条 junction：
New-Item -ItemType Junction `
  -Path "$env:USERPROFILE\.agents\skills\<name>" `
  -Target "D:\workbench\repos-ai\agent-kit\skills\<name>"
```

注意上面 Path 示例按实际盘符写，本机真源位置：`D:\workbench\repos-ai\agent-kit\`。

- 公开技能：真源在本仓库，`~/.agents/skills/<name>` 是 junction。
- 私有技能：**实体目录直接放在 `~/.agents/skills/<name>`**，不 junction、不进任何
  公开仓库 —— `~/.agents` 本身不是 git 仓库，私有内容只存在本机。

## 约定

- 技能目录名 = SKILL.md frontmatter 里的 `name`（kebab-case）。
- 私有技能若要避免与未来脚本混淆，目录名可用 `x-` 前缀。
- 推送目标：`git@github.com:cupen/skills`（公开）。
