"""Автоматичні тести публічної частини та моделей сайту КЗ «НРЦ «Оберіг»»."""
from datetime import date
from io import BytesIO, StringIO
import json
import logging
from pathlib import Path
import re
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.mail.backends.base import BaseEmailBackend
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, TestCase, override_settings
from PIL import Image

from .context_processors import site_context
from .models import (
    Block,
    ContactMessage,
    Document,
    HomePage,
    NewsItem,
    Page,
    Person,
    Section,
    SiteSettings,
    Sponsor,
    validate_image_file,
)
from .views import error_400, error_403, error_500, get_client_ip


class FailingEmailBackend(BaseEmailBackend):
    """Тестовий поштовий бекенд, який завжди кидає виняток при спробі надіслати лист."""

    def send_messages(self, email_messages):
        raise RuntimeError("Тестовий збій SMTP-сервера")


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=TEST_STORAGES)
class PublicSiteTests(TestCase):
    """Перевірка сторінок розділів, внутрішніх сторінок, новин, редіректів та правил безпеки."""

    def setUp(self):
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                "phone": "(0342) 55-05-24",
                "email": "nrts.oberih@osvita.if.ua",
                "address": "вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020",
                "director_name": "Шестопалова Галина Любомирівна",
            },
        )
        self.section = Section.objects.create(
            slug="pro-nas",
            title="Про нас",
            lead="Хто ми, як влаштований НРЦ «Оберіг» і хто в ньому працює.",
            color="teal",
            icon="about",
            order=1,
            show_in_menu=True,
        )
        self.pub_page = Page.objects.create(
            section=self.section,
            slug="misiya-i-viziya",
            title="Місія і візія закладу",
            lead="Для чого існує НРЦ «Оберіг».",
            is_published=True,
            docs_first=False,
            order=1,
        )
        self.draft_page = Page.objects.create(
            section=self.section,
            slug="chernetka-storinky",
            title="Чернетка сторінки",
            lead="Ця сторінка ще не опублікована.",
            is_published=False,
            docs_first=False,
            order=2,
        )

    def test_section_page_renders_only_published_pages(self):
        """Сторінка розділу відповідає 200 і містить лише опубліковані дочірні сторінки."""
        response = self.client.get("/pro-nas/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn('<h1 id="page-title">Про нас</h1>', html)
        self.assertIn("Місія і візія закладу", html)
        self.assertNotIn("Чернетка сторінки", html)

    def test_unpublished_page_hidden_everywhere_and_returns_404(self):
        """Неопублікована сторінка відсутня в розділі, головному меню, боковій навігації та повертає 404."""
        # 1. Прямий запит повертає 404
        resp_draft = self.client.get("/pro-nas/chernetka-storinky/")
        self.assertEqual(resp_draft.status_code, 404)

        # 2. Відсутня в головному меню та в боковій навігації сусідньої опублікованої сторінки
        resp_pub = self.client.get("/pro-nas/misiya-i-viziya/")
        self.assertEqual(resp_pub.status_code, 200)
        html = resp_pub.content.decode("utf-8")
        self.assertIn("Місія і візія закладу", html)
        self.assertNotIn("Чернетка сторінки", html)
        self.assertNotIn("/pro-nas/chernetka-storinky/", html)

    def test_empty_section_and_hidden_from_menu_section(self):
        """Порожній розділ і розділ із show_in_menu=False відкриваються з кодом 200 і показують p.notice."""
        empty_sec = Section.objects.create(
            slug="porozhnii-rozdil",
            title="Порожній розділ",
            lead="Опис порожнього розділу.",
            color="sky",
            order=2,
            show_in_menu=False,
        )
        response = self.client.get(f"/{empty_sec.slug}/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("Порожній розділ", html)
        self.assertIn("Матеріали розділу готуються.", html)
        # Оскільки show_in_menu=False, у головному меню (<ul class="menu" id="menu">) його немає
        menu_part = html.split('<ul class="menu" id="menu">')[1].split("</ul>")[0]
        self.assertNotIn("Порожній розділ", menu_part)

    def test_nonexistent_section_returns_404(self):
        """Неіснуючий розділ повертає 404."""
        response = self.client.get("/neisnuiuchyi-rozdil/")
        self.assertEqual(response.status_code, 404)

    def test_reserved_section_slugs_validation(self):
        """Заборонені системні адреси (admin-panel, media, static, novyny, kontakty) не проходять валідацію."""
        for bad_slug in ("admin-panel", "media", "static", "novyny", "kontakty"):
            sec = Section(slug=bad_slug, title="Тест")
            with self.assertRaises(ValidationError):
                sec.full_clean()

    def test_person_consent_filtering(self):
        """Працівник з consent_given=False не відображається, а з consent_given=True — відображається."""
        Person.objects.create(
            page=self.pub_page,
            position="Практичний психолог",
            full_name="Прихована Особа Без Згоди",
            consent_given=False,
            order=1,
        )
        Person.objects.create(
            page=self.pub_page,
            position="Директор",
            full_name="Публічна Особа Зі Згодою",
            consent_given=True,
            order=2,
        )
        response = self.client.get("/pro-nas/misiya-i-viziya/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertNotIn("Прихована Особа Без Згоди", html)
        self.assertIn("Публічна Особа Зі Згодою", html)

    def test_docs_first_ordering_on_page(self):
        """Перемикач docs_first змінює взаємний порядок блоків тексту та документів."""
        Block.objects.create(
            page=self.pub_page,
            block_type=Block.BlockType.PARAGRAPH,
            text="Унікальний текстовий абзац для перевірки порядку.",
            order=1,
        )
        Document.objects.create(
            page=self.pub_page,
            title="Унікальний PDF документ для перевірки порядку",
            order=1,
        )

        # 1. За замовчуванням docs_first=False: спочатку текст, потім документ
        resp_after = self.client.get("/pro-nas/misiya-i-viziya/")
        html_after = resp_after.content.decode("utf-8")
        self.assertLess(
            html_after.index("Унікальний текстовий абзац для перевірки порядку."),
            html_after.index("Унікальний PDF документ для перевірки порядку"),
        )

        # 2. Вмикаємо docs_first=True: спочатку документ, потім текст
        self.pub_page.docs_first = True
        self.pub_page.save(update_fields=["docs_first"])
        resp_before = self.client.get("/pro-nas/misiya-i-viziya/")
        html_before = resp_before.content.decode("utf-8")
        self.assertLess(
            html_before.index("Унікальний PDF документ для перевірки порядку"),
            html_before.index("Унікальний текстовий абзац для перевірки порядку."),
        )

    def test_empty_news_list_renders_200_with_notice(self):
        """Порожній список новин відповідає 200 і показує повідомлення «Поки що новин немає.»."""
        NewsItem.objects.all().delete()
        response = self.client.get("/novyny/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("Поки що новин немає.", html)

    def test_news_list_ordering_and_published_filtering(self):
        """Список новин показує лише опубліковані новини у порядку від новіших до старіших."""
        NewsItem.objects.create(
            title="Старіша опублікована новина",
            slug="starisha-novyna",
            category="Події",
            accent_color="teal",
            published_date=date(2026, 9, 10),
            summary="Анонс старішої новини.",
            body="Текст старішої новини.",
            is_published=True,
        )
        NewsItem.objects.create(
            title="Новіша опублікована новина",
            slug="novisha-novyna",
            category="Свята",
            accent_color="coral",
            published_date=date(2026, 10, 28),
            summary="Анонс новішої новини.",
            body="Текст новішої новини.",
            is_published=True,
        )
        NewsItem.objects.create(
            title="Чернетка новини не для публікації",
            slug="chernetka-novyny",
            category="Оголошення",
            accent_color="sky",
            published_date=date(2026, 11, 1),
            summary="Анонс чернетки.",
            body="Текст чернетки.",
            is_published=False,
        )

        response = self.client.get("/novyny/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn("Новіша опублікована новина", html)
        self.assertIn("28 жовтня 2026", html)
        self.assertIn('datetime="2026-10-28"', html)
        self.assertIn("Старіша опублікована новина", html)
        self.assertIn("10 вересня 2026", html)
        self.assertNotIn("Чернетка новини не для публікації", html)
        self.assertLess(
            html.index("Новіша опублікована новина"),
            html.index("Старіша опублікована новина"),
        )

    def test_news_list_pagination_and_invalid_page_numbers(self):
        """Пагінація списку новин (по 6 на сторінку) та стійкість до ?page=999 і ?page=abc."""
        for i in range(1, 9):
            NewsItem.objects.create(
                title=f"Новина номер {i}",
                slug=f"novyna-nomer-{i}",
                category="Події",
                accent_color="coral",
                published_date=date(2026, 10, i),
                summary=f"Анонс новини {i}.",
                body=f"Повний текст новини {i}.",
                is_published=True,
            )

        # Сторінка 1 — 6 найновіших новин (8..3)
        resp_p1 = self.client.get("/novyny/")
        self.assertEqual(resp_p1.status_code, 200)
        html_p1 = resp_p1.content.decode("utf-8")
        self.assertIn("Новина номер 8", html_p1)
        self.assertIn("Новина номер 3", html_p1)
        self.assertNotIn("Новина номер 2", html_p1)
        self.assertIn("?page=2", html_p1)

        # Сторінка 2 — решта 2 новини (2..1)
        resp_p2 = self.client.get("/novyny/?page=2")
        self.assertEqual(resp_p2.status_code, 200)
        html_p2 = resp_p2.content.decode("utf-8")
        self.assertIn("Новина номер 2", html_p2)
        self.assertIn("Новина номер 1", html_p2)

        # Некоректні параметри ?page=999 та ?page=abc не падають з 500
        resp_999 = self.client.get("/novyny/?page=999")
        self.assertEqual(resp_999.status_code, 200)
        resp_abc = self.client.get("/novyny/?page=abc")
        self.assertEqual(resp_abc.status_code, 200)

    def test_news_detail_published_and_unpublished_or_missing(self):
        """Опублікована новина повертає 200 і розбиває абзаци без |safe; чернетка й неіснуюча — 404."""
        pub_news = NewsItem.objects.create(
            title="Осінній тиждень рухливих ігор",
            slug="osinnii-tyzhden",
            category="Події",
            accent_color="coral",
            published_date=date(2026, 10, 28),
            summary="Короткий анонс події.",
            body="Перший абзац тексту новини.\n\nДругий абзац із <script>alert(1)</script>.",
            is_published=True,
        )
        draft_news = NewsItem.objects.create(
            title="Прихована чернетка",
            slug="prykhovana-chernetka",
            category="Події",
            accent_color="teal",
            published_date=date(2026, 10, 29),
            summary="Анонс.",
            body="Текст.",
            is_published=False,
        )

        resp_ok = self.client.get(f"/novyny/{pub_news.slug}/")
        self.assertEqual(resp_ok.status_code, 200)
        html = resp_ok.content.decode("utf-8")
        self.assertIn("<p>Перший абзац тексту новини.</p>", html)
        self.assertIn(
            "<p>Другий абзац із &lt;script&gt;alert(1)&lt;/script&gt;.</p>",
            html,
        )
        self.assertNotIn("<script>alert(1)</script>", html)

        resp_draft = self.client.get(f"/novyny/{draft_news.slug}/")
        self.assertEqual(resp_draft.status_code, 404)

        resp_missing = self.client.get("/novyny/neisnuiucha-novyna/")
        self.assertEqual(resp_missing.status_code, 404)

    @override_settings(SITE_URL="https://oberih.if.ua")
    def test_site_url_in_canonical_and_og_url(self):
        """Налаштування SITE_URL використовується у <link rel="canonical"> та <meta property="og:url">."""
        response = self.client.get("/pro-nas/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn(
            '<link rel="canonical" href="https://oberih.if.ua/pro-nas/">', html
        )
        self.assertIn(
            '<meta property="og:url" content="https://oberih.if.ua/pro-nas/">', html
        )

    def test_301_redirects_from_old_html_urls(self):
        """Старі статичні .html-адреси повертають постійний 301-редірект на чисті URL."""
        cases = [
            ("/index.html", "/"),
            ("/pro-nas/index.html", "/pro-nas/"),
            ("/pro-nas/misiya-i-viziya.html", "/pro-nas/misiya-i-viziya/"),
            ("/novyny/index.html", "/novyny/"),
            ("/novyny/pryklad-novyny.html", "/novyny/pryklad-novyny/"),
            ("/kontakty/index.html", "/kontakty/"),
        ]
        for old_url, expected_target in cases:
            with self.subTest(old_url=old_url):
                resp = self.client.get(old_url)
                self.assertEqual(resp.status_code, 301)
                self.assertEqual(resp.headers.get("Location"), expected_target)

    def test_home_page_basic_and_empty_news_and_sponsors(self):
        """Головна (/) відповідає 200, має один <h1>, без сирих тегів; без новин показує p.notice, без спонсорів ховає #sponsors."""
        NewsItem.objects.all().delete()
        Sponsor.objects.all().delete()
        HomePage.objects.get_or_create(pk=1)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertEqual(len(re.findall(r"<h1\b", html)), 1)
        self.assertEqual(html.count("</h1>"), 1)
        self.assertNotIn("{{", html)
        self.assertNotIn("{%", html)

        # За відсутності опублікованих новин показується p.notice і немає #news-slider та .slider-arrows
        self.assertIn("Поки що новин немає.", html)
        self.assertNotIn('id="news-slider"', html)
        self.assertNotIn('class="slider-arrows"', html)

        # За відсутності спонсорів секція #sponsors і посилання в підвалі приховані
        self.assertNotIn('id="sponsors"', html)
        self.assertNotIn('href="/#sponsors"', html)

    def test_home_page_news_slider_with_1_and_multiple_items_and_drafts(self):
        """Чернетки новин не потрапляють на /; при 1 новині немає стрілок, при 3+ є слайди, .slider-dots і .slider-arrows."""
        NewsItem.objects.all().delete()
        NewsItem.objects.create(
            title="Чернетка для головної",
            slug="chernetka-dlia-holovnoi",
            category="Оголошення",
            accent_color="sky",
            published_date=date(2026, 10, 30),
            summary="Анонс чернетки.",
            body="Текст чернетки.",
            is_published=False,
        )
        NewsItem.objects.create(
            title="Перша опублікована новина на головній",
            slug="persha-novyna-holovna",
            category="Події",
            accent_color="coral",
            published_date=date(2026, 10, 28),
            summary="Анонс першої новини.",
            body="Текст першої новини.",
            is_published=True,
        )

        # 1 опублікована новина: є #news-slider з 1 карткою, але немає .slider-arrows
        resp_one = self.client.get("/")
        self.assertEqual(resp_one.status_code, 200)
        html_one = resp_one.content.decode("utf-8")
        self.assertIn('id="news-slider"', html_one)
        self.assertIn("Перша опублікована новина на головній", html_one)
        self.assertNotIn("Чернетка для головної", html_one)
        self.assertEqual(len(re.findall(r'<li class="news-card\b', html_one)), 1)
        self.assertNotIn('class="slider-arrows"', html_one)

        # Додаємо ще 2 опубліковані новини (разом 3)
        for idx in (2, 3):
            NewsItem.objects.create(
                title=f"Опублікована новина {idx}",
                slug=f"opublikovana-novyna-{idx}",
                category="Навчання",
                accent_color="teal",
                published_date=date(2026, 10, 20 + idx),
                summary=f"Анонс новини {idx}.",
                body=f"Текст новини {idx}.",
                is_published=True,
            )

        resp_three = self.client.get("/")
        self.assertEqual(resp_three.status_code, 200)
        html_three = resp_three.content.decode("utf-8")
        self.assertEqual(len(re.findall(r'<li class="news-card\b', html_three)), 3)
        self.assertIn('class="slider-arrows"', html_three)
        self.assertIn('class="slider-dots"', html_three)
        self.assertNotIn("Чернетка для головної", html_three)

    def test_home_page_sponsor_without_logo(self):
        """Спонсор без завантаженого логотипа відображається на головній без помилки й вмикає розділ #sponsors."""
        Sponsor.objects.all().delete()
        Sponsor.objects.create(
            name="Благодійний партнер без логотипа",
            order=1,
        )
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        self.assertIn('id="sponsors"', html)
        self.assertIn('href="/#sponsors"', html)
        self.assertIn(
            '<span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
            '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/>'
            '<path d="M21 16l-5-5-9 9"/></svg>Благодійний партнер без логотипа</span>',
            html,
        )

    @override_settings(SITE_URL="https://oberih.if.ua")
    def test_home_page_json_ld_and_unusual_address_format(self):
        """JSON-LD на головній є валідним JSON і не ламається, якщо формат адреси у SiteSettings нестандартний."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")
        m = re.search(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(m, "На головній сторінці не знайдено блок JSON-LD.")
        data = json.loads(m.group(1))
        self.assertEqual(data["@type"], "EducationalOrganization")
        self.assertEqual(data["url"], "https://oberih.if.ua/")
        self.assertEqual(
            data["logo"], "https://oberih.if.ua/static/img/logo.jpg"
        )
        self.assertEqual(
            data["address"]["streetAddress"], "вул. Гната Хоткевича, 52-А"
        )
        self.assertEqual(data["address"]["postalCode"], "76020")

        # Нестандартний формат адреси без ", м." та без 5-цифрового індексу
        settings_obj = SiteSettings.objects.get(pk=1)
        settings_obj.address = "Івано-Франківськ, вул. Тестова будинок 10"
        settings_obj.save(update_fields=["address"])

        resp_custom = self.client.get("/")
        self.assertEqual(resp_custom.status_code, 200)
        html_custom = resp_custom.content.decode("utf-8")
        m_custom = re.search(
            r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
            html_custom,
            re.DOTALL,
        )
        self.assertIsNotNone(m_custom)
        data_custom = json.loads(m_custom.group(1))
        self.assertEqual(
            data_custom["address"]["streetAddress"],
            "Івано-Франківськ, вул. Тестова будинок 10",
        )
        self.assertNotIn("postalCode", data_custom["address"])


@override_settings(STORAGES=TEST_STORAGES)
class ImportedSiteMapPagesTests(TestCase):
    """Перевірка всіх сторінок сайту, імпортованих командою import_site_map."""

    @classmethod
    def setUpTestData(cls):
        call_command("import_site_map", stdout=StringIO())
        call_command("import_home", stdout=StringIO())

    def test_all_published_pages_render_valid_html(self):
        """Усі опубліковані сторінки з import_site_map відповідають 200, мають один <h1> і не мають сирих тегів."""
        published_pages = list(
            Page.objects.filter(is_published=True)
            .select_related("section")
            .order_by("section__order", "order", "id")
        )
        self.assertGreater(
            len(published_pages),
            0,
            "Після import_site_map не знайдено жодної опублікованої сторінки.",
        )

        for page in published_pages:
            url = page.get_absolute_url()
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    200,
                    f"Сторінка {url} повернула статус {response.status_code} замість 200.",
                )
                html = response.content.decode("utf-8")
                h1_open_count = len(re.findall(r"<h1\b", html))
                h1_close_count = html.count("</h1>")
                self.assertEqual(
                    h1_open_count,
                    1,
                    f"На сторінці {url} знайдено {h1_open_count} відкриваючих тегів <h1> (очікується рівно 1).",
                )
                self.assertEqual(
                    h1_close_count,
                    1,
                    f"На сторінці {url} знайдено {h1_close_count} закриваючих тегів </h1> (очікується рівно 1).",
                )
                self.assertNotIn(
                    "{{",
                    html,
                    f"На сторінці {url} знайдено необроблений вираз шаблону '{{{{'.",
                )
                self.assertNotIn(
                    "{%",
                    html,
                    f"На сторінці {url} знайдено необроблений тег шаблону '{{%'.",
                )
                self.assertNotIn(
                    "Traceback",
                    html,
                    f"На сторінці {url} знайдено слово 'Traceback'.",
                )
                self.assertNotIn(
                    "TemplateSyntaxError",
                    html,
                    f"На сторінці {url} знайдено слово 'TemplateSyntaxError'.",
                )

        print(
            f"\n[Перевірка import_site_map] Успішно перевірено опублікованих сторінок: {len(published_pages)}"
        )

    def test_all_unpublished_pages_return_404(self):
        """Усі неопубліковані сторінки (чернетки) з import_site_map повертають 404."""
        unpublished_pages = list(
            Page.objects.filter(is_published=False)
            .select_related("section")
            .order_by("section__order", "order", "id")
        )
        self.assertGreater(
            len(unpublished_pages),
            0,
            "Після import_site_map очікується принаймні одна неопублікована сторінка-чернетка.",
        )

        for page in unpublished_pages:
            url = page.get_absolute_url()
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    404,
                    f"Неопублікована сторінка {url} повернула {response.status_code} замість 404.",
                )

        print(
            f"\n[Перевірка import_site_map] Успішно перевірено неопублікованих сторінок (404): {len(unpublished_pages)} "
            f"({', '.join(p.get_absolute_url() for p in unpublished_pages)})"
        )

    def test_all_internal_links_on_home_page_return_200(self):
        """Усі внутрішні посилання <a href="/..."> на головній сторінці (/) відповідають 200."""
        # Опублікуємо одну новину, щоб на головній також перевірялося посилання з картки новини
        first_news = NewsItem.objects.first()
        if first_news:
            first_news.is_published = True
            first_news.save(update_fields=["is_published"])

        resp_home = self.client.get("/")
        self.assertEqual(resp_home.status_code, 200)
        html = resp_home.content.decode("utf-8")

        raw_hrefs = re.findall(r'<a\b[^>]*\bhref="(/[^"]*)"', html)
        unique_urls = []
        for href in raw_hrefs:
            # Пропускаємо лише якірні посилання (/#sponsors)
            if href.startswith("/#"):
                continue
            if href not in unique_urls:
                unique_urls.append(href)

        self.assertGreater(
            len(unique_urls),
            15,
            "Очікується щонайменше 15 унікальних внутрішніх посилань на головній сторінці.",
        )

        for url in unique_urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(
                    resp.status_code,
                    200,
                    f"Внутрішнє посилання {url} на головній сторінці повернуло {resp.status_code} замість 200.",
                )

        print(
            f"\n[Перевірка посилань головної] Успішно перевірено внутрішніх посилань (200 OK): {len(unique_urls)}"
        )


@override_settings(STORAGES=TEST_STORAGES)
class ContactsAndFormTests(TestCase):
    """Перевірка сторінки контактів (/kontakty/), обробки форми #ask-form, захисту від спаму та адмінки звернень."""

    @classmethod
    def setUpTestData(cls):
        call_command("createcachetable", stdout=StringIO())
        SiteSettings.objects.update_or_create(
            pk=1,
            defaults={
                "phone": "(0342) 55-05-24",
                "email": "nrts.oberih@osvita.if.ua",
                "address": "вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020",
                "director_name": "Шестопалова Галина Любомирівна",
                "schedule_notice": "",
            },
        )

    def setUp(self):
        cache.clear()
        mail.outbox.clear()

    def test_contacts_page_get_and_schedule_notice_and_sent_param(self):
        """GET /kontakty/ відповідає 200, має один <h1>, без сирих тегів; перевірка schedule_notice та ?sent=1."""
        response = self.client.get("/kontakty/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8")

        self.assertEqual(len(re.findall(r"<h1\b", html)), 1)
        self.assertEqual(html.count("</h1>"), 1)
        self.assertNotIn("{{", html)
        self.assertNotIn("{%", html)
        self.assertIn('<h1 id="page-title">Контакти</h1>', html)
        self.assertIn('<h2 id="contacts-title">Як з нами зв’язатися</h2>', html)
        # За замовчуванням schedule_notice порожнє — плашки p.notice немає
        self.assertNotIn('class="notice"', html)
        self.assertIn('<p class="form-status" id="form-status" role="status"></p>', html)

        # Коли schedule_notice заповнено — плашка з'являється
        ss = SiteSettings.objects.get(pk=1)
        ss.schedule_notice = "Прийом громадян: щовівторка з 10:00 до 13:00."
        ss.save(update_fields=["schedule_notice"])
        resp_notice = self.client.get("/kontakty/")
        self.assertEqual(resp_notice.status_code, 200)
        html_notice = resp_notice.content.decode("utf-8")
        self.assertIn("Прийом громадян: щовівторка з 10:00 до 13:00.", html_notice)

        # ?sent=1 виводить фіксований рядок з коду, а довільний вміст ?sent=... ніколи не виводиться
        resp_sent = self.client.get("/kontakty/?sent=1")
        html_sent = resp_sent.content.decode("utf-8")
        self.assertIn(
            "Дякуємо! Ваше запитання надіслано. Відповімо на вказану електронну пошту.",
            html_sent,
        )

        resp_xss = self.client.get("/kontakty/?sent=<script>alert(1)</script>")
        html_xss = resp_xss.content.decode("utf-8")
        self.assertNotIn("<script>alert(1)</script>", html_xss)
        self.assertNotIn("alert(1)", html_xss)
        self.assertIn('<p class="form-status" id="form-status" role="status"></p>', html_xss)

    def test_valid_post_creates_message_and_sends_email_json_and_redirect(self):
        """Валідний POST створює ContactMessage, надсилає лист із Reply-To і повертає успіх (JSON для fetch та 303 без JS)."""
        payload = {
            "name": "Оксана Ковальчук",
            "email": "oksana.kovalchuk@example.com",
            "message": "Добрий день! Підкажіть, будь ласка, які документи потрібні для вступу?",
            "consent": "on",
            "website": "",
        }

        # 1. Запит від fetch (AJAX) -> 200 JSON
        resp_json = self.client.post(
            "/kontakty/",
            data=payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            REMOTE_ADDR="198.51.100.10",
        )
        self.assertEqual(resp_json.status_code, 200)
        data = resp_json.json()
        self.assertTrue(data["ok"])
        self.assertIn("Дякуємо!", data["message"])

        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, "Оксана Ковальчук")
        self.assertEqual(msg.email, "oksana.kovalchuk@example.com")
        self.assertTrue(msg.consent_given)
        self.assertFalse(msg.is_read)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertIn("Оксана Ковальчук", sent_email.subject)
        self.assertEqual(sent_email.reply_to, ["oksana.kovalchuk@example.com"])
        self.assertEqual(sent_email.to, ["nrts.oberih@osvita.if.ua"])

        # 2. Звичайний браузерний POST (без JS) -> 303 редірект на /kontakty/?sent=1#ask-form
        resp_html = self.client.post(
            "/kontakty/",
            data={
                "name": "Петро Мельник",
                "email": "petro@example.com",
                "message": "Запитання без JavaScript.",
                "consent": "on",
            },
            REMOTE_ADDR="198.51.100.11",
        )
        self.assertEqual(resp_html.status_code, 303)
        self.assertEqual(resp_html.headers.get("Location"), "/kontakty/?sent=1#ask-form")
        self.assertEqual(ContactMessage.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_invalid_post_rejections_without_db_records(self):
        """Без згоди, з порожнім текстом/ім'ям, з некоректним email або завеликим текстом — 400 з українським повідомленням і без запису в БД."""
        invalid_cases = [
            (
                "без згоди",
                {
                    "name": "Іван",
                    "email": "ivan@example.com",
                    "message": "Питання",
                },
                "consent",
                "згоди",
            ),
            (
                "порожній текст",
                {
                    "name": "Іван",
                    "email": "ivan@example.com",
                    "message": "   ",
                    "consent": "on",
                },
                "message",
                "текст запитання",
            ),
            (
                "порожнє ім'я",
                {
                    "name": "   ",
                    "email": "ivan@example.com",
                    "message": "Питання",
                    "consent": "on",
                },
                "name",
                "ім’я",
            ),
            (
                "некоректний email",
                {
                    "name": "Іван",
                    "email": "ne-email-adresa",
                    "message": "Питання",
                    "consent": "on",
                },
                "email",
                "електронної пошти",
            ),
            (
                "завеликий текст (> 2000 символів)",
                {
                    "name": "Іван",
                    "email": "ivan@example.com",
                    "message": "А" * 2001,
                    "consent": "on",
                },
                "message",
                "2000",
            ),
            (
                "завелике ім'я (> 150 символів)",
                {
                    "name": "І" * 151,
                    "email": "ivan@example.com",
                    "message": "Питання",
                    "consent": "on",
                },
                "name",
                "150",
            ),
        ]

        for label, payload, expected_field, expected_word in invalid_cases:
            with self.subTest(case=label):
                resp = self.client.post(
                    "/kontakty/",
                    data=payload,
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                )
                self.assertEqual(resp.status_code, 400)
                data = resp.json()
                self.assertFalse(data["ok"])
                self.assertEqual(data["field"], expected_field)
                self.assertIn(expected_word, data["message"].lower())

                # Перевірка також для звичайного POST без JS
                resp_nojs = self.client.post("/kontakty/", data=payload)
                self.assertEqual(resp_nojs.status_code, 400)
                self.assertIn(
                    expected_word,
                    resp_nojs.content.decode("utf-8").lower(),
                )

        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_silently_ignored(self):
        """Заповнений honeypot (website) тихо ігнорується без запису в базу і без відправлення листа."""
        payload = {
            "name": "Спам Бот",
            "email": "bot@example.com",
            "message": "Рекламне повідомлення",
            "consent": "on",
            "website": "https://spam-casino.example",
        }
        resp = self.client.post(
            "/kontakty/",
            data=payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(
        CONTACT_RATE_LIMIT_COUNT=3,
        CONTACT_RATE_LIMIT_PERIOD=600,
        CLIENT_IP_HEADER="",
        TRUST_X_FORWARDED_FOR=False,
    )
    def test_rate_limit_and_x_forwarded_for_and_cache_fail_open(self):
        """Перевищення ліміту (3 за 10 хв) дає 429; перевірка останнього IP у X-Forwarded-For та відкритої відмови кешу."""
        valid_data = {
            "name": "Марія",
            "email": "maria@example.com",
            "message": "Тестове запитання для перевірки ліміту.",
            "consent": "on",
        }

        # Перші 3 запити з однієї IP-адреси проходять успішно
        for i in range(3):
            resp = self.client.post(
                "/kontakty/",
                data=valid_data,
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                REMOTE_ADDR="203.0.113.55",
            )
            self.assertEqual(resp.status_code, 200, f"Запит #{i + 1} мав пройти успішно.")

        self.assertEqual(ContactMessage.objects.count(), 3)

        # 4-й запит з тієї самої IP-адреси блокується зі статусом 429
        resp_4th = self.client.post(
            "/kontakty/",
            data=valid_data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            REMOTE_ADDR="203.0.113.55",
        )
        self.assertEqual(resp_4th.status_code, 429)
        self.assertFalse(resp_4th.json()["ok"])
        self.assertIn("забагато", resp_4th.json()["message"].lower())
        self.assertEqual(ContactMessage.objects.count(), 3)

        # Перевірка TRUST_X_FORWARDED_FOR=True: береться ОСТАННІЙ запис X-Forwarded-For (доданий проксі),
        # тому підробка першого запису клієнтом не обходить ліміт для 203.0.113.55
        with override_settings(TRUST_X_FORWARDED_FOR=True):
            resp_xff = self.client.post(
                "/kontakty/",
                data=valid_data,
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                REMOTE_ADDR="127.0.0.1",
                HTTP_X_FORWARDED_FOR="1.2.3.4, 9.9.9.9, 203.0.113.55",
            )
            self.assertEqual(resp_xff.status_code, 429)
            self.assertEqual(ContactMessage.objects.count(), 3)

        # Перевірка «відмови відкрито»: якщо таблиця кешу недоступна, форма не падає і зберігає звернення
        broken_caches = {
            "default": {
                "BACKEND": "django.core.cache.backends.db.DatabaseCache",
                "LOCATION": "nonexistent_cache_table_xyz",
            }
        }
        with override_settings(CACHES=broken_caches):
            with self.assertLogs("core.views", level=logging.ERROR):
                resp_fail_open = self.client.post(
                    "/kontakty/",
                    data=valid_data,
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                    REMOTE_ADDR="203.0.113.99",
                )
            self.assertEqual(resp_fail_open.status_code, 200)
            self.assertEqual(ContactMessage.objects.count(), 4)

    @override_settings(EMAIL_BACKEND="core.tests.FailingEmailBackend")
    def test_email_failure_does_not_lose_saved_message_or_return_error(self):
        """Збій надсилання пошти НЕ втрачає запис у БД і НЕ повертає помилку користувачеві."""
        payload = {
            "name": "Тарас Бондар",
            "email": "taras@example.com",
            "message": "Дуже важливе звернення, яке не можна втратити при збої пошти.",
            "consent": "on",
        }
        with self.assertLogs("core.views", level=logging.ERROR):
            resp = self.client.post(
                "/kontakty/",
                data=payload,
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                REMOTE_ADDR="198.51.100.77",
            )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(ContactMessage.objects.count(), 1)
        saved = ContactMessage.objects.first()
        self.assertEqual(saved.name, "Тарас Бондар")
        self.assertEqual(
            saved.message,
            "Дуже важливе звернення, яке не можна втратити при збої пошти.",
        )

    def test_header_injection_rejected(self):
        """Спроба Header Injection (символи переведення рядка в імені або email) відхиляється зі статусом 400."""
        injection_cases = [
            {
                "name": "Іван\r\nBcc: attacker@example.com",
                "email": "ivan@example.com",
                "message": "Текст",
                "consent": "on",
            },
            {
                "name": "Іван",
                "email": "ivan@example.com\nCc: attacker@example.com",
                "message": "Текст",
                "consent": "on",
            },
        ]
        for payload in injection_cases:
            resp = self.client.post(
                "/kontakty/",
                data=payload,
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(resp.status_code, 400)
            self.assertFalse(resp.json()["ok"])

        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_csrf_without_token_rejected(self):
        """POST-запит без CSRF-токена відхиляється зі статусом 403 Forbidden."""
        csrf_client = Client(enforce_csrf_checks=True)
        resp = csrf_client.post(
            "/kontakty/",
            data={
                "name": "Іван",
                "email": "ivan@example.com",
                "message": "Запит без CSRF токена.",
                "consent": "on",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_admin_contact_message_readonly_and_permissions(self):
        """Адмінка не дозволяє створювати звернення або змінювати текст/відправника, але дозволяє позначати прочитаним і видаляти."""
        admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@example.com",
            password="StrongTestPassword123!",
        )
        self.client.force_login(admin_user)

        # 1. Створення нового звернення через адмінку заборонене (403)
        resp_add_get = self.client.get("/admin-panel/core/contactmessage/add/")
        self.assertEqual(resp_add_get.status_code, 403)
        resp_add_post = self.client.post(
            "/admin-panel/core/contactmessage/add/",
            data={"name": "Хтось", "email": "a@b.com", "message": "Текст"},
        )
        self.assertEqual(resp_add_post.status_code, 403)

        # 2. Спроба змінити name, email, message через POST у change_view не змінює ці поля (вони readonly),
        #    тоді як прапорець is_read оновлюється
        msg = ContactMessage.objects.create(
            name="Початкове Ім'я",
            email="original@example.com",
            message="Початковий незмінний текст звернення.",
            consent_given=True,
            is_read=False,
        )
        resp_change = self.client.post(
            f"/admin-panel/core/contactmessage/{msg.pk}/change/",
            data={
                "name": "Підроблене Ім'я",
                "email": "hacked@example.com",
                "message": "Підроблений текст звернення.",
                "consent_given": "",
                "is_read": "on",
                "_save": "Зберегти",
            },
        )
        self.assertEqual(resp_change.status_code, 302)
        msg.refresh_from_db()
        self.assertEqual(msg.name, "Початкове Ім'я")
        self.assertEqual(msg.email, "original@example.com")
        self.assertEqual(msg.message, "Початковий незмінний текст звернення.")
        self.assertTrue(msg.consent_given)
        self.assertTrue(msg.is_read)

        # 3. Масова дія mark_as_read позначає непрочитані звернення як прочитані
        msg2 = ContactMessage.objects.create(
            name="Другий Відправник",
            email="second@example.com",
            message="Друге звернення.",
            consent_given=True,
            is_read=False,
        )
        resp_action = self.client.post(
            "/admin-panel/core/contactmessage/",
            data={
                "action": "mark_as_read",
                "_selected_action": [str(msg2.pk)],
            },
        )
        self.assertEqual(resp_action.status_code, 302)
        msg2.refresh_from_db()
        self.assertTrue(msg2.is_read)

        # 4. Видалення звернення (персональних даних) дозволене
        resp_del = self.client.post(
            f"/admin-panel/core/contactmessage/{msg.pk}/delete/",
            data={"post": "yes"},
        )
        self.assertEqual(resp_del.status_code, 302)
        self.assertFalse(ContactMessage.objects.filter(pk=msg.pk).exists())


class Stage8SecurityAndDeployTests(TestCase):
    """Тести 8-го кроку: сторінки помилок (404/500/403/400), CSP, захист входу в адмінку, ліміт фото, SEO та backup_site."""

    @classmethod
    def setUpTestData(cls):
        call_command("createcachetable", stdout=StringIO())
        call_command("import_site_map", stdout=StringIO())
        call_command("import_home", stdout=StringIO())

    def setUp(self):
        cache.clear()

    def test_404_page_matches_reference_and_survives_db_failure(self):
        """Неіснуючий URL повертає 404 у дизайні сайту з <meta name="robots" content="noindex"> та переживає збій БД."""
        resp = self.client.get("/neisnuiucha-storinka-404/")
        self.assertEqual(resp.status_code, 404)
        html = resp.content.decode("utf-8")
        self.assertIn('<meta name="robots" content="noindex">', html)
        self.assertIn('<section class="page-hero err404"', html)
        self.assertIn('<p class="err-code" aria-hidden="true">404</p>', html)
        self.assertIn('<h1 id="page-title">Сторінку не знайдено</h1>', html)
        self.assertIn('<ul class="err-links">', html)
        self.assertIn('href="/pro-nas/"', html)

        # Навіть якщо БД недоступна під час роботи context processor, сторінка 404 не падає з 500
        rf = RequestFactory()
        req = rf.get("/neisnuiucha-storinka-404/")
        with (
            patch(
                "core.context_processors.SiteSettings.objects.first",
                side_effect=RuntimeError("БД тимчасово недоступна"),
            ),
            self.assertLogs("core.context_processors", level=logging.ERROR),
        ):
            ctx = site_context(req)
        self.assertEqual(ctx["menu_sections"], [])
        self.assertFalse(ctx["has_sponsors"])

    def test_500_page_is_autonomous_zero_db_queries_and_uses_static_prefix(self):
        """Сторінка 500 не робить жодного запиту до БД і підключає статику через {% get_static_prefix %}."""
        rf = RequestFactory()
        req = rf.get("/500-test/")
        with self.assertNumQueries(0):
            resp = error_500(req)
        self.assertEqual(resp.status_code, 500)
        html = resp.content.decode("utf-8")
        self.assertIn('<p class="err-code" aria-hidden="true">500</p>', html)
        self.assertIn("Тимчасова технічна помилка", html)
        self.assertIn('/static/css/style.css"', html)
        self.assertIn('/static/js/main.js"', html)

    def test_403_and_400_pages_render_in_ukrainian(self):
        """Сторінки 403 (зокрема CSRF) та 400 відображаються українською в дизайні сайту."""
        rf = RequestFactory()
        resp_403 = error_403(rf.get("/403/"))
        self.assertEqual(resp_403.status_code, 403)
        html_403 = resp_403.content.decode("utf-8")
        self.assertIn('<p class="err-code" aria-hidden="true">403</p>', html_403)
        self.assertIn("Доступ обмежено", html_403)

        resp_400 = error_400(rf.get("/400/"))
        self.assertEqual(resp_400.status_code, 400)
        html_400 = resp_400.content.decode("utf-8")
        self.assertIn('<p class="err-code" aria-hidden="true">400</p>', html_400)
        self.assertIn("Некоректний запит", html_400)

        # Звичайний не-AJAX POST без CSRF-токена отримує українську сторінку 403
        csrf_client = Client(enforce_csrf_checks=True)
        resp_csrf = csrf_client.post("/kontakty/", data={"name": "Тест"})
        self.assertEqual(resp_csrf.status_code, 403)
        self.assertIn("Доступ обмежено", resp_csrf.content.decode("utf-8"))

    def test_csp_header_and_no_inline_scripts_on_public_pages(self):
        """На публічних сторінках присутній CSP без 'unsafe-inline' у script-src і немає вбудованих скриптів, крім application/ld+json."""
        first_news = NewsItem.objects.first()
        if first_news:
            first_news.is_published = True
            first_news.save(update_fields=["is_published"])

        public_urls = [
            "/",
            "/kontakty/",
            "/novyny/",
            f"/novyny/{first_news.slug}/",
            "/pro-nas/",
            "/pro-nas/struktura-ta-orhany-upravlinnia/",
            "/neisnuiucha-storinka-404/",
        ]
        script_pattern = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)

        for url in public_urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertIn("Content-Security-Policy", resp.headers)
                csp = resp.headers["Content-Security-Policy"]
                self.assertIn("script-src 'self'", csp)
                self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)

                html = resp.content.decode("utf-8")
                for attrs, body in script_pattern.findall(html):
                    has_src = bool(re.search(r'\bsrc\s*=\s*["\'][^"\']+["\']', attrs))
                    is_json_ld = bool(
                        re.search(
                            r'\btype\s*=\s*["\']application/ld\+json["\']', attrs
                        )
                    )
                    self.assertTrue(
                        has_src or is_json_ld,
                        f"Знайдено недозволений вбудований <script> на {url}: <script{attrs}>{body[:80]}</script>",
                    )

        # На /admin-panel/login/ заголовок CSP НЕ застосовується
        resp_admin = self.client.get("/admin-panel/login/")
        self.assertNotIn("Content-Security-Policy", resp_admin.headers)

        # При CSP_ENABLED=False заголовок вимикається
        with override_settings(CSP_ENABLED=False):
            resp_no_csp = self.client.get("/")
            self.assertNotIn("Content-Security-Policy", resp_no_csp.headers)

    @override_settings(
        ADMIN_LOGIN_RATE_LIMIT_COUNT=5,
        ADMIN_LOGIN_IP_RATE_LIMIT_COUNT=20,
        ADMIN_LOGIN_RATE_LIMIT_PERIOD=900,
        CLIENT_IP_HEADER="",
        TRUST_X_FORWARDED_FOR=False,
    )
    def test_admin_login_rate_limit_pair_and_ip_and_fail_open(self):
        """Вхід в адмінку обмежує 5 спроб на (IP+логін) та 20 спроб на IP (повертає 429 українською) і має відкриту відмову."""
        User.objects.create_superuser(
            username="editor_user",
            email="editor@example.com",
            password="ValidAdminPassword123!",
        )

        # 1. Ліміт на пару (адреса + логін): 5 невдалих спроб -> 200, 6-та -> 429
        for i in range(5):
            resp = self.client.post(
                "/admin-panel/login/",
                data={"username": "editor_user", "password": "wrong_password"},
                REMOTE_ADDR="198.51.100.10",
            )
            self.assertEqual(
                resp.status_code, 200, f"Спроба #{i + 1} мала повернути 200"
            )

        resp_blocked = self.client.post(
            "/admin-panel/login/",
            data={"username": "editor_user", "password": "ValidAdminPassword123!"},
            REMOTE_ADDR="198.51.100.10",
        )
        self.assertEqual(resp_blocked.status_code, 429)
        blocked_html = resp_blocked.content.decode("utf-8")
        self.assertIn("Забагато невдалих спроб входу", blocked_html)

        # 2. Загальний ліміт на IP (20 за 15 хв) при переборі різних логінів з однієї адреси
        cache.clear()
        for i in range(20):
            resp_ip = self.client.post(
                "/admin-panel/login/",
                data={"username": f"attacker_login_{i}", "password": "wrong"},
                REMOTE_ADDR="198.51.100.77",
            )
            self.assertEqual(resp_ip.status_code, 200)

        # 21-ша спроба з цього ж IP (навіть з новим логіном) блокується зі статусом 429
        resp_ip_blocked = self.client.post(
            "/admin-panel/login/",
            data={"username": "brand_new_login", "password": "wrong"},
            REMOTE_ADDR="198.51.100.77",
        )
        self.assertEqual(resp_ip_blocked.status_code, 429)

        # 3. Відкрита відмова при недоступному кеші: вхід працює навіть при збої таблиці кешу
        broken_caches = {
            "default": {
                "BACKEND": "django.core.cache.backends.db.DatabaseCache",
                "LOCATION": "nonexistent_admin_cache_table_xyz",
            }
        }
        with (
            override_settings(CACHES=broken_caches),
            self.assertLogs("core.middleware", level=logging.ERROR),
        ):
            resp_ok = self.client.post(
                "/admin-panel/login/",
                data={
                    "username": "editor_user",
                    "password": "ValidAdminPassword123!",
                },
                REMOTE_ADDR="198.51.100.99",
            )
        self.assertEqual(resp_ok.status_code, 302)

    def test_image_max_pixels_decompression_bomb_validation(self):
        """Перевищення ліміту IMAGE_MAX_PIXELS (DecompressionBombWarning та DecompressionBombError) видає зрозумілу українську помилку."""
        buf = BytesIO()
        Image.new("RGB", (200, 200), color=(40, 80, 120)).save(buf, format="JPEG")
        uploaded = SimpleUploadedFile(
            "large_dim.jpg", buf.getvalue(), content_type="image/jpeg"
        )

        # 1. Ліміт 10 000 пікселів для картинки 200x200 (40 000 пікселів -> DecompressionBombError)
        with override_settings(IMAGE_MAX_PIXELS=10_000):
            with self.assertRaises(ValidationError) as ctx_err:
                validate_image_file(uploaded)
            self.assertIn(
                "Фото завелике. Зменшіть його розмір і спробуйте ще раз.",
                str(ctx_err.exception),
            )

        # 2. Ліміт 30 000 пікселів для картинки 200x200 (40 000 пікселів -> між N і 2N Pillow кидає DecompressionBombWarning)
        with override_settings(IMAGE_MAX_PIXELS=30_000):
            with self.assertRaises(ValidationError) as ctx_warn:
                validate_image_file(uploaded)
            self.assertIn(
                "Фото завелике. Зменшіть його розмір і спробуйте ще раз.",
                str(ctx_warn.exception),
            )

    @override_settings(SITE_URL="https://oberih.if.ua")
    def test_robots_txt_and_sitemap_xml(self):
        """Перевірка /robots.txt та /sitemap.xml: валідний XML, наявність опублікованих сторінок і відсутність чернеток та адмінки."""
        resp_robots = self.client.get("/robots.txt")
        self.assertEqual(resp_robots.status_code, 200)
        self.assertTrue(resp_robots["Content-Type"].startswith("text/plain"))
        robots_text = resp_robots.content.decode("utf-8")
        self.assertIn("User-agent: *", robots_text)
        self.assertIn("Disallow: /admin-panel/", robots_text)
        self.assertIn("Sitemap: https://oberih.if.ua/sitemap.xml", robots_text)

        # Опублікуємо одну новину, а решту залишимо чернетками
        pub_news = NewsItem.objects.first()
        pub_news.is_published = True
        pub_news.save(update_fields=["is_published"])
        draft_news = NewsItem.objects.exclude(pk=pub_news.pk).first()

        resp_sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(resp_sitemap.status_code, 200)
        self.assertTrue(
            resp_sitemap["Content-Type"].startswith("application/xml")
        )
        xml_text = resp_sitemap.content.decode("utf-8")

        # Перевіряємо валідність XML
        root = ET.fromstring(xml_text)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [el.text for el in root.findall("sm:url/sm:loc", ns)]

        self.assertIn("https://oberih.if.ua/", locs)
        self.assertIn("https://oberih.if.ua/kontakty/", locs)
        self.assertIn("https://oberih.if.ua/novyny/", locs)
        self.assertIn("https://oberih.if.ua/pro-nas/", locs)
        self.assertIn(
            "https://oberih.if.ua/pro-nas/struktura-ta-orhany-upravlinnia/",
            locs,
        )
        self.assertIn(f"https://oberih.if.ua/novyny/{pub_news.slug}/", locs)

        # Чернетки сторінок, чернетки новин і /admin-panel/ НЕ потрапляють у sitemap.xml
        self.assertNotIn(
            "https://oberih.if.ua/reabilitatsiine-viddilennia/medychnyi-suprovid/",
            locs,
        )
        if draft_news:
            self.assertNotIn(
                f"https://oberih.if.ua/novyny/{draft_news.slug}/", locs
            )
        for loc in locs:
            self.assertNotIn("/admin-panel/", loc)

    def test_import_commands_require_yes_when_data_exists(self):
        """Команди import_site_map та import_home зупиняються без ключа --yes, якщо в базі вже є сторінки або новини."""
        out_map = StringIO()
        call_command("import_site_map", stdout=out_map)
        self.assertIn("--yes", out_map.getvalue())
        self.assertIn("Зміни НЕ внесено", out_map.getvalue())

        out_home = StringIO()
        call_command("import_home", stdout=out_home)
        self.assertIn("--yes", out_home.getvalue())
        self.assertIn("Зміни НЕ внесено", out_home.getvalue())

    def test_backup_site_safety_checks_and_rotation(self):
        """Команда backup_site відхиляє каталоги всередині MEDIA_ROOT та проєкту, коректно повідомляє про відсутність pg_dump і ротує лише власні файли."""
        # 1. Відмова, якщо BACKUP_DIR всередині MEDIA_ROOT
        inside_media = Path(settings.MEDIA_ROOT) / "backups"
        with self.assertRaises(CommandError) as err_media:
            call_command("backup_site", dir=str(inside_media), stdout=StringIO())
        self.assertIn("MEDIA_ROOT", str(err_media.exception))

        # 2. Відмова, якщо BACKUP_DIR всередині каталогу проєкту (BASE_DIR)
        inside_project = Path(settings.BASE_DIR) / "backups_in_repo"
        with self.assertRaises(CommandError) as err_proj:
            call_command(
                "backup_site", dir=str(inside_project), stdout=StringIO()
            )
        self.assertIn("каталогу проєкту", str(err_proj.exception))

        # 3. Якщо pg_dump не знайдено — зрозуміла помилка українською через CommandError
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("shutil.which", return_value=None):
                with self.assertRaises(CommandError) as err_pg:
                    call_command("backup_site", dir=tmp_dir, stdout=StringIO())
                self.assertIn("pg_dump не знайдено", str(err_pg.exception))

            # 4. Перевірка створення файлів і ротації лише за власним шаблоном імені
            tmp_path = Path(tmp_dir)
            unrelated_file = tmp_path / "important_notes.txt"
            unrelated_file.write_text("не чіпати", encoding="utf-8")
            old_dump_1 = tmp_path / "oberih_db_20250101_030000.dump"
            old_dump_2 = tmp_path / "oberih_db_20250102_030000.dump"
            old_dump_1.write_bytes(b"old1")
            old_dump_2.write_bytes(b"old2")

            def fake_run(cmd, env=None, **kwargs):
                # Створюємо файл дампу за шляхом аргументу -f
                f_idx = cmd.index("-f") + 1
                Path(cmd[f_idx]).write_bytes(b"PGDMP_TEST")

                class Res:
                    returncode = 0
                    stderr = ""
                    stdout = ""

                return Res()

            with (
                patch("shutil.which", return_value="/usr/bin/pg_dump"),
                patch("subprocess.run", side_effect=fake_run),
            ):
                call_command(
                    "backup_site", dir=tmp_dir, keep=2, stdout=StringIO()
                )

            # Сторонній файл залишився недоторканим, найстаріший дамп видалено, залишилося рівно 2 дампи
            self.assertTrue(unrelated_file.exists())
            self.assertFalse(old_dump_1.exists())
            self.assertTrue(old_dump_2.exists())
            dumps = list(tmp_path.glob("oberih_db_*.dump"))
            self.assertEqual(len(dumps), 2)

    def test_client_ip_header_behavior(self):
        """Перевірка CLIENT_IP_HEADER: валідний заголовок, некоректний заголовок, відсутній заголовок та ігнорування X-Forwarded-For."""
        rf = RequestFactory()

        # 1. Коли CLIENT_IP_HEADER задано і заголовок містить коректну IP-адресу (IPv4 або IPv6) — використовується він
        with override_settings(
            CLIENT_IP_HEADER="HTTP_TRUE_CLIENT_IP",
            TRUST_X_FORWARDED_FOR=False,
        ):
            req_valid = rf.get(
                "/",
                REMOTE_ADDR="10.0.0.1",
                HTTP_TRUE_CLIENT_IP="198.51.100.42",
                HTTP_X_FORWARDED_FOR="203.0.113.99",
            )
            self.assertEqual(get_client_ip(req_valid), "198.51.100.42")

            req_ipv6 = rf.get(
                "/",
                REMOTE_ADDR="10.0.0.1",
                HTTP_TRUE_CLIENT_IP="2001:db8::1",
            )
            self.assertEqual(get_client_ip(req_ipv6), "2001:db8::1")

        # 2. Некоректний заголовок ігнорується -> береться REMOTE_ADDR (НЕ X-Forwarded-For)
        with override_settings(
            CLIENT_IP_HEADER="HTTP_TRUE_CLIENT_IP",
            TRUST_X_FORWARDED_FOR=True,
        ):
            req_invalid = rf.get(
                "/",
                REMOTE_ADDR="10.0.0.2",
                HTTP_TRUE_CLIENT_IP="not-an-ip, 1.2.3.4",
                HTTP_X_FORWARDED_FOR="203.0.113.88",
            )
            self.assertEqual(get_client_ip(req_invalid), "10.0.0.2")

        # 3. Без заголовка береться REMOTE_ADDR
        with override_settings(
            CLIENT_IP_HEADER="HTTP_TRUE_CLIENT_IP",
            TRUST_X_FORWARDED_FOR=False,
        ):
            req_missing = rf.get("/", REMOTE_ADDR="10.0.0.3")
            self.assertEqual(get_client_ip(req_missing), "10.0.0.3")

        # 4. X-Forwarded-For ігнорується, коли CLIENT_IP_HEADER задано (навіть якщо TRUST_X_FORWARDED_FOR=True і заголовок відсутній)
        with override_settings(
            CLIENT_IP_HEADER="HTTP_TRUE_CLIENT_IP",
            TRUST_X_FORWARDED_FOR=True,
        ):
            req_xff_ignored = rf.get(
                "/",
                REMOTE_ADDR="10.0.0.4",
                HTTP_X_FORWARDED_FOR="203.0.113.77",
            )
            self.assertEqual(get_client_ip(req_xff_ignored), "10.0.0.4")


