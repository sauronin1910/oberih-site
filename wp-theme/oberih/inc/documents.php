<?php
/**
 * Документи (ст. 30 ЗУ «Про освіту»): окремий тип запису «Документ».
 *
 * Редактор додає документ в адмінці «Документи → Додати документ»: назва, файл (PDF), дата затвердження
 * і сторінка сайту, де його показати. Сторінка сама виводить список своїх документів — найновіші вгорі,
 * з датою затвердження й розміром файлу. Окремої сторінки в документа немає: посилання веде на файл.
 *
 * Якщо в змісті сторінки є приклад-заглушка зі списком документів («… додасть адміністрація»),
 * справжній список стає на її місце; інакше — на початку змісту сторінки.
 *
 * @package oberih
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Тип запису «Документ».
 */
function oberih_register_documents() {
	register_post_type(
		'oberih_doc',
		array(
			'labels'              => array(
				'name'               => __( 'Документи', 'oberih' ),
				'singular_name'      => __( 'Документ', 'oberih' ),
				'menu_name'          => __( 'Документи', 'oberih' ),
				'all_items'          => __( 'Усі документи', 'oberih' ),
				'add_new'            => __( 'Додати документ', 'oberih' ),
				'add_new_item'       => __( 'Новий документ', 'oberih' ),
				'edit_item'          => __( 'Редагувати документ', 'oberih' ),
				'new_item'           => __( 'Новий документ', 'oberih' ),
				'search_items'       => __( 'Шукати документи', 'oberih' ),
				'not_found'          => __( 'Документів не знайдено.', 'oberih' ),
				'not_found_in_trash' => __( 'У кошику документів немає.', 'oberih' ),
			),
			'public'              => false,
			'publicly_queryable'  => false,
			'exclude_from_search' => true,
			'show_ui'             => true,
			'show_in_menu'        => true,
			'show_in_rest'        => false,
			'menu_position'       => 21,
			'menu_icon'           => 'dashicons-media-document',
			'supports'            => array( 'title' ),
			'capability_type'     => 'post',
			'map_meta_cap'        => true,
			'has_archive'         => false,
			'rewrite'             => false,
		)
	);
}
add_action( 'init', 'oberih_register_documents' );

/**
 * Поля документа.
 *
 * @param int|WP_Post $doc Документ.
 * @return array{file:int,date:string,page:int}
 */
function oberih_doc_fields( $doc ) {
	$id = get_post( $doc )->ID;
	return array(
		'file' => (int) get_post_meta( $id, '_oberih_doc_file', true ),
		'date' => (string) get_post_meta( $id, '_oberih_doc_date', true ),
		'page' => (int) get_post_meta( $id, '_oberih_doc_page', true ),
	);
}

/**
 * Дата «РРРР-ММ-ДД» → «ДД.ММ.РРРР».
 *
 * @param string $ymd Дата.
 * @return string
 */
function oberih_doc_date_label( $ymd ) {
	$d = DateTime::createFromFormat( '!Y-m-d', $ymd );
	return $d ? $d->format( 'd.m.Y' ) : '';
}

/**
 * Розмір файлу українською: «850 КБ», «1,2 МБ».
 *
 * @param int $bytes Байти.
 * @return string
 */
function oberih_file_size( $bytes ) {
	if ( $bytes <= 0 ) {
		return '';
	}
	if ( $bytes < MB_IN_BYTES ) {
		return max( 1, (int) round( $bytes / KB_IN_BYTES ) ) . ' КБ';
	}
	return str_replace( '.', ',', (string) round( $bytes / MB_IN_BYTES, 1 ) ) . ' МБ';
}

/**
 * Документи сторінки: опубліковані, з файлом; найновіші (за датою затвердження) вгорі.
 *
 * @param int $page_id ID сторінки.
 * @return WP_Post[]
 */
function oberih_page_docs( $page_id ) {
	$docs = get_posts(
		array(
			'post_type'   => 'oberih_doc',
			'post_status' => 'publish',
			'numberposts' => -1,
			'meta_key'    => '_oberih_doc_page', // phpcs:ignore WordPress.DB.SlowDBQuery -- кілька десятків записів.
			'meta_value'  => (int) $page_id, // phpcs:ignore WordPress.DB.SlowDBQuery
		)
	);
	$docs = array_values(
		array_filter(
			$docs,
			static function ( $doc ) {
				$file = oberih_doc_fields( $doc )['file'];
				return $file && get_attached_file( $file );
			}
		)
	);
	usort(
		$docs,
		static function ( $a, $b ) {
			$da = oberih_doc_fields( $a )['date'] ? oberih_doc_fields( $a )['date'] : substr( $a->post_date, 0, 10 );
			$db = oberih_doc_fields( $b )['date'] ? oberih_doc_fields( $b )['date'] : substr( $b->post_date, 0, 10 );
			return ( $db <=> $da ) ? ( $db <=> $da ) : strcmp( $a->post_title, $b->post_title );
		}
	);
	return $docs;
}

/**
 * Список документів сторінки в розмітці макета.
 *
 * @param int $page_id ID сторінки.
 * @return string Порожній рядок, якщо документів немає.
 */
function oberih_docs_list( $page_id ) {
	$items = '';
	foreach ( oberih_page_docs( $page_id ) as $doc ) {
		$f    = oberih_doc_fields( $doc );
		$path = get_attached_file( $f['file'] );
		$ext  = strtoupper( pathinfo( $path, PATHINFO_EXTENSION ) );
		$size = oberih_file_size( (int) @filesize( $path ) ); // phpcs:ignore WordPress.PHP.NoSilencedErrors -- файл може бути недоступний.
		$date = oberih_doc_date_label( $f['date'] );
		$meta = array_filter(
			array(
				$date ? sprintf( /* translators: %s: дата */ __( 'Затверджено %s', 'oberih' ), $date ) : sprintf( /* translators: %s: дата */ __( 'Оприлюднено %s', 'oberih' ), get_the_date( 'd.m.Y', $doc ) ),
				$size,
			)
		);
		$items .= '<li><a href="' . esc_url( wp_get_attachment_url( $f['file'] ) ) . '" type="' . esc_attr( get_post_mime_type( $f['file'] ) ) . '">'
			. '<svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/></svg>'
			. '<span>' . esc_html( get_the_title( $doc ) ) . '<small>' . esc_html( implode( ' · ', $meta ) ) . '</small></span>'
			. '<em class="pdf">' . esc_html( $ext ) . '</em></a></li>';
	}
	return $items ? '<ul class="doc-list doc-list-page">' . $items . '</ul>' : '';
}

/**
 * Чи є в змісті сторінки приклад-заглушка зі списком документів (з макета).
 *
 * @param string $html Розмітка.
 * @return bool
 */
function oberih_is_docs_placeholder( $html ) {
	return false !== strpos( $html, 'doc-list' ) && false !== strpos( $html, 'додасть адміністрація' );
}

/**
 * Список документів сторінки на місці прикладу-заглушки.
 *
 * @param string $content Розмітка блоку.
 * @param array  $block   Блок.
 * @return string
 */
function oberih_docs_replace_placeholder( $content, $block ) {
	if ( 'core/html' !== $block['blockName'] || ! is_page() || ! oberih_is_docs_placeholder( $content ) ) {
		return $content;
	}
	$list = oberih_docs_list( get_queried_object_id() );
	return $list ? $list : $content;
}
add_filter( 'render_block', 'oberih_docs_replace_placeholder', 10, 2 );

/**
 * Список документів для виводу перед змістом сторінки — якщо в змісті немає заглушки, на місці якої він стане.
 *
 * @param int $page_id ID сторінки.
 * @return string
 */
function oberih_docs_before_content( $page_id ) {
	return oberih_is_docs_placeholder( (string) get_post_field( 'post_content', $page_id ) ) ? '' : oberih_docs_list( $page_id );
}

/* ---------- Адмінка ---------- */

/**
 * Поля документа в редакторі.
 */
function oberih_doc_meta_boxes() {
	add_meta_box( 'oberih_doc_fields', __( 'Файл і де показати', 'oberih' ), 'oberih_doc_meta_box', 'oberih_doc', 'normal', 'high' );
	add_meta_box( 'oberih_page_docs', __( 'Документи на цій сторінці', 'oberih' ), 'oberih_page_docs_box', 'page', 'side' );
}
add_action( 'add_meta_boxes', 'oberih_doc_meta_boxes' );

/**
 * Форма полів документа.
 *
 * @param WP_Post $post Документ.
 */
function oberih_doc_meta_box( $post ) {
	$f = oberih_doc_fields( $post );
	if ( ! $f['page'] && isset( $_GET['oberih_page'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- лише попереднє заповнення форми.
		$f['page'] = absint( $_GET['oberih_page'] ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	}
	$file_name = $f['file'] ? wp_basename( (string) get_attached_file( $f['file'] ) ) : '';
	wp_nonce_field( 'oberih_doc_save', 'oberih_doc_nonce' );
	?>
	<table class="form-table" role="presentation">
		<tr>
			<th scope="row"><?php esc_html_e( 'Файл', 'oberih' ); ?></th>
			<td>
				<input type="hidden" name="oberih_doc_file" id="oberih-doc-file" value="<?php echo esc_attr( $f['file'] ? $f['file'] : '' ); ?>">
				<p id="oberih-doc-file-name"><?php echo $file_name ? esc_html( $file_name ) : esc_html__( 'Файл не вибрано.', 'oberih' ); ?></p>
				<button type="button" class="button" id="oberih-doc-pick"><?php esc_html_e( 'Вибрати або завантажити файл', 'oberih' ); ?></button>
				<button type="button" class="button-link button-link-delete" id="oberih-doc-clear" style="margin-left:12px;vertical-align:middle"<?php echo $f['file'] ? '' : ' hidden'; ?>><?php esc_html_e( 'Прибрати файл', 'oberih' ); ?></button>
				<p class="description"><?php esc_html_e( 'Бажано PDF. Документ без файлу на сайті не показується.', 'oberih' ); ?></p>
			</td>
		</tr>
		<tr>
			<th scope="row"><label for="oberih-doc-date"><?php esc_html_e( 'Дата затвердження', 'oberih' ); ?></label></th>
			<td>
				<input type="date" name="oberih_doc_date" id="oberih-doc-date" value="<?php echo esc_attr( $f['date'] ); ?>" aria-describedby="oberih-doc-date-desc">
				<p class="description" id="oberih-doc-date-desc"><?php esc_html_e( 'Оприлюднити треба не пізніше ніж через 10 робочих днів після затвердження (ст. 30 ЗУ «Про освіту»). Якщо дату не вказано, на сайті буде дата оприлюднення.', 'oberih' ); ?></p>
			</td>
		</tr>
		<tr>
			<th scope="row"><label for="oberih-doc-page"><?php esc_html_e( 'Сторінка сайту', 'oberih' ); ?></label></th>
			<td>
				<?php
				wp_dropdown_pages(
					array(
						'name'              => 'oberih_doc_page',
						'id'                => 'oberih-doc-page',
						'selected'          => $f['page'], // phpcs:ignore WordPress.Security.EscapeOutput -- число.
						'show_option_none'  => esc_html__( '— оберіть сторінку —', 'oberih' ),
						'option_none_value' => '0',
						'sort_column'       => 'menu_order, post_title',
					)
				);
				?>
				<p class="description"><?php esc_html_e( 'Наприклад, «Статут» або «Фінансова звітність». Документ з’явиться у списку документів цієї сторінки.', 'oberih' ); ?></p>
			</td>
		</tr>
	</table>
	<?php
}

/**
 * Збереження полів документа.
 *
 * @param int $post_id ID документа.
 */
function oberih_doc_save( $post_id ) {
	if ( ! isset( $_POST['oberih_doc_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['oberih_doc_nonce'] ) ), 'oberih_doc_save' ) ) {
		return;
	}
	if ( ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) || ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}
	$file = isset( $_POST['oberih_doc_file'] ) ? absint( $_POST['oberih_doc_file'] ) : 0;
	$file = ( $file && 'attachment' === get_post_type( $file ) ) ? $file : 0;
	$date = isset( $_POST['oberih_doc_date'] ) ? sanitize_text_field( wp_unslash( $_POST['oberih_doc_date'] ) ) : '';
	$date = oberih_doc_date_label( $date ) ? $date : '';
	$page = isset( $_POST['oberih_doc_page'] ) ? absint( $_POST['oberih_doc_page'] ) : 0;
	$page = ( $page && 'page' === get_post_type( $page ) ) ? $page : 0;
	foreach ( array(
		'_oberih_doc_file' => $file,
		'_oberih_doc_date' => $date,
		'_oberih_doc_page' => $page,
	) as $key => $value ) {
		if ( $value ) {
			update_post_meta( $post_id, $key, $value );
		} else {
			delete_post_meta( $post_id, $key );
		}
	}
}
add_action( 'save_post_oberih_doc', 'oberih_doc_save' );

/**
 * На сторінці в редакторі: які документи на ній показуються і кнопка «Додати документ».
 *
 * @param WP_Post $post Сторінка.
 */
function oberih_page_docs_box( $post ) {
	$docs = get_posts(
		array(
			'post_type'   => 'oberih_doc',
			'post_status' => array( 'publish', 'draft', 'pending', 'future', 'private' ),
			'numberposts' => -1,
			'meta_key'    => '_oberih_doc_page', // phpcs:ignore WordPress.DB.SlowDBQuery
			'meta_value'  => (int) $post->ID, // phpcs:ignore WordPress.DB.SlowDBQuery
		)
	);
	if ( $docs ) {
		echo '<ul>';
		foreach ( $docs as $doc ) {
			$state = 'publish' === $doc->post_status ? '' : ' — ' . esc_html( get_post_status_object( $doc->post_status )->label );
			echo '<li><a href="' . esc_url( get_edit_post_link( $doc ) ) . '">' . esc_html( get_the_title( $doc ) ) . '</a>' . $state . '</li>'; // phpcs:ignore WordPress.Security.EscapeOutput -- екрановано вище.
		}
		echo '</ul>';
	} else {
		echo '<p>' . esc_html__( 'Документів поки немає.', 'oberih' ) . '</p>';
	}
	echo '<p><a class="button" href="' . esc_url( admin_url( 'post-new.php?post_type=oberih_doc&oberih_page=' . (int) $post->ID ) ) . '">' . esc_html__( 'Додати документ на цю сторінку', 'oberih' ) . '</a></p>';
}

/**
 * Вибір файлу з медіатеки в редакторі документа.
 *
 * @param string $hook Сторінка адмінки.
 */
function oberih_doc_admin_assets( $hook ) {
	if ( ! in_array( $hook, array( 'post.php', 'post-new.php' ), true ) || 'oberih_doc' !== get_current_screen()->post_type ) {
		return;
	}
	wp_enqueue_media();
	wp_enqueue_script( 'oberih-admin-doc', oberih_asset( 'js/admin-doc.js' ), array( 'jquery' ), oberih_asset_ver( 'js/admin-doc.js' ), true );
	wp_localize_script(
		'oberih-admin-doc',
		'oberihDoc',
		array(
			'title'  => __( 'Файл документа', 'oberih' ),
			'button' => __( 'Вибрати цей файл', 'oberih' ),
			'none'   => __( 'Файл не вибрано.', 'oberih' ),
		)
	);
}
add_action( 'admin_enqueue_scripts', 'oberih_doc_admin_assets' );

/**
 * Колонки в списку документів.
 *
 * @param array $cols Колонки.
 * @return array
 */
function oberih_doc_columns( $cols ) {
	$date = $cols['date'];
	unset( $cols['date'] );
	$cols['oberih_page'] = __( 'Сторінка', 'oberih' );
	$cols['oberih_appr'] = __( 'Затверджено', 'oberih' );
	$cols['oberih_file'] = __( 'Файл', 'oberih' );
	$cols['date']        = $date;
	return $cols;
}
add_filter( 'manage_oberih_doc_posts_columns', 'oberih_doc_columns' );

/**
 * Значення колонок у списку документів.
 *
 * @param string $col     Колонка.
 * @param int    $post_id ID документа.
 */
function oberih_doc_column( $col, $post_id ) {
	$f = oberih_doc_fields( $post_id );
	if ( 'oberih_page' === $col ) {
		echo $f['page'] ? '<a href="' . esc_url( get_permalink( $f['page'] ) ) . '">' . esc_html( get_the_title( $f['page'] ) ) . '</a>' : '<strong>' . esc_html__( 'не вибрано', 'oberih' ) . '</strong>';
	} elseif ( 'oberih_appr' === $col ) {
		echo esc_html( $f['date'] ? oberih_doc_date_label( $f['date'] ) : '—' );
	} elseif ( 'oberih_file' === $col ) {
		$path = $f['file'] ? get_attached_file( $f['file'] ) : '';
		echo $path ? esc_html( strtoupper( pathinfo( $path, PATHINFO_EXTENSION ) ) . ' · ' . oberih_file_size( (int) @filesize( $path ) ) ) : '<strong>' . esc_html__( 'немає файлу', 'oberih' ) . '</strong>'; // phpcs:ignore WordPress.PHP.NoSilencedErrors
	}
}
add_action( 'manage_oberih_doc_posts_custom_column', 'oberih_doc_column', 10, 2 );
