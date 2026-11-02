# 新概念英语课级音频播放 LLD（magicbook 直连 MinIO 流式播放）

> **特性代号**：nce-audio ｜ **日期**：2026-10-04 ｜ **状态**：草案（待用户评审确认后才进入编码）
> **需求来源**：requests.md R116③「把 mp3 也下载到 minio 中，增加一个文章级别的音频播放功能」
> **代码事实依据**：`cps/web.py`（read_book 音频路由、`_moonwell_proxy` 代理先例）、`cps/templates/detail.html:109-133`（audio_entries 入口）、`cps/templates/listenmp3.html`（soundmanager2 播放器）、`cps/audio.py`（mutagen 已随镜像安装）、moon-well `TedAudioService.java`（MinIO 服务端流式读取先例，bucket 私有、无预签名）
> **数据事实依据**：fnOS 生产库 books #92–#95，series=`新概念英语`，series_index=1.0–4.0；音频源 tangx/New-Concept-English 美音版，276 课 mp3+lrc 已规范化为 `book{1..4}/{num}-{slug}.{ext}`（552 文件，729MB，尺寸全量校验通过）

---

## 1. 背景与目标

新概念英语四册（#92–#95）已入库，但只有 PDF 正文，听音频需要离开 magicbook。配套美音 MP3（276 课）与 LRC 歌词已下载到本地并即将入库 MinIO `magicbook` bucket（私有）。

**本期目标**：
1. 音频对象入 MinIO：`magicbook/nce-audio/book{1..4}/`，与 ted-audio/reading-tts 同 bucket 前缀隔离（延续既有约定）；
2. magicbook 新增**课级音频播放**：从书的详情页进入「课文音频」列表，逐课在线播放（可拖动进度），按 series_index 与 Calibre 书关联；
3. 播放鉴权与书库一致：登录用户可播，未登录不可见。

**明确不做（负面清单）**：
- 不做段落级切分/逐句复读（只到"课"粒度）；
- 不把 mp3 作为 Calibre 音频格式入库（不改 metadata.db 数据模型，不进 OPDS/kobo 音频链路）；
- 不做下载/转码/波形图；播放倍速、A-B 复读不做（US2 之外再议）；
- 不暴露 MinIO 公网地址，不用预签名 URL（浏览器只见 magicbook 域名）；
- 不动 moon-well 代码。

---

## 2. 总体架构

```
浏览器（magicbook.haoyuhang.top）
   │  ① 页面/JSON（cookie 会话，Flask）
   ▼
magicbook 容器 :8083（fnOS，host network）
   cps/nce/ 新 blueprint：
   · GET /nce/<book_id>               播放页（登录）
   · GET /nce/<book_id>/lessons       课表 JSON（manifest 缓存）
   · GET /nce/<book_id>/audio/<num>   mp3 流（登录 + Range 透传）
   · GET /nce/<book_id>/lyric/<num>   lrc 文本（登录）
   │  ② minio SDK（urllib3），内网 http://192.168.31.10:9000
   ▼
MinIO（群晖 .10）bucket=magicbook（私有）
   nce-audio/book1/… / book4/…（552 对象 + 4 manifest）
```

关键取舍：**方案 A：magicbook 直连 MinIO 服务端流式读取**（已选定，理由见 §6 备选对比）。
不新增中间服务、不跨项目改动；magicbook 首次引入 MinIO 凭据（compose `.env` 两个键），bucket 保持私有。

## 3. 数据布局

### 3.1 MinIO 对象

| 前缀 | 内容 |
| --- | --- |
| `nce-audio/book{N}/{num}-{slug}.mp3` | 课文音频（美音，MPEG-1 Layer3 128kbps 级） |
| `nce-audio/book{N}/{num}-{slug}.lrc` | 歌词（时间轴 `[mm:ss.xx]`，UTF-8） |
| `nce-audio/book{N}/manifest.json` | 课表清单（服务端唯一枚举来源，禁止逐请求 listObjects） |

`num` 命名沿用下载脚本产物：book1 为合课号 `001-002`（48 课×2 课合并），book2–4 为单课号 `01`–`96`/`01`–`60`/`01`–`48`。`slug` 为英文课名小写下划线。

### 3.2 manifest.json（生成一次、上传后只读）

```json
{
  "book": 1,
  "generated": "2026-10-04T12:00:00Z",
  "lessons": [
    {"num": "001-002", "slug": "excuse_me", "title": "Excuse Me",
     "audio": "001-002-excuse_me.mp3", "lyric": "001-002-excuse_me.lrc",
     "duration_sec": 61, "size": 985733}
  ]
}
```

- `title` 取源文件名英文课名（`－` 后原文，保留大小写）；
- `duration_sec`/`size` 由生成脚本用 mutagen + 文件 stat 读取；
- 生成与上传脚本放 `docs/temp/scripts/`（nce_manifest.py + mc mirror），不入应用代码。

### 3.3 书 ↔ 音频映射（无新表、无 Calibre 字段改动）

`book_id → series_index`：书存在 `cps/` 数据库（SQLAlchemy `db.Series`/`series_index`）且 series 名称为 `新概念英语` 时，`book_no = int(round(series_index))`，取值 1–4。映射规则实现为单一函数（`resolve_nce_book_no(book)`），播放页/接口统一调用；非 NCE 系列书一律 404。

## 4. 后端设计（cps/nce/ 新 blueprint）

### 4.1 MinIO 客户端

- 新依赖 `minio>=7.2`（进 requirements.txt，走 aliyun pip 镜像构建）；
- 配置：`MINIO_ENDPOINT`（`192.168.31.10:9000`）、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY`、`NCE_AUDIO_BUCKET`（=`magicbook`），env 读取沿用 `CALIBRE_*` 大写键先例，fnOS compose `.env` 增两键；
- 客户端单例惰性初始化（模块级，凭据缺失时接口返回 503 并 log error，不影响主应用启动）。

### 4.2 流式端点（Range 支持）

`GET /nce/<book_id>/audio/<num>`：
1. 登录校验（`@user_login_required`）；`num` 白名单校验（只允许 manifest 中存在的课号）；
2. `minio.get_object(bucket, key, offset, length)` 透传 `Range: bytes=start-`；无 Range 时整对象流式返回；响应带 `Accept-Ranges: bytes`、`Content-Length`、`Content-Range`（206）、`Content-Type: audio/mpeg`；
3. 用 Flask `stream_with_context` 分块转发，不在内存攒整文件（ted-audio 全量 readAllBytes 的教训：mp3 单课 1–4MB 可接受，但流式实现与 Seek 天然契合）。

`lyrics` 端点返回 `text/plain; charset=utf-8` 原始 lrc 文本，解析在前端。

`lessons` 端点返回 manifest 内容（内存缓存：进程级 dict + 5 分钟 TTL + ETag 由 `generated` 字段承担），前端不直读 manifest 对象。

### 4.3 错误语义

| 场景 | 响应 |
| --- | --- |
| 未登录 | 302 登录页（Flask-Login 既有行为） |
| 书非 NCE 系列 / num 不在 manifest | 404 |
| MinIO 不可达 / 凭据缺失 | 503，log `nce-audio` 前缀（可被 filebeat 采集排障） |

## 5. 前端设计

### 5.1 入口（detail.html）

书的 series 解析出 NCE book_no 时（后端传 `nce_book_no` 变量），详情页现有 audio_entries 区块旁渲染「课文音频」卡片：`共 N 课 · 总时长`，链接 `/nce/<book_id>`。非 NCE 书零痕迹。

### 5.2 播放页 `nce_player.html`（新模板）

- 布局：左侧课表列表（课号+英文课名+时长），右侧固定底部播放器；移动端课表全宽（沿用 bootstrap 3 栅格，与现有模板一致，不引新 CSS 框架）；
- 播放器：**原生 `<audio>` + 自制控件**（播放/暂停、上下课、进度条 seek、时间显示）。不沿用 soundmanager2（模板老旧、SWF 遗留路径），listenmp3.html 保持原样不动；
- 连续播放：`ended` 事件自动下一课，列表滚动跟随；
- LRC（US2）：`lyric` 端点取文本 → 前端解析时间轴 → 随 `timeupdate` 高亮当前行、自动滚动；无歌词课显示课名兜底；
- 书签：本期不写 Calibre bookmark（音频课粒度无 CFI 语义），播放位置 localStorage 记忆"上次听到的课"，够用即可。

## 6. 备选方案对比（决策记录）

| 方案 | 结论 | 理由 |
| --- | --- | --- |
| A. magicbook 直连 MinIO（选定） | ✅ | 映射知识在 Calibre 库，播放数据归 magicbook 自治；依赖仅 +1 pip 包 +2 env 键；bucket 保持私有 |
| B. moon-well 加 NCE 端点，magicbook 代理 | ❌ | moon-well 沦为按对象名透传的 dumb proxy，课↔书映射仍需 magicbook 计算，跨两个部署单元、发版耦合 |
| C. 前缀匿名读 + 浏览器直连 MinIO | ❌ | MinIO 现仅内网 9000，需公网暴露新入口；bucket 安全策略弱化；浏览器侧 Range 直连跨域运维成本 |
| D. 本地磁盘副本直接静态服务 | ❌ | 与"入库 MinIO"诉求重复存储，两份真相 |

## 7. User Story 拆分（单线程推进）

| US | 内容 | 交付判定 |
| --- | --- | --- |
| US1 音频链路+播放核心 | manifest 生成/552 对象上传 MinIO、`cps/nce/` 四端点、详情页入口、播放页（课表/播放/seek/上下课/自动连播） | 单测（映射函数、Range 解析、白名单、manifest 缓存）绿；无头浏览器夹具截图；fnOS 发版后生产播放验证 |
| US2 LRC 同步歌词 | 歌词解析/高亮/滚动 + 兜底显示 | 同上口径，lrc 抽样课对时验证 |

## 8. 运维与发版

- MinIO 上传：本机 `mc mirror docs/temp/nce-audio/ homehttp/magicbook/nce-audio/`（内网直传，约 729MB）；上传后 `mc ls --recursive` 计数 556（552+4 manifest）核对；
- compose 变更：fnOS `docker-compose.yml` 环境变量 + `.env` 两键，与镜像重建（webhook-builder）同批发布；`minio` 依赖使镜像层多一层，构建时间影响可忽略；
- 回滚：端点集中在 `cps/nce/`，回滚 = 撤 blueprint 注册 + compose env 移除，数据对象留在 bucket 无副作用；
- 风险：MinIO 账号与 moon-well 共用（现有账户为 bucket 全权限，家内可接受；如后续收紧，用 IAM policy 限定 `magicbook/nce-audio/*` 只读）。

## 9. 验收要点（US1，细化到 AC 文档时展开）

1. 登录用户从 #92–#95 任一本书详情页进入播放页，课表数量正确（72/96/60/48 课）；
2. 任一课可播放、拖动进度（206 Range 生效）、播完自动下一课；
3. 未登录访问 `/nce/*` 全部重定向登录；伪造 num 404；
4. 非 NCE 书详情页无音频入口；
5. MinIO 停机时播放接口 503，magicbook 其余功能不受影响；
6. 公网经 Traefik 播放正常（走 15m 超时配置后的链路，与 TTS 同路径验证）。
