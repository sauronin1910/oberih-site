"""Представлення (views) для сторінок сайту КЗ «НРЦ «Оберіг»»."""
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static

from .models import HomePage, NewsItem, Page, Section, SiteSettings, Sponsor

NEWS_PER_PAGE = 6
HOME_NEWS_LIMIT = 6

PLACEHOLDER_DOT_SETS = (
    ("d1", "d2"),
    ("d3", "d4"),
    ("d5", "d6"),
    ("d7", "d8"),
    ("d9", "d10", "d11"),
    ("d12", "d13"),
)


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
