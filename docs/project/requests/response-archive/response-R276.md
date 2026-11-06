# response 归档：R276（2026-11-03）

> 从 response.md 原样搬移（2026-11-06 R285 / R286 并行会话 merge 后窗口达 11 节，按「写入即检查」续搬最旧一节）。只搬移原文，未总结、未改写、未改编号。

## R276 · 小程序切正式 AppID wx7b31b435be6beae3（2026-11-03）

**对 R276 的回应**：开发者工具弹「测试号 AppId 无法使用当前功能」。换正式号
`wx7b31b435be6beae3`，后端同步改（moon-well R242）。

- **换号不是改字符串**：`openid` 是 AppID 维度的——同一个微信在新号下是新 openid，
  `app_user_wechat` 里的旧绑定永远匹配不到。所以换号后第一次登录会落到一个新账号，
  得用「我已有账号，用邮箱登录」认领回原账号（归并时空壳账号被删、目标账号旧绑定被替换）。
  这不是我们的 bug，是微信的身份模型，写进了手册与 LLD。
- **合法域名也是按 AppID 存的**：新号要重新在「开发管理 → 开发设置 → 服务器域名」加
  `https://moon-well.haoshenqi.top`，旧号的配置不会继承。这条最容易漏，真机直接报
  「不在合法域名列表」。
- **静态锁只锁本仓这一侧**：理想是「小程序 appid == 后端默认 appid」一条测试守住，
  但两仓在 CI 里分开检出，跨仓断言要么恒跳过（假绿）要么恒失败（假红）。改成两侧各锁自己，
  magicbook 锁正式号字面量与格式，moon-well 的 `WechatAppIdConfigTest` 锁默认值。
- **验证**：`tests/test_r276_appid.py`（2 例）+ R271 既有锁 → **8 passed**。
  后端线上实测：新 appid + 新 secret 后 `/auth/wx/login` 传假 code 得到微信 `40029`
  （说明凭证有效、只是 code 伪造），且未重启（Nacos 热更新）。
  对照实验同时确认：新 appid + 旧 secret → `40125 invalid appsecret`。
- **未真机**：本机没有开发者工具，预览/真机、域名白名单、登录全流程要你在工具里走一遍。

**台账总结**：`requests.md` 第 276 条本处回填；`response.md` 写入前 10 节，本次压回 10 节，
最旧一节 R263（朗读速度选项）原样搬入 `response-archive/response-R263.md` 并登记索引。
