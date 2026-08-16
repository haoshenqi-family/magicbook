# 对话需求记录

> 仅记录每一次对话用户的需求，除此之外不做任何事情。

## 2026-08-14

1. 增加一个 agents.md 说明，明确 requests.md / response.md 的用途与维护规则：
   - requests.md 仅记录每次对话用户的需求，不做其他事。
   - 每次完成后检查需求列表，将功能说明更新到 response.md，包括对每个 request 的回应、对两个文件的总结。
   - 尽量简单。
   - 若 request 存在冲突，也需记录下来。

2. 打通 magicbook 与 moon-well 两个应用的用户体系（目标：SSO + 用户身份映射）：
   - 以 Authentik sub 为跨应用唯一身份标识，替代当前以 magicbook 自增 user.id 作为 moon-well userKey 的脆弱方案。
   - 先验证风险 1（Authentik 同一用户在两 provider 下的 sub 是否一致）；风险 2/3（数据可回溯性、上线窗口）忽略（尚未上线）。
   - 编码实施，注意尽量不影响其他模块。
   - 附带：提供 ES 旧数据迁移脚本、同步文档、修复既有测试编译问题。

## 2026-08-16

3. 检查划词翻译功能。
