"""slug → 书籍映射配置（V1 静态 YAML，见 LLD §3.2）。"""
import yaml


class Mapping:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self.books = {b["slug"]: b for b in data.get("books", [])}

    def get(self, slug):
        entry = self.books.get(slug)
        if not entry:
            return None
        return {
            "slug": slug,
            "book_id": int(entry["book_id"]),
            "title": entry.get("title", ""),
            "creator": entry.get("creator", "Magicbook Family Team"),
            "lang": entry.get("lang", "en"),
            "identifier": entry.get(
                "identifier", f"urn:uuid:connector-book{entry['book_id']}"),
            "trigger_translation": bool(entry.get("trigger_translation", True)),
            "cover_slug": entry.get("cover_from_post", False),
        }
