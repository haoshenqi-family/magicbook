# 整本任务进度条（L3 实现说明）

> 建立：2026-10-29（R246）。读者是**要改书籍详情页整本任务进度条的人**——这里只讲实现与边界；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)；
> 本次缺陷的取舍见 LLD
> [`project/iterations/1.0/r214-book-detail/lld.md`](../../../project/iterations/1.0/r214-book-detail/lld.md) §18。

## 1. 组成

进度条位于 `cps/templates/partials/whole_book_panel.html`，由
`cps/static/js/whole-book-panel.js` 驱动：

| 区域 | 内容 | 数据来源 |
| --- | --- | --- |
| 标题 | 任务类型 + 状态，如「全文单词详解 · 进行中」 | `data-t-progress-kind-*` + `data-t-progress-*` |
| 进度条 | 百分比 | `done / total` |
| 计数 | `done / total` | 三条整本链路状态接口 |
| 继续 | 仅朗读批次失联时出现 | 状态接口 `canResume=true` |
| 关闭 | 本次页面会话收起进度条 | 前端隐藏，不取消任务 |

页面初次加载的活跃批次由 `show_book` 注入 `entry.whole_book_active`；起批成功后使用
start 接口返回的快照；之后按既有频率轮询：翻译 4 秒、朗读 5 秒、详解 30 秒。

## 2. 任务类型键必须全小写

HTML 属性名会被浏览器统一解析成小写。因此模板写
`data-t-progress-kind-worddetail`，JS 必须先执行
`String(kind).toLowerCase()`，再拼成 `progress-kind-worddetail`。

不要把按钮动作文案复用为进度标题：`start-worddetail` 的值是「打开详解页面」，
它回答“点击后做什么”，而进度标题必须回答“当前是哪条任务”。

## 3. 状态映射

| job 状态 | 标题句式 |
| --- | --- |
| `PENDING` / `RUNNING` / 其他非终态 | `{task} · 进行中` |
| `COMPLETED` | `{task} · 已完成` |
| `PARTIAL_FAILED` | `{task} · 有失败段落` |
| `CANCELED` / `CANCELLED` | `{task} · 已取消` |

状态句式与任务名都放在模板 `data-t-*` 中，JS 只做变量替换；不要在 JS 里另写中文。

## 4. 边界

- **一条进度条**：同一本书多条链路并存时按
  `translate > tts > wordDetail` 选第一条展示，其余仍在各自面板中可见。
- **关闭不等于取消**：点 `×` 只隐藏当前页面的进度条，后台任务继续；刷新后若仍有活跃批次会重新出现。
- **不改任务契约**：进度条只消费既有 start/status/retry 响应，不新建 job、不改计费、不改缓存。
- **失败可见**：轮询单次失败不清空进度；恢复按钮失败原因留在进度条内显示。
- **响应式**：窄屏允许标题、进度条、计数换行，不横向溢出。

## 5. 测试

```bash
pytest tests/test_book_detail_r214.py -q
node --check cps/static/js/whole-book-panel.js
```

`test_progress_title_names_task_and_status` 钉住三类任务名、四种状态句式和小写化；
改回 `t('start-' + kind)` 或去掉 `toLowerCase()` 必须报红。
