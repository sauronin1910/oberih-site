<?php
/**
 * Блоки змісту в стилі макета: примітка, списки, кроки, таблиці.
 * Редактор працює зі звичайними блоками WordPress; потрібні класи тема додає під час показу сторінки.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Стиль абзацу «Примітка» у редакторі.
 */
function oberih_block_styles() {
	register_block_style(
		'core/paragraph',
		array(
			'name'  => 'notice',
			'label' => __( 'Примітка', 'oberih' ),
		)
	);
	register_block_style(
		'core/list',
		array(
			'name'  => 'steps',
			'label' => __( 'Кроки', 'oberih' ),
		)
	);
}
add_action( 'init', 'oberih_block_styles' );

/**
 * Перетворює розмітку блоків на розмітку макета.
 *
 * @param string $html  HTML блоку.
 * @param array  $block Дані блоку.
 * @return string
 */
function oberih_render_block( $html, $block ) {
	if ( is_admin() || wp_is_json_request() || empty( $block['blockName'] ) ) {
		return $html;
	}
	$class = isset( $block['attrs']['className'] ) ? (string) $block['attrs']['className'] : '';

	switch ( $block['blockName'] ) {
		case 'core/paragraph':
			// Примітка: значок «i» і текст у <span>, як у макеті.
			if ( false !== strpos( $class, 'is-style-notice' )
				&& preg_match( '/^\s*<p([^>]*)>(.*)<\/p>\s*$/s', $html, $m ) ) {
				$attrs = preg_replace( '/\bis-style-notice\b/', 'notice', $m[1] );
				return '<p' . $attrs . '>' . oberih_icon( 'info' ) . '<span>' . $m[2] . '</span></p>';
			}
			break;

		case 'core/list':
			// Маркований список — «bullets», нумерований — «steps» (кроки), якщо не вибрано інше.
			$p = new WP_HTML_Tag_Processor( $html );
			if ( $p->next_tag() && in_array( $p->get_tag(), array( 'UL', 'OL' ), true ) ) {
				$ordered = 'OL' === $p->get_tag();
				$p->add_class( ( $ordered || false !== strpos( $class, 'is-style-steps' ) ) ? 'steps' : 'bullets' );
				return $p->get_updated_html();
			}
			break;

		case 'core/table':
			// Таблиця з горизонтальною прокруткою; підпис — у <caption>, як у макеті.
			$caption = '';
			if ( preg_match( '/<figcaption[^>]*>(.*?)<\/figcaption>/s', $html, $m ) ) {
				$caption = trim( $m[1] );
				$html    = str_replace( $m[0], '', $html );
			}
			// <figure> -> <section> з назвою: область з прокруткою, доступна з клавіатури (як у макеті).
			$html = preg_replace( '/^(\s*)<figure\b/', '$1<section', $html, 1 );
			$html = preg_replace( '/<\/figure>(\s*)$/', '</section>$1', $html, 1 );
			$p    = new WP_HTML_Tag_Processor( $html );
			if ( $p->next_tag( 'section' ) ) {
				$p->add_class( 'table-wrap' );
				$p->set_attribute( 'tabindex', '0' );
				$p->set_attribute( 'aria-label', $caption ? wp_strip_all_tags( $caption ) : __( 'Таблиця', 'oberih' ) );
			}
			if ( $p->next_tag( 'table' ) ) {
				$p->add_class( 'data-table' );
			}
			$html = $p->get_updated_html();
			if ( $caption ) {
				$html = preg_replace( '/(<table[^>]*>)/', '$1<caption>' . $caption . '</caption>', $html, 1 );
			}
			// Заголовки стовпців таблиці.
			$html = str_replace( '<th>', '<th scope="col">', $html );
			return $html;
	}
	return $html;
}
add_filter( 'render_block', 'oberih_render_block', 10, 2 );
