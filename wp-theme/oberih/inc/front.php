<?php
/**
 * Головна: стрічка новин.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Запасний заголовок для новини без назви: «Новина від 14.11.2026».
 * Без заголовка картка й посилання були б порожні для читача екрана. В адмінці лишається «(без назви)».
 *
 * @param string      $title Заголовок.
 * @param int|WP_Post $post  Запис.
 * @return string
 */
function oberih_untitled_post( $title, $post = 0 ) {
	if ( is_admin() || '' !== trim( wp_strip_all_tags( (string) $title ) ) || ! $post || 'post' !== get_post_type( $post ) ) {
		return $title;
	}
	/* translators: %s: дата публікації */
	return sprintf( __( 'Новина від %s', 'oberih' ), get_the_date( 'd.m.Y', $post ) );
}
add_filter( 'the_title', 'oberih_untitled_post', 10, 2 );
add_filter( 'single_post_title', 'oberih_untitled_post', 10, 2 );

/**
 * Рубрика новини для підпису (крім категорії за замовчуванням, «Uncategorized»).
 *
 * @param int|WP_Post $post Запис.
 * @return string
 */
function oberih_news_category( $post ) {
	$cats = array_filter(
		get_the_category( get_post( $post )->ID ),
		static function ( $cat ) {
			return (int) $cat->term_id !== (int) get_option( 'default_category' );
		}
	);
	return $cats ? reset( $cats )->name : '';
}

/**
 * Фото новини: «Головне зображення», а якщо його не задано — перше зображення, завантажене в новину.
 *
 * @param int|WP_Post $post Запис.
 * @param string      $size Розмір.
 * @param array       $attr Атрибути img.
 * @return string Розмітка img або порожній рядок.
 */
function oberih_news_image( $post, $size = 'medium_large', $attr = array( 'loading' => 'lazy' ) ) {
	$post = get_post( $post );
	$id   = get_post_thumbnail_id( $post );
	if ( ! $id ) {
		$images = get_children(
			array(
				'post_parent'    => $post->ID,
				'post_type'      => 'attachment',
				'post_mime_type' => 'image',
				'numberposts'    => 1,
				'orderby'        => 'menu_order ID',
				'order'          => 'ASC',
			)
		);
		$id     = $images ? (int) array_key_first( $images ) : 0;
	}
	return $id ? wp_get_attachment_image( $id, $size, false, $attr ) : '';
}

/**
 * Дата новини українською: «14 листопада 2026» — незалежно від мови адмінки.
 *
 * @param int|WP_Post $post Запис.
 * @return string
 */
function oberih_news_date( $post = null ) {
	$months = array( 'січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня' );
	$time   = get_post_datetime( $post );
	return $time ? (int) $time->format( 'j' ) . ' ' . $months[ (int) $time->format( 'n' ) - 1 ] . ' ' . $time->format( 'Y' ) : '';
}

/**
 * Адреса сторінки «Новини».
 *
 * @return string
 */
function oberih_news_url() {
	$page = (int) get_option( 'page_for_posts' );
	return $page ? get_permalink( $page ) : home_url( '/' );
}

/**
 * Хлібні крихти розділу новин: Головна → Новини → (поточна).
 *
 * @param string $current Назва поточної сторінки; порожньо — поточна сторінка «Новини».
 * @return string
 */
function oberih_news_crumbs( $current = '' ) {
	$page  = (int) get_option( 'page_for_posts' );
	$news  = $page ? get_the_title( $page ) : __( 'Новини', 'oberih' );
	$items = array( '<li><a href="' . esc_url( home_url( '/' ) ) . '">' . esc_html__( 'Головна', 'oberih' ) . '</a></li>' );
	if ( '' === $current ) {
		$items[] = '<li><span aria-current="page">' . esc_html( $news ) . '</span></li>';
	} else {
		$items[] = '<li><a href="' . esc_url( oberih_news_url() ) . '">' . esc_html( $news ) . '</a></li>';
		$items[] = '<li><span aria-current="page">' . esc_html( $current ) . '</span></li>';
	}
	return '<nav class="crumbs" aria-label="' . esc_attr__( 'Хлібні крихти', 'oberih' ) . '"><ol>' . implode( '', $items ) . '</ol></nav>';
}

/**
 * Посторінкова навігація списку новин.
 *
 * @return string
 */
function oberih_news_pager() {
	$links = paginate_links(
		array(
			'type'               => 'list',
			'mid_size'           => 1,
			'before_page_number' => '<span class="sr-only">' . __( 'Сторінка', 'oberih' ) . ' </span>',
			'prev_text'          => '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg> ' . __( 'Новіші', 'oberih' ),
			'next_text'          => __( 'Старіші', 'oberih' ) . ' <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
		)
	);
	if ( ! $links ) {
		return '';
	}
	return '<nav class="pager" aria-label="' . esc_attr__( 'Сторінки новин', 'oberih' ) . '">' . $links . '</nav>';
}

/**
 * Список новин: 12 на сторінку (ділиться на 3 і на 2 колонки сітки).
 *
 * @param WP_Query $query Запит.
 */
function oberih_news_per_page( $query ) {
	if ( ! is_admin() && $query->is_main_query() && ( $query->is_home() || $query->is_category() || $query->is_tag() || $query->is_date() ) ) {
		$query->set( 'posts_per_page', 12 );
	}
}
add_action( 'pre_get_posts', 'oberih_news_per_page' );

// Заголовок рубрики чи дати без слова «Рубрика:» / «Місяць:» — лише назва.
add_filter( 'get_the_archive_title_prefix', '__return_empty_string' );

/**
 * Картка новини (запис WordPress) у розмітці макета.
 *
 * @param WP_Post $post  Запис.
 * @param string  $color Колір картки.
 * @param string  $tag   Тег заголовка (h3 на головній, h2 у списку новин).
 */
function oberih_news_card( $post, $color, $tag = 'h3' ) {
	$post = get_post( $post );
	$cat  = oberih_news_category( $post );
	?>
	<li class="news-card c-<?php echo esc_attr( $color ); ?>">
		<?php $img = oberih_news_image( $post, 'medium_large' ); ?>
		<?php if ( $img ) : ?>
		<div class="news-img"><?php echo $img; // phpcs:ignore WordPress.Security.EscapeOutput -- розмітка з wp_get_attachment_image(). ?></div>
		<?php else : ?>
		<div class="news-img" aria-hidden="true"><i class="d1"></i><i class="d2"></i></div>
		<?php endif; ?>
		<div class="news-body">
			<div class="news-meta">
				<?php if ( $cat ) : ?>
				<span class="cat"><?php echo esc_html( $cat ); ?></span>
				<?php endif; ?>
				<time datetime="<?php echo esc_attr( get_the_date( 'Y-m-d', $post ) ); ?>"><?php echo esc_html( oberih_news_date( $post ) ); ?></time>
			</div>
			<<?php echo tag_escape( $tag ); ?>><a href="<?php echo esc_url( get_permalink( $post ) ); ?>"><?php echo esc_html( get_the_title( $post ) ); ?></a></<?php echo tag_escape( $tag ); ?>>
			<?php $excerpt = wp_trim_words( get_the_excerpt( $post ), 22 ); ?>
			<?php if ( '' !== trim( $excerpt ) ) : ?>
			<p><?php echo esc_html( $excerpt ); ?></p>
			<?php endif; ?>
		</div>
	</li>
	<?php
}

/**
 * Стрічка новин на головній: 6 останніх записів; якщо записів немає — приклади з макета.
 */
function oberih_front_news() {
	$posts = get_posts(
		array(
			'numberposts'      => 6,
			'post_status'      => 'publish',
			'suppress_filters' => false,
		)
	);
	if ( ! $posts ) {
		get_template_part( 'template-parts/news-examples' );
		return;
	}
	$colors = array( 'coral', 'teal', 'sky', 'green', 'orange', 'amber' );
	foreach ( $posts as $i => $post ) {
		oberih_news_card( $post, $colors[ $i % count( $colors ) ] );
	}
}
