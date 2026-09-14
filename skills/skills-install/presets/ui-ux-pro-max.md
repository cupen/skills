# ui-ux-pro-max（nextlevelbuilder/ui-ux-pro-max-skill）

UI/UX 设计智能一组装：ui-ux-pro-max 主入口 + design / design-system / ui-styling / banner-design / brand / slides 六个领域技能。MIT，上游 <https://github.com/nextlevelbuilder/ui-ux-pro-max-skill>（12w+ star）。

官方要求用其 CLI 安装——模板随 npm 包发布，直接拷仓库文件会拿到旧的：

```bash
npm install -g ui-ux-pro-max-cli@latest
uipro init --ai universal --global   # 装到 ~/.agents/skills/，与 agent-kit 链接共存
```

- 善后：`uipro update --global` 更新，`uipro uninstall --global` 卸载。
- 脚本依赖 Python 3（仅标准库，官方声明无网络行为、不装东西）；装完过目一眼 scripts 再放心用。
