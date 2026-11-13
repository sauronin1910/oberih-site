<?php
/**
 * Форма «Поставити запитання»: перевірка, захист від спаму, лист на пошту закладу.
 *
 * Повідомлення в базі даних не зберігаються (персональні дані) — лише надсилаються листом.
 * Працює і без JavaScript (звичайне надсилання з поверненням на сторінку), і з ним (js/form.js, без перезавантаження).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const OBERIH_ASK_MIN_SECONDS = 3;    // швидше людина форму не заповнить — це бот.
const OBERIH_ASK_PER_HOUR    = 5;    // не більше запитань з однієї адреси за годину.
const OBERIH_ASK_MAX_MESSAGE = 3000; // символів у запитанні.

/**
 * Тексти відповідей форми за кодом.
 *
 * @param string $code ok | invalid | email | spam | limit | mail.
 */
function oberih_ask_message( $code ) {
	$email = oberih_contact( 'email' );
	$phone = oberih_contact( 'phone' );
	$texts = array(
		'ok'      => __( 'Дякуємо! Запитання надіслано. Відповімо на вказану електронну пошту.', 'oberih' ),
		'invalid' => __( 'Заповніть усі поля і поставте позначку згоди.', 'oberih' ),
		'email'   => __( 'Перевірте адресу електронної пошти.', 'oberih' ),
		'long'    => sprintf( /* translators: %d: кількість символів */ __( 'Запитання задовге: не більше %d символів.', 'oberih' ), OBERIH_ASK_MAX_MESSAGE ),
		'spam'    => __( 'Не вдалося надіслати запитання. Оновіть сторінку і спробуйте ще раз.', 'oberih' ),
		/* translators: %s: електронна пошта закладу */
		'limit'   => sprintf( __( 'Забагато запитань за короткий час. Спробуйте пізніше або напишіть на %s.', 'oberih' ), $email ),
		/* translators: 1: електронна пошта, 2: телефон */
		'mail'    => sprintf( __( 'Не вдалося надіслати запитання. Напишіть, будь ласка, на %1$s або зателефонуйте %2$s.', 'oberih' ), $email, $phone ),
	);
	return isset( $texts[ $code ] ) ? $texts[ $code ] : $texts['spam'];
}

/**
 * Приховані поля форми: дія, ключ захисту, час показу, пастка для ботів.
 */
function oberih_ask_form_fields() {
	echo '<input type="hidden" name="action" value="oberih_ask">';
	wp_nonce_field( 'oberih_ask', 'oberih_ask_nonce', false );
	echo '<input type="hidden" name="oberih_ts" value="' . esc_attr( time() ) . '">';
	// Пастка: люди цього поля не бачать і не заповнюють, боти — заповнюють.
	echo '<div class="hp" aria-hidden="true"><label for="f-website">' . esc_html__( 'Не заповнюйте це поле', 'oberih' )
		. '</label><input id="f-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>';
}

/**
 * Повідомлення після надсилання без JavaScript (адреса сторінки з ?ask=код).
 */
function oberih_ask_status() {
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- лише вибір тексту за кодом.
	$code = isset( $_GET['ask'] ) ? sanitize_key( wp_unslash( $_GET['ask'] ) ) : '';
	return '' === $code ? '' : oberih_ask_message( $code );
}

/**
 * IP-адреса відправника (для обмеження кількості запитань; ніде не зберігається довше години).
 */
function oberih_ask_ip() {
	$ip = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
	return filter_var( $ip, FILTER_VALIDATE_IP ) ? $ip : '0.0.0.0';
}

/**
 * Обробка надісланої форми.
 */
function oberih_handle_ask() {
	// phpcs:disable WordPress.Security.NonceVerification.Missing -- ключ перевіряється нижче.
	$post    = wp_unslash( $_POST );
	$as_json = ( isset( $_SERVER['HTTP_ACCEPT'] ) && false !== strpos( sanitize_text_field( wp_unslash( $_SERVER['HTTP_ACCEPT'] ) ), 'application/json' ) );
	// phpcs:enable

	$name    = isset( $post['name'] ) ? sanitize_text_field( $post['name'] ) : '';
	$email   = isset( $post['email'] ) ? sanitize_email( $post['email'] ) : '';
	$message = isset( $post['message'] ) ? sanitize_textarea_field( $post['message'] ) : '';
	$consent = ! empty( $post['consent'] );

	$code   = 'ok';
	$fields = array();
	if ( ! isset( $post['oberih_ask_nonce'] ) || ! wp_verify_nonce( $post['oberih_ask_nonce'], 'oberih_ask' )
		|| ! empty( $post['website'] )
		|| empty( $post['oberih_ts'] ) || ( time() - (int) $post['oberih_ts'] ) < OBERIH_ASK_MIN_SECONDS ) {
		$code = 'spam';
	} else {
		foreach ( array(
			'f-name'    => '' !== $name,
			'f-email'   => '' !== $email || ! empty( $post['email'] ),
			'f-msg'     => '' !== trim( $message ),
			'f-consent' => $consent,
		) as $id => $ok ) {
			if ( ! $ok ) {
				$fields[] = $id;
			}
		}
		if ( $fields ) {
			$code = 'invalid';
		} elseif ( ! is_email( $email ) ) {
			$code     = 'email';
			$fields[] = 'f-email';
		} elseif ( mb_strlen( $message ) > OBERIH_ASK_MAX_MESSAGE ) {
			$code     = 'long';
			$fields[] = 'f-msg';
		}
	}

	if ( 'ok' === $code ) {
		$key   = 'oberih_ask_' . md5( oberih_ask_ip() );
		$count = (int) get_transient( $key );
		if ( $count >= OBERIH_ASK_PER_HOUR ) {
			$code = 'limit';
		} else {
			set_transient( $key, $count + 1, HOUR_IN_SECONDS );
		}
	}

	if ( 'ok' === $code ) {
		$to      = apply_filters( 'oberih_ask_recipient', oberih_contact( 'email' ) );
		$subject = sprintf( /* translators: %s: ім'я */ __( 'Запитання з сайту НРЦ «Оберіг» від %s', 'oberih' ), mb_substr( $name, 0, 80 ) );
		$page    = wp_get_referer() ? esc_url_raw( wp_get_referer() ) : home_url( '/' );
		$body    = implode(
			"\n",
			array(
				__( 'Ім’я:', 'oberih' ) . ' ' . $name,
				__( 'Електронна пошта:', 'oberih' ) . ' ' . $email,
				__( 'Дата:', 'oberih' ) . ' ' . wp_date( 'd.m.Y H:i' ),
				__( 'Сторінка:', 'oberih' ) . ' ' . $page,
				'',
				__( 'Запитання:', 'oberih' ),
				$message,
				'',
				'—',
				__( 'Відповідь надсилайте на пошту автора (кнопка «Відповісти»). Лист надіслано з форми на сайті; копія на сайті не зберігається.', 'oberih' ),
			)
		);
		$headers = array( 'Reply-To: ' . str_replace( array( "\r", "\n", '<', '>', '"' ), '', $name ) . ' <' . $email . '>' );
		// Відправник у листі — назва сайту, а не «WordPress» (лише для цього листа).
		$from_name = static function () {
			return wp_specialchars_decode( get_bloginfo( 'name' ), ENT_QUOTES );
		};
		add_filter( 'wp_mail_from_name', $from_name );
		$sent = wp_mail( $to, $subject, $body, $headers );
		remove_filter( 'wp_mail_from_name', $from_name );
		if ( ! $sent ) {
			$code = 'mail';
		}
	}

	if ( $as_json ) {
		wp_send_json(
			array(
				'ok'      => 'ok' === $code,
				'message' => oberih_ask_message( $code ),
				'fields'  => $fields,
			),
			'ok' === $code ? 200 : 400
		);
	}

	$back = wp_get_referer();
	$back = $back ? $back : home_url( '/' );
	wp_safe_redirect( add_query_arg( 'ask', $code, remove_query_arg( 'ask', $back ) ) . '#ask-form-wp' );
	exit;
}
add_action( 'admin_post_nopriv_oberih_ask', 'oberih_handle_ask' );
add_action( 'admin_post_oberih_ask', 'oberih_handle_ask' );
