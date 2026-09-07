# Zig 预设

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官网实时为准；日期仅供判断新旧。

处理 `zig` 时先读本文件。**事实只认官网**：版本号、下载地址、签名公钥一律以 ziglang.org 为准。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| 下载页（版本、SHA、minisign 公钥） | https://ziglang.org/download/ |
| 自动化用 JSON 清单 | https://ziglang.org/download/index.json |
| 官方社区镜像列表（纯文本，一行一个 URL） | https://ziglang.org/download/community-mirrors.txt |

迭代节奏快：0.x 版本号，master 每天出 dev 构建；**默认装最新 stable**（现场从下载页取，0.16.0 是 2026-04 快照，勿凭记忆写版本），用户点名要某个旧版或 master 才例外。

## 已装检测

```bash
zig version
which -a zig
zig env 2>/dev/null    # 现有安装的 lib_dir 等布局信息
```

常见位置：`/opt/zig*`、`~/.local/zig*`、`/usr/local/zig*`（无统一约定，Zig 没有官方安装器，都是解压即用）。

## 安装方式

官方 tarball 是唯一官方路线（无官方 apt/brew 渠道）：

```bash
# 版本与文件名现场取；注意新命名是 架构在前
curl -fL https://ziglang.org/download/<版本>/zig-x86_64-linux-<版本>.tar.xz -o /tmp/zig.tar.xz
# 校验（官方强烈建议，走镜像时为强制）：
minisign -Vm /tmp/zig.tar.xz -P "<下载页公钥，现场取>"
sudo mkdir -p /opt && sudo tar -xJf /tmp/zig.tar.xz -C /opt
# PATH 加解压出来的目录（可执行文件在其根部：/opt/zig-x86_64-linux-<版本>/zig）
```

- minisign 没装的话 `apt install minisign` 或让用户选只核 SHA（下载页有）——但走镜像时签名校验不可省。
- `brew install zig` / 发行版包是社区维护的便捷替代，摘要里注明非官网直装、版本可能滞后。
- 没有自升级命令；升级 = 下载新 tarball 换目录，或用第三方版本管理器 **zigup**（github.com/marler8997/zigup，如实标注非官方）。

## 验证

```bash
zig version
zsh -ic 'zig version'   # 换成用户实际 shell，确认 PATH 已生效
```

## 中国大陆镜像

- 官方维护**社区镜像列表**：https://ziglang.org/download/community-mirrors.txt —— 现场抓取，逐个测可达性（`curl -sI -m 8`），挑一个通的下；URL 模式 `{镜像}/{文件名}?source=devenv-install`（`source` 参数官方鼓励带上）。
- **ZSF 官方声明：社区镜像不受官方信任与背书，可能投毒**——所以走镜像时 minisign 校验（用官网下载页的公钥）是强制步骤，不是可选项。
- TUNA / USTC / NJU 等大学镜像站**没有** zig 专区（2026-09 实测 404），别往那找。

## 坑

- **tarball 命名顺序变过**：≤ 0.14.0 是 `zig-linux-x86_64-<版本>`，0.15 起改成 `zig-x86_64-linux-<版本>`（架构在前）。脚本写死旧格式会 404。
- 0.x 相邻版本可能不兼容，用户项目常 pin 特定 zig 版本（`build.zig.zon` 里写最低版本）；装最新版前问一句项目有没有 pin。
- minisign 的 trusted comment 里有 `file` 字段需与请求的文件名一致，参考实现**不自动核**这项——防降级攻击要自己对一下。
- master/dev 构建别给生产环境用；用户说「装最新」默认理解为最新 stable，除非明说 nightly。
