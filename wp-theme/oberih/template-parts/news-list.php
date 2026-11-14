<?php
/**
 * Список новин у розмітці макета (novyny/index.html): шапка, сітка карток, посторінкова навігація.
 * Використовують home.php (сторінка «Новини») і archive.php (рубрика, мітка, дата).
 *
 * Аргументи: title — заголовок; lead — короткий опис; current — назва для крихт (порожньо — це сама сторінка «Новини»).
 *
 * @package oberih
 */

$oberih_args   = wp_parse_args(
	isset( $args ) ? $args : array(),
	array(
		'title'   => '',
		'lead'    => '',
		'current' => '',
	)
);
$oberih_colors = array( 'coral', 'teal', 'sky', 'green', 'orange', 'amber' );
?>
	<section class="page-hero" aria-labelledby="page-title">
		<div class="wrap">
			<?php echo oberih_news_crumbs( $oberih_args['current'] ); // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано в oberih_news_crumbs(). ?>
			<p class="eyebrow c-coral"><?php echo esc_html( "Життя НРЦ\u{00A0}«Оберіг»" ); ?></p>
			<h1 id="page-title"><?php echo esc_html( $oberih_args['title'] ); ?></h1>
			<?php if ( $oberih_args['lead'] ) : ?>
			<p class="lead"><?php echo esc_html( $oberih_args['lead'] ); ?></p>
			<?php endif; ?>
		</div>
	</section>
	<div class="wrap page-section">
		<?php if ( have_posts() ) : ?>
		<ul class="news-grid">
			<?php
			$oberih_i = 0;
			while ( have_posts() ) {
				the_post();
				oberih_news_card( get_post(), $oberih_colors[ $oberih_i % count( $oberih_colors ) ], 'h2' );
				++$oberih_i;
			}
			?>
		</ul>
			<?php echo oberih_news_pager(); // phpcs:ignore WordPress.Security.EscapeOutput -- розмітка з paginate_links(). ?>
		<?php else : ?>
		<p class="notice"><?php echo oberih_icon( 'info' ); // phpcs:ignore WordPress.Security.EscapeOutput -- статична розмітка svg. ?><span><?php esc_html_e( 'Новин поки немає.', 'oberih' ); ?></span></p>
		<?php endif; ?>
	</div>
