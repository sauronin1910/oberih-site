#!/usr/bin/env python
"""Командна утиліта Django для керування проєктом НРЦ «Оберіг»."""
import os
import sys


def main():
    """Запуск адміністративних команд Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не вдалося імпортувати Django. Перевірте, чи активовано віртуальне "
            "середовище та чи встановлено залежності з requirements.txt."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

