## 2026-10-28（R237：整本朗读批次全灭——proxy 三元组被二元组解包；兼答「开始整本朗读后白屏」）

### R237（用户报告：「点击开始整本朗读后白屏」）

- **结论先行**：同一请求下有两个独立缺陷，均已修复：①整本朗读批次 100% 全灭（proxy 三元组被二元组解包）；②进度条外层被浮动列撑成整屏透明层，正文看似白屏、实际是被它覆盖并截走点击。前一轮把白屏仅归因于批次资源耗尽的判断已被 CSSOM/盒模型实测推翻，以下补记真因。
- **证据链**：①生产日志 `voice select failed (too many values to unpack (expected 2))`；②moon-well 侧每段两次 `/tts/speak`（第一次 2~10s 真合成、约 1s 后同文本 6ms 缓存命中）＝worker 重试环的指纹；③app.db 批次台账 done=0 / failed 全量增长；④`MoonWellClient.proxy` 源码恒返回 `(body, status, headers)` 三元组，`cps/reading_tts/service.py` 两处按二元组解包。
- **单测为何漏网**：桩 proxy 也只回二元组——桩没有镜像真实契约，service 的二元解包在单测里永远通过、一到生产就炸。本轮把三个桩全部改为三元组并新增契约守卫（反向变异实测 3 failed）。
- **止血**：发现时 book 50（HP1，3007 段）批次已烧 208 段全 FAILED，已直接置 CANCELLED 停止空转；已合成的音频都在 moon-well 段落缓存里，重新发起批次将全部缓存命中、几乎零成本走完。
- **白屏真因（R237 验收追加）**：生产页 DOM 实测 `.wb-progress` 位于详情页 `.container-fluid` 内；容器中的 Bootstrap 浮动列高 775px 且未清除。进度条外层从容器顶部起算、内层被浮动推到底部：外层 `813px` 高、内层仅 `37px` 且在 y=846，页面中心的 `elementFromPoint()` 命中进度条。正文没有丢失，只是被透明层覆盖；`clear:both` 试验可恢复 38px，但会把吸顶条落到文档底部。
- **白屏修法**：`whole-book-panel.js` 初始化时执行 `$progress.insertAfter($nav)`，把 `#whole-book-progress` 从浮动容器移到导航栏之后，保留原 sticky 吸顶语义。实测重挂后外层 38px、内层 37px、页面中心重新命中 `.book-meta`；新增守卫 `test_progress_bar_is_moved_out_of_float_layout`。
- **测试**：detail 39 passed；整本估算 + tts 5 文件 62 passed；i18n / 重复 JS 行 6 passed。既有反向变异仍成立：worker 解包改回二元组 → 3 failed。
- **合并与部署**：实现 `8c388234` 已 fast-forward 合入 `origin/develop`；推送约 30 秒后生产静态资源包含新逻辑。用该生产资源在真实详情页结构内重放：进度条父节点为 `BODY.book`，外层 38px、内层 37px，页面中心命中 `.book-meta`。
- **文档**：LLD `iterations/1.0/r214-book-detail/lld.md` §16 + 状态行。
- **驻留与闸门**：worktree `../magicbook-r237-tts-proxy-unpack`（分支 `fix/r237-tts-proxy-unpack`，基线 origin/develop `a23c91ba`，实现 `f4d8b934` + `8c388234`）已合并、原样驻留待验收。真机验收项：打开 `/book/50` 发起整本朗读后正文仍完整可点，进度条吸在导航栏下方且高度正常；批次 done 稳定增长、failed 不再全量增长；moon-well 每段仅一次 `/tts/speak`。
- **验收追加（部署重启后批次失联）**：上线后 `book 50` 批次停在 `RUNNING 1239/3007`，`PENDING 1768`、`FAILED 0`；最后推进 14:15:32，14:15:53 与 14:33:00 两次容器重启均发生在批次运行期间。根因是 worker 为进程内 daemon，重启即消失，而台账与页面仍显示 RUNNING；「开始」又被活跃批次禁用，前端无恢复入口。修法：`/ajax/reading-tts-book/status` 增发服务端判定的 `canResume`（未终态 + 有 PENDING + 本进程无活 worker），进度条据此显示「继续」，点击调用既有 retry 原地续跑；失败原因留在进度条内。新增服务/路由/模板 JS 守卫，恢复不新建台账、不重置进度、已完成段与音频缓存继续复用。
- **继续入口合并与部署**：实现 `b48a29ed` 已快进推送 `origin/develop`（`bb6c66f6..a2a1e88f`）。fnOS 于 16:36 完整构建（非 docs-only），app-manager 返回 `deploy SUCCESS`；生产容器 `healthy`，镜像 label `house.build-sha=a2a1e88f...`，线上 `whole-book-panel.js` 已核验包含 `canResume`、`ttsRetry` 与 `.wb-progress-resume` 点击接线。待真机在 `/book/50` 的失联批次上点「继续」，确认 done 从 1239/3007 继续增长且 PENDING 下降。
- **窗口**：写入前 10 节已满，按「写入即检查」把最早 R226 整节原样搬至 `response-archive/response-R226.md` 并登记索引，窗口保持 10。
- **总结**：requests.md 条目 237 已从占位回填；本条为回应。冲突记录：无撞号（claim.sh 占号 `a23c91ba`）。遗留登记：估算面板对 `reading_word_detail_job` 表缺失只 WARN 降级（该表在首次全文详解时由 `_ensure_tables` 创建），暂不处理。
