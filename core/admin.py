"""Налаштування панелі адміністратора (/admin-panel/) для сайту КЗ «НРЦ «Оберіг»»."""
from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    MAX_PDF_SIZE_MB,
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
)

# --- Заголовки адмін-панелі українською ---
admin.site.site_header = "Адмін-панель НРЦ «Оберіг»"
admin.site.site_title = "Адмін-панель НРЦ «Оберіг»"
admin.site.index_title = "Адмін-панель НРЦ «Оберіг»"

# --- Порядок розділів на головній сторінці адмінки ---
ADMIN_MODEL_ORDER = {
    "Page": 1,
    "Section": 2,
    "NewsItem": 3,
    "ContactMessage": 4,
    "Person": 5,
    "Document": 6,
    "HomePage": 7,
    "SiteSettings": 8,
    "Sponsor": 9,
}

_orig_get_app_list = admin.site.get_app_list


def _ordered_get_app_list(request, app_label=None):
    app_list = _orig_get_app_list(request, app_label)
    for app in app_list:
        if app["app_label"] == "core":
            app["models"].sort(
                key=lambda m: ADMIN_MODEL_ORDER.get(m["object_name"], 99)
            )
    return app_list


admin.site.get_app_list = _ordered_get_app_list


# --- Форма для блоку вмісту (без показу JSON редактору) ---
class BlockAdminForm(forms.ModelForm):
    """Зручна форма для редагування блоків сторінки без роботи з JSON."""

    items_text = forms.CharField(
        label="Пункти списку (кожен пункт з нового рядка)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Перший пункт\nДругий пункт\nТретій пункт",
            }
        ),
        help_text="Використовується для маркованого списку або нумерованих кроків. Кожен рядок стане окремим пунктом.",
    )
    table_caption = forms.CharField(
        label="Заголовок (підпис) таблиці",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Наприклад: Режим роботи закладу"}
        ),
        help_text="Коротка назва таблиці (обов'язкова для доступності).",
    )
    table_text = forms.CharField(
        label="Таблиця (перший рядок: заголовки через « | », далі рядки)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": (
                    "Дні | Час\n"
                    "Понеділок — п’ятниця | 08:30 – 17:00\n"
                    "Субота, неділя | вихідні"
                ),
            }
        ),
        help_text=(
            "Перший рядок — назви колонок, розділені знаком « | ». "
            "Кожен наступний рядок — дані клітинок через « | »."
        ),
    )

    class Meta:
        model = Block
        fields = (
            "block_type",
            "order",
            "text",
            "items_text",
            "table_caption",
            "table_text",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.data:
            btype = self.instance.block_type
            data = self.instance.data
            if btype in Block.JSON_LIST_TYPES and isinstance(data, list):
                self.fields["items_text"].initial = "\n".join(
                    str(item) for item in data
                )
            elif btype == Block.BlockType.TABLE and isinstance(data, dict):
                self.fields["table_caption"].initial = data.get("caption", "")
                cols = data.get("columns", [])
                rows = data.get("rows", [])
                lines = []
                if cols:
                    lines.append(" | ".join(str(c) for c in cols))
                for row in rows:
                    lines.append(" | ".join(str(c) for c in row))
                self.fields["table_text"].initial = "\n".join(lines)

    def clean(self):
        cleaned_data = super().clean()
        block_type = cleaned_data.get("block_type")
        text = (cleaned_data.get("text") or "").strip()
        items_text = (cleaned_data.get("items_text") or "").strip()
        table_caption = (cleaned_data.get("table_caption") or "").strip()
        table_text = (cleaned_data.get("table_text") or "").strip()

        if block_type in Block.TEXT_TYPES:
            if not text:
                self.add_error(
                    "text",
                    "Введіть текст для цього блоку (абзацу, підзаголовка або примітки).",
                )
            cleaned_data["text"] = text
            self.instance.text = text
            self.instance.data = None

        elif block_type in Block.JSON_LIST_TYPES:
            items = [line.strip() for line in items_text.splitlines() if line.strip()]
            if not items:
                self.add_error(
                    "items_text",
                    "Введіть щонайменше один пункт списку (кожен пункт з нового рядка).",
                )
            cleaned_data["text"] = ""
            self.instance.text = ""
            self.instance.data = items

        elif block_type == Block.BlockType.TABLE:
            if not table_caption:
                self.add_error(
                    "table_caption",
                    "Вкажіть короткий заголовок (підпис) таблиці.",
                )
            lines = [line.strip() for line in table_text.splitlines() if line.strip()]
            if len(lines) < 2:
                self.add_error(
                    "table_text",
                    "Таблиця має містити щонайменше 2 рядки: перший рядок — заголовки колонок через « | », другий — дані.",
                )
                self.instance.text = ""
                self.instance.data = None
                return cleaned_data

            columns = [col.strip() for col in lines[0].split("|")]
            if not all(columns):
                self.add_error(
                    "table_text",
                    "У першому рядку всі колонки повинні мати назву (не залишайте порожніх місць між « | »).",
                )
                return cleaned_data

            col_count = len(columns)
            rows = []
            for row_idx, line in enumerate(lines[1:], start=2):
                cells = [cell.strip() for cell in line.split("|")]
                if len(cells) != col_count:
                    self.add_error(
                        "table_text",
                        f"У рядку №{row_idx} вказано {len(cells)} значень, а колонок у заголовку — {col_count}. "
                        f"Перевірте кількість роздільників « | ».",
                    )
                    return cleaned_data
                rows.append(cells)

            cleaned_data["text"] = ""
            self.instance.text = ""
            self.instance.data = {
                "caption": table_caption,
                "columns": columns,
                "rows": rows,
            }

        return cleaned_data

    def _post_clean(self):
        if self.errors:
            return
        super()._post_clean()


# --- Базовий клас для одиничних записів (SiteSettings, HomePage) ---
class SingletonModelAdmin(SimpleHistoryAdmin):
    """Адмін-клас для моделей з єдиним записом: одразу відкриває редагування."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=[obj.pk],
        )
        return HttpResponseRedirect(url)


# --- Вбудовані таблиці (Inlines) для сторінки Page ---
class BlockInline(admin.StackedInline):
    model = Block
    form = BlockAdminForm
    extra = 0
    classes = ["collapse"]
    verbose_name = "Блок тексту, списку або таблиці"
    verbose_name_plural = "1. Текстові блоки, списки та таблиці сторінки"
    description = (
        "Тут редагується основний текст сторінки: абзаци, підзаголовки, списки та таблиці. "
        "Поле «Порядок на сторінці» задається числом (1, 2, 3...) — менше число показується вище."
    )


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    classes = ["collapse"]
    fields = ("order", "title", "file", "show_st30_notice")
    verbose_name = "Документ (PDF)"
    verbose_name_plural = "2. Офіційні документи (PDF) на цій сторінці"
    description = (
        f"Прикріпіть PDF-файли (до {MAX_PDF_SIZE_MB} МБ), які мають відображатися на сторінці. "
        "Якщо файл ще готується, залиште поле файлу порожнім. Порядок задається числом."
    )


class PersonInline(admin.TabularInline):
    model = Person
    extra = 0
    classes = ["collapse"]
    fields = ("order", "position", "full_name", "photo", "consent_given")
    verbose_name = "Картка працівника"
    verbose_name_plural = "3. Працівники на цій сторінці (Адміністрація / Педагогічний колектив)"
    description = (
        "Картки працівників закладу. УВАГА: картка з'явиться на сайті ЛИШЕ тоді, "
        "коли заповнено ПІБ і поставлено галочку «Є письмова згода на оприлюднення»."
    )


# --- 1. Сторінки сайту (Page) ---
@admin.register(Page)
class PageAdmin(SimpleHistoryAdmin):
    list_display = (
        "title",
        "section",
        "publication_status",
        "updated_at",
        "order",
    )
    list_filter = ("section", "is_published")
    search_fields = ("title", "lead", "slug")
    list_select_related = ("section",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [BlockInline, DocumentInline, PersonInline]

    fieldsets = (
        (
            "Основна інформація про сторінку",
            {
                "fields": (
                    "section",
                    "title",
                    "slug",
                    "lead",
                    "is_published",
                    "order",
                ),
                "description": "Основні налаштування сторінки. Нижче у згорнутих блоках редагуються тексти, документи та працівники.",
            },
        ),
        (
            "Налаштування для пошукових систем (необов'язково)",
            {
                "classes": ("collapse",),
                "fields": ("meta_description",),
            },
        ),
    )

    class Media:
        css = {"all": ("core/admin/admin.css",)}
        js = ("core/admin/block_form.js",)

    @admin.display(description="Статус публікації", ordering="is_published")
    def publication_status(self, obj: Page):
        if obj.is_published:
            return format_html(
                '<span class="oberih-badge oberih-badge--published">Опубліковано</span>'
            )
        return format_html(
            '<span class="oberih-badge oberih-badge--draft">Чернетка</span>'
        )

    def delete_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = (
            "Ви впевнені, що хочете видалити цю сторінку? "
            "Разом із нею будуть видалені всі її текстові блоки, документи та картки працівників."
        )
        messages.warning(
            request,
            "Увага! Видалення сторінки призведе до видалення всіх прикріплених до неї блоків, документів і карток працівників. "
            "Якщо сторінку потрібно лише тимчасово сховати з сайту, поверніться назад і зніміть галочку «Опубліковано».",
        )
        return super().delete_view(request, object_id, extra_context=extra_context)


# --- 2. Розділи меню (Section) ---
@admin.register(Section)
class SectionAdmin(SimpleHistoryAdmin):
    list_display = ("title", "order", "show_in_menu", "color", "slug")
    list_editable = ("order", "show_in_menu")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "lead")


# --- 3. Новини (NewsItem) ---
@admin.register(NewsItem)
class NewsItemAdmin(SimpleHistoryAdmin):
    list_display = (
        "title",
        "category",
        "published_date",
        "publication_status",
        "is_published",
    )
    list_editable = ("is_published",)
    list_filter = ("is_published", "category", "published_date")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_date"

    fieldsets = (
        (
            "Публікація новини",
            {
                "fields": (
                    "title",
                    "slug",
                    ("category", "accent_color"),
                    ("published_date", "is_published"),
                    "summary",
                    "body",
                    "photo",
                )
            },
        ),
    )

    class Media:
        css = {"all": ("core/admin/admin.css",)}

    @admin.display(description="Статус", ordering="is_published")
    def publication_status(self, obj: NewsItem):
        if obj.is_published:
            return format_html(
                '<span class="oberih-badge oberih-badge--published">Опубліковано</span>'
            )
        return format_html(
            '<span class="oberih-badge oberih-badge--draft">Чернетка</span>'
        )


# --- 4. Звернення з форми зворотного зв'язку (ContactMessage) ---
@admin.register(ContactMessage)
class ContactMessageAdmin(SimpleHistoryAdmin):
    list_display = ("created_at", "name", "email", "is_read")
    list_editable = ("is_read",)
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = ("created_at", "name", "email", "message", "consent_given")
    fields = ("created_at", "name", "email", "message", "consent_given", "is_read")
    actions = ["mark_as_read"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Позначити вибрані звернення як прочитані")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request,
            f"Позначено як прочитані: {updated} звернень.",
            messages.SUCCESS,
        )


# --- 5. Працівники (Person) ---
@admin.register(Person)
class PersonAdmin(SimpleHistoryAdmin):
    list_display = (
        "position",
        "full_name_display",
        "page",
        "consent_icon",
        "order",
    )
    list_editable = ("order",)
    list_filter = ("consent_given", "page__section", "page")
    search_fields = ("full_name", "position", "page__title")
    list_select_related = ("page", "page__section")
    fields = ("page", "position", "full_name", "photo", "consent_given", "order")

    class Media:
        css = {"all": ("core/admin/admin.css",)}

    @admin.display(description="ПІБ", ordering="full_name")
    def full_name_display(self, obj: Person):
        if obj.full_name:
            return obj.full_name
        return format_html('<span style="color:#6b7280;font-style:italic;">— не заповнено —</span>')

    @admin.display(description="Згода на оприлюднення", ordering="consent_given")
    def consent_icon(self, obj: Person):
        if obj.consent_given:
            return format_html(
                '<span class="oberih-consent-yes" title="Згода є — показується на сайті">✔ Є згода</span>'
            )
        return format_html(
            '<span class="oberih-consent-no" title="Без згоди — приховано на сайті">✘ Немає згоди</span>'
        )


# --- 6. Документи (Document) ---
@admin.register(Document)
class DocumentAdmin(SimpleHistoryAdmin):
    list_display = (
        "title",
        "page",
        "file_size_display",
        "show_st30_notice",
        "order",
    )
    list_editable = ("order", "show_st30_notice")
    list_filter = ("show_st30_notice", "page__section", "page")
    search_fields = ("title", "page__title")
    list_select_related = ("page", "page__section")
    fields = ("page", "title", "file", "order", "show_st30_notice")

    @admin.display(description="Розмір PDF-файлу")
    def file_size_display(self, obj: Document):
        if not obj.has_file:
            return format_html(
                '<span style="color:#92400e;">Файл ще не завантажено</span>'
            )
        try:
            size_bytes = obj.file.size
        except OSError:
            return "Файл відсутній на диску"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} КБ"
        return f"{size_bytes / (1024 * 1024):.2f} МБ"


# --- 7. Головна сторінка (HomePage) ---
@admin.register(HomePage)
class HomePageAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            "1. Перший екран (Героїчний блок)",
            {
                "fields": (
                    "hero_eyebrow",
                    "hero_title",
                    "hero_title_em",
                    "hero_lead",
                    ("hero_fact_1", "hero_fact_2", "hero_fact_3"),
                ),
            },
        ),
        (
            "2. Блок «Про НРЦ «Оберіг»»",
            {
                "fields": (
                    "about_eyebrow",
                    "about_title",
                    "about_text",
                    "about_quote",
                    "about_quote_note",
                ),
            },
        ),
        (
            "3. Блок «Новини»",
            {
                "fields": ("news_eyebrow", "news_title"),
            },
        ),
        (
            "4. Блок «Документи»",
            {
                "fields": ("docs_eyebrow", "docs_title", "docs_note"),
            },
        ),
        (
            "5. Блок «Безпека та захист»",
            {
                "fields": ("safety_eyebrow", "safety_title", "safety_text"),
            },
        ),
        (
            "6. Блок «Запрошуємо»",
            {
                "fields": (
                    "welcome_eyebrow",
                    "welcome_title",
                    "welcome_text",
                    "welcome_image",
                ),
            },
        ),
        (
            "7. Блок «Наші спонсори»",
            {
                "fields": (
                    "sponsors_eyebrow",
                    "sponsors_title",
                    "sponsors_text",
                    "sponsors_note",
                ),
            },
        ),
    )


# --- 8. Налаштування сайту (SiteSettings) ---
@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    fieldsets = (
        (
            "Контакти та реквізити закладу (відображаються на всіх сторінках)",
            {
                "fields": (
                    "phone",
                    "email",
                    "address",
                    "director_name",
                    "map_url",
                    "footer_text",
                ),
            },
        ),
    )


# --- 9. Спонсори (Sponsor) ---
@admin.register(Sponsor)
class SponsorAdmin(SimpleHistoryAdmin):
    list_display = ("name", "logo_status", "url", "order")
    list_editable = ("order",)
    search_fields = ("name", "url")
    fields = ("name", "logo", "url", "order")

    @admin.display(description="Логотип")
    def logo_status(self, obj: Sponsor):
        if obj.has_logo:
            return format_html(
                '<span style="color:#15803d;font-weight:600;">✔ Завантажено</span>'
            )
        return format_html(
            '<span style="color:#92400e;">Ще не завантажено</span>'
        )
