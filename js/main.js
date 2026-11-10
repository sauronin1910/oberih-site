(function(){
  var root=document.documentElement;
  // localStorage може бути недоступним (приватний режим) — тоді налаштування просто не запам'ятовуються
  // Початкові значення вже прочитав js/prefs.js (зі сховища або з адреси ?prefs=…)
  var P=window.OBERIH_PREFS||{};
  function save(k,v){
    if(load(k)!==v){
      P[k]=v;P.ts=Date.now().toString(36);
      try{localStorage.setItem('oberih-'+k,v);localStorage.setItem('oberih-ts',P.ts)}catch{/* ігноруємо */}
    }
    carryPrefs();
  }
  function load(k){
    try{var v=localStorage.getItem('oberih-'+k);if(v!==null)return v}catch{/* сховище недоступне */}
    return P[k]===undefined?null:P[k];
  }
  // Перегляд з диска (file://) або без сховища: налаштування передаються між сторінками в адресі
  function prefsToken(){
    var t=[],sc=load('scale'),ts=load('ts');
    if(load('scheme')==='dark')t.push('dark');
    if(sc==='1.15')t.push('a115');else if(sc==='1.3')t.push('a130');
    if(load('data-contrast')==='high')t.push('hc');
    if(load('data-links')==='underline')t.push('ul');
    if(ts)t.push('t'+ts);
    return t.join('.');
  }
  function withPrefs(u,tok){
    var h='',i=u.indexOf('#');
    if(i>-1){h=u.slice(i);u=u.slice(0,i)}
    u=u.replace(/([?&])prefs=[^&]*(&|$)/,'$1').replace(/[?&]$/,'');
    return u+(tok?(u.indexOf('?')>-1?'&':'?')+'prefs='+tok:'')+h;
  }
  function carryPrefs(){
    if(!window.OBERIH_CARRY)return;
    var tok=prefsToken();
    [].forEach.call(document.querySelectorAll('a[href]'),function(a){
      var u=a.getAttribute('href');
      if(/^(#|[a-z][a-z0-9+.-]*:|\/)/i.test(u)||!/\.html?([?#]|$)/i.test(u))return;
      a.setAttribute('href',withPrefs(u,tok));
    });
    try{history.replaceState(history.state,'',withPrefs(location.href,tok))}catch{/* у вбудованому перегляді адресу змінити не можна */}
  }
  var reduceMotion=!!(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  // Світла / темна тема (за замовчуванням світла)
  var themeBtns=[].slice.call(document.querySelectorAll('.theme-toggle'));
  function paintTheme(dark){
    if(dark)root.setAttribute('data-scheme','dark');else root.removeAttribute('data-scheme');
    themeBtns.forEach(function(b){b.querySelector('.tt-label').textContent=dark?'Світла тема':'Темна тема'});
  }
  function setTheme(dark,btn){
    save('scheme',dark?'dark':'light');
    if(reduceMotion){paintTheme(dark);return}
    if(document.startViewTransition&&btn&&btn.offsetParent){
      var r=btn.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2;
      var R=Math.hypot(Math.max(x,innerWidth-x),Math.max(y,innerHeight-y));
      var vt=document.startViewTransition(function(){paintTheme(dark)});
      vt.ready.then(function(){
        root.animate({clipPath:['circle(0px at '+x+'px '+y+'px)','circle('+R+'px at '+x+'px '+y+'px)']},
          {duration:600,easing:'cubic-bezier(.4,0,.2,1)',pseudoElement:'::view-transition-new(root)'});
      }).catch(function(){});
    }else{
      root.classList.add('theme-fading');paintTheme(dark);
      setTimeout(function(){root.classList.remove('theme-fading')},450);
    }
  }
  themeBtns.forEach(function(b){b.addEventListener('click',function(){setTheme(root.getAttribute('data-scheme')!=='dark',b)})});
  paintTheme(load('scheme')==='dark');

  // Доступність: розмір шрифту
  var scaleBtns=[].slice.call(document.querySelectorAll('[data-scale]'));
  // A — як задумано; A+ / A++ — збільшують лише звичайний і дрібний текст (заголовки, кнопки й меню не змінюються)
  var TEXT_MIN={'1':['0px','0px'],'1.15':['1.125rem','1rem'],'1.3':['1.25rem','1.0625rem']};
  function setScale(s){
    var m=TEXT_MIN[s]||TEXT_MIN['1'];
    root.style.setProperty('--min-text',m[0]);root.style.setProperty('--min-small',m[1]);
    scaleBtns.forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.scale===String(s)))});
    save('scale',s);
    window.dispatchEvent(new Event('oberih:scale'));
  }
  scaleBtns.forEach(function(b){b.addEventListener('click',function(){setScale(b.dataset.scale)})});

  // Контраст і підкреслення посилань
  function toggle(btn,attr,val){
    var on=btn.getAttribute('aria-pressed')!=='true';
    btn.setAttribute('aria-pressed',String(on));
    if(on)root.setAttribute(attr,val);else root.removeAttribute(attr);
    save(attr,on?val:'');
  }
  var bc=document.getElementById('btn-contrast'),bl=document.getElementById('btn-links');
  bc.addEventListener('click',function(){toggle(bc,'data-contrast','high')});
  bl.addEventListener('click',function(){toggle(bl,'data-links','underline')});
  document.getElementById('btn-reset').addEventListener('click',function(){
    setScale('1');
    [[bc,'data-contrast'],[bl,'data-links']].forEach(function(p){p[0].setAttribute('aria-pressed','false');root.removeAttribute(p[1]);save(p[1],'')});
  });
  var s=load('scale');if(s)setScale(s);
  if(load('data-contrast')==='high'){bc.click()}
  if(load('data-links')==='underline'){bl.click()}

  // Інша вкладка змінила налаштування або сторінку повернуто кнопкою «Назад» — оновити без перезавантаження
  function applyPrefs(){
    var dark=load('scheme')==='dark';
    if(dark!==(root.getAttribute('data-scheme')==='dark'))paintTheme(dark);
    var sc=load('scale')||'1';
    if(!scaleBtns.some(function(b){return b.dataset.scale===sc&&b.getAttribute('aria-pressed')==='true'}))setScale(sc);
    [[bc,'data-contrast','high'],[bl,'data-links','underline']].forEach(function(p){
      if((load(p[1])===p[2])!==(p[0].getAttribute('aria-pressed')==='true'))toggle(p[0],p[1],p[2]);
    });
    carryPrefs();
  }
  window.addEventListener('storage',function(e){if(!e.key||e.key.indexOf('oberih-')===0)applyPrefs()});
  window.addEventListener('pageshow',function(e){if(e.persisted)applyPrefs()});
  carryPrefs();

  // Меню
  var nav=document.getElementById('main-nav');
  var burger=document.querySelector('.burger');
  var closeBtn=nav.querySelector('.drawer-close');
  var backdrop=document.querySelector('.nav-backdrop');
  var mq=window.matchMedia('(max-width:74.99em)');
  var outside=[].slice.call(document.querySelectorAll('.skip,.a11ybar,.site-header,main,.site-footer'));
  [].forEach.call(nav.querySelectorAll('.drawer-head,.menu > li,.drawer-foot'),function(el,i){el.style.setProperty('--i',i)});
  [].forEach.call(nav.querySelectorAll('.submenu'),function(ul){[].forEach.call(ul.children,function(li,j){li.style.setProperty('--j',j)})});
  var bdTimer;
  function setDrawer(open){
    if(open===nav.classList.contains('open'))return;
    nav.classList.toggle('open',open);
    burger.setAttribute('aria-expanded',String(open));
    burger.setAttribute('aria-label',open?'Закрити меню':'Відкрити меню');
    root.classList.toggle('nav-locked',open);
    outside.forEach(function(el){if(open)el.setAttribute('inert','');else el.removeAttribute('inert')});
    clearTimeout(bdTimer);
    if(open){
      backdrop.hidden=false;void backdrop.offsetWidth;backdrop.classList.add('show');
      setTimeout(function(){closeBtn.focus()},80);
    }else{
      backdrop.classList.remove('show');
      bdTimer=setTimeout(function(){backdrop.hidden=true},reduceMotion?0:400);
    }
  }
  burger.addEventListener('click',function(){setDrawer(true)});
  closeBtn.addEventListener('click',function(){setDrawer(false);burger.focus()});
  backdrop.addEventListener('click',function(){setDrawer(false)});
  nav.addEventListener('click',function(e){if(mq.matches&&e.target.closest('a'))setDrawer(false)});

  // Підменю: на комп'ютері — випадний список, на телефоні — акордеон з анімацією висоти
  var parents=[].slice.call(nav.querySelectorAll('.menu > li > button'));
  function animateSub(ul,open){
    ul.classList.toggle('is-open',open);
    if(!mq.matches){ul.style.height='';return}
    if(reduceMotion){ul.style.height=open?'auto':'';return}
    var start=ul.getBoundingClientRect().height;
    var end=open?ul.scrollHeight:0;
    ul.style.height=start+'px';void ul.offsetHeight;ul.style.height=end+'px';
    ul.addEventListener('transitionend',function te(e){
      if(e.propertyName!=='height')return;
      ul.removeEventListener('transitionend',te);
      if(ul.classList.contains('is-open'))ul.style.height='auto';
    });
  }
  function setSub(b,open){b.setAttribute('aria-expanded',String(open));animateSub(b.nextElementSibling,open)}
  function closeAll(except){parents.forEach(function(b){if(b!==except&&b.getAttribute('aria-expanded')==='true')setSub(b,false)})}
  parents.forEach(function(b){
    b.addEventListener('click',function(e){
      e.stopPropagation();
      var open;
      if(b.dataset.hover){delete b.dataset.hover;open=true}   // уже відкрито наведенням — клік не закриває
      else open=b.getAttribute('aria-expanded')!=='true';
      closeAll(b);setSub(b,open);
    });
  });
  // Наведення на комп'ютері: завжди відкритий лише один список
  var canHover=window.matchMedia('(hover:hover)');
  parents.forEach(function(b){
    var li=b.parentNode;
    li.addEventListener('mouseenter',function(){
      if(mq.matches||!canHover.matches)return;
      clearTimeout(li._t);
      closeAll(b);
      if(b.getAttribute('aria-expanded')!=='true'){setSub(b,true);b.dataset.hover='1'}
    });
    li.addEventListener('mouseleave',function(){
      if(mq.matches||!canHover.matches)return;
      li._t=setTimeout(function(){if(b.getAttribute('aria-expanded')==='true')setSub(b,false);delete b.dataset.hover},200);
    });
    // Клавіатура: фокус пішов за межі пункту (Tab далі) — підменю закриваємо
    li.addEventListener('focusout',function(e){
      if(mq.matches||(e.relatedTarget&&li.contains(e.relatedTarget)))return;
      if(e.relatedTarget&&b.getAttribute('aria-expanded')==='true'){setSub(b,false);delete b.dataset.hover}
    });
  });
  document.addEventListener('click',function(e){if(!mq.matches&&!nav.contains(e.target))closeAll()});
  document.addEventListener('keydown',function(e){
    if(e.key!=='Escape')return;
    if(nav.classList.contains('open')){setDrawer(false);burger.focus();return}
    var o=parents.filter(function(b){return b.getAttribute('aria-expanded')==='true'})[0];
    closeAll();if(o)o.focus();
  });
  function onMq(){setDrawer(false);closeAll();[].forEach.call(nav.querySelectorAll('.submenu'),function(ul){ul.style.height=''})}
  if(mq.addEventListener)mq.addEventListener('change',onMq);else if(mq.addListener)mq.addListener(onMq);

  // Меню в один ряд: якщо пункти не вміщаються, трохи стискаємо їх
  var menuEl=document.getElementById('menu'),fitTimer;
  function fitNav(){
    nav.classList.remove('nav-tight');
    if(mq.matches)return;
    var first=menuEl.firstElementChild;
    if(first&&menuEl.offsetHeight>first.offsetHeight*1.5)nav.classList.add('nav-tight');
  }
  function fitLater(){clearTimeout(fitTimer);fitTimer=setTimeout(fitNav,80)}
  window.addEventListener('resize',fitLater);
  window.addEventListener('oberih:scale',fitNav);
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fitNav);
  fitNav();

  // Слайдер новин
  (function(){
    var track=document.getElementById('news-track');if(!track)return;
    var slider=document.getElementById('news-slider');
    var items=[].slice.call(track.children);
    var dotsBox=slider.querySelector('.slider-dots');
    var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var paused=!!reduce,hover=false;   // автопрокрутка зупиняється назавжди після ручного гортання
    items.forEach(function(li,i){li.setAttribute('aria-roledescription','слайд');li.setAttribute('aria-label',(i+1)+' з '+items.length)});
    function step(){return items.length>1?items[1].offsetLeft-items[0].offsetLeft:track.clientWidth}
    function perView(){return Math.max(1,Math.round((track.clientWidth+1)/step()))}
    function maxIndex(){return Math.max(0,items.length-perView())}
    function current(){return Math.min(maxIndex(),Math.round(track.scrollLeft/step()))}
    function go(i){var m=maxIndex();if(i>m)i=0;if(i<0)i=m;track.scrollTo({left:i*step(),behavior:reduce?'auto':'smooth'})}
    function update(){var c=current();[].forEach.call(dotsBox.children,function(d,i){d.setAttribute('aria-current',String(i===c))})}
    function buildDots(){
      dotsBox.innerHTML='';
      for(var i=0;i<=maxIndex();i++){(function(idx){
        var b=document.createElement('button');b.type='button';b.setAttribute('aria-label','Слайд '+(idx+1));
        b.addEventListener('click',function(){paused=true;go(idx)});dotsBox.appendChild(b);
      })(i)}
      update();
    }
    [].forEach.call(document.querySelectorAll('.slider-btn'),function(b){
      b.addEventListener('click',function(){paused=true;go(current()+Number(b.dataset.dir))});
    });
    track.addEventListener('scroll',function(){window.requestAnimationFrame(update)},{passive:true});
    track.addEventListener('keydown',function(e){
      if(e.key==='ArrowRight'){e.preventDefault();paused=true;go(current()+1)}
      if(e.key==='ArrowLeft'){e.preventDefault();paused=true;go(current()-1)}
    });
    track.addEventListener('pointerdown',function(){paused=true});
    track.addEventListener('wheel',function(e){if(Math.abs(e.deltaX)>Math.abs(e.deltaY))paused=true},{passive:true});
    window.addEventListener('resize',buildDots);
    slider.addEventListener('mouseenter',function(){hover=true});
    slider.addEventListener('mouseleave',function(){hover=false});
    slider.addEventListener('focusin',function(){hover=true});
    slider.addEventListener('focusout',function(e){if(!slider.contains(e.relatedTarget))hover=false});
    setInterval(function(){if(!paused&&!hover&&!document.hidden)go(current()+1)},6000);
    buildDots();
  })();

  // Тінь меню під час прокрутки
  (function(){
    var navBar=document.getElementById('main-nav'),hdr=document.querySelector('.site-header');
    function upd(){var scrolled=window.scrollY>160;navBar.classList.toggle('scrolled',scrolled);hdr.classList.toggle('scrolled',scrolled)}
    window.addEventListener('scroll',upd,{passive:true});upd();
  })();

  // Поява блоків під час прокрутки. Блоки, які вже на екрані, не чіпаємо,
  // тож без скрипта або зі «зменшеним рухом» сторінка просто показана повністю.
  (function(){
    if(!('IntersectionObserver' in window))return;
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches)return;
    var groups=[
      ['.sec-head',0],['.about-text',0],['.directions > li',90],['.slider',0],
      ['.docs-band .wrap > div:first-child',0],['.doc-list > li',50],
      ['.safety > div:first-child',0],['.hotlines > li',80],['.sponsors > li',60],
      ['.welcome-text',0],['.welcome-art',0],['.contact > *',140],['.site-footer .cols > *',70]
    ];
    var io=new IntersectionObserver(function(es){
      es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('is-in');io.unobserve(e.target)}});
    },{rootMargin:'0px 0px -8% 0px',threshold:.12});
    var vh=window.innerHeight;
    groups.forEach(function(g){
      [].forEach.call(document.querySelectorAll(g[0]),function(el,i){
        if(el.getBoundingClientRect().top<vh)return;
        el.style.setProperty('--d',(i*g[1])+'ms');io.observe(el);
      });
    });
  })();

  // Форма (у макеті нікуди не надсилає)
  var form=document.getElementById('ask-form'),st=document.getElementById('form-status');
  if(form)form.addEventListener('submit',function(e){
    e.preventDefault();
    // поля з помилкою позначаємо для екранних читачів і ставимо фокус на перше
    var bad=[].filter.call(form.elements,function(f){
      if(!f.willValidate)return false;
      var inv=!f.checkValidity();
      if(inv)f.setAttribute('aria-invalid','true');else f.removeAttribute('aria-invalid');
      return inv;
    });
    if(bad.length){st.hidden=false;st.textContent='Заповніть усі поля і поставте позначку згоди.';bad[0].focus();return}
    st.hidden=false;st.textContent='Це макет. На готовому сайті запитання надійде на пошту НРЦ «Оберіг».';
    form.reset();
  });
})();
