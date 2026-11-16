const sharp=require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const fs=require('fs'),path=require('path');
(async()=>{
const out=path.join(__dirname,'../outputs');fs.mkdirSync(out,{recursive:true});
const svg=path.join(__dirname,'draft-v2.svg');
await sharp(svg).jpeg({quality:96,chromaSubsampling:'4:4:4'}).toFile(path.join(out,'清华葡萄酒协会_乐为品鉴_长图修订稿.jpg'));
const layout=JSON.parse(fs.readFileSync(path.join(__dirname,'layout-v2.json')));
for(const [i,y] of [0,layout.terroir,layout.winery,layout.speaker,layout.cards[0]-20,layout.event].entries())
await sharp(svg).extract({left:0,top:Math.floor(y),width:1080,height:Math.min(1600,Math.floor(layout.height-y))}).png().toFile(path.join(__dirname,'v2-qa'+i+'.png'));
console.log(fs.statSync(path.join(out,'清华葡萄酒协会_乐为品鉴_长图修订稿.jpg')).size);
})();
