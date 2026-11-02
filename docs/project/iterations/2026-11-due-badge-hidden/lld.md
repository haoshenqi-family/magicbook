# LLD — R266 学习入口待复习角标 hidden 失效（「红横杠」缺陷修复）

> 状态：已开发待验收（2026-11-02）
> 来源：用户原话「学习的主入口后边为什么有一个红色的横岗？」（2026-11-02）。首次排查误判为「无缺陷」，用户「再处理一下」后复检发现是真缺陷。

## 1. 现象与根因

「学习」一级导航入口（顶栏 `#top_learning` 与移动底栏同款）右侧常驻一条**空红色横杠**（无数字）。用户看到的就是它。

根因是一类已知的 CSS 坑（learning.html:261-263 注释点名的「R140 同款坑」）：HTML `hidden` 属性的 UA 样式 `[hidden] { display: none }` 位于用户代理样式表，特异性低于**作者样式表里的任何 display 声明**。R261 的角标基准规则 `.ln-due-badge { display: inline-block; … }`（magicbook.css:363）恰好声明了 display，于是模板里的 `hidden` 属性被顶掉——默认关闭（且 never 注入数字）的角标按 inline-block 渲染：`min-width:17px + padding 1px 5px + background #d9534f` 的胶囊里没有任何文字，视觉上就是「学习」入口后面的一条红色横杠。

而显示路径是好的：layout.html 的角标脚本与 learning-hub.js 保存钩子都走 `MBDueBadge`/`render()`，给 `el.textContent` 赋数字后 `el.hidden = false`。R261 静态锁只锁了镜像判关与缓存键（test_r261_jinshu_borrow.py），没有锁 CSS 基准态，所以单测全绿、页面上却常驻红杠。

## 2. 修法（cps/static/css/magicbook.css）

基准态改 `display: none`，新增非 hidden 态恢复规则：

```css
.ln-due-badge { display: none; …其余视觉声明不变… }
.ln-due-badge:not([hidden]) { display: inline-block; }
```

三条路径逐一对齐：

1. **默认关（缺陷态）**：span 带 `hidden` → `display:none`，红杠消失。这是本次修复的主目标。
2. **JS 显示**：`render()` 赋数字 + `hidden=false` → `:not([hidden])` 命中，inline-block 恢复。
3. **JS 再隐藏**：`MBLearning.show()`（learning-common.js:32-36）写 `el.hidden=true` 且同步 `style.display='none'`，内联样式压过作者规则，隐藏路径本就正确，不受影响。

`.mb-bottom-item .ln-due-badge` 的绝对定位规则不改（只覆盖定位属性，不涉及显隐）。

## 3. 守卫与回归

- 新增静态锁 `test_badge_css_基准态隐藏且非hidden才显示`（tests/test_r261_jinshu_borrow.py）：钉住基准块 `display: none`、`:not([hidden])` 恢复 inline-block、基准块不得回写 inline-block（根因回归即报红）。
- 定向回归：`test_r261_jinshu_borrow + test_nav_settings_dropdown + test_home_nav_shell + test_learning_hub_cards + test_learning_pages_static` 共 **97 passed**。

## 4. 视觉验证（真实页面渲染 + 无头 Chrome）

- 渲染：Flask test client 登录态 GET `/learning`（200），产物 `page.html`；分别配 origin/develop 的 magicbook.css（旧）与本轮 magicbook.css（新），headless Chrome 1440×900 截图。
- 数值判定（bootstrap `#d9534f` 强红像素）：导航条区域（y<100）旧版 34 红像素（bbox x838-854，即空角标），新版 **0**。
- 证据图（assets/）：`nav_compare.png`（上旧下新局部放大）、`old_full.png` / `new_full.png`（整页对照）。

## 5. 边界与不做

- 不改角标的开关语义（R261 原口径：学习抽屉「复习小件」勾选 + dueNow>0 才显示）、不改镜像键、不改 moon-well 接口。
- 「红杠」若出现在其它页面元素（如后端不可达的 alert-danger 报错条），那是另一个现象；本轮只修 R261 角标这一处实证缺陷。
