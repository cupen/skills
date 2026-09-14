# grill-me（mattpocock/skills）

拷问式访谈 + 教学一组装：grill-me、grill-with-docs 两个入口壳依赖 grilling 引擎；teach 教学工作区自包含。MIT，上游 <https://github.com/mattpocock/skills>。

```bash
npx skills add mattpocock/skills -s grill-me -s grill-with-docs -s grilling -s teach -g
```

- grilling 会因「拷问我 / grill me」自动触发；grill-me / grill-with-docs / teach 仅显式调用。
- 上游有更新时 `npx skills update` 逐个同步。
