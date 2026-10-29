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
ADMIN_PATH_PREFIXES = (
    '/translate-all', '/word-detail-batch', '/llm-tasks',
)

# One L2 page carries one task.  These definitions are product-owned navigation
# metadata: routes and Calibre pages stay where they are, while the layout uses
# the same source of truth for labels, grouping and the single active item.
ACCOUNT_L2_GROUPS = (
    ('身份与连接', (
        {'id': 'account-profile', 'label': '资料与身份',
         'endpoint': 'web.profile', 'matches': ('/me',)},
        {'id': 'account-buddy', 'label': '伙伴与 AI 伴读',
         'endpoint': 'web.buddy_page', 'matches': ('/buddy',)},
        {'id': 'account-mail', 'label': '站内信',
         'endpoint': 'web.mail_inbox_page', 'matches': ('/mail', '/mail/')},
    )),
    ('阅读与记录', (
        {'id': 'account-reading', 'label': '阅读与词汇',
         'endpoint': 'web.reading_settings', 'matches': ('/reading/settings',)},
        {'id': 'account-credits', 'label': '积分',
         'endpoint': 'web.credits_page', 'matches': ('/credits',)},
        {'id': 'account-achievements', 'label': '成就',
         'endpoint': 'web.achievements_page', 'matches': ('/achievements',)},
        {'id': 'account-export', 'label': '我的学习数据',
         'endpoint': 'web.profile_export', 'matches': ('/me/export',)},
    )),
)

ADMIN_L2_GROUPS = (
    ('用户与访问', (
        {'id': 'admin-users', 'label': '用户与权限',
         'endpoint': 'admin.edit_user_table',
         'matches': ('/admin/usertable', '/admin/user/')},
        {'id': 'admin-site', 'label': '站点与注册',
         'endpoint': 'admin.configuration', 'matches': ('/admin/config',)},
    )),
    ('内容与 AI', (
        {'id': 'admin-translate', 'label': '整本翻译',
         'endpoint': 'web.translate_all_page', 'matches': ('/translate-all',)},
        {'id': 'admin-word-detail', 'label': '全文单词详解',
         'endpoint': 'web.word_detail_batch_page', 'matches': ('/word-detail-batch',)},
        {'id': 'admin-llm', 'label': 'LLM 任务中心',
         'endpoint': 'web.llm_task_runner_page', 'matches': ('/llm-tasks',)},
    )),
    ('资产与运营', (
        {'id': 'admin-credits', 'label': '积分治理',
         'endpoint': 'web.admin_credits_page', 'matches': ('/admin/credits',)},
        {'id': 'admin-mail', 'label': '运营站内信',
         'endpoint': 'web.admin_mail_page', 'matches': ('/admin/mail',)},
    )),
    ('系统', (
        {'id': 'admin-ui', 'label': 'UI 配置',
         'endpoint': 'admin.view_configuration', 'matches': ('/admin/viewconfig',)},
        {'id': 'admin-db', 'label': '数据库配置',
         'endpoint': 'admin.db_configuration', 'matches': ('/admin/dbconfig',)},
        {'id': 'admin-mailserver', 'label': '邮件服务器',
         'endpoint': 'admin.edit_mailsettings', 'matches': ('/admin/mailsettings',)},
        {'id': 'admin-schedule', 'label': '计划任务',
         'endpoint': 'admin.edit_scheduledtasks', 'matches': ('/admin/scheduledtasks',)},
        {'id': 'admin-log', 'label': '日志',
         'endpoint': 'admin.view_logfile', 'matches': ('/admin/logfile',)},
        {'id': 'admin-debug', 'label': '调试',
         'endpoint': 'admin.download_debug', 'matches': ('/admin/debug',)},
    )),
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


def _matches_path(path, matches):
    for match in matches:
        if path == match:
            return True
        if match.endswith('/') and path.startswith(match):
            return True
    return False


def l2_nav_groups(domain, path):
    """Return grouped L2 navigation with exactly one active item where defined."""
    if domain == 'account':
        groups = ACCOUNT_L2_GROUPS
    elif domain == 'admin':
        groups = ADMIN_L2_GROUPS
    else:
        return ()

    path = path or ''
    rendered = []
    for label, items in groups:
        rendered_items = []
        for item in items:
            rendered_items.append(dict(
                item,
                active=_matches_path(path, item['matches']),
            ))
        rendered.append((label, rendered_items))
    return tuple(rendered)


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
    if (path == '/admin' or path.startswith('/admin/')
            or path in ADMIN_PATH_PREFIXES
            or path.startswith(tuple(prefix + '/' for prefix in ADMIN_PATH_PREFIXES))):
        return 'admin'
    if page in LIBRARY_PAGES or path.startswith(LIBRARY_PATH_PREFIXES):
        return 'library'
    return ''
