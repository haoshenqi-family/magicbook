"""magicbook 内部导入 API 客户端：5xx/超时指数退避重试，4xx 不重试。"""
import time

import requests


class MagicbookError(RuntimeError):
    def __init__(self, message, status=None, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload or {}


class MagicbookClient:
    def __init__(self, base_url, key, timeout=120, retries=3):
        self.base = base_url.rstrip("/")
        self.key = key
        self.timeout = timeout
        self.retries = retries

    def import_book(self, book_id, epub_path, cover_bytes=None,
                    trigger_translation=True, source_ref=None):
        data = {"book_id": str(book_id),
                "trigger_translation": "true" if trigger_translation else "false"}
        if source_ref:
            data["source_ref"] = source_ref
        last_error = None
        for attempt in range(self.retries):
            # 每次重试重新打开文件句柄（上一轮已被读尽）
            files = {"file": ("book.epub", open(epub_path, "rb"),
                              "application/epub+zip")}
            if cover_bytes:
                files["cover"] = ("cover.jpg", cover_bytes, "image/jpeg")
            try:
                resp = requests.post(
                    self.base + "/api/internal/book-import",
                    headers={"X-Connector-Key": self.key},
                    files=files, data=data, timeout=self.timeout)
            except requests.RequestException as exc:
                last_error = MagicbookError(f"request failed: {exc}")
                time.sleep(2 ** attempt)
                continue
            finally:
                for f in files.values():
                    f[1].close()
            if resp.status_code == 502:
                # 文件已替换成功，仅翻译触发失败：不重试，交由上层降级告警
                raise MagicbookError(
                    f"imported but translation failed: {resp.text[:200]}",
                    status=502, payload=self._safe_json(resp))
            if resp.status_code < 500:
                if resp.status_code != 200:
                    raise MagicbookError(
                        f"import rejected: {resp.text[:500]}",
                        status=resp.status_code,
                        payload=self._safe_json(resp))
                return self._safe_json(resp)
            last_error = MagicbookError(
                f"server error {resp.status_code}: {resp.text[:200]}",
                status=resp.status_code, payload=self._safe_json(resp))
            time.sleep(2 ** attempt)
        raise last_error

    @staticmethod
    def _safe_json(resp):
        try:
            return resp.json()
        except ValueError:
            return {}
