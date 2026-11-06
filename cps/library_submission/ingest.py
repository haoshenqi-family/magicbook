# -*- coding: utf-8 -*-

#  This file is part of the Magicbook (customized Calibre-Web).
#
#  R279 投稿入库：审核通过后把 MinIO 暂存对象解析并写入 calibre 书库。
#
#  Why 不直接调 cps/editbooks 的 create_book_on_upload：那批函数在三个地方
#  依赖请求上下文——`flash()`（需要 request 上下文）、`current_user`
#  （edit_book_languages 的 upload_mode 分支读用户语言过滤）、gettext
#  （需要 app 上下文）。后台线程里直接调会崩或行为错。这里抽出一份
#  不碰请求上下文的入库实现：
#    - 语言：元数据语言直接入库，不做「用户语言过滤换语言」的特殊分支
#      （那是 `/upload` 面向单个用户导入的体验，投稿入库没有「当前用户」语义）；
#    - 提示：所有失败都进日志与 book_submission.error_message，不 flash；
#    - 会话：调用方保证运行在 app.app_context() 内、用 calibre_db 会话实例。
#
#  边界（R78/R92/NFR-1）：不修改 cps/editbooks.py 既有函数行为；本模块
#  自带精简版 helper（作者/标签/出版社等直接 add-or-get，不做 `/upload`
#  的改名联动与目录搬移——投稿是新书目，没有旧路径要维护）。

import os
from datetime import datetime, timezone

from markupsafe import Markup

from .. import db, calibre_db, config, helper, logger, uploader, constants
from ..clean_html import clean_string
from ..string_helper import strip_whitespaces

log = logger.create()


def _get_or_create_author(name):
    author = calibre_db.session.query(db.Authors).filter(
        db.Authors.name == name).first()
    if author is None:
        author = db.Authors(name, helper.get_sorted_author(name), "")
        calibre_db.session.add(author)
        calibre_db.session.flush()
    return author


def _get_or_create_simple(db_class, name):
    row = calibre_db.session.query(db_class).filter(
        db_class.name == name).first()
    if row is None:
        row = db_class(name=name)
        calibre_db.session.add(row)
        calibre_db.session.flush()
    return row


def _get_or_create_language(lang_code):
    row = calibre_db.session.query(db.Languages).filter(
        db.Languages.lang_code == lang_code).first()
    if row is None:
        row = db.Languages(lang_code)
        calibre_db.session.add(row)
        calibre_db.session.flush()
    return row


def _attach_links(book, relationship, row):
    if row not in getattr(book, relationship):
        getattr(book, relationship).append(row)


def extract_meta(temp_path, original_filename, extension):
    """从临时文件解析元数据（uploader.process，失败回退文件名）。

    BookMeta.extension 形制为带点小写（uploader 全链以 `.ext` 传递，
    `db.Data` 落库时 `upper()[1:]` 去点）。
    """
    filename_root, _ = os.path.splitext(original_filename)
    return uploader.process(temp_path, filename_root, "." + extension.lower(),
                            config.config_rarfile_location)


def ingest_book_from_meta(meta, temp_path):
    """把解析好的 BookMeta 写入书库，返回 (db_book, error)。

    与 /upload 的 create_book_on_upload + move_coverfile + update_dir_structure
    同序，但无请求上下文依赖：
      1. 建 Books/Authors/Series/Tags/Publisher/Languages/Identifiers；
      2. 落 EPUB 等格式行（Data）；
      3. 生成书目目录并把临时文件搬进去（作者/标题目录 + get_valid_filename
         规整，与 Calibre 布局一致），封面 copy 为 cover.jpg。
    失败返回 (None, error_message)；调用方决定回滚与状态回写。
    """
    try:
        # Calibre schema 的 INSERT 触发器依赖 title_sort/uuid4 等 UDF；
        # /upload 同样在建书前显式注册（cps/editbooks.py:116）。线程作用域
        # 连接是新的，必须在本线程连接上注册一次。
        calibre_db.create_functions(config)
        title = strip_whitespaces(meta.title) or original_title(temp_path)
        author_name = strip_whitespaces(meta.author) or "Unknown"

        title_dir = helper.get_valid_filename(title, chars=96)
        author_dir = helper.get_valid_filename(author_name, chars=96)
        path = os.path.join(author_dir, title_dir).replace("\\", "/")

        try:
            pubdate = datetime.strptime((meta.pubdate or "")[:10], "%Y-%m-%d")
        except ValueError:
            pubdate = datetime(101, 1, 1)

        db_book = db.Books(title, "", helper.get_sorted_author(author_name),
                           datetime.now(timezone.utc), pubdate, "1",
                           datetime.now(timezone.utc), path, bool(meta.cover),
                           None, [], "")

        # 作者（ authors 是关联表，Book 构造器只收首作者行，链接后补）
        db_author = _get_or_create_author(author_name)
        db_book.authors.append(db_author)

        if strip_whitespaces(meta.series):
            _attach_links(db_book, "series",
                          _get_or_create_simple(db.Series,
                                                strip_whitespaces(meta.series)))
        if strip_whitespaces(meta.publisher):
            _attach_links(db_book, "publishers",
                          _get_or_create_simple(db.Publishers,
                                                strip_whitespaces(meta.publisher)))
        for tag in helper.uniq([strip_whitespaces(t)
                                for t in (meta.tags or "").split(",")]):
            if tag:
                _attach_links(db_book, "tags", _get_or_create_simple(db.Tags, tag))
        for lang_code in helper.uniq([c for c in (meta.languages or "").split(",")
                                      if c]):
            _attach_links(db_book, "languages", _get_or_create_language(lang_code))

        # 简介（与 /upload 同一净化口径）
        description = Markup(meta.description or "").unescape()
        if description:
            description = clean_string(description, 0)
        if description:
            db_book.comments.append(db.Comments(comment=description, book=db_book))

        # 格式行
        file_size = os.path.getsize(temp_path)
        db_data = db.Data(db_book, meta.extension.upper()[1:], file_size, title_dir)
        db_book.data.append(db_data)
        calibre_db.session.add(db_book)
        calibre_db.session.flush()

        # 标识符
        for type_key, type_value in meta.identifiers or []:
            calibre_db.session.add(db.Identifiers(type_value, type_key, db_book.id))

        # 书目目录：把临时文件搬进 书库/<author>/<title>/，文件名与 Calibre
        # 布局一致（title - author.ext）。目标目录已存在时加 book id 后缀，
        # 避免同名书互覆盖。
        book_path = os.path.join(config.get_book_path(), path)
        if os.path.exists(book_path):
            suffix = " ({})".format(db_book.id)
            title_dir = helper.get_valid_filename(title, chars=96) + suffix
            path = os.path.join(author_dir, title_dir).replace("\\", "/")
            db_book.path = path
            db_data.name = title_dir
            book_path = os.path.join(config.get_book_path(), path)
        os.makedirs(book_path, exist_ok=True)
        stored_name = helper.get_valid_filename(
            u"{} - {}".format(title, author_name), chars=90)
        os.replace(temp_path, os.path.join(book_path, stored_name + "." +
                                           meta.extension.lower().lstrip(".")))

        # 封面
        if meta.cover and os.path.exists(meta.cover):
            try:
                from shutil import copyfile
                copyfile(meta.cover, os.path.join(book_path, "cover.jpg"))
                os.unlink(meta.cover)
                db_book.has_cover = 1
            except OSError as cover_error:
                log.warning("submission ingest: cover copy failed for book %s: %s",
                            db_book.id, cover_error)

        calibre_db.set_metadata_dirty(db_book.id)
        calibre_db.session.commit()
        helper.add_book_to_thumbnail_cache(db_book.id)
        return db_book, None
    except Exception as ingest_error:  # noqa: BLE001 —— 入库失败必须可见，不能静默
        log.error("submission ingest failed: %s", ingest_error)
        try:
            calibre_db.session.rollback()
        except Exception:
            pass
        return None, str(ingest_error)


def original_title(temp_path):
    return os.path.splitext(os.path.basename(temp_path))[0] or "Unknown"


def allowed_submission_extensions():
    """投稿白名单：与 `/upload` 的 config_upload_formats 同源（站点可配），
    并收紧掉音频/视频（EXTENSIONS_AUDIO 及 mp4 等）——投稿只收书。
    """
    audio = set(constants.EXTENSIONS_AUDIO) | {"mp4"}
    return [e for e in config.config_upload_formats.split(",") if e and e not in audio]
