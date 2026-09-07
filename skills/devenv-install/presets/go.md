# Go（golang）预设

> 上次核对：2026-09-07 —— 版本与镜像信息会过期，以官网实时为准；日期仅供判断新旧。

处理 `go` / `golang` 时先读本文件。**事实只认官网**：版本号、下载地址、校验和一律以 go.dev（或大陆官方站 golang.google.cn）为准，其他来源只作参考。

## 官网与权威来源

| 用途 | 地址 |
|---|---|
| 下载页（版本与 SHA256） | https://go.dev/dl |
| 安装文档 | https://go.dev/doc/install |
| 中国大陆官方站（Google 运营，与 go.dev 同源同内容） | https://golang.google.cn/dl |

下载页每个文件都公布 SHA256，**装前必核**。版本号永远现场从下载页取，不凭记忆写。

## 已装检测

```bash
go version                       # 已装：go version go1.x.x <平台>
go env GOROOT GOPATH 2>/dev/null
which -a go                      # 可能多份并存（发行版包 + 手装）
```

常见位置：`/usr/local/go`（官方 tarball）、`/usr/lib/go-*`（发行版包）。注意 `~/go` 是 GOPATH 工作区，**不是**安装目录。

## 安装方式（Linux 为例，macOS/Windows 见下载页对应卡片）

官方 tarball 是跨发行版首选（发行版仓库的 go 往往滞后一到两个大版本）：

```bash
# 版本号与文件名从下载页实时取；架构映射 x86_64→amd64，aarch64→arm64
curl -fL https://go.dev/dl/go<版本>.linux-amd64.tar.gz -o /tmp/go.tar.gz
echo "<下载页公布的SHA256>  /tmp/go.tar.gz" | sha256sum -c
sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
```

- 旧版在 `/usr/local/go` 必须**先删再解压**（官方文档要求），避免两份 GOROOT。
- PATH（tarball 方式必做）：`export PATH=$PATH:/usr/local/go/bin` 写入用户 shell rc。
- macOS：下载页的 `.pkg` 安装器（darwin-amd64 / darwin-arm64）；`brew install go` 是便捷替代，摘要里注明非官网直装。
- Windows：`.msi` 安装器，自带 PATH。

## 验证

```bash
go version
zsh -ic 'go version'   # 换成用户实际 shell，确认 PATH 已生效
```

## 中国大陆镜像

- **工具链下载**：把下载域名换成 https://golang.google.cn/dl/ —— Google 官方大陆站，文件名与 SHA256 和 go.dev 完全一致，校验和照核不误。这是唯一「官方背书」的镜像。
- **模块代理**（装完顺手单独问，与工具链安装无关）：`go env -w GOPROXY=https://goproxy.cn,direct`（七牛维护，社区事实标准），备选 `https://goproxy.io`。用户要写 Go 代码基本绕不开，摘要里给选项。

## 坑

- `apt install golang` / `dnf install golang` 版本普遍滞后；用户没点名「就用发行版包」就默认官方 tarball。
- GOPROXY 未配置时大陆拉模块会卡在 proxy.golang.org——用户报「go get 卡住」多半是这个，与工具链安装是两回事。
- Go 没有自升级命令，升级 = 重跑同样的 tarball 流程（先删旧的）。
