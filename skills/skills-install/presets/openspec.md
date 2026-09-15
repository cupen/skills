# openspec（Fission-AI/OpenSpec）

规格驱动开发（SDD）一组装：openspec CLI 本体 + 11 个 openspec-* 技能。MIT，上游 <https://github.com/Fission-AI/OpenSpec>。

CLI 是 npm 包，skills 只是配套——只装技能不装 CLI，`openspec list` 等命令跑不了，两组都要装：

```bash
npm install -g @fission-ai/openspec@latest
npx skills add Fission-AI/OpenSpec \
  -s openspec-apply-change -s openspec-archive-change -s openspec-bulk-archive-change \
  -s openspec-continue-change -s openspec-explore -s openspec-ff-change \
  -s openspec-new-change -s openspec-onboard -s openspec-propose \
  -s openspec-sync-specs -s openspec-verify-change -g
```

- 技能是模板生成的，官方声明勿手工编辑；项目内还有 `openspec init` / `openspec update` 写入的副本，用户目录全局一份即可。
- 善后：`npm install -g @fission-ai/openspec@latest` 更新 CLI（skills 副本随 `openspec update` 刷新）；卸载 `npx skills remove openspec-*` 逐个 + `npm uninstall -g @fission-ai/openspec`。
