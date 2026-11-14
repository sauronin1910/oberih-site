<?php
/**
 * Шапка сайту: панель доступності, логотип, головне меню. Розмітка — з макета (index.html).
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#263763">
<meta name="format-detection" content="telephone=no">
<link rel="icon" href="<?php echo esc_url( oberih_asset( 'img/favicon-32.png' ) ); ?>" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="<?php echo esc_url( oberih_asset( 'img/apple-touch-icon.png' ) ); ?>">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip" href="#main"><?php esc_html_e( 'Перейти до основного вмісту', 'oberih' ); ?></a>

<!-- Панель доступності -->
<section class="a11ybar" aria-label="<?php esc_attr_e( 'Контакти та налаштування доступності', 'oberih' ); ?>">
	<div class="wrap">
		<div class="contacts">
			<a class="tel" href="<?php echo esc_url( oberih_contact( 'phone_href' ) ); ?>"><?php echo esc_html( oberih_contact( 'phone' ) ); ?></a>
			<a href="<?php echo esc_url( 'mailto:' . oberih_contact( 'email' ) ); ?>"><?php echo esc_html( oberih_contact( 'email' ) ); ?></a>
		</div>
		<div class="a11y-tools" role="group" aria-label="<?php esc_attr_e( 'Налаштування доступності', 'oberih' ); ?>">
			<span class="label"><?php esc_html_e( 'Доступність:', 'oberih' ); ?></span>
			<button type="button" data-scale="1" aria-pressed="true" title="<?php esc_attr_e( 'Звичайний шрифт', 'oberih' ); ?>">A</button>
			<button type="button" data-scale="1.15" aria-pressed="false" title="<?php esc_attr_e( 'Більший шрифт', 'oberih' ); ?>">A+</button>
			<button type="button" data-scale="1.3" aria-pressed="false" title="<?php esc_attr_e( 'Найбільший шрифт', 'oberih' ); ?>">A++</button>
			<button type="button" id="btn-contrast" aria-pressed="false"><?php esc_html_e( 'Контраст', 'oberih' ); ?></button>
			<button type="button" id="btn-links" aria-pressed="false"><?php esc_html_e( 'Підкреслити посилання', 'oberih' ); ?></button>
			<button type="button" id="btn-reset"><?php esc_html_e( 'Скинути', 'oberih' ); ?></button>
			<?php oberih_theme_toggle(); ?>
		</div>
	</div>
</section>

<!-- Шапка -->
<header class="site-header">
	<div class="wrap">
		<a class="brand" href="<?php echo esc_url( home_url( '/' ) ); ?>">
			<span class="logo-badge"><img src="<?php echo esc_url( oberih_asset( 'img/logo-192.jpg' ) ); ?>" alt="" width="192" height="192"></span>
			<span class="brand-text">
				<small>Комунальний заклад Івано-Франківської міської ради</small>
				<strong>Навчально-реабілітаційний центр <span>«Оберіг»</span></strong>
			</span>
		</a>
		<div class="header-right">
			<div class="header-cta">
				<a class="btn btn-ghost" href="<?php echo esc_url( oberih_page_url( 'kontakty' ) ); ?>"><?php esc_html_e( 'Поставити запитання', 'oberih' ); ?></a>
				<a class="btn btn-primary" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>">Вступ до НРЦ&nbsp;«Оберіг»</a>
			</div>
			<button class="burger" type="button" aria-expanded="false" aria-controls="main-nav" aria-label="<?php esc_attr_e( 'Відкрити меню', 'oberih' ); ?>">
				<span></span><span></span><span></span>
			</button>
		</div>
	</div>
</header>

<!-- Головне меню -->
<nav class="main-nav" id="main-nav" aria-label="<?php esc_attr_e( 'Головне меню', 'oberih' ); ?>">
	<div class="wrap">
		<div class="drawer-head">
			<span class="drawer-title"><?php esc_html_e( 'Меню', 'oberih' ); ?></span>
			<button type="button" class="drawer-close" aria-label="<?php esc_attr_e( 'Закрити меню', 'oberih' ); ?>"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
		</div>
		<ul class="menu" id="menu">
			<?php
			wp_nav_menu(
				array(
					'theme_location' => 'primary',
					'container'      => false,
					'items_wrap'     => '%3$s',
					'depth'          => 2,
					'walker'         => new Oberih_Menu_Walker(),
					'fallback_cb'    => 'oberih_menu_fallback',
				)
			);
			?>
		</ul>
		<div class="drawer-foot">
			<a class="btn btn-primary" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>">Вступ до НРЦ&nbsp;«Оберіг»</a>
			<a class="drawer-contact tel" href="<?php echo esc_url( oberih_contact( 'phone_href' ) ); ?>"><?php echo esc_html( oberih_contact( 'phone' ) ); ?></a>
			<a class="drawer-contact" href="<?php echo esc_url( 'mailto:' . oberih_contact( 'email' ) ); ?>"><?php echo esc_html( oberih_contact( 'email' ) ); ?></a>
			<?php oberih_theme_toggle( 'drawer-theme' ); ?>
		</div>
	</div>
</nav>
<div class="nav-backdrop" hidden></div>

<main id="main">
