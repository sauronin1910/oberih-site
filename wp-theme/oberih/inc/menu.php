<?php
/**
 * Меню: розмітка така сама, як у макеті (кнопки-підменю, назви у два рядки).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Назва пункту головного меню. Довгу ділимо на два рядки (на ПК);
 * короткі слова «та», «і» лишаються з наступним словом. Те саме робить tools/build_pages.py.
 *
 * @param string $title Назва пункту.
 * @return string Безпечний HTML.
 */
function oberih_menu_label( $title ) {
	$title = trim( wp_strip_all_tags( $title ) );
	$words = preg_split( '/[\s\x{00A0}]+/u', $title, -1, PREG_SPLIT_NO_EMPTY );
	if ( count( $words ) < 2 || mb_strlen( $title ) <= 8 ) {
		return esc_html( $title );
	}
	$best = null;
	$n    = count( $words );
	for ( $i = 1; $i < $n; $i++ ) {
		if ( mb_strlen( $words[ $i - 1 ] ) <= 2 ) {
			continue;
		}
		$a = implode( ' ', array_slice( $words, 0, $i ) );
		$b = implode( ' ', array_slice( $words, $i ) );
		$w = max( mb_strlen( $a ), mb_strlen( $b ) );
		if ( null === $best || $w < $best[0] ) {
			$best = array( $w, $a, $b );
		}
	}
	if ( null === $best ) {
		return esc_html( $title );
	}
	return '<span class="ln">' . esc_html( $best[1] ) . '</span> <span class="ln">' . esc_html( $best[2] ) . '</span>';
}

/**
 * Головне меню: пункт із підпунктами — кнопка, що відкриває підменю; без підпунктів — посилання.
 */
class Oberih_Menu_Walker extends Walker_Nav_Menu {

	/**
	 * Початок підменю.
	 *
	 * @param string   $output HTML.
	 * @param int      $depth  Рівень.
	 * @param stdClass $args   Параметри wp_nav_menu().
	 */
	public function start_lvl( &$output, $depth = 0, $args = null ) {
		$output .= "\n<ul class=\"submenu\">\n";
	}

	/**
	 * Кінець підменю.
	 *
	 * @param string   $output HTML.
	 * @param int      $depth  Рівень.
	 * @param stdClass $args   Параметри wp_nav_menu().
	 */
	public function end_lvl( &$output, $depth = 0, $args = null ) {
		$output .= "</ul>\n";
	}

	/**
	 * Пункт меню.
	 *
	 * @param string   $output HTML.
	 * @param WP_Post  $item   Пункт меню.
	 * @param int      $depth  Рівень.
	 * @param stdClass $args   Параметри wp_nav_menu().
	 * @param int      $id     Не використовується.
	 */
	public function start_el( &$output, $item, $depth = 0, $args = null, $id = 0 ) {
		$classes = empty( $item->classes ) ? array() : (array) $item->classes;
		$title   = apply_filters( 'the_title', $item->title, $item->ID );
		$current = ! empty( $item->current );
		$aria    = $current ? ' aria-current="page"' : '';

		if ( 0 < $depth ) {
			$output .= '<li><a href="' . esc_url( $item->url ) . '"' . $aria . '>' . esc_html( wp_strip_all_tags( $title ) ) . '</a>';
			return;
		}

		$active  = $current || ! empty( $item->current_item_ancestor ) || ! empty( $item->current_item_parent )
			|| in_array( 'current_page_parent', $classes, true );
		$output .= $active ? '<li class="is-active">' : '<li>';
		$label   = '<span class="lbl">' . oberih_menu_label( $title ) . '</span>';

		if ( in_array( 'menu-item-has-children', $classes, true ) ) {
			$output .= '<button type="button" aria-expanded="false">' . $label
				. ' <svg class="icon chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button>';
		} else {
			$output .= '<a href="' . esc_url( $item->url ) . '"' . $aria . '>' . $label . '</a>';
		}
	}

	/**
	 * Кінець пункту меню.
	 *
	 * @param string   $output HTML.
	 * @param WP_Post  $item   Пункт меню.
	 * @param int      $depth  Рівень.
	 * @param stdClass $args   Параметри wp_nav_menu().
	 */
	public function end_el( &$output, $item, $depth = 0, $args = null ) {
		$output .= "</li>\n";
	}
}

/**
 * Якщо головне меню ще не призначене: підказка адміністратору, для відвідувачів — посилання на головну.
 */
function oberih_menu_fallback() {
	echo '<li><a href="' . esc_url( home_url( '/' ) ) . '"><span class="lbl">' . esc_html__( 'Головна', 'oberih' ) . '</span></a></li>';
	if ( current_user_can( 'edit_theme_options' ) ) {
		echo '<li><a href="' . esc_url( admin_url( 'nav-menus.php' ) ) . '"><span class="lbl">' . esc_html__( 'Налаштувати меню', 'oberih' ) . '</span></a></li>';
	}
}

/**
 * Колонка підвалу: заголовок — назва меню (без службового початку «Підвал: »), далі його пункти.
 *
 * @param string $location Область меню: footer-1, footer-2 або footer-3.
 */
function oberih_footer_menu( $location ) {
	$locations = get_nav_menu_locations();
	$menu      = empty( $locations[ $location ] ) ? false : wp_get_nav_menu_object( $locations[ $location ] );
	$items     = $menu ? wp_get_nav_menu_items( $menu->term_id ) : array();
	if ( empty( $items ) ) {
		return;
	}
	echo "<div>\n";
	$title = preg_replace( '/^Підвал:\s*/u', '', $menu->name );
	echo '<h2 class="foot-title">' . esc_html( $title ) . "</h2>\n<ul>";
	foreach ( $items as $item ) {
		echo '<li><a href="' . esc_url( $item->url ) . '">' . esc_html( wp_strip_all_tags( $item->title ) ) . '</a></li>';
	}
	echo "</ul>\n</div>\n";
}
