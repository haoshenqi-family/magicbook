"""Bark 通知（复用家族 BARK_KEY 惯例；未配置则静默跳过）。"""
import urllib.parse

import requests

BASE = "https://api.day.app/"


def notify(title, body, bark_key=None):
    if not bark_key:
        return
    url = BASE + urllib.parse.quote(bark_key) + "/" + \
        urllib.parse.quote(title) + "/" + urllib.parse.quote(body)
    try:
        requests.get(url, timeout=10)
    except requests.RequestException:
        pass
