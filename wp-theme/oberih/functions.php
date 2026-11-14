<?php
/**
 * Тема «Оберіг»: базові налаштування.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

require get_template_directory() . '/inc/helpers.php';
require get_template_directory() . '/inc/menu.php';
require get_template_directory() . '/inc/navigation.php';
require get_template_directory() . '/inc/content.php';
require get_template_directory() . '/inc/front.php';
require get_template_directory() . '/inc/forms.php';
require get_template_directory() . '/inc/translit.php';

/**
 * Можливості теми й області меню.
 */
function oberih_setup() {
	load_theme_textdomain( 'oberih', get_template_directory() . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script', 'navigation-widgets' ) );

	// Короткий опис сторінки (поле «Уривок») показуємо під її заголовком.
	add_post_type_support( 'page', 'excerpt' );

	register_nav_menus(
		array(
			'primary'  => __( 'Головне меню', 'oberih' ),
			'footer-1' => __( 'Підвал: колонка 1', 'oberih' ),
			'footer-2' => __( 'Підвал: колонка 2', 'oberih' ),
			'footer-3' => __( 'Підвал: колонка 3', 'oberih' ),
		)
	);
}
add_action( 'after_setup_theme', 'oberih_setup' );

/**
 * Стилі та скрипти макета.
 */
function oberih_assets() {
	// prefs.js — у <head>, без defer: вмикає тему й розмір тексту ще до показу сторінки.
	wp_enqueue_script( 'oberih-prefs', oberih_asset( 'js/prefs.js' ), array(), oberih_asset_ver( 'js/prefs.js' ), false );

	wp_enqueue_style( 'oberih-fonts', oberih_asset( 'css/fonts.css' ), array(), oberih_asset_ver( 'css/fonts.css' ) );
	wp_enqueue_style( 'oberih-style', oberih_asset( 'css/style.css' ), array( 'oberih-fonts' ), oberih_asset_ver( 'css/style.css' ) );
	wp_enqueue_style( 'oberih-wp', oberih_asset( 'css/wp.css' ), array( 'oberih-style' ), oberih_asset_ver( 'css/wp.css' ) );

	wp_enqueue_script(
		'oberih-main',
		oberih_asset( 'js/main.js' ),
		array(),
		oberih_asset_ver( 'js/main.js' ),
		array(
			'strategy'  => 'defer',
			'in_footer' => false,
		)
	);

	// Форма запитання — на головній і на сторінці «Контакти».
	if ( is_front_page() || is_page( 'kontakty' ) ) {
		wp_enqueue_script(
			'oberih-form',
			oberih_asset( 'js/form.js' ),
			array(),
			oberih_asset_ver( 'js/form.js' ),
			array(
				'strategy'  => 'defer',
				'in_footer' => false,
			)
		);
	}
}
add_action( 'wp_enqueue_scripts', 'oberih_assets' );

/**
 * Прибираємо зайве з <head>: скрипт емодзі та версію WordPress.
 */
function oberih_cleanup_head() {
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
	remove_action( 'wp_head', 'wp_generator' );
}
add_action( 'init', 'oberih_cleanup_head' );

/**
 * Роздільник у заголовку вкладки: «Сторінка — НРЦ «Оберіг»».
 */
function oberih_title_separator() {
	return '—';
}
add_filter( 'document_title_separator', 'oberih_title_separator' );

/**
 * Клас body «tag» збігається з класом позначки новини в макеті — прибираємо його.
 *
 * @param string[] $classes Класи body.
 */
function oberih_body_class( $classes ) {
	return array_values( array_diff( $classes, array( 'tag' ) ) );
}
add_filter( 'body_class', 'oberih_body_class' );
