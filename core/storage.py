"""Власне сховище статичних файлів із вимкненим manifest_strict."""
from whitenoise.storage import CompressedManifestStaticFilesStorage


class NonStrictCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Сховище WhiteNoise, яке не падає з ValueError, якщо файл або маніфест ще не зібрано."""

    manifest_strict = False

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError:
            return self.clean_name(name)
