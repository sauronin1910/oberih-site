<?php
/**
 * Підвал сайту. Розмітка — з макета (index.html).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

?>
</main>

<!-- Підвал -->
<footer class="site-footer">
	<div class="wrap cols">
		<div class="foot-brand">
			<span class="logo-badge"><img src="<?php echo esc_url( oberih_asset( 'img/logo-192.jpg' ) ); ?>" alt="" width="192" height="192"></span>
			<p>Комунальний заклад «Навчально-реабілітаційний центр „Оберіг“» Івано-Франківської міської ради</p>
		</div>
		<?php
		oberih_footer_menu( 'footer-1' );
		oberih_footer_menu( 'footer-2' );
		oberih_footer_menu( 'footer-3' );
		?>
	</div>
	<div class="foot-bottom">
		<div class="wrap">
			<span>© <?php echo esc_html( wp_date( 'Y' ) ); ?> НРЦ&nbsp;«Оберіг». <?php esc_html_e( 'Матеріали сайту використовуються з посиланням на джерело.', 'oberih' ); ?></span>
		</div>
	</div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
