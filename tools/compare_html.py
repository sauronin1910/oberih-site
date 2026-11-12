#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Порівняння еталонного статичного HTML зі згенерованим Django-шаблоном.

Запуск із кореня проєкту:
    python tools/compare_html.py
або для конкретних файлів:
    python tools/compare_html.py pro-nas/struktura-ta-orhany-upravlinnia.html
"""
import difflib
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

DEFAULT_PAGES = [
    "pro-nas/struktura-ta-orhany-upravlinnia.html",
    "pro-nas/administratsiia.html",
    "ofitsiina-storinka/statut.html",
]

# Обов'язкові хуки для js/main.js та js/prefs.js на кожній внутрішній сторінці
REQUIRED_JS_HOOKS = [
    'class="skip"',
    'class="a11ybar"',
    'data-scale="1"',
    'data-scale="1.15"',
    'data-scale="1.3"',
    'id="btn-contrast"',
    'id="btn-links"',
    'id="btn-reset"',
    'class="theme-toggle"',
    'class="tt-label"',
    'class="site-header"',
    'class="burger"',
    'aria-controls="main-nav"',
    'id="main-nav"',
    'class="drawer-head"',
    'class="drawer-close"',
    'id="menu"',
    'class="submenu"',
    'class="drawer-foot"',
    'class="nav-backdrop"',
    'id="main"',
    'class="site-footer"',
]


def split_sections(html: str) -> dict[str, str]:
    """Розбиває HTML-документ на 4 логічні зони: head, header/nav, main, footer."""
    m_head = re.search(r"(<head>.*?</head>)", html, re.S)
    m_header_nav = re.search(r"<body>(.*?)<main id=\"main\">", html, re.S)
    m_main = re.search(r"(<main id=\"main\">.*?</main>)", html, re.S)
    m_footer = re.search(r"</main>(.*?)</body>", html, re.S)
    return {
        "1. <head>": m_head.group(1) if m_head else "",
        "2. header / nav (панель доступності, шапка, меню)": (
            m_header_nav.group(1) if m_header_nav else ""
        ),
        "3. <main> (основний вміст сторінки)": (
            m_main.group(1) if m_main else ""
        ),
        "4. <footer> (підвал)": m_footer.group(1) if m_footer else "",
    }


def normalize_html(raw: str) -> list[str]:
    """Нормалізує HTML для точного порівняння структури та тексту."""
    s = raw
    # 1. Прибираємо HTML-коментарі
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    # 2. Приводимо шляхи до статики (../img/, /static/img/, img/ тощо) до єдиного вигляду STATIC/
    s = re.sub(
        r'((?:href|src|content)=")(?:\.\./|/static/|/)?(css|js|img|fonts)/',
        r"\1STATIC/\2/",
        s,
    )
    # 3. Приводимо внутрішні посилання старого формату (.html) до чистих URL (/.../)
    s = re.sub(r'href="(?:\.\./)?index\.html(#[^"]*)?"', r'href="/\1"', s)
    s = re.sub(
        r'href="(?:\.\./)?([a-z0-9-]+)/index\.html"',
        r'href="/\1/"',
        s,
    )
    s = re.sub(
        r'href="(?:\.\./)?([a-z0-9-]+)/([a-z0-9-]+)\.html"',
        r'href="/\1/\2/"',
        s,
    )
    # 4. Прибираємо пробіли між тегами та розбиваємо по одному тегу/блоку на рядок
    s = re.sub(r">\s+<", "><", s.strip())
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("><", ">\n<")
    return [line.strip() for line in s.splitlines() if line.strip()]


def compare_page(client: Client, rel_html_path: str) -> None:
    ref_file = ROOT / rel_html_path
    if not ref_file.exists():
        print(f"[ПОМИЛКА] Еталонний файл не знайдено: {ref_file}")
        return

    parts = Path(rel_html_path).with_suffix("").parts
    if len(parts) != 2:
        print(f"[ПОМИЛКА] Очікується шлях вигляду <section>/<page>.html: {rel_html_path}")
        return

    section_slug, page_slug = parts[0], parts[1]
    url = f"/{section_slug}/{page_slug}/"
    old_url = f"/{section_slug}/{page_slug}.html"

    ref_html = ref_file.read_text(encoding="utf-8")
    response = client.get(url, HTTP_HOST="127.0.0.1:8000", secure=True)
    redirect_resp = client.get(old_url, HTTP_HOST="127.0.0.1:8000", secure=True)

    print("=" * 78)
    print(f"СТОРІНКА: {rel_html_path}  --->  URL: {url}")
    print(
        f"Статус відповіді: {response.status_code} | "
        f"Перевірка 301 зі старої адреси ({old_url}): {redirect_resp.status_code} -> {redirect_resp.headers.get('Location', '')}"
    )

    if response.status_code != 200:
        print(f"[ПОМИЛКА] Сторінка повернула код {response.status_code}")
        return

    gen_html = response.content.decode("utf-8")

    # Перевірка JS-хуків
    missing_hooks = [h for h in REQUIRED_JS_HOOKS if h not in gen_html]
    if missing_hooks:
        print(f"[ПОМИЛКА JS-ХУКІВ] Відсутні селектори: {missing_hooks}")
    else:
        print(f"Перевірка хуків main.js / prefs.js: УСІ {len(REQUIRED_JS_HOOKS)} ПРИСУТНІ")

    ref_zones = split_sections(ref_html)
    gen_zones = split_sections(gen_html)

    for zone_name in ref_zones:
        ref_lines = normalize_html(ref_zones[zone_name])
        gen_lines = normalize_html(gen_zones[zone_name])
        diff = list(
            difflib.unified_diff(
                ref_lines,
                gen_lines,
                fromfile=f"Еталон ({rel_html_path})",
                tofile=f"Django ({url})",
                lineterm="",
                n=1,
            )
        )
        print("-" * 78)
        if not diff:
            print(f"[{zone_name}] ІДЕНТИЧНО (0 розбіжностей)")
        else:
            print(f"[{zone_name}] ЗНАЙДЕНО РОЗБІЖНОСТІ:")
            for line in diff:
                print(f"  {line}")
    print()


def main():
    if "127.0.0.1" not in settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append("127.0.0.1")

    pages = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PAGES
    client = Client()
    for p in pages:
        compare_page(client, p)


if __name__ == "__main__":
    main()

