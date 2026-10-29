"""MagicBook-owned navigation information architecture helpers.

Keep presentation rules here instead of the vendored Calibre-Web modules.
The template only consumes stable group / active-domain values.
"""

import re


LEVEL_SHELF_RE = re.compile(r'^(?:分级)?阶\s*(\d+)')
MEDIA_SHELF_PREFIXES = tuple(
    prefix.casefold() for prefix in ('TED', 'Audio', 'Listening', '音频', '听力')
)

LIBRARY_PAGES = frozenset([
    'advsearch', 'archived', 'author', 'authorlist', 'book', 'book_table',
    'catlist', 'category', 'discover', 'download', 'downloadlist', 'formats',
    'formatslist', 'hot', 'langlist', 'language', 'newest', 'publisher',
    'publisherlist', 'rated', 'ratings', 'ratingslist', 'read', 'search',
    'series', 'serieslist', 'shelf', 'shelfcreate', 'shelfedit', 'shelforder',
    'unread',
])
LIBRARY_PATH_PREFIXES = ('/advsearch', '/book/', '/read/', '/search', '/shelf/')
ACCOUNT_PATH_PREFIXES = (
    '/achievements', '/buddy', '/credits', '/mail', '/me', '/reading/settings',
)


def shelf_nav_group(name):
    """Return one of ``shelves`` / ``levels`` / ``media`` for sidebar display."""
    value = (name or '').strip()
    if LEVEL_SHELF_RE.match(value):
        return 'levels'
    if value.casefold().startswith(MEDIA_SHELF_PREFIXES):
        return 'media'
    return 'shelves'


def shelf_level_sort(shelves):
    """Sort level shelves numerically, so 阶2 stays before 阶10."""
    def sort_key(shelf):
        name = (shelf.name or '').strip()
        match = LEVEL_SHELF_RE.match(name)
        level = int(match.group(1)) if match else 10 ** 9
        return level, name.casefold()

    return sorted(shelves, key=sort_key)


def nav_domain(path, page):
    """Return the single primary navigation domain owning the current route."""
    path = path or ''
    page = page or ''
    if page == 'home' or path == '/home':
        return 'home'
    if path == '/learning' or path.startswith('/learning/'):
        return 'learning'
    if path in ACCOUNT_PATH_PREFIXES or path.startswith(
            tuple(prefix + '/' for prefix in ACCOUNT_PATH_PREFIXES)):
        return 'account'
    if path == '/admin' or path.startswith('/admin/'):
        return 'admin'
    if page in LIBRARY_PAGES or path.startswith(LIBRARY_PATH_PREFIXES):
        return 'library'
    return ''
