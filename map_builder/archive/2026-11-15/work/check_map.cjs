const {chromium}=require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
const path=require('path');
const root='C:/Users/32697/Desktop/thuwine/map_builder';
const out='C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs';
(async()=>{
 fs.mkdirSync(out,{recursive:true});fs.mkdirSync(root+'/checks',{recursive:true});
 const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,args:['--disable-gpu']});
 const page=await browser.newPage({viewport:{width:1450,height:1080},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'networkidle'});
 await page.screenshot({path:root+'/checks/web-desktop.png'});
 const initial=await page.locator('#map-svg').getAttribute('viewBox');
 if(initial!=='0 0 600 900')throw Error('Invalid initial viewBox');
 await page.locator('[data-toggle="rivers"]').uncheck();
 const hidden=await page.locator('[data-layer="rivers"]').first().evaluate(e=>getComputedStyle(e).display);
 if(hidden!=='none')throw Error('River layer toggle failed');
 await page.locator('[data-toggle="rivers"]').check();
 await page.locator('[data-focus="vosne"]').click();
 const inset=await page.locator('#map-svg').getAttribute('viewBox');if(inset===initial)throw Error('Focus failed');
 await page.locator('#zoom-in').click();if(await page.locator('#zoom-label').innerText()!=='130%')throw Error('Zoom failed');
 await page.locator('[data-focus="all"]').click();
 await page.locator('#tab-dossier').click();if(await page.locator('.estate').count()!==20)throw Error('Missing estates');
 await page.locator('#tab-map').click();
 await page.locator('[data-focus="vosne"]').click();
 await page.locator('[data-toggle="rivers"]').uncheck();
 const downloadPromise=page.waitForEvent('download');await page.locator('#export-svg').click();const download=await downloadPromise;
 await download.saveAs(root+'/checks/export-from-focused-view.svg');
 const exported=fs.readFileSync(root+'/checks/export-from-focused-view.svg','utf8');
 if(!exported.includes('viewBox="0 0 600 900"')||exported.includes('class="hide-layer"'))throw Error('Export did not restore full map');
 await page.locator('[data-toggle="rivers"]').check();await page.locator('[data-focus="all"]').click();
 const bounds=await page.locator('#map-svg').evaluate(svg=>{
   let outside=[];for(const t of svg.querySelectorAll('text')){let b=t.getBBox();if(b.x<0||b.y<0||b.x+b.width>600.1||b.y+b.height>900.1)outside.push({text:t.textContent,box:{x:b.x,y:b.y,w:b.width,h:b.height}})}return outside;
 });
 const unique=await page.locator('[data-feature]').evaluateAll(es=>[...new Set(es.map(e=>e.dataset.feature))]);
 const textOverlaps=await page.locator('#map-svg').evaluate(svg=>{
   const rows=[];for(const p of svg.querySelectorAll('[data-panel]')){const ts=[...p.querySelectorAll('text')];for(let i=0;i<ts.length;i++)for(let j=i+1;j<ts.length;j++){const a=ts[i].getBBox(),b=ts[j].getBBox();const w=Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x),h=Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y);if(w>.8&&h>.8)rows.push({panel:p.dataset.panel,a:ts[i].textContent,b:ts[j].textContent,w,h})}}return rows;
 });
 const svg=fs.readFileSync(root+'/composition.svg','utf8');
 const art=await browser.newPage({viewport:{width:1200,height:1800},deviceScaleFactor:1});
 await art.setContent('<html><body style="margin:0">'+svg+'<style>svg{display:block;width:1200px;height:1800px}</style></body></html>');
 await art.screenshot({path:out+'/Bourgogne-composition.png',fullPage:true});
 for(const key of ['vosne','montrachet']){
   const box=await art.locator('#panel-'+key).boundingBox();await art.screenshot({path:root+'/checks/'+key+'.png',clip:box});
 }
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:root+'/checks/web-mobile.png',fullPage:true});
 const quality={errors,outside_page:bounds,visible_grand_cru_names:unique.length,grand_cru_names:unique,text_overlaps:textOverlaps,checks:{full_view:true,layer_toggle:true,inset_focus:true,zoom:true,estate_count:20,full_svg_export_from_cropped_hidden_view:true}};
 fs.writeFileSync(root+'/checks/validation.json',JSON.stringify(quality,null,2));console.log(JSON.stringify(quality,null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
