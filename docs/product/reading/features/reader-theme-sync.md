# 阅读主题账号同步 · L3

> R216（2026-10-23）建立：5 个内置主题跨设备一致，自定义颜色仍只留本机。
> 相关：L1 [reading.md](../../readme/reading.md)、L2 [interface.md](../interface.md)、
> 本次实现 [lld.md](../../../project/iterations/1.0/r216-onboarding-prefs/lld.md)、moon-well R207（`user_ui_settings.reader_theme`）。

## 1. 主题范围

| 主题 | key | 是否同步 | 说明 |
| --- | --- | --- | --- |
| 浅色 | `lightTheme` | ✅ | 默认 |
| 深色 | `darkTheme` | ✅ | |
| 羊皮纸 | `sepiaTheme` | ✅ | |
| 琥珀 | `amberTheme` | ✅ | |
| 纯黑 | `blackTheme` | ✅ | |
| 自定义 | `customTheme` | ❌ | 色值存本机 `localStorage`，不上传 |

`/me` 只提供 5 个内置主题的原生 `radio`；阅读器工具栏保留自定义颜色入口。

## 2. 读取链路

```text
read.html <head>
  └─ <script src=".../static/js/ui-prefs.js">      ← 先于 epub.js
       ├─ GET /ajax/ui-settings（credentials: same-origin）
       ├─ readerTheme 合法 且 用户未手选 ─► window.__mbReaderTheme
       │                                ─► localStorage["calibre.reader.theme"]
       │                                ─► dispatch "magicbook:reader-theme"
       └─ 失败 ─► console.warn，本机主题照常

epub.js 初始化
  └─ 初始值 = window.__mbReaderTheme
              || localStorage["calibre.reader.theme"]
              || "lightTheme"
  └─ 监听 "magicbook:reader-theme" → selectTheme(synced)
```

- `ui-prefs.js` 从自身 `script.src` 反推应用根（子路径部署），并写入 `window.__mbBasePath` 供阅读器保存复用。
- 账号未设置（`readerTheme=null`）或值不在白名单内时，**保留本机选择**，不重置成默认。
- 新设备首帧可能先按本机/默认色渲染，异步结果到达后再切一次；这是有意的不阻塞阅读。

## 3. 写入链路

**阅读器**（`cps/templates/read.html`）

- 5 个内置主题按钮调用 `selectTheme(id, true)`；`sync === true` 且是内置主题时：
  1. 置 `window.__mbReaderThemePicked = true`；
  2. 本机立即生效并写 `localStorage`；
  3. `POST /ajax/ui-settings/reader-theme`（`X-CSRFToken`）。
- `customTheme` 只写本机并置 `picked=true`，不同步。
- 同步失败不回滚本机主题；阅读器 toast「主题未能同步到账号」，无 toast 组件时 `console.warn`。

**`/me` 偏好页**（`cps/static/js/me.js`）

- 初始选中顺序：本机合法值 → 账号值到达后覆盖（用户已改过则保留用户选择）。
- 保存：`POST /ajax/ui-settings/reader-theme` → 成功后写 `localStorage` 并回到服务端返回的主题。
- 读取账号值失败只提示「未能读取账号主题，显示本机上次选择」，不伪造已同步。

**代理**（`cps/routes/preferences.py`）

- `POST /ajax/ui-settings/reader-theme` → moon-well 同名端点，超时 8s。
- 代理层先按 5 个 key 白名单挡非法值（400），不把脏值送上游。
- 上游 `success:false` 原样透传；前端按失败呈现。

## 4. 竞态与边界

| 场景 | 处理 |
| --- | --- |
| 账号主题请求晚于用户手选 | `__mbReaderThemePicked` 为 true 时丢弃账号值，不覆盖用户动作 |
| 账号主题请求早于阅读器初始化 | `ui-prefs.js` 写 `window.__mbReaderTheme`，epub.js 初始值直接命中 |
| 账号主题请求晚于阅读器初始化 | 事件 `magicbook:reader-theme` 补切一次 |
| `/ajax/ui-settings` 不可达 | 阅读不受影响；仅 warn，不回退成「已同步」文案 |
| 保存失败 | 本机主题保持，状态可见；其他设备仍显示旧值 |
| 账号值为 `customTheme` / 未知值 | 按未设置处理，保留本机主题 |
| 隐私模式写 `localStorage` 失败 | 服务端仍是权威；本页内即时生效 |
| 同一浏览器切换账号 | 账号值覆盖本机镜像；用户手选优先于本次会话的异步值 |

## 5. 测试

`tests/test_reader_theme_sync.py`：

- 阅读页 `<head>` 在阅读器脚本前加载 `ui-prefs.js`。
- `ui-prefs.js` 有 `__mbReaderThemePicked` 守卫与子路径 base 推导。
- 5 个内置主题按钮都传 `true` 触发同步；自定义主题只置 picked。
- epub.js 初始值优先账号同步值，并监听 `magicbook:reader-theme`。
- `/me` 提供 5 个内置主题、读取账号值、保存后写本机并显示状态。

## 6. 已知不做

- 不做主题的强实时推送：其他设备在下一次打开/刷新阅读器时生效。
- 不同步自定义主题色值（涉及跨设备色板命名与冲突合并，收益不足）。
- 不在服务端保存「当前页面滚动位置」等瞬态阅读状态（属 R213-B `reading_progress` 的范围）。
