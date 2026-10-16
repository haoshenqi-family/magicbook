# credit 模块（积分与订阅）· 用户手册

## 能做什么

- **积分账户**：查看余额、累计发放/消耗；AI 功能按 token 用量扣积分（1 千 token = 1 积分）。
- **积分明细**：获取与消耗统一列表（充值/赠送/AI 功能名/模型/日期筛选），汇总占比一目了然。
- **积分充值**：支付宝当面付扫码充值（档位可选），下单→扫码→轮询自动开通。
- **订阅**：查看当前订阅与有效期（TeslaMate 托管等订阅能力的基础）。
- **成就**：读书/学单词/打卡三维成就徽章，查看进度、解锁、领取积分奖励。
- **管理员调整**：管理员账号可见积分调整面板（正负均可，需填原因，落流水）。

## 谁在用

站内个人页/积分页；消耗积分的 AI 功能（翻译、详解、伴读等）。

## 深入阅读

- L2 接口说明：暂无（本模块为 moon-well credit/saas/achievement 的薄代理层）
- 历史设计（`docs/project/_legacy/feat/`）：[订阅与充值页](../../project/_legacy/feat/subscription-page/design/lld.md)
- 后端契约权威：moon-well `docs/credit/hld/hld.md`、`docs/saas/hld/hld.md`、`docs/achievement/hld/hld.md`
