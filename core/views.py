"""Представлення (views) для сторінок сайту КЗ «НРЦ «Оберіг»»."""
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render

from .models import Page


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


def redirect_index_html(request):
    """Постійний 301-редірект зі старої адреси /index.html на /."""
    return HttpResponsePermanentRedirect("/")


def redirect_section_index_html(request, section_slug: str):
    """Постійний 301-редірект зі старої адреси /<section>/index.html на /<section>/."""
    return HttpResponsePermanentRedirect(f"/{section_slug}/")


def redirect_page_html(request, section_slug: str, page_slug: str):
    """Постійний 301-редірект зі старої адреси /<section>/<page>.html на /<section>/<page>/."""
    return HttpResponsePermanentRedirect(f"/{section_slug}/{page_slug}/")

