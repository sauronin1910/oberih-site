<?php
/**
 * Сторінка «Контакти» (адреса /kontakty/): контакти, форма запитання і зміст сторінки (графік роботи тощо).
 *
 * @package oberih
 */

get_header();
the_post();

oberih_page_hero( get_the_ID(), "НРЦ\u{00A0}«Оберіг»", 'sky' );
?>
	<section class="block page-contacts" aria-labelledby="contacts-title">
		<div class="wrap">
			<?php get_template_part( 'template-parts/contact-block', null, array( 'title' => __( 'Як з нами зв’язатися', 'oberih' ) ) ); ?>
			<?php the_content(); ?>
		</div>
	</section>
<?php
get_footer();
