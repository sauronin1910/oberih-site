<?php
/**
 * Створює у WordPress структуру сайту за tools/wp-seed/site-map.json: сторінки розділів і підсторінки,
 * «Головну», «Новини», «Контакти», головне меню і три меню підвалу.
 *
 * Запуск (WP-CLI):  wp eval-file tools/wp-seed/seed.php
 *
 * Можна запускати повторно: наявні сторінки й меню не змінюються і не дублюються, додається лише те, чого бракує.
 * Зміст-заготовку отримують лише сторінки з порожнім змістом. Нічого не видаляє.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$oberih_map = json_decode( file_get_contents( __DIR__ . '/site-map.json' ), true );
if ( ! is_array( $oberih_map ) ) {
	WP_CLI::error( 'Не вдалося прочитати site-map.json' );
}

$oberih_stats = array(
	'pages_new' => 0,
	'pages_old' => 0,
	'menus_new' => 0,
	'menus_old' => 0,
	'filled'    => 0,
);

/**
 * Сторінка за шляхом; якщо її немає — створює.
 *
 * @param string $slug   Slug сторінки.
 * @param string $title  Назва.
 * @param string $lead   Короткий опис (поле «Уривок»).
 * @param int    $parent ID батьківської сторінки.
 * @param int    $order  Порядок серед сусідніх сторінок.
 * @param array  $stats  Лічильники.
 * @param string $content Зміст-заготовка (розмітка редактора); ставиться лише в порожню сторінку.
 * @return int ID сторінки.
 */
function oberih_seed_page( $slug, $title, $lead, $parent, $order, &$stats, $content = '' ) {
	$path = $parent ? get_page_uri( $parent ) . '/' . $slug : $slug;
	$page = get_page_by_path( $path );
	if ( $page ) {
		++$stats['pages_old'];
		if ( '' !== $content && '' === trim( $page->post_content ) ) {
			wp_update_post(
				array(
					'ID'           => $page->ID,
					'post_content' => wp_slash( $content ),
				)
			);
			++$stats['filled'];
		}
		return (int) $page->ID;
	}
	$id = wp_insert_post(
		array(
			'post_type'      => 'page',
			'post_status'    => 'publish',
			'post_title'     => $title,
			'post_name'      => $slug,
			'post_excerpt'   => $lead,
			'post_content'   => wp_slash( $content ),
			'post_parent'    => $parent,
			'menu_order'     => $order,
			'comment_status' => 'closed',
			'ping_status'    => 'closed',
		),
		true
	);
	if ( is_wp_error( $id ) ) {
		WP_CLI::error( "Сторінка «{$title}»: " . $id->get_error_message() );
	}
	++$stats['pages_new'];
	if ( '' !== $content ) {
		++$stats['filled'];
	}
	return (int) $id;
}

/**
 * Додає до меню пункт-сторінку.
 *
 * @param int    $menu_id ID меню.
 * @param int    $page_id ID сторінки.
 * @param int    $parent  ID батьківського пункту меню.
 * @param string $title   Власна назва пункту (порожньо — назва сторінки).
 * @return int ID пункту меню.
 */
function oberih_seed_menu_page( $menu_id, $page_id, $parent = 0, $title = '' ) {
	$args = array(
		'menu-item-object-id' => $page_id,
		'menu-item-object'    => 'page',
		'menu-item-type'      => 'post_type',
		'menu-item-parent-id' => $parent,
		'menu-item-status'    => 'publish',
	);
	if ( '' !== $title && get_the_title( $page_id ) !== $title ) {
		$args['menu-item-title'] = $title;
	}
	return (int) wp_update_nav_menu_item( $menu_id, 0, $args );
}

// 1. Сторінки.
$oberih_home     = oberih_seed_page( 'holovna', 'Головна', '', 0, 0, $oberih_stats );
$oberih_ids      = array();
$oberih_sections = array();
foreach ( $oberih_map['sections'] as $oberih_i => $oberih_s ) {
	$oberih_sid = oberih_seed_page( $oberih_s['slug'], $oberih_s['title'], $oberih_s['lead'], 0, $oberih_i + 1, $oberih_stats );
	if ( ! get_post_meta( $oberih_sid, '_oberih_color', true ) ) {
		update_post_meta( $oberih_sid, '_oberih_color', $oberih_s['color'] );
	}
	$oberih_ids[ $oberih_s['slug'] ] = $oberih_sid;
	$oberih_children                 = array();
	foreach ( $oberih_s['pages'] as $oberih_j => $oberih_p ) {
		$oberih_pid        = oberih_seed_page( $oberih_p['slug'], $oberih_p['title'], $oberih_p['lead'], $oberih_sid, $oberih_j + 1, $oberih_stats, isset( $oberih_p['content'] ) ? $oberih_p['content'] : '' );
		$oberih_children[] = $oberih_pid;
		$oberih_ids[ $oberih_s['slug'] . '/' . $oberih_p['slug'] ] = $oberih_pid;
	}
	$oberih_sections[] = array( $oberih_sid, $oberih_children );
}
$oberih_news     = oberih_seed_page( $oberih_map['news']['slug'], $oberih_map['news']['title'], '', 0, 20, $oberih_stats );
$oberih_contacts = oberih_seed_page( $oberih_map['contacts']['slug'], $oberih_map['contacts']['title'], $oberih_map['contacts']['lead'], 0, 21, $oberih_stats, $oberih_map['contacts']['content'] );
// Короткий опис «Контактів» — і для сторінки, створеної раніше без нього.
if ( ! has_excerpt( $oberih_contacts ) ) {
	wp_update_post(
		array(
			'ID'           => $oberih_contacts,
			'post_excerpt' => $oberih_map['contacts']['lead'],
		)
	);
}
$oberih_ids[ $oberih_map['news']['slug'] ]     = $oberih_news;
$oberih_ids[ $oberih_map['contacts']['slug'] ] = $oberih_contacts;

// 2. Головна — статична сторінка, новини — на сторінці «Новини».
if ( 'page' !== get_option( 'show_on_front' ) ) {
	update_option( 'show_on_front', 'page' );
	update_option( 'page_on_front', $oberih_home );
	update_option( 'page_for_posts', $oberih_news );
}

// 3. Назва сайту — лише під час першого запуску.
if ( ! get_option( 'oberih_seeded' ) ) {
	update_option( 'blogname', "НРЦ\u{00A0}«Оберіг»" );
	update_option( 'blogdescription', 'навчання та реабілітація дітей, Івано-Франківськ' );
	update_option( 'oberih_seeded', gmdate( 'Y-m-d' ) );
}

// 4. Меню.
$oberih_locations = get_theme_mod( 'nav_menu_locations', array() );

if ( wp_get_nav_menu_object( 'Головне меню' ) ) {
	++$oberih_stats['menus_old'];
	$oberih_menu = (int) wp_get_nav_menu_object( 'Головне меню' )->term_id;
} else {
	++$oberih_stats['menus_new'];
	$oberih_menu = (int) wp_create_nav_menu( 'Головне меню' );
	foreach ( $oberih_sections as $oberih_pair ) {
		$oberih_item = oberih_seed_menu_page( $oberih_menu, $oberih_pair[0] );
		foreach ( $oberih_pair[1] as $oberih_pid ) {
			oberih_seed_menu_page( $oberih_menu, $oberih_pid, $oberih_item );
		}
	}
	oberih_seed_menu_page( $oberih_menu, $oberih_news );
	oberih_seed_menu_page( $oberih_menu, $oberih_contacts );
}
if ( empty( $oberih_locations['primary'] ) ) {
	$oberih_locations['primary'] = $oberih_menu;
}

foreach ( $oberih_map['footer'] as $oberih_i => $oberih_col ) {
	$oberih_location = 'footer-' . ( $oberih_i + 1 );
	$oberih_name     = 'Підвал: ' . $oberih_col['title'];
	if ( wp_get_nav_menu_object( $oberih_name ) ) {
		++$oberih_stats['menus_old'];
		$oberih_fmenu = (int) wp_get_nav_menu_object( $oberih_name )->term_id;
	} else {
		++$oberih_stats['menus_new'];
		$oberih_fmenu = (int) wp_create_nav_menu( $oberih_name );
		foreach ( $oberih_col['items'] as $oberih_it ) {
			if ( isset( $oberih_ids[ $oberih_it['path'] ] ) ) {
				oberih_seed_menu_page( $oberih_fmenu, $oberih_ids[ $oberih_it['path'] ], 0, $oberih_it['title'] );
			} else {
				// Посилання не на сторінку, напр. «#sponsors» на головній.
				wp_update_nav_menu_item(
					$oberih_fmenu,
					0,
					array(
						'menu-item-type'   => 'custom',
						'menu-item-title'  => $oberih_it['title'],
						'menu-item-url'    => home_url( '/' . $oberih_it['path'] ),
						'menu-item-status' => 'publish',
					)
				);
			}
		}
	}
	if ( empty( $oberih_locations[ $oberih_location ] ) ) {
		$oberih_locations[ $oberih_location ] = $oberih_fmenu;
	}
}
set_theme_mod( 'nav_menu_locations', $oberih_locations );

WP_CLI::success(
	sprintf(
		'Сторінки: створено %d, уже були %d, заповнено змістом-заготовкою %d. Меню: створено %d, уже були %d.',
		$oberih_stats['pages_new'],
		$oberih_stats['pages_old'],
		$oberih_stats['filled'],
		$oberih_stats['menus_new'],
		$oberih_stats['menus_old']
	)
);
