#!/usr/bin/env python3
"""R214 子项 A：存量书目语言补正（dry-run 默认，--apply 才写库）。

Why: 导入侧「读全 dc:language」（cps/epub.py）只对新导入生效，存量书目（尤其
     双语书虫批次）库里可能只有一条语言声明，页面因此只能显示单语——但页面
     「不猜」（拍板⑤），补齐数据是唯一正解。写库是书库数据变更，遵循家族
     「扫描=只出报告」纪律：默认只读出清单，--apply 显式执行且执行前自动备份
     metadata.db；任何情形不改 EPUB 文件本身。

用法：
  python3 scripts/backfill_languages.py                   # dry-run：只出差异清单
  python3 scripts/backfill_languages.py --ids 337,336     # 只看/只改指定书目
  python3 scripts/backfill_languages.py --apply           # 备份 metadata.db 后写库
  python3 scripts/backfill_languages.py --db /path/metadata.db --library /path

输出三列（只列有差异的）：book_id | 现状 | OPF 声明
"""
import argparse
import os
import re
import shutil
import sqlite3
import sys
import time
import zipfile

from lxml import etree

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from cps.isoLanguages import get_lang3  # noqa: E402  需先插仓库根再导入

_NS = {
    'n': 'urn:oasis:names:tc:opendocument:xmlns:container',
    'pkg': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}


def opf_languages(epub_path):
    """读 EPUB 内全部 dc:language → lang3 去重保序列表（与 cps/epub.py 同口径）。"""
    with zipfile.ZipFile(epub_path) as zf:
        container = etree.fromstring(zf.read('META-INF/container.xml'))
        rootfiles = container.xpath('/n:container/n:rootfiles/n:rootfile/@full-path', namespaces=_NS)
        if not rootfiles:
            return []
        opf_path = rootfiles[0]
        tree = etree.fromstring(zf.read(opf_path))
        codes = []
        for raw in tree.xpath('/pkg:package/pkg:metadata/dc:language/text()', namespaces=_NS):
            code = get_lang3((raw or '').strip().split('-', 1)[0].lower())
            if code and code not in codes:
                codes.append(code)
        return codes


def current_languages(conn, book_id):
    rows = conn.execute(
        "SELECT l.lang_code FROM books_languages_link bll "
        "JOIN languages l ON l.id = bll.lang_code WHERE bll.book = ? ORDER BY l.lang_code",
        (book_id,)).fetchall()
    return [r[0] for r in rows]


def diff_languages(current, opf):
    """对账：集合不同才算差异（顺序无关）。"""
    return sorted(current) != sorted(opf)


def _epub_file(conn, library_root, book_id):
    row = conn.execute("SELECT path, format FROM books b JOIN data d ON d.book = b.id "
                       "WHERE b.id = ? AND UPPER(d.format) = 'EPUB'", (book_id,)).fetchone()
    if not row:
        return None
    return os.path.join(library_root, row[0])


def main():
    ap = argparse.ArgumentParser(description="存量书目语言补正（dry-run 默认）")
    ap.add_argument("--db", default=os.path.join(REPO_ROOT, "library", "metadata.db"))
    ap.add_argument("--library", default=os.path.join(REPO_ROOT, "library"))
    ap.add_argument("--ids", default="", help="逗号分隔 book_id，缺省全库")
    ap.add_argument("--apply", action="store_true", help="真正写库（默认只出清单）")
    args = ap.parse_args()

    ids = [int(x) for x in re.findall(r"\d+", args.ids)] if args.ids else None
    conn = sqlite3.connect(args.db)
    try:
        sql = "SELECT id, path FROM books"
        params = ()
        if ids:
            sql += " WHERE id IN ({0})".format(",".join("?" * len(ids)))
            params = tuple(ids)
        books = conn.execute(sql, params).fetchall()

        changes = []
        for book_id, _path in books:
            epub = _epub_file(conn, args.library, book_id)
            if not epub or not os.path.exists(epub):
                continue
            try:
                opf = opf_languages(epub)
            except Exception as ex:  # 解析失败只记不改，绝不因单本中断全库
                print("{0}\t<解析失败: {1}>\t-".format(book_id, ex))
                continue
            cur = current_languages(conn, book_id)
            if diff_languages(cur, opf):
                changes.append((book_id, cur, opf))

        for book_id, cur, opf in changes:
            print("{0}\t{1}\t{2}".format(book_id, ",".join(cur) or "-", ",".join(opf) or "-"))
        print("---\n差异 {0} 本{1}".format(
            len(changes), "（已写库）" if args.apply else "（dry-run，未写库；--apply 才执行）"))

        if not args.apply or not changes:
            return 0

        backup = "{0}.bak-{1}".format(args.db, time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(args.db, backup)
        print("已备份 metadata.db -> {0}".format(backup))
        for book_id, _cur, opf in changes:
            conn.execute("DELETE FROM books_languages_link WHERE book = ?", (book_id,))
            for code in opf:
                row = conn.execute("SELECT id FROM languages WHERE lang_code = ?", (code,)).fetchone()
                lang_id = row[0] if row else conn.execute(
                    "INSERT INTO languages (lang_code) VALUES (?)", (code,)).lastrowid
                conn.execute(
                    "INSERT INTO books_languages_link (book, lang_code) VALUES (?, ?)",
                    (book_id, lang_id))
        conn.commit()
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
