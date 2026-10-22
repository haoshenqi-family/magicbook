# 博客导入链（Halo → magicbook）补强（magicbook R195–R199）· LLD

**状态**：已 push 上线（magicbook `8a09af81` / moon-well `8a64094`，2026-10-21），worktree 驻留待用户验收；MAGICBOOK-206/207/208/209 未流转 Completed

## 1. 承接与诊断口径

用户指令「检查 magicbook 的博客导入和 ted 导入的功能还有哪些不足」→「这些问题拆分记录进 pingcode，然后开始修复」。
盘点按**事实源语义**倒推每条链路的失效面，而非按代码逐行找 bug：

- 博客链的事实源是「Halo 当前发布版」，连接器只是**触发器 + 搬运工**。任何让「Halo 已改、书没跟上」的路径都是缺陷。
- 由此得到四条实缺陷（本轮修）+ 一条体验缺口（R199，仅记录）。

## 2. 改动

### 2.1 `state.json` 跨书并发竞态（R195 / MAGICBOOK-206）

`tools/connector/server.py` 的 `_load_state()` / `_save_state()` 是**整份读-改-写**，
而 `_slug_lock` 只护同一本书 ⇒ `Dockerfile` 的 `gunicorn -w 1 --threads 4` 下两本书同时发布
会互相覆盖，丢掉对方的 `last_sha`。后果不是「少导一次」：下次该书发布时旧 sha 被当作新版本，
重建 EPUB ⇒ 文件 mtime 变 ⇒ 整本翻译 fingerprint 变 ⇒ **白烧积分**。

修法：新增模块级 `_state_lock`，并把散落的读改写收敛成两个原语——

```python
def _state_entry(slug):            # 读：进临界区，返回副本
def _state_update(slug, remove=(), **fields):   # 读改写：整段进临界区
```

`_slug_lock` 保留（防同书重入，锁序固定为 str 锁 → state 锁，无反向持有）。
`_state_update(remove=("translation_error",))` 顺带替掉原先手写的 pop 分支。

### 2.2 事件白名单（R196 / MAGICBOOK-207）

原实现 `payload.eventType != "NEW_POST"` 直接 ignored，文章修订后重新发布不进书。
改为 `_allowed_events()`：读 `CONNECTOR_EVENTS`（缺省 `NEW_POST,UPDATE_POST`），逗号分隔、大写归一、去空。
DELETE 类事件不在缺省白名单内，也不提供「配了就跑」的隐式放宽——真想删书要显式配置，且仍受
「映射表里没有就 no-op」保护。

### 2.3 手动对账入口 `POST /resync`（R197 / MAGICBOOK-208）

webhook 是事件驱动、无补投的：连接器停机或网络抖动期间丢掉的发布事件，此前只能去 Halo 手动重发布，
书的过期是**静默**的。

- 鉴权沿用 `X-Hook-Token`（与 webhook 同一把），未配置 token 时 fail-closed。
- body 可带 `{"slugs": ["a", "b"]}`，缺省 = `mapping.yaml` 全量。
- 逐条复用 `_process_slug`（sha 未变自动 no-op ⇒ 天然幂等），**单条失败不中断整批**，末尾汇总
  `{total, imported, failed, results:[{slug, result, ...}]}`；未进映射表的 slug 记 `no-mapping` 而不是 4xx。

### 2.4 封面先于 EPUB 落盘（R198 / MAGICBOOK-209）

`cps/book_import.py::_do_import` 原顺序是「`save_cover` + 刷缩略图 → 写 EPUB」，
EPUB 校验失败或超限时**封面已被换掉**，出现「新封面 + 旧正文」。改为：

```
EPUB 临时文件 → 大小校验 → os.replace 原子换入 → save_cover
```

封面失败降级为告警：EPUB 已生效，不回滚整次导入；响应体新增 `coverError` 字段（仅降级时出现），
`payload` 统一构造后 502 分支复用同一份。

## 3. 运维口径

```
# 容器 env（compose.yaml 的 env_file）
CONNECTOR_EVENTS=NEW_POST,UPDATE_POST      # 缺省即此值，列出想响应的事件类型
CONNECTOR_HOOK_TOKEN=...                   # webhook 与 /resync 共用，未配则拒绝一切

# 手动补账（映射表全量对账，幂等）
curl -X POST http://<connector>:9878/resync \
  -H "X-Hook-Token: $TOKEN" -H 'Content-Type: application/json' \
  -d '{"slugs":["some-slug"]}'        # 省略 body / slugs 即全量
```

返回里 `result` 取值：`imported`（含重建翻译）/ `unchanged`（sha 未变，no-op）/ `no-mapping` / `failed`。

## 4. 测试

`tools/connector/tests/test_server.py` 新增 8 例（21 passed）：

- `test_state_updates_are_serialized_across_slugs`：`slow_load` 放大读改写窗口 + 5 线程并发写 5 个 slug，断言 5 条全在（无锁时实测只剩 1 条，已用反向变异确认用例有效）。
- `test_state_update_removes_translation_error`、`test_update_post_event_is_processed`、`test_events_can_be_overridden_by_env`、`test_delete_events_stay_ignored`。
- `/resync`：缺 token 拒绝、全量两次跑幂等、未映射 slug 不失败、单条失败继续。

`tests/test_book_import.py` 新增 2 例（17 passed）：`test_cover_not_touched_when_epub_fails`（413 且 `save_cover` 零调用）、`test_cover_failure_after_epub_saved_degrades`（200 + `coverError`）。

## 5. 未修（R199 / MAGICBOOK-210）

H2 不进 TOC、H1 只识别单空格 ATX、图片只重写双引号 `src`（srcset/单引号漏下载，正文仍指外站）。
三条都属「离线可读性」，与 R195–R198 的数据正确性不同级，待真机验收后按需排期。
