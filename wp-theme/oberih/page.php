<?php
/**
 * Сторінка.
 * — Розділ (сторінка верхнього рівня з підсторінками): шапка і плитки підсторінок.
 * — Сторінка розділу: шапка з «хлібними крихтами», зміст і бічне меню розділу.
 * — Окрема сторінка: шапка і зміст на всю ширину.
 *
 * @package oberih
 */

get_header();
the_post();

$oberih_id         = get_the_ID();
$oberih_section    = oberih_section_root( $oberih_id );
$oberih_color      = oberih_section_color( $oberih_section );
$oberih_is_section = ( $oberih_section === $oberih_id ) && oberih_child_pages( $oberih_id );

if ( $oberih_is_section ) :
	oberih_page_hero( $oberih_id, __( 'Розділ', 'oberih' ), $oberih_color );
	?>
	<div class="wrap page-section">
		<?php
		if ( '' !== trim( get_the_content() ) ) {
			echo '<div class="page-body section-intro-text">';
			the_content();
			echo '</div>';
		}
		echo oberih_section_tiles( $oberih_id ); // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано в oberih_section_tiles().
		?>
	</div>
	<?php
else :
	$oberih_nav = ( $oberih_section !== $oberih_id ) ? oberih_side_nav( $oberih_section, $oberih_id ) : '';
	oberih_page_hero( $oberih_id, $oberih_nav ? get_the_title( $oberih_section ) : '', $oberih_color );
	?>
	<div class="wrap page-layout<?php echo $oberih_nav ? '' : ' page-layout-single'; ?>">
		<div class="page-body">
			<?php the_content(); ?>
		</div>
		<?php echo $oberih_nav; // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано в oberih_side_nav(). ?>
	</div>
	<?php
endif;

get_footer();
