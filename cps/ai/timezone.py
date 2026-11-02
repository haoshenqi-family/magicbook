"""AI 模块统一时区：中国大陆时区（Asia/Shanghai，UTC+8）。

为什么返回 naive 的北京时间而非带时区对象：
- 业务面向中文读者，会话/消息时间按北京时间展示最直观。
- MySQL DATETIME 无时区，PyMySQL 序列化 aware datetime 时会转成 UTC 存储，
  而 SQLite 的存储行为不同；为让两种存储下的落库值一致且就是北京时间
  墙钟时间，这里统一返回 ``naive`` 的北京时间。
"""
import pytz
from datetime import datetime

CN_TZ = pytz.timezone("Asia/Shanghai")


def now():
    """当前中国大陆时间（北京时间，UTC+8），naive datetime。"""
    return datetime.now(CN_TZ).replace(tzinfo=None)
