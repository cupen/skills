# Bun 预设

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官网实时为准；日期仅供判断新旧。

处理 `bun` 时先读本文件。**事实只认官网**：bun.com 与 bun.sh 都是官方域名（文档混用，Windows 脚本仍在 bun.sh），不是钓鱼站。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| 安装文档（命令原文） | https://bun.com/docs/installation |
| 安装脚本（POSIX） | https://bun.com/install |
| GitHub Releases（二进制直链） | https://github.com/oven-sh/bun/releases |

版本现场从官网/文档取；无 LTS 概念，默认装最新 stable。

## 已装检测

```bash
bun --version
which -a bun    # ~/.bun/bin/bun（脚本安装）vs npm 全局（npm i -g bun）
```

已有版本管理器/包管理器装的（brew、scoop）→ 升级走对应命令，不混装。

## 安装方式

官方脚本（Linux / macOS）：

```bash
curl -fsSL https://bun.com/install | bash
```

- 审阅时注明：脚本管道进 bash，会写 `~/.bun` 并把 `BUN_INSTALL`/PATH 追加进 shell rc；指定旧版在后面接 `-s "bun-v<版本>"`。
- Windows：`powershell -c "irm bun.sh/install.ps1|iex"`（注意 ps1 在 bun.sh 域名下，官方文档原文如此）。
- node 已就位时的替代：`npm install -g bun`（bun 本身是原生二进制，npm 只是分发渠道，不依赖 node 运行）。
- macOS `brew install oven-sh/bun/bun`、Windows Scoop：便捷替代，摘要里注明非官网直装。
- Bun 自带包管理器，装完 `bun install` 直接替代 `npm install`，不需要再装别的。

## 升级（已装时）

```bash
bun upgrade          # 自升级（走 GitHub 源）
```

brew / scoop 装的分别用 `brew upgrade bun` / `scoop update bun`，避免双份冲突。

## 验证

```bash
bun --version && which bun
zsh -ic 'bun --version'   # 换成用户实际 shell，确认 PATH 已生效
```

## 中国大陆镜像

- 官方脚本**没有**镜像变量（下载源硬编码 GitHub Releases，大陆直连慢/断是常态）——不改脚本，改走二进制直装。
- **npmmirror.com**（阿里维护）镜像 bun 二进制，路径实测可用（302 进 CDN）：

  ```text
  https://registry.npmmirror.com/-/binary/bun/bun-v<版本>/bun-linux-x64.zip
  https://registry.npmmirror.com/-/binary/bun/bun-v<版本>/bun-linux-aarch64.zip
  ```

  流程：从镜像下 zip → 解压 → 把 `bun` 二进制放到 `~/.bun/bin/` 并 `chmod +x` → PATH 确认。版本号从官网文档取，镜像只是替换下载源。
- `bun upgrade` 的日常自升级仍走 GitHub；大陆环境升级同样卡的话，重复上面的镜像直装流程换版本即可。

## 坑

- bun.com 与 bun.sh 双域名并存：文档页在 bun.com，Windows 的 ps1 在 bun.sh，都是官方，别互相「纠正」。
- 脚本装的 bun 与 `npm i -g bun` 装的并存时，PATH 顺序决定用哪个；摘要里让用户二选一。
- zip 不是 tar.xz：bun 的发布物是 `.zip`，解压用 `unzip`。
- Bun 既是运行时也是包管理器/测试器；用户说「装 bun」通常顺带指 `bun install` 能跑起来，验证时用 `bun --version` 即可，不必拉项目依赖。
