const sharp=require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const fs=require('fs');
const root='C:/Users/32697/Desktop/thuwine/map_builder';
const out='C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs';
(async()=>{
fs.mkdirSync(out,{recursive:true});
await sharp(root+'/composition.svg',{density:96}).resize(1800,2700).png().toFile(out+'/Bourgogne-composition.png');
await sharp(out+'/Bourgogne-composition.png').extract({left:75,top:1395,width:555,height:810}).png().toFile(root+'/checks/insets.png');
await sharp(out+'/Bourgogne-composition.png').extract({left:640,top:450,width:1090,height:1000}).png().toFile(root+'/checks/north-detail.png');
console.log('Static map PNG: 1800 x 2700. Two inspection crops saved.');
})().catch(e=>{console.error(e);process.exit(1)});
