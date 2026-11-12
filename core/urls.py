"""Маршрути публічної частини сайту КЗ «НРЦ «Оберіг»»."""
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Постійні 301-редіректи зі старих статичних .html адрес
    path("index.html", views.redirect_index_html, name="redirect_index_html"),
    path(
        "<slug:section_slug>/index.html",
        views.redirect_section_index_html,
        name="redirect_section_index_html",
    ),
    path(
        "<slug:section_slug>/<slug:page_slug>.html",
        views.redirect_page_html,
        name="redirect_page_html",
    ),
    # Чисті URL внутрішніх сторінок
    path(
        "<slug:section_slug>/<slug:page_slug>/",
        views.page_detail,
        name="page_detail",
    ),
]

