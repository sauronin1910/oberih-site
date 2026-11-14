<?php
/**
 * Фото, які завантажує редактор: зменшені копії (для карток і новин) WordPress зберігає у форматі WebP —
 * вони у 1,5–3 рази легші за JPEG при тій самій якості. Оригінал лишається як є.
 * Працює, лише якщо сервер уміє WebP; інакше все як звичайно.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * JPEG → WebP для зменшених копій фото.
 *
 * @param array $formats Відповідність форматів.
 * @return array
 */
function oberih_webp_sizes( $formats ) {
	if ( wp_image_editor_supports( array( 'mime_type' => 'image/webp' ) ) ) {
		$formats['image/jpeg'] = 'image/webp';
	}
	return $formats;
}
add_filter( 'image_editor_output_format', 'oberih_webp_sizes' );
