<?php
/**
 * Контакти й форма запитання. Параметр $args['title'] — заголовок блоку.
 * Згенеровано tools/build_wp_front.py з index.html — вручну не правити.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

?>
      <div class="contact">
        <div class="contact-info">
          <h2 id="contacts-title"><?php echo esc_html( isset( $args['title'] ) ? $args['title'] : 'Контакти' ); ?></h2>
          <dl>
            <div><dt>Адреса</dt><dd>вул. Гната Хоткевича, 52-А, м. Івано-Франківськ, 76020</dd></div>
            <div><dt>Телефон</dt><dd><a class="tel" href="tel:+380342550524">(0342) 55-05-24</a></dd></div>
            <div><dt>Електронна пошта</dt><dd><a href="mailto:nrts.oberih@osvita.if.ua">nrts.oberih@osvita.if.ua</a></dd></div>
            <div><dt>Директор</dt><dd>Шестопалова Галина Любомирівна</dd></div>
          </dl>
          <div class="map">
            <a href="https://www.google.com/maps/search/?api=1&amp;query=%D0%B2%D1%83%D0%BB.+%D0%93%D0%BD%D0%B0%D1%82%D0%B0+%D0%A5%D0%BE%D1%82%D0%BA%D0%B5%D0%B2%D0%B8%D1%87%D0%B0+52%D0%90+%D0%86%D0%B2%D0%B0%D0%BD%D0%BE-%D0%A4%D1%80%D0%B0%D0%BD%D0%BA%D1%96%D0%B2%D1%81%D1%8C%D0%BA" target="_blank" rel="noopener">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>
              Відкрити на карті<span class="sr-only"> (відкриється в новій вкладці)</span>
            </a>
          </div>
        </div>
        <form class="form" id="ask-form-wp" method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" novalidate>
          <?php oberih_ask_form_fields(); ?>
          <h2>Поставити запитання</h2>
          <p class="hint">Відповімо на вказану електронну пошту.</p>
          <div class="field"><label for="f-name">Ваше ім'я</label><input id="f-name" name="name" type="text" autocomplete="name" required></div>
          <div class="field"><label for="f-email">Електронна пошта</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
          <div class="field"><label for="f-msg">Запитання</label><textarea id="f-msg" name="message" required></textarea></div>
          <label class="check"><input id="f-consent" name="consent" type="checkbox" value="1" required>Погоджуюся на обробку персональних даних для відповіді на запитання. Згоду можна відкликати будь-коли.</label>
          <div><button class="btn btn-primary" type="submit">Надіслати</button></div>
          <p class="form-status" id="form-status" role="status"><?php echo esc_html( oberih_ask_status() ); ?></p>
        </form>
      </div>
