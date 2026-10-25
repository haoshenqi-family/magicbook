# LLD — R226 阅读器验收缺陷修复

> 状态：**开发中（2026-10-25，代码与定向回归完成，待合并上线与真机验收）**
> 关联需求：R226（登记于 `docs/project/requests/requests.md`）；验收缺陷归属 MB-14 / R215、R223、R216。

## 1. 背景与结论

用户在 R225 上线后补做阅读器验收。先确认以下既有能力正常：

- 普通读者可进入 `/read/223/epub`，不再 403；
- 桌面顶栏显示 24px 图标 + 12px 文字标签；
- 段落朗读/翻译/批注/AI 伴读四枚控件都有 `title` 与 `aria-label`；
- AI 面板打开后为 420px 覆盖式抽屉，移动端全屏。

同时确认三项真实缺陷：

1. 伙伴 FAB 头像外仍出现白色圆形底；
2. 阅读器右下角有一枚无文案「?」，看起来像幽灵浮层；
3. 整页翻译在请求期逐段插入 `Translating…`，每次结果返回又逐段替换，连续改变 iframe
   内容高度并触发重分页。

AI 面板遮正文不是缺陷：2026-10-23 用户已明确否决停靠式面板，接受 420px 覆盖式抽屉。
本轮不改该形态。

## 2. 根因

### 2.1 伙伴白圆底

`ai_chat.css` 先声明：

```css
#ai-companion-fab.has-buddy { background: transparent; box-shadow: none; }
```

R206 区块随后以同特异度再次声明：

```css
#ai-companion-fab.has-buddy { background: #fff; padding: 0; }
```

后写规则覆盖透明背景，真机呈现白色圆形底板。

### 2.2 幽灵「?」

`onboarding.js::showReaderHelp()` 动态创建固定定位的 `#onb-help`，按钮可见文本只有 `?`；
`title`/`aria-label` 虽为「使用引导」，但桌面不悬停时无法知道含义。CSS 只是把它从
左下移到 FAB 上方，仍然是无标签圆形浮层。

### 2.3 翻译连续重排

`applyImmersiveTranslation()` 先对最多 20 个可见段插入 `Translating…`，随后每个并发请求
完成就用译文替换该段占位。每替换一次都改变 iframe 内容高度，最多造成 20 次布局变化。即使用户
接受最终译文导致的整体重分页，也没有理由接受请求期间的连续抖动。

## 3. 实现

### 3.1 伙伴头像

- 删除 R206 重复的 `background: #fff`，只保留 `padding: 0`；
- 首次声明的 `background: transparent; box-shadow: none;` 继续作为唯一来源；
- 无头像兜底态仍保留浅蓝底 +「AI」，不改变可读性。

### 3.2 导览入口

- 按钮可见文本与 `title`/`aria-label` 共用本地化 `mbT("Onboarding Tour")`；
- 保持右下 FAB 上方位置，改为 40px 高胶囊，水平内边距 14px；
- 移除旧收尾文案「左下角 ?」，改为指向右下角「Onboarding Tour」；同步替换 i18n 种子
  与中文 PO/MO，避免旧文案继续出现。

### 3.3 批量翻译

- 请求期不再向正文插入占位；
- 顶栏 `#immersive-translate` 加 `is-loading` 与 `aria-busy="true"`，图标做轻微脉冲，
  `prefers-reduced-motion` 下关闭动画；
- 并发池仍为 4，所有请求结束后在同一 JS 任务里按原顺序一次性 `insertTranslation`；
- 缓存写入合并为一次；失败段在同一批渲染中显示既有可点击重试块；
- 如果用户在请求期间关闭翻译，完成回调不再写正文。

## 4. 能观察到的结果

- 伙伴头像边缘直接贴合书页背景，没有白圆；
- 阅读器右下角出现明确的「使用引导」按钮；
- 点顶栏「译」后，正文在等待期间保持不动，只看到顶栏加载态；整页译文一次出现；
- 最终整体插入仍可能触发一次 epub.js 重分页，这是 R215 已接受的固有代价。

## 5. 边界与回归

| 场景 | 结果 |
| --- | --- |
| 单段「译」 | 仍立即插入加载态并显示译文，不受批量路径改动影响 |
| 批量翻译部分失败 | 成功段显示译文，失败段显示可重试错误块 |
| 批量请求中关闭翻译 | 加载态立即清除；迟到的结果不写正文 |
| 批量请求中翻页 | 结果按原段落节点回填；不存在节点时 `insertTranslation` 找不到父节点即跳过，不新插到别页 |
| 缓存命中 | 不请求，直接显示缓存译文 |
| 减少动态效果 | 顶栏加载态不脉冲，但仍保留 `aria-busy` 与行为 |

## 6. 测试

新增 `tests/test_reader_r226_acceptance.py`：

- `.has-buddy` 的 R206 区块不得再声明 `background`；
- `#onb-help` 必须渲染本地化文案，禁止 `>?</button>` 回流；
- 导览收尾文案必须指向右下角入口；
- 批量翻译不得在请求期插占位，必须在全部完成后一次调用 `renderTranslationBatch`；
- 顶栏加载态与 reduced-motion 样式存在。

定向回归覆盖 R215 UI、引导导览、导航下拉、模块表面、翻译与 i18n 契约。

## 7. 文档四问

- 能力：L1 `readme/reading.md` 补「使用引导」和批量翻译等待反馈；
- 契约：无接口变化；
- 实现/边界：L3 `reading/features/companion-panel.md`、`learning/features/onboarding.md`；
- 本次实现：本 LLD。
