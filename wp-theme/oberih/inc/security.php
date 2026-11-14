<?php
/**
 * Захист сайту, який не потребує плагінів.
 *
 * — Логіни й імена користувачів не видно публічно: немає сторінок авторів (/author/…, ?author=1),
 *   списку користувачів у REST API для гостей, імені автора в RSS, oEmbed і карті сайту.
 * — Коментарі й пінгбеки вимкнено: на офіційному сайті закладу вони не потрібні (і це персональні дані).
 * — XML-RPC вимкнено (через нього підбирають паролі).
 * — Версія WordPress ніде не показується; повідомлення про помилку входу не підказує, що саме не так.
 * — Заголовки безпеки для браузера.
 *
 * Обмеження спроб входу, резервні копії, HTTPS — на етапі запуску (хостинг і плагін захисту).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ---------- Користувачі не видно публічно ---------- */

/**
 * Сторінки авторів і перебір ?author=N — «сторінку не знайдено».
 */
function oberih_no_author_pages() {
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- лише перевірка наявності параметра.
	if ( is_author() || ( isset( $_GET['author'] ) && ! is_admin() ) ) {
		global $wp_query;
		$wp_query->set_404();
		status_header( 404 );
		nocache_headers();
	}
}
add_action( 'template_redirect', 'oberih_no_author_pages', 1 );

// Посилання на сторінку автора ніде не виводимо.
add_filter( 'author_link', 'oberih_home_link', 99 );

/**
 * Адреса головної (замість сторінки автора).
 *
 * @return string
 */
function oberih_home_link() {
	return home_url( '/' );
}

/**
 * Список користувачів у REST API — лише для тих, хто увійшов в адмінку (редактор його використовує).
 *
 * @param array $endpoints Маршрути REST.
 * @return array
 */
function oberih_rest_hide_users( $endpoints ) {
	if ( ! is_user_logged_in() ) {
		foreach ( array_keys( $endpoints ) as $route ) {
			if ( 0 === strpos( $route, '/wp/v2/users' ) ) {
				unset( $endpoints[ $route ] );
			}
		}
	}
	return $endpoints;
}
add_filter( 'rest_endpoints', 'oberih_rest_hide_users' );

/**
 * Автор у RSS — назва закладу, а не ім'я користувача.
 *
 * @param string $name Ім'я автора.
 * @return string
 */
function oberih_feed_author( $name ) {
	return is_feed() ? wp_strip_all_tags( get_bloginfo( 'name' ) ) : $name;
}
add_filter( 'the_author', 'oberih_feed_author' );

/**
 * Автор в oEmbed (вбудовування посилання в інших сайтах) — назва закладу.
 *
 * @param array $data Дані oEmbed.
 * @return array
 */
function oberih_oembed_author( $data ) {
	$data['author_name'] = wp_strip_all_tags( get_bloginfo( 'name' ) );
	$data['author_url']  = home_url( '/' );
	return $data;
}
add_filter( 'oembed_response_data', 'oberih_oembed_author' );

/**
 * Карта сайту без користувачів.
 *
 * @param WP_Sitemaps_Provider $provider Розділ карти.
 * @param string               $name     Назва розділу.
 * @return WP_Sitemaps_Provider|false
 */
function oberih_sitemap_no_users( $provider, $name ) {
	return 'users' === $name ? false : $provider;
}
add_filter( 'wp_sitemaps_add_provider', 'oberih_sitemap_no_users', 10, 2 );

/**
 * Помилка входу без підказок (не видно, чи існує такий користувач).
 *
 * @return string
 */
function oberih_login_error() {
	return __( 'Неправильний логін або пароль.', 'oberih' );
}
add_filter( 'login_errors', 'oberih_login_error' );

/* ---------- Коментарі й пінгбеки вимкнено ---------- */

add_filter( 'comments_open', '__return_false', 20 );
add_filter( 'pings_open', '__return_false', 20 );
add_filter( 'comments_array', '__return_empty_array', 20 );
add_filter( 'feed_links_show_comments_feed', '__return_false' );

/**
 * Прибрати підтримку коментарів у записах і сторінках, пункт меню «Коментарі» й лічильник у верхній панелі.
 */
function oberih_disable_comments_support() {
	foreach ( array( 'post', 'page', 'attachment' ) as $type ) {
		remove_post_type_support( $type, 'comments' );
		remove_post_type_support( $type, 'trackbacks' );
	}
}
add_action( 'init', 'oberih_disable_comments_support', 100 );

/**
 * Пункт «Коментарі» в меню адмінки.
 */
function oberih_disable_comments_menu() {
	remove_menu_page( 'edit-comments.php' );
	remove_submenu_page( 'options-general.php', 'options-discussion.php' );
}
add_action( 'admin_menu', 'oberih_disable_comments_menu' );

/**
 * Значок коментарів у верхній панелі.
 *
 * @param WP_Admin_Bar $bar Панель.
 */
function oberih_disable_comments_bar( $bar ) {
	$bar->remove_node( 'comments' );
}
add_action( 'admin_bar_menu', 'oberih_disable_comments_bar', 999 );

/**
 * Пряме надсилання коментаря (wp-comments-post.php) — відмова.
 */
function oberih_block_comment_post() {
	wp_die( esc_html__( 'Коментарі на сайті вимкнено.', 'oberih' ), '', array( 'response' => 403 ) );
}
add_action( 'pre_comment_on_post', 'oberih_block_comment_post' );

/* ---------- XML-RPC і версія WordPress ---------- */

add_filter( 'xmlrpc_enabled', '__return_false' );
add_filter( 'xmlrpc_methods', '__return_empty_array' );
add_filter( 'the_generator', '__return_empty_string' );

/**
 * Без заголовка X-Pingback.
 *
 * @param array $headers Заголовки.
 * @return array
 */
function oberih_security_headers( $headers ) {
	unset( $headers['X-Pingback'] );
	$headers['X-Content-Type-Options'] = 'nosniff';
	$headers['X-Frame-Options']        = 'SAMEORIGIN';
	$headers['Referrer-Policy']        = 'strict-origin-when-cross-origin';
	$headers['Permissions-Policy']     = 'camera=(), microphone=(), geolocation=(), payment=(), usb=()';
	return $headers;
}
add_filter( 'wp_headers', 'oberih_security_headers' );

/**
 * Не показувати версію PHP у заголовках відповіді (якщо сервер дозволяє).
 */
function oberih_hide_powered_by() {
	if ( function_exists( 'header_remove' ) && ! headers_sent() ) {
		header_remove( 'X-Powered-By' );
	}
}
add_action( 'send_headers', 'oberih_hide_powered_by' );
