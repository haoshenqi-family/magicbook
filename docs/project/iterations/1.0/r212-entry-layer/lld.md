# 入口层换皮 · 品牌资产与字样收敛（magicbook R212 / PJM MB-11）· LLD

**状态**：已上线（2026-10-24 develop `195ab0d7`，新基线全量 819 passed；本轮覆盖交付项 2 + 交付项 5 的素材面。**R212 整条仍未完成**：交付项 1「价值主张 + 书墙」、3「locale claim 链路」、4「语言入口前置」未做）

## 1. 承接与拍板

MB-11 待办第 1 项：authentik 的 logo 与登录页背景仍是官方默认。用户 2026-10-23 三项拍板：

1. 素材托管走 **MinIO `brand/` 前缀**（不新建静态服务、不从 magicbook 直链）；
2. 主标识取**圆章版**「雪鸮立旧书 + 魔杖一点光」；
3. magicbook 本轮只改到**「改名 + 挂徽章 + favicon」**一层，不动配色与布局（登录页换皮与整站 HP 化明确不做）。

视觉延续站内既有语言：伙伴引导文案已是「一只雪鸮正在等新读者」（`messages.po`），雪鸮即家族吉祥物；**不使用**霍格沃茨校徽、闪电 H 字标或任何电影原图。

## 2. 两条通道，一枚圆章

| 消费方 | 取法 | 原因 |
| --- | --- | --- |
| authentik（`account.haoshenqi.top`） | MinIO 匿名直链 `https://minio.haoshenqi.top/magicbook/brand/{logo,favicon,login-bg}` | 它的 `branding_*` 只吃 URL 字符串，自身无上传与静态路由（moon-well R209 已背书并开白名单） |
| magicbook 顶栏与 favicon | **同源静态文件** `cps/static/img/brand/{logo,favicon}.png` | 本仓 CSP 是 `img-src 'self' data:`，且 `tests/test_csp_media.py::test_buddy_image_origin_not_opened_site_wide` 明确断言「其余页面不放行 MinIO」（R181 窄面口径）。顶栏徽章全站可见，逐端点放行表达不了，故不为其放宽守卫 |

**同一枚圆章、两份产物**，由 `haoshenqi-family/vibe_images/build_brand_assets.py` 一次性生成（源图 = AI 生成的圆章与背景；圆章无水印，背景裁掉右下角「Qoder AI生成」水印条）。改标识只改源图 + 重跑脚本，两份产物不手改。

产物尺寸：MinIO `logo.png` 256px/106KB、`favicon.png` 64px/9KB、`login-bg.jpg` 1792×972/**178KB**；站内 `logo.png` 128px/30KB（顶栏实显 26px，留 5x 余量）、`favicon.png` 64px/9KB。

**背景做过一次压暗**（整图 ×0.72 + 中上带再压）：authentik 的 flow 标题是**无阴影白字**，落点正在这张图的亮窗上——headless Chrome 去掉 mock 里误加的 `text-shadow` 复测，对比度不足。压暗比给 brand 挂 `branding_custom_css` 更省事，也不会把「素材问题」伪装成「样式覆盖问题」。

## 3. 字样收敛（交付项 2）

台账原记「6 处」是**只扫模板**的结果，实测用户可见面共 **13 处**（模板 6 + Python 7）。按「token 替换、不重写文案」处理：

- 模板：`http_error.html`、`detail.html`（归档 tooltip）、`logviewer.html` ×3、`osd.xml`。
- Python：`admin.py`（配置保存 flash ×2、封面刷新确认、Kobo 全量同步确认）、`kobo_auth.py`、`helper.py`（邮件正文落款、测试邮件主题、注册欢迎邮件正文与主题）、`search.py`。
- `config_sql.py` 的 `config_calibre_web_title` 默认值 `Calibre-Web` → `magicbook`（只影响新库首启；运行态仍以「管理 → 界面设置」为准）。

**有意保留**（守卫测试里逐条注明）：文件头许可证署名、`log.*`/`print`（ES `app-log-magicbook` 按文本检索，改了断链）、`stats.html` 的 "powered by Calibre-Web"（真实上游归属）、`cli.py --help` 与调试包文件名（运维面，非站内观感）。

**i18n 联动**：gettext 按 msgid 匹配，改 msgid 必须同步 `zh_Hans_CN/messages.po` 的 msgid+msgstr 并重编 `.mo`，否则中文界面**退回英文**——现场看起来像「翻译丢了」。本轮 10 条有译文的词条成对更新（顺带修上游两处笔误：`Caliebre`、`Catalog` 误译「路径」），无译文的 3 条（`admin.py` 两条确认文案、`kobo_auth.py`）行为与改前一致。

## 4. 顶栏与图标

`layout.html`：`.navbar-brand` 内在文字 wordmark 前插 `<img class="brand-mark" alt="">`（`alt=""` 因相邻文字已承担名称，避免读屏念两遍）；`rel="shortcut icon"` 换成 `rel="icon" type="image/png"` 指向品牌圆章，`apple-touch-icon` 未动。
`style.css`：新增 `.navbar-brand .brand-mark`（26×26、`margin: -6px 8px 0 0`、`vertical-align: middle`）。**偏移是量出来的**：headless Chrome 实测圆章中线与文字盒中线差 **-0.4px**（Grand Hotel 35px 手写体的字形中线低于行框中线，直接 `vertical-align: middle` 会顶高）。

## 5. 测试

`tests/test_brand_consistency.py` 5 例（新增）：模板无残留字样 / 无 `_(...)` 带上游品牌 / 10 条改名词条必须解析出中文 / 资产存在且被 `layout.html` 引用且 CSS 有定位规则 / 配置默认值形态。
**反向变异已做两处**：把 `http_error.html` 还原成 Calibre-Web + 把 `.mo` 还原成改前版本 → 2 例即红；复原后 5 passed。
开发态闸门（仓规只跑改动相关）：`test_brand_consistency` + `test_csp_media` + `test_adv_search_read_status` + `test_book_detail_r214` + `test_i18n_seed_contract` + `test_llm_task_admin_monitor_r130` + `test_login_invite_link` + `test_oidc_admin_role` + `test_word_detail_batch_r176` = **138 passed / 0 failed**。全量 `pytest tests/` 属发布闸门，留用户显式指令。

## 6. 交付四问

- 用户可见能力变了吗 → 无新能力，仅品牌观感；L1 只在 `readme/admin.md` 消歧「上游 Calibre-Web 自带的」。
- 契约变了吗 → 无（未新增路由、未改接口）。
- 实现/边界变了吗 → 是：字样收敛边界（改什么、留什么）与「站内同源 / 认证域 MinIO」双通道，落在本 LLD 与守卫测试注释。
- 本次怎么实现 → 本文。

## 7. 上线顺序与实况（2026-10-24 回填）

1. ~~moon-well R209 push 上线~~ **未做**（push 闸门留用户）。现网 `brand/` 匿名读改由脚本手工设置 → **不持久**，见 §8。
2. **已完成**：三张对象已传 MinIO `magicbook/brand/`，匿名 GET 实测 `logo.png`/`favicon.png`/`login-bg.jpg` 全 **200**，`buddy/` 与 `ted-audio/` 同期回归 200（无过授权、无被抹掉）。
3. **已完成（2026-10-24 08:09）**：magicbook push develop `8842d1c2..195ab0d7` → fnOS `build END OK`、基线推进；线上实测 `<title>magicbook | Login</title>`、顶栏圆章 + Grand Hotel wordmark 渲染正确、`/static/img/brand/{logo,favicon}.png` 双 200。发布闸门：合并新基线后 `pytest tests/` = **819 passed / 0 failed**（首跑 819 同数，合并 ai_chat 那笔后复跑）。
4. **已完成**：authentik 两条 brand 的 `branding_logo`/`branding_favicon`/`branding_default_flow_background` 已写入（`UPDATE 2`，改前值备份在 fnOS `/root/authentik-brands-backup-20261024-r212.json`）+ `docker compose restart server worker`（server 约 10s 回 healthy）。
5. **已完成**：现网核验（headless Chrome 真页面截图）——`--ak-flow-background` 与 `branding_logo`/`branding_favicon` 均指向新对象，圆章与背景实际渲染正确、白卡对比度足够。

**顺带查清的一处非本轮缺陷**：登录按钮文案仍是英文「Log in」（真人中文浏览器实测，非探针假象）。它**不在**任何配置面里——2025.10 的 `authentik_flows_flow` 无 `submit_button_text` 列、`authentik_flows_flowstagebinding` 无 `label` 列（均实测 schema），R162 的「表单文案中文化」覆盖的是 prompt 的 label/placeholder，不含提交按钮。要改只能动上游前端包，另立条目，不夹进本轮。

## 8. 风险登记

- **IP**：认证域 logo/背景是新的对外可见面，随 `docs/product/companion/features/buddy-ip-risk.md` 同一登记处置（内测可接受，公开注册/对外发布前须换原创）。本轮素材为原创构图，未使用电影原图与校徽。
- **依赖**：authentik 登录页由此依赖 `minio.haoshenqi.top`（群晖 `.10`）。MinIO 不可达时登录**功能不受影响**，仅裂图；刻意不加兜底 CSS——把素材故障伪装成「本来就这样」会让下一次排查从「图没了」变成「样式怪」。
- **~~现网策略是手工设的，不持久~~ 已闭合（2026-10-24）**：moon-well R209 上线后策略由代码在启动时写入，在跑槽 `moon-well-blue`（`house.build-sha=3fa0800`）日志实证 `prefixes=[ted-audio/, buddy/, brand/]`。残留风险改述为：**回退 moon-well 到早于 `3fa0800` 的镜像会抹掉 `brand/`**，认证页三图随之 403（登录功能不受影响）。
- **站点标题已改（2026-10-24）**：`app.db` 的 `settings` 表单行 `config_calibre_web_title` 由 `Calibre-Web` 更新为 `magicbook`（取拉丁文而非中文——顶栏 wordmark 是 Grand Hotel 手写体，无中文字形，中文会掉成默认字体）。该值在应用启动时读入内存，改完当下线上仍吐旧值，由本次部署的重启生效，已实测 `<title>magicbook | Login</title>`。
