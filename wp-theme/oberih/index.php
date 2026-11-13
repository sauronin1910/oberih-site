<?php
/**
 * Запасний шаблон: показує будь-яку сторінку чи список записів у оформленні внутрішньої сторінки.
 * Окремі шаблони (головна, сторінка розділу, новини, 404) буде додано на наступних кроках.
 *
 * @package oberih
 */

get_header();

if ( is_singular() ) {
	the_post();
	$oberih_title = get_the_title();
	$oberih_lead  = has_excerpt() ? get_the_excerpt() : '';
} elseif ( is_404() ) {
	$oberih_title = __( 'Сторінку не знайдено', 'oberih' );
	$oberih_lead  = '';
} elseif ( is_search() ) {
	$oberih_title = __( 'Результати пошуку', 'oberih' );
	$oberih_lead  = '';
} elseif ( is_home() ) {
	$oberih_title = get_option( 'page_for_posts' ) ? get_the_title( get_option( 'page_for_posts' ) ) : __( 'Новини', 'oberih' );
	$oberih_lead  = '';
} else {
	$oberih_title = wp_strip_all_tags( get_the_archive_title() );
	$oberih_lead  = '';
}
?>
	<section class="page-hero" aria-labelledby="page-title">
		<div class="wrap">
			<h1 id="page-title"><?php echo esc_html( $oberih_title ); ?></h1>
			<?php if ( $oberih_lead ) : ?>
			<p class="lead"><?php echo esc_html( $oberih_lead ); ?></p>
			<?php endif; ?>
		</div>
	</section>
	<div class="wrap page-layout page-layout-single">
		<div class="page-body">
			<?php
			if ( is_singular() ) {
				the_content();
			} elseif ( have_posts() ) {
				while ( have_posts() ) {
					the_post();
					echo '<h2><a href="' . esc_url( get_permalink() ) . '">' . esc_html( get_the_title() ) . '</a></h2>';
					echo '<p>' . esc_html( get_the_date() ) . '</p>';
				}
				the_posts_pagination();
			} else {
				echo '<p>' . esc_html__( 'Тут поки нічого немає.', 'oberih' ) . '</p>';
			}
			?>
		</div>
	</div>
<?php
get_footer();
