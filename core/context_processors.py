"""Контекстний процесор для глобальних даних шаблонів сайту НРЦ «Оберіг»."""
from django.db.models import Prefetch

from .models import Page, Section, SiteSettings


def site_context(request) -> dict:
    """Додає в усі шаблони налаштування сайту (SiteSettings) і структуру головного меню."""
    if not hasattr(request, "_cached_site_context"):
        site_settings = SiteSettings.objects.first() or SiteSettings()
        published_pages_prefetch = Prefetch(
            "pages",
            queryset=Page.objects.filter(is_published=True).order_by("order", "id"),
            to_attr="published_pages",
        )
        menu_sections = list(
            Section.objects.filter(show_in_menu=True)
            .order_by("order", "id")
            .prefetch_related(published_pages_prefetch)
        )
        request._cached_site_context = {
            "site_settings": site_settings,
            "menu_sections": menu_sections,
        }
    return request._cached_site_context

