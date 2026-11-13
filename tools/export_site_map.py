# -*- coding: utf-8 -*-
"""Записує структуру сайту з tools/site_map.py у JSON для WordPress: tools/wp-seed/site-map.json.

Запуск з кореня репозиторію після зміни site_map.py:
    python tools/export_site_map.py
"""
import json
from pathlib import Path

from build_pages import ST30, esc, render_block
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


def wp_blocks(blocks):
    """Блоки змісту сторінки (site_map.py) -> розмітка редактора WordPress (Gutenberg).

    Абзаци, підзаголовки, списки, кроки, таблиці й примітки — звичайні блоки, які редактор може правити.
    Документи-заглушки й картки працівників — блок «HTML» з розміткою макета (їх замінить адміністрація).
    """
    out = []

    def para(text, notice=False):
        if notice:
            return ('<!-- wp:paragraph {"className":"is-style-notice"} -->\n'
                    f'<p class="is-style-notice">{esc(text)}</p>\n<!-- /wp:paragraph -->')
        return f'<!-- wp:paragraph -->\n<p>{esc(text)}</p>\n<!-- /wp:paragraph -->'

    def lst(items, ordered=False):
        tag = 'ol' if ordered else 'ul'
        lis = ''.join(f'<!-- wp:list-item -->\n<li>{esc(x)}</li>\n<!-- /wp:list-item -->' for x in items)
        attrs = ' {"ordered":true}' if ordered else ''
        return f'<!-- wp:list{attrs} -->\n<{tag} class="wp-block-list">{lis}</{tag}>\n<!-- /wp:list -->'

    for b in blocks:
        kind = b[0]
        if kind == 'p':
            out.append(para(b[1]))
        elif kind == 'h2':
            out.append(f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{esc(b[1])}</h2>\n<!-- /wp:heading -->')
        elif kind == 'notice':
            out.append(para(b[1], notice=True))
        elif kind == 'list':
            out.append(lst(b[1]))
        elif kind == 'steps':
            out.append(lst(b[1], ordered=True))
        elif kind == 'table':
            cap, head, rows = b[1], b[2], b[3]
            th = ''.join(f'<th>{esc(h)}</th>' for h in head)
            tr = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in rows)
            out.append('<!-- wp:table {"hasFixedLayout":true} -->\n'
                       f'<figure class="wp-block-table"><table class="has-fixed-layout"><thead><tr>{th}</tr></thead>'
                       f'<tbody>{tr}</tbody></table><figcaption class="wp-element-caption">{esc(cap)}</figcaption></figure>\n'
                       '<!-- /wp:table -->')
        elif kind == 'docs':
            html = render_block(('docs', b[1], False))
            out.append(f'<!-- wp:html -->\n{html}\n<!-- /wp:html -->')
            if b[2]:
                out.append(para(ST30, notice=True))
        elif kind == 'people':
            out.append(f'<!-- wp:html -->\n{render_block(b)}\n<!-- /wp:html -->')
        else:
            raise ValueError(kind)
    return '\n\n'.join(out)


def main():
    data = {
        'sections': [
            {'slug': s['slug'], 'title': s['title'], 'lead': s['lead'], 'color': s['color'],
             'pages': [{'slug': p['slug'], 'title': p['title'], 'lead': p['lead'],
                        'content': wp_blocks(p['blocks'])} for p in s['pages']]}
            for s in SECTIONS
        ],
        'news': {'slug': NEWS['slug'], 'title': NEWS['title'], 'color': NEWS['color']},
        'contacts': {'slug': CONTACTS['slug'], 'title': CONTACTS['title'], 'color': CONTACTS['color'],
                     'lead': 'Адреса, телефон, електронна пошта та форма запитання.',
                     'content': wp_blocks([('notice', 'Графік роботи та прийому громадян надасть адміністрація.')])},
        'footer': [{'title': title, 'items': [{'title': t, 'path': wp_path(h)} for t, h in items]}
                   for title, items in FOOTER_COLS],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    pages = sum(len(s['pages']) for s in data['sections'])
    print(f'{OUT.relative_to(OUT.parent.parent.parent).as_posix()}: розділів {len(data["sections"])}, підсторінок {pages}')


if __name__ == '__main__':
    main()
