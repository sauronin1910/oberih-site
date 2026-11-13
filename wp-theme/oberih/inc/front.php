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
 * Картка новини (запис WordPress) у розмітці макета.
 *
 * @param WP_Post $post  Запис.
 * @param string  $color Колір картки.
 * @param string  $tag   Тег заголовка (h3 на головній, h2 у списку новин).
 */
function oberih_news_card( $post, $color, $tag = 'h3' ) {
	$post = get_post( $post );
	$cats = array_filter(
		get_the_category( $post->ID ),
		static function ( $cat ) {
			return (int) $cat->term_id !== (int) get_option( 'default_category' );
		}
	);
	$cat  = $cats ? reset( $cats )->name : '';
	?>
	<li class="news-card c-<?php echo esc_attr( $color ); ?>">
		<?php if ( has_post_thumbnail( $post ) ) : ?>
		<div class="news-img"><?php echo get_the_post_thumbnail( $post, 'medium_large', array( 'loading' => 'lazy' ) ); ?></div>
		<?php else : ?>
		<div class="news-img" aria-hidden="true"><i class="d1"></i><i class="d2"></i></div>
		<?php endif; ?>
		<div class="news-body">
			<div class="news-meta">
				<?php if ( $cat ) : ?>
				<span class="cat"><?php echo esc_html( $cat ); ?></span>
				<?php endif; ?>
				<time datetime="<?php echo esc_attr( get_the_date( 'Y-m-d', $post ) ); ?>"><?php echo esc_html( get_the_date( 'j F Y', $post ) ); ?></time>
			</div>
			<<?php echo tag_escape( $tag ); ?>><a href="<?php echo esc_url( get_permalink( $post ) ); ?>"><?php echo esc_html( get_the_title( $post ) ); ?></a></<?php echo tag_escape( $tag ); ?>>
			<p><?php echo esc_html( wp_trim_words( get_the_excerpt( $post ), 22 ) ); ?></p>
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
