<?php
/**
 * Сторінка «Новини» (Налаштування → Читання → Сторінка записів): усі новини, 12 на сторінку.
 * Короткий опис під заголовком — поле «Уривок» сторінки «Новини».
 *
 * @package oberih
 */

get_header();

$oberih_page  = (int) get_option( 'page_for_posts' );
$oberih_title = $oberih_page ? get_the_title( $oberih_page ) : __( 'Новини', 'oberih' );
$oberih_lead  = ( $oberih_page && has_excerpt( $oberih_page ) ) ? get_the_excerpt( $oberih_page ) : __( 'Події, оголошення та новини закладу.', 'oberih' );

get_template_part(
	'template-parts/news-list',
	null,
	array(
		'title' => $oberih_title,
		'lead'  => $oberih_lead,
	)
);

get_footer();
