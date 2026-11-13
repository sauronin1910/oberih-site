<?php
/**
 * Сторінку не знайдено (404). Розмітка — з макета (404.html).
 *
 * @package oberih
 */

get_header();
?>
	<section class="page-hero err404" aria-labelledby="page-title">
		<div class="wrap">
			<p class="err-code" aria-hidden="true">404</p>
			<h1 id="page-title"><?php esc_html_e( 'Сторінку не знайдено', 'oberih' ); ?></h1>
			<p class="lead"><?php esc_html_e( 'Можливо, адресу введено з помилкою або сторінку перенесли. Скористайтеся меню або перейдіть до одного з розділів.', 'oberih' ); ?></p>
			<div class="actions">
				<a class="btn btn-primary" href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'На головну', 'oberih' ); ?></a>
				<a class="btn btn-ghost" href="<?php echo esc_url( oberih_page_url( 'kontakty' ) ); ?>"><?php esc_html_e( 'Контакти', 'oberih' ); ?></a>
			</div>
			<?php
			$oberih_sections = get_pages(
				array(
					'parent'      => 0,
					'sort_column' => 'menu_order',
					'post_status' => 'publish',
				)
			);
			$oberih_links    = '';
			foreach ( $oberih_sections as $oberih_s ) {
				if ( oberih_child_pages( $oberih_s->ID ) ) {
					$oberih_links .= '<li><a href="' . esc_url( get_permalink( $oberih_s ) ) . '">' . esc_html( get_the_title( $oberih_s ) ) . '</a></li>';
				}
			}
			if ( $oberih_links ) {
				echo '<ul class="err-links">' . $oberih_links . '</ul>'; // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано вище.
			}
			?>
		</div>
	</section>
<?php
get_footer();
