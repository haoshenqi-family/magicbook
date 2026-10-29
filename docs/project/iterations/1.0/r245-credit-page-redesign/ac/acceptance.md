# R245 验收标准

状态：待验收（2026-10-29）
PingCode：需求 MB-235、缺陷 MB-21（`xn-uxsjb`）。

| # | 场景 | 期望 |
| --- | --- | --- |
| A1 | 普通用户打开 `/credits` | 看到充值、积分卡、明细三个任务页签；余额 Hero 快捷按钮可切换 |
| A2 | 管理员打开 `/credits` | 额外看到管理页签；管理内分为积分调整、充值活动、批量发卡 |
| A3 | 分享卡密进入积分页 | 自动切到积分卡页签，兑换框已填入卡密 |
| B1 | 管理员选择带秒的 `datetime-local` 并发布 | POST 请求为 `yyyy-MM-dd HH:mm:ss`，不再返回 400 |
| B2 | 管理员选择不带秒的 `datetime-local` 并发布 | 缺省秒补 `00`，发布成功 |
| B3 | 发布失败 | `#credit-promo-feedback` 行内红字显示上游 message，表单值保留 |
| B4 | 发布成功 | 行内绿字显示成功，活动和充值档位刷新 |
| C1 | 明细含获取记录 | 获取徽标为深绿字、浅绿底、可见边框；金额为深绿粗体 |
| C2 | 明细含消耗记录 | 消耗徽标为深褐字、琥珀底、深琥珀边框；金额为深褐粗体 |
| C3 | 普通行与条纹行 | 两种背景上均能辨认方向徽标和金额，不依赖内联浅色 |
| D1 | 非管理员直接 POST 管理代理 | Flask 返回 403，且不触达 moon-well |
| D2 | 活动时间以 ISO 或空格格式到达 moon-well | R229 字段级反序列化均按东八区墙上时间解析，不改全局 Jackson 契约 |

## 自动验证

```bash
../magicbook/.venv/bin/python -m pytest \
  tests/test_credit_page_r245.py tests/test_credit_card.py \
  tests/test_credit_consume.py tests/test_i18n_seed_contract.py -q
node --check cps/static/js/credits.js
git diff --check
```
