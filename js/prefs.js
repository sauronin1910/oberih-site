/* Тема й налаштування доступності: застосовуються ще до показу сторінки, щоб вона не блимала білим.
   Зберігаються в localStorage. Коли сайт відкрито з диска (file://) або сховище недоступне,
   налаштування ще й передаються між сторінками в адресі (?prefs=…) — це робить js/main.js. */
(function(){
  var root=document.documentElement,K=['scheme','scale','data-contrast','data-links','ts'],P={},ok=true;
  try{K.forEach(function(k){P[k]=localStorage.getItem('oberih-'+k)})}catch{ok=false}
  var m=/[?&]prefs=([^&#]*)/.exec(location.search),t=m?decodeURIComponent(m[1]).split('.'):[];
  var ts=t.filter(function(x){return x.charAt(0)==='t'})[0];
  ts=ts?ts.slice(1):'';
  // з адреси беремо лише новіші налаштування, ніж у сховищі (напр., після «Назад» діє останній вибір)
  if(m&&(!ok||parseInt(ts||'0',36)>parseInt(P.ts||'0',36))){
    P.ts=ts;
    P.scheme=t.indexOf('dark')>-1?'dark':'light';
    P.scale=t.indexOf('a130')>-1?'1.3':(t.indexOf('a115')>-1?'1.15':'1');
    P['data-contrast']=t.indexOf('hc')>-1?'high':'';
    P['data-links']=t.indexOf('ul')>-1?'underline':'';
    if(ok)try{K.forEach(function(k){localStorage.setItem('oberih-'+k,P[k])})}catch{/* сховище переповнене — працюємо з адреси */}
  }
  window.OBERIH_PREFS=P;
  window.OBERIH_CARRY=location.protocol==='file:'||!ok;
  if(P.scheme==='dark')root.setAttribute('data-scheme','dark');
  if(P['data-contrast']==='high')root.setAttribute('data-contrast','high');
  if(P['data-links']==='underline')root.setAttribute('data-links','underline');
  // ті самі значення, що й TEXT_MIN у js/main.js
  var T={'1.15':['1.125rem','1rem'],'1.3':['1.25rem','1.0625rem']}[P.scale];
  if(T){root.style.setProperty('--min-text',T[0]);root.style.setProperty('--min-small',T[1])}
})();
