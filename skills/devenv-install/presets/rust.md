# Rust（rustup / cargo）预设

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官网实时为准；日期仅供判断新旧。

处理 `rust` / `rustup` / `cargo` 时先读本文件。**事实只认官网**：rust-lang.org 的安装文档是唯一权威，rustup.rs 是官方短链域名。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| 安装文档（rustup 一行命令） | https://www.rust-lang.org/tools/install |
| rustup 官方短链 | https://rustup.rs |
| 安装器脚本 | https://sh.rustup.rs |

安装页**不标具体版本号**（rustup 永远装最新 stable）；要报版本就现场跑 `rustc --version`，或看 https://blog.rust-lang.org 的 release 公告。

## 已装检测

```bash
rustc --version; cargo --version
rustup show 2>/dev/null     # 有 rustup → 升级走 rustup update stable，不重装
which -a rustc              # ~/.cargo/bin（rustup 默认）vs 发行版包
```

已有发行版包（如 apt 的 rustc）再装 rustup 会两套并存，`~/.cargo/bin` 在 PATH 前面通常赢；摘要里向用户说明这一点。

## 安装方式

官网原文一行命令（macOS / Linux / WSL 通用）：

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

- 给用户审阅时可保留交互（默认 stable，回车即可）或加 `-y` 变 `... | sh -s -- -y`，摘要里说明选了哪种。
- 脚本会把 `source "$HOME/.cargo/env"` 追加进 shell rc；**当前会话**要手动 source 一次才能立刻用。
- Linux 前置依赖：要有 C 编译器（`cc --version`），没有先装 gcc/clang，否则装完 link 失败。
- macOS 也可 `brew install rustup`（注明非官网直装）；Linux 发行版包版本滞后，默认不用。

升级（已有 rustup）：`rustup update stable`。

## 验证

```bash
source "$HOME/.cargo/env" 2>/dev/null
rustc --version && cargo --version
```

## 中国大陆镜像

- **rsproxy.cn**（字节跳动维护，社区镜像；仅支持 sparse index，Cargo ≥ 1.68）：

  ```bash
  export RUSTUP_DIST_SERVER="https://rsproxy.cn"
  export RUSTUP_UPDATE_ROOT="https://rsproxy.cn/rustup"
  # 两个变量就位之后再跑上面的 rustup 安装命令
  ```

  crates 依赖镜像（`~/.cargo/config.toml`，与工具链安装无关，装完单独问要不要配）：

  ```toml
  [source.crates-io]
  replace-with = 'rsproxy-sparse'

  [source.rsproxy-sparse]
  registry = "sparse+https://rsproxy.cn/index/"

  [registries.rsproxy]
  index = "sparse+https://rsproxy.cn/registry/"

  [net]
  git-fetch-with-cli = true
  ```

- **清华 TUNA** 也提供 rustup 镜像，环境变量取值以其帮助页为准：https://mirrors.tuna.tsinghua.edu.cn/help/rustup/
- 两个都列给用户挑。安装脚本 sh.rustup.rs 本身一般直连可达，卡的是后续 toolchain 下载——所以只改环境变量，**不改官网的管道命令**。

## 坑

- `RUSTUP_DIST_SERVER` / `RUSTUP_UPDATE_ROOT` 要在**跑安装命令之前** export，且只影响当前会话；要不要持久化进 rc 单独问用户。
- rustup 是工具链管理器，磁盘占用在 `~/.rustup`；`rustup default stable` 管默认链。
- 没有「只装 cargo 不装 rustc」的合理装法；别用 `apt install cargo` 凑合。
