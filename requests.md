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

## 2026-08-19

4. magicbook.haoyuhang.top 返回 500：重启服务后再检查。

## 2026-08-20

5. grafana.haoshenqi.top 也返回 500：确认还有其他问题。

## 2026-08-21

6. OIDC 登录的 redirect_uri 仍是旧域名 hyh.haoshenqi.top，需改为新域名 magicbook.haoyuhang.top。
7. 重启服务。
8. 总结本次会话内容，生成一份 OIDC login 的说明文档。

7. 修改划词翻译接口设计：payload 太大，改为只发送这一页的文本，其他逻辑（分词/查词/归档）由 moon-well 完成。

10. 总结划词翻译的功能要求，更新到 reading-vocabulary.md。

## 2026-08-29

11. 拉取代码，并重新部署服务。
12. 将 master 与 develop 两个分支合并，推送到 develop；之后统一在 develop 分支开发。
13. 合并且部署时确认：library 下的书籍是否不应纳入 git 管理。
14. 合并中采用 master 分支的鉴权方式（moon-well JWT），抛弃 develop 分支的（user_key / X-Magicbook-Token）。
15. 重启后图书全部消失 —— 排查并恢复图书。附带：master 分支曾跟踪 library/metadata.db，需移除跟踪防复发。
16. reading-vocabulary 401 排查：定位为 moon-well CI 构建失败（阿里云 Maven 502）导致新版镜像未部署、两侧鉴权方案不匹配。
17. 重跑失败的 CI；并修复排查中发现的隐患——moon-well access token 7 天过期后无刷新逻辑，阅读词汇功能会周期性 401。
18. 整理 Harry Potter 系列：为什么显示 "cover not available"？封面能否从互联网获取并补充必要的 metadata。
19. 把哈利波特系列放入书架 https://magicbook.haoyuhang.top/shelf/2。
20. 哈利波特系列无法在线阅读，是否因为格式是 mobi？
21. reading-vocabulary 仍 401（moon-well 在飞牛 192.168.31.9，magicbook 在 ubuntu 192.168.31.11）：排查并部署修复（HS256 验签 bug）。
22. reading-vocabulary 接口通了，但没有查询单词本——返回所有单词而非用户不认识的词（参考 FamiliarityLevelEnum）。先做设计写文档，再把 reading-vocabulary 接口合并到 /vocabulary。
23. 部署 reading-vocabulary 新判定后接口 503：排查并修复（moon-well 内网请求被环境代理劫持）。
