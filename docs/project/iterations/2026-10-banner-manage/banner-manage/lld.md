# 每日学习 banner 小功能管理（magicbook R208 / moon-well R203）· magicbook 侧 LLD

状态：开发中（2026-10-22，随本轮 merge develop，待用户验收）

## 需求一句话与拍板口径

用户可自由勾选哪些学习小功能出现在每日学习中枢 banner 轮播里，不勾选的不出现；
目标是减少选择成本。三项拍板（2026-10-22）：勾选存 moon-well 账号级、banner 齿轮
抽屉管理、允许全不勾 + 引导卡兜底。存储与契约设计见 moon-well 侧 LLD（同目录名
`2026-10-banner-manage/banner-manage/lld.md`），本文件只写 magicbook 侧实现。

## 交互设计

- **入口**：`#lh-banner` 右上角齿轮按钮（`.lh-manage-btn`，aria-haspopup/aria-expanded/
  aria-controls 全套），点击开合 `#lh-manage` 抽屉（banner 下方 panel，非模态），Esc 可关。
- **抽屉**：服务端渲染七个复选框（data-key 与功能卡一一对应，行序=卡片模板序），
  出厂全勾=默认全显；真实勾选态由 JS 在打开时回填。保存/关闭按钮 + 预填兜底文案的
  错误行（保存失败必须可见，优先展示上游业务文案）。
- **引导卡**：`#lh-guide` 放在 banner viewport 内，无 lh-card 类不进轮播数组；
  可见卡数为 0 时显示，按钮直接开抽屉——全不勾状态自愈回管理入口。
- **裁剪语义**：`learning-hub.js` 维护主列表 `cards`（七张 `a.lh-card`）与可见列表
  `visible`（按 hiddenKeys 过滤）；轮播/圆点/prev/next/缺口排序全部只看 visible。
  被隐藏的卡留在 DOM（display:none）——服务端始终渲染七张，`test_learning_hub_cards`
  的八卡契约只需把 data-key 正则锚定到 `<a class="lh-card>`（契约本身不变）。

## 勾选状态的读取与对账（首屏零上游调用不破）

1. **镜像先行**：JS 启动时同步读 `localStorage['ln-banner-hidden-v1']`（JSON 数组，
   过滤到已知 key，坏数据当未配置），在首帧前 applyVisibility——消除「plan 回来前
   先全显再隐藏」的闪现。
2. **服务端对账**：`plan/today` 的 `settings.bannerHiddenKeys`（R208 起随既有异步
   响应顺路带回，不加新请求、不破 R166 零上游调用纪律）到达后 reconcile：
   与当前态不一致才应用并回写镜像——服务端是真相，跨设备改动被对齐。
3. **降级**：字段缺失（旧后端）→ 保留镜像不做对账，功能退化为本机偏好但不报错；
   localStorage 不可用（隐私模式）→ 读写全部 try/catch 吞掉，功能走服务端真相。

## 保存流程

- 勾选态 → `hiddenList`（未勾的 key）；payload = 既有四股设置（来自 `lastPlan.settings`，
  缺失时补拉一次 `plan/today`；拼不出完整底稿就可见报错——宁可不保存也不拿猜的默认值
  盖掉用户已存的四股配比）+ `bannerHiddenKeys: hiddenList`。
- POST `/ajax/learning/plan/settings`（既有代理），成功后更新本地态 + 镜像 +
  applyVisibility + 关抽屉；失败（HTTP/业务/网络）→ busy 复位 + 错误行可见。
- 空数组=显式全显必须原样透传（代理与上游契约，见 L2）。

## 改动清单（本仓）

- `cps/templates/learning.html`：齿轮 + 引导卡 + 抽屉标记 + CSS（`.lh-guide` 基态
  `display:none`、`:not([hidden])` 才 flex——作者 display 会压过 UA `[hidden]`，R140
  同款坑）+ `learningUrls.settings` 注入。
- `cps/static/js/learning-hub.js`：cards/visible 双列表、hiddenKeys + 镜像 + 对账、
  applyVisibility、抽屉与保存逻辑；轮播/圆点/缺口排序改走 visible。
- `cps/routes/learning.py`：`learning_plan_settings` 代理增 `bannerHiddenKeys` 形制
  校验（`[a-z]{2,32}`、≤10，本地 400 镜像上游）与透传（字段缺失不重建——null 语义
  归上游）。
- `cps/translations/zh_Hans_CN/LC_MESSAGES/messages.po`：7 条新词条（管理标题、
  抽屉说明、引导卡两句、保存失败兜底文案、Save/Close）+ pybabel compile。
- JS 零新增 mbT 字面量（文案全部服务端渲染或复用上游 message）——i18n 种子不动。

## 测试

- `tests/test_learning_banner_manage.py`（新）：抽屉七复选框与卡片同序、齿轮/保存/
  关闭接线、出厂全勾、引导卡默认隐藏、settings 路由注入、新词条 .mo 可取中文。
- `tests/test_learning_hub_cards.py`：七卡顺序正则锚定 `<a class="lh-card>`（R208 起
  data-key 也出现在抽屉复选框上；八卡契约本身不变）。
- `tests/test_learning_proxy.py`：banner 勾选转发、空列表透传、形制违例本地 400、
  老客户端不带字段转发体不变。
- 开发态闸门（2026-10-22 本机实测）：pytest
  `test_learning_proxy.py test_learning_banner_manage.py test_learning_hub_cards.py
  test_learning_pages_static.py test_nav_settings_dropdown.py test_i18n_seed_contract.py`
  全绿（数字见 response.md 回填）。

## 兼容与部署

- 上线顺序：moon-well 先（加列向后兼容），本仓随后。
- 本仓先上 × 旧后端：moon-well `WebConfig` 显式关闭 FAIL_ON_UNKNOWN_PROPERTIES，
  新字段被静默忽略——保存返回成功但勾选不落库，本机镜像兜底当会话内偏好，
  moon-well 上线后自动变为账号级。降级可见（跨设备不一致），功能不报错。
- 真机验收点：齿轮开合、勾选裁剪即时生效、刷新与跨设备一致、全不勾引导卡回入口、
  保存失败报错可见、移动端抽屉可用。
