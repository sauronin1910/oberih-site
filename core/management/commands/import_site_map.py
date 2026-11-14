"""Management-команда для безпечного імпорту структури та початкового вмісту з tools/site_map.py."""
import importlib.util
from pathlib import Path
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Block, Document, Page, Person, Section, SiteSettings


class Command(BaseCommand):
    help = (
        "Імпортує розділи, сторінки, блоки, документи, працівників і налаштування сайту "
        "з файлу tools/site_map.py (ідемпотентно, без перезапису наявних даних)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="tools/site_map.py",
            help="Шлях до файлу site_map.py (за замовчуванням: tools/site_map.py).",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            default=False,
            help="Підтвердити виконання імпорту, якщо в базі даних вже є сторінки.",
        )

    def _load_site_map(self, path_str: str):
        path = Path(path_str)
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / path
        if not path.exists():
            raise CommandError(f"Файл карти сайту не знайдено за шляхом: {path}")

        spec = importlib.util.spec_from_file_location("site_map_module", str(path))
        if spec is None or spec.loader is None:
            raise CommandError(f"Не вдалося завантажити Python-модуль із файлу: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, path

    def _extract_index_contacts(self) -> dict:
        """Зчитує реквізити з index.html (якщо файл є в корені проєкту)."""
        defaults = {
            "phone": "(0342) 55-05-24",
            "email": "nrts.oberih@osvita.if.ua",
            "address": "вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020",
            "director_name": "Шестопалова Галина Любомирівна",
            "map_url": (
                "https://www.google.com/maps/search/?api=1&query="
                "%D0%B2%D1%83%D0%BB.+%D0%93%D0%BD%D0%B0%D1%82%D0%B0+"
                "%D0%A5%D0%BE%D1%82%D0%BA%D0%B5%D0%B2%D0%B8%D1%87%D0%B0+52%D0%90+"
                "%D0%86%D0%B2%D0%B0%D0%BD%D0%BE-%D0%A4%D1%80%D0%B0%D0%BD%D0%BA%D1%96%D0%B2%D1%81%D1%8C%D0%BA"
            ),
            "footer_text": "© 2026 НРЦ «Оберіг». Матеріали сайту використовуються з посиланням на джерело.",
        }
        index_path = Path(settings.BASE_DIR) / "index.html"
        if not index_path.exists():
            return defaults

        html = index_path.read_text(encoding="utf-8")

        m_addr = re.search(r"<dt>Адреса</dt><dd>([^<]+)</dd>", html)
        if m_addr:
            defaults["address"] = m_addr.group(1).strip()

        m_tel = re.search(r'<dt>Телефон</dt><dd><a[^>]*>([^<]+)</a></dd>', html)
        if m_tel:
            defaults["phone"] = m_tel.group(1).strip()

        m_mail = re.search(
            r'<dt>Електронна пошта</dt><dd><a[^>]*>([^<]+)</a></dd>', html
        )
        if m_mail:
            defaults["email"] = m_mail.group(1).strip()

        m_dir = re.search(r"<dt>Директор</dt><dd>([^<]+)</dd>", html)
        if m_dir:
            defaults["director_name"] = m_dir.group(1).strip()

        m_foot = re.search(
            r'<div class="foot-bottom">\s*<div class="wrap">\s*<span>([^<]+)</span>',
            html,
        )
        if m_foot:
            defaults["footer_text"] = m_foot.group(1).strip()

        return defaults

    def _is_placeholder_only_page(self, raw_blocks: list, todo_text: str) -> bool:
        """Повертає True, якщо сторінка містить лише примітки-заглушки без змістовних блоків, документів чи людей."""
        if not raw_blocks:
            return True
        for b in raw_blocks:
            kind = b[0]
            if kind in ("docs", "people", "table", "list", "steps", "h2", "p"):
                return False
            if kind == "notice" and b[1] != todo_text:
                # Якщо є інша примітка, перевіряємо, чи це не просто технічне застереження без жодного іншого вмісту
                continue
        return True

    def handle(self, *args, **options):
        if Page.objects.exists() and not options.get("yes"):
            self.stdout.write(
                self.style.WARNING(
                    "УВАГА: У базі даних вже є сторінки. Команда import_site_map призначена для "
                    "початкового наповнення сайту і при повторному запуску може відновити видалені "
                    "сторінки або скинути налаштування порядку документів.\n"
                    "Зміни НЕ внесено. Якщо ви справді хочете виконати імпорт поверх наявних даних, "
                    "запустіть команду з ключем підтвердження --yes:\n"
                    "  python manage.py import_site_map --yes"
                )
            )
            return

        site_map, resolved_path = self._load_site_map(options["path"])
        sections_data = getattr(site_map, "SECTIONS", None)
        todo_text = getattr(site_map, "TODO", "")

        if not sections_data:
            raise CommandError(f"У файлі {resolved_path} не знайдено списку SECTIONS.")

        stats = {
            "settings_created": 0,
            "settings_skipped": 0,
            "sections_created": 0,
            "sections_skipped": 0,
            "pages_created": 0,
            "pages_skipped": 0,
            "pages_draft": 0,
            "blocks_created": 0,
            "documents_created": 0,
            "people_created": 0,
        }
        warnings_list = []

        contacts = self._extract_index_contacts()

        with transaction.atomic():
            # 1. Налаштування сайту (SiteSettings)
            if SiteSettings.objects.exists():
                stats["settings_skipped"] += 1
                site_settings = SiteSettings.objects.first()
            else:
                site_settings = SiteSettings.objects.create(
                    pk=1,
                    phone=contacts["phone"],
                    email=contacts["email"],
                    address=contacts["address"],
                    director_name=contacts["director_name"],
                    map_url=contacts["map_url"],
                    footer_text=contacts["footer_text"],
                )
                stats["settings_created"] += 1

            # 2. Розділи та сторінки
            for sec_order, sec_dict in enumerate(sections_data, start=1):
                sec_slug = sec_dict["slug"]
                section = Section.objects.filter(slug=sec_slug).first()
                if section is not None:
                    stats["sections_skipped"] += 1
                else:
                    section = Section.objects.create(
                        slug=sec_slug,
                        title=sec_dict["title"],
                        lead=sec_dict.get("lead", ""),
                        color=sec_dict.get("color", "teal"),
                        icon=sec_dict.get("icon", "doc"),
                        order=sec_order,
                        show_in_menu=True,
                    )
                    stats["sections_created"] += 1

                for page_order, page_dict in enumerate(
                    sec_dict.get("pages", []), start=1
                ):
                    page_slug = page_dict["slug"]
                    if Page.objects.filter(section=section, slug=page_slug).exists():
                        stats["pages_skipped"] += 1
                        continue

                    raw_blocks = page_dict.get("blocks", [])
                    is_only_placeholder = self._is_placeholder_only_page(
                        raw_blocks, todo_text
                    )
                    is_published = not is_only_placeholder
                    docs_first = bool(raw_blocks and raw_blocks[0][0] == "docs")
                    if not is_published:
                        stats["pages_draft"] += 1
                        warnings_list.append(
                            f"Сторінка «{section.title} / {page_dict['title']}» містить лише примітки-заглушки — "
                            f"створено зі статусом «Чернетка» (is_published=False)."
                        )

                    page = Page.objects.create(
                        section=section,
                        slug=page_slug,
                        title=page_dict["title"],
                        lead=page_dict.get("lead", ""),
                        meta_description="",
                        is_published=is_published,
                        docs_first=docs_first,
                        order=page_order,
                    )
                    stats["pages_created"] += 1

                    block_order = 0
                    doc_order = 0
                    person_order = 0
                    has_todo_notice = False

                    for raw_block in raw_blocks:
                        kind = raw_block[0]

                        if kind == "docs":
                            doc_titles = raw_block[1]
                            st30_flag = bool(raw_block[2]) if len(raw_block) > 2 else False
                            for doc_title in doc_titles:
                                doc_order += 1
                                Document.objects.create(
                                    page=page,
                                    title=doc_title,
                                    file="",
                                    order=doc_order,
                                    show_st30_notice=st30_flag,
                                )
                                stats["documents_created"] += 1

                        elif kind == "people":
                            people_items = raw_block[1]
                            for role, full_name in people_items:
                                person_order += 1
                                clean_name = (full_name or "").strip()
                                # Якщо ПІБ дублює директора з SiteSettings або відсутній:
                                if (
                                    role == "Директор"
                                    and clean_name == site_settings.director_name
                                ):
                                    warnings_list.append(
                                        f"Сторінка «{page.title}»: ПІБ директора збережено у «Налаштуваннях сайту»; "
                                        f"картку створено зі статусом без згоди (consent_given=False)."
                                    )
                                Person.objects.create(
                                    page=page,
                                    position=role,
                                    full_name=clean_name,
                                    consent_given=False,
                                    order=person_order,
                                )
                                stats["people_created"] += 1

                        elif kind in ("p", "h2", "notice"):
                            block_order += 1
                            text_val = raw_block[1]
                            if kind == "notice" and text_val == todo_text:
                                has_todo_notice = True
                            # Уникаємо дублювання номера телефону з SiteSettings у тексті блоку
                            if site_settings.phone and site_settings.phone in text_val:
                                text_val = text_val.replace(
                                    f": {site_settings.phone}", ""
                                ).replace(site_settings.phone, "").strip()
                                warnings_list.append(
                                    f"Сторінка «{page.title}»: номер телефону ({site_settings.phone}) "
                                    f"прибрано з текстового блоку, оскільки він централізовано зберігається в SiteSettings."
                                )
                            block = Block(
                                page=page,
                                block_type=kind,
                                order=block_order,
                                text=text_val,
                                data=None,
                            )
                            block.full_clean()
                            block.save()
                            stats["blocks_created"] += 1

                        elif kind in ("list", "steps"):
                            block_order += 1
                            items = list(raw_block[1])
                            block = Block(
                                page=page,
                                block_type=kind,
                                order=block_order,
                                text="",
                                data=items,
                            )
                            block.full_clean()
                            block.save()
                            stats["blocks_created"] += 1

                        elif kind == "table":
                            block_order += 1
                            caption, columns, rows = (
                                raw_block[1],
                                list(raw_block[2]),
                                [list(r) for r in raw_block[3]],
                            )
                            block = Block(
                                page=page,
                                block_type="table",
                                order=block_order,
                                text="",
                                data={
                                    "caption": caption,
                                    "columns": columns,
                                    "rows": rows,
                                },
                            )
                            block.full_clean()
                            block.save()
                            stats["blocks_created"] += 1

                        else:
                            raise CommandError(
                                f"Невідомий тип блоку «{kind}» на сторінці {section.slug}/{page_slug}."
                            )

                    if has_todo_notice and is_published:
                        warnings_list.append(
                            f"Сторінка «{section.title} / {page.title}» містить блок-нагадування TODO для адміністрації."
                        )

        # --- Виведення підсумкового звіту українською ---
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("=== ЗВІТ ПРО ІМПОРТ КАРТИ САЙТУ (import_site_map) ===")
        )
        self.stdout.write(f"Джерело даних: {resolved_path}")
        self.stdout.write(
            f"Налаштування сайту (SiteSettings): створено — {stats['settings_created']}, "
            f"пропущено (вже існували) — {stats['settings_skipped']}"
        )
        self.stdout.write(
            f"Розділи (Section):                 створено — {stats['sections_created']}, "
            f"пропущено (вже існували) — {stats['sections_skipped']}"
        )
        self.stdout.write(
            f"Сторінки (Page):                   створено — {stats['pages_created']} "
            f"(з них чернеток: {stats['pages_draft']}), "
            f"пропущено (вже існували) — {stats['pages_skipped']}"
        )
        self.stdout.write(
            f"Блоки вмісту (Block):              створено — {stats['blocks_created']}"
        )
        self.stdout.write(
            f"Документи без файлів (Document):   створено — {stats['documents_created']}"
        )
        self.stdout.write(
            f"Працівники (Person, без згоди):    створено — {stats['people_created']}"
        )

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

