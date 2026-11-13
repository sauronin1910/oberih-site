# -*- coding: utf-8 -*-
"""Копіює спільні файли макета (css, js, fonts, img) у тему WordPress: wp-theme/oberih/assets/.

Запуск з кореня репозиторію (гілка wordpress), після кожного оновлення дизайну з main:
    python tools/sync_theme_assets.py          скопіювати
    python tools/sync_theme_assets.py --check  лише перевірити, чи копії збігаються

Файли в assets/ вручну не правити: джерело — css/, js/, fonts/, img/ у корені.
Власні стилі теми лежать окремо: wp-theme/oberih/assets/css/wp.css (скрипт їх не чіпає).
"""
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'wp-theme' / 'oberih' / 'assets'
DIRS = ['css', 'js', 'fonts', 'img']
KEEP = {Path('css/wp.css')}          # файли теми, яких немає в макеті
SKIP = set()                         # файли макета, які в тему не потрібні


def main():
    check = '--check' in sys.argv
    changed, extra = [], []
    wanted = set()
    for d in DIRS:
        for src in sorted((ROOT / d).rglob('*')):
            if not src.is_file():
                continue
            rel = src.relative_to(ROOT)
            if rel in SKIP:
                continue
            wanted.add(rel)
            dst = DEST / rel
            if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                changed.append(rel)
                if not check:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
    if DEST.exists():
        for dst in sorted(DEST.rglob('*')):
            rel = dst.relative_to(DEST)
            if dst.is_file() and rel not in wanted and rel not in KEEP:
                extra.append(rel)
                if not check:
                    dst.unlink()
    word = 'відрізняються' if check else 'оновлено'
    print(f'Файлів макета: {len(wanted)}; {word}: {len(changed)}; зайвих у темі: {len(extra)}')
    for rel in changed + extra:
        print('  ', rel.as_posix())
    if check and (changed or extra):
        sys.exit(1)


if __name__ == '__main__':
    main()
