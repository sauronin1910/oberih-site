<?php
/**
 * Запасний шаблон. Справжні шаблони (головна, сторінка, новини, 404) буде додано на наступних кроках.
 *
 * @package oberih
 */

?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<main id="main">
<?php
if ( have_posts() ) {
	while ( have_posts() ) {
		the_post();
		the_title( '<h1>', '</h1>' );
		the_content();
	}
} else {
	echo '<p>' . esc_html__( 'Тут поки нічого немає.', 'oberih' ) . '</p>';
}
?>
</main>
<?php wp_footer(); ?>
</body>
</html>
