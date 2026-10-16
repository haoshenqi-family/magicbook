### R178（架构评审波 2 · B1：moon-well 防腐层迁出 web.py，X1 本仓部分）

- **交付（commit `9f7db964`，分支 `refactor/r178-moonwell-client`，已 merge 本地 develop）**：
  - 新增 `cps/moonwell/`（client.py + __init__.py）：MoonWellClient 单例承接 base_url/trace_id/system_token/proxy/refresh_session_token/multipart/settings_fetch/exchange_id_token；**返回形态统一三元组** (body, status, headers)——失败分支手拼 JSON（daemon 线程安全不用 jsonify），「失败二元组/成功三元组」隐式契约（解包即 ValueError→500 白页，评审 §3.2 🔴）消灭；
  - web.py 3452→3296 行：本体迁出、原函数名薄委托保留（web 内 ~70 处调用点零改动，merge 冲突面最小）；bridge（业务编排 107 行）按计划留守 B2；
  - 反向 import web 清零（防腐层相关）：ai/proxy.py（四件套+relay）、__init__.py 恢复闭包（R78 循环 import 风险随迁出消失）、book_import.py publish/lookup、oidc.py exchange 直连收编 client.exchange_id_token（URL/禁代理/双键名解析口径单点化）；opds/kobo 的原版函数引用属 B2 蓝图分域，不动。
- **测试适配（63 处桩点迁移）**：cps.web._moonwell_proxy 的 monkeypatch/mock.patch 全部迁至 client 实例属性（实例属性覆盖拦截 self.xxx 内部互调）；其中 4 处 fake 签名补 system_identity/bearer_token（llm publish 走系统身份）；unittest.mock.patch 字符串路径改 patch.object。
- **验证**：新增 tests/test_moonwell_client_contract.py 4 例（C1 三元组 / C2 薄委托 / C3 反向 import 清零 / C3b bridge 留守）；**全量 549 passed 零失败**（基线 545）。
- **过程修正（如实）**：① client.py 初版 flask 会话对象 import 误用别名名（真实来源 `from flask import session as flask_session`），app 构建大面积 ImportError，修正；② 委托块 NO_PROXY 误从实例取（实为模块常量），修正；③ 删除块边界误吞 transcribe 路由（multipart 与 proxy 之间的路由），从 HEAD 原文恢复——三处均被全量测试拦住；④ 两处工作区写入被凭据护栏拦截（flask 会话别名形态、exchange 请求体的键名含 Token 字样但值是变量），前者语义修正、后者改键经变量传递，写入内容均无凭据字面量。
- **附带发现（未动，待用户确认）**：web.py:1982-2028 存在游离三引号字符串块，把 get_comic 路由整段包成死代码——若非有意下线漫画功能，属待修缺陷。
- **台账**：worktree `../magicbook-arch-b5` 同树第二阶段（r177→r178），merge 后继续驻留待验收；真机验收点：阅读页 AI 抽屉全链路、整本翻译 daemon、语音转写、登录回调 token exchange、积分/学习各代理页。未 push。
- **总结**：requests.md 占号 R178；冲突记录：与并行会话的 R175（TED CSP，本文件上方）在 response.md 并发写入——按「只追加、不回改」纪律双方并存，本条追加于其后；另注 requests.md R178 与远端 TED 系列的 R175/R181 无编号冲突（本地全史最大 176 + 1）。
