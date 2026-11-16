const { chromium } = require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--disable-gpu']});
const page=await browser.newPage({viewport:{width:1080,height:1400},deviceScaleFactor:1});
await page.goto('file:///'+path.join(__dirname,'draft.html').replaceAll('\\','/'));
await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()))});
const height=await page.locator('main').evaluate(el=>el.offsetHeight);
const out=path.join(__dirname,'../outputs');fs.mkdirSync(out,{recursive:true});
await page.screenshot({path:path.join(out,'清华葡萄酒协会_乐为品鉴_长图初稿.jpg'),fullPage:true,type:'jpeg',quality:95});
await page.screenshot({path:path.join(__dirname,'top.png'),clip:{x:0,y:0,width:1080,height:1900}});
for(const [i,y] of [3400,4700,height-2100].entries())await page.screenshot({path:path.join(__dirname,'check'+i+'.png'),clip:{x:0,y,width:1080,height:1900}});
console.log(JSON.stringify({height,images:await page.locator('img').count(),overflow:await page.evaluate(()=>[...document.querySelectorAll('.winecopy')].filter(e=>e.scrollWidth>e.clientWidth).length)}));
await browser.close();
})();
