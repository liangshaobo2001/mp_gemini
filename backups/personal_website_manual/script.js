(function(){
  const links = document.querySelectorAll('a[href^="#"]');
  links.forEach(a=>a.addEventListener('click',e=>{
    const id = a.getAttribute('href');
    if(id.length>1){
      e.preventDefault();
      document.querySelector(id)?.scrollIntoView({behavior:'smooth'});
    }
  }));
  const toggles = document.querySelectorAll('.excerpt-toggle');
  toggles.forEach(t=>t.addEventListener('click',e=>{
    e.preventDefault();
    const p = t.nextElementSibling;
    const open = p.hasAttribute('hidden') ? false : true;
    if(open){ p.setAttribute('hidden',''); t.setAttribute('aria-expanded','false'); }
    else { p.removeAttribute('hidden'); t.setAttribute('aria-expanded','true'); }
  }));
  const form = document.getElementById('contact-form');
  const note = document.getElementById('form-note');
  form?.addEventListener('submit',e=>{
    e.preventDefault();
    note.hidden = false;
    note.textContent = 'Thanks — message captured locally.';
  });
  const toTop = document.querySelector('[data-test="back-to-top"]');
  const hero = document.getElementById('hero');
  const toggleTop = ()=>{
    const y = window.scrollY || document.documentElement.scrollTop;
    toTop.hidden = y < (hero?.offsetHeight||200)/2;
  };
  window.addEventListener('scroll',toggleTop,{passive:true});
  toTop?.addEventListener('click',e=>{ e.preventDefault(); hero?.scrollIntoView({behavior:'smooth'}); });
  toggleTop();
})();
