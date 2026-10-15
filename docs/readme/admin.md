# admin 模块（管理）· 用户手册

## 能做什么

- **LLM 任务手动执行**（管理员）：设置页「任务执行」面板——选择供应商、模型、并发数与本批上限，手动消费积压的翻译/详解等队列任务；实时看进度（已认领/成功/失败/执行中），可中途停止，可在队列排空后重放失败任务（不会重复计费）。与「自动执行」模式互斥。
- **用户与权限**：Calibre-Web 自带的用户管理、匿名访问、注册开关等站点管理。
- **登录管理**：Authentik（OIDC）统一登录；邀请制注册入口（邀请链接由管理员轮换下发）。
- **AI 伴读配置**：伴读能力开关（配置收敛在 moon-well 侧 Nacos，本项目只读状态）。

## 谁在用

站点管理员。

## 深入阅读

- L3：[LLM 任务手动执行面板](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/feat/llm-task-run/design/admin-panel.md) · [OIDC 登录工作流](/Users/haoshenqi/codelib/haoshenqi-family/magicbook/docs/kb/instructions/workflows/oidc-login.md)
- 后端契约权威：moon-well `docs/feat/llm/design/llm-task-manual-run.md`（R110）
