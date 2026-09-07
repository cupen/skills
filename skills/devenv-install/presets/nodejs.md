# Node.js 生态预设（node / npm / pnpm）

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官网实时为准；日期仅供判断新旧。

`node`、`npm`、`pnpm` 共用本文件：npm 随 node 分发，pnpm 独立安装但同生态。**事实只认官网**：nodejs.org 与 pnpm.io。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| Node 下载页（LTS / Current 版本号） | https://nodejs.org/en/download |
| Node 二进制直链 | https://nodejs.org/dist/v<版本>/node-v<版本>-linux-<arch>.tar.xz |
| Node 校验和（与文件同目录） | https://nodejs.org/dist/v<版本>/SHASUMS256.txt |
| 包管理器安装指引 | https://nodejs.org/en/download/package-manager |
| pnpm 安装文档 | https://pnpm.io/installation |

版本策略默认 **LTS**（下载页明确标注哪条是 LTS），用户点名 Current 才装 Current。下载页是 JS 渲染，抓取可能拿不全——拿不全就去 package-manager 子页，还不行就用 tarball 直链。

## 已装检测

```bash
node --version; npm --version
pnpm --version 2>/dev/null
which -a node
grep -l 'nvm\|fnm\|volta' ~/.zshrc ~/.bashrc 2>/dev/null   # 已有版本管理器？
```

已有 nvm / fnm / volta → 升级走它（如 `nvm install --lts`），不再并装系统级 node；先问用户。

## 安装方式

多条路线，摘要里写明推荐与理由让用户挑：多项目多版本 → 版本管理器；就要一个稳定环境 → 官方 tarball 或包仓库。

1. **官方 tarball 直装**（跨发行版，校验和可核）：

   ```bash
   curl -fL https://nodejs.org/dist/v<版本>/node-v<版本>-linux-x64.tar.xz -o /tmp/node.tar.xz
   # SHASUMS256.txt 同目录，装前核对
   sudo mkdir -p /usr/local/lib/nodejs && sudo tar -xJf /tmp/node.tar.xz -C /usr/local/lib/nodejs
   # PATH 加 /usr/local/lib/nodejs/node-v<版本>-linux-x64/bin
   ```

2. **NodeSource 仓库**（nodejs.org 下载页给出的 apt/dnf 方式，系统级）：

   ```bash
   curl -fsL https://deb.nodesource.com/setup_<主版本>.x | sudo -E bash - && sudo apt-get install -y nodejs
   ```

   审阅时注明：脚本以 root 跑，是 nodejs.org 官方文档指引的方式。

3. **nvm / fnm**（版本管理器；来源是各自 GitHub 仓库而非 nodejs.org 域名，摘要里如实标注）：
   nvm：https://github.com/nvm-sh/nvm ；fnm：https://fnm.vercel.app

**pnpm**（官网首选独立脚本；pnpm 12 起是原生可执行文件，装好不依赖 Node）：

```bash
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

- 走 npm 装（Node ≥ 22.13 就位时）：`npx get-pnpm`（官网当前推荐写法，**不是** `npm i -g pnpm`）。
- 已装 pnpm 升级：`pnpm self-update`。
- 与 npm 全局装的 pnpm 并存会打架，二选一。

## 验证

```bash
node --version && npm --version
pnpm --version   # 装了才跑
```

## 中国大陆镜像

- **npmmirror.com**（阿里维护，原淘宝镜像，社区事实标准）：
  - node 二进制：https://npmmirror.com/mirrors/node/ （302 到 registry.npmmirror.com/-/binary/node/，直链同路径可用）；tarball 模式直接替换下载 URL。
  - nvm：`export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node`
  - fnm：`export FNM_NODE_DIST_MIRROR=https://npmmirror.com/mirrors/node`
  - pnpm：大陆用 `npm i -g pnpm --registry=https://registry.npmmirror.com` 更稳（get.pnpm.io 大陆可达性一般）。
- NodeSource 的 apt 源在大陆可达性一般；下载不通优先改走 npmmirror tarball。
- 日常包源（与工具链安装分开，装完单独问）：`npm config set registry https://registry.npmmirror.com`。

## 坑

- nvm 是 shell 函数不是可执行文件，非交互 shell 里 `command -v nvm` 查不到；看 rc 文件里有没有 source nvm.sh。
- tarball 直装把版本号钉死在 PATH 路径里，升级要改 rc；用户在意升级省心就推荐 nvm/fnm。
- 官网直装也要核对 SHASUMS256.txt，别只看文件大小。
- `npx get-pnpm` 取代了老的 `npm i -g pnpm` 推荐位，别教老命令。
