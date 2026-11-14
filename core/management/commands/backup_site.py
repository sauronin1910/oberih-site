"""Management-команда для створення резервної копії бази даних PostgreSQL та папки media/."""
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DB_DUMP_PATTERN = re.compile(r"^oberih_db_\d{8}_\d{6}\.dump$")
MEDIA_ARCHIVE_PATTERN = re.compile(r"^oberih_media_\d{8}_\d{6}\.tar\.gz$")


def _is_subpath(child: Path, parent: Path) -> bool:
    """Повертає True, якщо шлях child збігається з parent або лежить всередині нього."""
    return child == parent or parent in child.parents


class Command(BaseCommand):
    help = (
        "Створює резервну копію бази даних PostgreSQL (pg_dump -Fc) та архів папки media/ "
        "із правами 600 і безпечною ротацією старих копій."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            type=str,
            default="",
            help="Каталог для збереження резервних копій (за замовчуванням: BACKUP_DIR із налаштувань).",
        )
        parser.add_argument(
            "--keep",
            type=int,
            default=0,
            help="Кількість останніх копій, які слід залишати під час ротації (за замовчуванням: BACKUP_KEEP_COUNT).",
        )

    def _validate_backup_dir(self, backup_dir: Path) -> None:
        media_root = Path(settings.MEDIA_ROOT).resolve()
        base_dir = Path(settings.BASE_DIR).resolve()

        if _is_subpath(backup_dir, media_root):
            raise CommandError(
                f"Помилка безпеки: каталог резервних копій ({backup_dir}) не може знаходитися "
                f"всередині або збігатися з MEDIA_ROOT ({media_root}). "
                "Вкажіть зовнішній каталог у змінній BACKUP_DIR."
            )

        if _is_subpath(backup_dir, base_dir):
            raise CommandError(
                f"Помилка безпеки: каталог резервних копій ({backup_dir}) не може знаходитися "
                f"всередині каталогу проєкту, який відстежується git ({base_dir}). "
                "Вкажіть каталог за межами проєкту (наприклад, ../oberih_backups або /var/backups/oberih)."
            )

    def _rotate_files(self, backup_dir: Path, pattern: re.Pattern, keep: int) -> int:
        if keep <= 0:
            return 0
        matched = sorted(
            (
                p
                for p in backup_dir.iterdir()
                if p.is_file() and pattern.match(p.name)
            ),
            key=lambda p: p.name,
            reverse=True,
        )
        removed = 0
        for old_file in matched[keep:]:
            old_file.unlink(missing_ok=True)
            removed += 1
        return removed

    def handle(self, *args, **options):
        raw_dir = options.get("dir") or getattr(
            settings,
            "BACKUP_DIR",
            Path(settings.BASE_DIR).parent / "oberih_backups",
        )
        backup_dir = Path(raw_dir).resolve()
        keep = int(
            options.get("keep")
            or getattr(settings, "BACKUP_KEEP_COUNT", 7)
        )

        # 1. Перевірка, що BACKUP_DIR поза MEDIA_ROOT і поза git-каталогом проєкту
        self._validate_backup_dir(backup_dir)

        # 2. Перевірка наявності pg_dump
        pg_dump_bin = shutil.which("pg_dump")
        if not pg_dump_bin:
            raise CommandError(
                "Утиліту pg_dump не знайдено в системі. Встановіть клієнтські утиліти PostgreSQL "
                "(пакет postgresql-client) або додайте шлях до pg_dump у змінну середовища PATH."
            )

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(backup_dir, 0o700)
        except OSError as exc:
            raise CommandError(
                f"Не вдалося створити або налаштувати каталог резервних копій {backup_dir}: {exc}"
            ) from exc

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_dump_path = backup_dir / f"oberih_db_{timestamp}.dump"
        media_archive_path = backup_dir / f"oberih_media_{timestamp}.tar.gz"

        # 3. Створення дампу PostgreSQL (пароль передається лише через змінну середовища PGPASSWORD)
        db_cfg = settings.DATABASES["default"]
        env = os.environ.copy()
        if db_cfg.get("PASSWORD"):
            env["PGPASSWORD"] = str(db_cfg["PASSWORD"])

        cmd = [
            pg_dump_bin,
            "-Fc",
            "-h",
            str(db_cfg.get("HOST") or "127.0.0.1"),
            "-p",
            str(db_cfg.get("PORT") or "5432"),
            "-U",
            str(db_cfg.get("USER") or "oberih_user"),
            "-d",
            str(db_cfg.get("NAME") or "oberih_db"),
            "-f",
            str(db_dump_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CommandError(
                "Утиліту pg_dump не знайдено в системі. Перевірте встановлення postgresql-client."
            ) from exc

        if result.returncode != 0:
            if db_dump_path.exists():
                db_dump_path.unlink(missing_ok=True)
            err_text = (result.stderr or result.stdout or "").strip()
            raise CommandError(
                f"Помилка створення резервної копії бази даних через pg_dump: {err_text}"
            )

        os.chmod(db_dump_path, 0o600)

        # 4. Архівація папки media/
        media_root = Path(settings.MEDIA_ROOT).resolve()
        try:
            with tarfile.open(media_archive_path, "w:gz") as tar:
                if media_root.exists():
                    tar.add(media_root, arcname="media")
            os.chmod(media_archive_path, 0o600)
        except OSError as exc:
            raise CommandError(
                f"Не вдалося створити архів папки media/ ({media_archive_path}): {exc}"
            ) from exc

        # 5. Ротація старих копій (видаляються ЛИШЕ файли за власним шаблоном імені)
        db_removed = self._rotate_files(backup_dir, DB_DUMP_PATTERN, keep)
        media_removed = self._rotate_files(
            backup_dir, MEDIA_ARCHIVE_PATTERN, keep
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Резервну копію успішно створено в {backup_dir}:\n"
                f"  - База даних: {db_dump_path.name} (права 600)\n"
                f"  - Медіафайли: {media_archive_path.name} (права 600)\n"
                f"  - Видалено застарілих копій (залишено останніх {keep}): БД — {db_removed}, медіа — {media_removed}"
            )
        )

