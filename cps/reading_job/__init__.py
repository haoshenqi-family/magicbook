"""整本批次链路的公共骨架（架构评审 B6）。

`reading_translation` / `reading_tts` / `reading_word_detail` 三条链路共用同一形制的
job/item 台账，公共方法此前是三份拷贝（R166 设计 §3.1 明确「镜像
WholeBookTranslationService 骨架」，R176 又照抄一次）。本包只收**已被多份实现证明逐字
相同**的部分；各家差异（进度口径、item 状态机、worker 循环内容）留在自己的 service 里。

这里刻意不做 re-export：三个调用方都是 `from ..reading_job.service_base import JobServiceBase`
按模块路径取，包级 eager import 只会让「导入本包」连带拉起台账模型与 `ub`。
"""
