<?php
/**
 * Тема «Оберіг»: базові налаштування.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Можливості теми й області меню.
 */
function oberih_setup() {
	load_theme_textdomain( 'oberih', get_template_directory() . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'gallery', 'caption', 'style', 'script', 'navigation-widgets' ) );

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
