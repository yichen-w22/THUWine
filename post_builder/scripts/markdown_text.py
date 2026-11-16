"""Human-editable Markdown text, with stable references into the component layout."""
from __future__ import annotations
import copy
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

FIELD=re.compile(r'<!--\s*pb-text:\s*([^\s>]+)\s*-->(.*?)<!--\s*/pb-text\s*-->',re.S)

def markdown_path(directory, post):
    name=post.get('text_source')
    if not name:return None
    p=(directory/name).resolve()
    if not p.is_relative_to(directory.resolve()):raise ValueError('Markdown正文必须位于本项目目录内。')
    return p

def plain(value, spec):
    value=value.strip('\n\r ')
    if spec.get('markdown_heading'):
        value='\n'.join(re.sub(r'^\s*#{1,6}\s+','',line).rstrip() for line in value.splitlines())
    # Markdown is the writing format; font/weight remains controlled by the fixed component theme.
    value=re.sub(r'\*\*(.+?)\*\*',r'\1',value,flags=re.S)
    value=re.sub(r'__(.+?)__',r'\1',value,flags=re.S)
    value=re.sub(r'`([^`\n]+)`',r'\1',value)
    value=re.sub(r'\\([\\`*_{}\[\]()#+.!>\-])',r'\1',value)
    if spec['kind']=='lines':return [line.strip() for line in value.splitlines() if line.strip()]
    if spec['kind']=='paragraphs':return [p.strip() for p in re.split(r'\n\s*\n',value) if p.strip()]
    return value

def parse_markdown(text, schema):
    matches=list(FIELD.finditer(text));values={}
    for match in matches:
        key=match.group(1)
        if key in values:raise ValueError('正文中出现重复编辑标记：'+key)
        if key not in schema:raise ValueError('正文含未知编辑标记：'+key+'；请保留编辑标记，只修改其中的文字。')
        values[key]=plain(match.group(2),schema[key])
    missing=set(schema)-set(values)
    if missing:raise ValueError('正文缺少编辑标记：'+', '.join(sorted(missing))+'。请恢复标记；原网页已保留。')
    remainder=FIELD.sub('',text)
    for line in remainder.splitlines():
        line=line.strip()
        if not line or line.startswith('>') or re.fullmatch(r'!\[.*\]\(.*\)',line):continue
        raise ValueError('有文字位于编辑区域之外：'+line[:70]+'。请将文字放入相邻正文段落，或由排版工具新增组件。')
    return values

def resolve_post(directory, raw):
    path=markdown_path(directory,raw)
    if path is None:return copy.deepcopy(raw)
    values=parse_markdown(path.read_text(encoding='utf-8-sig'),raw['text_schema'])
    def resolve(node):
        if isinstance(node,dict):
            if '$text' in node:
                key=node['$text']
                if key not in values:raise ValueError('Missing Markdown text: '+key)
                return copy.deepcopy(values[key])
            return {k:resolve(v) for k,v in node.items()}
        if isinstance(node,list):return [resolve(v) for v in node]
        return node
    return resolve(raw)

def init_markdown(directory, root, refresh=False):
    directory=Path(directory);root=Path(root)
    raw=json.loads((directory/'post.json').read_text(encoding='utf-8-sig'))
    existing=markdown_path(directory,raw)
    if existing is not None and not refresh:
        raise ValueError('正文.md 已启用，不会覆盖。日常直接编辑正文；结构变化后用 markdown-refresh 保留文字并更新编辑区。')
    if existing is None and (directory/'正文.md').exists():raise ValueError('已有正文.md，未覆盖。请先核对其来源。')
    resolved=resolve_post(directory,raw)
    resolved.pop('text_source',None);resolved.pop('text_schema',None)
    document=copy.deepcopy(resolved);schema={};chunks=[
        '> 直接修改下方标题、段落和酒款介绍并保存。启用自动预览后，网页会自动更新。',
        '> 字体、字号和布局沿用固定模板。图片为排版参考；图片更换、裁切和组件增删仍由排版配置处理。',
        '> 灰色/隐藏的 pb-text 注释是定位标记，请保留；不要把新增文字写在编辑区之外。\n']

    def add(parent,field,key,label,kind='string',heading=None):
        if field not in parent:return
        value=parent[field]
        if not isinstance(value,(str,list)):raise ValueError('无法建立正文编辑区：'+key)
        schema[key]={'kind':kind,'label':label}
        if heading:schema[key]['markdown_heading']=heading
        if kind=='paragraphs':body='\n\n'.join(value)
        elif kind=='lines':body='\n'.join(value)
        else:body=str(value)
        if heading:body='\n'.join('#'*heading+' '+line for line in body.splitlines())
        elif label:chunks.append('> '+label)
        chunks.append('<!-- pb-text: '+key+' -->\n'+body+'\n<!-- /pb-text -->\n')
        parent[field]={'$text':key}

    def reference_image(spec,label):
        asset=spec.get('asset')
        if not asset or asset not in document.get('assets',{}):return
        source=(directory/document['assets'][asset]['path']).resolve()
        if not source.is_relative_to(root.resolve()):raise ValueError('图片必须先归档到 post_builder。')
        thumb_dir=directory/'editing-assets';thumb_dir.mkdir(exist_ok=True)
        key=hashlib.sha256((asset+str(spec.get('crop'))).encode()).hexdigest()[:12]
        dest=thumb_dir/(key+'.png')
        with Image.open(source) as image:
            if spec.get('crop'):
                x,y,w,h=spec['crop'];image=image.crop((x,y,x+w,y+h))
            image.thumbnail((720,640))
            image.save(dest,'PNG')
        chunks.append('!['+label.replace(']','')+'](editing-assets/'+dest.name+')\n')

    add(document,'title','post/title','推送名称',heading=1)
    for section in document.get('sections',[]):
        add(section,'label','section/'+section['id']+'/label','分段名称',heading=2)
        for b in section.get('blocks',[]):
            bid=b['id'];kind=b['type']
            def field(name,label,**kw):add(b,name,bid+'/'+name,label,**kw)
            if kind=='cover':
                if b.get('logo'):reference_image(b['logo'],'联合主办标志')
                field('brand','联合署名');field('title_lines','主标题',kind='lines',heading=3)
                field('subtitle','副标题');field('meta','日期与招募信息')
            elif kind=='heading':
                field('eyebrow','英文眉题');field('text','分节标题',heading=3)
            elif kind=='paragraph':field('text','正文')
            elif kind=='image':
                reference_image(b,b.get('alt','图片参考'));field('caption','图片说明')
            elif kind=='stats':
                for i,item in enumerate(b['items']):
                    add(item,'value',bid+'/'+str(i)+'/value','风土数据')
                    add(item,'label',bid+'/'+str(i)+'/label','数据说明')
            elif kind=='table':
                for i,column in enumerate(b['columns']):
                    add(column,'label',bid+'/column/'+str(i)+'/label','表头')
                for row in b['rows']:
                    for i in range(len(row['cells'])):
                        parent={'value':row['cells'][i]}
                        add(parent,'value',bid+'/row/'+row['id']+'/'+str(i),'表格单元格')
                        row['cells'][i]=parent['value']
            elif kind=='wine_list':
                for wine in b['items']:
                    wid=bid+'/'+wine['id']
                    add(wine,'name',wid+'/name','酒款名称',heading=4)
                    reference_image(wine['image'],'酒瓶参考')
                    for name,label in [('brand','品牌/系列'),('meta','葡萄品种与工艺'),('description','酒款介绍')]:
                        add(wine,name,wid+'/'+name,label)
            elif kind=='speaker':
                reference_image(b['image'],'分享人照片');field('name','分享人姓名',heading=4);field('description','分享人介绍')
            elif kind=='callout':field('eyebrow','提示眉题');field('text','彩蛋提示')
            elif kind=='event':
                b.setdefault('heading','分享人 Lecturer')
                for name,label in [('heading','分享人栏目标题'),('speakers','分享人'),('speaker_roles','分享人身份'),('when','时间'),('where','地点'),('contact','联系电话')]:field(name,label)
                if b.get('horse'):reference_image(b['horse'],'马元素参考')
            elif kind=='notice':
                b.setdefault('heading','温馨提示');field('heading','提示标题',heading=3);field('text','报名须知')
            elif kind=='sponsor':
                b.setdefault('heading','特别鸣谢');field('heading','鸣谢标题',heading=3);field('thanks','致谢文字')
                if b.get('logo'):reference_image(b['logo'],'赞助方标志')
                field('paragraphs','赞助方介绍；空行分段',kind='paragraphs')
            elif kind=='responsible':reference_image(b['image'],'理性饮酒提示');field('text','理性饮酒说明')
            elif kind=='closing':field('lines','文末结语',kind='lines');field('brand','文末署名')

    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=directory/'history'/'markdown-migration';backup.mkdir(parents=True,exist_ok=True)
    (backup/(stamp+'-post.json')).write_bytes((directory/'post.json').read_bytes())
    if existing is not None:(backup/(stamp+'-正文.md')).write_bytes(existing.read_bytes())
    document['text_source']='正文.md';document['text_schema']=schema
    markdown='\n'.join(chunks)+'\n'
    parse_markdown(markdown,schema)
    (directory/'正文.md').write_text(markdown,encoding='utf-8')
    (directory/'post.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    launcher='@echo off\r\nchcp 65001 >nul\r\ncd /d "%~dp0\\..\\.."\r\npython -X utf8 scripts\\post_builder.py serve "'+directory.name+'" --open\r\nif errorlevel 1 pause\r\n'
    (directory/'开始编辑.cmd').write_bytes(launcher.encode('utf-8'))
    stop='@echo off\r\nchcp 65001 >nul\r\ncd /d "%~dp0\\..\\.."\r\npython -X utf8 scripts\\post_builder.py stop "'+directory.name+'"\r\nif errorlevel 1 pause\r\n'
    (directory/'停止预览.cmd').write_bytes(stop.encode('utf-8'))
    return directory/'正文.md'
