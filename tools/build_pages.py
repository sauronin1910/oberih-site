# -*- coding: utf-8 -*-
"""Генератор сторінок сайту НРЦ «Оберіг».

Запуск з кореня репозиторію:   python tools/build_pages.py

Що робить:
  1. Оновлює меню і колонки підвалу в index.html (між мітками <!-- build:… -->).
  2. Створює всі внутрішні сторінки за tools/site_map.py, беручи шапку, меню
     і підвал з index.html, тож вони однакові на всіх сторінках.
Тільки стандартна бібліотека Python 3.8+.
"""
import html as H
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_map import SECTIONS, NEWS, CONTACTS, FOOTER_COLS, N  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ICONS = {
    'doc': '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
    'about': '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    'book': '<path d="M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1z"/><path d="M12 6v14"/>',
    'star': '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    'house': '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    'rehab': '<circle cx="12" cy="5" r="2"/><path d="M5 8c2 1.5 4.5 2 7 2s5-.5 7-2"/><path d="M12 10v5l-3 6M12 15l3 6"/>',
    'shield': '<path d="M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    'chev': '<path d="M6 9l6 6 6-6"/>',
    'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'back': '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    'pin': '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
}


def icon(name, cls='icon'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def esc(t):
    return H.escape(t, quote=True)


# ───────────────────────── меню і підвал ─────────────────────────

def menu_label(title):
    """Назва пункту меню: довгу ділимо на два рядки (на ПК), короткі слова «та», «і» тримаємо з наступним."""
    words = title.split()
    if len(words) < 2 or len(title) <= 8:
        return esc(title)
    best = None
    for i in range(1, len(words)):
        if len(words[i - 1]) <= 2:
            continue
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        w = max(len(a), len(b))
        if best is None or w < best[0]:
            best = (w, a, b)
    return f'<span class="ln">{esc(best[1])}</span> <span class="ln">{esc(best[2])}</span>'


def render_menu(current=''):
    """Пункти головного меню. current — шлях поточної сторінки від кореня."""
    out = []
    for s in SECTIONS:
        active = current.startswith(s['slug'] + '/')
        items = []
        for p in s['pages']:
            path = f"{s['slug']}/{p['slug']}.html"
            cur = ' aria-current="page"' if path == current else ''
            items.append(f'          <li><a href="{path}"{cur}>{esc(p["title"])}</a></li>')
        li_cls = ' class="is-active"' if active else ''
        out.append(
            f'      <li{li_cls}>\n'
            f'        <button type="button" aria-expanded="false"><span class="lbl">{menu_label(s["title"])}</span> {icon("chev", "icon chev")}</button>\n'
            f'        <ul class="submenu">\n' + '\n'.join(items) + '\n        </ul>\n      </li>')
    for d in (NEWS, CONTACTS):
        path = f"{d['slug']}/index.html"
        active = current.startswith(d['slug'] + '/')
        cur = ' aria-current="page"' if current == path else ''
        li_cls = ' class="is-active"' if active else ''
        out.append(f'      <li{li_cls}><a href="{path}"{cur}><span class="lbl">{menu_label(d["title"])}</span></a></li>')
    return '\n'.join(out)


def render_footer_cols():
    cols = []
    for title, links in FOOTER_COLS:
        lis = ''.join(f'<li><a href="{href}">{esc(t)}</a></li>' for t, href in links)
        cols.append(f'    <div>\n      <h2 class="foot-title">{esc(title)}</h2>\n      <ul>{lis}</ul>\n    </div>')
    return '\n'.join(cols)


def replace_region(text, name, body):
    pat = re.compile(r'(<!-- build:%s -->)(.*?)([ \t]*<!-- /build:%s -->)' % (name, name), re.S)
    assert len(pat.findall(text)) == 1, f'мітка build:{name} має бути рівно одна'
    return pat.sub(lambda m: m.group(1) + '\n' + body + '\n' + m.group(3), text)


# ───────────────────────── шляхи ─────────────────────────

SKIP = ('#', 'http:', 'https:', 'mailto:', 'tel:', 'data:', '/', '../')


def rewrite_paths(doc, prefix):
    """Відносні шляхи від кореня сайту → відносні від поточної сторінки."""
    if not prefix:
        return doc

    def fix(m):
        val = m.group(2)
        return m.group(0) if val.startswith(SKIP) else f'{m.group(1)}{prefix}{val}"'
    doc = re.sub(r'(\s(?:href|src)=")([^"]*)"', fix, doc)
    doc = re.sub(r'(<meta property="og:image" content=")([^"]*)"', fix, doc)
    return doc


# ───────────────────────── блоки вмісту ─────────────────────────

ST30 = 'Документ оприлюднюється відповідно до ст. 30 Закону України «Про освіту» не пізніше ніж через 10 робочих днів після затвердження.'


def notice(t):
    return f'<p class="notice">{icon("info")}<span>{esc(t)}</span></p>'


def render_block(b):
    kind = b[0]
    if kind == 'p':
        return f'<p>{esc(b[1])}</p>'
    if kind == 'h2':
        return f'<h2>{esc(b[1])}</h2>'
    if kind == 'notice':
        return notice(b[1])
    if kind == 'docs':
        items = ''.join(
            f'<li><div class="doc-item">{icon("doc", "icon ic")}<span>{esc(t)}<small>PDF · додасть адміністрація</small></span><em class="pdf">PDF</em></div></li>'
            for t in b[1])
        return f'<ul class="doc-list doc-list-page">{items}</ul>' + (notice(ST30) if b[2] else '')
    if kind == 'table':
        cap, head, rows = b[1], b[2], b[3]
        th = ''.join(f'<th scope="col">{esc(h)}</th>' for h in head)
        tr = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>' for r in rows)
        return (f'<section class="table-wrap" tabindex="0" aria-label="{esc(cap)}"><table class="data-table"><caption>{esc(cap)}</caption>'
                f'<thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></section>')
    if kind == 'people':
        cards = []
        for role, name in b[1]:
            nm = esc(name) if name else 'ПІБ <span class="tag-example">приклад</span>'
            cards.append(f'<li class="person"><span class="person-photo">{icon("user")}</span>'
                         f'<span class="person-text"><span class="person-role">{esc(role)}</span>'
                         f'<span class="person-name">{nm}</span></span></li>')
        return f'<ul class="people">{"".join(cards)}</ul>'
    if kind == 'steps':
        return '<ol class="steps">' + ''.join(f'<li>{esc(s)}</li>' for s in b[1]) + '</ol>'
    if kind == 'list':
        return '<ul class="bullets">' + ''.join(f'<li>{esc(s)}</li>' for s in b[1]) + '</ul>'
    raise ValueError(kind)


def crumbs(trail):
    """trail: [(назва, шлях або None для поточної)]"""
    lis = ['<li><a href="index.html">Головна</a></li>']
    for t, href in trail:
        lis.append(f'<li><a href="{href}">{esc(t)}</a></li>' if href else f'<li><span aria-current="page">{esc(t)}</span></li>')
    return f'<nav class="crumbs" aria-label="Хлібні крихти"><ol>{"".join(lis)}</ol></nav>'


def page_hero(color, eyebrow, title, lead, trail):
    eb = f'<p class="eyebrow c-{color}">{esc(eyebrow)}</p>' if eyebrow else ''
    ld = f'<p class="lead">{esc(lead)}</p>' if lead else ''
    inner = [crumbs(trail), eb, f'<h1 id="page-title">{esc(title)}</h1>', ld]
    return ('  <section class="page-hero" aria-labelledby="page-title">\n    <div class="wrap">\n'
            + ''.join(f'      {x}\n' for x in inner if x)
            + '    </div>\n  </section>\n')


def side_nav(s, current):
    lis = []
    for p in s['pages']:
        path = f"{s['slug']}/{p['slug']}.html"
        cur = ' aria-current="page"' if path == current else ''
        lis.append(f'<li><a href="{path}"{cur}>{esc(p["title"])}</a></li>')
    return (f'<nav class="side-nav c-{s["color"]}" aria-label="Розділ «{esc(s["title"])}»">'
            f'<p class="side-title"><a href="{s["slug"]}/index.html">{esc(s["title"])}</a></p>'
            f'<ul>{"".join(lis)}</ul></nav>')


# ───────────────────────── збирання сторінки ─────────────────────────

def build_doc(shell, path, title, description, main_html):
    head, top, bottom = shell
    depth = path.count('/')
    prefix = '../' * depth
    full_title = f'{title} — НРЦ «Оберіг»'
    if len(full_title) > 70:  # пошуковики обрізають довгі заголовки
        full_title = title
    d = esc(description.replace(' ', ' '))
    h = head
    h = re.sub(r'<title>.*?</title>', f'<title>{esc(full_title)}</title>', h)
    h = re.sub(r'(<meta name="description" content=")[^"]*"', lambda m: m.group(1) + d + '"', h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*"', lambda m: m.group(1) + esc(title) + '"', h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*"', lambda m: m.group(1) + d + '"', h)
    h = re.sub(r'<script type="application/ld\+json">.*?</script>\n', '', h, flags=re.S)  # дані організації — лише на головній
    t = replace_region(top, 'menu', render_menu(path))
    doc = h + t + '<main id="main">\n' + main_html + '</main>' + bottom
    return rewrite_paths(doc, prefix)


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main():
    idx_path = os.path.join(ROOT, 'index.html')
    src = open(idx_path, encoding='utf-8').read()

    # 1. меню і підвал на головній
    new = replace_region(src, 'menu', render_menu(''))
    new = replace_region(new, 'footer', render_footer_cols())
    if new != src:
        open(idx_path, 'w', encoding='utf-8', newline='\n').write(new)
    src = new

    # 2. оболонка для внутрішніх сторінок
    head, rest = src.split('<body>', 1)
    top, rest = rest.split('<main id="main">', 1)
    _, bottom = rest.split('</main>', 1)
    shell = (head + '<body>', top, bottom)

    news_items = re.findall(r'(        <li class="news-card[^"]*">.*?        </li>)', src, re.S)
    contact_block = re.search(r'(      <div class="contact">.*?\n        </form>\n      </div>)', src, re.S).group(1)

    pages = []

    # розділи
    for s in SECTIONS:
        cards = ''.join(
            f'<li><a class="tile c-{s["color"]}" href="{s["slug"]}/{p["slug"]}.html"><span class="ic">{icon("doc")}</span>'
            f'<strong>{esc(p["title"])}</strong><span>{esc(p["lead"])}</span></a></li>' for p in s['pages'])
        main_html = (page_hero(s['color'], 'Розділ', s['title'], s['lead'], [(s['title'], None)]) +
                     f'  <div class="wrap page-section">\n    <ul class="child-grid">{cards}</ul>\n  </div>\n')
        pages.append((f"{s['slug']}/index.html", s['title'], s['lead'], main_html))
        for p in s['pages']:
            path = f"{s['slug']}/{p['slug']}.html"
            body = '\n      '.join(render_block(b) for b in p['blocks'])
            main_html = (page_hero(s['color'], s['title'], p['title'], p['lead'],
                                   [(s['title'], f"{s['slug']}/index.html"), (p['title'], None)]) +
                         f'  <div class="wrap page-layout">\n    <div class="page-body">\n      {body}\n    </div>\n'
                         f'    {side_nav(s, path)}\n  </div>\n')
            pages.append((path, p['title'], p['lead'], main_html))

    # новини
    art = 'novyny/pryklad-novyny.html'
    cards = '\n'.join(re.sub(r'<a href="[^"]*">', f'<a href="{art}">', li) for li in news_items)
    cards = re.sub(r'<h3([ >])', r'<h2\1', cards).replace('</h3>', '</h2>')  # під h1 сторінки — h2
    news_main = (page_hero(NEWS['color'], f'Життя {N}', 'Новини', 'Події, оголошення та новини закладу.', [('Новини', None)]) +
                 f'  <div class="wrap page-section">\n    <ul class="news-grid">\n{cards}\n    </ul>\n'
                 f'    {notice("Новини — приклад. У WordPress тут буде стрічка всіх новин з посторінковою навігацією.")}\n  </div>\n')
    pages.append(('novyny/index.html', 'Новини', 'Події, оголошення та новини НРЦ «Оберіг».', news_main))
    art_main = (page_hero(NEWS['color'], 'Новини', 'Приклад новини', '', [('Новини', 'novyny/index.html'), ('Приклад новини', None)]) +
                '  <div class="wrap page-layout page-layout-single">\n    <div class="page-body article">\n'
                '      <p class="news-meta"><span class="cat">Події</span><time datetime="2026-10-28">28 жовтня 2026</time></p>\n'
                '      <div class="news-img article-img" role="img" aria-label="Місце для фото новини"><i class="d1"></i><i class="d2"></i><span class="tag">Приклад</span></div>\n'
                f'      {notice("Це шаблон сторінки новини. Текст і фото додає редактор в адмінпанелі. Фото дітей — лише зі згодою батьків.")}\n'
                '      <p>Перший абзац новини: коротко про подію — що, де і коли відбулося.</p>\n'
                '      <p>Другий абзац: подробиці, хто брав участь, що вдалося зробити.</p>\n'
                f'      <p><a class="more" href="novyny/index.html">{icon("back")} Усі новини</a></p>\n'
                '    </div>\n  </div>\n')
    pages.append((art, 'Приклад новини', 'Шаблон сторінки новини НРЦ «Оберіг».', art_main))

    # контакти
    cb = contact_block.replace('<h2 id="contacts-title">Контакти</h2>', '<h2 id="contacts-title">Як з нами зв’язатися</h2>')
    contacts_main = (page_hero(CONTACTS['color'], f'{N}', 'Контакти', 'Адреса, телефон, електронна пошта та форма запитання.', [('Контакти', None)]) +
                     f'  <section class="block page-contacts" aria-labelledby="contacts-title">\n    <div class="wrap">\n{cb}\n'
                     f'      {notice("Графік роботи та прийому громадян надасть адміністрація.")}\n    </div>\n  </section>\n')
    pages.append(('kontakty/index.html', 'Контакти', 'Адреса, телефон, електронна пошта НРЦ «Оберіг» і форма запитання.', contacts_main))

    # 404
    links = ''.join(f'<li><a href="{s["slug"]}/index.html">{esc(s["title"])}</a></li>' for s in SECTIONS)
    err_main = ('  <section class="page-hero err404" aria-labelledby="page-title">\n    <div class="wrap">\n'
                '      <p class="err-code" aria-hidden="true">404</p>\n'
                '      <h1 id="page-title">Сторінку не знайдено</h1>\n'
                '      <p class="lead">Можливо, адресу введено з помилкою або сторінку перенесли. Скористайтеся меню або перейдіть до одного з розділів.</p>\n'
                '      <div class="actions"><a class="btn btn-primary" href="index.html">На головну</a><a class="btn btn-ghost" href="kontakty/index.html">Контакти</a></div>\n'
                f'      <ul class="err-links">{links}</ul>\n    </div>\n  </section>\n')
    pages.append(('404.html', 'Сторінку не знайдено', 'Сторінку не знайдено. Перейдіть на головну або скористайтеся меню.', err_main))

    for path, title, desc, main_html in pages:
        write(path, build_doc(shell, path, title, desc, main_html))
    print(f'Згенеровано сторінок: {len(pages)} (+ оновлено index.html)')


if __name__ == '__main__':
    main()
