<?php
/**
 * Допоміжні функції теми.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Адреса файлу з assets/ (копії спільних файлів макета).
 *
 * @param string $path Шлях усередині assets/, напр. 'img/logo-192.jpg'.
 */
function oberih_asset( $path ) {
	return get_template_directory_uri() . '/assets/' . ltrim( $path, '/' );
}

/**
 * Версія файлу для скидання кешу браузера: час останньої зміни.
 *
 * @param string $path Шлях усередині assets/.
 */
function oberih_asset_ver( $path ) {
	$file = get_template_directory() . '/assets/' . ltrim( $path, '/' );
	return file_exists( $file ) ? (string) filemtime( $file ) : wp_get_theme()->get( 'Version' );
}

/**
 * Контакти закладу. Поки що задані тут; згодом — у налаштуваннях теми.
 *
 * @param string $key phone | phone_href | email.
 */
function oberih_contact( $key ) {
	$contacts = apply_filters(
		'oberih_contacts',
		array(
			'phone'      => '(0342) 55-05-24',
			'phone_href' => 'tel:+380342550524',
			'email'      => 'nrts.oberih@osvita.if.ua',
		)
	);
	return isset( $contacts[ $key ] ) ? $contacts[ $key ] : '';
}

/**
 * Адреса сторінки за її шляхом, напр. 'ofitsiina-storinka/pravyla-pryiomu'.
 *
 * @param string $path Шлях сторінки (slug батьківської / slug сторінки).
 */
function oberih_page_url( $path ) {
	$path = trim( $path, '/' );
	$page = get_page_by_path( $path );
	return $page ? get_permalink( $page ) : home_url( '/' . $path . '/' );
}

/**
 * Кнопка перемикання світлої і темної теми (підпис змінює js/main.js).
 *
 * @param string $extra_class Додатковий клас кнопки.
 */
function oberih_theme_toggle( $extra_class = '' ) {
	$class = trim( 'theme-toggle ' . $extra_class );
	?>
	<button type="button" class="<?php echo esc_attr( $class ); ?>">
		<svg class="icon i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>
		<svg class="icon i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
		<span class="tt-label"><?php esc_html_e( 'Темна тема', 'oberih' ); ?></span>
	</button>
	<?php
}
