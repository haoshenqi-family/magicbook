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
24. magicbook.haoyuhang.top 的 POST /ajax/reading-translate 返回 400 Bad Request（划词翻译失败），排查并修复。
25. 排查所有调用 moon-well 的接口，排查类似的问题（CSRF / 代理 / 鉴权）。
26. 日志出现「The CSRF token has expired.」导致阅读功能 400（长时间保持阅读器页面打开时 CSRF token 过期），排查并修复。
27. 检查本地与远程代码冲突：本地 develop 落后 origin/develop，未提交的 CSRF 修复与远程「段落级翻译」提交都改了 epub.js，先提交本地再 merge 并解决冲突。

## 2026-08-30

28. TTS 应该怎么配置（moonwell 的 tts 配置项、业务空间 base_url 是否需要配置）。
29. magicbook.haoyuhang.top/ajax/reading-tts 返回 500，为什么——排查并修复（最终定位为 moonwell 下载 OSS 签名音频时 RestTemplate 二次编码导致 SignatureDoesNotMatch）。
30. /ajax/reading-tts 接口成功但没有声音播放出来——排查并修复（定位为 CSP 未放行 blob: 媒体，media-src 回退 default-src 拦截 Audio 播放）。

## 2026-08-31

31. 双击单词的划词翻译经常不会自动消失。除了发音功能，增加一个+（标记不认识）一个-（标记已认识这个单词）。增加esc快捷键，可以退出划词翻译，关闭AI弹窗。

## 2026-09-03

32. 更新前端 magicbook，添加阅读器段落批注相关功能。

## 2026-09-08

33. 移除 magicbook 对 Nacos 的依赖。
34. 修复 joserfc 与 cryptography 依赖问题，使服务正常启动。
35. 修复登录后 /ajax/reading-vocabulary 返回 401。

## 2026-09-13

36. 修复 TXT 阅读器对预排版文本（Project Gutenberg 类硬换行 TXT，如 Harper's Young People）的排版问题：硬换行 + 不规则缩进在 pre-wrap 双栏分页下渲染成左右交错的乱版。
37. reading-vocabulary 功能现在是不是被弃用了？排查一下为什么（阅读器里看不到生词标注）。
38. 翻译功能增加一个显示时间的配置，默认 5 秒；超过这个时间后翻译内容自动消失；可以随时在页面上配置修改。
39. 补充 R37：生词标注问题发生在哈利波特 EPUB（book 50，/read/50/epub）上，继续定位。
40. 实测复现：打开 book 50 后无法翻页，DevTools 报 Uncaught IndexSizeError（epub.min.js toRange setStart），定位并修复。
41. R40 修复部署后复测 /ajax/reading-vocabulary 仍偶发 500，继续排查（已部署完成仍复现，响应体 "save reading vocabulary failed"）。

## 2026-09-14

42. 生词显示的两种展示形式（悬停提示 / 点击弹窗）都太长，暂时都注释掉（配合 moon-well analyze 仅返回生词本身）。

## 2026-09-15

43. 用户默认难度级别定为 3（CET4）；新增一个配置页面允许用户自己修改级别，之后的阅读相关配置修改都放到这个页面；不要改动 calibre 原有功能，新建独立页面。

44. AI伴读的提示词中增加一句话「以下是用户暂时还未掌握的词汇{}」，填充 reading-vocabulary 返回的生词。

45. 借鉴 AutoClaw 记忆系统改造 magicbook 记忆：①提取前加信号门控（省 token）②写入前去重/合并（防堆积）③注入按相关性过滤（跨书精准）。


46. magicbook 的整本翻译功能还是不行：排查修复（moon-well 侧配套：任务发布即入队执行 + PENDING 积压恢复 + 模板渲染；本仓库：发布带 promptTemplate、进度 pendingCount、前端进度轮询与提交反馈）。

47. 部署成功后整本翻译还是不对：哈利波特2（book 44）发布批次只有 128 个段落，不可能这么少。排查修复。
