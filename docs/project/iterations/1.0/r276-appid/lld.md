# R276 · 小程序切正式 AppID

## 1. 起因

开发者工具点「预览 / 真机调试」弹「测试号 AppId 无法使用当前功能，请填写正式的 AppId」。
测试号除了不能真机调试，还有一个更隐蔽的后果：**openid 与正式号不同域**，
换号后所有微信绑定都「查无此人」。

正式号：`wx7b31b435be6beae3`（替换过渡期测试号 `wxd511f98508dc9cee`）。

## 2. 改动

| 文件 | 改动 |
|---|---|
| `miniprogram/project.config.json` | `appid` → `wx7b31b435be6beae3` |
| `tests/test_r276_appid.py`（新增） | 2 例：必须是正式号（且不是退役测试号 / touristappid）、格式 `wx` + 16 位十六进制 |
| `docs/product/readme/miniprogram.md` | 新增「工程信息」一节：AppID、后端/网页版地址、导入目录，以及合法域名与 openid 都按 AppID 存的两个坑 |

后端默认值同步改动在 moon-well R242（`app.wx.appid`），两边必须同值。

## 3. 为什么这里只锁「本仓这一侧」

理想情况是「小程序 appid == 后端默认 appid」由一条测试守住。但两个仓在 CI 里是分开检出的，
跨仓断言要么因路径不存在而跳过（假绿），要么在只检出 magicbook 时必然失败（假红）。
所以拆成两侧各锁自己：这里锁正式号字面量与格式，moon-well 的 `WechatAppIdConfigTest`
锁它自己的默认值。配对关系写在两边的注释与手册里，靠评审保证。

## 4. 换号带来的两个真实后果（写进手册）

1. **request 合法域名按 AppID 存**：新号要重新加 `https://moon-well.haoshenqi.top`，
   旧号的配置不会继承；否则真机报「不在合法域名列表」。
2. **openid 按 AppID 分**：同一微信在新号下是新 openid，旧绑定永远匹配不到。
   第一次登录会落到一个新账号，需用「我已有账号，用邮箱登录」认领回原账号
   （归并时空壳账号被删、目标账号的旧绑定被替换，属自我清理）。

## 5. 验证

- `tests/test_r276_appid.py` + 既有 `test_r271_miniprogram.py` → **8 passed**。
- 后端侧：线上 `/auth/wx/login` 传假 code 返回微信 `40029 invalid code`（凭证有效、只是 code 假），
  说明服务端已在用新 appid + 新 secret；未经重启（Nacos 热更新）。
- **本机无开发者工具**：真机预览、域名白名单、登录全流程仍需你在开发者工具/真机确认。
