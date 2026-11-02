> 归档：R204（写作批改 SSE 真机无进度——WSGI 容器把流缓冲掉了）原样搬移自 `response.md`。
> 2026-10-23 R216 第三次 merge（R215/R218 基线）后窗口达 11，按「写入即检查」续搬最旧一节；只搬移原文、不总结、不改写。

## 2026-10-22（R204：写作批改 SSE 真机无进度——根因是 WSGI 容器把流缓冲掉了）

### R204（用户：还是有问题。2.5分钟后 超时，response 一直没有数据）

- **先纠正上一轮的定性**：上一轮把这次失败判成「magpie 150s 预算耗尽，代理已生效」。后半句是错的——代理确实逐 chunk `yield`，但**一帧都没离开进程**。两个缺陷同时存在，各自独立。
- **根因（容器内实测，不是推断）**：本仓用 tornado `HTTPServer(MyWSGIContainer(app))` 起 WSGI（容器内 `import gevent` 直接失败，走的 tornado 分支）。tornado ≥6.3 的 `WSGIContainer.handle_request` 把 WSGI iterable 的全部 chunk 收进 `response` 列表，最后 `b"".join` 一次性 `write_headers(chunk=body)` 并补 `Content-Length`。SSE 于是被整体缓冲：`status`/`ping` 全押到批改结束，前端整个等待期看不到任何事件——就是用户说的「一直没有数据」。
- **复现手法（可复用）**：在生产容器里跑一个与业务无关的最小 WSGI 应用（4 帧、每帧间隔 1s），用 `MyWSGIContainer` + tornado `HTTPServer` 起服务，客户端按行打时间戳。修复前：**响应头 4.00s 才出现、`Content-Length: 108`、四帧全部挤在 4.00s**。这比读代码更硬，因为用的是生产同一个类、同一个容器。
- **第二个隐蔽坑**：tornado 6.3 起 `WSGIContainer` 默认 `dummy_executor`（WSGI 应用跑在事件循环线程）。SSE 的阻塞读一次要等 5s 心跳、极端情况下整段批改，若沿用会让整站请求跟着卡死。所以流式分支必须换独立线程池。
- **修法（只动 `cps/tornado_wsgi.py` 一处）**：覆写 `handle_request`，按响应头 `Content-Type` 分流 —— ① `text/event-stream` 走流式：丢弃 `Content-Length`（上游给了也丢，否则浏览器按定长读完即关）、逐 chunk `write` 并在返回的 Future 上 await（等价 flush）、阻塞读放 16 worker 的专用 `ThreadPoolExecutor`、断连只停推送不取消上游；② 其余响应保持上游整段缓冲语义，响应形态与改动前逐字节一致。
- **测试**：新增 `tests/test_tornado_wsgi_stream.py` 4 条（真实 socket，按「首帧到达时刻」判定）：eager/lazy 两种 `start_response` 形态的流式断言、非 SSE 仍带 `Content-Length`、SSE 在途时普通请求不被阻塞。**反向变异**：把 `tornado_wsgi.py` 换回旧实现，两条流式用例立刻报红（access log `200 GET / 1511.69ms`）。
- **闸门**：定向 `test_tornado_wsgi_stream.py + test_learning_writing_sse.py + test_learning_proxy.py` **62 passed**；全量 **594 passed / 0 failed / 58 errors**，同环境主检出基线 **590 / 0 / 58**——差值正好是新增 4 条，58 个 error 全是沙箱 pytest 临时目录权限问题（`pytest-of-root` 建不了目录），与本次改动无关。
- **仍未解决（如实）**：magpie 环在 150s 处零 token 挂起（`ms=150013,status=499`），批改本身仍会以 `error` 结束。那是 moon-well 的 LLM 预算/路由问题，本仓不越界改；修完流式后，用户至少能逐秒看到进度、并在 150s 时收到明确错误而不是干等。
- **台账**：分支 `fix/r204-sse-stream`，worktree `../magicbook-r204-sse-stream` 留待验收后按闸门删除。
