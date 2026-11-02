# response 归档：R158（2026-10-11）

> 从 response.md 原样搬移（2026-10-13 R168 写入触发窗口检查：写入后窗口达 11 节）。
> 只搬移原文，未总结、未改写、未改编号。
> 注：文中提到的 `test_speaking_writing_static.py` 已于 R166 拆分时被
> `tests/test_learning_pages_static.py` 取代（双锁按「模块 ↔ 它自己的模板」逐页参数化），
> 归档按「历史只标注不重写」保留原貌。

## 2026-10-11（R158：麦克风转写卡死修复）

### R158（「转写中…」永远不结束：els 注册表漏项 + 同步 TypeError 防御）

- **根因定位**（ES app-log-magicbook + docker logs + 代码比对）：停止分支 `statusNode.textContent = ''` 对未注册的 `els['sw-s-audio-status']`（undefined）赋值 → 同步 TypeError 在 fetch 之前炸掉 → 无 alert、按钮禁用、标签停在「转写中…」——且服务端零日志（请求根本没发出）。只影响口语面板（复述的 sw-r-metrics 已注册）。注册表漏项是 R155 建表时只列了麦克风按钮、R156 改 statusNode 引用时未同步注册表所致。
- **修复**：①注册表补 `'sw-s-audio-status'`；②停止分支同步段包 try/catch——任何异常都复原按钮 + 提示，永不卡「转写中…」；③新静态测试 `test_speaking_writing_static.py` 双锁：JS 引用的每个元素必已注册、注册表每个 id 必在模板（此类错误 pytest 页面断言抓不到）。
- **顺带排查结论**（另两条独立线）：①moon-well 直连实测 SiliconFlow 引擎链路 OK（key 200、热重绑 provider=siliconflow 生效），但 RestTemplate 文件 part 默认 octet-stream 会被 SiliconFlow 500 [no body]（audio/wav 同请求 200 实测）——已修（moon-well R160：文件 part 按扩展名给标准 audio/* MIME）；②**Nacos 里的 siliconflow api-key 现在返回 401 Token is invalid**（14:05 实测 200 → 14:2x 失效）——用户需在 SiliconFlow 控制台取当前 key 重新填入 Nacos。
- **测试**：静态完整性 2 例 + 代理 40 例 = 42 passed。
- **总结**：requests.md 占号 R158；本条为回应；冲突记录：无。归档：窗口未超。
