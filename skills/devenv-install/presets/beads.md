# Beads（bd）预设

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官方实时为准；日期仅供判断新旧。

处理 `beads` / `bd` 时先读本文件。**事实只认官方**：GitHub 仓库与官方文档站 beads.gascity.com。Beads 是面向 AI agent 的分布式图状 issue tracker（CLI 命令 `bd`，内嵌 Dolt 数据库），不是语言工具链，装完还要在项目里 `bd init` 才可用。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| GitHub 仓库（安装脚本、Releases） | https://github.com/gastownhall/beads |
| 官方文档站 | https://beads.gascity.com/ |
| 升级指南（有数据库，升级必读） | https://beads.gascity.com/getting-started/upgrading |
| Releases 校验和 | `https://github.com/gastownhall/beads/releases/download/<tag>/checksums.txt` |

版本现场从 Releases 取（2026-09-07 快照：v1.2.2，与 npm 包 @beads/bd 同版本）。

## 已装检测

```bash
bd version            # 官方升级流程用的就是这条
which -a bd
```

常见位置：`/usr/local/bin/bd`（install.sh 首选）、`~/.local/bin/bd`（install.sh 兜底）、brew / npm 全局 bin。注意区分**工具**与**数据**：`bd init` 在每个项目里生成 `.beads/` 数据库，重装工具不碰各项目数据。

## 安装方式（README 官方给出的路线，按现场让用户挑）

1. **Homebrew**（upstream 标注 recommended，macOS / Linux）：

   ```bash
   brew install beads
   ```

2. **官方 install.sh**（走 GitHub Releases，自动核 SHA256）：

   ```bash
   curl -fsSL https://raw.githubusercontent.com/gastownhall/beads/main/scripts/install.sh | bash
   ```

   脚本装到 `/usr/local/bin`（不可写则 `~/.local/bin`），并强制下载 `checksums.txt` 核验、核验不过拒绝安装。
3. **npm**（Node 就位时）：`npm install -g @beads/bd` —— 注意包里只有 JS 壳，**postinstall 会去 GitHub Releases 拉平台二进制**（URL 硬编码，无换源变量），大陆环境此路线不完整，见镜像节。
4. **go install**（有 Go 工具链时）：

   ```bash
   CGO_ENABLED=0 go install -tags gms_pure_go github.com/steveyegge/beads/cmd/bd@latest
   ```

Windows 用 install.ps1（`irm https://raw.githubusercontent.com/gastownhall/beads/main/install.ps1 | iex`）。

## 验证

```bash
bd version
zsh -ic 'bd version'   # 换成用户实际 shell，确认 PATH 已生效
```

装完提醒用户：在项目目录 `bd init`（或 `bd init --stealth` 免 git 提交）才会创建数据库；`bd setup claude` / `bd setup codex` 等可装 agent 集成。

## 中国大陆镜像

- **首选 go install + goproxy.cn**（有 Go 工具链时，完整性走 GOSUMDB 校验链）：

  ```bash
  GOPROXY=https://goproxy.cn,direct CGO_ENABLED=0 go install -tags gms_pure_go github.com/steveyegge/beads/cmd/bd@latest
  ```

  注意 go module 路径是 `github.com/steveyegge/beads`，**不是** gastownhall——别「纠正」它（见坑）。
- **GitHub Releases 加速代理**：`beads_<版本>_<platform>.tar.gz`（如 `beads_1.2.2_linux_amd64.tar.gz`）与 `checksums.txt` 都经代理下载，装前必须对 SHA256；checksums.txt 与压缩包同源经代理，信任链有折扣，向用户明示。
- **npm 路线**：registry 可走 `https://registry.npmmirror.com`（包已同步），但 postinstall 拉二进制仍直连 GitHub 且无换源变量——大陆不建议此路线，走上面两条。
- npmmirror 的二进制区**没有** beads（`/-/binary/beads/` 404），别去找。

## 坑

- **Go module 路径与 GitHub 仓库不同名**：仓库在 `gastownhall/beads`，module 是 `github.com/steveyegge/beads`（官方脚本注释：为兼容已发布 tag）。改写成 gastownhall 会 go install 失败。
- **升级不是换二进制就完事**：beads 带数据库。官方流程：`bd export --all` 备份 → 升级二进制 → `bd info --whats-new`、`bd hooks install`、`bd version`；远程库跨 schema 迁移时由一个指定 clone 跑 `bd migrate` + `bd dolt push`，其余 clone `bd bootstrap`。已有项目升级先读升级指南，问用户有没有要同步的库。
- npm 包与 release 二进制版本号同步（都是 v1.2.2 之类），但来源不同（npm registry vs GitHub Releases），混装时以 `bd version` 实测为准。
- raw.githubusercontent.com 与 api.github.com 在大陆可达性差：install.sh 依赖这两处，走镜像节方案，别反复重试硬刚。
