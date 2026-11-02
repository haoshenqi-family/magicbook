# LLD · R230 个人学习数据导出入口（magicbook 侧）

> 状态：已上线待验收（2026-10-26；修订=①密码可选：空密码转发空 payload、任务行「未加密」标志；②下载 attachment 文件名透传上游（带任务创建时间）；③导出面板文案**中文直写**（不走 `_()` 翻译链，账号 locale=en 时 gettext 回退英文、用户要求恒中文；种子/po 既有词条留存无害）。代理 9 例 + 契约 5 例全绿）
> 需求基线：`docs/product/learning/requirements.md` §R230；后端主体与产物细节见 moon-well
> `iterations/2026-10-user-data-export/r220-user-data-export/`（同号跨仓）。

## 改动清单

| 文件 | 改动 |
| --- | --- |
| `cps/routes/user_export.py`（新） | 三代理端点；create 本地校验密码 6-128（400 不触上游）后仅透传 `{password}`；tasks GET 透传；download **binary=True** 透传 + `Content-Disposition: attachment; filename="my-learning-data-<id>.zip"`，非 200 原样透传（上游 Result 错误前端可读） |
| `cps/routes/__init__.py` | 注册 user_export 域路由 |
| `cps/templates/me.html` | 「Export My Learning Data」panel：说明、密码两遍（autocomplete=off）、帮助（密码不保存）、任务列表容器 |
| `cps/static/js/me.js` | 追加导出 IIFE：`MBApi.httpJson` 公共层 + csrfToken；提交校验（两遍一致）；任务列表渲染（状态/大小/过期时间/downloadable 下载按钮、FAILED 展示错误）；有 PENDING/RUNNING 时 5s 轮询、静默停轮 |
| `cps/templates/i18n_seed.html` | +14 词条（Queued/Generating/Ready/Failed/Expired/Download ZIP/…） |
| `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po`（+mo） | 种子词条 + me.html 模板词条共 +19 条译文，`babel.messages.frontend compile` 重编译 |
| `tests/test_user_export_proxy.py`（新） | 8 例：鉴权 302；短密码/缺失/非串本地 400 不触代理；create 载荷仅 password；tasks GET 无载荷；download 字节透传+attachment+binary 标志；上游 500 错误透传 |

## 关键决策

- **密码零存储**：本仓不落任何密码（连日志都没有），仅请求线程内透传 moon-well。
- **密码可选（2026-10-26 修订）**：空/缺省 → 转发空 payload（moon-well 不加密导出）；
  非字符串类型仍本地 400。
- **面板文案中文直写（2026-10-26 修订）**：me.html 导出面板与 me.js 导出段改中文常量、
  不经 `_()`/`mbT`——本站 i18n 是「英文 msgid→locale 译文」，账号 locale=en 时会回退英文，
  而该面板唯一读者要求恒中文。种子/po 既有词条留存（契约仍绿，无害）。
- **下载不缓冲**：binary 透传（Flask Response 直接回字节，moon-well 侧已流式）。
- **i18n**：me.js 在 `tests/i18n_js_files.json` 清单内 → 新 mbT 词条必须进种子（契约 2）+
  po（契约 3）+ mo（契约 5）；「Failed」词条本轮漏过一次种子，靠契约测试拦下。
- 部署顺序：moon-well R220 先（API 就绪），本仓后。

## 验收提示（真机）

1. `/me` 面板出现与文案中文化；2. 发起导出（密码两遍不一致有提示）；3. 轮询到「可下载」
后下载、用设定密码解压、Anki 导入 anki-vocabulary.csv；4. REPORT.md 可读；5. 7 天后任务
置灰「已过期」不可下载；6. 断开 moon-well（或积分不足场景不存在——导出不耗积分）时
错误透传可见。
