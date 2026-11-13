<?php
/**
 * Головна сторінка. Згенеровано tools/build_wp_front.py з index.html — вручну не правити.
 *
 * @package oberih
 */

get_header();
?>
  <!-- Героїчний блок -->
  <section class="hero section-intro" id="intro" aria-labelledby="hero-title">
    <div class="wrap">
      <div>
        <p class="eyebrow">Івано-Франківськ · вул. Гната Хоткевича, 52-А</p>
        <h1 id="hero-title">Навчання і реабілітація <em>в одному місці</em></h1>
        <p class="lead">НРЦ «Оберіг» навчає дітей з особливими освітніми потребами, зокрема з порушеннями опорно-рухового апарату. Уроки поєднуємо з фізичною терапією, корекційними заняттями та психологічною підтримкою.</p>
        <div class="actions">
          <a class="btn btn-primary" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>">Як вступити до НРЦ «Оберіг»</a>
          <a class="btn btn-ghost" href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/dostupnist-dlia-osib-z-oop' ) ); ?>">Умови доступності</a>
        </div>
        <ul class="hero-facts">
          <li class="c-sky">Комунальний заклад</li>
          <li class="c-teal">Навчання безоплатне</li>
          <li class="c-coral">Безбар'єрне середовище</li>
        </ul>
      </div>
      <div class="art" aria-hidden="true">
        <span class="ball b1"></span><span class="ball b2"></span><span class="ball b3"></span><span class="ball b4"></span><span class="ball b5"></span>
        <div class="big"><img src="<?php echo esc_url( oberih_asset( 'img/logo.jpg' ) ); ?>" alt="" width="512" height="512"></div>
      </div>
    </div>
  </section>

  <!-- Швидкі посилання -->
  <nav class="tiles section-quicklinks" aria-label="Швидкі посилання">
    <div class="wrap">
      <ul>
        <li><a class="tile c-coral" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/><path d="M10 16l4-4-4-4"/><path d="M14 12H4"/></svg></span><strong>Вступ до НРЦ «Оберіг»</strong><span>Правила прийому і документи</span></a></li>
        <li><a class="tile c-sky" href="<?php echo esc_url( oberih_page_url( 'osvitnia-diialnist/rozklad-zaniat' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg></span><strong>Розклад</strong><span>Уроки та реабілітаційні заняття</span></a></li>
        <li><a class="tile c-teal" href="<?php echo esc_url( oberih_page_url( 'reabilitatsiine-viddilennia' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="5" r="2"/><path d="M5 8c2 1.5 4.5 2 7 2s5-.5 7-2"/><path d="M12 10v5l-3 6M12 15l3 6"/></svg></span><strong>Реабілітація</strong><span>Фізична терапія, логопед, корекція</span></a></li>
        <li><a class="tile c-orange" href="<?php echo esc_url( oberih_page_url( 'reabilitatsiine-viddilennia/psykholohichna-sluzhba' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/><path d="M12 13s-3-1.8-3-3.6a1.6 1.6 0 0 1 3-.8 1.6 1.6 0 0 1 3 .8c0 1.8-3 3.6-3 3.6z"/></svg></span><strong>Психологічна служба</strong><span>Підтримка дітей і батьків</span></a></li>
        <li><a class="tile c-green" href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/></svg></span><strong>Прозорість</strong><span>Кошторис, звіти, документи</span></a></li>
        <li><a class="tile c-amber" href="<?php echo esc_url( oberih_page_url( 'bezpeka-ta-zakhyst' ) ); ?>"><span class="ic"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></span><strong>Безпека та захист</strong><span>Булінг, безпека, повітряна тривога</span></a></li>
      </ul>
    </div>
  </nav>

  <!-- Про НРЦ «Оберіг» -->
  <section class="block section-about" id="about" aria-labelledby="about-title">
    <div class="wrap">
      <div class="about">
        <div class="about-text">
          <p class="eyebrow c-teal">Про НРЦ «Оберіг»</p>
          <h2 id="about-title">Кожна дитина вчиться у своєму темпі</h2>
          <p>НРЦ «Оберіг» — комунальний заклад Івано-Франківської міської ради для дітей з особливими освітніми потребами. Ми поєднуємо загальну середню освіту з комплексною реабілітацією, щоб навчання й відновлення йшли поруч, а не конкурували за час дитини.</p>
          <p>Над кожною дитиною працює команда: вчителі, асистенти, фізичні терапевти, логопеди, психологи. Разом із батьками вони складають індивідуальну програму розвитку і переглядають її впродовж року.</p>
          <div class="quote">
            Тексти на цій сторінці тимчасові. Їх замінить опис НРЦ «Оберіг» від адміністрації.
            <small>Примітка до макета</small>
          </div>
        </div>
        <ul class="directions">
          <li class="card card-wide c-amber" id="preschool">
            <svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/></svg>
            <h3><a href="<?php echo esc_url( oberih_page_url( 'doshkilne-viddilennia' ) ); ?>">Дошкільне відділення</a></h3>
            <p>Групи для дітей дошкільного віку: розвиток, корекційні заняття і реабілітація з раннього віку, підготовка до школи.</p>
          </li>
          <li class="card c-sky">
            <svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1z"/><path d="M12 6v14"/></svg>
            <h3><a href="<?php echo esc_url( oberih_page_url( 'osvitnia-diialnist' ) ); ?>">Навчання</a></h3>
            <p>Загальна середня освіта за освітніми програмами НУШ, адаптованими до потреб кожного учня.</p>
          </li>
          <li class="card c-teal">
            <svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="5" r="2"/><path d="M5 8c2 1.5 4.5 2 7 2s5-.5 7-2"/><path d="M12 10v5l-3 6M12 15l3 6"/></svg>
            <h3><a href="<?php echo esc_url( oberih_page_url( 'reabilitatsiine-viddilennia' ) ); ?>">Фізична реабілітація</a></h3>
            <p>Фізична терапія та ерготерапія: рух, координація, навички самообслуговування.</p>
          </li>
          <li class="card c-orange">
            <svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="3.5"/><rect x="4" y="13" width="7" height="7" rx="3.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/></svg>
            <h3><a href="<?php echo esc_url( oberih_page_url( 'reabilitatsiine-viddilennia/korektsiino-rozvytkova-robota' ) ); ?>">Корекційна допомога</a></h3>
            <p>Логопедичні та корекційно-розвиткові заняття індивідуально і в малих групах.</p>
          </li>
          <li class="card c-coral">
            <svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/><path d="M12 13s-3-1.8-3-3.6a1.6 1.6 0 0 1 3-.8 1.6 1.6 0 0 1 3 .8c0 1.8-3 3.6-3 3.6z"/></svg>
            <h3><a href="<?php echo esc_url( oberih_page_url( 'reabilitatsiine-viddilennia/psykholohichna-sluzhba' ) ); ?>">Психологічна підтримка</a></h3>
            <p>Консультації для дітей і батьків, адаптація до навчання, розвиток соціальних навичок.</p>
          </li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Новини -->
  <section class="block section-news" id="news" aria-labelledby="news-title">
    <div class="wrap">
      <div class="sec-head">
        <div>
          <p class="eyebrow c-coral">Життя НРЦ «Оберіг»</p>
          <h2 id="news-title">Новини</h2>
        </div>
        <div class="sec-actions">
          <a class="more" href="<?php echo esc_url( oberih_page_url( 'novyny' ) ); ?>">Усі новини <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
          <div class="slider-arrows">
            <button type="button" class="slider-btn" data-dir="-1" aria-controls="news-track" aria-label="Попередні новини"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg></button>
            <button type="button" class="slider-btn" data-dir="1" aria-controls="news-track" aria-label="Наступні новини"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg></button>
          </div>
        </div>
      </div>
      <section class="slider" id="news-slider" aria-roledescription="карусель" aria-label="Стрічка новин">
      <ul class="news" id="news-track" tabindex="0">
<?php oberih_front_news(); ?>
      </ul>
      <div class="slider-foot">
        <div class="slider-dots" role="group" aria-label="Вибір слайда"></div>
      </div>
      </section>
    </div>
  </section>

  <!-- Документи -->
  <section class="docs-band section-documents" id="documents" aria-labelledby="docs-title">
    <div class="wrap">
      <div>
        <p class="eyebrow c-sky">Прозорість та відкритість</p>
        <h2 id="docs-title">Документи НРЦ «Оберіг»</h2>
        <p class="note">Оприлюднюємо документи відповідно до статті 30 Закону України «Про освіту» не пізніше ніж через 10 робочих днів після затвердження.</p>
        <a class="btn btn-ghost" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka' ) ); ?>">Усі документи</a>
      </div>
      <ul class="doc-list">
        <li><a href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/statut' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Статут<small>Офіційна сторінка</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/litsenziia' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Ліцензія<small>Офіційна сторінка</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/finansova-zvitnist' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Фінансова звітність<small>Прозорість та відкритість</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/richnyi-zvit' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Річний звіт<small>Прозорість та відкритість</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Правила прийому<small>Офіційна сторінка</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/dostupnist-dlia-osib-z-oop' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Доступність для осіб з ООП<small>Прозорість та відкритість</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'bezpeka-ta-zakhyst/buling' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Протидія булінгу<small>Безпека та захист</small></span><em class="pdf">PDF</em></a></li>
        <li><a href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/vakansii' ) ); ?>"><svg class="icon ic" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg><span>Вакансії<small>Прозорість та відкритість</small></span><em class="pdf">PDF</em></a></li>
      </ul>
    </div>
  </section>

  <!-- Безпека та захист -->
  <section class="block section-safety" id="safety" aria-labelledby="safety-title">
    <div class="wrap">
      <div class="safety">
        <div>
          <p class="eyebrow">Безпека та захист</p>
          <h2 id="safety-title">Якщо дитину кривдять, є кому допомогти</h2>
          <p>Повідомити про булінг можна класному керівнику, психологу або директору НРЦ «Оберіг». Заяви розглядаємо конфіденційно.</p>
          <div class="links">
            <a href="<?php echo esc_url( oberih_page_url( 'bezpeka-ta-zakhyst/buling' ) ); ?>">Протидія булінгу</a>
            <a href="<?php echo esc_url( oberih_page_url( 'bezpeka-ta-zakhyst/povitriana-tryvoha' ) ); ?>">Увага! Повітряна тривога!</a>
            <a href="<?php echo esc_url( oberih_page_url( 'bezpeka-ta-zakhyst/bezpeka-v-interneti' ) ); ?>">Безпека в інтернеті</a>
          </div>
        </div>
        <ul class="hotlines">
          <li><b><a class="tel" href="tel:116111">116 111</a></b><span>Національна дитяча гаряча лінія, безкоштовно</span></li>
          <li><b><a class="tel" href="tel:1547">1547</a></b><span>Урядова лінія: насильство, булінг, торгівля людьми</span></li>
          <li><b><a class="tel" href="tel:0800501720">0 800 50 17 20</a></b><span>Уповноважений Верховної Ради з прав людини</span></li>
          <li><b><a class="tel" href="tel:102">102</a></b><span>Національна поліція</span></li>
        </ul>
      </div>
    </div>
  </section>

  <!-- Запрошення -->
  <section class="block section-welcome" id="welcome" aria-labelledby="welcome-title">
    <div class="wrap">
      <div class="welcome">
        <div class="welcome-text">
          <p class="eyebrow c-orange">Запрошуємо</p>
          <h2 id="welcome-title">У НРЦ «Оберіг» кожна дитина серед друзів</h2>
          <p>Діти вчаться, граються і займаються разом, а фахівці дбають, щоб кожному було комфортно. Розкажемо, як вступити до НРЦ «Оберіг», і відповімо на ваші запитання.</p>
          <div class="actions">
            <a class="btn btn-primary" href="<?php echo esc_url( oberih_page_url( 'ofitsiina-storinka/pravyla-pryiomu' ) ); ?>">Правила прийому</a>
            <a class="btn btn-ghost" href="#contacts">Поставити запитання</a>
          </div>
        </div>
        <img class="welcome-art" src="<?php echo esc_url( oberih_asset( 'img/kids.jpg' ) ); ?>" alt="" width="1400" height="499" loading="lazy">
      </div>
    </div>
  </section>

  <!-- Спонсори -->
  <section class="block section-sponsors" id="sponsors" aria-labelledby="sponsors-title">
    <div class="wrap">
      <div class="sec-head">
        <div>
          <p class="eyebrow c-green">Разом із нами</p>
          <h2 id="sponsors-title">Наші спонсори</h2>
          <p>Дякуємо всім, хто підтримує дітей НРЦ «Оберіг». Звіти про отриману допомогу оприлюднюємо в розділі «Прозорість та відкритість».</p>
        </div>
        <a class="more" href="<?php echo esc_url( oberih_page_url( 'prozorist-ta-vidkrytist/finansova-zvitnist' ) ); ?>">Звіт про благодійну допомогу <svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      </div>
      <ul class="sponsors">
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
        <li class="sponsor"><span class="sponsor-ph"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/></svg>Логотип спонсора</span></li>
      </ul>
      <p class="sponsors-note">Логотипи — приклад. Справжні з'являться після погодження зі спонсорами.</p>
    </div>
  </section>

  <!-- Контакти -->
  <section class="block section-contacts" id="contacts" aria-labelledby="contacts-title">
    <div class="wrap">
      <?php get_template_part( 'template-parts/contact-block', null, array( 'title' => 'Контакти' ) ); ?>
    </div>
  </section>
<?php
get_footer();
