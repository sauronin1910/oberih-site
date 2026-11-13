# -*- coding: utf-8 -*-
"""Записує структуру сайту з tools/site_map.py у JSON для WordPress: tools/wp-seed/site-map.json.

Запуск з кореня репозиторію після зміни site_map.py:
    python tools/export_site_map.py
"""
import json
from pathlib import Path

from site_map import CONTACTS, FOOTER_COLS, NEWS, SECTIONS

OUT = Path(__file__).resolve().parent / 'wp-seed' / 'site-map.json'


def wp_path(href):
    """'pro-nas/statut.html' -> 'pro-nas/statut'; 'pro-nas/index.html' -> 'pro-nas'; 'index.html#x' -> '#x'."""
    path, _, anchor = href.partition('#')
    path = path[:-len('.html')] if path.endswith('.html') else path
    if path == 'index':
        path = ''
    elif path.endswith('/index'):
        path = path[:-len('/index')]
    return path + ('#' + anchor if anchor else '')


def main():
    data = {
        'sections': [
            {'slug': s['slug'], 'title': s['title'], 'lead': s['lead'], 'color': s['color'],
             'pages': [{'slug': p['slug'], 'title': p['title'], 'lead': p['lead']} for p in s['pages']]}
            for s in SECTIONS
        ],
        'news': {'slug': NEWS['slug'], 'title': NEWS['title'], 'color': NEWS['color']},
        'contacts': {'slug': CONTACTS['slug'], 'title': CONTACTS['title'], 'color': CONTACTS['color']},
        'footer': [{'title': title, 'items': [{'title': t, 'path': wp_path(h)} for t, h in items]}
                   for title, items in FOOTER_COLS],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    pages = sum(len(s['pages']) for s in data['sections'])
    print(f'{OUT.relative_to(OUT.parent.parent.parent).as_posix()}: розділів {len(data["sections"])}, підсторінок {pages}')


if __name__ == '__main__':
    main()
