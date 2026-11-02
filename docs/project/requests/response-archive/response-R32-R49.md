# 对话回应记录归档（R32–R49）

> 由 `response.md` 归档产生（2026-09-20）。收录 2026-09-03 ～ 2026-09-17 期间 R32–R49 的回应原文，原样保留、不再修改；查阅历史回应按编号检索本目录，不要读全量 `response.md`。

---

## 2026-09-03（第十一次对话：阅读器段落批注前端接入）

### 对 requests 的回应（R32）

- **代理路由**：magicbook 新增 3 个登录保护的批注代理：创建批注、按段落查询、按书查询；均转发到 moon-well 对应接口，校验段落/内容长度，trim 书名与章节并限制 200 字符。
- **段落批注 UI**：EPUB 每个段落新增 `✎` 按钮；点击后显示段落原文摘要、已有批注、批注输入框和提交操作。批注提交只发送段落与内容，昵称和时间由 moon-well 服务端生成。
- **本书批注面板**：标题栏新增「批」入口，按章节显示本书已批注段落及其批注列表，支持关闭和空态/失败态提示。
- **同文档契约**：前端批注使用与翻译/TTS 相同的 `paragraphSpeechText` 归一化文本，保证批注与翻译、音频落入 moon-well 的同一个 `reading_paragraph_cache` ES 文档。
- **交互与安全**：批注请求显式携带 `X-CSRFToken`；段落弹层、本书面板、划词气泡和 AI 抽屉支持分层 `Esc` 退出；翻页、点击正文和点击外部区域会关闭失效浮层；CSRF 失败沿用自动刷新恢复机制。
- **测试**：新增代理校验/透传/503/CSRF 测试与 epub.js 静态契约测试；阅读测试 **32 passed**，magicbook 全量测试 **167 passed**（3 个既有 SAWarning，无失败）。JS `node --check`、Python `py_compile` 均通过。
- **遗留工作区说明**：本次未修改此前遗留的 `ai_chat.js`、既有阅读文档、既有测试等未提交改动；它们与本次批注功能一并处于当前工作区，但未被撤销或覆盖。

### 总结

- **requests.md**：新增 R32（magicbook 阅读器段落批注）。
- **response.md**：记录批注代理、段落弹层、本书批注面板、同 ES 文档键契约、安全处理与测试结果。

### 冲突记录

- 无。

---

## 2026-09-08

### 对 requests 的回应

- **R33（移除 magicbook 对 Nacos 的依赖）**：已完成。
  - 删除 `nacos-sdk-python` 依赖、`cps/nacos_client.py` 及应用启动时的 Nacos 注册/发现逻辑。
  - 删除 `NACOS_*`、`MOON_WELL_DISCOVERY_SCHEME` 配置项；moon-well 调用统一使用 `MOON_WELL_READING_URL`。
  - 保留现有 moon-well 请求代理、JWT/会话鉴权与内网直连逻辑不变。
  - `py_compile` 与差异检查通过；启动验证继续被当前环境缺失的 `joserfc` 阻断，该问题与 Nacos 移除无关。

- **R34（修复 joserfc 与 cryptography 依赖问题）**：已完成。
  - **根因**：`cps/oidc.py` 无条件导入 `joserfc`（用于 RS256/JWKS 验签），但 `requirements.txt` 和 `pyproject.toml` 均未声明该依赖；当前机器系统 `cryptography==2.8`（`/usr/lib`）覆盖了 `>=39` 的声明，`joserfc` 无法导入。
  - **修复**：补齐 `requirements.txt` 和 `pyproject.toml` 中 `joserfc>=1.0.0,<2.0.0` 声明；本机执行 `pip install --force-reinstall 'cryptography>=39,<48' 'joserfc>=1,<2'`，将 `cryptography` 升至 47.0.0。
  - **验证**：`./restart.sh` 成功启动（PID 2446058，端口 8085）；`test_oidc.py` **6/6 通过**；阅读测试 setup 错误数量从 30 降至 16（joserfc 阻断已消除，剩余为测试夹具环境问题）。

### 总结

- **requests.md**：新增 R33，记录移除 Nacos 依赖的需求。
- **response.md**：记录 R33 的删除范围、替代地址配置与验证结果及环境阻断。

### 冲突记录

- 无。

---

## 2026-09-08（第三次对话）

### 对 requests 的回应

- **R35（修复登录后 /ajax/reading-vocabulary 返回 401）**：已完成。
  - **根因**：moon-well 要求 `Authorization: Bearer <JWT>` 鉴权，但 `oidc.py` callback 中 token 交换已被移除（注释"不再在此交换 moon-well token"），`_moonwell_proxy` 也不携带 `authorization` 头。moon-well 返回 401「未登录」。
  - **修复**：
    - `oidc.py` callback：登录成功后用 Authentik `id_token` 调 moon-well `POST /auth/oidc/exchange` 换取 `access_token` + `refresh_token`，存入 Flask session。
    - `web.py` `_moonwell_proxy`：从 session 读取 token 携带 `Authorization: Bearer` 头；收到 401 时自动调 `/auth/refreshToken` 刷新并重试一次。
  - **验证**：`py_compile` 通过；`test_oidc.py` **6/6 通过**；服务正常启动，`/login` 返回 200。

### 总结

- **requests.md**：新增 R35，记录 reading-vocabulary 401 问题。
- **response.md**：记录根因（token 交换被移除 + proxy 无 Bearer 头）与修复方案。

### 冲突记录

- 无。

## 2026-09-13

### R36：TXT 阅读器预排版文本乱版修复

- **原因**：`readtxt.html` + `txt_reader.js` + `text.css` 的 TXT 阅读器用 `<pre>`（pre-wrap）+ 双栏（column-count:2）+ 水平翻页渲染。Project Gutenberg 类 TXT 保留纸质书排版：行尾硬换行、行首不规则缩进（起句 4 空格、续行 2 空格）。这些硬换行被原样保留，被双栏分页任意切割，一行起句与续行落入不同栏/页，形成交错乱版（用户截图中 Harper's Young People, January 27, 1880 即此问题）。
- **方案**：在 `cps/static/js/reading/txt_reader.js` 加载文本后增加预排版检测与重排：
  - `isHardWrappedText`：非空行 ≥20 且长行（>72 字符）占比 <30% 判定为预排版（流式 TXT/TED 字幕不受影响）；
  - `reflowHardWrappedText`：空行为段落边界，段内硬换行合并为流式段落——行尾连字符按断词直接拼接（保留连字符，tea- + kettle → tea-kettle），CJK 字符间不插空格，其余以单空格连接；标题行因空行分隔保留为独立段。
  - 已知取舍：诗行会被并入段落（换取整体可读性）。
- **验证**：无 JS 测试基建，用 node 直接加载修改后文件中的真实函数验证：PG #28318 全文判定为预排版并重排成功（诗节成段、标题独立、断词正确）；30 段流式 TED 字幕样本判定为非预排版、原样保留；中文句合并不插空格。部署后建议用截图书目视复核。
- **部署**：develop 分支，需在 Ubuntu（192.168.31.11）重新构建/重启 magicbook 生效（静态资源无缓存版本号，浏览器需强刷）。

### R37：reading-vocabulary「疑似弃用」排查（未改动代码）

- **结论：功能没有被弃用，两侧均在正常服役。**
  - moon-well：`ReadingVocabularyController`（`/vocabulary/reading/analyze|translate|translate-batch`）与 `ReadingVocabularyService` 无任何 `@Deprecated`/开关/下线逻辑；2026-09-12 `f73fc6f` 还把其 ES 索引收编进 `EsIndexEnum.READING_VOCABULARY`（`reading_vocabulary`）统一管理。
  - magicbook：EPUB 阅读器（read.html + epub.js，1483 行）生词标注/划词翻译/标记认识全在，开关 `readingVocabularyEnabled = current_user.is_authenticated`；9/8 刚修复 401（21c93189）。
- **「被弃用」错觉的真实原因（按可能性排序）**：
  1. **TXT 阅读器从未实现过该功能**：`readtxt.html` + `txt_reader.js`（仅 137 行，只有翻页与 R36 排版重排）没有任何 `readingVocabularyUrl`/标注/划词/TTS/批注代码。最近阅读的书恰好全是 TXT（TED 导入书、PG TXT），在 TXT 书里自然看不到生词波浪线——不是功能被弃用，而是功能只存在于 EPUB 阅读器。
  2. **旧接口路径确实删除过**：2026-08-29 `aca377e` 将 `/reading-vocabulary/**` 并入 `/vocabulary/reading/**`（原路径已删除），直接调旧路径会 404，易误判为弃用。
- **验证**：grep 全仓无弃用标记；git log 两项目均无下线提交；requests/response 记录无弃用计划；`web.py:1963` 确认 TXT 书渲染 `readtxt.html`。
- **如需 TXT 阅读器也支持生词标注**：需把 epub.js 的词汇链路（取页文本、CSRF、标注、缓存签名）移植到 txt_reader.js，属新功能开发，另行安排。

### 总结

R36 为纯前端渲染修复，不涉及数据与接口变更；TED 书（moon-well 同步的流式字幕 TXT）不受影响。R37 为排查类任务，未改动任何代码。

### R38：翻译内容显示时长配置（默认 5 秒自动消失，页面可改）

- **实现**（纯前端，EPUB 阅读器 `cps/static/js/reading/epub.js` + `cps/templates/read.html`）：
  - 配置存 localStorage `calibre.reader.translationDisplaySeconds`，默认 5 秒，0 = 一直显示（非法/负数回退 5）；入口在阅读器设置弹窗（齿轮）朗读引擎下方，数字输入框，改动即时保存并生效。
  - 生效范围覆盖全部翻译展示：段落译文块（单段「译」按钮、整页沉浸翻译、翻页缓存回填，统一在 `insertTranslation` 入口调度）与划词翻译气泡（译文渲染完成后计时）。到点移除译文并复位段落按钮，可再点「译」重出（命中缓存即时显示）。
  - 细节：loading（翻译中…）/error（失败重试）中间态不计时；划词气泡内点击（🔊 发音、＋/－ 标记）以捕获阶段监听重置计时，避免操作中途气泡消失；配置修改后已显示的译文立即按新时长重排计时。
- **验证**：`node --check` 语法通过；全量 pytest **160 passed**；node 模拟受控时钟 15 用例全过（默认 5s 到点消失、0 不隐藏、改配置重排、手动取消 no-op、loading/error 不计时、非法值回退）；临时拉起服务确认可正常启动，且 `read.html` 经 Jinja 渲染含新输入项（默认值 5）。
- **部署**：develop 分支工作区改动；静态资源无版本号，部署后需强刷浏览器。

### 总结（R38 后更新）

- **requests.md**：追加 R38（翻译显示时长配置）。
- **response.md**：记录 R38 的实现范围（段落译文块 + 划词气泡）、配置入口（设置弹窗，localStorage 持久化，0 = 不自动消失）与验证结果。
- **冲突记录**：无；R31 曾要求划词气泡可通过 ESC/点击关闭——本次自动隐藏与该需求方向一致（多一种消失途径），配置为 0 时保留原有纯手动关闭行为。

### R39：哈利波特 EPUB（book 50）生词标注失效定位（R37 补充，未改动代码）

- **结论：功能链路健康，9/9 那次 HP 阅读会话的生词上报在目录页之后静默中断，且仅中断在那一次会话。**
  - book 50（Sorcerer's Stone）在 ES `reading_vocabulary` 只有 9/9 07:59:02-03 的 2 条 `"chapter"` 事件——该词只出现在目录页（"CHAPTER ONE…"），说明 analyze 当时只处理了目录页。
  - 同一会话 45 秒后（07:59:48）整页翻译缓存仍在正常写入（`magicbook-read-paragraph`，同一鉴权/同一代理），排除 401/CSRF/代理问题。
  - **全链路今天验证正常**：9/13 12:36 读 book 5 时 analyze 成功调用 10 次、写事件 12 条；用户 hard_level=6、单词本 8499 词（8403 个 familiarity=0），任何 HP 正文页都必然命中生词——9/9 正文页从未发出过 analyze 请求（moon-well 无对应 requestURI 记录）。
  - **书本身无问题**：把 book 50 EPUB 拉到本地，用线上同款 `epub.min.js` 复现「目录页→盲文说明页→第一章正文」逐页取文，全部成功（每页 1600~2200 字符）；`index_split_*` 分章结构与 CSS 均无异常。
  - 9/9 中断的直接现场已不可追溯（moon-well 容器 9/13 重启，日志丢失；magicbook 访问日志随容器重建丢失）。关联背景：`reading_vocabulary` 索引 9/8 22:01 被备份为 `reading_vocabulary_bak_20260908` 后删除，9/9 07:59:02 由该书的第一条请求隐式重建——当时正处于索引迁移窗口。
  - **建议**：环境恢复后在 book 50 上翻一页正文即可验证恢复；若再现中断，浏览器 DevTools Network 看 `/ajax/reading-vocabulary` 是否发出及响应码（最可能：请求未发出=前端取文/翻页事件问题，或 401/503=会话令牌）。
- **顺带发现（建议处理）**：
  1. 公网 `moonwell.haoshenqi.top` 的 Traefik 路由（Server 2 `/app/app-manager/traefik-dynamic/moonwell.yml`）指向 Ubuntu .11 上 8/12 启动的旧 moon-well 裸进程（旧 API 路径、`/auth/refreshToken` 抛 `NoClassDefFoundError`），应改指 fnos:8082 或删除。
  2. book 50 整书翻译任务（9/8 13:22）`PARTIAL_FAILED`：224 段仅完成 1 段。
  3. magicbook `bookmark` 表为空：阅读器书签从未落库，位置恢复仅靠浏览器 localStorage。
- **环境突发（排查尾声，与本问题无关）**：9/13 13:15 前后 PVE 宿主机（192.168.31.5）连同其上的 fnos（.9，magicbook/moon-well 所在）与群晖（.10）全部失联，公网 `magicbook.haoyuhang.top`/`moonwell.haoshenqi.top` 因此整体不可用；13:12 前 SSH/服务均正常。待宿主机恢复后再做实时复现验证。

### 总结（R39 后更新）

- **requests.md**：追加 R39（R37 补充：问题发生在 HP book 50 EPUB）。
- **response.md**：记录 book 50 的定位结论（9/9 单次会话中断、链路今天验证健康、书无问题）、三个顺带发现与 PVE 宿主机宕机事件。未改动任何代码。
- **冲突记录**：R37 初判主因为「TXT 阅读器无此功能」，R39 依据用户补充（HP 为 EPUB）修正为「9/9 那次会话静默中断」；TXT 阅读器无词汇功能的事实不变，作为背景保留。

### R40：哈利波特 EPUB 打开即卡死无法翻页（IndexSizeError 毒化 epub.js 显示队列）修复

- **现象（用户实测复现）**：打开 book 50 后无法翻页，DevTools 报 `Uncaught IndexSizeError: Failed to execute 'setStart' on 'Range': There is no child at offset 309`（epub.min.js 内部 `display → locationOf → toRange` 链）。
- **根因**：阅读器位置恢复逻辑（`cps/static/js/reading/epub.js`）在启动时 `rendition.display(localStorage 保存的 CFI)`。书内容更新（Calibre 重新转换/元数据刷新等）后旧 CFI 的字符 offset 越界，epub.js 内部 `toRange` 抛 IndexSizeError。该异常：① 同步 try/catch 接不住（异步 promise 链）；② rejection 被 epub.js 内部链吞掉，`display()` 返回的 promise 永远 pending、调用方 `.catch` 也不会触发；③ 显示队列（promise 链式 enqueue）被 rejection 毒死——此后所有 `display/next/prev` 永不执行，整本书无法翻页。**生词标注失效（R37/R39）正是此卡死的伴生症状**：翻页不动 → `relocated` 不触发 → `inspectVocabulary` 不跑 → 无 analyze 请求；而划词/段落翻译作用于当前可见页，不受队列影响，仍能工作（与 9/9 现场完全吻合）。
- **本地复现与验证**（/tmp harness + 线上同款 epub.min.js + book50.epub）：现状写法 display(坏CFI) 后 next 两次均 4s 无响应（队列死亡，100% 复现）；`.catch` 与 catch 内的恢复调用均无法挽救（promise 永远 pending）——修复必须让坏 CFI 进不了队列。
- **修复**（纯 `cps/static/js/reading/epub.js`，~100 行）：
  1. **两级位置恢复**：先经 `book.spine.get(savedCfi)` 得到 spine 序号 `display(index)` 安全落位（整数路径不走 CFI Range，无此雷，新老位置缓存统一支持）；随后用 `cfiSafeForCurrentDocument` 轻量校验（解析 CFI 末段 id 断言 + 字符 offset，在当前渲染文档累计该元素文本总长，offset 超界判不安全），通过才 `display(cfi)` 章内精调，不通过丢弃保存的位置并停留在章开头。
  2. **保存端**：位置缓存（localStorage `calibre.reader.position.<bookKey>`）增加 `index`（spine 序号）字段。
  3. **全局兜底**：window error 监听捕获 epub.min.js 的 IndexSizeError（覆盖其他潜在 display(CFI) 调用点，如未来功能），清掉坏位置后刷新重建；sessionStorage 标记防「保存→崩→刷」死循环，阅读器成功初始化后重置标记。
- **验证**：`node --check` 通过；本地 harness 用线上同款 epub.min.js + book50.epub 实测：坏 CFI 判定 `safe=false`、好 CFI `safe=true`；两级恢复落位正确章（index=3, index_split_002.html）；坏 CFI 被拦截未进队列；连续两次 next 均 resolve 且页面切换（对照现状代码为双卡死）。校验与兜底均以「放行+兜底」为缺省，不误伤正常书。
- **部署**：develop 分支提交推送后由 GitHub Actions 构建镜像并经 app-manager 自动更新部署；静态资源无版本号，浏览器需强刷。存量受影响用户（localStorage 中的坏 CFI）部署后首次打开会自动走兜底刷新或两级恢复，无需手动清缓存。

### 总结（R40 后更新）

- **requests.md**：追加 R40（打开 book 50 无法翻页的 IndexSizeError）。
- **response.md**：记录根因（旧 CFI 越界 → epub.js 显示队列毒化 → 翻页卡死 → 生词标注伴生失效）、三级修复（两级恢复/位置缓存加 index/全局兜底）与本地实测结果。
- **冲突记录**：无；R39 中「9/9 中断现场不可追溯」的遗留疑问由 R40 的机制解释补齐。

### R41：复测期偶发 500 定位——moon-well 被并行操作反复重建，窗口期请求必然失败（未改动代码）

- **R40 修复部署验证（成功）**：20:34 CI 构建（1m11s）→ app-manager 自动更新 fnos magicbook 容器 → 线上 epub.js 已含修复。用户强刷后翻页恢复正常，多次复测的生词事件在 ES `reading_vocabulary` 全部落库：20:36 目录页 `chapter`×3、20:49 正文 `half`/`edge`、23:13 正文 `edge`/`open`/`back`/`wide`、23:14 正文 `tiny`/`straight`；21:17 用户在 book 16 上也成功标注 19 词。**生词功能修复确认生效。**
- **「仍然 500」的定位**：用户复测期 `/ajax/reading-vocabulary` 偶发 500。排查发现 fnos 的 moon-well 容器在 23:13:49 与 23:15:24 被 docker compose 连续 replace（`com.docker.compose.replace` 事件，working_dir=/host/app/moon-well），同时 `/book/import-ted` 持续有调用——**有并行会话/自动化正在执行 moon-well 部署与 TED 重导入**。重建窗口期（容器停止→启动→Spring 初始化，约 90 秒）所有代理请求失败，表现为 500/503。窗口外的请求全部成功（23:14:38/40 两次 analyze 成功且事件落库）。moon-well 的 GlobalExceptionHandler 不打日志，故失败实例侧无痕迹。
- **当前状态**：moon-well 现实例 healthy，无 token analyze 正确返回 401；功能链路完整可用。若并行侧（TED 导入/部署）仍在进行，建议待其完成后再复测，避免撞上下一次重建窗口。
- **改进建议（另行安排）**：① magicbook `_moonwell_proxy` 对 502/503/504 增加一次短重试（analyze 幂等可安全重试），跨越部署窗口；② moon-well 侧部署如需零中断，走健康检查就绪后再切流量；③ moon-well `GlobalExceptionHandler` 补异常日志（当前吞异常无痕迹，本次排查显著受阻）；④ `Result.error` 生成的 `success` 字段恒为 true（body `"success":true` 但 code 500），前端无法凭 success 判错，一并修正。

### 总结（R41 后更新）

- **requests.md**：追加 R41（部署后复测仍偶发 500）。
- **response.md**：记录 R40 修复的部署验证结果（ES 多批落库证据）与偶发 500 的根因（moon-well 被并行操作反复重建、窗口期失败），四条改进建议。未改动代码。
- **冲突记录**：无。

### R42：reading-vocabulary 偶发 500 真根因——Nacos 覆盖 ES 为公网环回链路，间歇 IOException（moon-well 侧修复）

- **决定性证据（用户提供 500 响应体）**：`{"message":"save reading vocabulary failed","code":500}`——即 `ReadingVocabularyService.analyze` 中 `client.index()` 抛 IOException 被 `catch (IOException)` 包装的异常。同页其他 analyze 成功、ES 落库正常，故障为间歇性。
- **排查路径**：moon-well 日志成功调用（07:19/07:20/07:32/33 共 8 次全部 201 落库，HP 每页仅 1-2 个超档词，单条写入属正常）与用户稳定 500 矛盾 → `GlobalExceptionHandler` 不打日志吞异常 → 用 magicbook 代理日志改进（R41 建议落地：非 2xx 记录状态码+响应体）拿到响应体 → 定位 ES 写入链路 → **发现容器环境变量（`ELASTICSEARCH_HOST=192.168.31.9` 直连）与运行时行为（`https://es.haoshenqi.top:443`）矛盾** → Nacos 配置中心 `moon-well.yaml`（spring.config.import，优先级高于环境变量）硬编码 `elasticsearch.host: es.haoshenqi.top`。
- **根因**：moon-well 在 fnos 上访问**同机的 ES**，却经 `fnos → Server2 Traefik(443) → Tailscale → fnos:9200` 的公网环回链路（延迟 165ms vs 直连 0.7ms，且受 Traefik keep-alive/Tailscale 抖动影响）。链路间歇失败时：`findPrevious`/`dictionaryEntry` 等查询类调用被 catch 静默（日志中 `nextWord doesn't exists` 频发即征兆），**唯独 index 写入的 IOException 被包装为 500**——表现为「生词标注偶发失败、翻页/翻译正常」。
- **修复**：经 Nacos v3 API 更新 `moon-well.yaml` 的 `elasticsearch` 段为直连（`host: 192.168.31.9, port: 9200, scheme: http`），重启 moon-well。验证：重启后 healthy，RestClient 日志已显示 `GET http://192.168.31.9:9200/_cluster/health` 200。修改前配置已备份至 fnos `/vol1/1000/app/moon-well/nacos-moon-well.yaml.bak-es-roundtrip-20260914`。
- **遗留**：① moon-well `internalUri` 互信路径实测未生效（无 token + X-User-Subject 仍 401），配置绑定待查（Nacos 优先级/绑定问题），不影响主链路（用户走 session token）；② `Result.error` 的 success 恒 true、全局异常处理器无日志，均已列 R41 建议待修；③ Nacos 侧改配置后需重启才对非 @RefreshScope 的 ES client bean 生效。

### 总结（R42 后更新）

- **requests.md**：R41 追加「部署完成后仍 500」。
- **response.md**：记录 R42 真根因（Nacos 覆盖 ES 为公网环回 → index 间歇 IOException → 500）与修复（Nacos ES 段改直连 + 重启验证），含配置备份位置与三条遗留。
- **冲突记录**：R41 曾将偶发 500 归因于并行重建窗口期，R42 以响应体证据修正为 Nacos ES 公网环回链路的间歇 IOException；窗口期失败与链路抖动两类 500 并存，R42 修复后者（主因）。

### 对 requests 的回应（R43 生词两种展示临时下线，requests #42）

- **改动**：`cps/static/js/reading/epub.js` `markVocabulary` 注释掉生词的两种信息展示——① 悬停 tooltip（`span.title`：释义 + 「上次：书 · 章节」）；② 点击 `alert` 弹窗。两者内容相同且过长，仅保留波浪线标注与 `dataset.word`；划词气泡（翻译/发音/＋－标记）不受影响。
- **配合（moon-well 侧）**：analyze 接口同步暂停查词典释义、仅返回生词本身（`word` + `unknown`），响应体积大幅缩小；连带超纲词（词典 level）判定暂停，仅单词本内未掌握词会返回，详见 moon-well response.md R25 与其 `docs/readme/reading-vocabulary.md` 临时调整说明。
- **验证**：`pytest tests/test_reading_vocabulary.py` 27/27 通过；`node --check epub.js` 语法通过；全仓测试无其它断言依赖被注释代码。
- **恢复方式**：取消 `markVocabulary` 内两处注释即可（moon-well 侧需同步恢复 VO 字段）。

### 总结（R43 后更新）

- **requests.md**：2026-09-14 新增 #42。
- **response.md**：记录 R43 前端展示下线范围、moon-well 配套改动、测试结果与恢复方式。
- **冲突记录**：无。

## 2026-09-15

**R43：默认档位 CET4 + 阅读设置独立页**

- moon-well：DEFAULT_HARD_LEVEL 6→3（CET4），未配置 hard_level 的用户按 CET4 判生词；新增 ReadingSettingsService/Controller（GET /vocabulary/reading/settings 返回当前档位+0-9 档全集，POST /vocabulary/reading/settings/hard-level 校验并落库 app_user.hard_level）；路径复用 /vocabulary/reading/** 的 internalUri 放行规则，无需改拦截器。
- magicbook：新增独立页面 /reading/settings（模板 reading_settings.html，不动 calibre 原有 profile/admin 功能）；web.py 增加页面路由与 /ajax/reading-settings、/ajax/reading-settings/hard-level 两个代理（与现有 reading-* 代理同模式：内网信任 + 身份头透传 + 401 自动刷新）；layout.html 两套主题的用户菜单加「Reading Settings」入口。
- 后续扩展：新的用户级阅读配置统一加到 ReadingSettingsService + reading_settings.html 页面，不再散落。
- 测试：moon-well 259/260（MagicbookApplicationTests 为 contextLoads 冒烟，依赖真实 DB，非内网环境连不上，存量问题）；magicbook pytest 163+6=169 全过（新增 tests/test_reading_settings.py）。

**总结**：requests.md 与 response.md 已同步更新；R43 无与既有需求冲突项。

**R43 修复：保存档位 400**

- 根因：CSRFProtect 全局启用，设置页 JS 从 cookie 读 CSRF token（项目 token 不写 cookie），X-CSRFToken 为空被 400 拒绝。
- 修复：表单加 hidden csrf_token input，JS 改从 DOM 读取（与 epub.js/ai_chat.js 项目惯例一致）；400 响应体含 csrf 时自动刷新页面取新 token（sessionStorage 防死循环，与 epub.js reloadIfCsrfBlocked 同策略）；错误提示带上 HTTP 状态码。
- 测试：新增 CSRF 400 透传用例，pytest 164 全过；已提交推送。

## 2026-09-15（续）

**R44：AI 伴读提示词增加未掌握词汇**

- chat-system 模板生词段落改为「以下是用户暂时还未掌握的词汇：{{unfamiliar_words}}」，空态文案统一为「（本页暂无）」（原 "(none marked)" 中英混杂）。
- 数据无需改动：前端 getUnfamiliarWords() 返回的 vocabularyRecords.unknown=true 集合已包含 reading-vocabulary（/analyze 按档位判定）的生词与用户手动 +/− 标记，经 /ai/chat → build_system_prompt 注入提示词。
- 测试：test_ai_memory 断言更新 + 新增句子存在性断言；pytest 164 全过。

**R44 修正：原提示词保留，中文句作为新增段**

- chat-system 模板恢复原「Unfamiliar words on this page」英文段（列表原样），中文句「以下是用户暂时还未掌握的词汇：…」作为单独一段追加在其后——同一数据源（unfamiliar_words）渲染两处，原提示词语义完整保留。

**R44 再修正：原 chat-system 模板原样保留，中文句作为独立段追加在末尾**

- 之前两次把中文句插进了模板中间（原英文生词段内/其后），不符合「保留原先的系统提示词」的本意。
- 现模板结构：原英文 AI Reading Companion 提示词逐字不动（含 Book Metadata 书名段），末尾在 memory 段之后追加独立段落「以下是用户暂时还未掌握的词汇：{{unfamiliar_words}}」，与 {{extra_section}}（管理员附加指令）共存。
- 书名说明：用户发送消息时前端已带 book_title/book_authors（ai_chat.js POST body），服务端渲染进 Book Metadata 的 Title 行，本就满足「带上当前正在阅读的书名」，无需改动。

**R44 最终态：撤销新增段，chat-system 模板恢复原样**

- 「## Unfamiliar words on this page」原生词段本就承担该职责（reading-vocabulary 判定的生词 + 手动标记都渲染在这里），追加中文句属重复注入，全部撤销。
- 模板回到本次需求前的原始版本；memory.py 的空态「（本页暂无）」保留（替代原 "(none marked)"，纯文案优化）。
- 测试：test_ai_memory 断言同步，pytest 164 全过。

## 2026-09-15（续2）

**R45：记忆系统三项借鉴落地**

- ①信号门控：`has_memory_signal(recent_messages)` 零成本正则扫描（偏好/纠正/背景信号 + 噪音快答识别 + 长文兜底），`/ai/chat` 提取点改为「间隔门控 + 信号门控」双闸，无信号跳过 LLM 提取。
- ②去重/合并：`find_duplicate_memory()` 落库前与现有记忆比对——token 集合 overlap 系数（连字符归一化 world-building=worldbuilding，系数 = 交集/较小集合），阈值 0.5；近重复跳过写入仅刷新原条目时间戳，防重复行挤占注入窗口。
- ③相关性注入：`select_relevant_memories(user_id, book_id, book_keywords, limit)` 排序规则——本书记忆（source_book_id 匹配）优先 → 文本提到本书关键词（书名/作者/标签）的次之 → 近期记忆补位，注入上限不变。
- 测试：新增 tests/test_memory_gating.py 13 用例；集成测试对话改为含偏好信号的消息（门控预期行为）；pytest 177 全过。



---

## 2026-09-15（第二次对话）

### R46（整本翻译还是不行：跨仓库三断点修复）

- **排查结论（跨 magicbook + moon-well 全链路）**：设计为「magicbook 发布任务 → moon-well 任务队列 → 外部执行器执行 → moon-well 自写段落缓存 → magicbook 单向查缓存」。但部署内**没有外部执行器**（fnos compose 仅 moon-well 单服务，全仓库无 /llm/task/accept 消费方），发布的任务只是 PENDING 记录，永不执行；payload 未带 promptTemplate，即使执行也不会产出中文译文；前端提交后无进度反馈，用户感知即「整本翻译不行」。
- **moon-well 侧修复**（见 moon-well 仓库 R30 记录）：发布即入进程内优先级调度器、启动恢复历史 PENDING 积压、执行前按模板渲染提示词。全量 267 passed。
- **magicbook 侧修复**：
  - `cps/reading_translation/service.py`：发布/重试 payload 增加 `promptTemplate: reading-paragraph-translate-plain`（不依赖书名/章节变量，渲染稳妥）；`progress()` 增加 `pendingCount`（区分「发布未完成」与「失败」）。
  - `cps/static/js/reading/epub.js`：提交成功后持久化 jobId（localStorage）并每 30s 轮询 status 接口，COMPLETED / PARTIAL_FAILED 时 toast 提示并停止；提交弹窗展示 总段落/已缓存/新发布 三项规模，说明译文后台逐段生成、阅读时自动回填。
  - `cps/templates/detail.html`：提交反馈同步为批次规模弹窗。
  - 新增测试 `test_publish_payload_carries_prompt_template_and_progress_reports_pending`（断言发布 payload 带模板键 + progress 含 pendingCount）；全量 **181 passed**。
- **生效条件**：两侧镜像均需重新构建部署；moon-well 重启后自动恢复此前卡住的 PENDING 任务（含 9/8 之前发布的旧批次）。
- **阅读器回填说明**：已读段落的译文优先走 localStorage 本地缓存；未读段落经 status 轮询触发懒回收后，翻页由 `restoreCachedTranslations` 回填（ES 缓存保证跨设备不丢）。

### 总结

- **requests.md**：追加 R46（整本翻译排查修复）。
- **response.md**：记录三断点根因、两侧修复、测试与部署要求。
- **冲突记录**：无；功能为 R46 新增排查，未与既有需求冲突。


---

## 2026-09-16

### R47（整本翻译段落数异常：128 段 vs 实际 3177 个 <p>）

- **排查**：从 fnos 拉取 book 44 的 EPUB 实测：全书 3177 个 `<p>`、约 48 万字符；模拟解析规则应保留 3160 段；但 `extract_epub_paragraphs` 只抽出 796 段，且**同一文件多次抽取结果随机**（759 / 78 / 78 / 78 段）——「结果不确定」直接指向非确定性 bug。
- **根因**：`extract_epub_paragraphs` 用 `id(node)` 做「同一节点不重复处理」的去重集合。lxml 的元素代理对象按需创建、循环内不再被引用即被 GC，后续元素复用同一内存地址 → `id()` 碰撞 → 大量未处理段落被误判「已见」直接跳过。生产那次恰好在只处理到 128 段的窗口里完成任务提交。另发现两处伴生问题：章节名取 `<title>` 优先于 `<h1>`（Calibre 转换书每章 `<title>` 恒为书名，全书章节全被标成书名）；全角空格等空段落未过滤。
- **修复（parser.py 重写抽取部分）**：
  - 块级节点先**物化成强引用列表**再遍历——地址稳定后 `id()` 去重才可靠；
  - 祖先过滤改走 `getparent()` 真实引用链，不再用 `iterancestors()` 的临时代理；
  - 章节名 **h1 优先**、`<title>` 兜底；
  - 空文本段落不产出。
- **验证**：修复后 HP2 抽取 **3160 段 / 19 章**，三次运行结果完全一致；新增确定性回归测试（300 段 synthetic EPUB 多次运行必须一致）与嵌套块/空段测试；全量 **183 passed**。已提交 44577fe6 并推送。
- **注意**：此前发布的错误批次（jobId 0bd46ce1...，total=128）建立在错误抽取结果上——新版本部署后需在详情页 force 重新翻译，旧批次直接在「翻译状态」里取消即可（其段落索引/文本与新版抽取不一致，不能复用）。

### 总结

- **requests.md**：追加 R47（段落数异常排查修复）。
- **response.md**：记录 id() 复用根因、三处修复与验证。
- **冲突记录**：无。


---

## 2026-09-17

### R48（段落数还是不对：109 段——同步发布循环被网关超时杀死）

- **排查**：线上 epub.js hash 与本地一致 → 容器已是新镜像、新 parser 生效。但 109 ≠ 3160，且上次 128 / 这次 109 每次不同——两次的共同点是**数字都远小于全书段落，且都在「发布中途停止」**。根因不在抽取，而在 `start()` 的结构性缺陷：整本书数千段、每段一次 moon-well HTTP 发布，全部跑在 HTTP 请求线程里同步串行（3160 次 × ~0.5s ≈ 25 分钟），公网网关（openresty 默认 ~60s）必然先断连，gevent pywsgi 随即终止该请求的 greenlet → 发布循环死在断连点。109 就是这次请求死掉的位置。数字每次不同 = 死亡位置不同（受每次请求耗时抖动影响）。
- **修复（service.py 重构）**：
  - `start()`：请求线程只做 抽取 + 建 job（秒级），发布整体交给**后台线程** `_publish_pending`，HTTP 立即返回 job 进度；线程内自建 scoped session，finally 归还。
  - `retry()`：同样后台化（`_retry_failed`），失败段上千时不再占住请求。
  - **缓存查询分批**：`find-translations` 一次性携带全书 3160 段（~1MB body）本身就是超时隐患，改为每批 200 段，单批失败跳过不影响其余。
  - 单段发布失败只标 FAILED 可重试，不中断整批。
- **验证**：新增「单段发布失败不中断整批」测试（3 段中第 2 段抛异常 → published=2 / failed=1，且 3 段全部尝试）；全量 **184 passed**。
- **遗留说明**：fnos SSH 当前不可达（22 端口超时），无法直接查生产容器日志验证 109 断连点，修复逻辑由测试覆盖。部署后验证方式：提交后立即返回 totalCount≈3160；pendingCount 随 status 轮询持续下降——只要 pending 在动，发布线程就是活的。

### 总结

- **requests.md**：追加 R48（109 段排查修复）。
- **response.md**：记录同步发布循环被网关超时杀死的根因与后台化改造。
- **冲突记录**：无。


---

## 2026-09-17（第二次对话）

### R49（彻底解决：启动恢复 + 系统身份内部调用，断点续作闭环）

- **补充修复**：后台发布线程是 daemon，容器重启/更新会杀死它，遗留 PENDING 段落既不发布也不失败，批次永久卡死。
  - `service.py` 新增 `recover_active_jobs(publish, lookup)`：应用启动时扫描存在 PENDING 项的活动批次并重新拉起发布线程（设计文档 §9 断点续作落地）。
  - `web.py` `_moonwell_proxy` 新增 `system_identity=True` 内部调用模式：以系统身份 X-User-* 头（moon-well 内网信任自动建号）发布任务，启动恢复不依赖用户会话。
  - `__init__.py` `create_app` 挂启动钩子（WHOLE_BOOK_RECOVERY=0 可关闭）。
- **验证**：全量 184 passed。
- **e2e 环境约束**：调用 API 翻译整本书需要 magicbook 登录态；Authentik OIDC 启用后本地密码登录前后端均禁用，密码模式/设备流均需 client_secret（存于服务器 .env，当前 fnos SSH 不可达），自动化登录暂不可行。部署完成后由用户在页面发起（或提供可编程凭据）即可完成验证。

### 总结

- **requests.md**：追加 R49。
- **response.md**：记录启动恢复机制与 e2e 约束。

---

