"""Конфігурація основного застосунку сайту КЗ «НРЦ «Оберіг»»."""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Вміст сайту НРЦ «Оберіг»"

