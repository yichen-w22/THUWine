const sharp=require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root='C:/Users/32697/Desktop/thuwine/map_builder',out='C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs';
(async()=>{
await sharp(root+'/composition-v02.svg',{density:96}).resize(1800,2700).png().toFile(out+'/Bourgogne-composition-v02.png');
await sharp(out+'/Bourgogne-composition-v02.png').extract({left:620,top:260,width:1110,height:1050}).png().toFile(root+'/checks/columns-v02.png');
await sharp(out+'/Bourgogne-composition-v02.png').extract({left:60,top:1050,width:550,height:1350}).png().toFile(root+'/checks/insets-v02.png');
console.log('Rendered static composition 02');
})().catch(e=>{console.error(e);process.exit(1)});
