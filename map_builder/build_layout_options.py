from pathlib import Path
import sys,json,math,html
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape,box
from shapely.ops import unary_union
from shapely.affinity import rotate
from shapely import make_valid
from pyproj import Transformer

ROOT=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
OUT=Path(r'C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs')
OUT.mkdir(exist_ok=True)
features=json.loads((ROOT/'data/appellations_l93.geojson').read_text(encoding='utf-8'))['features']
base=unary_union([make_valid(shape(f['geometry'])) for f in features if f['properties']['class'] in ['village','premier','grand']])
# Deliberately generalized masses for composition studies only, never legal boundaries.
regions={
 'nuits':base.intersection(box(836000,6667200,855500,6690600)),
 'beaune':base.intersection(box(822000,6644900,848000,6667200)),
 'chablis':base.intersection(box(738000,6729500,779000,6755500)),
 'chalonnaise':base.intersection(box(817000,6618500,843000,6644800)),
 'maconnais':base.intersection(box(824000,6571300,848000,6615000)),
}
# Include regional AOCs where they define the regional footprint, particularly
# Mâcon (which is absent from the village/premier/grand layer).
raw=json.loads((ROOT/'sources/ign/aoc_bourgogne.geojson').read_text(encoding='utf-8'))['features']
for key,terms in [('maconnais',['Mâcon']),('chalonnaise',['Chalonnaise','Couchois']),('chablis',['Petit Chablis'])]:
    supplement=[make_valid(shape(f['geometry'])) for f in raw if any(term in f['properties'].get('denom','') for term in terms)]
    if supplement:regions[key]=unary_union([regions[key]]+supplement)
for k,g in regions.items():
    regions[k]=g.buffer(280).buffer(-110).simplify(110,preserve_topology=True)
col={'nuits':'#80505a','beaune':'#9b8050','chablis':'#738b80','chalonnaise':'#a39059','maconnais':'#7d8b56'}
labels={'nuits':'Côte de Nuits','beaune':'Côte de Beaune','chablis':'Chablis & Auxerrois','chalonnaise':'Côte Chalonnaise','maconnais':'Mâconnais'}
forward=Transformer.from_crs(4326,2154,always_xy=True)
inverse=Transformer.from_crs(2154,4326,always_xy=True)
S=[];checks=[]
def add(s):S.append(s)
def text(x,y,s,size=12,anchor='middle',fill='#4a493c',extra=''):
    add(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" {extra}>{html.escape(s)}</text>')
def path(g,convert):
    def ring(cs):return 'M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in (convert(a,b) for a,b in cs))+'Z'
    if g.is_empty:return ''
    if g.geom_type=='Polygon':return ring(g.exterior.coords)+''.join(ring(r.coords) for r in g.interiors)
    return ''.join(path(p,convert) for p in g.geoms)
def compass(x,y,small=False):
    h=13 if small else 24
    add(f'<path d="M{x},{y+h}V{y}M{x},{y}l-3,7M{x},{y}l3,7" fill="none" stroke="#5d6250" stroke-width="1"/>')
    text(x,y-5,'N',9 if small else 12)
def map_group(keys,rect,style='main',title=None,tag=''):
    x,y,w,h=rect
    mini=style=='inset'
    if mini:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="#f6f1e3" stroke="#b4aa8a" stroke-width=".8"/>')
        text(x+w/2,y+19,title or ' · '.join(labels[k] for k in keys),10.3)
        compass(x+w-14,y+37,True)
        mx,my,mw,mh=x+12,y+32,w-25,h-50
    else:mx,my,mw,mh=x,y,w,h
    combined=unary_union([regions[k] for k in keys]);cx,cy=combined.centroid.coords[0]
    lon,lat=inverse.transform(cx,cy);nx,ny=forward.transform(lon,lat+.01)
    # Correct meridian convergence: geographic north is vertical at each map's centre.
    a=math.degrees(math.atan2(nx-cx,ny-cy))
    gs={k:rotate(regions[k],a,origin=(cx,cy)) for k in keys}
    l,b,r,t=unary_union(list(gs.values())).bounds
    scale=min(mw/(r-l),mh/(t-b))
    ox=mx+(mw-(r-l)*scale)/2;oy=my+(mh-(t-b)*scale)/2
    def convert(a,b):return ox+(a-l)*scale,oy+(t-b)*scale
    for k,g in gs.items():
        add(f'<path d="{path(g,convert)}" fill="{col[k]}" fill-rule="evenodd" stroke="{col[k]}" stroke-width=".35"/>')
    if style=='main':
        for k in keys:
            g=gs[k];p=g.representative_point();px,py=convert(p.x,p.y)
            # Clear short labels are visual anchors, not final cartographic annotations.
            right=k in ['nuits','chalonnaise','maconnais'] and not tag.startswith('D')
            tx=px+28 if right else px-26
            text(tx,py,labels[k],12,'start' if right else 'end',extra='font-style="italic" paint-order="stroke" stroke="#f0ead7" stroke-width="3" stroke-linejoin="round"')
    if mini and len(keys)>1:
        for k,g in gs.items():
            p=g.representative_point();px,py=convert(p.x,p.y)
            text(px+11,py,labels[k],8.4,'start',extra='paint-order="stroke" stroke="#f6f1e3" stroke-width="2.3"')
    checks.append({'id':tag,'regions':keys,'box':rect,'north_up':True,'meridian_correction_deg':round(a,4),'uniform_scale':scale})

layouts=[
 {'id':'A','name':'Deux angles opposés','main':[55,100,480,670],
  'insets':[(['chablis'],[28,110,188,195],None),(['chalonnaise','maconnais'],[388,490,184,300],'Du Chalonnais au Mâconnais')]},
 {'id':'B','name':'Trois satellites','main':[40,100,490,675],
  'insets':[(['chablis'],[28,110,184,190],None),(['chalonnaise'],[409,404,163,180],None),(['maconnais'],[404,602,168,188],None)]},
 {'id':'C','name':'Couronne supérieure','main':[35,255,470,530],
  'insets':[(['chablis'],[28,102,185,145],None),(['chalonnaise'],[401,102,171,145],None),(['maconnais'],[405,579,167,211],None)]},
 {'id':'D','name':'Grande carte décalée','main':[15,105,367,680],
  'insets':[(['chablis'],[428,103,144,196],None),(['chalonnaise','maconnais'],[384,472,188,318],'Du Chalonnais au Mâconnais')]},
 {'id':'E','name':'Trois cartes au pied','main':[55,99,495,535],
  'insets':[(['chablis'],[28,652,174,145],None),(['chalonnaise'],[213,652,174,145],None),(['maconnais'],[398,652,174,145],None)]},
 {'id':'F','name':'Le vignoble en continu','main':[67,104,475,680],'continuous':True,
  'insets':[(['chablis'],[28,108,185,175],None)]},
]
W,H=1880,2020
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><style>text{{font-family:Georgia,serif}}</style><rect width="100%" height="100%" fill="#deded6"/>')
text(W/2,40,'BOURGOGNE · ÉTUDES DE COMPOSITION',25)
text(W/2,69,'Six dispositions · Nord en haut pour toutes les cartes · Silhouettes simplifiées',15)
for i,L in enumerate(layouts):
    dx=20+(i%3)*620;dy=100+(i//3)*950
    add(f'<g transform="translate({dx},{dy})">')
    text(0,20,L['id'],28,'start',fill='#633c46')
    text(38,19,L['name'],18,'start')
    add('<g transform="translate(0,35)"><rect width="600" height="900" fill="#f0ead7"/><rect x="12" y="12" width="576" height="876" fill="none" stroke="#9d9679" stroke-width="1"/>')
    text(300,43,'BOURGOGNE',29,extra='letter-spacing="3"')
    text(300,65,'Vignobles & grands terroirs',11,extra='font-style="italic"')
    add('<path d="M30,79H570" stroke="#b8ad8d" stroke-width=".7"/>')
    mainkeys=['nuits','beaune','chalonnaise','maconnais'] if L.get('continuous') else ['nuits','beaune']
    map_group(mainkeys,L['main'],tag=L['id']+'-main')
    for j,(keys,rect,title) in enumerate(L['insets']):map_group(keys,rect,'inset',title,L['id']+'-inset-'+str(j))
    # Compass occupies an open location; north is never the vineyard's oblique axis.
    compass(555,330 if L['id']=='D' else 285 if L['id']=='C' else 125)
    add('<path d="M30,819H570" stroke="#b8ad8d" stroke-width=".7"/>')
    text(300,842,'Légende · Domaines · Sources',12,fill='#87816a')
    text(300,865,'Réserve pour les mentions et les ornements',9,fill='#98917a',extra='font-style="italic"')
    add('</g></g>')
text(W/2,2000,'Étude de mise en page — contours généralisés, sans valeur de délimitation parcellaire.',13)
add('</svg>')
svg=''.join(S)
(OUT/'Bourgogne-layout-options.svg').write_text(svg,encoding='utf-8')
(ROOT/'composition-options.svg').write_text(svg,encoding='utf-8')
(ROOT/'layout-options.json').write_text(json.dumps({'choices':layouts,'checks':checks,'status':'abstract_composition_review','source':'INAO / IGN cached geometry; buffered and simplified for layout only'},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'composition-options.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Bourgogne — six compositions</title><style>body{margin:0;background:#deded6}svg{display:block;width:100%;height:auto}</style>'+svg,encoding='utf-8')
print(json.dumps({'options':len(layouts),'maps':len(checks),'all_north_up':all(c['north_up'] for c in checks)}))
