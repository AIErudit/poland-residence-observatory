'use strict';
function updatePageLanguage(){
 document.querySelectorAll('[data-locale]').forEach(el=>el.hidden=el.dataset.locale!==RO.language);
 const title=document.querySelector('[data-locale="'+RO.language+'"] h1');if(title)document.title=title.textContent+' · Residence Observatory';
}
window.addEventListener('languagechange',updatePageLanguage);
document.addEventListener('DOMContentLoaded',()=>{
 updatePageLanguage();
 document.querySelectorAll('[data-copy-citation]').forEach(b=>b.addEventListener('click',async()=>{
  const block=document.querySelector('[data-locale="'+RO.language+'"]'),text=block.querySelector('.citation').textContent;
  try{await navigator.clipboard.writeText(text);block.querySelector('[role=status]').textContent=RO.t('Skopiowano ze źródłem i zastrzeżeniem.','Скапіявана з крыніцай і агаворкай.','Copied with source and limitation.');}catch{window.prompt(RO.t('Skopiuj:','Скапіруйце:','Copy:'),text);}
 }));
});
