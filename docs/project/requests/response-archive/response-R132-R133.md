# response 归档：R132–R133

> 2026-10-10（R143 写入触发窗口轮转）从 `response.md` 原样搬移：R132（B3 学习调度中枢前端实施）、R133（排查「查 creation 详解显示 created」）。只搬移原文，不总结、不改写、不改编号。

## 2026-10-08（R132：B3 学习调度中枢前端实施）

- **范围**：moon-well R116 B3 后端就绪后的 magicbook 前端落地 + 双仓提交推送（用户指令「前端一并也实施，然后提交推送，我来验收」）。
- **web.py（8 个视图）**：`GET /learning` 每日学习页（首屏零上游调用，数据全异步）+ 7 个 `/ajax/learning-*` 薄代理（srs/queue|answer|stats、plan/today|settings、match/books|book）。代理纪律与词汇量测试一致：登录墙、参数域本地校验（scheduleId 纯数字、grade 1-4、latencyMs≥0、四股 0-100、bookId 纯数字）、业务错误 HTTP 500 + Result.code 原样透传（50501-50506 语义归上游）、不可达 503 JSON。
- **cps/templates/learning.html**：统计头（今日/明日到期、已掌握、7 天保持率）、每日计划头（四股分钟预算）、复习卡（词条+遇见次数徽章+语境卡+出处）、CHOOSE 四选一 / RECALL 揭示 / 四档评分（忘记/难/想起/轻松）、选书难度匹配列表（三档 label + 密度 + 高频生词样例）；bootstrap modal/theme 复用不自带配色（vocab-test 同 UI 纪律）。
- **cps/static/js/learning.js（新增 350 行）**：队列状态机（在途锁、评分连击忽略、500ms 过渡刷新统计）、三题型渲染与判定、计划/统计/匹配三路异步加载互不阻塞、CSRF 注入读取（ln-csrf）、mbT 本地化通道。
- **i18n**：i18n_seed.html 新增 40 词条（含 Daily Learning/Review Queue/忘记/难/想起/轻松等），messages.po 补 38 条中文（2 条已存在），pybabel 重编 mo；`2–8%` 触发 pybabel placeholders 不兼容 → 改写为「每一百个词里有二到八个生词」后编译通过。test_i18n_seed_contract 的 JS 清单加入 learning.js（本地化守卫同 vocab-test 先例）。
- **导航**：layout.html Settings 下拉新增「Daily Learning」（top_learning， Achievement 上方）。
- **阅读页零改动说明**：阅读器 ＋/－ 标记经 /vocabulary/unknown|known 即触发 moon-well LearningMarkEvent（R116 已接线），SRS 入队自动完成，无需前端改动。
- **测试**：新增 tests/test_learning_proxy.py 17 用例（鉴权 7 端点、GET 透传、answer/settings/match 参数域、上游 50503/50501 透传、页面 DOM 渲染、导航入口）；**开发态部分单测**（R131 两级闸门）：test_learning_proxy 17 绿、i18n_seed_contract+nav 11 绿；**全量**（本次为推送验收）：`pytest tests/` **381 passed / 0 failed**（基线 364 + 17）。
- **边界**：书架页 badge 未做（难度匹配集中在学习页列表呈现，避免侵入上游书架模板）；magiclens 不涉及；LLD/契约见 moon-well docs/feat/scientific-learning/design/us1-b3-scheduling-lld.md §4。
- **总结**：requests.md 本条 R132；冲突记录：无（132 未被并行占用）。

### R133（排查「查 creation 详解显示 created」——magicbook 侧结论）

- **回应**：magicbook 侧链路（`/ajax/reading-word-detail` 代理 + `epub.js` 面板）无缺陷：代理正确归一化（小写+直撇号）转发 moon-well；前端标题取 `d.lemma || d.word`，与 magiclens v0.4.0 同源。根因在 moon-well（详见 moon-well response.md R123）：creation 的预热任务失败（worker DNS）致其无自有缓存文档，`findCached` 经 `forms.form=creation` 命中 `lemma=create` 的文档，而该文档内容是 created 任务的输出（docId=SHA-256(lemma) 覆盖写撞车，created 任务 22:12:24 顶掉 create 任务 22:11:26 的正解）。magicbook 侧无需改动。

