# L3 · AI 了解我：用户自我介绍实现说明

> 覆盖 magicbook R260；存储与提示词注入主责 moon-well R234。给修改伴读记忆面板、档案代理或隐私边界的人读。

## 实现方式

- **入口**：`cps/templates/ai_chat_panel.html` 在 `#ai-memory-panel` 顶部新增 `ai-user-profile` 区块，位于“本书学情 / 长期记忆”之前。
- **加载**：打开记忆面板时 `loadMemoryPanel()` 调用 `loadUserProfile()`，请求 `GET /ai/agent/profile`；后端只按当前登录用户返回，面板切到空串时显示未填写。
- **保存**：`cps/static/js/ai_chat.js::saveUserProfile()` 先 trim，空内容要求用户先填写；有内容时 POST `{"selfIntroduction": text}` 到 `/ai/agent/profile/save`，成功后用服务端返回值回填。
- **清空**：用户确认后发送 `{"selfIntroduction": ""}`；成功后清空 textarea 与计数。清空是明确撤回，不做软删除。
- **代理**：`cps/ai/proxy.py` 提供两条薄代理。GET `/ai/agent/profile` 固定转 moon-well POST；保存请求体原样透传，均保持 `_moonwell_proxy` 三元组。
- **渲染安全**：用户文本只用 jQuery `.val()` 读写，不参与 `.html()` 拼接；动态文案通过 `t()` 在调用时翻译。
- **计数与按钮**：`maxlength="2000"`，输入事件更新 `n / 2000`；达到上限高亮；保存/清空期间两按钮同时禁用，结束恢复。
- **视觉与移动端**：桌面使用轻量分区卡；≤600px 时按钮最小高度 44px，textarea 最小 144px，避免移动端触控目标过小。

## 边界条件

- 加载失败显示“介绍加载失败 + 原因”，不清空用户当前输入，也不伪装成未填写。
- 保存/清空失败显示明确错误，按钮恢复可用；用户可重试。
- 清空必须二次确认，文案明确“AI 将不再使用这些背景信息”。
- 档案只存在服务端，不写 localStorage/sessionStorage；退出登录后由后续账号重新加载自己的数据。
- 2000 字符是用户主动编辑上限；服务端仍有 Bean Validation 与业务服务双重校验。
- 档案正文会随每次提问进入模型上下文，界面固定提示不要填写密码、密钥、证件号等敏感信息。
- 本功能与长期记忆视觉分区、数据分区、编辑链路均独立；“清空介绍”不删除长期记忆。
- 本轮不引入结构化档案字段或 AI 摘要；后续若升级，应保留原始介绍并提供“AI 将看到什么”的摘要预览。

## 验证

- `tests/test_ai_agent_proxy.py`：两条代理的路径、payload 与三元组透传。
- `tests/test_ai_user_profile_r260.py`：模板控件、2000 上限、统计、保存/清空请求、`.val()` 渲染、i18n 种子/po 与移动端触控契约。
- `node --check cps/static/js/ai_chat.js`。
- 与 moon-well R234 的书内/网页提示词注入测试联合验收。
