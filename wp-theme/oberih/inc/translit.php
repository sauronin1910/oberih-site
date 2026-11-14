<?php
/**
 * Адреси сторінок, новин, рубрик і назви завантажених файлів — латиницею
 * за офіційною транслітерацією (постанова КМУ № 55 від 27.01.2010):
 * «Осінній тиждень» → osinnii-tyzhden, «Подія у Яремчі.jpg» → podiia-u-iaremchi.jpg.
 * Уже збережені адреси не змінюються.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Транслітерація українського тексту латиницею.
 *
 * @param string $text Текст.
 * @return string
 */
function oberih_translit( $text ) {
	if ( ! preg_match( '/[\x{0400}-\x{04FF}]/u', $text ) ) {
		return $text;
	}
	$text = mb_strtolower( $text, 'UTF-8' );
	$text = str_replace( 'зг', 'zgh', $text );
	// На початку слова: є, ї, й, ю, я.
	$text = preg_replace_callback(
		'/(^|[^\p{L}\x{2019}\'])([єїйюя])/u',
		static function ( $m ) {
			$first = array(
				'є' => 'ye',
				'ї' => 'yi',
				'й' => 'y',
				'ю' => 'yu',
				'я' => 'ya',
			);
			return $m[1] . $first[ $m[2] ];
		},
		$text
	);
	$map = array(
		'а' => 'a',
		'б' => 'b',
		'в' => 'v',
		'г' => 'h',
		'ґ' => 'g',
		'д' => 'd',
		'е' => 'e',
		'є' => 'ie',
		'ж' => 'zh',
		'з' => 'z',
		'и' => 'y',
		'і' => 'i',
		'ї' => 'i',
		'й' => 'i',
		'к' => 'k',
		'л' => 'l',
		'м' => 'm',
		'н' => 'n',
		'о' => 'o',
		'п' => 'p',
		'р' => 'r',
		'с' => 's',
		'т' => 't',
		'у' => 'u',
		'ф' => 'f',
		'х' => 'kh',
		'ц' => 'ts',
		'ч' => 'ch',
		'ш' => 'sh',
		'щ' => 'shch',
		'ю' => 'iu',
		'я' => 'ia',
		'ь' => '',
		'’' => '',
		'\'' => '',
		'ʼ' => '',
		// Російські літери, якщо трапляться.
		'ё' => 'io',
		'ы' => 'y',
		'э' => 'e',
		'ъ' => '',
	);
	return strtr( $text, $map );
}

/**
 * Адреса (slug) під час збереження: латиницею. Спрацьовує до стандартної обробки WordPress.
 *
 * @param string $title     Заголовок.
 * @param string $raw_title Початковий заголовок.
 * @param string $context   Контекст.
 * @return string
 */
function oberih_translit_slug( $title, $raw_title = '', $context = 'display' ) {
	return 'save' === $context ? oberih_translit( $title ) : $title;
}
add_filter( 'sanitize_title', 'oberih_translit_slug', 9, 3 );

/**
 * Назва завантаженого файлу: латиницею.
 *
 * @param string $filename Назва файлу.
 * @return string
 */
function oberih_translit_file( $filename ) {
	return oberih_translit( $filename );
}
add_filter( 'sanitize_file_name', 'oberih_translit_file', 9 );
