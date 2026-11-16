"""Data-driven local preview, approval, and contiguous equal-width image export."""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import os
import tempfile
from html import escape
from pathlib import Path
from markdown_text import resolve_post, markdown_path, init_markdown

try:
    from PIL import Image
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
except ImportError as exc:
    raise SystemExit('Missing dependency. Run: python -m pip install -r requirements.txt') from exc

ROOT = Path(__file__).resolve().parents[1]
TYPES = {'cover','heading','paragraph','image','stats','table','wine_list','speaker','callout','event','notice','sponsor','responsible','closing','spacer','rule'}

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    atomic_text(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def atomic_text(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    handle=tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.'+path.name+'-',suffix='.tmp',delete=False)
    temp=Path(handle.name)
    try:
        with handle:handle.write(value)
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)

def project_path(value):
    p=Path(value)
    p=p if p.is_absolute() else ROOT/'projects'/p
    p=p.resolve()
    if not p.is_relative_to((ROOT/'projects').resolve()):
        raise ValueError('Project must be inside post_builder/projects.')
    return p

class Project:
    def __init__(self, directory):
        self.directory=directory
        self.raw_post=read_json(directory/'post.json')
        self.theme=read_json(ROOT/'theme.json')
        self.assets={}
        for key, value in self.raw_post.get('assets',{}).items():
            p=(directory/value['path']).resolve()
            if not p.is_relative_to(ROOT.resolve()):
                raise ValueError(f'Asset {key} must be copied into post_builder first: {p}')
            self.assets[key]=p
        self.digest=self.fingerprint()
        self.post=resolve_post(directory,self.raw_post)
        if self.fingerprint()!=self.digest:raise ValueError('正文正在保存，请稍后重试。')

    def fingerprint(self):
        h=hashlib.sha256()
        paths=[self.directory/'post.json',ROOT/'theme.json',Path(__file__),Path(__file__).with_name('markdown_text.py'),Path(__file__).with_name('live_preview.py'),ROOT/'scripts/export_images.cjs']
        source=markdown_path(self.directory,self.raw_post)
        if source is not None:paths.append(source)
        for p in paths:
            h.update(p.read_bytes())
        for key,p in sorted(self.assets.items()):
            h.update(key.encode());h.update(p.read_bytes())
        for spec in self.theme['fonts'].values():
            h.update(Path(spec['file']).read_bytes())
        return h.hexdigest()

    def validate(self):
        errors=[];warnings=[];ids=set();wines=[]
        if self.post.get('schema_version')!=1: errors.append('schema_version must be 1.')
        if self.post.get('theme')!=self.theme['id']: errors.append('Project theme does not match theme.json.')
        if not self.post.get('title'):errors.append('Missing post title.')
        if not self.post.get('sections'):errors.append('No sections.')
        for s in self.post.get('sections',[]):
            if not s.get('blocks'):errors.append(f"Empty section: {s.get('id')}")
            for b in s.get('blocks',[]):
                bid=b.get('id')
                if not bid or bid in ids:errors.append(f'Missing or duplicate block id: {bid}')
                ids.add(bid)
                if b.get('type') not in TYPES:errors.append(f'Unknown component: {b.get("type")}')
                for asset in self.asset_references(b):
                    if asset not in self.assets:errors.append(f'Unknown asset {asset} in {bid}')
                if b.get('type')=='wine_list':wines.extend(b.get('items',[]))
                if b.get('type')=='table':
                    columns=b.get('columns',[]);rows=b.get('rows',[])
                    widths=[c.get('width',0) for c in columns]
                    available=self.theme['canvas']['width']-2*self.theme['canvas']['margin']
                    valid_widths=bool(widths) and all(isinstance(w,(int,float)) and w>24 for w in widths)
                    if not valid_widths or abs(sum(widths)-available)>.1:
                        errors.append(f'{bid}: table column widths must fill the content area.')
                    if not rows or any(not isinstance(c.get('label'),str) for c in columns):
                        errors.append(f'{bid}: table needs labelled columns and rows.')
                    row_ids=set()
                    for row in rows:
                        rid=row.get('id')
                        if not rid or rid in row_ids:errors.append(f'{bid}: table row ids must be unique.')
                        row_ids.add(rid)
                        if len(row.get('cells',[]))!=len(columns) or any(not isinstance(v,str) for v in row.get('cells',[])):
                            errors.append(f'{bid}: table row {rid} must have one text cell per column.')
                if b.get('type')=='notice' and not b.get('confirmed',False):
                    errors.append(f'{bid}: registration/refund terms need user confirmation.')
                if b.get('type')=='event':
                    for field in ['when','where','contact']:
                        if not b.get(field):warnings.append(f'{bid}: {field} not supplied; do not invent it.')
                if b.get('needs_confirmation'):errors.append(f'{bid}: unresolved content confirmation.')
        for k,p in self.assets.items():
            if not p.is_file():errors.append(f'Missing asset: {k}: {p}')
        if wines:
            names=[w.get('name') for w in wines]
            if len(names)!=len(set(names)):errors.append('Duplicate wine names.')
            expected=self.post.get('expected_wine_count')
            if expected is not None and expected!=len(wines):errors.append(f'Wine count {len(wines)} differs from expected {expected}.')
            for w in wines:
                if not w.get('name') or not w.get('description'):errors.append('Wine needs name and description.')
                for sid in w.get('sources',[]):
                    if sid not in self.post.get('sources',{}):errors.append(f'Unknown wine source: {sid}')
        return {'errors':errors,'warnings':warnings,'wine_count':len(wines),'digest':self.digest}

    @staticmethod
    def asset_references(value):
        found=[]
        if isinstance(value,dict):
            for k,v in value.items():
                if k=='asset' and isinstance(v,str):found.append(v)
                else:found.extend(Project.asset_references(v))
        elif isinstance(value,list):
            for v in value:found.extend(Project.asset_references(v))
        return found

    def log(self, action, note=''):
        row={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'action':action,'digest':self.digest,'note':note}
        with (self.directory/'revisions.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(row,ensure_ascii=False)+'\n')

class Layout:
    def __init__(self, project):
        self.p=project;self.t=project.theme;self.nodes=[];self.sections=[];self.y=40;self.block_id='';self.counter=0
        self.width=self.t['canvas']['width'];self.margin=self.t['canvas']['margin'];self.content=self.width-2*self.margin
        self.fonts={k:TTFont(v['file'],fontNumber=v.get('index',0)) for k,v in self.t['fonts'].items()}
        self.glyph_cache={};self.missing=set();self.wine_index=0
        wine_items=[w for section in project.post['sections'] for b in section['blocks'] if b['type']=='wine_list' for w in b['items']]
        self.counts={'wine_count':len(wine_items),'grape_wine_count':sum(w.get('category')!='RICE WINE' for w in wine_items),'rice_wine_count':sum(w.get('category')=='RICE WINE' for w in wine_items)}

    def style(self, role):return self.t['type'][role].copy()
    def color(self, value):return self.t['colors'].get(value,value)
    def resolve_text(self, value):
        for key,count in self.counts.items():value=value.replace('{'+key+'}',str(count))
        return value
    def add(self, kind, **attrs):
        self.counter+=1;self.nodes.append({'kind':kind,'id':f'{self.block_id}-{self.counter}',**attrs})

    def glyph(self,char,font):
        key=(font,char)
        if key not in self.glyph_cache:
            f=self.fonts[font];name=f.getBestCmap().get(ord(char))
            if name is None:self.missing.add(char);name='.notdef'
            gs=f.getGlyphSet();pen=SVGPathPen(gs);gs[name].draw(pen)
            self.glyph_cache[key]=(pen.getCommands(),gs[name].width,f['head'].unitsPerEm)
        return self.glyph_cache[key]

    def measure(self,s,size,font):return sum(self.glyph(c,font)[1]/self.glyph(c,font)[2]*size for c in s)

    def text(self,s,x,y,role='body',align='left',**override):
        style=self.style(role);style.update(override)
        w=self.measure(s,style['size'],style['font'])
        if align=='center':x-=w/2
        if align=='right':x-=w
        if x<0 or x+w>self.width+1:raise ValueError(f'Text exceeds canvas in {self.block_id}: {s}')
        self.add('text',text=s,x=x,y=y,role=role,**style)

    def paragraph(self,s,role='body',x=None,y=None,w=None,align='left',**override):
        x=self.margin if x is None else x;y=self.y if y is None else y;w=self.content if w is None else w
        st=self.style(role);st.update(override);lines=[];current=''
        for token in re.findall(r'[0-9]+(?:[.–—:][0-9]+)*(?:%|℃)?|[A-Za-z]+|.',s,flags=re.S):
            if token=='\n':lines.append(current);current='';continue
            if current and self.measure(current+token,st['size'],st['font'])>w:
                if token in '，。！？；：、）》”：' and current:
                    last=current[-1];current=current[:-1];lines.append(current);current=last
                else:lines.append(current);current=''
            current+=token
        if current:lines.append(current)
        for line in lines:
            pos=x+w/2 if align=='center' else x+w if align=='right' else x
            self.text(line,pos,y,role,align=align,**override);y+=st['line']
        return y

    def rect(self,x,y,w,h,color):self.add('rect',x=x,y=y,width=w,height=h,color=color)
    def rule(self,y):self.rect(self.margin,y,self.content,1,'rule')

    def image(self,spec,x=None,y=None,w=None,h=None):
        x=self.margin if x is None else x;y=self.y if y is None else y;w=self.content if w is None else w
        with Image.open(self.p.assets[spec['asset']]) as im:iw,ih=im.size
        crop=spec.get('crop',[0,0,iw,ih]);cx,cy,cw,ch=crop
        if cw<=0 or ch<=0 or cx<0 or cy<0 or cx+cw>iw+.1 or cy+ch>ih+.1:
            raise ValueError(f'Invalid crop in {self.block_id}: {crop}, source {iw}x{ih}')
        h=w*ch/cw if h is None else h
        self.add('image',asset=spec['asset'],x=x,y=y,width=w,height=h,crop=crop,iw=iw,ih=ih,alt=spec.get('alt',''))
        return y+h

    def heading(self,b):
        if b.get('eyebrow'):
            self.text(b['eyebrow'],self.margin,self.y,'eyebrow');self.y+=62
        role=b.get('role','section')
        self.y=self.paragraph(b['text'],role,align=b.get('align','left'),color=b.get('color',self.style(role)['color']))+b.get('after',30)

    def cover(self,b):
        if b.get('logo'):
            self.y=self.image(b['logo'],x=143,w=794,h=122)+53
        self.text(b['brand'],self.margin,self.y,'meta');self.y+=85
        for line in b['title_lines']:
            self.text(line,self.width/2,self.y,'cover',align='center');self.y+=self.style('cover')['line']
        self.rect(self.margin,self.y+22,70,3,'accent');self.y+=70
        self.text(b['subtitle'],self.margin,self.y,'small',color='muted');self.y+=75
        self.text(b['meta'],self.margin,self.y,'small',color='accent');self.y+=95

    def stats(self,b):
        self.rule(self.y);self.y+=38;cell=self.content/len(b['items'])
        for i,item in enumerate(b['items']):
            cx=self.margin+cell*(i+.5)
            self.text(item['value'],cx,self.y,'stat',align='center')
            self.text(item['label'],cx,self.y+71,'stat_label',align='center')
        self.y+=142;self.rule(self.y);self.y+=50

    def wine_list(self,b):
        cfg=self.t['wine'];right=self.width-self.margin-cfg['text_x']
        for wine in b['items']:
            top=self.y;self.wine_index+=1
            label=wine.get('category','WINE')+' / '+str(self.wine_index).zfill(2)
            self.text(label,cfg['text_x'],self.y,'eyebrow');self.y+=58
            self.text(wine['brand'],cfg['text_x'],self.y,'wine_brand');self.y+=self.style('wine_brand')['line']
            self.y=self.paragraph(wine['name'],'wine_title',x=cfg['text_x'],w=right)+17
            self.rect(cfg['text_x'],self.y+5,3,37,'rule')
            self.y=self.paragraph(wine['meta'],'tag',x=cfg['text_x']+20,w=right-20)+23
            self.y=self.paragraph(wine['description'],'wine_body',x=cfg['text_x'],w=right)+48
            self.image(wine['image'],x=cfg['image_x'],y=top+25,w=cfg['image_width'],h=cfg['image_height'])
            self.y=max(self.y,top+self.t['spacing']['wine_min_height']);self.rule(self.y);self.y+=self.t['spacing']['wine_gap']

    def table(self,b):
        columns=b['columns'];start=self.y;padding=12;vertical=18
        rows=[[c['label'] for c in columns]]+[row['cells'] for row in b['rows']]
        for index,cells in enumerate(rows):
            top=self.y;insertion=len(self.nodes);x=self.margin;bottom=top
            for column,value in zip(columns,cells):
                bottom=max(bottom,self.paragraph(value,'small',x=x+padding,y=top+vertical,w=column['width']-2*padding,color='accent' if index==0 else 'body'))
                x+=column['width']
            self.y=bottom+vertical
            if index==0:
                self.nodes.insert(insertion,{'kind':'rect','id':self.block_id+'-header','x':self.margin,'y':top,'width':self.content,'height':self.y-top,'color':'callout'})
            self.rect(self.margin,self.y,self.content,1,'rule')
        self.rect(self.margin,start,self.content,1,'rule')
        x=self.margin
        for width in [0]+[c['width'] for c in columns]:
            x+=width;self.rect(x,start,1,self.y-start,'rule')
        self.y+=b.get('after',55)

    def speaker(self,b):
        self.y=self.image(b['image'])+35
        self.text('本次分享人 · '+b['name'],self.margin,self.y,'small',color='accent');self.y+=65
        self.y=self.paragraph(b['description'],'meta')+70

    def callout(self,b):
        start=self.y;insert=len(self.nodes)
        self.y+=35
        if b.get('eyebrow'):self.text(b['eyebrow'],self.margin+40,self.y,'eyebrow');self.y+=65
        self.y=self.paragraph(b['text'],'wine_body',x=self.margin+40,w=self.content-80)+45
        end=self.y
        self.nodes[insert:insert]=[
            {'kind':'rect','id':self.block_id+'-background','x':self.margin,'y':start,'width':self.content,'height':end-start,'color':'callout'},
            {'kind':'rect','id':self.block_id+'-stripe','x':self.margin,'y':start,'width':4,'height':end-start,'color':'accent'}]
        self.y+=65

    def event(self,b):
        # All date/location/contact text is editable; no dated poster is reused as a flat event panel.
        right=self.width-self.margin
        self.text(b.get('heading','分享人 Lecturer'),right,self.y,'small',align='right',color='accent');self.y+=60
        self.y=self.paragraph(b.get('speakers',''),'small',align='right')
        self.y=self.paragraph(b.get('speaker_roles',''),'meta',align='right')+20
        if b.get('horse'):
            top=self.y;self.y=self.image(b['horse'],x=0,w=self.width)
            # The supplied crop retains old text only in the top-right blank area; mask that area in layout.
            if b.get('horse_mask'):
                mask=b['horse_mask'];self.rect(mask[0],top+mask[1],mask[2],mask[3],self.t['canvas']['background'])
            self.y+=25
        for field,label in [('when','时间'),('where','地点'),('contact','电话')]:
            if b.get(field):self.y=self.paragraph(b[field]+'  |  '+label,'small',align='right',color='muted')
        self.y+=45

    def notice(self,b):
        self.heading({'text':b.get('heading','温馨提示'),'role':'subheading','color':'black'})
        self.y=self.paragraph(b['text'],'wine_body')+65

    def sponsor(self,b):
        self.heading({'text':b.get('heading','特别鸣谢'),'role':'subheading','color':'black'})
        self.y=self.paragraph(b['thanks'],'wine_body')+35
        if b.get('logo'):self.y=self.image(b['logo'],x=150,w=780)+55
        for s in b['paragraphs']:self.y=self.paragraph(s,'small')+35
        self.y+=25

    def responsible(self,b):
        self.y=self.image(b['image'])+39
        self.y=self.paragraph(b['text'],'small')+15

    def closing(self,b):
        self.y+=75;self.rect(self.width/2-30,self.y,60,2,'black');self.y+=38
        for s in b['lines']:
            self.text(s,self.width/2,self.y,'closing',align='center');self.y+=self.style('closing')['line']
        self.y+=20;self.text(b['brand'],self.width/2,self.y,'caption',align='center');self.y+=90

    def build(self):
        for section in self.p.post['sections']:
            start=0 if not self.sections else self.y
            for b in section['blocks']:
                self.block_id=b['id'];self.counter=0;kind=b['type']
                if kind=='heading':self.heading(b)
                elif kind=='paragraph':self.y=self.paragraph(self.resolve_text(b['text']),b.get('role','body'),align=b.get('align','left'),**({'color':b['color']} if 'color' in b else {}))+b.get('after',self.t['spacing']['paragraph'])
                elif kind=='image':
                    self.y=self.image(b,w=b.get('width',self.content),x=b.get('x',self.margin),h=b.get('height'))+b.get('after',30)
                    if b.get('caption'):self.text(b['caption'],self.margin,self.y,'caption');self.y+=78
                elif kind=='spacer':self.y+=b.get('height',55)
                elif kind=='rule':self.rule(self.y);self.y+=b.get('after',40)
                else:getattr(self,kind)(b)
            self.sections.append({'id':section['id'],'label':section['label'],'start':start,'end':int(self.y)})
            self.y=int(self.y)
        if self.missing:raise ValueError('Font does not contain: '+''.join(sorted(self.missing)))
        return {'digest':self.p.digest,'width':self.width,'height':int(self.y),'sections':self.sections,'nodes':self.nodes,'export':self.t['export']}

    def svg(self, scene, outlines=False):
        body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{scene["width"]}" height="{scene["height"]}" viewBox="0 0 {scene["width"]} {scene["height"]}" role="document" aria-label="{escape(self.p.post["title"],quote=True)}">',f'<rect width="100%" height="100%" fill="{self.t["canvas"]["background"]}"/>']
        asset_data={}
        for n in scene['nodes']:
            kind=n['kind'];nid=escape(n['id'],quote=True)
            if kind=='rect':body.append(f'<rect id="{nid}" x="{n["x"]}" y="{n["y"]}" width="{n["width"]}" height="{n["height"]}" fill="{self.color(n["color"])}"/>')
            elif kind=='text':
                color=self.color(n['color']);size=n['size'];stroke=''
                if not outlines:
                    if n.get('bold'):stroke=f' stroke="{color}" stroke-width="1.5" stroke-linejoin="round" paint-order="stroke fill"'
                    body.append(f'<text id="{nid}" x="{n["x"]}" y="{n["y"]+size}" font-family="{self.t["fonts"][n["font"]]["family"]}" font-size="{size}" fill="{color}"{stroke}>{escape(n["text"])}</text>')
                else:
                    x=n['x']
                    for char in n['text']:
                        d,advance,upm=self.glyph(char,n['font']);scale=size/upm
                        stroke=f' stroke="{color}" stroke-width="{1.5/scale}" stroke-linejoin="round" paint-order="stroke fill"' if n.get('bold') else ''
                        if d:body.append(f'<path fill="{color}"{stroke} d="{d}" transform="translate({x},{n["y"]+size}) scale({scale},{-scale})"/>')
                        x+=advance*scale
            elif kind=='image':
                key=n['asset']
                if key not in asset_data:
                    p=self.p.assets[key];mime='image/png' if p.suffix.lower()=='.png' else 'image/jpeg'
                    asset_data[key]='data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
                cx,cy,cw,ch=n['crop'];scale=min(n['width']/cw,n['height']/ch)
                ox=n['x']+(n['width']-cw*scale)/2-cx*scale;oy=n['y']+(n['height']-ch*scale)/2-cy*scale
                body.append(f'<clipPath id="clip-{nid}"><rect x="{n["x"]}" y="{n["y"]}" width="{n["width"]}" height="{n["height"]}"/></clipPath><image id="{nid}" href="{asset_data[key]}" x="{ox}" y="{oy}" width="{n["iw"]*scale}" height="{n["ih"]*scale}" clip-path="url(#clip-{nid})" aria-label="{escape(n["alt"],quote=True)}"/>')
        return ''.join(body)+'</svg>'

def require_valid(p):
    result=p.validate()
    if result['errors']:raise ValueError('\n'.join(result['errors']))
    for w in result['warnings']:print('Warning:',w)
    return result

def preview(p,note):
    require_valid(p);renderer=Layout(p);scene=renderer.build();out=p.directory/'preview';out.mkdir(exist_ok=True)
    svg=renderer.svg(scene)
    if p.fingerprint()!=p.digest:raise ValueError('内容在排版期间发生变化，等待保存完成后重新预览。')
    html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(p.post['title'])+'</title><style>body{margin:0;background:#eeeae8}svg{display:block;margin:auto;max-width:100%;height:auto}text{cursor:text;user-select:text}</style>'+svg+'</html>'
    atomic_text(out/'index.html',html);write_json(out/'layout.json',scene)
    source=markdown_path(p.directory,p.raw_post)
    if source is not None:
        history=p.directory/'history/text';history.mkdir(parents=True,exist_ok=True)
        snapshot=history/(p.digest[:12]+'.md')
        if not snapshot.exists():snapshot.write_bytes(source.read_bytes())
    p.log('preview',note);print(out/'index.html')

def approve(p,note):
    require_valid(p)
    layout=read_json(p.directory/'preview/layout.json')
    if layout['digest']!=p.digest:raise ValueError('Preview is stale. Generate and review a new preview first.')
    if not note.strip():raise ValueError('Record the actual user approval in --note.')
    write_json(p.directory/'approval.json',{'digest':p.digest,'approved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'user_instruction':note})
    p.log('approve',note);print('Approved current preview:',p.digest[:12])

def export(p):
    require_valid(p)
    approval=p.directory/'approval.json'
    if not approval.is_file() or read_json(approval).get('digest')!=p.digest:
        raise ValueError('Current content/theme/assets have no matching approval. Review the current preview and obtain user approval before export.')
    renderer=Layout(p);scene=renderer.build();out=p.directory/'exports'/p.digest[:12];out.mkdir(parents=True,exist_ok=True)
    internal=p.directory/'preview';svg=internal/'export.svg';layout=internal/'export-layout.json'
    svg.write_text(renderer.svg(scene,outlines=True),encoding='utf-8');write_json(layout,scene)
    if p.fingerprint()!=p.digest:raise ValueError('内容在导出前发生变化，请重新审阅当前版本。')
    subprocess.run(['node',str(ROOT/'scripts/export_images.cjs'),str(svg),str(layout),str(out)],check=True)
    p.log('export');print(out)

def initial_post(directory,title):
    theme=read_json(ROOT/'theme.json')
    post={'schema_version':1,'title':title,'theme':theme['id'],'assets':{},'sources':{},'sections':[{'id':key,'label':label,'blocks':[]} for key,label in [('terroir','风土介绍'),('winery','酒庄介绍'),('wines','酒款介绍'),('registration','报名细节')]]}
    branding=theme.get('branding',{})
    if branding.get('logo'):
        logo=branding['logo'];path=(ROOT/logo['path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError('Default association logo is missing or outside post_builder.')
        width=logo['width'];available=theme['canvas']['width']-2*theme['canvas']['margin']
        if not 0<width<=available:raise ValueError('Default logo width exceeds the content area.')
        post['assets']['association_logo']={'path':os.path.relpath(path,directory).replace('\\','/'),'source':logo.get('source','用户提供的协会标志')}
        block={'id':'association-logo','type':'image','asset':'association_logo','x':(theme['canvas']['width']-width)/2,'width':width,'alt':branding.get('name','协会')+'标志','after':48}
        if logo.get('crop'):block['crop']=logo['crop']
        post['sections'][0]['blocks'].append(block)
    return post

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['new','check','preview','approve','export','markdown','markdown-refresh','serve','stop'])
    parser.add_argument('project',help='Slug under projects/, or an absolute project directory.')
    parser.add_argument('--title',default='')
    parser.add_argument('--note',default='')
    parser.add_argument('--port',type=int,default=8876)
    parser.add_argument('--open',action='store_true',dest='open_browser')
    args=parser.parse_args();directory=project_path(args.project)
    if args.command=='new':
        if directory.exists():raise ValueError('Project already exists; no files were overwritten.')
        post=initial_post(directory,args.title or args.project)
        directory.mkdir(parents=True);(directory/'assets').mkdir()
        write_json(directory/'post.json',post)
        print(init_markdown(directory,ROOT));return
    if args.command in ('markdown','markdown-refresh'):
        print(init_markdown(directory,ROOT,refresh=args.command=='markdown-refresh'));return
    if args.command=='serve':
        from live_preview import serve
        raw=read_json(directory/'post.json')
        if not raw.get('text_source'):init_markdown(directory,ROOT)
        serve(directory,ROOT,Project,preview,port=args.port,open_browser=args.open_browser);return
    if args.command=='stop':
        from live_preview import stop_server
        stop_server(directory);return
    p=Project(directory)
    if args.command=='check':
        result=p.validate();print(json.dumps(result,ensure_ascii=False,indent=2))
        if result['errors']:raise SystemExit(1)
    elif args.command=='preview':preview(p,args.note)
    elif args.command=='approve':approve(p,args.note)
    else:export(p)

if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,FileNotFoundError,subprocess.CalledProcessError) as e:
        print('ERROR:',e,file=sys.stderr);raise SystemExit(1)
