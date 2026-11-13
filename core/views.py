"""Представлення (views) для сторінок сайту КЗ «НРЦ «Оберіг»»."""
from django.core.paginator import Paginator
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render

from .models import NewsItem, Page, Section

NEWS_PER_PAGE = 6

PLACEHOLDER_DOT_SETS = (
    ("d1", "d2"),
    ("d3", "d4"),
    ("d5", "d6"),
    ("d7", "d8"),
    ("d9", "d10", "d11"),
    ("d12", "d13"),
)


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
