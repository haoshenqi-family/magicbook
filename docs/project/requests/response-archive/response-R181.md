# response 归档 · R181

### R181（架构评审波 3 · B2 小步重做完成：web.py 蓝图分域拆分）

- **交付（commit `3211f600`，分支 `refactor/r178-moonwell-client`（同分支第五 commit），已 merge 本地 develop）**：94 条定制路由分四批迁出（每批后全量 pytest）——cps/routes/reading.py（28 段 470 行）/credit.py（19 段 227 行）/vocab.py（9 段 146 行）/learning.py（38 段 432 行），全部 <1000 行；**web.py 3304→2299 行**（定制路由清零回归原版形状，上游 merge 冲突面下降；留守 42 条原版路由与辅助函数为上游同款，原版巨石拆分属上游范畴）。getcomic 死字符串块同步清除（路由激活，R180 前置的连带完成）。
- **装配**：延迟注册（web.py 末尾 register_domain_routes(web)，全部辅助符号定义后）；装饰注册沿用原 web blueprint——**endpoint 名不变，url_for/模板/前端/测试零改动**；routes 子包内相对导入升两级。
- **验证**：每批迁移后全量 pytest（reading 2 处桩点配套后全绿；credit/vocab/learning 各一次过）；**endpoint 集合前后比对 133 无丢失**（get_comic_book 为死块激活的预期新增）；四域文件全部 <1000 行；两处配套适配——test_reading_tts 桩点迁 routes 模块属性（whole_book_tts_service 值拷贝绑定），test_llm_task_run 的 hasattr 代理断言改为 endpoint 注册断言（url_for 依赖 url_map 而非模块属性）。
- **台账**：worktree `../magicbook-arch-b5` 同树多阶段（r177→r178→r179 尝试撤销→r180→r181），merge 后驻留待验收；真机验收点：阅读页全链路（划词/翻译/TTS/批注/伴读）、每日学习七子页、积分充值/订阅、词汇量测试、LLM 任务面板、漫画页（新激活）。未 push。
- **总结**：requests.md 占号 R181；冲突记录：无。上轮 R179 的四类坑均已按留存方案规避/修复。
