# companion 模块（AI 伴读）· 用户手册

## 能做什么

- **围绕当前书对话**：阅读页打开 AI 伴读抽屉，就当前书内容提问（书名/章节/当前页文本自动作为上下文）。
- **状态可读（R215）**：点发送即出现「思考中 · N 秒」计时，首个字到达后自动替换；右下角悬浮按钮带头像与「AI 伴读」标签，不再是看不出含义的白圈。
- **工具调用**：AI 可调用查词、翻译等工具，界面以「工具芯片」展示调用过程与结果。
- **跨书记忆**：AI 记住你的偏好与背景（如英语水平），跨书、跨会话复用；会话可改名、可删除。
- **流式回复**：回答逐字输出，生成中显示占位提示。
- **伙伴（buddy）**：伙伴是 AI 阅读按钮上的那张脸——领取、切换只改变外观，**不会改变 AI 作为英语老师的角色**。`/buddy` 管理花名册，个人页 `/me` 只展示当前使用的伙伴并可跳转管理。

## 谁在用

阅读页右侧伴读抽屉与左下角的伙伴按钮；同一能力也以 Chrome 扩展 magiclens 的形态用在任意网页。

## 深入阅读

- L3：[伙伴 IP 风险登记](../companion/features/buddy-ip-risk.md)（内测保留现有角色，正式对外发布前须替换为原创形象）
- 历史设计（`docs/project/_legacy/feat/`）：[伴读 Agent 化 magicbook 侧设计](../../project/_legacy/feat/ai-agent/design/magicbook-side-design.md)
- 后端契约权威：moon-well 伴读 Agent（`/ai/agent/*`，见 moon-well `docs/system/hld/hld.md` 伴读 Agent 节）
