# -*- coding: utf-8 -*-
"""Переносить головну сторінку макета (index.html) у тему WordPress.

Створює:
  wp-theme/oberih/front-page.php                   — головна; стрічку новин бере з записів WordPress
  wp-theme/oberih/template-parts/news-examples.php — новини-приклади з макета (показуються, поки записів немає)
  wp-theme/oberih/template-parts/contact-block.php — контакти й форма запитання (для сторінки «Контакти»)

Запуск з кореня репозиторію (гілка wordpress), після оновлення index.html з main:
    python tools/build_wp_front.py

Обидва файли згенеровані: вручну не правити, зміни робити в index.html (у main) і запускати скрипт знову.
"""
import re
from pathlib import Path

from export_site_map import wp_path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / 'wp-theme' / 'oberih'
NOTE = 'Згенеровано tools/build_wp_front.py з index.html — вручну не правити.'
GUARD = "if ( ! defined( 'ABSPATH' ) ) {\n\texit;\n}\n\n"  # прямий виклик файлу шаблону — нічого не робити


def php_links(html, news_to_list=False):
    """Відносні посилання макета -> адреси WordPress; зображення -> файли теми."""
    def href(m):
        path = wp_path(m.group(1))
        if news_to_list and path.startswith('novyny/'):
            path = 'novyny'
        page, _, anchor = path.partition('#')
        url = "home_url( '/' )" if page == '' else f"oberih_page_url( '{page}' )"
        if anchor:
            url += f" . '#{anchor}'"
        return f'href="<?php echo esc_url( {url} ); ?>"'

    html = re.sub(r'href="((?:[a-z0-9-]+/)*[a-z0-9-]+\.html(?:#[a-z0-9-]+)?)"', href, html)
    html = re.sub(r'src="(img/[^"]+)"', lambda m: f'src="<?php echo esc_url( oberih_asset( \'{m.group(1)}\' ) ); ?>"', html)
    left = re.findall(r'(?:href|src)="(?!<\?php|#|https?:|mailto:|tel:)[^"]*"', html)
    assert not left, f'лишились відносні посилання: {left[:5]}'
    assert '<?' not in re.sub(r'<\?php .*? \?>', '', html), 'у макеті трапився «<?»'
    return html


def main():
    src = (ROOT / 'index.html').read_text(encoding='utf-8')
    main_html = src.split('<main id="main">', 1)[1].split('</main>', 1)[0]

    track = re.search(r'(<ul class="news" id="news-track" tabindex="0">\n)(.*?\n)(      </ul>)', main_html, re.S)
    assert track, 'не знайдено стрічку новин <ul id="news-track">'
    examples = track.group(2)
    main_html = main_html.replace(track.group(0), track.group(1) + '<?php oberih_front_news(); ?>\n' + track.group(3))

    contact = re.search(r'(      <div class="contact">.*?\n        </form>\n      </div>)', main_html, re.S)
    assert contact, 'не знайдено блок контактів <div class="contact">'
    main_html = main_html.replace(
        contact.group(1),
        "      <?php get_template_part( 'template-parts/contact-block', null, array( 'title' => 'Контакти' ) ); ?>")

    front = ('<?php\n/**\n * Головна сторінка. ' + NOTE + '\n *\n * @package oberih\n */\n\n' + GUARD + 'get_header();\n?>'
             + php_links(main_html) + '<?php\nget_footer();\n')
    (THEME / 'front-page.php').write_text(front, encoding='utf-8', newline='\n')

    parts = THEME / 'template-parts'
    parts.mkdir(exist_ok=True)
    ex = ('<?php\n/**\n * Новини-приклади з макета: показуються на головній, поки в WordPress немає записів.\n * '
          + NOTE + '\n *\n * @package oberih\n */\n\n' + GUARD + '?>\n' + php_links(examples, news_to_list=True))
    (parts / 'news-examples.php').write_text(ex, encoding='utf-8', newline='\n')
    block = contact.group(1).replace(
        '<h2 id="contacts-title">Контакти</h2>',
        "<h2 id=\"contacts-title\"><?php echo esc_html( isset( $args['title'] ) ? $args['title'] : 'Контакти' ); ?></h2>")
    assert 'isset( $args' in block, 'не знайдено заголовок контактів'
    # Форма надсилається на сервер (inc/forms.php); id інший, щоб нею керував js/form.js, а не js/main.js макета.
    for old, new in [
        ('<form class="form" id="ask-form" novalidate>',
         '<form class="form" id="ask-form-wp" method="post" '
         'action="<?php echo esc_url( admin_url( \'admin-post.php\' ) ); ?>" novalidate>\n'
         '          <?php oberih_ask_form_fields(); ?>'),
        ('<input id="f-consent" type="checkbox" required>', '<input id="f-consent" name="consent" type="checkbox" value="1" required>'),
        ('<p class="form-status" id="form-status" role="status"></p>',
         '<p class="form-status" id="form-status" role="status"><?php echo esc_html( oberih_ask_status() ); ?></p>'),
    ]:
        assert block.count(old) == 1, f'у формі не знайдено: {old}'
        block = block.replace(old, new)
    cb = ('<?php\n/**\n * Контакти й форма запитання. Параметр $args[\'title\'] — заголовок блоку.\n * '
          + NOTE + '\n *\n * @package oberih\n */\n\n' + GUARD + '?>\n' + php_links(block) + '\n')
    (parts / 'contact-block.php').write_text(cb, encoding='utf-8', newline='\n')
    print('front-page.php і template-parts (news-examples, contact-block) оновлено; новин-прикладів:',
          examples.count('<li class="news-card'))


if __name__ == '__main__':
    main()
