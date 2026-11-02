# R239 全文单词详解预览屈折词覆盖漏算 · LLD

> 状态：**开发中**（跨仓根因已由 moon-well R226 修复，本仓文档与验收口径已更新，待上游上线）
> 工作项：R239 · 迭代 1.0
> 用户反馈：「这个计算不对，完全没有考虑曲折变形。」其中“曲折”按“屈折”理解。

## 1. 结论

R238 已完成“后台计算 + 页面轮询 + READY 快照”，但预览数字来自 moon-well
`cached-check`。后者的全索引扫描只投影 `forms.form`、漏掉 `forms.type`，因此
`books / children / going / beasts / witches / revolting` 等已由词目文档覆盖的屈折形式
仍被列为缺失。

这不是 book 145 的单书问题，也不是 magicbook worker 失败：缓存键集合是全局词库视图，
所有含屈折形式的书都会被高估待生成量。

## 2. 责任边界与修复

修复主责在 moon-well R226：

```text
WordDetailService.cachedLookupKeys()
  _source: lemma, word, forms.form
        -> lemma, word, forms.form, forms.type
```

`collectLookupKeys()` 继续只收七类屈折：过去式 / 过去分词 / 现在分词 / 三单 / 复数 /
比较级 / 最高级；派生词不借父词目文档。

magicbook 本轮**零代码改动**：

- 不复制屈折/派生判定；
- 不修改 2000 词分批；
- 不修改快照与 worker；
- 不新增任何生成调用。

## 3. 快照与部署顺序

1. 先部署 moon-well R226；
2. 再用管理员会话请求 `POST /ajax/word-detail-preview`，
   参数 `{book_id:145, book_format:"epub", force:true}`；
3. 等状态从 `RUNNING/CHECKING` 进入 `READY`；
4. 核对缺失样例会随正文首次出现顺序变化，重点断言上述六个代表词不在列表中；
5. 记录新的 `cachedWords / targetWords`。

READY 默认复用 10 分钟；不 force 时可能暂时看到旧快照，属缓存 TTL，不是二次计算错误。
`start()` 也只在 READY 新鲜时复用 `missing_json`，上游部署与验收之间必须强制刷新。

## 4. 测试与文档

本仓无功能代码，保留既有预览链路定向回归作为无回归证据：

```bash
../magicbook/.venv/bin/python -m pytest \
  tests/test_word_detail_batch_r176.py tests/test_job_service_base.py
```

- L2 `vocabulary/interface.md`：补充覆盖率权威与 force 刷新；
- L3 `vocabulary/features/word-detail-preview.md`：补充上游算法更新后的快照边界；
- 需求基线 `vocabulary/requirements.md`：新增 R239；
- R238 LLD 仅加“R226 后续修复”注记，不改写当时范围。

## 5. 驻留

- worktree：`../magicbook-r239-word-detail-inflection`
- 分支：`fix/r239-word-detail-inflection`
- R238 worktree `../magicbook-r238-word-detail-preview` 原样保留，不复用于 R239。
