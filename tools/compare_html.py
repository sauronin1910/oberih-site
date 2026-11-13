#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Порівняння еталонного статичного HTML зі згенерованим Django-шаблоном.

Запуск із кореня проєкту:
    python tools/compare_html.py
або для конкретних файлів:
    python tools/compare_html.py index.html
"""
from datetime import date
import difflib
import json
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
from django.db import transaction  # noqa: E402
from django.test import Client  # noqa: E402

from core.models import HomePage, NewsItem, Sponsor  # noqa: E402

DEFAULT_PAGES = [
    "index.html",
    "pro-nas/struktura-ta-orhany-upravlinnia.html",
    "pro-nas/administratsiia.html",
    "ofitsiina-storinka/statut.html",
    "pro-nas/index.html",
    "novyny/index.html",
    "novyny/pryklad-novyny.html",
]

# Обов'язкові базові хуки для js/main.js та js/prefs.js на кожній сторінці
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

# Додаткові хуки main.js специфічно для головної сторінки (слайдер, поява блоків, форма)
HOME_JS_HOOKS = [
    'id="news-slider"',
    'id="news-track"',
    'class="slider-dots"',
    'class="slider-btn"',
    'data-dir="-1"',
    'data-dir="1"',
    'class="sec-head"',
    'class="about-text"',
    'class="directions"',
    'class="docs-band section-documents"',
    'class="doc-list"',
    'class="safety"',
    'class="hotlines"',
    'class="sponsors"',
    'class="welcome-text"',
    'class="welcome-art"',
    'class="contact"',
    'id="ask-form"',
    'id="form-status"',
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
    s = s.replace("&#x27;", "'").replace("\u00a0", " ")
    s = re.sub(r">\s+<", "><", s.strip())
    s = re.sub(r"[ \t]+", " ", s)
    s = s.replace("><", ">\n<")
    return [line.strip() for line in s.splitlines() if line.strip()]


def resolve_urls(rel_html_path: str) -> tuple[str, str]:
    """Повертає (новий_чистий_url, старий_html_url) для відносного шляху еталонного файлу."""
    norm = rel_html_path.replace("\\", "/")
    if norm == "index.html":
        return "/", "/index.html"
    parts = Path(norm).with_suffix("").parts
    if len(parts) == 2:
        section_slug, page_slug = parts[0], parts[1]
        if page_slug == "index":
            return f"/{section_slug}/", f"/{section_slug}/index.html"
        return f"/{section_slug}/{page_slug}/", f"/{section_slug}/{page_slug}.html"
    raise ValueError(f"Непідтримуваний шлях еталонного файлу: {rel_html_path}")


def _setup_demo_news_in_tx():
    """Тимчасово (у межах відкочуваної транзакції) приводить 6 демо-новин до еталону макета."""
    demo_colors = {
        "osinnii-tyzhden-rukhlyvykh-ihor-iak-my-provely-ioho-razom": "coral",
        "konsultatsii-fakhivtsiv-dlia-batkiv-u-lystopadi": "teal",
        "opryliudneno-koshtorys-na-2027-rik": "sky",
        "novyi-sensornyi-kutochok-dlia-zaniat-z-erhoterapii": "green",
        "den-pratsivnyka-osvity-diakuiemo-nashym-pedahoham": "orange",
        "iak-zapysatysia-na-konsultatsiiu-psykholoha-nrts-oberih": "teal",
    }
    NewsItem.objects.all().update(is_published=True, photo="")
    for slug, color in demo_colors.items():
        NewsItem.objects.filter(slug=slug).update(accent_color=color)


def fetch_with_temp_data(client: Client, rel_html_path: str, url: str, old_url: str):
    """Виконує запит до Django у відкочуваній транзакції, тимчасово створюючи дані макета без зміни реальної БД."""
    norm = rel_html_path.replace("\\", "/")
    with transaction.atomic():
        if norm == "index.html":
            _setup_demo_news_in_tx()
            hp = HomePage.objects.first()
            if hp:
                hp.about_quote = (
                    "Тексти на цій сторінці тимчасові. Їх замінить опис НРЦ «Оберіг» від адміністрації."
                )
                hp.about_quote_note = "Примітка до макета"
                hp.sponsors_note = (
                    "Логотипи — приклад. Справжні з'являться після погодження зі спонсорами."
                )
                hp.save()
            Sponsor.objects.all().delete()
            for i in range(1, 7):
                Sponsor.objects.create(
                    name="Логотип спонсора",
                    logo="",
                    url="",
                    order=i,
                )
        elif norm == "novyny/index.html":
            _setup_demo_news_in_tx()
            if not Sponsor.objects.exists():
                Sponsor.objects.create(name="Логотип спонсора", order=1)
        elif norm == "novyny/pryklad-novyny.html":
            NewsItem.objects.update_or_create(
                slug="pryklad-novyny",
                defaults={
                    "title": "Приклад новини",
                    "category": "Події",
                    "accent_color": "coral",
                    "published_date": date(2026, 10, 28),
                    "summary": "Шаблон сторінки новини НРЦ «Оберіг».",
                    "body": (
                        "Перший абзац новини: коротко про подію — що, де і коли відбулося.\n\n"
                        "Другий абзац: подробиці, хто брав участь, що вдалося зробити."
                    ),
                    "is_published": True,
                },
            )
            if not Sponsor.objects.exists():
                Sponsor.objects.create(name="Логотип спонсора", order=1)
        else:
            if not Sponsor.objects.exists():
                Sponsor.objects.create(name="Логотип спонсора", order=1)

        response = client.get(url, HTTP_HOST="127.0.0.1:8000", secure=True)
        redirect_resp = client.get(old_url, HTTP_HOST="127.0.0.1:8000", secure=True)
        transaction.set_rollback(True)
    return response, redirect_resp


def compare_json_ld(ref_html: str, gen_html: str) -> None:
    """Порівнює блок JSON-LD (<script type="application/ld+json">) між еталоном і Django."""
    m_ref = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        ref_html,
        re.S,
    )
    m_gen = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        gen_html,
        re.S,
    )
    print("-" * 78)
    print("[5. JSON-LD (schema.org EducationalOrganization)]:")
    if not m_ref or not m_gen:
        print("  [ПОМИЛКА] Блок JSON-LD не знайдено!")
        return
    try:
        ref_data = json.loads(m_ref.group(1))
        gen_data = json.loads(m_gen.group(1))
    except json.JSONDecodeError as exc:
        print(f"  [ПОМИЛКА JSON] Невалідний JSON-LD: {exc}")
        return

    print("  Статус JSON: ВАЛІДНИЙ JSON в обох випадках")
    ref_pretty = json.dumps(ref_data, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    gen_pretty = json.dumps(gen_data, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    diff = list(
        difflib.unified_diff(
            ref_pretty,
            gen_pretty,
            fromfile="Еталон JSON-LD",
            tofile="Django JSON-LD",
            lineterm="",
        )
    )
    if not diff:
        print("  Порівняння JSON-LD: ІДЕНТИЧНО")
    else:
        for line in diff:
            print(f"  {line}")


def compare_page(client: Client, rel_html_path: str) -> None:
    ref_file = ROOT / rel_html_path
    if not ref_file.exists():
        print(f"[ПОМИЛКА] Еталонний файл не знайдено: {ref_file}")
        return

    try:
        url, old_url = resolve_urls(rel_html_path)
    except ValueError as exc:
        print(f"[ПОМИЛКА] {exc}")
        return

    ref_html = ref_file.read_text(encoding="utf-8")
    response, redirect_resp = fetch_with_temp_data(
        client, rel_html_path, url, old_url
    )

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
    norm_path = rel_html_path.replace("\\", "/")
    hooks_to_check = (
        REQUIRED_JS_HOOKS + HOME_JS_HOOKS
        if norm_path == "index.html"
        else REQUIRED_JS_HOOKS
    )
    missing_hooks = [h for h in hooks_to_check if h not in gen_html]
    if missing_hooks:
        print(f"[ПОМИЛКА JS-ХУКІВ] Відсутні селектори: {missing_hooks}")
    else:
        print(f"Перевірка хуків main.js / prefs.js: УСІ {len(hooks_to_check)} ПРИСУТНІ")

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

    if norm_path == "index.html":
        compare_json_ld(ref_html, gen_html)

    print("-" * 78)
    print("Пояснення очікуваних розбіжностей із демо-еталоном:")
    print("  • <head>: додано бойові теги <link rel=\"canonical\"> та <meta property=\"og:url\">.")
    print("  • Меню: сторінка «Медичний супровід» має is_published=False (чернетка), тому прихована.")
    if norm_path == "index.html":
        print(
            "  • JSON-LD: у <head> додано абсолютний 'url' та абсолютний шлях 'logo' на основі SITE_URL."
        )
        print(
            "  • <main> (#news): прибрано демо-мітки <span class=\"tag\">Приклад</span>, "
            "а картки новин ведуть на власні чисті URL /novyny/<slug>/."
        )
        print(
            "  • <main> (#contacts): у форму #ask-form додано method=\"post\" action=\"/kontakty/\", "
            "прихований csrfmiddlewaretoken та name=\"consent\" у чекбокс згоди."
        )
    elif norm_path == "pro-nas/administratsiia.html":
        print("  • <main>: картки працівників мають consent_given=False до отримання письмових згод.")
    elif norm_path == "novyny/index.html":
        print(
            "  • <main>: у бойовому шаблоні прибрано демо-мітки <span class=\"tag\">Приклад</span>, "
            "демо-плашку p.notice про WordPress, а кожна картка веде на власний чистий URL /novyny/<slug>/."
        )
    elif norm_path == "novyny/pryklad-novyny.html":
        print(
            "  • <main>: у бойовому шаблоні прибрано демо-мітку <span class=\"tag\">Приклад</span> "
            "та демо-плашку p.notice «Це шаблон сторінки новини...»."
        )
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
