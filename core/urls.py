"""Маршрути публічної частини сайту КЗ «НРЦ «Оберіг»»."""
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # 1. Постійні 301-редіректи зі старих статичних .html адрес (спочатку конкретні маршрути)
    path("index.html", views.redirect_index_html, name="redirect_index_html"),
    path(
        "novyny/index.html",
        views.redirect_news_list_html,
        name="redirect_news_list_html",
    ),
    path(
        "novyny/<slug:slug>.html",
        views.redirect_news_detail_html,
        name="redirect_news_detail_html",
    ),
    # 2. Новини (розташовані ПЕРЕД загальним <slug:section_slug>/, щоб не виникало конфліктів)
    path("novyny/", views.news_list, name="news_list"),
    path("novyny/<slug:slug>/", views.news_detail, name="news_detail"),
    # УВАГА: Маршрути сторінки контактів (kontakty/index.html та kontakty/)
    # додаються на наступному кроці САМЕ ТУТ — ПЕРЕД загальними маршрутами <slug:section_slug>/.
    # 3. Редіректи та чисті URL розділів і внутрішніх сторінок
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
    path(
        "<slug:section_slug>/",
        views.section_detail,
        name="section_detail",
    ),
    path(
        "<slug:section_slug>/<slug:page_slug>/",
        views.page_detail,
        name="page_detail",
    ),
]
