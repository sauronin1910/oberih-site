<?php
/**
 * Внутрішні сторінки: розділ, колір, шапка сторінки, «хлібні крихти», бічне меню, огляд розділу.
 * Розмітка — як у макеті (tools/build_pages.py).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Значок макета (SVG).
 *
 * @param string $name  doc | info | user | arrow.
 * @param string $class Клас svg.
 */
function oberih_icon( $name, $class = 'icon' ) {
	$paths = array(
		'doc'   => '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
		'info'  => '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
		'user'  => '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
		'arrow' => '<path d="M5 12h14M13 6l6 6-6 6"/>',
	);
	if ( ! isset( $paths[ $name ] ) ) {
		return '';
	}
	return '<svg class="' . esc_attr( $class ) . '" viewBox="0 0 24 24" aria-hidden="true">' . $paths[ $name ] . '</svg>';
}

/**
 * Сторінка верхнього рівня (розділ), до якої належить сторінка.
 *
 * @param int|WP_Post $post Сторінка.
 * @return int ID розділу (або самої сторінки, якщо вона верхнього рівня).
 */
function oberih_section_root( $post ) {
	$post      = get_post( $post );
	$ancestors = get_post_ancestors( $post );
	return $ancestors ? (int) end( $ancestors ) : (int) $post->ID;
}

/**
 * Колір розділу (клас c-…). Задається полем _oberih_color сторінки розділу.
 *
 * @param int $section_id ID розділу.
 */
function oberih_section_color( $section_id ) {
	$allowed = array( 'teal', 'coral', 'orange', 'sky', 'green', 'amber' );
	$color   = get_post_meta( $section_id, '_oberih_color', true );
	return in_array( $color, $allowed, true ) ? $color : 'teal';
}

/**
 * Дочірні сторінки в порядку меню.
 *
 * @param int $parent_id ID батьківської сторінки.
 * @return WP_Post[]
 */
function oberih_child_pages( $parent_id ) {
	return get_pages(
		array(
			'parent'      => $parent_id,
			'sort_column' => 'menu_order,post_title',
			'post_status' => 'publish',
		)
	);
}

/**
 * «Хлібні крихти»: Головна / розділ / … / поточна сторінка.
 *
 * @param int|WP_Post $post Сторінка.
 */
function oberih_crumbs( $post ) {
	$post  = get_post( $post );
	$items = array( '<li><a href="' . esc_url( home_url( '/' ) ) . '">' . esc_html__( 'Головна', 'oberih' ) . '</a></li>' );
	foreach ( array_reverse( get_post_ancestors( $post ) ) as $ancestor ) {
		$items[] = '<li><a href="' . esc_url( get_permalink( $ancestor ) ) . '">' . esc_html( get_the_title( $ancestor ) ) . '</a></li>';
	}
	$items[] = '<li><span aria-current="page">' . esc_html( get_the_title( $post ) ) . '</span></li>';
	return '<nav class="crumbs" aria-label="' . esc_attr__( 'Хлібні крихти', 'oberih' ) . '"><ol>' . implode( '', $items ) . '</ol></nav>';
}

/**
 * Шапка внутрішньої сторінки: крихти, надзаголовок, заголовок, короткий опис (поле «Уривок»).
 *
 * @param int|WP_Post $post    Сторінка.
 * @param string      $eyebrow Надзаголовок.
 * @param string      $color   Колір надзаголовка.
 */
function oberih_page_hero( $post, $eyebrow, $color ) {
	$post = get_post( $post );
	$lead = has_excerpt( $post ) ? get_the_excerpt( $post ) : '';
	?>
	<section class="page-hero" aria-labelledby="page-title">
		<div class="wrap">
			<?php echo oberih_crumbs( $post ); // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано в oberih_crumbs(). ?>
			<?php if ( $eyebrow ) : ?>
			<p class="eyebrow c-<?php echo esc_attr( $color ); ?>"><?php echo esc_html( $eyebrow ); ?></p>
			<?php endif; ?>
			<h1 id="page-title"><?php echo esc_html( get_the_title( $post ) ); ?></h1>
			<?php if ( $lead ) : ?>
			<p class="lead"><?php echo esc_html( $lead ); ?></p>
			<?php endif; ?>
		</div>
	</section>
	<?php
}

/**
 * Бічне меню розділу: назва розділу і його сторінки.
 *
 * @param int $section_id ID розділу.
 * @param int $current_id ID поточної сторінки.
 */
function oberih_side_nav( $section_id, $current_id ) {
	$children = oberih_child_pages( $section_id );
	if ( ! $children ) {
		return '';
	}
	$title = get_the_title( $section_id );
	$items = '';
	foreach ( $children as $child ) {
		$aria   = ( (int) $child->ID === (int) $current_id || in_array( (int) $child->ID, array_map( 'intval', get_post_ancestors( $current_id ) ), true ) ) ? ' aria-current="page"' : '';
		$items .= '<li><a href="' . esc_url( get_permalink( $child ) ) . '"' . $aria . '>' . esc_html( get_the_title( $child ) ) . '</a></li>';
	}
	return '<nav class="side-nav c-' . esc_attr( oberih_section_color( $section_id ) ) . '" aria-label="' . esc_attr( sprintf( /* translators: %s: назва розділу */ __( 'Розділ «%s»', 'oberih' ), $title ) ) . '">'
		. '<p class="side-title"><a href="' . esc_url( get_permalink( $section_id ) ) . '">' . esc_html( $title ) . '</a></p>'
		. '<ul>' . $items . '</ul></nav>';
}

/**
 * Огляд розділу: плитки його сторінок.
 *
 * @param int $section_id ID розділу.
 */
function oberih_section_tiles( $section_id ) {
	$color = oberih_section_color( $section_id );
	$out   = '';
	foreach ( oberih_child_pages( $section_id ) as $child ) {
		$lead = has_excerpt( $child ) ? get_the_excerpt( $child ) : '';
		$out .= '<li><a class="tile c-' . esc_attr( $color ) . '" href="' . esc_url( get_permalink( $child ) ) . '"><span class="ic">' . oberih_icon( 'doc' ) . '</span>'
			. '<strong>' . esc_html( get_the_title( $child ) ) . '</strong>'
			. ( $lead ? '<span>' . esc_html( $lead ) . '</span>' : '' ) . '</a></li>';
	}
	return $out ? '<ul class="child-grid">' . $out . '</ul>' : '';
}
