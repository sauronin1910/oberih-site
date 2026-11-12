"""Моделі даних сайту КЗ «НРЦ «Оберіг»»."""
from io import BytesIO
from pathlib import Path
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image, UnidentifiedImageError
from simple_history.models import HistoricalRecords

# --- Константні обмеження для завантажуваних файлів ---
MAX_PDF_SIZE_MB = 20
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024

MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_IMAGE_DIMENSIONS = (1600, 1600)
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]


class AccentColor(models.TextChoices):
    """Палітра акцентних кольорів макета сайту."""

    TEAL = "teal", "Бірюзовий (teal)"
    SKY = "sky", "Блакитний (sky)"
    GREEN = "green", "Зелений (green)"
    CORAL = "coral", "Кораловий (coral)"
    ORANGE = "orange", "Помаранчевий (orange)"
    AMBER = "amber", "Бурштиновий (amber)"


class SectionIcon(models.TextChoices):
    """Доступні іконки розділів макета сайту."""

    ABOUT = "about", "Людина (Про нас)"
    DOC = "doc", "Документ"
    BOOK = "book", "Книга (Освіта)"
    STAR = "star", "Зірка (Виховна робота)"
    HOUSE = "house", "Будинок (Дошкільне відділення)"
    REHAB = "rehab", "Реабілітація"
    SHIELD = "shield", "Щит (Безпека та захист)"


# --- Безпечні шляхи збереження файлів ---
def _safe_filename(subdir: str, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return f"{subdir}/{uuid.uuid4().hex}{ext}"


def document_upload_to(instance, filename: str) -> str:
    return _safe_filename("documents", filename)


def person_photo_upload_to(instance, filename: str) -> str:
    return _safe_filename("people", filename)


def news_photo_upload_to(instance, filename: str) -> str:
    return _safe_filename("news", filename)


def homepage_image_upload_to(instance, filename: str) -> str:
    return _safe_filename("home", filename)


def sponsor_logo_upload_to(instance, filename: str) -> str:
    return _safe_filename("sponsors", filename)


# --- Валідатори та обробка файлів ---
def validate_pdf_file(value):
    """Перевіряє, що завантажений файл є справжнім PDF і не перевищує ліміт розміру."""
    if not value:
        return
    if value.size > MAX_PDF_SIZE_BYTES:
        raise ValidationError(
            f"Файл занадто великий ({value.size / (1024 * 1024):.1f} МБ). "
            f"Максимальний дозволений розмір PDF-файлу — {MAX_PDF_SIZE_MB} МБ."
        )
    file_obj = value.file if hasattr(value, "file") else value
    pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        header = file_obj.read(5)
    finally:
        if hasattr(file_obj, "seek"):
            file_obj.seek(pos)
    if header != b"%PDF-":
        raise ValidationError(
            "Завантажений файл не є коректним документом PDF. "
            "Будь ласка, збережіть документ у форматі PDF і спробуйте ще раз."
        )


def validate_image_file(value):
    """Перевіряє розмір і формат зображення (лише JPG або PNG)."""
    if not value:
        return
    if value.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Зображення занадто велике ({value.size / (1024 * 1024):.1f} МБ). "
            f"Максимальний дозволений розмір — {MAX_IMAGE_SIZE_MB} МБ."
        )
    file_obj = value.file if hasattr(value, "file") else value
    pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        with Image.open(file_obj) as img:
            img.verify()
            fmt = (img.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(
            "Файл пошкоджений або не є зображенням. Завантажте фото у форматі JPG або PNG."
        ) from exc
    finally:
        if hasattr(file_obj, "seek"):
            file_obj.seek(pos)

    if fmt not in ("JPEG", "PNG"):
        raise ValidationError(
            "Дозволено завантажувати лише зображення у форматах JPG (JPEG) або PNG."
        )


def compress_image_field(image_field) -> None:
    """Автоматично зменшує та оптимізує завантажене зображення за допомогою Pillow."""
    if not image_field or getattr(image_field, "_committed", True):
        return
    file_obj = image_field.file if hasattr(image_field, "file") else image_field
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    with Image.open(file_obj) as img:
        orig_format = (img.format or "JPEG").upper()
        img.thumbnail(MAX_IMAGE_DIMENSIONS, Image.Resampling.LANCZOS)
        buffer = BytesIO()

        if orig_format == "PNG":
            if img.mode not in ("RGB", "RGBA", "P"):
                img = img.convert("RGBA")
            img.save(buffer, format="PNG", optimize=True)
            ext = ".png"
        else:
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            ext = ".jpg"

    new_name = f"{Path(image_field.name).stem}{ext}"
    image_field.save(new_name, ContentFile(buffer.getvalue()), save=False)


# --- 1. Налаштування сайту (Singleton) ---
class SiteSettings(models.Model):
    """Єдиний запис із наскрізними контактами та реквізитами закладу."""

    phone = models.CharField(
        "Телефон",
        max_length=50,
        default="(0342) 55-05-24",
        help_text="Основний контактний номер телефону закладу (показується в шапці, меню та контактах).",
    )
    email = models.EmailField(
        "Електронна пошта",
        default="nrts.oberih@osvita.if.ua",
        help_text="Офіційна адреса електронної пошти закладу.",
    )
    address = models.CharField(
        "Адреса",
        max_length=255,
        default="вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020",
        help_text="Повна поштова адреса закладу.",
    )
    director_name = models.CharField(
        "Директор (ПІБ)",
        max_length=200,
        default="Шестопалова Галина Любомирівна",
        help_text="Прізвище, ім'я та по батькові керівника закладу.",
    )
    map_url = models.URLField(
        "Посилання на карту",
        max_length=500,
        default=(
            "https://www.google.com/maps/search/?api=1&query="
            "%D0%B2%D1%83%D0%BB.+%D0%93%D0%BD%D0%B0%D1%82%D0%B0+"
            "%D0%A5%D0%BE%D1%82%D0%BA%D0%B5%D0%B2%D0%B8%D1%87%D0%B0+52%D0%90+"
            "%D0%86%D0%B2%D0%B0%D0%BD%D0%BE-%D0%A4%D1%80%D0%B0%D0%BD%D0%BA%D1%96%D0%B2%D1%81%D1%8C%D0%BA"
        ),
        help_text="Посилання на Google Карти з точкою розташування закладу.",
    )
    footer_text = models.CharField(
        "Текст у підвалі сайту",
        max_length=300,
        default="© 2026 НРЦ «Оберіг». Матеріали сайту використовуються з посиланням на джерело.",
        help_text="Короткий підпис у найнижчій частині всіх сторінок сайту.",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self) -> str:
        return "Загальні налаштування сайту НРЦ «Оберіг»"

    def clean(self):
        super().clean()
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError(
                "Налаштування сайту вже створені. Відредагуйте існуючий запис замість створення нового."
            )

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        super().save(*args, **kwargs)


# --- 2. Розділ сайту ---
class Section(models.Model):
    """Основний розділ меню сайту."""

    slug = models.SlugField(
        "Адреса розділу (slug)",
        max_length=100,
        unique=True,
        help_text="Частина веб-адреси латиницею без пробілів (наприклад: pro-nas). Не змінюйте без потреби.",
    )
    title = models.CharField(
        "Назва розділу",
        max_length=200,
        help_text="Назва, яку бачать відвідувачі в головному меню та в заголовку розділу.",
    )
    lead = models.TextField(
        "Короткий опис (лід)",
        blank=True,
        help_text="Одне-два речення під заголовком розділу, що пояснюють, про що цей розділ.",
    )
    color = models.CharField(
        "Колір оформлення",
        max_length=20,
        choices=AccentColor.choices,
        default=AccentColor.TEAL,
        help_text="Колір плашки та акцентів розділу відповідно до дизайну сайту.",
    )
    icon = models.CharField(
        "Іконка розділу",
        max_length=20,
        choices=SectionIcon.choices,
        default=SectionIcon.DOC,
        help_text="Іконка для оформлення карток розділу.",
    )
    order = models.PositiveIntegerField(
        "Порядок у меню",
        default=0,
        help_text="Менше число — вище (лівіше) у меню. Наприклад: 1, 2, 3.",
    )
    show_in_menu = models.BooleanField(
        "Показувати в меню",
        default=True,
        help_text="Зніміть позначку, якщо розділ потрібно тимчасово приховати з головного меню.",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Розділ сайту"
        verbose_name_plural = "Розділи сайту"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


# --- 3. Внутрішня сторінка ---
class Page(models.Model):
    """Внутрішня сторінка, що належить певному розділу."""

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name="Розділ",
        help_text="Розділ меню, до якого входить ця сторінка.",
    )
    slug = models.SlugField(
        "Адреса сторінки (slug)",
        max_length=120,
        help_text="Частина веб-адреси сторінки латиницею (наприклад: statut або rezhym-roboty).",
    )
    title = models.CharField(
        "Назва сторінки",
        max_length=255,
        help_text="Головний заголовок сторінки та її назва в підменю розділу.",
    )
    lead = models.TextField(
        "Короткий опис (лід)",
        blank=True,
        help_text="Коротке пояснення під заголовком сторінки.",
    )
    meta_description = models.CharField(
        "Опис для пошукових систем (meta description)",
        max_length=300,
        blank=True,
        help_text="Короткий опис сторінки для Google (якщо залишити порожнім, використається короткий опис).",
    )
    is_published = models.BooleanField(
        "Опубліковано",
        default=True,
        help_text="Якщо зняти позначку, сторінка буде чернеткою і не показуватиметься відвідувачам.",
    )
    order = models.PositiveIntegerField(
        "Порядок у розділі",
        default=0,
        help_text="Порядковий номер сторінки в меню розділу (менше число — вище у списку).",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Сторінка"
        verbose_name_plural = "Сторінки"
        ordering = ["section__order", "order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "slug"],
                name="unique_page_section_slug",
            )
        ]

    def __str__(self) -> str:
        return f"{self.section.title} — {self.title}"


# --- 4. Контентний блок сторінки ---
class Block(models.Model):
    """Блок вмісту на внутрішній сторінці (абзац, підзаголовок, список, кроки, примітка, таблиця)."""

    class BlockType(models.TextChoices):
        PARAGRAPH = "p", "Абзац тексту (p)"
        HEADING = "h2", "Підзаголовок (h2)"
        LIST = "list", "Маркований список (list)"
        STEPS = "steps", "Нумеровані кроки (steps)"
        NOTICE = "notice", "Важлива примітка в рамці (notice)"
        TABLE = "table", "Таблиця (table)"

    TEXT_TYPES = {BlockType.PARAGRAPH, BlockType.HEADING, BlockType.NOTICE}
    JSON_LIST_TYPES = {BlockType.LIST, BlockType.STEPS}

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="blocks",
        verbose_name="Сторінка",
        help_text="Сторінка, на якій розміщується цей блок.",
    )
    block_type = models.CharField(
        "Тип блоку",
        max_length=16,
        choices=BlockType.choices,
        default=BlockType.PARAGRAPH,
        help_text="Оберіть вигляд блоку: звичайний абзац, підзаголовок, список, кроки, примітка або таблиця.",
    )
    order = models.PositiveIntegerField(
        "Порядок на сторінці",
        default=0,
        help_text="Порядковий номер блоку зверху вниз (менше число — вище на сторінці).",
    )
    text = models.TextField(
        "Текст блоку",
        blank=True,
        help_text="Заповнюється лише для типів «Абзац», «Підзаголовок» та «Важлива примітка».",
    )
    data = models.JSONField(
        "Структуровані дані (список або таблиця)",
        blank=True,
        null=True,
        help_text=(
            "Заповнюється лише для списків, кроків і таблиць. "
            "Для списку/кроків: [\"Пункт 1\", \"Пункт 2\"]. "
            "Для таблиці: {\"caption\": \"Назва\", \"columns\": [\"Колонка 1\"], \"rows\": [[\"Значення 1\"]]}."
        ),
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Блок вмісту"
        verbose_name_plural = "Блоки вмісту"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.page.title}: {self.get_block_type_display()} (#{self.order})"

    def clean(self):
        super().clean()
        has_text = bool(self.text and self.text.strip())
        has_data = self.data not in (None, "", [], {})

        if self.block_type in self.TEXT_TYPES:
            if not has_text:
                raise ValidationError(
                    {"text": "Для обраного типу блоку необхідно заповнити поле «Текст блоку»."}
                )
            if has_data:
                raise ValidationError(
                    {"data": "Для текстового блоку поле «Структуровані дані» має бути порожнім."}
                )
            self.data = None

        elif self.block_type in self.JSON_LIST_TYPES:
            if has_text:
                raise ValidationError(
                    {"text": "Для списку або кроків поле «Текст блоку» має бути порожнім (використовуйте поле даних)."}
                )
            if not isinstance(self.data, list) or not self.data:
                raise ValidationError(
                    {"data": "Вкажіть непорожній список текстових пунктів, наприклад: [\"Перший пункт\", \"Другий пункт\"]."}
                )
            if not all(isinstance(item, str) and item.strip() for item in self.data):
                raise ValidationError(
                    {"data": "Кожен пункт списку має бути непорожнім текстовим рядком."}
                )

        elif self.block_type == self.BlockType.TABLE:
            if has_text:
                raise ValidationError(
                    {"text": "Для таблиці поле «Текст блоку» має бути порожнім."}
                )
            if not isinstance(self.data, dict):
                raise ValidationError(
                    {
                        "data": (
                            "Дані таблиці мають бути об'єктом із ключами "
                            "\"caption\" (заголовок), \"columns\" (колонки) та \"rows\" (рядки)."
                        )
                    }
                )
            caption = self.data.get("caption")
            columns = self.data.get("columns")
            rows = self.data.get("rows")

            if not isinstance(caption, str) or not caption.strip():
                raise ValidationError(
                    {"data": "У таблиці обов'язково має бути непорожній заголовок (\"caption\")."}
                )
            if (
                not isinstance(columns, list)
                or not columns
                or not all(isinstance(col, str) and col.strip() for col in columns)
            ):
                raise ValidationError(
                    {"data": "Поле \"columns\" має містити непорожній список назв колонок таблиці."}
                )
            if not isinstance(rows, list) or not rows:
                raise ValidationError(
                    {"data": "Поле \"rows\" має містити список рядків таблиці (щонайменше один рядок)."}
                )
            col_count = len(columns)
            for idx, row in enumerate(rows, start=1):
                if (
                    not isinstance(row, list)
                    or len(row) != col_count
                    or not all(isinstance(cell, str) for cell in row)
                ):
                    raise ValidationError(
                        {
                            "data": (
                                f"Рядок №{idx} таблиці має бути списком текстових клітинок "
                                f"із тією ж кількістю значень, що й кількість колонок ({col_count})."
                            )
                        }
                    )


# --- 5. Офіційний документ (PDF) ---
class Document(models.Model):
    """PDF-документ, прикріплений до сторінки сайту."""

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Сторінка",
        help_text="Сторінка, на якій буде опубліковано цей документ.",
    )
    title = models.CharField(
        "Назва документа",
        max_length=255,
        help_text="Зрозуміла назва документа (наприклад: Статут закладу або Фінансовий звіт за 2026 рік).",
    )
    file = models.FileField(
        "PDF-файл",
        upload_to=document_upload_to,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"],
                message="Дозволено завантажувати лише файли у форматі PDF (.pdf).",
            ),
            validate_pdf_file,
        ],
        help_text=f"Завантажте файл у форматі PDF (максимальний розмір — {MAX_PDF_SIZE_MB} МБ).",
    )
    order = models.PositiveIntegerField(
        "Порядок у списку",
        default=0,
        help_text="Порядковий номер документа на сторінці (менше число — вище у списку).",
    )
    show_st30_notice = models.BooleanField(
        "Показувати примітку про ст. 30 Закону України «Про освіту»",
        default=False,
        help_text="Увімкніть, якщо під документом потрібна офіційна примітка про оприлюднення згідно зі ст. 30 ЗУ «Про освіту».",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Документ (PDF)"
        verbose_name_plural = "Документи (PDF)"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.title} ({self.page.title})"


# --- 6. Працівник закладу ---
class PersonQuerySet(models.QuerySet):
    """Набір запитів із фільтрацією за наявністю письмової згоди."""

    def with_consent(self):
        return self.filter(consent_given=True)


class PublishedPersonManager(models.Manager):
    """Менеджер, який повертає лише працівників із наданою згодою на публікацію."""

    def get_queryset(self):
        return PersonQuerySet(self.model, using=self._db).with_consent()


class Person(models.Model):
    """Картка працівника (адміністрація, педагогічний колектив)."""

    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="people",
        verbose_name="Сторінка",
        help_text="Сторінка (наприклад, «Адміністрація» або «Педагогічний колектив»), де відображається працівник.",
    )
    position = models.CharField(
        "Посада",
        max_length=200,
        help_text="Посада працівника (наприклад: Директор, Вчитель-логопед, Практичний психолог).",
    )
    full_name = models.CharField(
        "Прізвище, ім'я та по батькові",
        max_length=200,
        help_text="Повне ПІБ працівника.",
    )
    photo = models.ImageField(
        "Фотографія",
        upload_to=person_photo_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
                message="Дозволено завантажувати лише фото у форматах JPG або PNG.",
            ),
            validate_image_file,
        ],
        help_text="Необов'язкове фото працівника (формат JPG або PNG, стискається автоматично).",
    )
    consent_given = models.BooleanField(
        "Наявна письмова згода на публікацію персональних даних",
        default=False,
        help_text=(
            "ОБОВ'ЯЗКОВО: позначте лише за наявності письмової згоди працівника. "
            "Без цієї позначки картка працівника на сайті НЕ показується."
        ),
    )
    order = models.PositiveIntegerField(
        "Порядок відображення",
        default=0,
        help_text="Порядковий номер картки на сторінці (менше число — вище у списку).",
    )

    objects = PersonQuerySet.as_manager()
    published = PublishedPersonManager()
    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Працівники"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        status = "опубліковано" if self.consent_given else "без згоди — приховано"
        return f"{self.full_name} — {self.position} ({status})"

    def save(self, *args, **kwargs):
        if self.photo:
            compress_image_field(self.photo)
        super().save(*args, **kwargs)


# --- 7. Новина ---
class NewsItem(models.Model):
    """Публікація в розділі «Новини» та в каруселі на головній сторінці."""

    title = models.CharField(
        "Заголовок новини",
        max_length=255,
        help_text="Короткий і зрозумілий заголовок події або оголошення.",
    )
    slug = models.SlugField(
        "Адреса новини (slug)",
        max_length=255,
        unique=True,
        help_text="Унікальна частина веб-адреси новини латиницею (наприклад: osinnii-tyzhden-ihor).",
    )
    category = models.CharField(
        "Категорія",
        max_length=100,
        default="Події",
        help_text="Коротка рубрика новини (наприклад: Події, Батькам, Оголошення, Реабілітація, Свята).",
    )
    accent_color = models.CharField(
        "Колір акценту картки",
        max_length=20,
        choices=AccentColor.choices,
        default=AccentColor.CORAL,
        help_text="Колір верхньої смужки та рубрики на картці новини.",
    )
    published_date = models.DateField(
        "Дата публікації",
        help_text="Дата події або публікації, за якою сортуються новини (від найновіших).",
    )
    summary = models.TextField(
        "Короткий анонс",
        help_text="Кілька речень для картки новини на головній сторінці та в загальному списку новин.",
    )
    body = models.TextField(
        "Повний текст новини",
        help_text="Основний текст статті. Абзаци розділяйте порожнім рядком.",
    )
    photo = models.ImageField(
        "Фотографія новини",
        upload_to=news_photo_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
                message="Дозволено завантажувати лише фото у форматах JPG або PNG.",
            ),
            validate_image_file,
        ],
        help_text=(
            "Необов'язкове фото до новини (JPG або PNG). "
            "Увага: фото з дітьми публікуються виключно за письмової згоди батьків!"
        ),
    )
    is_published = models.BooleanField(
        "Опубліковано на сайті",
        default=True,
        help_text="Зніміть позначку, щоб зберегти новину як чернетку без показу на сайті.",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Новина"
        verbose_name_plural = "Новини"
        ordering = ["-published_date", "-id"]

    def __str__(self) -> str:
        return f"{self.published_date:%d.%m.%Y} — {self.title}"

    def save(self, *args, **kwargs):
        if self.photo:
            compress_image_field(self.photo)
        super().save(*args, **kwargs)


# --- 8. Головна сторінка (Singleton) ---
class HomePage(models.Model):
    """Єдиний запис для редагування текстових секцій головної сторінки."""

    # Героїчний блок (#intro)
    hero_eyebrow = models.CharField(
        "Перший екран: надзаголовок",
        max_length=200,
        default="Івано-Франківськ · вул. Гната Хоткевича, 52-А",
        help_text="Короткий рядок над головним заголовком першого екрана.",
    )
    hero_title = models.CharField(
        "Перший екран: головний заголовок",
        max_length=255,
        default="Навчання і реабілітація в одному місці",
        help_text="Головний заголовок (H1) на першому екрані сайту.",
    )
    hero_lead = models.TextField(
        "Перший екран: підзаголовок (опис)",
        default=(
            "НРЦ «Оберіг» навчає дітей з особливими освітніми потребами, зокрема з порушеннями "
            "опорно-рухового апарату. Уроки поєднуємо з фізичною терапією, корекційними заняттями "
            "та психологічною підтримкою."
        ),
        help_text="Пояснювальний текст під головним заголовком першого екрана.",
    )

    # Секція «Про НРЦ «Оберіг»» (#about)
    about_eyebrow = models.CharField(
        "Блок «Про нас»: надзаголовок",
        max_length=150,
        default="Про НРЦ «Оберіг»",
        help_text="Малий підпис над заголовком секції «Про нас».",
    )
    about_title = models.CharField(
        "Блок «Про нас»: заголовок",
        max_length=255,
        default="Кожна дитина вчиться у своєму темпі",
        help_text="Заголовок секції «Про НРЦ «Оберіг»».",
    )
    about_text = models.TextField(
        "Блок «Про нас»: основний текст",
        default=(
            "НРЦ «Оберіг» — комунальний заклад Івано-Франківської міської ради для дітей з особливими "
            "освітніми потребами. Ми поєднуємо загальну середню освіту з комплексною реабілітацією, "
            "щоб навчання й відновлення йшли поруч, а не конкурували за час дитини.\n\n"
            "Над кожною дитиною працює команда: вчителі, асистенти, фізичні терапевти, логопеди, "
            "психологи. Разом із батьками вони складають індивідуальну програму розвитку і "
            "переглядають її впродовж року."
        ),
        help_text="Основний опис закладу на головній сторінці (абзаци розділяйте порожнім рядком).",
    )
    about_quote = models.TextField(
        "Блок «Про нас»: виділена цитата або примітка",
        blank=True,
        default="Тексти на цій сторінці тимчасові. Їх замінить опис НРЦ «Оберіг» від адміністрації.",
        help_text="Виділений блок-цитата під текстом «Про нас» (можна залишити порожнім).",
    )

    # Секція «Документи» (#documents)
    docs_eyebrow = models.CharField(
        "Блок «Документи»: надзаголовок",
        max_length=150,
        default="Прозорість та відкритість",
        help_text="Малий підпис над заголовком секції документів.",
    )
    docs_title = models.CharField(
        "Блок «Документи»: заголовок",
        max_length=255,
        default="Документи НРЦ «Оберіг»",
        help_text="Заголовок секції документів на головній сторінці.",
    )
    docs_note = models.TextField(
        "Блок «Документи»: пояснення",
        default=(
            "Оприлюднюємо документи відповідно до статті 30 Закону України «Про освіту» "
            "не пізніше ніж через 10 робочих днів після затвердження."
        ),
        help_text="Коротке пояснення поруч зі списком основних документів.",
    )

    # Секція «Безпека та захист» (#safety)
    safety_eyebrow = models.CharField(
        "Блок «Безпека»: надзаголовок",
        max_length=150,
        default="Безпека та захист",
        help_text="Малий підпис над заголовком секції безпеки.",
    )
    safety_title = models.CharField(
        "Блок «Безпека»: заголовок",
        max_length=255,
        default="Якщо дитину кривдять, є кому допомогти",
        help_text="Заголовок секції безпеки та протидії булінгу.",
    )
    safety_text = models.TextField(
        "Блок «Безпека»: текст",
        default=(
            "Повідомити про булінг можна класному керівнику, психологу або директору НРЦ «Оберіг». "
            "Заяви розглядаємо конфіденційно."
        ),
        help_text="Пояснювальний текст у секції безпеки.",
    )

    # Секція «Запрошуємо» (#welcome)
    welcome_eyebrow = models.CharField(
        "Блок «Запрошуємо»: надзаголовок",
        max_length=150,
        default="Запрошуємо",
        help_text="Малий підпис над заголовком секції запрошення.",
    )
    welcome_title = models.CharField(
        "Блок «Запрошуємо»: заголовок",
        max_length=255,
        default="У НРЦ «Оберіг» кожна дитина серед друзів",
        help_text="Заголовок секції запрошення на головній сторінці.",
    )
    welcome_text = models.TextField(
        "Блок «Запрошуємо»: текст",
        default=(
            "Діти вчаться, граються і займаються разом, а фахівці дбають, щоб кожному було комфортно. "
            "Розкажемо, як вступити до НРЦ «Оберіг», і відповімо на ваші запитання."
        ),
        help_text="Запрошувальний текст для батьків та відвідувачів.",
    )
    welcome_image = models.ImageField(
        "Блок «Запрошуємо»: ілюстрація або фото",
        upload_to=homepage_image_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
                message="Дозволено завантажувати лише зображення у форматах JPG або PNG.",
            ),
            validate_image_file,
        ],
        help_text="Якщо не завантажено, використовується стандартна ілюстрація макета (img/kids.jpg).",
    )

    # Секція «Наші спонсори» (#sponsors)
    sponsors_eyebrow = models.CharField(
        "Блок «Спонсори»: надзаголовок",
        max_length=150,
        default="Разом із нами",
        help_text="Малий підпис над заголовком секції спонсорів.",
    )
    sponsors_title = models.CharField(
        "Блок «Спонсори»: заголовок",
        max_length=255,
        default="Наші спонсори",
        help_text="Заголовок секції благодійників і спонсорів.",
    )
    sponsors_text = models.TextField(
        "Блок «Спонсори»: опис",
        default=(
            "Дякуємо всім, хто підтримує дітей НРЦ «Оберіг». "
            "Звіти про отриману допомогу оприлюднюємо в розділі «Прозорість та відкритість»."
        ),
        help_text="Текст подяки над логотипами спонсорів.",
    )
    sponsors_note = models.CharField(
        "Блок «Спонсори»: примітка внизу",
        max_length=300,
        blank=True,
        default="Логотипи — приклад. Справжні з'являться після погодження зі спонсорами.",
        help_text="Необов'язкова примітка під списком логотипів спонсорів.",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Головна сторінка"
        verbose_name_plural = "Головна сторінка"

    def __str__(self) -> str:
        return "Вміст головної сторінки НРЦ «Оберіг»"

    def clean(self):
        super().clean()
        if not self.pk and HomePage.objects.exists():
            raise ValidationError(
                "Запис головної сторінки вже існує. Відредагуйте існуючий запис."
            )

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        if self.welcome_image:
            compress_image_field(self.welcome_image)
        super().save(*args, **kwargs)


# --- 9. Спонсор / благодійник ---
class Sponsor(models.Model):
    """Картка спонсора або партнера в секції «Наші спонсори»."""

    name = models.CharField(
        "Назва спонсора або організації",
        max_length=200,
        help_text="Назва компанії, фонду чи партнера (використовується також як підпис до логотипа).",
    )
    logo = models.ImageField(
        "Логотип",
        upload_to=sponsor_logo_upload_to,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
                message="Дозволено завантажувати лише логотипи у форматах JPG або PNG.",
            ),
            validate_image_file,
        ],
        help_text="Зображення логотипа у форматі PNG або JPG (стискається автоматично).",
    )
    url = models.URLField(
        "Посилання на сайт спонсора",
        max_length=500,
        blank=True,
        help_text="Необов'язкова веб-адреса сайту спонсора (починається з https://).",
    )
    order = models.PositiveIntegerField(
        "Порядок відображення",
        default=0,
        help_text="Порядковий номер логотипа у списку (менше число — раніше у списку).",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Спонсор"
        verbose_name_plural = "Спонсори"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.logo:
            compress_image_field(self.logo)
        super().save(*args, **kwargs)


# --- 10. Звернення з форми зворотного зв'язку ---
class ContactMessage(models.Model):
    """Повідомлення відвідувача з форми «Поставити запитання» (лише для читання в адмінці)."""

    name = models.CharField(
        "Ім'я відправника",
        max_length=150,
        help_text="Ім'я, яке вказав відвідувач у формі звернення.",
    )
    email = models.EmailField(
        "Електронна пошта для відповіді",
        help_text="Адреса електронної пошти відвідувача, куди слід надіслати відповідь.",
    )
    message = models.TextField(
        "Текст запитання",
        help_text="Зміст звернення або запитання відвідувача.",
    )
    consent_given = models.BooleanField(
        "Надано згоду на обробку персональних даних",
        default=False,
        help_text="Позначка про те, що відвідувач погодився на обробку своїх персональних даних.",
    )
    created_at = models.DateTimeField(
        "Дата і час отримання",
        auto_now_add=True,
        help_text="Коли саме звернення надійшло через сайт.",
    )
    is_read = models.BooleanField(
        "Опрацьовано (прочитано)",
        default=False,
        help_text="Позначте після того, як адміністрація прочитала звернення та надала відповідь.",
    )

    history = HistoricalRecords(verbose_name="Історія змін")

    class Meta:
        verbose_name = "Звернення з форми"
        verbose_name_plural = "Звернення з форми"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        status = "прочитано" if self.is_read else "нове"
        return f"Звернення від {self.name} ({self.email}) — {status}"
