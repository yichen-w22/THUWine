'use strict';
const fs=require('fs'),path=require('path'),os=require('os');
function loadSharp(){
  const candidates=['sharp'];
  if(process.env.POST_BUILDER_NODE_MODULES)candidates.push(path.join(process.env.POST_BUILDER_NODE_MODULES,'sharp'));
  candidates.push(path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp'));
  for(const p of candidates){try{return require(p)}catch(e){if(e.code!=='MODULE_NOT_FOUND')throw e}}
  throw new Error('sharp not found. Run npm install in post_builder, or set POST_BUILDER_NODE_MODULES.');
}
async function main(){
  const sharp=loadSharp(),[svgPath,manifestPath,outDir]=process.argv.slice(2);
  if(!svgPath||!manifestPath||!outDir)throw new Error('Expected SVG, layout JSON, and output directory.');
  const layout=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
  const theme=layout.export;
  fs.mkdirSync(outDir,{recursive:true});
  const raster=await sharp(svgPath).png().toBuffer();
  const results=[];
  for(let i=0;i<layout.sections.length;i++){
    const s=layout.sections[i],top=Math.floor(s.start),height=Math.floor(s.end)-top;
    if(height<=0)throw new Error('Empty section: '+s.id);
    const safe=s.label.replace(/[<>:"/\\|?*\x00-\x1f]/g,'_');
    const file=String(i+1).padStart(2,'0')+'_'+safe+'.'+theme.format;
    let img=sharp(raster).extract({left:0,top,width:layout.width,height});
    img=theme.format==='png'?img.png():img.jpeg({quality:theme.quality,chromaSubsampling:theme.chromaSubsampling});
    await img.toFile(path.join(outDir,file));
    const meta=await sharp(path.join(outDir,file)).metadata();
    if(meta.width!==layout.width||meta.height!==height)throw new Error('Output dimension mismatch: '+file);
    results.push({file,width:meta.width,height:meta.height,bytes:fs.statSync(path.join(outDir,file)).size});
  }
  fs.writeFileSync(path.join(outDir,'manifest.json'),JSON.stringify({digest:layout.digest,width:layout.width,height:layout.height,images:results},null,2));
  process.stdout.write(JSON.stringify(results,null,2)+'\n');
}
main().catch(e=>{console.error(e.message);process.exit(1)});
