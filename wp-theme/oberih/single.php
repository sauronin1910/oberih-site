<?php
/**
 * Новина (запис) у розмітці макета (novyny/pryklad-novyny.html):
 * крихти, рубрика й дата, фото («Зображення запису»), текст, посилання «Усі новини».
 *
 * @package oberih
 */

get_header();
the_post();

$oberih_cat = oberih_news_category( get_the_ID() );
?>
	<section class="page-hero" aria-labelledby="page-title">
		<div class="wrap">
			<?php echo oberih_news_crumbs( get_the_title() ); // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано в oberih_news_crumbs(). ?>
			<p class="eyebrow c-coral"><?php esc_html_e( 'Новини', 'oberih' ); ?></p>
			<h1 id="page-title"><?php the_title(); ?></h1>
		</div>
	</section>
	<div class="wrap page-layout page-layout-single">
		<article class="page-body article" aria-labelledby="page-title">
			<p class="news-meta">
				<?php if ( $oberih_cat ) : ?>
				<span class="cat"><?php echo esc_html( $oberih_cat ); ?></span>
				<?php endif; ?>
				<time datetime="<?php echo esc_attr( get_the_date( 'Y-m-d' ) ); ?>"><?php echo esc_html( oberih_news_date() ); ?></time>
			</p>
			<?php if ( has_post_thumbnail() ) : ?>
			<figure class="article-photo">
				<?php the_post_thumbnail( 'large' ); ?>
				<?php if ( get_the_post_thumbnail_caption() ) : ?>
				<figcaption class="wp-element-caption"><?php the_post_thumbnail_caption(); ?></figcaption>
				<?php endif; ?>
			</figure>
			<?php endif; ?>
			<?php the_content(); ?>
			<p><a class="more" href="<?php echo esc_url( oberih_news_url() ); ?>"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg> <?php esc_html_e( 'Усі новини', 'oberih' ); ?></a></p>
		</article>
	</div>
<?php
get_footer();
