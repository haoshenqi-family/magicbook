# UI 信息架构与导航分组（L3 实现说明）

> 建立：2026-10-29（R251）。读者是**要改 MagicBook 顶栏、侧栏或移动导航的人**；
> 用户视角见 L1 [`product/readme/library.md`](../../readme/library.md)，
> 本次实现与取舍见 LLD
> [`project/iterations/1.0/r251-ui-ia/lld.md`](../../../project/iterations/1.0/r251-ui-ia/lld.md)。

## 1. 产品层规则

所有可测试的信息架构规则集中在 `cps/ui_ia.py`：

| 函数 | 作用 | 不应放在模板里的原因 |
| --- | --- | --- |
| `nav_domain(path, page)` | 返回唯一一级域 | 模板里第二份路径名单会与路由漂移 |
| `shelf_nav_group(name)` | 识别分级 / 媒体 / 默认书架 | 规则需要单测与安全兜底 |
| `shelf_level_sort(shelves)` | 阶号按数值排序 | 字符串排序会把阶10排在阶2前 |

`cps/jinjia.py` 只把三个函数注册为 Jinja filter。新增分类规则先改 Python，
再让模板消费，不直接在 `layout.html` 写新正则。

## 2. 唯一一级域

优先级固定为：

```text
home
learning
account
admin
library
unknown ("")
```

注意事项：

- 账号路径必须优先于书库路径：`/reading/settings` 是账号，不是阅读页。
- `/stats`、`/login` 等未知页面返回空值，不得默认成书库。
- 阅读器路径 `/read/<id>` 属于书库，用户从书目进入阅读时上下文不跳域。
- 新增页面时先在 `tests/test_home_nav_shell.py::test_r251_active_domain_has_one_owner_and_unknown_has_none`
  补归属断言，再改 `LIBRARY_PAGES`、路径前缀或账号白名单。

## 3. 侧栏分组契约

### 3.1 分级

```text
^(?:分级)?阶\s*(\d+)
```

只识别明确以“阶N / 分级阶N”开头的书架；`第一阶段` 不冒充阶 1。
同组按解析出的整数升序，规则不锚定结尾，允许“阶3 桥梁书”。

### 3.2 媒体

名称大小写不敏感，以 `TED`、`Audio`、`Listening`、`音频`、`听力` 开头。

### 3.3 默认兜底

除分级、媒体之外的用户书架全部进入 `Shelves`。模板用已分组 id 排除后取剩余集合，
使分类互相重叠或规则调整时仍不丢入口。

**不要为展示目的增加 `Shelf.kind`。** 当前分组是可解释的名称规则，不改变书目归属；
只有在出现“用户显式指定类型、组内排序、权限或跨设备稳定分类”的真实需求时再设计 schema。

## 4. 模板边界

- 主导航 `<ul>` 增加 `mb-primary-nav`，但仍沿用 Calibre 的 Bootstrap 3 骨架。
- 保留 `top_home` / `top_library` / `top_learning` / `top_me` / `top_admin`。
  onboarding 与测试依赖这些锚点。
- `current_domain` 是 active 的唯一来源；不要为每个页面再写一套 active 条件。
- Calibre 的 Browse 项仅在域为 `library` 且 page 匹配时 active。
- 移动底栏与桌面主导航使用同一个 `current_domain`，避免两套名单产生不同答案。
- 系统空组不渲染标题；CaliBlur 自己承接系统操作时隐藏 MagicBook 的系统标题。

## 5. CSS 叠层

产品样式只追加在 `cps/static/css/magicbook.css`，不改 vendored Calibre CSS。

| 问题 | 处理 |
| --- | --- |
| Bootstrap `.visible-xs` 使用 `display:block!important` | `.mb-bottom-nav.visible-xs { display:flex!important; }` |
| `ai_chat.css` 后加载，同 ID 覆盖悬浮球 bottom | `body #ai-companion-fab-wrap { bottom:64px; }` 提高一级特异度 |
| CaliBlur 给 nav-head 分配 60px | 用 `body.blur #scnd-nav#scnd-nav` 收紧高度 |
| 五域在平板宽度拥挤 | 768–1199px 缩减主导航内边距 |

遇到同 ID 覆盖时优先增加作用域或特异度，不用更晚加载的重复 ID 规则互相抢。

## 6. 测试要求

每次改动至少验证：

1. 一级域归属：目标页只有唯一 active，未知页无 active。
2. 入口守恒：分组前后书架入口数量一致。
3. 排序：`阶1 < 阶2 < 阶10`。
4. 响应式：桌面与 390px 无横向滚动，移动底栏可见。
5. 主题：至少检查默认主题与 CaliBlur。
6. 关键 DOM ID 未漂移。

```bash
pytest tests/test_home_nav_shell.py -q
```

## 7. 扩展边界

- 新增一级域前先证明它承担独立任务，且不与现有域重叠。
- 移动底栏最多四个高频入口；低频管理能力不进入底栏。
- 新分类不得静默隐藏任何既有项。
- 规则是展示层时，不顺便改模型；模型变化必须单独立需求与迁移方案。
