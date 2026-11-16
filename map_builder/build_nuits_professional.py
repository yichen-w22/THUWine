"""Deterministic north-up SVG atlas with sourced terrain and named vineyard geometry."""
from pathlib import Path
from collections import Counter, defaultdict
import base64
import html
import io
import json
import math
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUT = Path(r'C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs')
sys.path.insert(0, r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageFont
from shapely import make_valid
from shapely.geometry import shape, box, Point, LineString
from shapely.affinity import affine_transform
from shapely.ops import unary_union

DATA = ROOT/'data'
CACHE = ROOT/'sources/professional'
COLORS = {'regional':'#e9e5d8','village':'#a5b28e','premier':'#c9a15e','grand':'#834954'}
FONT = {'regular':ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',1000),
        'italic':ImageFont.truetype('C:/Windows/Fonts/georgiai.ttf',1000),
        'bold':ImageFont.truetype('C:/Windows/Fonts/georgiab.ttf',1000)}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def features(path):
    output=[]
    for feature in read(path)['features']:
        geometry=make_valid(shape(feature['geometry']))
        if not geometry.is_empty:
            output.append((geometry,feature['properties']))
    return output

old=read(ROOT/'layout-nuits-atlas-04.json')
panels={}
for key,frame,map_box in [
    ('cote',[24,86,552,708],[30,96,346,690]),
    ('gevrey',[380,100,190,310],[387,127,176,246]),
    ('vosne',[380,425,190,355],[387,452,176,296]),
]:
    source=old[key]
    left,bottom,right,top=source['bounds']
    x,y,width,height=map_box
    if key=='cote':
        factor=source['factor']
        offset=[source['offset'][0]-107.5,source['offset'][1]+4]
    else:
        factor=min(width/(right-left),height/(top-bottom))
        offset=[x+(width-factor*(right-left))/2,y+(height-factor*(top-bottom))/2]
    theta=math.radians(source['rotation'])
    a,b=factor*math.cos(theta),-factor*math.sin(theta)
    d,e=-factor*math.sin(theta),-factor*math.cos(theta)
    ox,oy=source['origin']
    matrix=[a,b,d,e,offset[0]-left*factor-a*ox-b*oy,offset[1]+top*factor-d*ox-e*oy]
    panels[key]={'frame':frame,'map':map_box,'matrix':matrix,'factor':factor,
                 'rotation':source['rotation'],'bounds':source['bounds'],'origin':source['origin']}
    determinant=a*e-b*d
    inverse=[e/determinant,-b/determinant,-d/determinant,a/determinant,
             (b*matrix[5]-e*matrix[4])/determinant,(d*matrix[4]-a*matrix[5])/determinant]
    panels[key]['clip']=box(x,y,x+width,y+height)
    panels[key]['geographic_clip']=affine_transform(panels[key]['clip'],inverse)

areas=features(DATA/'appellations_l93.geojson')
grands=features(DATA/'grands_crus_l93.geojson')
selected=features(DATA/'nuits_professional_premiers.geojson')
all_premiers=features(DATA/'nuits_all_named_premiers.geojson')
appellations=features(DATA/'nuits_village_appellations.geojson')
context={name:features(CACHE/f'{name}.geojson') for name in
         ['roads','railways','forest','buildings','communes','contours','places','toponyms','lieux_dits','local_water']}
context['communes']=features(CACHE/'cadastral_communes_l93.geojson')
main_grands={name for name in old['gevrey']['names']+old['vosne']['names']}
main_grands.update(['Clos de la Roche','Clos Saint-Denis','Clos des Lambrays','Clos de Tart','Bonnes-Mares','Musigny','Clos de Vougeot'])
forest=unary_union([g for g,p in context['forest'] if p['nature'] in ['Bois','Forêt fermée de feuillus','Forêt fermée mixte','Forêt fermée de conifères','Forêt ouverte','Peupleraie']])
regional_mask=box(839000,6666500,844600,6674500)

def xy(panel,coordinate):
    a,b,d,e,tx,ty=panel['matrix']
    return a*coordinate[0]+b*coordinate[1]+tx,d*coordinate[0]+e*coordinate[1]+ty

protected_points={key:[] for key in panels}
detailed_grands=set(old['gevrey']['names']+old['vosne']['names'])
for key,panel in panels.items():
    if key=='cote':
        candidates=selected+[(g,p) for g,p in grands if p['name'] in main_grands and p['name'] not in detailed_grands]
        protected_points[key]=[Point(xy(panel,p['label_xy'])) for _,p in candidates]
    else:
        for geometry,properties in all_premiers:
            clipped=geometry.intersection(panel['geographic_clip'])
            if clipped.area>=3500 and clipped.area/geometry.area>=.25:
                protected_points[key].append(Point(xy(panel,clipped.representative_point().coords[0])))

def projected(panel,geometry):
    if not geometry.intersects(panel['geographic_clip']):
        return None
    return affine_transform(geometry.intersection(panel['geographic_clip']),panel['matrix']).intersection(panel['clip'])

def path(geometry):
    if geometry is None or geometry.is_empty:
        return ''
    def ring(coordinates,closed):
        return 'M'+'L'.join(f'{p[0]:.2f},{p[1]:.2f}' for p in coordinates)+('Z' if closed else '')
    if geometry.geom_type=='Polygon':
        return ring(geometry.exterior.coords,True)+''.join(ring(interior.coords,True) for interior in geometry.interiors)
    if geometry.geom_type in ['LineString','LinearRing']:
        return ring(geometry.coords,False)
    if hasattr(geometry,'geoms'):
        return ''.join(path(part) for part in geometry.geoms)
    return ''

parts=[]
labels=[]
counts=defaultdict(Counter)
leaders=[]
deferred_labels=[]

def add(markup):
    parts.append(markup)

def draw(geometry,attributes):
    data=path(geometry)
    if data:
        add(f'<path d="{data}" {attributes}/>')

def text_bounds(x,y,value,size,anchor,font):
    width=FONT[font].getlength(value)/1000*size
    left=x-width if anchor=='end' else x-width/2 if anchor=='middle' else x
    return box(left,y-size*.85,left+width,y+size*.25)

def available(bounds,panel,padding=.7,protect_anchors=False):
    if panel=='cote':
        limits=box(27,91,376,782)
        if bounds.intersects(box(29,98,161,277)):
            return False
    else:
        x,y,w,h=panels[panel]['frame']
        limits=box(x+3,y+24,x+w-3,y+h-32)
    padded=bounds.buffer(padding)
    if protect_anchors and any(padded.contains(point) for point in protected_points[panel]):
        return False
    return (limits.contains(bounds)
            and all(not padded.intersects(label['bounds']) for label in labels if label['panel']==panel)
            and all(not padded.intersects(LineString([leader['start'],leader['end']]))
                    for leader in leaders if leader['panel']==panel))

def txt(x,y,value,size=3.6,anchor='start',font='regular',color='#403d32',panel='',kind='',halo=True):
    bounds=text_bounds(x,y,value,size,anchor,font)
    css='font-style="italic"' if font=='italic' else 'font-weight="bold"' if font=='bold' else ''
    add(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" {css} class="{"halo" if halo else ""}">{html.escape(value)}</text>')
    if panel:
        labels.append({'text':value,'panel':panel,'kind':kind,'bounds':bounds,'size_mm':size,
                       'x_mm':x,'y_mm':y,'anchor':anchor,'font':font,
                       'priority':{'grand':1,'village':2,'premier':3,'river':4,'landscape':5,'road':6,'elevation':7}[kind]})
    return bounds

def line(x,y,end_x,end_y,color='#7f745e',width=.22,dash=''):
    add(f'<path d="M{x:.2f},{y:.2f}L{end_x:.2f},{end_y:.2f}" fill="none" stroke="{color}" stroke-width="{width}" {dash}/>')

def scale_bar(panel,key,length):
    x,y,w,h=panel['frame']
    sx,sy=(35,788) if key=='cote' else (x+9,y+h-11)
    sl=length*panel['factor']
    line(sx,sy,sx+sl,sy,'#4d5142',.38)
    for px in [sx,sx+sl/2,sx+sl]:
        line(px,sy-1,px,sy+1,'#4d5142',.25)
    txt(sx,sy-2.2,'0',3.2)
    txt(sx+sl,sy-2.2,f'{length//1000} km' if length>=1000 else f'{length} m',3.2,'end')
    nx,ny=(365,113) if key=='cote' else (x+w-10,y+h-11)
    add(f'<path d="M{nx},{ny-6}l-1.5,6 1.5,-1.2 1.5,1.2Z" fill="#48533e"/>')
    txt(nx,ny-8,'N',3.2,'middle')

def hillshade():
    elevation=np.fromfile(CACHE/'dem_20m.bil',dtype='<f4').reshape(1110,550)
    smooth=gaussian_filter(elevation,.8)
    dy,dx=np.gradient(smooth,20,20)
    normal=np.sqrt(1+dx*dx+dy*dy)
    illumination=(-.5*dx-.5*dy+.707)/normal
    alpha=np.clip((.86-illumination)*65,0,35).astype('uint8')
    rgba=np.zeros((1110,550,4),dtype='uint8')
    rgba[:,:,:3]=[104,94,72]
    rgba[:,:,3]=alpha
    stream=io.BytesIO()
    Image.fromarray(rgba).save(stream,format='PNG')
    return base64.b64encode(stream.getvalue()).decode()

shade=hillshade()
add('''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="600mm" height="900mm" viewBox="0 0 600 900" role="img" aria-labelledby="map-title map-desc">
<title id="map-title">Côte de Nuits — climats, relief et appellations</title>
<desc id="map-desc">Carte orientée au nord, 36 premiers crus sélectionnés, 24 appellations grands crus, relief IGN et deux agrandissements.</desc>
<defs><style>text{font-family:Georgia,serif}.halo{paint-order:stroke;stroke:#f8f5e9;stroke-width:.85;stroke-linejoin:round}path{stroke-linejoin:round;stroke-linecap:round}</style>''')
for key,panel in panels.items():
    x,y,w,h=panel['map']
    add(f'<clipPath id="clip-{key}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>')
add('</defs><rect width="600" height="900" fill="#f8f5e9"/><rect x="13" y="13" width="574" height="874" fill="none" stroke="#7b7c61" stroke-width=".55"/>')
txt(300,32,'BOURGOGNE',4.5,'middle',color='#697151')
txt(300,58,'CÔTE DE NUITS',22,'middle',color='#364b3b')
txt(300,73,'Climats, relief et appellations · De Marsannay à Premeaux-Prissey',4.5,'middle','italic',color='#696a54')
line(25,81,575,81)

def render_base(key,panel):
    x,y,w,h=panel['frame']
    if key!='cote':
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f8f5e9" stroke="#868067" stroke-width=".35"/>')
    add(f'<g id="geography-{key}" clip-path="url(#clip-{key})">')
    add(f'<g id="forest-{key}">')
    g=projected(panel,forest)
    draw(g,'fill="#d9dfc9" fill-opacity=".64" stroke="#aab693" stroke-width=".15"')
    add('</g>')
    a,b,d,e,_,_=panel['matrix'];sx,sy=xy(panel,[843000,6690400])
    add(f'<image id="hillshade-{key}" width="11000" height="22200" transform="matrix({a},{d},{-b},{-e},{sx},{sy})" href="data:image/png;base64,{shade}"/>')
    add(f'<g id="appellation-fills-{key}">')
    for geometry,properties in areas:
        category=properties['class']
        if category=='neighbour' or category=='grand':
            continue
        if key=='cote' and category=='regional':
            geometry=geometry.difference(regional_mask)
        g=projected(panel,geometry)
        draw(g,f'fill="{COLORS[category]}" fill-rule="evenodd" fill-opacity="{.88 if key=="cote" else .72}"')
    add(f'</g><g id="premier-cru-parcels-{key}">')
    for geometry,properties in all_premiers:
        g=projected(panel,geometry)
        draw(g,'fill="none" stroke="#9f814f" stroke-width=".18"')
    for geometry,properties in selected:
        g=projected(panel,geometry)
        draw(g,'fill="#caa05a" fill-opacity=".8" stroke="#94713f" stroke-width=".28"')
        if g is not None and not g.is_empty:
            counts[key]['selected_premier_polygons']+=1
    # Trace each legal grand-cru area; coincident Charmes/Mazoyeres is painted once.
    add(f'</g><g id="grand-cru-parcels-{key}">')
    for geometry,properties in grands:
        if properties['name'] not in main_grands or properties['name']=='Mazoyères-Chambertin':
            continue
        g=projected(panel,geometry)
        draw(g,f'fill="{COLORS["grand"]}" fill-rule="evenodd" stroke="#f3e3d1" stroke-width=".23" data-name="{html.escape(properties["name"])}"')
    add(f'</g><g id="contours-{key}">')
    for geometry,properties in context['contours']:
        elevation=int(properties['altitude'])
        interval=25 if key=='cote' else 10
        if elevation%interval:
            continue
        g=projected(panel,geometry)
        major=elevation%(100 if key=='cote' else 50)==0
        draw(g,f'fill="none" stroke="#9c8766" stroke-opacity="{.65 if major else .40}" stroke-width="{.26 if major else .13}"')
        if g is not None and not g.is_empty:
            counts[key]['contour_segments']+=1
    # Two visibly different, independently sourced types of geographic boundary.
    add(f'</g><g id="administrative-boundaries-{key}">')
    administrative=unary_union([g.boundary for g,p in context['communes']])
    draw(projected(panel,administrative),'fill="none" stroke="#727b83" stroke-width=".25" stroke-dasharray="2,.7,.35,.7" stroke-opacity=".8"')
    add(f'</g><g id="aoc-boundaries-{key}">')
    for geometry,properties in appellations:
        draw(projected(panel,geometry.boundary),'fill="none" stroke="#566f51" stroke-opacity=".6" stroke-width=".22"')
    add(f'</g><g id="roads-{key}">')
    for geometry,properties in context['roads']:
        nature=properties['nature'];number=properties.get('cpx_numero') or ''
        if properties.get('etat_de_l_objet')!='En service':
            continue
        if key=='cote' and not number and nature not in ['Route à 1 chaussée','Route à 2 chaussées']:
            continue
        if key!='cote' and nature in ['Sentier','Escalier']:
            continue
        g=projected(panel,geometry)
        if g is None or g.is_empty:
            continue
        major=number in ['D974','M974']
        width=.65 if major else .43 if number else .22
        draw(g,f'fill="none" stroke="#9d8b70" stroke-width="{width+.24}"')
        draw(g,f'fill="none" stroke="#fff9e9" stroke-width="{width}"')
        counts[key]['road_segments']+=1
    add(f'</g><g id="railways-{key}">')
    for geometry,properties in context['railways']:
        if properties['nature']!='Voie ferrée principale' or properties.get('etat_de_l_objet')!='En service':
            continue
        g=projected(panel,geometry)
        draw(g,'fill="none" stroke="#787777" stroke-width=".65"')
        draw(g,'fill="none" stroke="#f8f5e9" stroke-width=".28" stroke-dasharray="1.5,1.3"')
        if g is not None and not g.is_empty:counts[key]['railway_segments']+=1
    add(f'</g><g id="water-{key}">')
    for geometry,properties in context['local_water']:
        if properties.get('fictif') or properties.get('position_par_rapport_au_sol')=='-1':
            continue
        g=projected(panel,geometry)
        dash='stroke-dasharray="1.2,.7"' if properties.get('persistance')=='Intermittent' else ''
        draw(g,f'fill="none" stroke="#7799a0" stroke-width=".30" {dash}')
    add(f'</g><g id="buildings-{key}">')
    building_paths=[]
    for geometry,properties in context['buildings']:
        if properties.get('etat_de_l_objet')!='En service':continue
        g=projected(panel,geometry)
        if g is not None and not g.is_empty:
            building_paths.append(path(g.simplify(.025)))
            counts[key]['buildings']+=1
    add(f'<path d="{"".join(building_paths)}" fill="#777168" fill-opacity=".67"/>')
    add('</g></g>')

def place_label(panel,key,x,y,value,size=3.7,font='italic',color='#665034',side='left',kind='premier'):
    anchor='end' if side=='left' else 'start'
    sign=-1 if side=='left' else 1
    offsets=[0,-5,5,-10,10,-16,16,-22,22,-29,29,-36,36]
    positions=sorted([(distance,offset) for distance in [6,12,20,30,42,55] for offset in offsets],
                     key=lambda position:math.hypot(*position))
    for distance,offset in positions:
        tx,ty=x+sign*distance,y+offset+1
        bounds=text_bounds(tx,ty,value,size,anchor,font)
        if not available(bounds,key,protect_anchors=True):continue
        end=tx+1 if side=='left' else tx-1
        leader_geometry=LineString([(x,y),(end,ty-1)])
        if any(leader_geometry.intersects(label['bounds'].buffer(.35))
               for label in labels if label['panel']==key):
            continue
        line(x,y,end,ty-1,color,.2)
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".45" fill="{color}"/>')
        txt(tx,ty,value,size,anchor,font,color,key,kind)
        leaders.append({'panel':key,'label':value,'length_mm':math.hypot(end-x,ty-1-y),
                        'start':[x,y],'end':[end,ty-1]})
        return
    raise RuntimeError(f'Unable to place {key} label {value}')

def label_main(panel):
    town_names=['Marsannay-la-Côte','Couchey','Fixey','Fixin','Brochon','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Flagey-Echézeaux','Vosne-Romanée','Nuits-Saint-Georges','Premeaux-Prissey']
    for geometry,properties in context['places']:
        name=properties['toponyme']
        if name not in town_names:continue
        x,y=xy(panel,geometry.coords[0]);display=name.replace('Flagey-Echézeaux','Flagey-Échezeaux')
        size=4.25 if name in ['Couchey','Brochon','Fixey'] else 4.5
        add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".8" fill="#3f4839" stroke="#f8f5e9" stroke-width=".3"/>')
        for dy in [1,-4,6,-9,11]:
            bounds=text_bounds(x+3,y+dy,display,size,'start','bold')
            if available(bounds,'cote',protect_anchors=True):
                txt(x+3,y+dy,display,size,font='bold',panel='cote',kind='village')
                break
        else:place_label(panel,'cote',x,y,display,size,'bold','#403d32','right','village')
    names=[]
    for geometry,properties in selected:
        x,y=xy(panel,properties['label_xy'])
        names.append((y,x,properties['name'],'premier'))
    detailed=set(old['gevrey']['names']+old['vosne']['names'])
    for geometry,properties in grands:
        name=properties['name']
        if name not in main_grands or name in detailed:continue
        x,y=xy(panel,properties['label_xy'])
        names.append((y,x,name,'grand'))
    for y,x,name,category in sorted(names):
        place_label(panel,'cote',x,y,name,3.8 if category=='grand' else 3.65,'italic',
                    '#763c49' if category=='grand' else '#6e512e',kind=category)

def multiline_inside(key,geometry,name,lines):
    panel=panels[key]
    g=projected(panel,geometry)
    if g is None or g.is_empty:return False
    size=3.8;line_height=4.6
    xs=[g.representative_point().x,g.centroid.x]
    ys=[g.representative_point().y,g.centroid.y]
    for x,y in zip(xs,ys):
        for shift in [0,-5,5,-10,10,15,-15]:
            boxes=[text_bounds(x,y+shift+(i-(len(lines)-1)/2)*line_height,line,size,'middle','italic') for i,line in enumerate(lines)]
            if all(g.buffer(-.3).contains(bounds) and available(bounds,key,.5) for bounds in boxes):
                for i,line_text in enumerate(lines):
                    txt(x,y+shift+(i-(len(lines)-1)/2)*line_height,line_text,size,'middle','italic','#fff1da',key,'grand',False)
                return True
    return False

def label_inset(key,panel):
    line_breaks={
      'Chambertin-Clos de Bèze':['Chambertin-','Clos de Bèze'],
      'Romanée-Saint-Vivant':['Romanée-','Saint-Vivant'],
      'Grands Échezeaux':['Grands','Échezeaux'],
      'Charmes-Chambertin':['Charmes-Chambertin','/ Mazoyères-','Chambertin'],
      'Latricières-Chambertin':['Latricières-','Chambertin'],
      'Chapelle-Chambertin':['Chapelle-','Chambertin'],
    }
    pending=[]
    for geometry,properties in grands:
        name=properties['name']
        if name not in old[key]['names'] or name=='Mazoyères-Chambertin':continue
        x,y=xy(panel,properties['label_xy'])
        if name in ['Griotte-Chambertin','Ruchottes-Chambertin','Mazis-Chambertin','La Romanée','Romanée-Conti','La Grande Rue'] or not multiline_inside(key,geometry,name,line_breaks.get(name,[name])):
            pending.append((y,x,name))
    for y,x,name in sorted(pending):
        side='right' if name in ['Griotte-Chambertin','Chapelle-Chambertin'] else 'left'
        place_label(panel,key,x,y,name,3.7,'italic','#733e49',side,'grand')
    # Name neighboring grands crus that occupy a substantial part of the same frame.
    for geometry,properties in grands:
        name=properties['name']
        if name in old[key]['names'] or name not in main_grands:continue
        clipped=geometry.intersection(panel['geographic_clip'])
        if clipped.area<8000 or clipped.area/geometry.area<.12:continue
        if not multiline_inside(key,geometry,name,{'Clos de Vougeot':['Clos de','Vougeot'],
                                                   'Clos de la Roche':['Clos de','la Roche']}.get(name,[name])):
            point=clipped.representative_point();x,y=xy(panel,point.coords[0])
            place_label(panel,key,x,y,name,3.5,'italic','#733e49','left','grand')
    priority={properties['source_name'] for geometry,properties in selected}
    adjacent=[(geometry,properties) for geometry,properties in all_premiers if geometry.intersects(panel['geographic_clip'])]
    adjacent.sort(key=lambda item:(item[1]['source_name'] not in priority,-item[0].intersection(panel['geographic_clip']).area))
    for geometry,properties in adjacent:
        clipped=geometry.intersection(panel['geographic_clip'])
        if clipped.area<3500 or clipped.area/geometry.area<.25:continue
        point=clipped.representative_point()
        x,y=xy(panel,point.coords[0]);name=properties['name']
        bounds=text_bounds(x,y,name,3.3,'middle','italic')
        if projected(panel,geometry).buffer(-.2).contains(bounds) and available(bounds,key):
            txt(x,y,name,3.3,'middle','italic','#75592f',key,'premier')
        else:
            preferred='left' if x<panel['frame'][0]+panel['frame'][2]/2 else 'right'
            for side in [preferred,'right' if preferred=='left' else 'left']:
                try:
                    place_label(panel,key,x,y,name,3.3,'italic','#75592f',side,'premier')
                    break
                except RuntimeError:
                    continue
            else:
                counts[key]['adjacent_labels_deferred']+=1
                deferred_labels.append({'panel':key,'name':name,'reason':'No collision-free label position in frame'})

def context_labels(key,panel):
    # Sparse contour labels, roads and landscape names follow sourced geometry.
    for geometry,properties in context['contours']:
        elevation=int(properties['altitude'])
        if elevation%(100 if key=='cote' else 50):continue
        g=projected(panel,geometry)
        if g is None or g.is_empty:continue
        lines=list(g.geoms) if hasattr(g,'geoms') else [g]
        for curve in lines:
            if curve.geom_type!='LineString' or curve.length<20:continue
            for fraction in [.25,.65]:
                point=curve.interpolate(fraction,normalized=True)
                bounds=text_bounds(point.x,point.y,str(elevation),3.2,'middle','regular')
                if available(bounds,key,4):
                    txt(point.x,point.y,str(elevation),3.2,'middle',color='#8d795c',panel=key,kind='elevation')
                    break
    road_groups=defaultdict(list)
    for geometry,properties in context['roads']:
        number=properties.get('cpx_numero')
        if number and number in ['D974','M974','D122','M122','D109','D31','D25','D8','M108','D122H']:
            g=projected(panel,geometry)
            if g is not None and not g.is_empty:road_groups[number].append(g)
    for name,geometries in road_groups.items():
        geometries.sort(key=lambda g:-g.length)
        limit=3 if key=='cote' and name in ['D974','M974'] else 1
        placed=0
        for geometry in geometries:
            if geometry.geom_type!='LineString' or geometry.length<3:continue
            point=geometry.interpolate(.5,normalized=True)
            bounds=text_bounds(point.x,point.y,name,3.2,'middle','regular')
            if available(bounds,key,2):
                txt(point.x,point.y,name,3.2,'middle',color='#7b6650',panel=key,kind='road')
                placed+=1
                if placed==limit:break
    if key!='cote':return
    names=['Combe de Fixin','Combe de Brochon','Combe Lavaux','Combe Pernant','Bois de la Montagne','Bois Communal de la Montagne','la Taupe']
    for geometry,properties in context['toponyms']+context['lieux_dits']:
        name=properties['toponyme']
        if name not in names:continue
        x,y=xy(panel,geometry.coords[0]);name=name[0].upper()+name[1:]
        bounds=text_bounds(x,y,name,3.35,'middle','italic')
        if available(bounds,key,2):txt(x,y,name,3.35,'middle','italic','#778064',key,'landscape')
    water_groups=defaultdict(list)
    for geometry,properties in context['local_water']:
        name=properties.get('cpx_toponyme_de_cours_d_eau')
        if name in ['Le Meuzin','La Vouge','la Vouge','le Meuzin']:
            g=projected(panel,geometry)
            if g is not None and g.geom_type=='LineString':water_groups[name].append(g)
    for name,geometries in water_groups.items():
        for geometry in sorted(geometries,key=lambda g:-g.length):
            point=geometry.interpolate(.5,normalized=True)
            bounds=text_bounds(point.x,point.y-2,name,3.4,'middle','italic')
            if available(bounds,key,2):
                txt(point.x,point.y-2,name,3.4,'middle','italic','#5c818a',key,'river')
                break

render_base('cote',panels['cote'])
label_main(panels['cote'])
context_labels('cote',panels['cote'])

# Source-derived inset footprints on the main map.
for letter,key in [('A','gevrey'),('B','vosne')]:
    extent=affine_transform(panels[key]['geographic_clip'],panels['cote']['matrix'])
    draw(extent,'fill="none" stroke="#6b3543" stroke-width=".4" stroke-dasharray="1.3,.8"')
    left,bottom,right,top=extent.bounds
    txt(left-2,bottom+3,letter,4.1,'end','bold','#6b3543')
scale_bar(panels['cote'],'cote',2000)

# Reuse the verified regional locator with its own scale and north correction.
source=ET.parse(ROOT/'nuits-atlas-04.svg').getroot()
ns='{http://www.w3.org/2000/svg}'
overview=source.find(f"{ns}g[@id='panel-overview']")
for element in overview.iter(f'{ns}text'):
    element.set('font-size',str(max(3.2,float(element.get('font-size','3.2')))))
overview_markup=ET.tostring(overview,encoding='unicode').replace('ns0:','').replace(':ns0','')
add('''<style>#panel-overview .frame{fill:#f8f5e9;stroke:#868067;stroke-width:.35}
#panel-overview .line{fill:none;stroke:#8c8168;stroke-width:.24}
#panel-overview .title{fill:#344a3a}#panel-overview .muted{fill:#746f5d}
#panel-overview .italic{font-style:italic}#panel-overview .water{fill:#5e7e85;font-style:italic}
#panel-overview .town{fill:#344633;stroke:#f5efdf;stroke-width:.4}
#panel-overview .caps{letter-spacing:.55px}</style>''')
add('<g transform="translate(0,-8)">'+overview_markup+'</g>')

for key,title,subtitle in [('gevrey','A · GEVREY-CHAMBERTIN','Les neuf appellations grands crus'),('vosne','B · VOSNE–FLAGEY','Les huit grands crus')]:
    panel=panels[key]
    render_base(key,panel)
    x,y,w,h=panel['frame']
    txt(x+w/2,y+11,title,4.6,'middle',color='#354a39')
    txt(x+w/2,y+18,subtitle,3.5,'middle','italic',color='#736c58')
    label_inset(key,panel)
    context_labels(key,panel)
    scale_bar(panel,key,250)
    if key=='gevrey':
        txt(x+9,y+h-28,'Charmes / Mazoyères-Chambertin',3.25,font='italic',color='#6f4350')
        txt(x+9,y+h-22,'Aire AOC commune · limite des climats non figurée.',3.2,color='#766b58')

# A compact technical legend makes linework and classification explicit.
line(25,805,575,805)
for x,category,name in [(26,'grand','Grand cru'),(123,'premier','Premier cru'),(226,'village','Village'),(319,'regional','Régionale')]:
    add(f'<rect x="{x}" y="814" width="8" height="4" fill="{COLORS[category]}" stroke="#8d8068" stroke-width=".15"/>')
    txt(x+12,818,name,3.8)
add('<rect x="422" y="814" width="8" height="4" fill="#d9dfc9"/>')
txt(434,818,'Bois et forêts',3.8)
add('<rect x="523" y="814" width="5" height="4" fill="#777168"/>')
txt(532,818,'Bâti',3.8)
line(27,831,40,831,'#566f51',.35);txt(44,832.2,'Limite d’aire AOC',3.4)
line(161,831,174,831,'#727b83',.3,'stroke-dasharray="2,.7,.35,.7"');txt(178,832.2,'Limite communale',3.4)
line(307,831,320,831,'#9c8766',.25);txt(324,832.2,'Courbes 25 m · détails 10 m',3.4)
line(500,831,514,831,'#7799a0',.35);txt(518,832.2,'Cours d’eau',3.4)
line(27,840,40,840,'#9d8b70',.75);line(27,840,40,840,'#fff9e9',.48);txt(44,841.2,'Route',3.4)
line(161,840,174,840,'#787777',.65);line(161,840,174,840,'#f8f5e9',.28,'stroke-dasharray="1.5,1.3"');txt(178,841.2,'Voie ferrée',3.4)
line(307,840,320,840,'#9c8766',.4);txt(324,841.2,'Courbes maîtresses 100 m · détails 50 m',3.4)
txt(26,849,'36 PREMIERS CRUS SÉLECTIONNÉS',4,color='#45583f')
txt(26,857,'Délimitations parcellaires INAO · Relief RGE ALTI · Routes, bâti et végétation IGN',3.35,color='#726a57')
txt(26,864,'Lambert-93 · Nord géographique · Données consultées les 12–14 novembre 2026',3.35,color='#726a57')
txt(574,849,'BONNES-MARES',3.7,'end',color='#743d4a')
txt(574,857,'Grand cru partagé entre deux communes.',3.35,'end',color='#726a57')
txt(574,864,'Morey-Saint-Denis et Chambolle-Musigny.',3.35,'end',color='#726a57')
line(25,872,575,872)
txt(300,879,'L’Atlas mondial du vin, 8e éd., p. 64–67 · INAO / IGN / DGFiP–Etalab / BIVB · Données géographiques sous Licence Ouverte 2.0',3.05,'middle',color='#7a725e')
add('</svg>')

svg=''.join(parts)
ET.fromstring(svg)
(ROOT/'nuits-professional-01.svg').write_text(svg,encoding='utf-8')
(ROOT/'nuits-professional-01.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Côte de Nuits</title><style>body{margin:0;background:#e8e4d6}svg{display:block;width:100%;height:auto}</style>'+svg,encoding='utf-8')

overlaps=[]
for i,label in enumerate(labels):
    for other in labels[i+1:]:
        if label['panel']!=other['panel']:continue
        overlap=label['bounds'].intersection(other['bounds'])
        if overlap.area>.4:
            overlaps.append([label['panel'],label['text'],other['text'],round(overlap.area,2)])
coverage=[]
for geometry,properties in selected:
    coverage.append({'name':properties['name'],'fraction':round(geometry.intersection(panels['cote']['geographic_clip']).area/geometry.area,6)})
leader_crossings=[]
for i,leader in enumerate(leaders):
    geometry=LineString([leader['start'],leader['end']])
    for other in leaders[i+1:]:
        if leader['panel']==other['panel'] and geometry.crosses(LineString([other['start'],other['end']])):
            leader_crossings.append([leader['panel'],leader['label'],other['label']])
report={'version':'nuits-professional-01','premiers_selected':36,'grand_cru_appellations':len(main_grands),
        'label_counts':dict(Counter(label['kind'] for label in labels)),'labels_total':len(labels),
        'overlaps':overlaps,'context_counts':{k:dict(v) for k,v in counts.items()},
        'premier_coverage':coverage,'minimum_map_font_pt':min(label['size_mm']*72/25.4 for label in labels),
        'leaders_over_35mm':[leader for leader in leaders if leader['length_mm']>35],
        'deferred_adjacent_labels':deferred_labels,
        'leader_crossings':leader_crossings,'leaders':leaders,
        'label_boxes':[dict(label,bounds=list(label['bounds'].bounds)) for label in labels],
        'panels':{key:{k:v for k,v in panel.items() if k not in ['clip','geographic_clip']} for key,panel in panels.items()}}
(ROOT/'checks/nuits-professional-01.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'layout-nuits-professional-01.json').write_text(json.dumps({
    'panels':report['panels'],'colors':COLORS,'labels':report['label_boxes'],
    'label_placement':'Geometry-derived positions, collision-adjusted; no manual geographic displacement',
    'contours_m':{'cote':{'interval':25,'index':100},'insets':{'interval':10,'index':50}}
},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['premiers_selected','grand_cru_appellations','labels_total','label_counts','overlaps','context_counts','minimum_map_font_pt','leaders_over_35mm']},ensure_ascii=False),flush=True)
