# requests 归档（R01–R129）

> 2026-10-08 整理归档：自 requests.md 原样搬移的已确认完成/过时条目。只搬移原文，不改写、不改编号；查历史回应按编号到 response-archive/ 对应文件检索。

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

48. 部署后整本翻译仍不对：HP2 只提交了 109 个段落（上次 128，每次数字都不一样）。排查修复。

49. 彻底解决整本翻译问题：修完代码推送，等 CI 构建重新部署后以哈利波特 1 为例调用 API 翻译整本书，直到正确的提交了全部任务。

## 2026-09-18
50. 整本翻译功能前端拆分后，后端完全没有收到 `/ajax/reading-translate-book` 的请求。检查该接口的完整逻辑并说明，先不做 debug、不修改代码。

51. 生产 magicbook 报错：`Exception in thread whole-book-publish-xxx ... service.py:141 session = ub.session() TypeError: 'Session' object is not callable`。修复整本翻译发布线程崩溃。

52. 部署修复后点击整本翻译，docker logs 里没有任何日志。排查并让整本翻译链路可观测。

53. 把 moon-well 和 magicbook 的日志接入 ES，索引名 app-log-{module}。

53. status 返回 job 57b763d：failedCount=4477=totalCount、pendingCount=0、publishedCount=0、PARTIAL_FAILED——发布线程跑完全程但每段都失败。修复。

## 2026-09-19
54. magicbook 的单词发音很奇怪，是有道 API 的发音吗？（只排查发音来源并说明，不修改代码）

55. 把单词发音改为免费的单词发音 API（R54 结论：现状是浏览器合成音）。

56. 翻译显示时长改为按段落词数动态调整：功能描述改为「每 100 词显示的时间」（默认仍为 5），词数以原文（段落/划中选区）为基数，中文按字、英文按词计；0 仍表示不自动消失。

57. 选中后复制内容到 AI 伴读文本框太麻烦：添加选中后右键的快捷功能，直接把选中文本复制到 AI 对话框，默认不发送，可以再追加自己的提示词。

58. 参考翻译功能，添加 AI 批注功能：选择一个批注角色（首批固定两个：背景讲解、典故讲解），AI 扮演该角色对段落添加批注；文本翻译、语音合成也统一归为伴读 AI 角色。先只做设计（moon-well 侧为主，设计文档见 moon-well `docs/feat/reading-companion/design/`）。

## 2026-09-20
59. 在 magicbook 里新增订阅充值页面：展示可选套餐、当前订阅状态；购买后调 moon-well 支付宝当面付生成二维码收款，扫码支付后自动开通订阅（后端 moon-well 已于 R39 就绪，本任务为其加前端入口）。

59. response.md 越来越大是否影响 AI 使用？（结论：影响）三个项目统一「对话记录归档」：response.md 仅保留最近 10 个 request 的回应，每满 10 个将最早一批原样归档到 response-archive/，并同步更新 AGENTS.md 说明。

60. 在 magicbook 里新增订阅充值页面：展示可选套餐、当前订阅状态；购买后调 moon-well 支付宝当面付生成二维码收款，扫码支付后自动开通订阅（后端 moon-well 已于 R39 就绪，本任务为其加前端入口）。

60. 多任务并行时 request 编号经常冲突。约定改为：agent 接到任务立即在 requests.md 占号追加，任务完成后再写 response.md；编号只追加不回改，撞号续编空号。同步到三个项目 AGENTS.md。

61. 存量 bug（未修，建议另行安排）：achievements.js 的成就领取是原生 fetch 且没带 X-CSRFToken，在 CSRFProtect 全局启用下成就领取可能一直 400。确认这个 bug，然后修复。

62. 订阅页改造：暂时隐藏按月订阅套餐，仅支持充值积分（99元2000分 / 10元100分 / 0.01元1分测试档仅管理员可见，后续删除）；充值成功即刻发放（moon-well 侧 R47 已就绪）。

63. 把 magicbook 的使用指南写成一本书（电子书），导入 Calibre 书库，让学完这本书的人可以立刻获得一项成就。
   （R63 补充说明：EPUB 已导入 fnOS 生产书库 id=89，含封面与元数据；另在 AutoClaw 工作区生成网页预览版。）

64. 积分页增加「消耗明细」：余额面板下方新增明细区（汇总 + 分页列表），数据来自 moon-well 新增的 /credit/consume/page 与 /credit/consume/summary（moon-well 侧 R48），magicbook 新增代理 /ajax/credit/consume-page 与 /ajax/credit/consume-summary。

64. Bug 反馈：读完《魔法书使用指南》（Calibre 书库 book 89）没有获得成就"开卷有益"。排查 toggleread→moon-well 成就链路，确认缺口并补偿。

## 2026-09-21
65. 实施两项：① 打开 moon-well INTERNAL_TRUST_ENABLED（内网信任头）；② toggleread 桥接 moon-well（读完 Calibre 书触发成就事件）。

66. 积分消耗明细反馈（截图）：列表去掉 token 列；获取（充值/赠送）也要展示；分页没生效要修；Feature 列为空要回溯；获取/消耗原因要写清楚。数据源 moon-well R49（明细扩展为全流水 + 原因字段）。

66. 《魔法书使用指南》作者"Magicbook 家族团队"太奇怪：此类自著书籍的作者署名统一改为【好神奇】（Calibre 书库、EPUB 元数据、书内署名、moon-well 侧书架同步）。

67. 明细 reason 不再显示 token 消耗数；汇总 Total Tokens 指标不展示（后台照常记录）。

68. 消耗行 reason 只保留功能名；充值行加「更多」查看充值详情（订单号/账单号等，moon-well R51 落库 detail）。

69. 问明 Feature/Model 列含义（为何为空）；Model 只记录不展示——明细表去掉 Model 列与模型筛选。

70. magicbook 与 moon-well 已同机部署在 fnOS（192.168.31.9）：把两个项目的日志接入 ES 落地到生产（R53 的执行收尾），并更新文档说明部署位置变更。

71. 运维统一运维 3 个项目：日志查询文档收敛到仓库根目录，新增 OPS.md 运维手册；顺带修复 AGENTS.md 中不可直接执行的示例命令占位。

72. 评估并实施系统 trace-id：请求级 trace-id 贯穿 magicbook→moon-well 并进 ES 日志，支持全链路排查；顺带把 moon-well 的 ES RestClient DEBUG 日志降为 INFO。

70. 用户不在内网：积分页给管理员加积分调整入口（moon-well R54 提供接口）。

71. 积分页板块排序：充值放到第二块（Credits 下），明细区挪到最后。

73. 日志级别独立成字段：filebeat script processor 从日志行解析级别写入 log.level（keyword），Kibana 可直接过滤聚合；ES 索引模板补映射。

74. Bark 通知更换：build-and-push.yml 的通知地址从 api.day.app 改为自建 https://bark-server.haoshenqi.top，key 同步更换。

## 2026-09-25
75. 整本翻译仍报 `can't subtract offset-naive and offset-aware datetimes`，需要定位修复。

76. 一键登记全部英文书的整本翻译任务队列（只入队不发布）；逐本激活时才发布执行（缓存回收+只发缺失段）。

77. 不要分开登记和激活——一键翻译全部英文书：登记即执行。

## 2026-09-26
78. 从架构设计层面评价 haoshenqi-family 三个系统（app-manager / moon-well / magicbook；跨项目家族级评审，只读分析，不改代码）。

79. 执行架构评审修复（跨仓库，涉及本仓库仅文档间接关联）：修复3/4/5a/5b 与数据库关系整理；修复1/2 本轮明确不做。

78. 一键翻译全部英文书进度停滞：44 并发发布线程锁死 SQLite（39,645 段滞留 PENDING），并发收敛 + 锁重试 + 进度接缓存懒回收。
修复过程中追加：启动恢复闭包 NameError（_moonwell_proxy 未定义）致恢复批次 27,428 段误标 FAILED；连同 FAILED 重发机制一并处理。

## 2026-09-27
80. 《书id=89》（/read/89）这本书改用英文写：同其他英文书一样纳入整本翻译并缓存。

81. 检查 llm task list，重新激活失败的任务，完成所有的翻译（跨 moon-well + magicbook 生产运维）。

## 2026-09-28
82. https://magicbook.haoyuhang.top/ajax/reading-translate-batch 500 了，排查一下原因。

83. 解释 magicbook reading-translate 接口的逻辑（只读问答，不改代码）。

84. 检查日志：sidebars 这个词查询了多次，每次都很慢，为什么？具体是词典还是 llm？是否有缓存？（生产日志/数据取证，不改代码）

85. 词典 miss 后词形还原重查一次，怎么还原？（方案设计问答）

86. 划词结果加缓存，词典 miss 后先尝试还原，两个一起做掉。（moon-well 编码实现，含测试）

87. 排查 https://magicbook.haoyuhang.top/ 突然访问不了（线上故障排查，TCP 通但应用不响应）。

88. magicbook 仅谷歌相关请求走内网代理 192.168.31.11:12811，其余请求保持直连（编码实现，含测试；顺带堵住元数据外呼无 timeout 的假死隐患）。

## 2026-09-29
89. 检查 llm task list 为什么现在队列没有任务了，但是明显所有的书没有完成翻译（生产诊断，只读取证）。

90. 清理 llm task list 里的僵尸任务（4,902 条 FAILED/ACCEPTED），并补齐 7 条真实缺失的段落翻译（生产运维，含数据清理）。

90. 把 magicbook 的伴读功能做成轻量化 AI agent（有自我分析、工具使用能力，非一次性对话框；不要 opencode 那么重）——设计方向咨询，只读分析不改代码。

91. 追问 R90：agent 放 moon-well、magicbook 只做前端是否可行（含工具面/鉴权/迁移影响评估）——设计咨询，只读不改代码。

92. 追问 R91：①书内检索确认走前端注入上下文；②确认 magicbook 数据库迁移边界——calibre 的 metadata.db 不能动，magicbook 增强数据（app.db 增强表 + ai_companion.db）迁 MySQL/后端。设计确认，只读不改代码。

93. 追问 R92：app.db 具体哪部分不迁移、为什么——逐表归类答复（只读分析，不改代码）。

94. 追问 R93：magicbook 的表能否挂载给 moon-well 读取——可行性+架构判断（只读咨询，不改代码）。

95. 设计文档交付：伴读 agent 化 magicbook 侧改造 LLD——薄代理/SSE 转发/前端 drawer 工具芯片/数据迁移边界。仅写文档，不开发。

96. 同源登记（moon-well R71）：AgentTool 设计与用法讲解（含前端工具芯片事件消费侧）。只读问答。

97. 同源登记（moon-well R72）：SSE/线程模型/WebSocket 取舍答疑。只读答疑。

98. 同源登记（moon-well R81）：伴读 agent magicbook 侧开发——/ai/* 薄代理（SSE 流式转发+JWT 注入）、drawer 前端升级（事件分型渲染/工具芯片/bookContext 上行）、记忆面板、学情摘要入口、ai_companion.db 迁移脚本与 cps/ai 退役（旧端点只读保底）。

99. 同源登记（moon-well R88）：伴读 agent 前端「思考中」动效占位——LLM 首 token 前的等待反馈（三点波浪动画），零工具场景长静默不再像「没反应」。仅静态 JS/CSS，不改代理与后端契约。

## 2026-09-30
100. 登录页出现两个「Log in with Authentik」按钮（蓝色大按钮 + 右下青绿色同名链接），保留一个即可。

101. 生产报错诊断：「no translatable paragraphs found」，https://magicbook.haoyuhang.top/book/91 整本翻译无法启动——定位原因（只读诊断）。

102. 设置页改版：magicbook 扩展设置（非 calibre-web 部分）平铺放不下，改为下拉框跳转对应设置分区；页面支持中英双语，默认中文。

103. 把 Authentik 邀请制注册链接（https://authentik.haoshenqi.top/if/flow/invitation-enrollment/?itoken=5566492c-5d73-49dd-abe0-8dc9d48c14d8）放到 magicbook 首页，跟登录入口放在一起。

104. 为书 #89《Magicbook User Guide》生成哈利波特风格封面并替换线上封面（已完成：ImageGen 生成 + 编辑元数据页上传，/cover/89 已生效）。

105. 咨询：这本书是指南、后续可能要改部分内容，应该走什么流程（已答复：下载线上 EPUB→解包改 xhtml→重打包→上传格式替换→重新触发整本翻译）。

106. 设计咨询：书原文放 Halo blog（note.haoshenqi.top）用 Markdown 写，点「发布」自动更新到 magicbook——评估连接器可行性与方案（只读咨询，不改代码）。

107. 采纳 R106 的 A 方案（magicbook 新增内部导入 API），编写 Halo→magicbook 书籍连接器 LLD 设计文档。仅写文档，不开发。

108. 登录页文案：①删掉「注册采用邀请制，请使用管理员发放的邀请链接 / Registration is invite-only...」提示句；②"Sign in with your Authentik account" 简化为 "Sign in"；③"Log in with Authentik" 同理简化。（占号时误写 103，与并行会话冲突，按纪律续编 108）

109. 为 magicbook 做一个前端引导模式（onboarding），引导用户学习使用这个系统。

110. 把工作区并行会话的未提交改动提交并推送：R107 halo-book-connector（内部导入 API + connector 工具）、R109 前端 onboarding 引导（代为验证、提交、部署）。

111. 图书内的导览太丑了——阅读器段（read.html）的 spotlight 视觉需要重做。

112. 语言模块还是有问题。很多没有双语设置，很多直接把双语显示出来了，而不是根据选择的语言切换。

113. 阅读部分的引导模式卡死：阅读器页点左下角「?」没有反应，强制刷新浏览器无效。

114. 输入法回车误提交优化：中文 IME 确认候选词的回车不应触发搜索/表单提交，需加 IME 守卫（header 搜索、高级搜索、元数据检索、AI 聊天、app-manager SearchDialog 等）。

115. 引入《新概念英语》到 magicbook 书库。

116. 在 https://magicbook.haoyuhang.top/reading/settings 引入一个词汇量测试环节，帮助用户更清晰地认识自己的词汇量。

116. ①magicbook 上传链路限制修改为 100MB；②封面先不动；③把新概念英语 mp3 音频下载到 MinIO，并为 magicbook 增加文章（课）级别的音频播放功能。

117. 分析 ES app-log-magicbook 日志级别合理性（与 moon-well ES 日志级别分析为同一任务）：全量 5363 条级别分布与 warn/error 样本聚类，评估是否需要调整日志级别。

118. 评估把 magicbook 非 calibre-web 部分（词汇表、翻译、语音生成等阅读能力）做成 Chrome 插件的可行性：自由翻译任意 web 页面的单词、段落，逻辑与 magicbook 一致（只评估，暂不开发）。

119. 追加评估 R118 Chrome 插件方案中的 AI 伴读聊天（agent 后端化后的对话面板）：移植到任意 web 页面的可行性，重点评估 SSE 流式、页面上下文提取、记忆与工具链在插件形态下的表现（只评估，暂不开发）。

120. 新概念 epub 整章音频：为三本《新概念英语85》epub（#102/#103/#104）在阅读器每章末尾增加整章 mp3 播放功能（复用 nce-audio MinIO 课级音频）。

121. （R116 续）vocab-size-test US1 词形过度归属缺陷返工定夺并执行：选项 A（`-es` 只接 s/x/z/ch/sh/o 词尾）+ 选项 B+（准入只认原形证词 + 哨兵行最短词长 3），彩排库全量重跑 attest→merge→sentences，把新终态数字（秩集换掉 353 词、31,668 行、例句覆盖 95.99%）同步到 `docs/feat/vocab-size-test/ac/vocab-size-test-ac.md` A 段。

122. 排查 `https://magicbook.haoyuhang.top/ajax/reading-translate`（evidence）为什么查询了 6 秒：定位该请求 6 秒耗时落在哪一环（magicbook → moon-well → LLM/ES），只诊断不改代码。

123. 会话 cookie 浏览器级失效导致「一天就要重新登录」：配置 session.permanent + PERMANENT_SESSION_LIFETIME 使会话跨浏览器重启存活（moon-well token 随 session 一起持久化）。bug 修复。

123. magicbook 阅读器同步上线「单词详解」（对齐 magiclens v0.4.0 / moon-well R100）：划词气泡加「详」按钮 → 新代理路由 /ajax/reading-word-detail 转发 moon-well GET /vocabulary/detail/{word} → 六板块详解面板（基本意思/词源/搭配·用法·习语/变体衍生（不规则高亮）/同反义词/俚语冷知识，变体词显示词目+角标）；含 i18n 词条与单测。

124. （更正：上一条重复的 123「阅读器同步上线单词详解」系本会话所补，编号与并行会话的「会话 cookie 持久化」撞号，按纪律续编为 124）magicbook 阅读器同步上线「单词详解」（对齐 magiclens v0.4.0 / moon-well R100）：划词气泡「详」按钮 → /ajax/reading-word-detail 代理 → 六板块详解面板；含 i18n 词条与单测。

125. 词汇量测试完成后，自动根据测试结果推荐我修改难度等级（词汇测试结果 → 建议难度 + 一键应用）。编码实现。

125. 详解面板不因离开/误点关闭（对齐 magiclens R19）：面板与划词气泡生命周期解耦，请求未完成时保持面板并提示「AI 正常生成中」，完成后自动显示；仅 ✕/Esc 关闭，生成等待期的滚动/翻选/点外不再误关。SSE 暂缓（结构化 JSON 无法优雅增量渲染）。

126. LLM 任务管理员手动执行面板（对齐 moon-well R110 US3）：管理员选择供应商/模型/并发/本批上限，手动执行队列任务并可查进度、停止。

127. 你是一个资深的产品经理，从产品设计的角度评估近期的功能，哪些设计不合理，哪些设计冗余。提出优化建议，并写入文档。重新整理整个组多个项目的设计，检查L1-L3 3级文档。确保文档的正确性。你只修改文档不动代码。（跨项目文档任务：moon-well L1-L3 三级体系 + magiclens/magicbook/app-manager 文档 + 家族级产品评估文档）

128. 更新四个子项目的 AGENTS.md 文档规范：统一 L1-L3 三级体系口径与三级联动纪律（数值同源/L1 负面清单/状态行回填/历史文档标注），不合理之处写修改方案（家族 docs/agents-doc-spec-plan-2026-10-07.md）。只改文档与 AGENTS.md 行为约束，不动代码。

129. 执行 AGENTS.md 文档统一方案的待决策项 P1-A（magicbook L1/L2 骨架）、P1-B（拓扑表指针化）、P2-C（moon-well 事实层+伴读归属）、P2-D（归档规则修订+补账）、P2-E（hugo 降级）、P3-F（家族 Agents.md 锚点节）。只改文档。
