/* Форма «Поставити запитання» у WordPress: перевірка полів і надсилання без перезавантаження сторінки.
   Без JavaScript форма надсилається звичайно (сервер повертає на сторінку з повідомленням). */
(function(){
  'use strict';
  var form=document.getElementById('ask-form-wp');
  if(!form||!window.fetch||!window.FormData)return;
  var st=form.querySelector('.form-status'),btn=form.querySelector('button[type="submit"]');
  var MSG_INVALID='Заповніть усі поля і поставте позначку згоди.';
  var MSG_NET='Не вдалося надіслати запитання. Перевірте з’єднання з інтернетом і спробуйте ще раз.';

  function mark(ids){
    [].forEach.call(form.elements,function(f){
      if(!f.willValidate||f.type==='hidden'||f.name==='website')return;
      if(ids.indexOf(f.id)>-1)f.setAttribute('aria-invalid','true');else f.removeAttribute('aria-invalid');
    });
    if(ids.length){var first=document.getElementById(ids[0]);if(first)first.focus()}
  }
  function say(text){st.textContent=text}

  form.addEventListener('submit',function(e){
    e.preventDefault();
    if(form.getAttribute('aria-busy'))return;   // уже надсилаємо — повторне натискання ігноруємо
    // перевірка у браузері — ті самі правила, що й на сервері
    var bad=[].filter.call(form.elements,function(f){
      return f.willValidate&&f.type!=='hidden'&&f.name!=='website'&&!f.checkValidity();
    }).map(function(f){return f.id});
    mark(bad);
    if(bad.length){say(MSG_INVALID);return}

    // aria-disabled замість disabled: фокус лишається на кнопці
    btn.setAttribute('aria-disabled','true');form.setAttribute('aria-busy','true');say('Надсилаємо…');
    // getAttribute: поле name="action" у формі затіняє властивість form.action
    fetch(form.getAttribute('action'),{method:'POST',body:new FormData(form),credentials:'same-origin',headers:{'Accept':'application/json'}})
      .then(function(r){return r.json()})
      .then(function(d){
        say(d.message||MSG_NET);
        mark(d.fields||[]);
        if(d.ok)form.reset();
      })
      .catch(function(){say(MSG_NET)})
      .then(function(){btn.removeAttribute('aria-disabled');form.removeAttribute('aria-busy')});
  });
})();
