"""Конфігурація Gunicorn для сайту КЗ «НРЦ «Оберіг»» (VPS та PaaS)."""
import multiprocessing
import os

# Прив'язка сокета:
# 1. Якщо явно задано GUNICORN_BIND (наприклад, "unix:/run/oberih/gunicorn.sock" або "127.0.0.1:8000") — беремо його.
# 2. Якщо присутня змінна PORT (стандарт для PaaS-платформ) — слухаємо 0.0.0.0:$PORT.
# 3. За замовчуванням для VPS за Nginx — слухаємо лише локальний інтерфейс 127.0.0.1:8000.
_port = os.environ.get("PORT", "").strip()
bind = os.environ.get(
    "GUNICORN_BIND",
    f"0.0.0.0:{_port}" if _port else "127.0.0.1:8000",
)

# Помірна кількість робочих процесів (налаштовується через WEB_CONCURRENCY або GUNICORN_WORKERS):
# За замовчуванням 2–3 воркери (достатньо для шкільного сайту без зайвого споживання RAM).
_default_workers = min(max(multiprocessing.cpu_count(), 2), 3)
workers = int(
    os.environ.get(
        "GUNICORN_WORKERS",
        os.environ.get("WEB_CONCURRENCY", str(_default_workers)),
    )
)

# Таймаут обробки запиту (30 секунд) та перезапуск воркерів для запобігання витокам пам'яті
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "30"))
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Логування у стандартні потоки (їх збирає systemd/journald на VPS або лог-колектор на PaaS)
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "warning")
capture_output = True

