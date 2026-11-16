"""Compose the original C illumination with unchanged verified vector geography."""
from pathlib import Path
import base64
import copy
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape,box
from shapely.affinity import affine_transform
from PIL import ImageFont

ROOT=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
OUT=Path(r'C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs')
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
def element(name,attributes=None):
    return ET.Element(f'{{{NS}}}{name}',attributes or {})
def read(path):return json.loads(path.read_text(encoding='utf8'))

source=ET.parse(ROOT/'nuits-professional-02.svg').getroot()
original=copy.deepcopy(source)
art_source=Path(r'C:/Users/32697/.codex/generated_images/01a1cf3f-b916-7802-9022-320fcc520ddd/exec-c8da96f2-7194-4246-abaf-8181087aebbe.png')
art=ROOT/'styles/Nuits-style-C-04-frame.png'
if not art.exists():
    shutil.copy2(art_source,art)
grove=ROOT/'styles/Nuits-style-C-04-woodland.png'
if not grove.exists():
    shutil.copy2(Path(r'C:/Users/32697/.codex/generated_images/01a1cf3f-b916-7802-9022-320fcc520ddd/exec-87e9e0a8-2938-4845-87e6-25b7f22a7502.png'),grove)
paper='#f4ebd2'

# Remove the old page furniture. Every map path, label position and scale stays in its original coordinate system.
for child in list(source):
    tag=child.tag.split('}')[-1]
    if tag=='text':
        y=float(child.get('y','0'))
        if y<82 or y>794:source.remove(child)
    elif tag=='rect':
        if child.get('width')=='600' or child.get('x')=='13' or float(child.get('y','0'))>=805:
            source.remove(child)
    elif tag=='path':
        numbers=[float(value) for value in re.findall(r'-?\d+(?:\.\d+)?',child.get('d',''))]
        if numbers and (min(numbers[1::2])>=805 or max(numbers[1::2])<=81):source.remove(child)

# Recolor linework only. Cadastral outlines and all other geometry remain untouched.
recolors={'#f8f5e9':paper,'#d9dfc9':'#d7d9b8','#777168':'#876e50',
          '#a5b28e':'#a3af81','#834954':'#904c58','#c9a15e':'#c7a15f'}
for node in source.iter():
    for key,value in list(node.attrib.items()):
        if value in recolors:node.set(key,recolors[value])
    if node.tag.endswith('style') and node.text:
        node.text=node.text.replace('#f8f5e9',paper)
source.find(f'{{{NS}}}title').text='Côte de Nuits — Terres de légende'
source.find(f'{{{NS}}}desc').text='Carte géographique vérifiée, orientée au nord, 73 premiers crus nommés sur la carte principale, ornements inspirés des manuscrits enluminés.'
body=element('g',{'id':'cartographic-body','transform':'translate(30,40) scale(.9)'})
for child in list(source):
    if child.tag.split('}')[-1] not in ['defs','title','desc','style']:
        source.remove(child);body.append(child)
source.append(body)
for node in body.iter(f'{{{NS}}}text'):
    node.set('font-size',str(max(3.53,float(node.get('font-size','3.53')))))

defs=source.find(f'{{{NS}}}defs')
assets=ET.fromstring('''<defs xmlns="http://www.w3.org/2000/svg">
<g id="church-symbol">
 <path d="M-2.4,0V-2.5L-.4,-3.6 1.7,-2.5V0Z" fill="#ecddaf" stroke="#8c7651" stroke-width=".17"/>
 <path d="M-2.6,-2.5L-.4,-4 1.9,-2.5 .2,-2.2Z" fill="#a65e44" stroke="#8c7651" stroke-width=".17"/>
 <path d="M1,0V-4H2.7V0Z" fill="#e8d5a5" stroke="#8c7651" stroke-width=".17"/>
 <path d="M.8,-4L1.85,-6.3 2.9,-4Z" fill="#776447" stroke="#695b45" stroke-width=".17"/>
 <path d="M-.7,0V-1.4H0V0M1.5,-2.6V-3.3H2.1V-2.6" fill="#7a6c53"/>
</g>
<pattern id="woodland-engraving" patternUnits="userSpaceOnUse" width="64" height="48"/>
<pattern id="vineyard-engraving" patternUnits="userSpaceOnUse" width="4" height="5">
 <path d="M.6,0L.6,5M2.6,0L2.6,5M.2,1.4l.4,.45 .4,-.45M2.2,3.5l.4,.45 .4,-.45" fill="none" stroke="#fff0c3" stroke-width=".12"/>
</pattern>
</defs>''')
for child in assets:defs.append(child)
pattern=defs.find(f'{{{NS}}}pattern[@id="woodland-engraving"]')
defs.append(element('image',{'id':'woodland-grove','width':'18','height':'12','href':'data:image/png;base64,'+base64.b64encode(grove.read_bytes()).decode()}))
for x,y,width in [(0,0,18),(20,3,21),(44,-1,22),(8,17,24),(35,19,22),(54,27,20),(-4,35,25),(25,37,21)]:
    pattern.append(element('use',{'href':'#woodland-grove','transform':f'translate({x},{y}) scale({width/18:.3f})'}))

for key in ['cote','gevrey','vosne']:
    forest=source.find(f'.//{{{NS}}}g[@id="forest-{key}"]')
    for path in list(forest):
        overlay=copy.deepcopy(path)
        overlay.attrib={'d':path.get('d'),'fill':'url(#woodland-engraving)','fill-opacity':'.78','stroke':'none'}
        forest.append(overlay)
    for group_name in ['appellation-fills','premier-cru-parcels','grand-cru-parcels']:
        group=source.find(f'.//{{{NS}}}g[@id="{group_name}-{key}"]')
        for path in list(group):
            if path.get('fill') in [None,'none']:continue
            overlay=copy.deepcopy(path)
            overlay.attrib={'d':path.get('d'),'fill':'url(#vineyard-engraving)','fill-rule':'evenodd','fill-opacity':'.4','stroke':'none'}
            group.append(overlay)

layout=read(ROOT/'checks/nuits-professional-02-labels.json')
church_count=0
for key in ['cote','gevrey','vosne']:
    panel=layout['panels'][key];x,y,w,h=panel['map'];clip=box(x,y,x+w,y+h)
    occupied=[box(*label['bounds']).buffer(1.2) for label in layout['label_boxes'] if label['panel']==key]
    if key=='cote':occupied.append(box(29,98,161,277))
    group=element('g',{'id':f'church-symbols-{key}'})
    for feature in read(ROOT/'sources/professional/buildings.geojson')['features']:
        p=feature['properties']
        if p.get('nature')!='Eglise' or p.get('etat_de_l_objet')!='En service':continue
        point=affine_transform(shape(feature['geometry']),panel['matrix']).representative_point()
        symbol_bounds=box(point.x-2.6,point.y-6.3,point.x+2.9,point.y)
        if not clip.contains(symbol_bounds) or any(symbol_bounds.intersects(label) for label in occupied):continue
        group.append(element('use',{'href':'#church-symbol','transform':f'translate({point.x:.2f},{point.y:.2f})','data-source-id':p['cleabs']}))
        church_count+=1
    source.find(f'.//{{{NS}}}g[@id="geography-{key}"]').append(group)

image_data='data:image/png;base64,'+base64.b64encode(art.read_bytes()).decode()
background=element('g',{'id':'illuminated-page'})
background.append(element('rect',{'width':'600','height':'900','fill':paper}))
background.append(element('image',{'width':'600','height':'900','href':image_data}))
# Opaque warm paper behind geography avoids shading from the frame asset's alpha transition.
background.append(element('rect',{'x':'27','y':'115','width':'546','height':'662','fill':paper}))
source.insert(list(source).index(defs)+1,background)

def text(x,y,value,size=3.2,anchor='start',color='#5a4e3c',italic=False):
    attrs={'x':str(x),'y':str(y),'font-size':str(size),'text-anchor':anchor,'fill':color}
    if italic:attrs['font-style']='italic'
    node=element('text',attrs);node.text=value;source.append(node)
def line(x,y,length,color,width=.3,dash=None):
    attrs={'d':f'M{x},{y}h{length}','fill':'none','stroke':color,'stroke-width':str(width)}
    if dash:attrs['stroke-dasharray']=dash
    source.append(element('path',attrs))

text(300,66,'TERRES DE LÉGENDE',12.8,'middle','#8c3e34',True)
text(300,87,'CÔTE DE NUITS',8.4,'middle','#3b4b51')

# Compact legend above the separately scaled footer illustration.
for x,color,label in [(30,'#904c58','Grand cru'),(110,'#c7a15f','Premier cru'),(206,'#a3af81','Village'),(280,'#e9e5d8','Régionale'),(374,'#d7d9b8','Forêt'),(445,'#876e50','Bâti')]:
    source.append(element('rect',{'x':str(x),'y':'756','width':'6','height':'3.4','fill':color,'stroke':'#887855','stroke-width':'.12'}))
    text(x+9,759.3,label)
line(503,758,9,'#7799a0');text(515,759.3,'Cours d’eau')
line(30,766,10,'#566f51');text(43,767.2,'Aire AOC')
line(108,766,10,'#727b83',.25,'2,.7,.35,.7');text(121,767.2,'Commune')
line(205,766,10,'#9c8766');text(218,767.2,'Courbes 25 m · détails 10 m')
line(392,766,10,'#787777',.65);line(392,766,10,paper,.28,'1.5,1.3');text(405,767.2,'Voie ferrée')
line(503,766,10,'#9d8b70',.7);line(503,766,10,'#fff9e9',.4);text(516,767.2,'Route')
text(300,775,'Atlas mondial du vin, 8e éd., p. 64–67 · INAO / IGN / DGFiP–Etalab · Licence Ouverte 2.0 · Textures figuratives',2.85,'middle','#71634d')

# All source paths must survive exactly, alongside the added illustrative texture copies.
path_checks={}
for key in ['cote','gevrey','vosne']:
    before=original.find(f'.//{{{NS}}}g[@id="geography-{key}"]')
    after=source.find(f'.//{{{NS}}}g[@id="geography-{key}"]')
    before_paths=[node.get('d') for node in before.iter(f'{{{NS}}}path')]
    after_paths={node.get('d') for node in after.iter(f'{{{NS}}}path')}
    assert all(value in after_paths for value in before_paths)
    path_checks[key]={'original_paths_retained':len(before_paths),'all_geometry_preserved':True}
labels=read(ROOT/'checks/nuits-professional-02-labels.json')['label_boxes']
texts={(node.text,node.get('x'),node.get('y')) for node in source.iter(f'{{{NS}}}text')}
missing=[]
for label in labels:
    if not any(node.text==label['text'] and abs(float(node.get('x','-1'))-label['x_mm'])<.02 and abs(float(node.get('y','-1'))-label['y_mm'])<.02
               for node in source.iter(f'{{{NS}}}text')):
        missing.append(label['text'])
assert not missing,missing
fonts={name:ImageFont.truetype('C:/Windows/Fonts/'+file,1000) for name,file in [('regular','georgia.ttf'),('italic','georgiai.ttf'),('bold','georgiab.ttf')]}
measured=[]
for label in labels:
    node=next(node for node in body.iter(f'{{{NS}}}text') if node.text==label['text'] and abs(float(node.get('x','-1'))-label['x_mm'])<.02 and abs(float(node.get('y','-1'))-label['y_mm'])<.02)
    size=float(node.get('font-size'));style='italic' if node.get('font-style')=='italic' else 'bold' if node.get('font-weight')=='bold' else 'regular'
    width=fonts[style].getlength(label['text'])/1000*size;x=float(node.get('x'));y=float(node.get('y'));anchor=node.get('text-anchor')
    left=x-width if anchor=='end' else x-width/2 if anchor=='middle' else x
    measured.append({'panel':label['panel'],'text':label['text'],'bounds':box(left,y-size*.85,left+width,y+size*.25),'size_pt':size*.9*72/25.4})
collisions=[(a['text'],b['text']) for i,a in enumerate(measured) for b in measured[i+1:] if a['panel']==b['panel'] and a['bounds'].intersection(b['bounds']).area>.4]
assert not collisions,collisions
markup=ET.tostring(source,encoding='unicode')
(ROOT/'nuits-C-precise-01.svg').write_text(markup,encoding='utf8')
(ROOT/'nuits-C-precise-01.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Côte de Nuits · Terres de légende</title><style>body{margin:0;background:#e2d4b7}svg{display:block;width:100%;height:auto}</style>'+markup,encoding='utf8')
report={'version':'nuits-C-precise-01','geography_base':'nuits-professional-02.svg','style_reference':'original C from Nuits-styles-ABCD-01.png',
        'path_checks':path_checks,'source_label_count':len(labels),'source_label_positions_preserved':not missing,
        'main_premier_count':73,'north_up_and_scales':'Uniform page-layout scale 0.9; north and distance scales remain consistent',
        'page_layout_transform':{'scale':.9,'translation_mm':[30,40]},'church_symbols_at_IGN_locations':church_count,
        'illustration':'Raster manuscript frame and woodland symbols; vector vineyard textures; forest and vineyard fills clipped to source polygons.',
        'label_collisions':collisions,'minimum_map_font_pt':min(item['size_pt'] for item in measured),
        'secondary_icon':'Saint Vincent retained per earlier user request',
        'limitations':['Tree and vine-row symbols are illustrative textures, not individual surveyed trees or row directions.',
                       'Frame figures are newly drawn in original C style.','Charmes/Mazoyeres share the mapped AOC extent; internal climat division remains unverified.'],
        'frame_sha256':hashlib.sha256(art.read_bytes()).hexdigest()}
(ROOT/'checks/nuits-C-precise-01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
