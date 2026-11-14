<?php
/**
 * Новини однієї рубрики, мітки чи дати — у тому ж оформленні, що й «Новини».
 *
 * @package oberih
 */

get_header();

$oberih_title = wp_strip_all_tags( get_the_archive_title() );

get_template_part(
	'template-parts/news-list',
	null,
	array(
		'title'   => $oberih_title,
		'lead'    => wp_strip_all_tags( get_the_archive_description() ),
		'current' => $oberih_title,
	)
);

get_footer();
