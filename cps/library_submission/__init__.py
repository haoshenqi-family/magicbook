# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  cps/library_submission — R279 用户投稿域（暂存 + 审核 + 入库）。
#
#  Why 独立包而不是塞进 editbooks：投稿链路与上游 Calibre-Web 的 `/upload`
#  是两条完全不同的权限模型（前者登录即可、写 MinIO 暂存；后者要求
#  ROLE_UPLOAD、直写书库）。独立包把「暂存不碰书库」这条边界固化在目录
#  层面，防止后人把两链路的校验互相抄坏。
