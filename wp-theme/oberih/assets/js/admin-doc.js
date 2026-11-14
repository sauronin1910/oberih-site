/* Адмінка, «Документ»: вибір файлу з медіатеки (або завантаження нового). */
/* global wp, jQuery */
(function($){
  'use strict';
  var frame,input=$('#oberih-doc-file'),name=$('#oberih-doc-file-name'),clear=$('#oberih-doc-clear'),L=window.oberihDoc||{};
  $('#oberih-doc-pick').on('click',function(e){
    e.preventDefault();
    if(!frame){
      frame=wp.media({title:L.title,button:{text:L.button},multiple:false});
      frame.on('select',function(){
        var a=frame.state().get('selection').first().toJSON();
        input.val(a.id);name.text(a.filename||a.title);clear.prop('hidden',false);
      });
    }
    frame.open();
  });
  clear.on('click',function(e){
    e.preventDefault();input.val('');name.text(L.none);clear.prop('hidden',true);
  });
})(jQuery);
