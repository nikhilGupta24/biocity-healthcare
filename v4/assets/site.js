const prog=document.getElementById('prog'),nav=document.getElementById('nav'),mbar=document.getElementById('mbar'),docEl=document.documentElement;
let ticking=false;
function onScroll(){const sc=docEl.scrollTop||window.pageYOffset;prog.style.width=(sc/(docEl.scrollHeight-docEl.clientHeight))*100+'%';nav.classList.toggle('stuck',sc>50);mbar.classList.toggle('on',sc>600);ticking=false}
addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(onScroll);ticking=true}},{passive:true});
function toggleTheme(){const d=document.documentElement,n=d.getAttribute('data-theme')==='dark'?'light':'dark';d.setAttribute('data-theme',n);document.getElementById('sunI').style.display=n==='light'?'block':'none';document.getElementById('moonI').style.display=n==='dark'?'block':'none';localStorage.setItem('theme',n)}
(()=>{const s=localStorage.getItem('theme');if(s){document.documentElement.setAttribute('data-theme',s);document.getElementById('sunI').style.display=s==='light'?'block':'none';document.getElementById('moonI').style.display=s==='dark'?'block':'none'}})();
function openModal(){document.getElementById('modal').classList.add('on');document.body.style.overflow='hidden'}
function closeModal(){document.getElementById('modal').classList.remove('on');document.body.style.overflow=''}
document.getElementById('modal').addEventListener('click',e=>{if(e.target===e.currentTarget)closeModal()});
function submitForm(e){e.preventDefault();const b=document.getElementById('mGoBtn');const t=b.textContent;b.textContent='Confirmed! ✓';b.style.background='var(--accentH)';setTimeout(()=>{closeModal();b.textContent=t;b.style.background='';e.target.reset()},2500)}
function togFaq(btn){const it=btn.closest('.faq-item');const w=it.classList.contains('on');document.querySelectorAll('.faq-item').forEach(i=>{i.classList.remove('on');i.querySelector('.faq-a').style.maxHeight=null});if(!w){it.classList.add('on');it.querySelector('.faq-a').style.maxHeight=it.querySelector('.faq-a').scrollHeight+'px'}}
function formatNum(n){if(n>=100000)return(n/100000).toFixed(1).replace(/\.0$/,'')+'L+';if(n>=1000)return n.toLocaleString('en-IN')+'+';return n+'+'}
function animateCounters(){document.querySelectorAll('.ni-v[data-to]').forEach(el=>{const to=+el.dataset.to;if(el.dataset.done)return;el.dataset.done='1';const dur=2200,start=performance.now();function step(now){const p=Math.min((now-start)/dur,1),ease=1-Math.pow(1-p,4);el.textContent=formatNum(Math.floor(ease*to));if(p<1)requestAnimationFrame(step)}requestAnimationFrame(step)})}
const obs=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('v');if(e.target.closest('.nums'))animateCounters()}})},{threshold:.06,rootMargin:'0px 0px -50px 0px'});
document.querySelectorAll('.sr').forEach(el=>obs.observe(el));
document.querySelectorAll('a[href^="#"]').forEach(a=>{a.addEventListener('click',function(e){const id=this.getAttribute('href');if(id==='#')return;e.preventDefault();const t=document.querySelector(id);if(t)t.scrollIntoView({behavior:'smooth',block:'start'})})});
(()=>{if(matchMedia('(pointer:coarse)').matches)return;const g=document.getElementById('cg');let raf;document.addEventListener('mousemove',e=>{if(raf)cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>{g.style.left=e.clientX+'px';g.style.top=e.clientY+'px';g.classList.add('on')})},{passive:true});document.addEventListener('mouseleave',()=>g.classList.remove('on'))})();
(()=>{if(matchMedia('(pointer:coarse)').matches)return;document.querySelectorAll('.tilt').forEach(c=>{c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;c.style.transform='perspective(800px) rotateY('+x*5+'deg) rotateX('+-y*5+'deg) translateY(-6px) scale3d(1.015,1.015,1.015)'},{passive:true});c.addEventListener('mouseleave',()=>{c.style.transform=''})})})();

/* ── mobile drawer ── */
function openDrawer(){const d=document.getElementById('drawer');if(d){d.classList.add('on');document.body.style.overflow='hidden'}}
function closeDrawer(){const d=document.getElementById('drawer');if(d){d.classList.remove('on');document.body.style.overflow=''}}

/* ── coverflow photo deck ── */
function initDeck(root){
  const deck=root.querySelector('.deck');if(!deck)return;
  const cards=[...deck.querySelectorAll('.dcard')];
  const dotsWrap=root.querySelector('.deck-dots');
  let i=0,timer;
  cards.forEach((c,idx)=>c.addEventListener('click',()=>{if(idx===i)openModalMaybe(c);else{i=idx;render();reset()}}));
  if(dotsWrap){dotsWrap.innerHTML=cards.map((_,idx)=>`<i data-i="${idx}"></i>`).join('');
    dotsWrap.querySelectorAll('i').forEach(d=>d.addEventListener('click',()=>{i=+d.dataset.i;render();reset()}));}
  function openModalMaybe(c){if(typeof openModal==='function')openModal();}
  function render(){
    const n=cards.length;
    const w=(root.querySelector('.deck-wrap')||root).clientWidth||900;
    const step=Math.max(70,Math.min(230,w*0.27));
    const depth=Math.min(280,w*0.32);
    cards.forEach((c,idx)=>{
      let o=idx-i; if(o>n/2)o-=n; if(o<-n/2)o+=n;
      const abs=Math.abs(o);
      const tx=o*step, tz=-abs*depth, ry=o*-38, sc=1-abs*0.12;
      c.style.transform=`translateX(${tx}px) translateZ(${tz}px) rotateY(${ry}deg) scale(${sc})`;
      c.style.opacity=abs>2?0:1;
      c.style.zIndex=100-abs;
      c.style.filter=abs===0?'none':`brightness(${1-abs*0.18})`;
      c.style.pointerEvents=abs>2?'none':'auto';
    });
    if(dotsWrap)dotsWrap.querySelectorAll('i').forEach((d,idx)=>d.classList.toggle('on',idx===i));
  }
  let rz;addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(render,120)},{passive:true});
  function go(dir){i=(i+dir+cards.length)%cards.length;render();reset()}
  function reset(){clearInterval(timer);timer=setInterval(()=>go(1),4500)}
  const prev=root.querySelector('.deck-prev'),next=root.querySelector('.deck-next');
  if(prev)prev.addEventListener('click',()=>{go(-1)}); if(next)next.addEventListener('click',()=>{go(1)});
  render();reset();
  if(matchMedia('(pointer:coarse)').matches){let sx=0;deck.addEventListener('touchstart',e=>sx=e.touches[0].clientX,{passive:true});deck.addEventListener('touchend',e=>{const dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>40)go(dx<0?1:-1)},{passive:true})}
}
document.querySelectorAll('.deck-wrap').forEach(initDeck);

/* ── image lightbox ── */
(()=>{
  const figs=[...document.querySelectorAll('.gal figure img, .lbx')];
  if(!figs.length)return;
  const items=figs.map(im=>({src:im.dataset.full||im.src,cap:im.closest('figure')?.querySelector('figcaption')?.textContent||im.alt||''}));
  let cur=0;
  const lb=document.createElement('div');lb.className='lb';
  lb.innerHTML='<button class="lb-x" aria-label="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg></button><button class="lb-p" aria-label="Prev"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></button><img alt=""><button class="lb-n" aria-label="Next"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg></button><div class="lb-cap"></div>';
  document.body.appendChild(lb);
  const im=lb.querySelector('img'),cap=lb.querySelector('.lb-cap');
  function show(n){cur=(n+items.length)%items.length;im.src=items[cur].src;cap.textContent=items[cur].cap}
  figs.forEach((f,idx)=>f.addEventListener('click',()=>{show(idx);lb.classList.add('on');document.body.style.overflow='hidden'}));
  lb.querySelector('.lb-x').addEventListener('click',()=>{lb.classList.remove('on');document.body.style.overflow=''});
  lb.querySelector('.lb-p').addEventListener('click',e=>{e.stopPropagation();show(cur-1)});
  lb.querySelector('.lb-n').addEventListener('click',e=>{e.stopPropagation();show(cur+1)});
  lb.addEventListener('click',e=>{if(e.target===lb){lb.classList.remove('on');document.body.style.overflow=''}});
  addEventListener('keydown',e=>{if(!lb.classList.contains('on'))return;if(e.key==='Escape'){lb.classList.remove('on');document.body.style.overflow=''}if(e.key==='ArrowLeft')show(cur-1);if(e.key==='ArrowRight')show(cur+1)});
})();

/* ── inject shared SVG icon sprite ── */
(()=>{const s=`<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-stethoscope" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.3.3 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6 6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></symbol>
<symbol id="i-heart" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7Z"/><path d="M3.22 12H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.28"/></symbol>
<symbol id="i-droplet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></symbol>
<symbol id="i-activity" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></symbol>
<symbol id="i-award" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15.477 12.89 1.515 8.526a.5.5 0 0 1-.81.47l-3.58-2.687a1 1 0 0 0-1.197 0l-3.586 2.686a.5.5 0 0 1-.81-.469l1.514-8.526"/><circle cx="12" cy="8" r="6"/></symbol>
<symbol id="i-bone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 10c.7-.7 1.69 0 2.5 0a2.5 2.5 0 1 0 0-5 .5.5 0 0 1-.5-.5 2.5 2.5 0 1 0-5 0c0 .81.7 1.8 0 2.5l-7 7c-.7.7-1.69 0-2.5 0a2.5 2.5 0 0 0 0 5c.28 0 .5.22.5.5a2.5 2.5 0 1 0 5 0c0-.81-.7-1.8 0-2.5z"/></symbol>
<symbol id="i-scan" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 12h10"/></symbol>
<symbol id="i-scale" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></symbol>
<symbol id="i-gauge" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/></symbol>
<symbol id="i-home" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></symbol>
<symbol id="i-usercheck" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m16 11 2 2 4-4"/></symbol>
<symbol id="i-wallet" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></symbol>
<symbol id="i-leaf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></symbol>
<symbol id="i-target" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
<symbol id="i-help" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></symbol>
<symbol id="i-phone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></symbol>
<symbol id="i-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></symbol>
<symbol id="i-star" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></symbol>
<symbol id="i-fb" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></symbol>
<symbol id="i-ig" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><path d="M17.5 6.5h.01"/></symbol>
<symbol id="i-in" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></symbol>
<symbol id="i-wa" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></symbol>
</defs></svg>`;const d=document.createElement('div');d.style.cssText='position:absolute;width:0;height:0;overflow:hidden';d.setAttribute('aria-hidden','true');d.innerHTML=s;document.body.insertBefore(d,document.body.firstChild)})();
