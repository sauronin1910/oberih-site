# Сайт КЗ «НРЦ «Оберіг»» (Івано-Франківськ)

Офіційний вебсайт комунального закладу «Навчально-реабілітаційний центр „Оберіг“» Івано-Франківської міської ради.

- **Адреса:** вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020
- **Телефон:** (0342) 55-05-24
- **E-mail:** nrts.oberih@osvita.if.ua
- **Стек:** Python 3.12+, Django 5.2 LTS, PostgreSQL, WhiteNoise, Gunicorn (без Docker)

---

## Структура проєкту

```text
oberih-site-main/
├── config/                 # Конфігурація Django-проєкту
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py         # Налаштування з підтримкою .env та продакшн-безпекою
│   ├── urls.py             # Маршрути проєкту (адмінка на /admin-panel/)
│   └── wsgi.py
├── core/                   # Основний застосунок сайту (усі моделі даних)
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── apps.py
│   └── models.py           # 10 моделей даних з історією змін (django-simple-history)
├── static/                 # Статичні файли фронтенду (скопійовані без змін)
│   ├── css/
│   ├── fonts/
│   ├── img/
│   └── js/
├── tools/                  # Генератор статичних сторінок і карта сайту за ТЗ
│   ├── build_pages.py
│   └── site_map.py
├── .env.example            # Шаблон змінних середовища
├── .gitignore
├── manage.py
├── requirements.txt        # Зафіксовані версії залежностей (==)
└── README.md
```

---

## Як запустити локально

### 1. Підготовка бази даних PostgreSQL

Створіть базу даних і користувача в PostgreSQL (наприклад, через `psql` або pgAdmin):

```sql
CREATE DATABASE oberih_db ENCODING 'UTF8';
CREATE USER oberih_user WITH PASSWORD 'ваш_надійний_пароль';
GRANT ALL PRIVILEGES ON DATABASE oberih_db TO oberih_user;
ALTER DATABASE oberih_db OWNER TO oberih_user;
```

### 2. Створення віртуального середовища та встановлення залежностей

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Налаштування змінних середовища (`.env`)

Скопіюйте `.env.example` у `.env` та заповніть параметри підключення до PostgreSQL і секретний ключ:

```powershell
Copy-Item .env.example .env
```

Для локальної розробки (без HTTPS) у `.env` встановіть:
```ini
DEBUG=True
SECRET_KEY=згенерований-секретний-ключ
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=oberih_db
DB_USER=oberih_user
DB_PASSWORD=ваш_надійний_пароль
DB_HOST=127.0.0.1
DB_PORT=5432
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
```

Згенерувати надійний `SECRET_KEY` можна командою:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Застосування міграцій, таблиця кешу та створення адміністратора

```powershell
python manage.py migrate
python manage.py createcachetable
python manage.py createsuperuser
```

### 5. Запуск сервера розробки

```powershell
python manage.py runserver
```

- Сайт буде доступний за адресою: `http://127.0.0.1:8000/`
- Адмін-панель: `http://127.0.0.1:8000/admin-panel/`

---

## Розгортання на сервері (Production)

1. **Створення таблиці кешу в PostgreSQL:**
   Для роботи спільного ліміту форми звернень між усіма робочими процесами Gunicorn обов'язково виконайте:
   ```bash
   python manage.py migrate
   python manage.py createcachetable
   ```
   *(Якщо таблиця кешу раптом не створена або недоступна, форма не падає — помилка лише логується, а звернення зберігається в базу даних).*

2. **Робота за Nginx (`TRUST_X_FORWARDED_FOR`):**
   На сервері за reverse-proxy (Nginx) у файлі `.env` обов'язково увімкніть:
   ```ini
   TRUST_X_FORWARDED_FOR=True
   ```
   та переконайтеся, що в конфігурації Nginx передається `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`.
   При `TRUST_X_FORWARDED_FOR=True` Django бере **останній** запис із `X-Forwarded-For` (який додає безпосередньо Nginx, тому клієнт не може його підробити). Якщо залишити `False` за проксі-сервером, усі відвідувачі матимуть `REMOTE_ADDR=127.0.0.1` і ліміт форми заблокує всіх одночасно.

---

## Основні команди

- `python manage.py check` — перевірка конфігурації та моделей на помилки.
- `python manage.py makemigrations` — створення нових міграцій при зміні моделей.
- `python manage.py migrate` — застосування міграцій до бази даних PostgreSQL.
- `python manage.py createcachetable` — створення таблиці кешу в PostgreSQL для спільного ліміту форми звернень.
- `python manage.py collectstatic` — збирання статики у `STATIC_ROOT` для продакшену.
- `python manage.py check --deploy` — перевірка готовності налаштувань безпеки до продакшену (при `DEBUG=False`).
