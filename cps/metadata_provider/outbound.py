# -*- coding: utf-8 -*-
"""Metadata provider outbound requests: domain-routed proxy + enforced timeouts.

Why this module exists (R87/R88, 2026-09-28):

* The fnOS LAN has no route to Google. A bare ``requests.get`` to
  ``www.googleapis.com`` used to hang forever, which froze the two
  ``ThreadPoolExecutor`` workers behind ``/metadata/search`` and — because
  that Flask view runs inside the Tornado IOLoop thread — took the whole
  site down (all of :8083 stopped answering while the container still
  reported healthy via a TCP-only ``nc -z`` healthcheck).
* The LAN has a proxy that CAN reach Google (e.g. 192.168.31.11:12811),
  but it must only be used for Google traffic — Douban/Amazon/ComicVine/
  LubimyCzytac must stay direct.

Contract for every metadata provider:

1. Route by host: hosts under the Google suffixes below go through the
   ``METADATA_GOOGLE_PROXY`` (if configured); everything else is forced
   direct (``proxies={'http': None, 'https': None}``) so that leaked
   ``http_proxy``/``https_proxy`` environment variables can never silently
   reroute non-Google traffic through the proxy.
2. Never wait unbounded: ``timeout`` is enforced (callers may tighten it,
   never remove it).
"""
import os
from urllib.parse import urlsplit

import requests

# Environment variable holding the Google-only HTTP proxy, e.g.
# "http://192.168.31.11:12811". Empty/unset means Google requests also go
# direct (fine on networks that can reach Google).
GOOGLE_PROXY_ENV = "METADATA_GOOGLE_PROXY"

# Host suffixes considered "Google related": these go through the proxy.
# scholar.google.com (used by the scholarly package) matches "google.com".
_GOOGLE_HOST_SUFFIXES = (
    "googleapis.com",
    "google.com",
    "googleusercontent.com",
    "gstatic.com",
)

# Default (connect, read) timeout in seconds. Connect stays short so an
# unroutable source is abandoned quickly; read is generous for slow sources.
DEFAULT_TIMEOUT = (5, 30)

# Explicit "no proxy" mapping: pinning None defeats leaked http_proxy /
# https_proxy environment variables (requests would trust them otherwise).
DIRECT_PROXIES = {"http": None, "https": None}


def _host(url):
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def is_google_url(url):
    """True when the URL points at a Google-related host (proxy candidate).

    Match on domain-label boundaries: ``notgoogle.com`` must NOT count as
    Google, so a bare ``endswith`` is not enough.
    """
    host = _host(url)
    return any(host == suffix or host.endswith("." + suffix)
               for suffix in _GOOGLE_HOST_SUFFIXES)


def _proxies_for(url):
    if not is_google_url(url):
        # Why explicit None: requests trusts http_proxy/https_proxy env vars
        # by default; pinning None guarantees "non-Google stays direct".
        return DIRECT_PROXIES
    proxy = google_proxy()
    if not proxy:
        return DIRECT_PROXIES
    return {"http": proxy, "https": proxy}


def google_proxy():
    """Configured Google-only proxy URL (empty string when unset/disabled)."""
    return os.environ.get(GOOGLE_PROXY_ENV, "").strip()


def request(method, url, timeout=DEFAULT_TIMEOUT, **kwargs):
    """``requests.request`` with domain routing and an enforced timeout.

    ``timeout=None`` is rejected on purpose — passing it would reopen the
    unbounded-wait window that caused the R87 site freeze.
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    return requests.request(method, url, timeout=timeout,
                            proxies=_proxies_for(url), **kwargs)


def get(url, timeout=DEFAULT_TIMEOUT, **kwargs):
    return request("GET", url, timeout=timeout, **kwargs)


def post(url, timeout=DEFAULT_TIMEOUT, **kwargs):
    return request("POST", url, timeout=timeout, **kwargs)
