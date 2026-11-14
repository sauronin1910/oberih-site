"""Проміжне ПЗ (middleware) для заголовків безпеки (CSP) та захисту входу в адмінку."""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import render

from .views import get_client_ip

logger = logging.getLogger(__name__)

ADMIN_LOGIN_PATH = "/admin-panel/login/"
ADMIN_LOGIN_RATE_LIMIT_MESSAGE = (
    "Забагато невдалих спроб входу. Зачекайте 15 хвилин і спробуйте знову."
)

DEFAULT_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "form-action 'self'"
)


def _admin_login_keys(request) -> tuple[str, str]:
    """Формує SHA-256 ключі в кеші: загальний на IP-адресу та на пару (IP + логін)."""
    client_ip = get_client_ip(request)
    username = (request.POST.get("username") or "").strip().lower()
    ip_raw = f"admin_ip:{client_ip}:{settings.SECRET_KEY}".encode("utf-8")
    pair_raw = (
        f"admin_pair:{client_ip}:{username}:{settings.SECRET_KEY}".encode(
            "utf-8"
        )
    )
    ip_key = f"admin_rl_ip:{hashlib.sha256(ip_raw).hexdigest()}"
    pair_key = f"admin_rl_pair:{hashlib.sha256(pair_raw).hexdigest()}"
    return ip_key, pair_key


def _is_admin_login_limited(ip_key: str, pair_key: str) -> bool:
    """Перевіряє ліміт входу в адмінку за IP (20/15хв) та за парою IP+логін (5/15хв). Відмова відкрито."""
    pair_limit = getattr(settings, "ADMIN_LOGIN_RATE_LIMIT_COUNT", 5)
    ip_limit = getattr(settings, "ADMIN_LOGIN_IP_RATE_LIMIT_COUNT", 20)
    try:
        with transaction.atomic():
            if ip_limit > 0:
                ip_count = int(cache.get(ip_key, 0) or 0)
                if ip_count >= ip_limit:
                    return True
            if pair_limit > 0:
                pair_count = int(cache.get(pair_key, 0) or 0)
                if pair_count >= pair_limit:
                    return True
        return False
    except Exception:
        logger.exception(
            "Не вдалося перевірити ліміт входу в адмінку в кеші (відмова відкрито)"
        )
        return False


def _record_admin_login_failure(ip_key: str, pair_key: str) -> None:
    """Збільшує обидва лічильники невдалих спроб входу в адмінку. Відмова відкрито."""
    period = getattr(settings, "ADMIN_LOGIN_RATE_LIMIT_PERIOD", 900)
    try:
        with transaction.atomic():
            ip_count = int(cache.get(ip_key, 0) or 0)
            cache.set(ip_key, ip_count + 1, timeout=period)
            pair_count = int(cache.get(pair_key, 0) or 0)
            cache.set(pair_key, pair_count + 1, timeout=period)
    except Exception:
        logger.exception(
            "Не вдалося оновити лічильник невдалих спроб входу в адмінку (відмова відкрито)"
        )


def _clear_admin_login_pair(pair_key: str) -> None:
    """Скидає лічильник пари (IP + логін) після успішного входу адміністратора."""
    try:
        with transaction.atomic():
            cache.delete(pair_key)
    except Exception:
        logger.exception(
            "Не вдалося очистити лічильник входу в адмінку після успішної авторизації"
        )


class AdminLoginRateLimitMiddleware:
    """Обмежує кількість невдалих спроб входу на /admin-panel/login/ через DatabaseCache."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == ADMIN_LOGIN_PATH and request.method == "POST":
            ip_key, pair_key = _admin_login_keys(request)
            if _is_admin_login_limited(ip_key, pair_key):
                logger.warning(
                    "Заблоковано спробу входу в адмінку (перевищено ліміт, ключ %s)",
                    pair_key[:22],
                )
                context = {
                    "error_message": ADMIN_LOGIN_RATE_LIMIT_MESSAGE,
                    "current_section_slug": None,
                    "current_page_slug": None,
                }
                return render(request, "429.html", context, status=429)

            response = self.get_response(request)

            user = getattr(request, "user", None)
            if (
                user is not None
                and user.is_authenticated
                and response.status_code in (301, 302, 303)
            ):
                _clear_admin_login_pair(pair_key)
            elif response.status_code == 200:
                _record_admin_login_failure(ip_key, pair_key)
                logger.warning(
                    "Невдала спроба входу в адмінку (ключ %s)",
                    pair_key[:22],
                )
            return response

        return self.get_response(request)


class ContentSecurityPolicyMiddleware:
    """Додає заголовок Content-Security-Policy до всіх публічних сторінок (крім /admin-panel/)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, "CSP_ENABLED", True):
            return response
        if request.path.startswith("/admin-panel/"):
            return response
        if "Content-Security-Policy" not in response:
            response["Content-Security-Policy"] = getattr(
                settings, "CSP_POLICY", DEFAULT_CSP_POLICY
            )
        return response

