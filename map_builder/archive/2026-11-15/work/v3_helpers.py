"""Compact static atlas layout: rigidly rotated coastal strips, no geography distortion."""
from pathlib import Path
import sys,json,math,html
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape,box
from shapely import make_valid
from shapely.affinity import rotate
from shapely.ops import unary_union
from pyproj import Transformer
from PIL import ImageFont
D=ROOT/'data'
def read(n):return json.loads((D/n).read_text(encoding='utf-8'))
areas=read('appellations_l93.geojson')['features'];grands=read('grands_crus_l93.geojson')['features'];rivers=read('rivers_l93.geojson')['features'];extras=read('selected_climats_l93.geojson')['features']
towns={t['name']:t for t in read('villages.json') if 'xy' in t};estates=read('estates.json')
G={id(f):make_valid(shape(f['geometry'])) for fs in [areas,grands,rivers,extras] for f in fs}
GC={f['properties']['name']:f for f in grands}
C={'regional':'#d8d1b6','village':'#99a984','premier':'#c6a05e','grand':'#814751','neighbour':'#d6d0c0'}
forward=Transformer.from_crs(4326,2154,always_xy=True); inverse=Transformer.from_crs(2154,4326,always_xy=True)
vosne=['Échezeaux','Grands Échezeaux','Richebourg','Romanée-Saint-Vivant','La Romanée','Romanée-Conti','La Grande Rue','La Tâche']
montrachet=['Chevalier-Montrachet','Montrachet','Bâtard-Montrachet','Bienvenues-Bâtard-Montrachet','Criots-Bâtard-Montrachet']
nuit_names=['Marsannay-la-Côte','Fixin','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Vosne-Romanée','Nuits-Saint-Georges','Premeaux-Prissey','Comblanchien','Corgoloin']
beaune_names=['Ladoix-Serrigny','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-les-Beaune','Beaune','Pommard','Volnay','Monthelie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Cheilly-lès-Maranges']
overview_names=['Auxerre','Chablis','Tonnerre','Vézelay','Châtillon-sur-Seine','Dijon','Beaune','Chalon-sur-Saône','Tournus','Mâcon']
def local(p,x,y):
    ox,oy=p['origin'];t=math.radians(p.get('rotation',0));dx=x-ox;dy=y-oy
    return math.cos(t)*dx-math.sin(t)*dy,math.sin(t)*dx+math.cos(t)*dy
def narrow_bounds(p,start,end,width,left=-.52):
    points=[local(p,*towns[n]['xy']) for n in [start,end]]
    return [width*left,min(y for x,y in points)-800,width*(left+1),max(y for x,y in points)+800]
def mapxy(p,x,y):
    a,b=local(p,x,y)
    return p['offset'][0]+(a-p['bounds'][0])*p['factor'],p['offset'][1]+(p['bounds'][3]-b)*p['factor']
def maplocal(p,x,y):return p['offset'][0]+(x-p['bounds'][0])*p['factor'],p['offset'][1]+(p['bounds'][3]-y)*p['factor']
def geom(p,f):
    from shapely.affinity import translate
    g=rotate(G[id(f)],p.get('rotation',0),origin=p['origin'])
    g=translate(g,-p['origin'][0],-p['origin'][1])
    return g.intersection(p['clip']) if g.intersects(p['clip']) else None
def path(g,p):
    if g is None or g.is_empty:return ''
    def ring(cs,closed):return 'M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in (maplocal(p,c[0],c[1]) for c in cs))+('Z' if closed else '')
    if g.geom_type=='Polygon':return ring(g.exterior.coords,True)+''.join(ring(r.coords,True) for r in g.interiors)
    if g.geom_type=='LineString':return ring(g.coords,False)
    return ''.join(path(z,p) for z in g.geoms) if hasattr(g,'geoms') else ''
def distribute(vals,gap,low,high):
    blocks=[]
    for i,y in enumerate(vals):
        blocks.append([y-gap*i,1,[i]])
        while len(blocks)>1 and blocks[-2][0]>blocks[-1][0]:
            a,b=blocks[-2:];n=a[1]+b[1];blocks[-2:]=[[(a[0]*a[1]+b[0]*b[1])/n,n,a[2]+b[2]]]
    out=[0]*len(vals)
    for val,_,idx in blocks:
        for i in idx:out[i]=val+gap*i
    if out:
        shift=max(0,low-out[0])-max(0,out[-1]-high);out=[y+shift for y in out]
    return out

S=[];TEXTS=[]
font_paths={'normal':'C:/Windows/Fonts/georgia.ttf','italic':'C:/Windows/Fonts/georgiai.ttf'}
fonts={k:ImageFont.truetype(v,1000) for k,v in font_paths.items()}
def esc(s):return html.escape(str(s),quote=True)
def add(s):S.append(s)
def txt(x,y,s,size=4,cls='',anchor='start',panel='',extra=''):
    add(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" class="{cls}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')
    font=fonts['italic' if ('italic' in cls or 'cru' in cls) else 'normal'];w=font.getlength(s)/1000*size
    x0=x-w if anchor=='end' else x-w/2 if anchor=='middle' else x
    TEXTS.append({'text':s,'panel':panel,'box':[x0,y-size*.82,x0+w,y+size*.23]})
def line(x,y,a,b,cls='line',extra=''):add(f'<path d="M{x:.2f},{y:.2f}L{a:.2f},{b:.2f}" class="{cls}" {extra}/>')
def point(x,y,r=.8):add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" class="town"/>')
def number(x,y,n):
    add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.15" fill="#f7f1de" stroke="#75454c" stroke-width=".22"/>')
    txt(x,y+1.1,str(n),3.1,'cru','middle')
def wrap(s,maxwidth,size):
    words=s.split(' ');lines=['']
    for w in words:
        trial=(lines[-1]+' '+w).strip()
        if lines[-1] and fonts['normal'].getlength(trial)/1000*size>maxwidth:lines.append(w)
        else:lines[-1]=trial
    return lines

