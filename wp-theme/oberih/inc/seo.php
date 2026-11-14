<?php
/**
 * Метадані сторінок для пошуковиків і соцмереж — за тими самими правилами, що й у макеті (tools/build_pages.py):
 * опис (description), Open Graph, картка для X/Twitter, дані організації (JSON-LD) на головній,
 * noindex для 404, короткий <title> для довгих назв.
 *
 * Адреси (og:url, og:image) — повні, від адреси сайту з налаштувань WordPress; canonical додає саме ядро WordPress.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Назва закладу в текстах.
 *
 * @return string
 */
function oberih_short_name() {
	return "НРЦ\u{00A0}«Оберіг»";
}

/**
 * Опис сторінки (meta description, og:description).
 *
 * @return string Порожній рядок — опис не потрібен (пошук, 404 має свій).
 */
function oberih_meta_description() {
	$city = __( 'м. Івано-Франківськ', 'oberih' );
	$tail = sprintf( /* translators: %s: місто */ __( 'Офіційний сайт закладу, %s.', 'oberih' ), $city );

	if ( is_front_page() ) {
		return 'Комунальний заклад «НРЦ „Оберіг“» Івано-Франківської міської ради: навчання та комплексна реабілітація дітей з особливими освітніми потребами.';
	}
	if ( is_404() ) {
		return sprintf( 'Сторінку не знайдено. Перейдіть на головну або скористайтеся меню. %s, %s.', oberih_short_name(), $city );
	}
	if ( is_search() ) {
		return '';
	}
	if ( is_home() ) {
		$page = (int) get_option( 'page_for_posts' );
		$text = ( $page && has_excerpt( $page ) ) ? get_the_excerpt( $page ) : sprintf( 'Події, оголошення та новини %s.', oberih_short_name() );
		return oberih_meta_finish( $text, '', $tail );
	}
	if ( is_category() || is_tag() || is_date() ) {
		return oberih_meta_finish( sprintf( 'Новини %s: %s.', oberih_short_name(), wp_strip_all_tags( get_the_archive_title() ) ), '', $tail );
	}
	if ( is_singular( 'post' ) ) {
		$post = get_queried_object();
		$text = has_excerpt( $post ) ? get_the_excerpt( $post ) : wp_trim_words( wp_strip_all_tags( strip_shortcodes( $post->post_content ) ), 30, '…' );
		return oberih_meta_finish( '' !== trim( $text ) ? $text : get_the_title( $post ) . '.', '', $tail );
	}
	if ( is_page() ) {
		$post    = get_queried_object();
		$text    = has_excerpt( $post ) ? get_the_excerpt( $post ) : get_the_title( $post ) . '.';
		$section = oberih_section_root( $post );
		$sec     = ( $section !== $post->ID ) ? get_the_title( $section ) : '';
		return oberih_meta_finish( $text, $sec, $tail );
	}
	return '';
}

/**
 * Короткий опис доповнюємо до зручної для пошуковиків довжини (як у макеті); довгий обрізаємо до 160 знаків.
 *
 * @param string $text    Опис.
 * @param string $section Назва розділу (для підсторінок).
 * @param string $tail    «Офіційний сайт закладу, м. …».
 * @return string
 */
function oberih_meta_finish( $text, $section, $tail ) {
	$text = trim( preg_replace( '/\s+/u', ' ', wp_strip_all_tags( $text ) ) );
	if ( '' !== $text && ! preg_match( '/[.!?…]$/u', $text ) ) {
		$text .= '.';
	}
	if ( mb_strlen( $text ) < 70 ) {
		if ( false !== mb_strpos( $text, 'Оберіг' ) ) {
			$text .= ' ' . $tail;
		} else {
			$text .= ' ' . ( $section ? $section . ' — ' : '' ) . oberih_short_name() . ', ' . __( 'м. Івано-Франківськ', 'oberih' ) . '.';
		}
	}
	if ( mb_strlen( $text ) > 160 ) {
		$text = rtrim( mb_substr( $text, 0, 157 ), ' ,.;:—-' ) . '…';
	}
	return $text;
}

/**
 * Зображення для соцмереж: фото новини, інакше — картинка сайту (1200×630).
 *
 * @return array{url:string,width:int,height:int,alt:string}
 */
function oberih_og_image() {
	if ( is_singular( 'post' ) ) {
		$id  = oberih_news_image_id( get_queried_object_id() );
		$src = $id ? wp_get_attachment_image_src( $id, 'large' ) : false;
		if ( $src ) {
			return array(
				'url'    => $src[0],
				'width'  => (int) $src[1],
				'height' => (int) $src[2],
				'alt'    => (string) get_post_meta( $id, '_wp_attachment_image_alt', true ),
			);
		}
	}
	return array(
		'url'    => oberih_asset( 'img/og-image.jpg' ),
		'width'  => 1200,
		'height' => 630,
		'alt'    => 'Логотип і назва ' . oberih_short_name(),
	);
}

/**
 * Повна адреса поточної сторінки (для og:url).
 *
 * @return string
 */
function oberih_current_url() {
	if ( is_singular() ) {
		return (string) wp_get_canonical_url();
	}
	if ( is_front_page() ) {
		return home_url( '/' );
	}
	global $wp;
	return home_url( user_trailingslashit( $wp->request ) );
}

/**
 * Метатеги в <head>.
 */
function oberih_meta_tags() {
	if ( is_search() ) {
		return;
	}
	$desc  = oberih_meta_description();
	$title = is_front_page() ? 'Навчально-реабілітаційний центр «Оберіг»' : wp_strip_all_tags( html_entity_decode( wp_get_document_title(), ENT_QUOTES, 'UTF-8' ) );
	if ( ! is_front_page() ) {
		// Заголовок без «— НРЦ «Оберіг»» (як og:title у макеті).
		$title = preg_replace( '/\s+—\s+' . preg_quote( wp_strip_all_tags( get_bloginfo( 'name' ) ), '/' ) . '$/u', '', $title );
	}
	$img  = oberih_og_image();
	$tags = array(
		array( 'name', 'description', $desc ),
		array( 'property', 'og:type', is_singular( 'post' ) ? 'article' : 'website' ),
		array( 'property', 'og:locale', 'uk_UA' ),
		array( 'property', 'og:site_name', wp_strip_all_tags( get_bloginfo( 'name' ) ) ),
		array( 'property', 'og:title', $title ),
		array( 'property', 'og:description', $desc ),
		array( 'property', 'og:url', is_404() ? '' : oberih_current_url() ),
		array( 'property', 'og:image', $img['url'] ),
		array( 'property', 'og:image:width', $img['width'] ? (string) $img['width'] : '' ),
		array( 'property', 'og:image:height', $img['height'] ? (string) $img['height'] : '' ),
		array( 'property', 'og:image:alt', $img['alt'] ),
		array( 'name', 'twitter:card', 'summary_large_image' ),
	);
	if ( is_singular( 'post' ) ) {
		$tags[] = array( 'property', 'article:published_time', get_post_time( 'c', false, get_queried_object() ) );
		$tags[] = array( 'property', 'article:modified_time', get_post_modified_time( 'c', false, get_queried_object() ) );
	}
	foreach ( $tags as $t ) {
		if ( '' !== $t[2] ) {
			printf( '<meta %s="%s" content="%s">' . "\n", esc_attr( $t[0] ), esc_attr( $t[1] ), esc_attr( $t[2] ) );
		}
	}
	// Канонічна адреса для списку новин і категорій (окремим сторінкам її додає сам WordPress).
	if ( ! is_singular() && ! is_404() && ! is_front_page() ) {
		echo '<link rel="canonical" href="' . esc_url( oberih_current_url() ) . '">' . "\n";
	}

	if ( is_front_page() ) {
		$org = array(
			'@context'      => 'https://schema.org',
			'@type'         => 'EducationalOrganization',
			'name'          => 'Комунальний заклад «Навчально-реабілітаційний центр „Оберіг“» Івано-Франківської міської ради',
			'alternateName' => 'НРЦ «Оберіг»',
			'url'           => home_url( '/' ),
			'logo'          => oberih_asset( 'img/logo.jpg' ),
			'address'       => array(
				'@type'           => 'PostalAddress',
				'streetAddress'   => 'вул. Гната Хоткевича, 52-А',
				'addressLocality' => 'Івано-Франківськ',
				'addressRegion'   => 'Івано-Франківська область',
				'postalCode'      => '76020',
				'addressCountry'  => 'UA',
			),
			'telephone'     => '+380342550524',
			'email'         => oberih_contact( 'email' ),
		);
		echo '<script type="application/ld+json">' . wp_json_encode( $org, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES ) . "</script>\n";
	}
}
add_action( 'wp_head', 'oberih_meta_tags', 2 );

/**
 * Сторінку «не знайдено» не індексуємо (пошук WordPress закриває сам).
 *
 * @param array $robots Директиви robots.
 * @return array
 */
function oberih_robots( $robots ) {
	if ( is_404() ) {
		$robots['noindex'] = true;
	}
	return $robots;
}
add_filter( 'wp_robots', 'oberih_robots' );

/**
 * Довгий заголовок у вкладці — без «— НРЦ «Оберіг»» (пошуковики обрізають понад ~70 знаків), як у макеті.
 *
 * @param array $parts Частини заголовка.
 * @return array
 */
function oberih_short_title( $parts ) {
	if ( ! is_front_page() && isset( $parts['title'], $parts['site'] ) && mb_strlen( $parts['title'] . ' — ' . $parts['site'] ) > 70 ) {
		unset( $parts['site'] );
	}
	return $parts;
}
add_filter( 'document_title_parts', 'oberih_short_title', 20 );
