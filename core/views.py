"""Представлення (views) для сторінок сайту КЗ «НРЦ «Оберіг»»."""
import hashlib
import json
import logging
import unicodedata

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import transaction
from django.http import (
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import (
    ContactMessage,
    HomePage,
    NewsItem,
    Page,
    Section,
    SiteSettings,
    Sponsor,
)

logger = logging.getLogger(__name__)

NEWS_PER_PAGE = 6
HOME_NEWS_LIMIT = 6

CONTACT_SUCCESS_MESSAGE = (
    "Дякуємо! Ваше запитання надіслано. Відповімо на вказану електронну пошту."
)
CONTACT_RATE_LIMIT_MESSAGE = (
    "Ви надіслали забагато звернень поспіль. Будь ласка, зачекайте кілька хвилин і спробуйте знову."
)

PLACEHOLDER_DOT_SETS = (
    ("d1", "d2"),
    ("d3", "d4"),
    ("d5", "d6"),
    ("d7", "d8"),
    ("d9", "d10", "d11"),
    ("d12", "d13"),
)


# УВАГА щодо кешування: головна сторінка (/) та сторінка контактів (/kontakty/)
# містять форму #ask-form із захисним токеном {% csrf_token %}, тому їх НЕ МОЖНА
# віддавати з публічного кешу (@never_cache гарантує Cache-Control: no-cache, no-store, must-revalidate).
@never_cache
def home(request):
    """Відображає головну сторінку сайту (/)."""
    home_page = HomePage.objects.first() or HomePage()
    site_settings = SiteSettings.objects.first() or SiteSettings()
    news_items = list(
        NewsItem.objects.filter(is_published=True).order_by(
            "-published_date", "-id"
        )[:HOME_NEWS_LIMIT]
    )
    for idx, item in enumerate(news_items):
        item.placeholder_dots = PLACEHOLDER_DOT_SETS[
            idx % len(PLACEHOLDER_DOT_SETS)
        ]

    sponsors = list(Sponsor.objects.order_by("order", "id"))

    site_url = getattr(settings, "SITE_URL", "")
    base_url = (
        site_url if site_url else request.build_absolute_uri("/").rstrip("/")
    )
    logo_path = static("img/logo.jpg")
    logo_url = (
        f"{base_url}{logo_path}" if logo_path.startswith("/") else logo_path
    )

    address_data = {
        "@type": "PostalAddress",
        "streetAddress": site_settings.street_address,
        "addressLocality": "Івано-Франківськ",
        "addressRegion": "Івано-Франківська область",
    }
    if site_settings.postal_code:
        address_data["postalCode"] = site_settings.postal_code
    address_data["addressCountry"] = "UA"

    schema_data = {
        "@context": "https://schema.org",
        "@type": "EducationalOrganization",
        "name": (
            "Комунальний заклад «Навчально-реабілітаційний центр „Оберіг“» "
            "Івано-Франківської міської ради"
        ),
        "alternateName": "НРЦ «Оберіг»",
        "url": f"{base_url}/",
        "address": address_data,
        "telephone": site_settings.phone_tel,
        "email": site_settings.email,
        "logo": logo_url,
    }
    json_ld = json.dumps(schema_data, ensure_ascii=False).replace("</", r"<\/")

    context = {
        "home_page": home_page,
        "news_items": news_items,
        "sponsors": sponsors,
        "json_ld": json_ld,
        "current_section_slug": None,
        "current_page_slug": None,
    }
    return render(request, "home.html", context)


def section_detail(request, section_slug: str):
    """Відображає сторінку розділу зі списком його опублікованих підсторінок."""
    section = get_object_or_404(Section, slug=section_slug)
    pages = list(section.pages.filter(is_published=True).order_by("order", "id"))
    context = {
        "section": section,
        "pages": pages,
        "current_section_slug": section.slug,
        "current_page_slug": None,
    }
    return render(request, "section.html", context)


def page_detail(request, section_slug: str, page_slug: str):
    """Відображає опубліковану внутрішню сторінку розділу."""
    page = get_object_or_404(
        Page.objects.select_related("section"),
        section__slug=section_slug,
        slug=page_slug,
        is_published=True,
    )
    section = page.section
    blocks = list(page.blocks.order_by("order", "id"))
    documents = list(page.documents.order_by("order", "id"))
    show_st30_notice = any(doc.show_st30_notice for doc in documents)
    people = list(page.people.with_consent().order_by("order", "id"))
    section_pages = list(
        section.pages.filter(is_published=True).order_by("order", "id")
    )

    context = {
        "page": page,
        "section": section,
        "blocks": blocks,
        "documents": documents,
        "show_st30_notice": show_st30_notice,
        "people": people,
        "section_pages": section_pages,
        "current_section_slug": section.slug,
        "current_page_slug": page.slug,
    }
    return render(request, "page.html", context)


def news_list(request):
    """Відображає список опублікованих новин із пагінацією по 6 карток на сторінку."""
    queryset = NewsItem.objects.filter(is_published=True).order_by(
        "-published_date", "-id"
    )
    paginator = Paginator(queryset, NEWS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))
    news_items = list(page_obj.object_list)
    for idx, item in enumerate(news_items):
        item.placeholder_dots = PLACEHOLDER_DOT_SETS[
            idx % len(PLACEHOLDER_DOT_SETS)
        ]

    context = {
        "news_items": news_items,
        "page_obj": page_obj,
        "current_section_slug": "novyny",
        "current_page_slug": None,
    }
    return render(request, "news_list.html", context)


def news_detail(request, slug: str):
    """Відображає сторінку окремої опублікованої новини."""
    news = get_object_or_404(NewsItem, slug=slug, is_published=True)
    context = {
        "news": news,
        "current_section_slug": "novyny",
        "current_page_slug": news.slug,
    }
    return render(request, "news_detail.html", context)


def _is_ajax(request) -> bool:
    """Повертає True, якщо запит надіслано через fetch / XMLHttpRequest і очікує JSON."""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept


def _get_client_ip(request) -> str:
    """Безпечно визначає адресу клієнта (бере останній запис X-Forwarded-For лише коли TRUST_X_FORWARDED_FOR=True)."""
    if getattr(settings, "TRUST_X_FORWARDED_FOR", False):
        xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if xff:
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[-1]
    return (request.META.get("REMOTE_ADDR") or "").strip() or "unknown"


def _rate_limit_key(request) -> str:
    """Формує незворотний SHA-256 ключ для ліміту запитів без збереження сирого IP."""
    client_ip = _get_client_ip(request)
    raw = f"{client_ip}:{settings.SECRET_KEY}".encode("utf-8")
    return f"contact_rl:{hashlib.sha256(raw).hexdigest()}"


def _is_rate_limited(request) -> bool:
    """Перевіряє, чи перевищено ліміт звернень. При недоступності кешу відмовляє відкрито (пропускає)."""
    limit = getattr(settings, "CONTACT_RATE_LIMIT_COUNT", 3)
    if limit <= 0:
        return False
    key = _rate_limit_key(request)
    try:
        # transaction.atomic() створює SAVEPOINT у PostgreSQL, щоб помилка SQL
        # (наприклад, якщо таблицю кешу ще не створено) не переривала поточну транзакцію БД.
        with transaction.atomic():
            count = cache.get(key, 0)
        return int(count or 0) >= limit
    except Exception:
        logger.exception(
            "Не вдалося перевірити ліміт звернень у кеші (відмова відкрито)"
        )
        return False


def _increment_rate_limit(request) -> None:
    """Збільшує лічильник звернень у кеші. При збої кешу лише логує помилку."""
    period = getattr(settings, "CONTACT_RATE_LIMIT_PERIOD", 600)
    key = _rate_limit_key(request)
    try:
        with transaction.atomic():
            count = int(cache.get(key, 0) or 0)
            cache.set(key, count + 1, timeout=period)
    except Exception:
        logger.exception(
            "Не вдалося оновити лічильник звернень у кеші (відмова відкрито)"
        )


def _strip_control_chars(value: str, *, allow_newlines: bool = False) -> str:
    """Прибирає невидимі керуючі символи Unicode (категорія C), зберігаючи переведення рядків за потреби."""
    cleaned = []
    for ch in value:
        if allow_newlines and ch in ("\n", "\t"):
            cleaned.append(ch)
        elif unicodedata.category(ch).startswith("C"):
            continue
        else:
            cleaned.append(ch)
    return "".join(cleaned)


def _validate_contact_submission(post_data):
    """Перевіряє поля форми звернення та повертає (cleaned_dict, error_message, error_field)."""
    raw_name = post_data.get("name", "")
    raw_email = post_data.get("email", "")
    raw_message = post_data.get("message", "")
    raw_consent = post_data.get("consent", "")

    # Захист від Header Injection у заголовках листа (Subject / Reply-To)
    if any(sep in raw_name for sep in ("\r", "\n", "\x00")):
        return None, "Вкажіть коректне ім’я без символів переведення рядка.", "name"
    if any(sep in raw_email for sep in ("\r", "\n", "\x00")):
        return (
            None,
            "Вкажіть коректну адресу електронної пошти.",
            "email",
        )

    name = _strip_control_chars(raw_name, allow_newlines=False).strip()
    email = _strip_control_chars(raw_email, allow_newlines=False).strip()
    normalized_msg = raw_message.replace("\r\n", "\n").replace("\r", "\n")
    message = _strip_control_chars(normalized_msg, allow_newlines=True).strip()
    consent = str(raw_consent).strip().lower() in ("on", "true", "1", "yes")

    form_values = {
        "name": name,
        "email": email,
        "message": message,
        "consent": consent,
    }

    if not name:
        return form_values, "Вкажіть ваше ім’я.", "name"
    if len(name) > 150:
        return (
            form_values,
            "Ім’я занадто довге (максимум 150 символів).",
            "name",
        )

    if not email:
        return form_values, "Вкажіть електронну пошту.", "email"
    if len(email) > 254:
        return (
            form_values,
            "Вкажіть коректну адресу електронної пошти.",
            "email",
        )
    try:
        validate_email(email)
    except ValidationError:
        return (
            form_values,
            "Вкажіть коректну адресу електронної пошти.",
            "email",
        )

    if not message:
        return form_values, "Напишіть текст запитання.", "message"
    if len(message) > 2000:
        return (
            form_values,
            "Текст запитання занадто довгий (максимум 2000 символів).",
            "message",
        )

    if not consent:
        return (
            form_values,
            "Поставте позначку згоди на обробку персональних даних.",
            "consent",
        )

    return form_values, None, None


def _send_contact_notification(contact_msg: ContactMessage) -> None:
    """Надсилає сповіщення про нове звернення на пошту закладу. Помилки лише логуються."""
    site_settings = SiteSettings.objects.first() or SiteSettings()
    recipient = (
        getattr(settings, "CONTACT_NOTIFY_EMAIL", "").strip()
        or (site_settings.email or "").strip()
        or getattr(settings, "DEFAULT_FROM_EMAIL", "").strip()
    )
    if not recipient:
        return

    try:
        local_dt = timezone.localtime(contact_msg.created_at).strftime(
            "%d.%m.%Y %H:%M"
        )
        body = (
            "Надійшло нове запитання через форму на сайті НРЦ «Оберіг».\n\n"
            f"Ім'я відправника: {contact_msg.name}\n"
            f"Електронна пошта: {contact_msg.email}\n"
            f"Дата і час: {local_dt}\n\n"
            f"Текст запитання:\n{contact_msg.message}\n"
        )
        email_message = EmailMessage(
            subject=f"Нове запитання з сайту НРЦ «Оберіг» від {contact_msg.name}",
            body=body,
            from_email=getattr(
                settings, "DEFAULT_FROM_EMAIL", "noreply@oberih.if.ua"
            ),
            to=[recipient],
            reply_to=[contact_msg.email],
        )
        email_message.send(fail_silently=False)
    except Exception:
        logger.exception(
            "Не вдалося надіслати email-сповіщення про звернення #%s",
            contact_msg.pk,
        )


@never_cache
def contacts(request):
    """Відображає сторінку контактів (/kontakty/) та обробляє відправлення форми #ask-form."""
    is_ajax = _is_ajax(request)

    if request.method == "POST":
        # 1. Перевірка honeypot-поля: якщо заповнене — тихо ігноруємо без запису в БД
        honeypot = request.POST.get("website", "").strip()
        if honeypot:
            if is_ajax:
                return JsonResponse(
                    {"ok": True, "message": CONTACT_SUCCESS_MESSAGE}
                )
            return HttpResponseRedirect("/kontakty/?sent=1#ask-form", status=303)

        # 2. Перевірка ліміту запитів (rate limit)
        if _is_rate_limited(request):
            if is_ajax:
                return JsonResponse(
                    {"ok": False, "message": CONTACT_RATE_LIMIT_MESSAGE},
                    status=429,
                )
            context = {
                "current_section_slug": "kontakty",
                "current_page_slug": None,
                "form_status_message": CONTACT_RATE_LIMIT_MESSAGE,
                "error_field": None,
                "form_values": {},
            }
            return render(request, "contacts.html", context, status=429)

        # 3. Серверна валідація полів
        form_values, error_msg, error_field = _validate_contact_submission(
            request.POST
        )
        if error_msg:
            if is_ajax:
                return JsonResponse(
                    {
                        "ok": False,
                        "message": error_msg,
                        "field": error_field,
                    },
                    status=400,
                )
            context = {
                "current_section_slug": "kontakty",
                "current_page_slug": None,
                "form_status_message": error_msg,
                "error_field": error_field,
                "form_values": form_values or {},
            }
            return render(request, "contacts.html", context, status=400)

        # 4. Збільшуємо лічильник ліміту та СПОЧАТКУ зберігаємо звернення в базу даних
        _increment_rate_limit(request)
        contact_msg = ContactMessage.objects.create(
            name=form_values["name"],
            email=form_values["email"],
            message=form_values["message"],
            consent_given=True,
        )

        # 5. Надсилаємо сповіщення на пошту (збій пошти не скасовує запис і не повертає помилку)
        _send_contact_notification(contact_msg)

        if is_ajax:
            return JsonResponse(
                {"ok": True, "message": CONTACT_SUCCESS_MESSAGE}
            )
        return HttpResponseRedirect("/kontakty/?sent=1#ask-form", status=303)

    # GET-запит: якщо передано ?sent=1, виводимо фіксований рядок з коду (ніколи не вміст параметра)
    form_status_message = (
        CONTACT_SUCCESS_MESSAGE if request.GET.get("sent") == "1" else ""
    )
    context = {
        "current_section_slug": "kontakty",
        "current_page_slug": None,
        "form_status_message": form_status_message,
        "error_field": None,
        "form_values": {},
    }
    return render(request, "contacts.html", context)


def redirect_contacts_html(request):
    """Постійний 301-редірект зі старої адреси /kontakty/index.html на /kontakty/."""
    return HttpResponsePermanentRedirect("/kontakty/")


def redirect_index_html(request):
    """Постійний 301-редірект зі старої адреси /index.html на /."""
    return HttpResponsePermanentRedirect("/")


def redirect_news_list_html(request):
    """Постійний 301-редірект зі старої адреси /novyny/index.html на /novyny/."""
    return HttpResponsePermanentRedirect("/novyny/")


def redirect_news_detail_html(request, slug: str):
    """Постійний 301-редірект зі старої адреси /novyny/<slug>.html на /novyny/<slug>/."""
    return HttpResponsePermanentRedirect(f"/novyny/{slug}/")


def redirect_section_index_html(request, section_slug: str):
    """Постійний 301-редірект зі старої адреси /<section>/index.html на /<section>/."""
    return HttpResponsePermanentRedirect(f"/{section_slug}/")


def redirect_page_html(request, section_slug: str, page_slug: str):
    """Постійний 301-редірект зі старої адреси /<section>/<page>.html на /<section>/<page>/."""
    return HttpResponsePermanentRedirect(f"/{section_slug}/{page_slug}/")
