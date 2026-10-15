#!/usr/bin/env python3
"""B7（架构评审）：i18n 种子与 JS 文件清单的生成器。

Why 脚本化：五步链（JS 加 mbT → 种子加 _() 行 → pybabel 抽取 → po/mo → JS_FILES
清单）有两处人肉环节——种子字典手写 323 行、test 的 JS_FILES 清单手维护——漏一步
即静默英文回退（R112 教训）。本脚本扫描 JS 层 mbT() 字面量，自动维护两处。

幂等契约：重复运行无变化；只追加 JS 新增词条，不自动删除（种子有但 JS 已不用的
词条打印提示，由人工判断——模板层共用词条的保护）。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, 'cps', 'templates', 'i18n_seed.html')
OUT_MANIFEST = os.path.join(ROOT, 'tests', 'i18n_js_files.json')

MBT_RE = re.compile(r"mbT\(\s*(['\"])((?:[^'\"\\]|\\.)*?)\1")


def scan_js():
    """扫 static/js（排除 libs）的 mbT 字面量，返回 (使用 mbT 的文件相对路径列表, msgid 集合)。"""
    js_files, msgids = [], set()
    js_root = os.path.join(ROOT, 'cps', 'static', 'js')
    for dp, dirnames, fns in os.walk(js_root):
        dirnames[:] = [d for d in dirnames if d != 'libs']
        for fn in sorted(fns):
            if not fn.endswith('.js'):
                continue
            p = os.path.join(dp, fn)
            code = open(p, encoding='utf-8').read()
            found = MBT_RE.findall(code)
            if found:
                js_files.append(os.path.relpath(p, ROOT))
                msgids.update(m for _, m in found)
    return sorted(js_files), msgids


def existing_msgids(seed_text):
    return re.findall(r'^\s{2}"((?:[^"\\]|\\.)*)":\s*_\(', seed_text, re.M)


def main():
    js_files, msgids = scan_js()
    seed_text = open(SEED, encoding='utf-8').read()
    existing = existing_msgids(seed_text)
    existing_set = set(existing)
    missing = sorted(m for m in msgids if m not in existing_set)
    stale = sorted(m for m in existing if m not in msgids)

    lines = seed_text.split('\n')
    # 种子段闭合行：`}` %}（最后一个词条行之后）
    close_idx = next(i for i, l in enumerate(lines) if l.strip() == '} %}')
    insert_at = close_idx  # 新词条插在 `} %}` 前（保持最后一个词条的尾逗号规则：给最后一个词条行补逗号）
    if missing:
        # 原最后一个词条行若无尾逗号则补
        for i in range(close_idx - 1, 0, -1):
            if lines[i].strip().startswith('"'):
                if not lines[i].rstrip().endswith(','):
                    lines[i] = lines[i].rstrip() + ','
                break
        added = ['  "%s": _("%s"),' % (m, m) for m in missing]
        lines[insert_at:insert_at] = added
        open(SEED, 'w', encoding='utf-8').write('\n'.join(lines))
        print(f'种子追加 {len(missing)} 条新词条: {missing[:5]}{"..." if len(missing) > 5 else ""}')
    else:
        print('种子无缺词条')

    # JS_FILES 清单生成物（契约测试读取）
    manifest = {'generated_by': 'scripts/generate_i18n_seed.py',
                'files': js_files, 'msgid_count': len(msgids | existing_set)}
    with open(OUT_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'JS 清单生成: {len(js_files)} 文件 -> {os.path.relpath(OUT_MANIFEST, ROOT)}')

    if stale:
        print(f'提示：种子有但 JS 已不用的词条 {len(stale)} 条（保留，人工判断后可手工移除）:')
        for m in stale[:10]:
            print('   -', m[:80])


if __name__ == '__main__':
    main()
