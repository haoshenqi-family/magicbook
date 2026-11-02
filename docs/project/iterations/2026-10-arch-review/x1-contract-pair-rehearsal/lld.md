# X1 契约治理 · 两端联合彩排（magicbook ↔ moon-well）· LLD

**状态**：已上线（2026-10-16，magicbook `develop` push 至 `82200509`；本工作项自身只新增文档与一处代码注释，无行为变更）。
**需求**：magicbook requests R189 ｜ **家族项**：X1（三端契约合围＝moon-well M4 + magicbook B5 + magiclens L1）
**范围**：本轮只做**两两联合**（magicbook ↔ moon-well）。第三端 magiclens 的代码已在 develop 并已推送，但**扩展未发版**，浏览器里跑的还是旧版，所以 X1 的三端联合验收仍属未完成，判据见 §6。

> ⚠️ 本目录是 v2 迁移后**第一个** `iterations/` 工作项。`<ITER>` 取名 `2026-10-arch-review`（沿用架构评审系列的既有编号空间）——
> 这是**提案不是结论**：若你要按 PingCode 迭代/版本重新命名，改名成本只有一个目录，随时可换。

## 1. Why 要本机彩排，而不是等线上

X1 的判据是**两端拼起来才算数**的：服务端 M4 开始框架兜底统一 `Result` 信封，消费方（magicbook 的 `common/api.js`、
magiclens 的 `rpc.js`）解包口径必须同时改，任何一端旧了就退化成「各自单测绿、线上仍误判」。
线上验不了这三类形状（正常业务不会返回网关 HTML），而把故障注入生产是不可接受的。
2026-10-05 那次 vocab-size-test 的 §4 彩排已经证明「本机起真 moon-well」这条路可行，本轮复用同一配方。

## 2. 彩排拓扑（全部本机，生产零接触）

| 件 | 形态 | 关键点 |
| --- | --- | --- |
| moon-well | 真 `develop` HEAD（`4e4fc3d`，含 M4 `ResultResponseBodyAdvice`、M5 `UserContext`）检出到 `/tmp/mw-x1`（detached worktree），`mvn -o spring-boot:run`，端口 **18090** | `SPRING_CONFIG_IMPORT=`（空值）→ config-data 列表为空、**完全不碰 Nacos**；`SPRING_CLOUD_NACOS_DISCOVERY_ENABLED=false` |
| MySQL | `docker run vt-x1-mysql -p 3397:3306`，空库 `magichouse` | 空库启动 → Hibernate 建表 + 应用自播种（TTS 模型表、25 条成就定义）；**不指向生产 .9** |
| Redis | `docker run vt-x1-redis -p 6382:6379` | 一次性 |
| ES / MinIO / NewAPI / 代理 | 全部 dummy 值 | 故意留坏，用来造「上游依赖故障」样本 |
| 认证 | `app_user` 里插一行 `token='mk-<hex32>'` | 拦截器 `mk-` 分支查库校验（`UserService.getByToken`）→ **magicbook 侧不需要 OIDC 也能拿到合法身份**，这是本轮解锁「本机跑不了要令牌的链路」的关键 |
| magicbook | `docs/temp/run_x1_pair.py`：`create_app` + 手工注册蓝图 + `config.db_configured=True` + `before_request` 里 `login_user(admin)` 并写 `session["moonwell_access_token"]` | `MOON_WELL_READING_URL=http://127.0.0.1:18090`，**不桩 `_moonwell_proxy`**——采到的是上游真实产出 |

## 3. 实测样本（五条，全部来自真链路）

| # | 造法 | magicbook 侧看到的 | 判定 |
| --- | --- | --- | --- |
| S1 正常 | `GET /ajax/reading-settings` | `200 {"success":true,"message":"","code":200,"result":{hardLevel,hardLevelName,usingDefault,options[10],morphologyVersion}}` | ✅ 信封由 M4 兜底，`options` 十档齐全且不含哨兵 10 |
| S2 业务失败 | `POST hardLevel=99` | `500 {"success":false,"message":"系统异常，请联系管理员","code":500}` | ⚠️ **失败可见成立，但文案被吃掉**：moon-well 日志里抛的是 `IllegalArgumentException: hardLevel 必须是 0-9 之间的有效档位`，`GlobalExceptionHandler` 把它降级成通用 500 文案（见 §5 缺陷①） |
| S3 凭证无效 | 送一个不存在的 `mk-` key | `401 {"success":false,"message":"登陆信息无效，请重新登陆","code":401}` | ✅ 401 且 Result 形制 |
| S4 非 Result 上游 | 把 base 指到 `python3 -m http.server`（网关/非服务方的 HTML 错误页等价物） | `404` + `<!DOCTYPE HTML>…` **原样透传** | ✅ 防腐层不假装包装；❌ 消费端必须自己判（见 §4） |
| S5 上游不可达 | base 指到关闭端口 | `503 {"success": false, "message": "reading settings service unavailable"}` | ✅ 由 `MoonWellClient` 自己造的 Result，前端 strict 解包会抛 → 可见 |

## 4. 判据①② 的实测结论

把上表 5 条 body 喂给**真 `cps/static/js/common/api.js`**（无头 Chrome，`docs/temp/x1_unwrap_probe.html`，`fetch` 按样本桩入），
矩阵结果（节选）：

| 样本 | `httpJson` 解析 | `unwrapResult`（容错） | `unwrapStrict`（严格） |
| --- | --- | --- | --- |
| S1 | object | 返回 `result` 载荷 | 返回 `result` 载荷 |
| S2 | object | **抛** `系统异常，请联系管理员` | 同左 |
| S3 | object | **抛** `登陆信息无效，请重新登陆` | 同左 |
| S4 | `null`（parse 失败） | **返回 null，不抛** ← 唯一需要调用方兜住的一格 | 抛（但因 `window.mbT` 缺席变成 `TypeError`） |
| S5 | object | **抛** `reading settings service unavailable` | 同左 |

**判据①（非 Result 不误判）达成**——但成立的理由不是「容错解包会抛」，而是**可达性**：
逐个查了消费点，`ai_chat.js` 走 `$.getJSON`（非 JSON 直接进 jQuery 的 fail 分支，够不到 `unwrapResult` 的 null 格），
`learning-common.js`/`credits.js` 走 `unwrapStrict`（null 必抛）。S4 那一格在现网**不可达**。
**判据②（失败可见）达成**：S2/S3/S5 都带可读 message 抛出；且 `credits.js` 的 catch 一律 `showError(...)`/
`text-danger` 行、`learning-common.js:122` 是 `window.alert(err.message)`，`ai_chat.js` 的
`loadBookProfile`/`loadMemories` 也是「错误行进面板」——即同文件里既有正确姿势，也有下面 §4.1 的吞错姿势。

### 4.1 我在 R189 里把三条「缺陷」写重了，逐条复核

占号那条写得比实测硬，这里如实降级（编号不回改，更正就写在本节）：

1. **「配合 ai_chat 的 `catch (e) { convs = []; }` 会把网关故障伪装成没有会话」→ 不成立**。
   网关 HTML 那一路在 `$.getJSON` 阶段就进 `.fail()`，够不到这个 catch；这个 catch 只在
   「2xx 且 `success:false`」或「body 字面量 `null`」时才可能触发，而 `/ai/agent/conversations` 两种都不会返回。
   它是**冗余的吞错写法**（同文件另有两处把错误呈现出来的正确姿势），属可读性/一致性问题，不是线上缺陷。
2. **「`reading_settings.html` 只引 api.js 不引 i18n 种子，strict 解包会抛 TypeError」→ 前提错**。
   该模板 `{% extends "layout.html" %}`，而种子在 layout 第 263 行 → `mbT` 在该页是**有定义的**。
   降级为**潜在约束**：api.js 是全站公共层却硬依赖 `window.mbT`，将来任何「引 api.js 但不带种子」的骨架页
   都会把故障文案变成 `TypeError: window.mbT is not a function`。本轮**只把这个依赖写进 api.js 的注释**
   （不加兜底代码：为一个今天不存在的场景加分支，正是家族规约里禁止的那类「假想未来」）。
3. **「那两个吞错的调用点没有任何 fail 分支」→ 错**。`loadConversations` 有 `.fail()`，且带设计理由
   （agent 未开 / moon-well 不可达时下拉留空、输入框仍可用，发送时再报具体错）。

## 5. 本轮真正的产出：一条 moon-well 侧缺陷 + 一份可复现彩排

**缺陷①（属 moon-well，不在本轮修）**：入参校验失败被统一降级成「系统异常，请联系管理员」。
日志里 `IllegalArgumentException: hardLevel 必须是 0-9 之间的有效档位` 是**精确文案**，但
`GlobalExceptionHandler` 对非 `GlobalException` 的异常一律回 500 + 通用文案 ⇒ 用户在页面上看到的永远是
「系统异常」，排查要从 ES 反查 traceId 才知道是自己填错档位。这正是家族规约⑦「失败必须在界面上可见且可归因」
要防的形态。修法属 moon-well 的异常映射（把校验类异常映射 400 + 原 message），**需要它的会话/用户立项**，
我不跨仓改鉴权与异常语义。

## 6. 判据③ 与剩下的一格

X1 完整判据还差：**第三端（magiclens）真版本上线后的同窗验收**，以及**异步链路用户上下文不丢**（M5）的
端到端证据——后者本轮**没验**：彩排实例的 LLM/计费通道全是 dummy，扣费归属这条路走不通。
两条都要等 moon-well 绿闸门 + 上线、magiclens 发版后，在真登录态下跑。

## 7. 复现步骤（照抄即可）

```bash
# 1) 依赖容器（端口沿用 release-checklist §4.0 的避让区间）
docker run -d --name vt-x1-mysql -p 3397:3306 -e MYSQL_ROOT_PASSWORD=vt123 -e MYSQL_DATABASE=magichouse mysql:8.0
docker run -d --name vt-x1-redis -p 6382:6379 redis:latest
# 2) 彩排实例（env 全套见 §2；键值不落文档，AUTH_TOKEN_SECRET 用清单里那个 local-rehearsal 值）
git -C moon-well worktree add --detach /tmp/mw-x1 develop
cd /tmp/mw-x1 && export … SPRING_CONFIG_IMPORT= SPRING_CLOUD_NACOS_DISCOVERY_ENABLED=false \
  && mvn -o -DskipTests -Djava.version=21 spring-boot:run -Dspring-boot.run.arguments="--server.port=18090"
# 3) 造一个 mk- API-key 身份（绕开「本机没有合法 moon-well 令牌」这条老边界）
docker exec vt-x1-mysql mysql -uroot -pvt123 -e \
  "insert into magichouse.app_user (password, token, username) values ('scratch','mk-<hex32>','x1-rehearsal');"
# 4) magicbook 采形制（docs/temp/ 不入库，脚本在本工作项同目录另有副本说明）
cd magicbook && MOONWELL_X1_TOKEN=mk-<hex32> .venv/bin/python docs/temp/run_x1_pair.py   # → PAIRJSON[...]
# 5) 前端解包矩阵：repo 根起静态服务后无头 Chrome dump-dom 取 #out
python3 -m http.server 8099 --bind 127.0.0.1
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
  --user-data-dir=/tmp/x1-ch-$(uuidgen) --window-size=1200,900 --virtual-time-budget=15000 \
  --dump-dom "http://127.0.0.1:8099/docs/temp/x1_unwrap_probe.html"
# 6) 收尾（本机 scratch，随手清）
git -C moon-well worktree remove /tmp/mw-x1 && docker rm -f vt-x1-mysql vt-x1-redis
```

探针脚本与样本落在 `docs/temp/`（不入库），五条样本原文内联在下面，保证证据本身可回溯：

```
S1 200 {"success":true,"message":"","code":200,"result":{"hardLevel":3,"hardLevelName":"CET4","usingDefault":true,"options":[{"code":0,"name":"小学"},…,{"code":9,"name":"GRE"}],"morphologyVersion":"1.0.0"},"timestamp":…}
S2 500 {"success":false,"message":"系统异常，请联系管理员","code":500,"result":null,"timestamp":…}
S3 401 {"success":false,"message":"登陆信息无效，请重新登陆","code":401,"result":null,"timestamp":…}
S4 404 <!DOCTYPE HTML>…<h1>Error response</h1><p>Error code: 404</p>…   ← 非 JSON，原样透传
S5 503 {"success": false, "message": "reading settings service unavailable"}   ← magicbook 防腐层自造
```
