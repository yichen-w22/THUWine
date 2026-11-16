"""Add source-backed vineyard labels to the approved static map without redrawing geography."""
from pathlib import Path
import copy
import html
import json
import math
import sys
import xml.etree.ElementTree as ET

ROOT=Path('C:/Users/32697/Desktop/thuwine/map_builder')
WORK=Path('C:/Users/32697/Documents/Codex/2026-11-12/wo/work')
sys.path.insert(0,str(WORK/'gislibs'))
from PIL import ImageFont
from shapely.geometry import shape,box,Point,LineString
from shapely.affinity import affine_transform

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

SELECTION={
 'Fixin':['Arvelets','Les Meix Bas'],
 'Gevrey-Chambertin':['Clos des Varoilles','Estournelles-Saint-Jacques','Les Goulots','Poissenot','La Romanée','Champonnet','Craipillot','Les Corbeaux','Fonteny'],
 'Morey-Saint-Denis':['Les Ruchots','Les Blanchards','Les Faconnières','Clos des Ormes','Les Sorbès','La Riotte'],
 'Chambolle-Musigny':['Les Sentiers','Les Feusselottes ou Les Feusselotes','Les Chatelots','Les Gruenchers','Les Hauts Doix','Les Borniques','Aux Beaux Bruns'],
 'Vougeot':['Les Crâs'],
 'Vosne-Romanée':['Clos des Réas','Les Chaumes'],
 'Nuits-Saint-Georges':['Les Pruliers','Les Damodes','Aux Chaignots','Aux Thorey','Aux Bousselots','Aux Vignerondes','Les Perrières','Les Didiers','Clos des Forêts Saint-Georges','Clos des Porrets-Saint-Georges','Clos des Corvées','Clos des Argillières','Clos des Grandes Vignes','Rue de Chaux'],
}
ALIASES={'Arvelets':'Les Arvelets','Les Feusselottes ou Les Feusselotes':'Les Feusselottes'}
report=read(ROOT/'checks/nuits-professional-01.json')
labels=copy.deepcopy(report['label_boxes'])
for label in labels:label['geometry']=box(*label['bounds'])
leaders=copy.deepcopy(report['leaders'])
for leader in leaders:leader['geometry']=LineString([leader['start'],leader['end']])
font=ImageFont.truetype('C:/Windows/Fonts/georgiai.ttf',1000)
svg=ET.parse(ROOT/'nuits-professional-01.svg').getroot()
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
new_group=ET.SubElement(svg,f'{{{NS}}}g',{'id':'additional-vineyard-labels'})
added=[]
deferred=[]
forbidden=box(29,98,161,277)

def xy(panel,coordinate):
    a,b,d,e,x,y=report['panels'][panel]['matrix']
    return a*coordinate[0]+b*coordinate[1]+x,d*coordinate[0]+e*coordinate[1]+y

def add_label(panel,name,geometry,kind,source_name,source,village):
    matrix=report['panels'][panel]['matrix']
    map_box=report['panels'][panel]['map']
    clip=box(map_box[0],map_box[1],map_box[0]+map_box[2],map_box[1]+map_box[3])
    projected=affine_transform(geometry,matrix).intersection(clip)
    if projected.is_empty:return False
    bounds=box(28,97,375,782) if panel=='cote' else clip.buffer(2)
    occupied=[label['geometry'].buffer(.55) for label in labels if label['panel']==panel]
    prior_lines=[leader['geometry'] for leader in leaders if leader['panel']==panel]
    points=[projected.representative_point()]
    if projected.geom_type!='Point':
        left,bottom,right,top=projected.bounds
        points += [Point(left+(right-left)*fx,bottom+(top-bottom)*fy)
                   for fx in [.25,.5,.75] for fy in [.25,.5,.75]
                   if projected.contains(Point(left+(right-left)*fx,bottom+(top-bottom)*fy))]
    size=3.55 if kind=='premier' else 3.65
    width=font.getlength(name)/1000*size
    candidates=[]
    for point in points:
        if any(area.contains(point) for area in occupied):continue
        for side in [-1,1]:
            for distance in [5,8,12,18,25,32]:
                for dy in [0,-5,5,-10,10,-16,16,-22,22]:
                    length=math.hypot(distance-1,dy)
                    if length>33:continue
                    candidates.append((length+(1 if side==1 else 0),point,side,distance,dy))
    candidates.sort(key=lambda item:item[0])
    for _,point,side,distance,dy in candidates:
        x=point.x+side*distance;y=point.y+dy+1
        left=x-width if side<0 else x
        rectangle=box(left,y-size*.85,left+width,y+size*.25)
        line_end=[x-side,y-1]
        line=LineString([(point.x,point.y),line_end])
        if not bounds.contains(rectangle):continue
        if panel=='cote' and (rectangle.intersects(forbidden) or line.intersects(forbidden)):continue
        if any(rectangle.intersects(area) or line.intersects(area) for area in occupied):continue
        if any(rectangle.buffer(.5).intersects(previous) or line.crosses(previous) for previous in prior_lines):continue
        color='#6e512e' if kind=='premier' else '#4e6748'
        ET.SubElement(new_group,f'{{{NS}}}path',{'d':f'M{point.x:.2f},{point.y:.2f}L{line_end[0]:.2f},{line_end[1]:.2f}',
            'fill':'none','stroke':color,'stroke-width':'.2'})
        ET.SubElement(new_group,f'{{{NS}}}circle',{'cx':f'{point.x:.2f}','cy':f'{point.y:.2f}','r':'.45','fill':color})
        element=ET.SubElement(new_group,f'{{{NS}}}text',{'x':f'{x:.2f}','y':f'{y:.2f}','font-size':str(size),
            'text-anchor':'end' if side<0 else 'start','font-style':'italic','fill':color,'class':'halo'})
        element.text=name
        record={'text':name,'panel':panel,'kind':kind,'bounds':list(rectangle.bounds),'size_mm':size,'x_mm':x,'y_mm':y,
                'village':village,'source_name':source_name,'source':source,'point_xy_mm':[point.x,point.y]}
        labels.append(dict(record,geometry=rectangle))
        leaders.append({'panel':panel,'label':name,'start':[point.x,point.y],'end':line_end,'length_mm':line.length,'geometry':line})
        added.append(record)
        return True
    deferred.append({'panel':panel,'name':name,'village':village,'source_name':source_name,'reason':'No available collision-free label position'})
    return False

all_premiers=read(ROOT/'data/nuits_all_named_premiers.geojson')['features']
chosen=[feature for feature in all_premiers if feature['properties']['name'] in SELECTION.get(feature['properties']['village'],[])]
# Larger parcels first leave adequate space for names of the smaller neighboring plots.
chosen.sort(key=lambda feature:-shape(feature['geometry']).area)
for feature in chosen:
    p=feature['properties'];name=ALIASES.get(p['name'],p['name'])
    add_label('cote',name,shape(feature['geometry']),'premier',p['source_name'],p['source'],p['village'])

# Book p. 67 names these Marsannay lieux-dits; IGN provides validated locations.
marsannay=next(shape(f['geometry']) for f in read(ROOT/'data/nuits_village_appellations.geojson')['features'] if f['properties']['name']=='Marsannay')
village_names={'le Clos du Roy':'Clos du Roy','les Grasses Têtes':'Les Grasses Têtes','les Favières':'Les Favières'}
for feature in read(ROOT/'sources/professional/lieux_dits.geojson')['features']:
    p=feature['properties']
    if p['toponyme'] not in village_names:continue
    geometry=shape(feature['geometry'])
    assert p['statut_du_toponyme']=='Validé' and marsannay.buffer(30).contains(geometry)
    add_label('cote',village_names[p['toponyme']],geometry,'village_climat',p['toponyme'],
              'IGN BD TOPO named point; book p. 67; location only','Marsannay')

total_main=36+sum(label['kind']=='premier' and label['panel']=='cote' for label in added)
for text in svg.iter(f'{{{NS}}}text'):
    if text.text=='36 PREMIERS CRUS SÉLECTIONNÉS':text.text=f'{total_main} PREMIERS CRUS SUR LA CARTE PRINCIPALE'
svg.find(f'{{{NS}}}desc').text=f'Carte orientée au nord, {total_main} premiers crus sur la carte principale, 24 appellations grands crus, relief IGN et deux agrandissements.'
markup=ET.tostring(svg,encoding='unicode')
(ROOT/'nuits-professional-02.svg').write_text(markup,encoding='utf-8')
(ROOT/'nuits-professional-02.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Côte de Nuits</title><style>body{margin:0;background:#e8e4d6}svg{display:block;width:100%;height:auto}</style>'+markup,encoding='utf-8')
overlaps=[]
crossings=[]
for i,label in enumerate(labels):
    for other in labels[i+1:]:
        if label['panel']==other['panel'] and label['geometry'].intersection(other['geometry']).area>.4:
            overlaps.append([label['text'],other['text']])
for i,leader in enumerate(leaders):
    for other in leaders[i+1:]:
        if leader['panel']==other['panel'] and leader['geometry'].crosses(other['geometry']):
            crossings.append([leader['label'],other['label']])
assert not overlaps and not crossings
result={'version':'nuits-professional-02','main_premier_count':total_main,'added_labels':added,'deferred':deferred,
        'label_boxes':[{k:v for k,v in item.items() if k!='geometry'} for item in labels],
        'leaders':[{k:v for k,v in item.items() if k!='geometry'} for item in leaders],
        'panels':report['panels'],'minimum_added_font_pt':3.55*72/25.4,
        'text_collisions':overlaps,'leader_crossings':crossings}
(ROOT/'checks/nuits-professional-02-labels.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'main_premier_count':total_main,'added':[(x['village'],x['text']) for x in added],
                  'deferred':deferred},ensure_ascii=False,indent=2))
