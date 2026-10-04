# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  新概念英语课级音频播放（R116③，LLD：docs/feat/nce-audio/design/lld.md）。
#  所有 nce 代码集中于此子包，与上游 calibre-web 隔离；回滚 = 撤销 main.py 的
#  蓝图注册。__init__ 不做任何重导入，纯映射函数（series）可在蓝图未注册时
#  被 web.py 安全引用。
