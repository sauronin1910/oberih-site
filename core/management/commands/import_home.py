"""Management-команда для безпечного імпорту головної сторінки, новин і спонсорів."""
from datetime import date
import html as html_lib
from pathlib import Path
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import HomePage, NewsItem, SiteSettings, Sponsor

# Таблиця транслітерації українського алфавіту (КМУ № 55) для генерації унікальних slug новин
_UKR_TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "ie",
    "ж": "zh",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ь": "",
    "ю": "iu",
    "я": "ia",
}


def transliterate_slug(text: str, max_len: int = 120) -> str:
    """Перетворює український заголовок на безпечний латинський slug."""
    lower = text.lower()
    out = []
    for ch in lower:
        if ch in _UKR_TRANSLIT:
            out.append(_UKR_TRANSLIT[ch])
        elif ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_", "—", "–", ":"):
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug[:max_len].strip("-") or "novyna"


def clean_html_text(raw: str) -> str:
    """Прибирає теги та розкодовує HTML-сутність у чистий текст."""
    no_tags = re.sub(r"<[^>]+>", "", raw)
    text = html_lib.unescape(no_tags).replace("\u00a0", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


class Command(BaseCommand):
    help = (
        "Імпортує вміст головної сторінки (HomePage), спонсорів (Sponsor) і новини (NewsItem) "
        "з файлів index.html та novyny/pryklad-novyny.html (ідемпотентно, в одній транзакції)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--index",
            type=str,
            default="index.html",
            help="Шлях до файлу головної сторінки (за замовчуванням: index.html).",
        )
        parser.add_argument(
            "--news",
            type=str,
            default="novyny/pryklad-novyny.html",
            help="Шлях до файлу шаблону/сторінки новини (за замовчуванням: novyny/pryklad-novyny.html).",
        )

    def _resolve_file(self, path_str: str, fallback_rel: str | None = None) -> Path:
        base = Path(settings.BASE_DIR)
        p = Path(path_str)
        if not p.is_absolute():
            p = base / p
        if p.exists():
            return p
        if fallback_rel:
            alt = base / fallback_rel
            if alt.exists():
                return alt
        raise CommandError(f"Файл не знайдено за шляхом: {p}")

    def _extract_section(self, html: str, section_id: str, file_label: str, warnings: list) -> str:
        pattern = re.compile(
            rf'<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>(.*?)</section>',
            re.S,
        )
        m = pattern.search(html)
        if not m:
            warnings.append(
                f"[{file_label} -> #{section_id}] Секцію #{section_id} не знайдено в розмітці."
            )
            return ""
        return m.group(1)

    def _extract_tag_text(
        self, block: str, pattern: str, location: str, warnings: list
    ) -> str:
        m = re.search(pattern, block, re.S)
        if not m:
            warnings.append(f"[{location}] Не вдалося надійно витягти текст за шаблоном {pattern}.")
            return ""
        return clean_html_text(m.group(1))

    def _ensure_site_settings(self, index_html: str, index_label: str, stats: dict, warnings: list):
        """Перевіряє заповненість SiteSettings і доповнює лише порожні поля з index.html."""
        contacts_sec = self._extract_section(index_html, "contacts", index_label, warnings)

        def find_dd(dt_title: str) -> str:
            m = re.search(
                rf"<dt>{re.escape(dt_title)}</dt>\s*<dd>(.*?)</dd>",
                contacts_sec or index_html,
                re.S,
            )
            return clean_html_text(m.group(1)) if m else ""

        extracted = {
            "address": find_dd("Адреса"),
            "phone": find_dd("Телефон"),
            "email": find_dd("Електронна пошта"),
            "director_name": find_dd("Директор"),
        }
        m_map = re.search(
            r'<div class="map">\s*<a href="([^"]+)"', contacts_sec or index_html, re.S
        )
        if m_map:
            extracted["map_url"] = html_lib.unescape(m_map.group(1)).strip()

        m_foot = re.search(
            r'<div class="foot-bottom">\s*<div class="wrap">\s*<span>(.*?)</span>',
            index_html,
            re.S,
        )
        if m_foot:
            extracted["footer_text"] = clean_html_text(m_foot.group(1))

        site_settings = SiteSettings.objects.first()
        if site_settings is None:
            site_settings = SiteSettings.objects.create(
                pk=1,
                phone=extracted.get("phone") or "(0342) 55-05-24",
                email=extracted.get("email") or "nrts.oberih@osvita.if.ua",
                address=extracted.get("address") or "",
                director_name=extracted.get("director_name") or "",
                map_url=extracted.get("map_url") or "",
                footer_text=extracted.get("footer_text") or "",
            )
            stats["settings_updated"] = "створено новий запис (бо був відсутній)"
        else:
            updated_fields = []
            for field_name, val in extracted.items():
                current_val = getattr(site_settings, field_name, "")
                if not (current_val and str(current_val).strip()) and val:
                    setattr(site_settings, field_name, val)
                    updated_fields.append(field_name)
            if updated_fields:
                site_settings.save()
                stats["settings_updated"] = f"доповнено порожні поля: {', '.join(updated_fields)}"
            else:
                stats["settings_updated"] = "усі поля вже заповнені (пропущено)"
        return site_settings

    def _parse_homepage_fields(
        self,
        index_html: str,
        index_label: str,
        site_settings: SiteSettings,
        warnings: list,
    ) -> dict:
        """Витягує тексти секцій головної сторінки без дублювання контактів із SiteSettings."""
        fields = {}

        # 1. #intro
        intro = self._extract_section(index_html, "intro", index_label, warnings)
        if intro:
            raw_eyebrow = self._extract_tag_text(
                intro, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #intro -> eyebrow", warnings
            )
            # Не дублюємо поштову адресу з SiteSettings у HomePage
            if site_settings.address and "вул." in raw_eyebrow:
                city_only = raw_eyebrow.split("·")[0].strip()
                fields["hero_eyebrow"] = city_only
                warnings.append(
                    f"[{index_label} -> #intro -> eyebrow] Вулицю з адреси не дубльовано в HomePage.hero_eyebrow "
                    f"(збережено «{city_only}», повна адреса береться з SiteSettings)."
                )
            else:
                fields["hero_eyebrow"] = raw_eyebrow

            m_h1 = re.search(r'<h1 id="hero-title">(.*?)</h1>', intro, re.S)
            if m_h1:
                h1_inner = m_h1.group(1)
                m_em = re.search(r"<em>(.*?)</em>", h1_inner, re.S)
                if m_em:
                    fields["hero_title_em"] = clean_html_text(m_em.group(1))
                    main_part = h1_inner.replace(m_em.group(0), "")
                    fields["hero_title"] = clean_html_text(main_part)
                else:
                    fields["hero_title"] = clean_html_text(h1_inner)
                    fields["hero_title_em"] = ""
            else:
                warnings.append(f"[{index_label} -> #intro -> #hero-title] Не знайдено заголовок H1.")

            fields["hero_lead"] = self._extract_tag_text(
                intro, r'<p class="lead">(.*?)</p>', f"{index_label} -> #intro -> .lead", warnings
            )

            facts = re.findall(r'<ul class="hero-facts">.*?</ul>', intro, re.S)
            if facts:
                li_items = [
                    clean_html_text(x)
                    for x in re.findall(r"<li[^>]*>(.*?)</li>", facts[0], re.S)
                ]
                for i in range(1, 4):
                    if len(li_items) >= i:
                        fields[f"hero_fact_{i}"] = li_items[i - 1]
                    else:
                        warnings.append(
                            f"[{index_label} -> #intro -> .hero-facts] Відсутній факт №{i}."
                        )

        # 2. #about
        about = self._extract_section(index_html, "about", index_label, warnings)
        if about:
            about_text_block = re.search(
                r'<div class="about-text">(.*?)</div>\s*<ul class="directions">',
                about,
                re.S,
            )
            sub = about_text_block.group(1) if about_text_block else about
            fields["about_eyebrow"] = self._extract_tag_text(
                sub, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #about -> eyebrow", warnings
            )
            fields["about_title"] = self._extract_tag_text(
                sub, r'<h2 id="about-title">(.*?)</h2>', f"{index_label} -> #about -> #about-title", warnings
            )
            # Абзаци без .eyebrow
            paragraphs = [
                clean_html_text(p)
                for p in re.findall(r"<p>(.*?)</p>", sub, re.S)
                if clean_html_text(p)
            ]
            if paragraphs:
                fields["about_text"] = "\n\n".join(paragraphs)
            else:
                warnings.append(f"[{index_label} -> #about] Не знайдено абзаців опису.")

            # Не заповнюємо about_quote та about_quote_note демо-текстом макета
            fields["about_quote"] = ""
            fields["about_quote_note"] = ""

        # 3. #news (заголовок секції)
        news_sec = self._extract_section(index_html, "news", index_label, warnings)
        if news_sec:
            fields["news_eyebrow"] = self._extract_tag_text(
                news_sec, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #news -> eyebrow", warnings
            )
            fields["news_title"] = self._extract_tag_text(
                news_sec, r'<h2 id="news-title">(.*?)</h2>', f"{index_label} -> #news -> #news-title", warnings
            )

        # 4. #documents
        docs_sec = self._extract_section(index_html, "documents", index_label, warnings)
        if docs_sec:
            fields["docs_eyebrow"] = self._extract_tag_text(
                docs_sec, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #documents -> eyebrow", warnings
            )
            fields["docs_title"] = self._extract_tag_text(
                docs_sec, r'<h2 id="docs-title">(.*?)</h2>', f"{index_label} -> #documents -> #docs-title", warnings
            )
            fields["docs_note"] = self._extract_tag_text(
                docs_sec, r'<p class="note">(.*?)</p>', f"{index_label} -> #documents -> .note", warnings
            )

        # 5. #safety
        safety_sec = self._extract_section(index_html, "safety", index_label, warnings)
        if safety_sec:
            fields["safety_eyebrow"] = self._extract_tag_text(
                safety_sec, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #safety -> eyebrow", warnings
            )
            fields["safety_title"] = self._extract_tag_text(
                safety_sec, r'<h2 id="safety-title">(.*?)</h2>', f"{index_label} -> #safety -> #safety-title", warnings
            )
            fields["safety_text"] = self._extract_tag_text(
                safety_sec, r"<h2[^>]*>.*?</h2>\s*<p>(.*?)</p>", f"{index_label} -> #safety -> p", warnings
            )

        # 6. #welcome
        welcome_sec = self._extract_section(index_html, "welcome", index_label, warnings)
        if welcome_sec:
            fields["welcome_eyebrow"] = self._extract_tag_text(
                welcome_sec, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #welcome -> eyebrow", warnings
            )
            fields["welcome_title"] = self._extract_tag_text(
                welcome_sec, r'<h2 id="welcome-title">(.*?)</h2>', f"{index_label} -> #welcome -> #welcome-title", warnings
            )
            fields["welcome_text"] = self._extract_tag_text(
                welcome_sec, r"<h2[^>]*>.*?</h2>\s*<p>(.*?)</p>", f"{index_label} -> #welcome -> p", warnings
            )

        # 7. #sponsors
        sponsors_sec = self._extract_section(index_html, "sponsors", index_label, warnings)
        if sponsors_sec:
            fields["sponsors_eyebrow"] = self._extract_tag_text(
                sponsors_sec, r'<p class="eyebrow[^"]*">(.*?)</p>', f"{index_label} -> #sponsors -> eyebrow", warnings
            )
            fields["sponsors_title"] = self._extract_tag_text(
                sponsors_sec, r'<h2 id="sponsors-title">(.*?)</h2>', f"{index_label} -> #sponsors -> #sponsors-title", warnings
            )
            fields["sponsors_text"] = self._extract_tag_text(
                sponsors_sec, r"<h2[^>]*>.*?</h2>\s*<p>(.*?)</p>", f"{index_label} -> #sponsors -> p", warnings
            )
            # Не заповнюємо sponsors_note демо-текстом макета
            fields["sponsors_note"] = ""

        return fields

    def _parse_news_body_template(self, news_html: str, news_label: str, warnings: list) -> str:
        """Витягує основні абзаци тексту зі сторінки pryklad-novyny.html."""
        m_art = re.search(
            r'<div class="page-body article">(.*?)</div>\s*</div>\s*</main>',
            news_html,
            re.S,
        )
        if not m_art:
            warnings.append(
                f"[{news_label} -> .page-body.article] Не знайдено контейнера тексту новини."
            )
            return ""
        article_block = m_art.group(1)
        paragraphs = []
        for p_match in re.finditer(r"<p(\s[^>]*)?>(.*?)</p>", article_block, re.S):
            attrs = p_match.group(1) or ""
            inner = p_match.group(2)
            # Пропускаємо службові блоки .news-meta, .notice та посилання «Усі новини»
            if "news-meta" in attrs or "notice" in attrs or 'class="more"' in inner:
                continue
            txt = clean_html_text(inner)
            if txt:
                paragraphs.append(txt)

        if not paragraphs:
            warnings.append(
                f"[{news_label} -> .page-body.article] Не знайдено жодного текстового абзацу новини."
            )
        return "\n\n".join(paragraphs)

    def handle(self, *args, **options):
        index_path = self._resolve_file(options["index"], "index.html")
        news_path = self._resolve_file(options["news"], "novyny/pryklad-novyny.html")

        index_html = index_path.read_text(encoding="utf-8")
        news_html = news_path.read_text(encoding="utf-8")

        index_label = index_path.name
        news_label = f"{news_path.parent.name}/{news_path.name}"

        stats = {
            "settings_updated": "",
            "homepage_created": 0,
            "homepage_skipped": 0,
            "sponsors_created": 0,
            "sponsors_skipped": 0,
            "news_created": 0,
            "news_draft_created": 0,
            "news_skipped": 0,
        }
        warnings_list = []

        # Перевірка вмісту папки static/img
        static_img_dir = Path(settings.BASE_DIR) / "static" / "img"
        static_img_files = (
            sorted(p.name for p in static_img_dir.iterdir() if p.is_file())
            if static_img_dir.exists()
            else []
        )

        with transaction.atomic():
            # 1. Перевірка та доповнення SiteSettings
            site_settings = self._ensure_site_settings(
                index_html, index_label, stats, warnings_list
            )

            # 2. Головна сторінка (HomePage)
            if HomePage.objects.exists():
                stats["homepage_skipped"] += 1
            else:
                hp_fields = self._parse_homepage_fields(
                    index_html, index_label, site_settings, warnings_list
                )
                HomePage.objects.create(pk=1, **hp_fields)
                stats["homepage_created"] += 1

            # 3. Спонсори (Sponsor)
            sponsors_sec = self._extract_section(
                index_html, "sponsors", index_label, warnings_list
            )
            sponsor_items = re.findall(
                r'<li class="sponsor[^"]*">(.*?)</li>', sponsors_sec, re.S
            )
            if not sponsor_items:
                warnings_list.append(
                    f"[{index_label} -> #sponsors] Не знайдено елементів <li class=\"sponsor\">."
                )

            placeholder_sponsors_count = 0
            for idx, item_html in enumerate(sponsor_items, start=1):
                m_href = re.search(r'<a[^>]+href="([^"]+)"', item_html)
                url = html_lib.unescape(m_href.group(1)).strip() if m_href else ""

                m_alt = re.search(r'<img[^>]+alt="([^"]+)"', item_html)
                raw_name = (
                    clean_html_text(m_alt.group(1))
                    if m_alt and m_alt.group(1).strip()
                    else clean_html_text(item_html)
                )

                is_placeholder_sponsor = (
                    not raw_name or raw_name.lower() == "логотип спонсора"
                )
                if is_placeholder_sponsor:
                    placeholder_sponsors_count += 1
                    continue

                sponsor_name = raw_name
                if Sponsor.objects.filter(name=sponsor_name).exists():
                    stats["sponsors_skipped"] += 1
                    continue

                Sponsor.objects.create(
                    name=sponsor_name,
                    logo="",
                    url=url,
                    order=idx,
                )
                stats["sponsors_created"] += 1

            if placeholder_sponsors_count:
                warnings_list.append(
                    f"[{index_label} -> #sponsors] Пропущено {placeholder_sponsors_count} демо-заглушок спонсорів "
                    f"(«Логотип спонсора») — демо-спонсори не створюються в базі."
                )

            # 4. Новини (NewsItem)
            template_body = self._parse_news_body_template(
                news_html, news_label, warnings_list
            )
            news_sec = self._extract_section(
                index_html, "news", index_label, warnings_list
            )
            card_matches = re.findall(
                r'<li class="news-card\s+c-([a-z]+)"[^>]*>(.*?)</li>',
                news_sec,
                re.S,
            )
            if not card_matches:
                warnings_list.append(
                    f"[{index_label} -> #news] Не знайдено карток <li class=\"news-card\">."
                )

            for idx, (color_code, card_html) in enumerate(card_matches, start=1):
                loc = f"{index_label} -> #news -> картка #{idx}"

                title = self._extract_tag_text(
                    card_html, r"<h[23][^>]*>\s*<a[^>]*>(.*?)</a>\s*</h[23]>", loc, warnings_list
                )
                if not title:
                    continue

                category = self._extract_tag_text(
                    card_html, r'<span class="cat">(.*?)</span>', loc, warnings_list
                ) or "Події"

                m_time = re.search(r'<time datetime="([^"]+)">', card_html)
                if m_time:
                    try:
                        pub_date = date.fromisoformat(m_time.group(1).strip())
                    except ValueError:
                        warnings_list.append(
                            f"[{loc}] Некоректний формат дати datetime=\"{m_time.group(1)}\", використано сьогоднішню."
                        )
                        pub_date = date.today()
                else:
                    warnings_list.append(f"[{loc}] Не знайдено тегу <time datetime=\"...\">.")
                    pub_date = date.today()

                summary = self._extract_tag_text(
                    card_html, r"</h[23]>\s*<p>(.*?)</p>", loc, warnings_list
                )

                # Перевіряємо, чи це демо-новина («Приклад» або посилання на pryklad-novyny.html)
                is_demo = (
                    '<span class="tag">Приклад</span>' in card_html
                    or "pryklad-novyny.html" in card_html
                )
                is_published = not is_demo

                slug = transliterate_slug(title)
                if NewsItem.objects.filter(slug=slug).exists():
                    stats["news_skipped"] += 1
                    continue

                # Прибираємо пряму згадку про захардкоджений телефон, якщо є
                body_text = template_body or summary
                NewsItem.objects.create(
                    title=title,
                    slug=slug,
                    category=category,
                    accent_color=color_code,
                    published_date=pub_date,
                    summary=summary,
                    body=body_text,
                    photo="",
                    is_published=is_published,
                )
                stats["news_created"] += 1
                if not is_published:
                    stats["news_draft_created"] += 1

            if stats["news_draft_created"] > 0:
                warnings_list.append(
                    f"[{index_label} -> #news] {stats['news_draft_created']} демо-новин мають позначку «Приклад» "
                    f"і посилаються на шаблон {news_label} — їх створено зі статусом «Чернетка» (is_published=False) "
                    f"та без фото, щоб демо-записи не з'являлися на публічному сайті."
                )

        # --- Підсумковий звіт у консоль ---
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("=== ЗВІТ ПРО ІМПОРТ ГОЛОВНОЇ СТОРІНКИ, СПОНСОРІВ І НОВИН (import_home) ===")
        )
        self.stdout.write(f"Файл головної сторінки: {index_path}")
        self.stdout.write(f"Файл шаблону новини:    {news_path}")
        self.stdout.write(
            f"Налаштування сайту (SiteSettings): {stats['settings_updated']}"
        )
        self.stdout.write(
            f"Головна сторінка (HomePage):       створено — {stats['homepage_created']}, "
            f"пропущено (вже існувала) — {stats['homepage_skipped']}"
        )
        self.stdout.write(
            f"Спонсори (Sponsor, без логотипів): створено — {stats['sponsors_created']}, "
            f"пропущено (вже існували) — {stats['sponsors_skipped']}"
        )
        self.stdout.write(
            f"Новини (NewsItem, без фото):       створено — {stats['news_created']} "
            f"(з них демо-чернеток: {stats['news_draft_created']}), "
            f"пропущено (вже існували) — {stats['news_skipped']}"
        )
        self.stdout.write("")
        self.stdout.write(
            "Наявні файли у static/img/ (файли у media/ під час імпорту не копіювалися):"
        )
        if static_img_files:
            for fname in static_img_files:
                self.stdout.write(f"  - static/img/{fname}")
            self.stdout.write(
                "  (Примітка: файлів логотипів спонсорів або фотографій новин у static/img/ немає; "
                "ілюстрація секції «Запрошуємо» — static/img/kids.jpg)."
            )
        else:
            self.stdout.write("  Папка static/img/ порожня або відсутня.")

        if warnings_list:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(f"Попередження ({len(warnings_list)}):")
            )
            for idx, w in enumerate(warnings_list, start=1):
                self.stdout.write(self.style.WARNING(f"  {idx}. {w}"))
        else:
            self.stdout.write(self.style.SUCCESS("Попереджень немає."))
        self.stdout.write(self.style.SUCCESS("=== ІМПОРТ ЗАВЕРШЕНО УСПІШНО ==="))
