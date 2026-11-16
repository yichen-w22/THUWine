const sharp=require('C:/Users/32697/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const fs=require('fs'),path=require('path');
(async()=>{
  const layout=JSON.parse(fs.readFileSync(path.join(__dirname,'layout-v2.json')));
  const svg=path.join(__dirname,'approved.svg');
  const out=path.resolve(__dirname,'../outputs/公众号分段图片');fs.mkdirSync(out,{recursive:true});
  const specs=[
    ['01_封面与风土介绍',0,layout.winery],
    ['02_酒庄与分享人介绍',layout.winery,layout.wines],
    ['03_葡萄酒介绍',layout.wines,layout.rice],
    ['04_精酿米酒与彩蛋',layout.rice,layout.event],
    ['05_报名细节',layout.event,layout.notice],
    ['06_温馨提示与特别鸣谢',layout.notice,layout.responsible],
    ['07_理性饮酒与结语',layout.responsible,layout.height]
  ];
  const full=await sharp(svg).png().toBuffer();
  const results=[];
  for(const [name,start,end] of specs){
    const top=Math.floor(start),height=Math.floor(end)-top;
    const file=path.join(out,name+'.jpg');
    await sharp(full).extract({left:0,top,width:1080,height}).jpeg({quality:97,chromaSubsampling:'4:4:4'}).toFile(file);
    results.push({name,width:1080,height,bytes:fs.statSync(file).size});
  }
  const checks=[[0,950,'header'],[layout.cards[5]-20,1000,'white-wine'],[layout.notice,850,'notice'],[layout.height-500,500,'ending']];
  for(const [top,h,name] of checks) await sharp(full).extract({left:0,top:Math.floor(top),width:1080,height:h}).png().toFile(path.join(__dirname,'final-check-'+name+'.png'));
  fs.writeFileSync(path.join(__dirname,'export-results.json'),JSON.stringify(results));
  console.log(JSON.stringify({totalHeight:layout.height,parts:results},null,2));
})();
