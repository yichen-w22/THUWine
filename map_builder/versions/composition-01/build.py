"""Build one inline-SVG composition, used unchanged by the web preview and SVG export."""
from pathlib import Path
import sys,json,html,math
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape,box
from shapely import make_valid
from pyproj import Transformer
D=ROOT/'data'
def read(n):return json.loads((D/n).read_text(encoding='utf-8'))
AREAS=read('appellations_l93.geojson')['features']; GRAND=read('grands_crus_l93.geojson')['features']
RIVERS=read('rivers_l93.geojson')['features']; TOWNS=read('villages.json'); ESTATES=read('estates.json'); RESEARCH=read('research.json')
GEOMS={id(f):make_valid(shape(f['geometry'])) for fs in [AREAS,GRAND,RIVERS] for f in fs}
COLORS={'regional':'#dcd4b9','village':'#a2ad8b','premier':'#c6a363','grand':'#81454e','neighbour':'#d4d0c4'}
TRANS=Transformer.from_crs(4326,2154,always_xy=True)
def geo_bounds(w,s,e,n):
    points=[TRANS.transform(x,y) for x,y in [(w,s),(w,n),(e,s),(e,n)]]
    return min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)
PANELS={
 'overview':{'frame':[30,132,174,324],'map':[34,156,166,278],'bounds':[734000,6571000,861000,6761000],'title':'LA BOURGOGNE VITICOLE','scale':20000},
 'main':{'frame':[218,132,352,598],'map':[222,157,344,550],'bounds':[823000,6640500,859000,6698000],'title':'LA CÔTE D’OR','scale':5000},
 'vosne':{'frame':[30,472,174,122],'map':[34,492,83,88],'bounds':geo_bounds(4.944,47.153,4.977,47.178),'title':'A · VOSNE-ROMANÉE','scale':500},
 'montrachet':{'frame':[30,610,174,120],'map':[34,632,83,85],'bounds':geo_bounds(4.728,46.934,4.754,46.951),'title':'B · MONTRACHET','scale':500},
}
for k,p in PANELS.items():
    x,y,w,h=p['map']; xmin,ymin,xmax,ymax=p['bounds']; s=min(w/(xmax-xmin),h/(ymax-ymin)); p['factor']=s
    p['origin']=[x+(w-s*(xmax-xmin))/2,y+(h-s*(ymax-ymin))/2]; p['clip']=box(*p['bounds'])
def xy(p,a,b):return p['origin'][0]+(a-p['bounds'][0])*p['factor'],p['origin'][1]+(p['bounds'][3]-b)*p['factor']
S=[]
def add(s):S.append(s)
def esc(s):return html.escape(str(s),quote=True)
def text(x,y,s,size=3.7,cls='',anchor='start',extra=''):
    add(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" class="{cls}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')
def line(x1,y1,x2,y2,cls='',extra=''):
    add(f'<path d="M{x1:.3f},{y1:.3f}L{x2:.3f},{y2:.3f}" class="{cls}" {extra}/>')
def path_of(g,p):
    def ring(cs,close=False):
        return 'M'+'L'.join(f'{u:.2f},{v:.2f}' for u,v in [xy(p,c[0],c[1]) for c in cs])+('Z' if close else '')
    if g.is_empty:return ''
    if g.geom_type=='Polygon':return ring(g.exterior.coords,True)+''.join(ring(r.coords,True) for r in g.interiors)
    if g.geom_type=='LineString':return ring(g.coords)
    if hasattr(g,'geoms'):return ''.join(path_of(c,p) for c in g.geoms)
    return ''
def clipped(f,p):
    g=GEOMS[id(f)]
    return g.intersection(p['clip']) if g.intersects(p['clip']) else None
def label_ys(values,gap,low,high):
    # Isotonic regression of y_i - gap*i minimizes label displacement.
    blocks=[]
    for i,y in enumerate(values):
        blocks.append([y-gap*i,1,[i]])
        while len(blocks)>1 and blocks[-2][0]>blocks[-1][0]:
            a,b=blocks[-2:]; n=a[1]+b[1]; blocks[-2:]=[[(a[0]*a[1]+b[0]*b[1])/n,n,a[2]+b[2]]]
    out=[0]*len(values)
    for val,_,idx in blocks:
        for i in idx:out[i]=val+gap*i
    if out:
        shift=max(0,low-out[0])-max(0,out[-1]-high);out=[y+shift for y in out]
    return out
add('''<svg id="map-svg" xmlns="http://www.w3.org/2000/svg" width="600mm" height="900mm" viewBox="0 0 600 900" role="img" aria-labelledby="map-title map-desc">
<title id="map-title">Bourgogne — épreuve de composition</title><desc id="map-desc">Carte de la Bourgogne, détail de la Côte d’Or, agrandissements de Vosne-Romanée et de Montrachet. Données INAO et IGN, projection Lambert-93. Les domaines proposés figurent dans l’index sans points de localisation non vérifiés.</desc>
<defs><style>
text{font-family:Georgia,'Times New Roman',serif;fill:#3b3b2c}.smallcaps{letter-spacing:.65px}.muted{fill:#77705e}.italic{font-style:italic}.title{fill:#344539}.cru-label{fill:#733d46;font-style:italic}.town-label{paint-order:stroke;stroke:#f5f0df;stroke-width:1.5px;stroke-linejoin:round}.water-label{fill:#60828b;font-style:italic;paint-order:stroke;stroke:#f5f0df;stroke-width:1px}.rule{fill:none;stroke:#8e866b;stroke-width:.25}.leader{fill:none;stroke:#897f6c;stroke-width:.18}.frame{fill:#f5f0df;stroke:#9b937b;stroke-width:.35}.town{fill:#3c4438;stroke:#f5f0df;stroke-width:.35}.hide-layer{display:none}.interactive{cursor:pointer}.interactive:hover{stroke:#242e25;stroke-width:.65}
</style></defs>''')
add('<rect width="600" height="900" fill="#f0ead7"/>')
add('<g data-layer="frame"><rect x="15" y="15" width="570" height="870" fill="none" stroke="#6c6a52" stroke-width=".7"/><rect x="18" y="18" width="564" height="864" fill="none" stroke="#a99b77" stroke-width=".2"/>')
for x,y in [(21,21),(579,21),(21,879),(579,879)]:add(f'<path d="M{x-1.3},{y}l1.3,-1.3l1.3,1.3l-1.3,1.3Z" fill="#8c7852"/>')
add('</g>')
text(300,47,'ATLAS DES VIGNOBLES',5,'smallcaps title','middle')
text(300,83,'BOURGOGNE',26,'title','middle',extra='letter-spacing="3"')
text(300,101,'Climats, villages & grands domaines',6,'italic muted','middle')
line(171,112,429,112,'rule')
text(300,121,'DE CHABLIS AU MÂCONNAIS',3.9,'smallcaps','middle')

town_lookup={r['name']:r for r in TOWNS if 'xy' in r}
main_names=['Dijon','Marsannay-la-Côte','Fixin','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Vosne-Romanée','Nuits-Saint-Georges','Premeaux-Prissey','Comblanchien','Corgoloin','Ladoix-Serrigny','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-les-Beaune','Beaune','Pommard','Volnay','Monthelie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Cheilly-lès-Maranges','Chagny']
overview_names=['Auxerre','Chablis','Tonnerre','Irancy','Vézelay','Châtillon-sur-Seine','Dijon','Beaune','Couches','Chalon-sur-Saône','Bouzeron','Mercurey','Givry','Tournus','Mâcon','Fuissé']
vosne_gcs=['Échezeaux','Grands Échezeaux','Richebourg','Romanée-Conti','Romanée-Saint-Vivant','La Romanée','La Tâche','La Grande Rue']
montrachet_gcs=['Montrachet','Chevalier-Montrachet','Bâtard-Montrachet','Bienvenues-Bâtard-Montrachet','Criots-Bâtard-Montrachet']

for key,p in PANELS.items():
    fx,fy,fw,fh=p['frame'];mx,my,mw,mh=p['map']
    add(f'<g id="panel-{key}" data-panel="{key}"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" class="frame"/>')
    text(fx+fw/2,fy+12,p['title'],5.1 if key=='main' else 3.85,'smallcaps title','middle')
    line(fx+7,fy+17,fx+fw-7,fy+17,'rule')
    add('<g data-layer="areas">')
    for cat in ['neighbour','regional','village','premier','grand']:
        for f in AREAS:
            if f['properties']['class']!=cat:continue
            g=clipped(f,p)
            if g is None:continue
            if key=='overview':g=g.simplify(75,preserve_topology=True)
            elif key=='main':g=g.simplify(7,preserve_topology=True)
            add(f'<path d="{path_of(g,p)}" fill="{COLORS[cat]}" fill-rule="evenodd"/>')
    add('</g><g data-layer="rivers">')
    for f in RIVERS:
        g=clipped(f,p)
        if g is None:continue
        width=.33 if key=='overview' else .38
        add(f'<path d="{path_of(g,p)}" fill="none" stroke="#78939b" stroke-width="{width}"/>')
    # River labels on actual longest clipped segments; only large-scale overview.
    if key=='overview':
        for f in RIVERS:
            if f['properties']['name'] not in ['la Saône',"l'Yonne",'le Serein']:continue
            g=clipped(f,p)
            if g is None:continue
            segs=list(g.geoms) if hasattr(g,'geoms') else [g]
            seg=max(segs,key=lambda z:z.length); pt=seg.interpolate(.6,normalized=True); xx,yy=xy(p,pt.x,pt.y)
            rname=f['properties']['name']
            dx,dy=(-12,9) if rname=="l'Yonne" else (3,11) if rname=='la Saône' else (2,0)
            text(xx+dx,yy+dy,rname,3,'water-label')
    add('</g>')
    add('<g data-layer="crus">')
    for f in GRAND:
        g=clipped(f,p)
        if g is None:continue
        prop=f['properties']; add(f'<path class="interactive" data-feature="{esc(prop["name"])}" d="{path_of(g,p)}" fill="{COLORS["grand"]}" fill-rule="evenodd" stroke="#59333b" stroke-width="{.12 if key in ["main","overview"] else .22}"><title>{esc(prop["name"])}</title></path>')
    if key=='main':
        visible=[]
        for f in GRAND:
            n=f['properties']['name']
            if n in vosne_gcs+montrachet_gcs:continue
            a,b=xy(p,*f['properties']['label_xy'])
            if mx<a<mx+mw and my<b<my+mh:visible.append((a,b,n))
        visible.sort(key=lambda z:z[1]); ys=label_ys([v[1] for v in visible],6.1,my+40,my+mh-15)
        for (a,b,n),yy in zip(visible,ys):
            # Constant label column in the open west of the northern map.
            lx=365 if b<my+300 else 306
            line(lx+2,yy-1,a,b,'leader')
            text(lx,yy,n,3.6,'cru-label town-label','end')
    elif key in ['vosne','montrachet']:
        names=vosne_gcs if key=='vosne' else montrachet_gcs
        visible=[]
        for f in GRAND:
            if f['properties']['name'] in names:
                a,b=xy(p,*f['properties']['label_xy']);visible.append((a,b,f['properties']['name']))
        visible.sort(key=lambda z:z[1]); ys=label_ys([v[1] for v in visible],8.6,fy+31,fy+fh-18)
        for (a,b,n),yy in zip(visible,ys):
            line(a,b,fx+91,yy-1,'leader')
            if n=='Bienvenues-Bâtard-Montrachet':
                text(fx+93,yy-1.5,'Bienvenues-Bâtard-',3.2,'cru-label');text(fx+93,yy+2.5,'Montrachet',3.2,'cru-label')
            elif n=='Criots-Bâtard-Montrachet':
                text(fx+93,yy-1.5,'Criots-Bâtard-',3.2,'cru-label');text(fx+93,yy+2.5,'Montrachet',3.2,'cru-label')
            else:text(fx+93,yy,n,3.2,'cru-label')
    add('</g>')
    if key in ['main','overview']:
        add('<g data-layer="villages">')
        ns=main_names if key=='main' else overview_names
        points=[]
        for n in ns:
            if n not in town_lookup:continue
            a,b=xy(p,*town_lookup[n]['xy'])
            if mx<=a<=mx+mw and my<=b<=my+mh:points.append((a,b,n))
        points.sort(key=lambda z:z[1]);ys=label_ys([z[1] for z in points],6 if key=='main' else 6.5,my+4,my+mh-3)
        for (a,b,n),yy in zip(points,ys):
            size=4.3 if n in ['Dijon','Beaune','Chablis','Mâcon'] else 3.65 if key=='main' else 3.15
            name='Monthélie' if n=='Monthelie' else 'Les Maranges' if n=='Cheilly-lès-Maranges' else n
            if key=='overview':
                side='end' if n in ['Couches','Bouzeron','Mercurey','Givry','Fuissé','Irancy','Vézelay'] else 'start'
                tx=a-3 if side=='end' else a+3
                if n=='Châtillon-sur-Seine':tx=a;side='middle';yy=b-4
            else:tx=a+4;side='start'
            # Keep long labels inside the map panel.
            approx=len(name)*size*.51
            if side=='start' and tx+approx>fx+fw-4:tx=fx+fw-4;side='end'
            line(a,b,tx if side=='start' else tx,yy-1,'leader')
            add(f'<circle cx="{a:.3f}" cy="{b:.3f}" r="{.85 if size>4 else .60}" class="town"/>')
            text(tx,yy,name,size,'town-label',side)
        add('</g>')
    if key=='overview':
        add('<g data-layer="regions">')
        for lon,lat,label,size in [(3.62,47.85,'CHABLIS',3.5),(3.85,47.64,'GRAND AUXERROIS',3),(4.61,48.0,'CHÂTILLONNAIS',2.8),(4.29,47.21,'CÔTE DE NUITS',3),(4.18,46.99,'CÔTE DE BEAUNE',3),(4.20,46.73,'CÔTE CHALONNAISE',2.8),(4.29,46.38,'MÂCONNAIS',3.4),(4.7,46.17,'BEAUJOLAIS',3)]:
            a,b=xy(p,*TRANS.transform(lon,lat));text(a,b,label,size,'italic muted','middle')
        # True geographic extent of the main panel, not an arbitrary schematic box.
        a,b=xy(p,PANELS['main']['bounds'][0],PANELS['main']['bounds'][3]); c,d=xy(p,PANELS['main']['bounds'][2],PANELS['main']['bounds'][1])
        add(f'<rect x="{a:.3f}" y="{b:.3f}" width="{c-a:.3f}" height="{d-b:.3f}" fill="none" stroke="#7b474e" stroke-width=".45" stroke-dasharray="1.4 1"/>')
        add('</g>')
    if key=='main':
        add('<g data-layer="regions">')
        text(268,432,'HAUTES-CÔTES DE NUITS',4.1,'italic muted')
        line(325,431,439.69,415.89,'leader')
        text(238,530,'HAUTES-CÔTES DE BEAUNE',4.1,'italic muted')
        line(303,529,331.91,520.75,'leader')
        text(518,427,'Côte de Nuits',5,'italic muted','middle')
        text(454,635,'Côte de Beaune',5,'italic muted','middle')
        for inset,letter in [('vosne','A'),('montrachet','B')]:
            bds=PANELS[inset]['bounds'];a,b=xy(p,bds[0],bds[3]);c,d=xy(p,bds[2],bds[1])
            add(f'<rect x="{a:.3f}" y="{b:.3f}" width="{c-a:.3f}" height="{d-b:.3f}" fill="none" stroke="#675e49" stroke-width=".45" stroke-dasharray="1.5 1"/>');text(c+3 if letter=='B' else a-2,b-3,letter,4.5,'smallcaps','start' if letter=='B' else 'end')
        add('</g>')
    # Scale bar is generated from the exact panel transform.
    sx=fx+8;sy=fy+fh-8;sl=p['scale']*p['factor']
    line(sx,sy,sx+sl,sy,'rule',extra='stroke-width=".5"')
    for a in [sx,sx+sl/2,sx+sl]:line(a,sy-1,a,sy+1,'rule')
    text(sx,sy-2,'0',2.8,'muted');text(sx+sl,sy-2,(str(p['scale']//1000)+' km') if p['scale']>=1000 else str(p['scale'])+' m',2.8,'muted','end')
    nx=fx+fw-9;ny=fy+fh-9
    add(f'<path d="M{nx},{ny-6}l-1.3,4h2.6Z" fill="#56604c"/>');text(nx,ny-7,'N',2.6,'','middle')
    add('</g>')

# Compact legend and proposed estate index, separated from the cartography.
line(30,744,570,744,'rule')
text(30,754,'LÉGENDE',3.4,'smallcaps')
for x,k,label in [(80,'grand','Grand cru'),(155,'premier','Premier cru'),(237,'village','Appellation village'),(348,'regional','Appellation régionale')]:
    add(f'<rect x="{x}" y="749.5" width="8" height="4.5" fill="{COLORS[k]}" stroke="#746b56" stroke-width=".2"/>');text(x+11,753.3,label,3.5)
text(481,753.3,'—  Cours d’eau',3.5,'water-label')
text(30,764,'Aires délimitées d’appellation ; elles ne représentent ni les propriétés des domaines ni toutes les vignes plantées.',3.1,'muted')
text(30,781,'DOMAINES & MAISONS',4.6,'smallcaps title')
text(570,781,'Sélection proposée · 20 repères',3.5,'italic muted','end')
add('<g data-layer="estates">')
for i,e in enumerate(ESTATES):
    col=i//7; row=i%7; xx=30+col*183; yy=794+row*7
    text(xx,yy,e['id'],3.1,'muted')
    text(xx+9,yy,e['name'],3.7)
    text(xx+9,yy+3.3,e['commune'],2.8,'italic muted')
add('</g>')
line(30,847,570,847,'rule')
text(300,856,'ÉPREUVE DE COMPOSITION · SIÈGES DES DOMAINES À LOCALISER APRÈS VALIDATION',3.1,'smallcaps muted','middle')
text(300,864,'Source éditoriale : The World Atlas of Wine, 8e éd. · Géographie : INAO / IGN / BAN · Licence Ouverte',2.9,'muted','middle')
text(300,871,'Lambert-93 · 60 × 90 cm · Données consultées le 12 novembre 2026',2.9,'muted','middle')
add('</svg>')
SVG=''.join(S).replace('class="interactive"','class="cru-shape"')
(ROOT/'composition.svg').write_text(SVG,encoding='utf-8')

template=(ROOT/'web-template.html').read_text(encoding='utf-8')
meta=json.dumps({'estates':ESTATES,'research':RESEARCH,'panels':{k:v['frame'] for k,v in PANELS.items()}},ensure_ascii=False).replace('</',r'<\/')
out=template.replace('<!-- MAP_SVG -->',SVG).replace('/* MAP_METADATA */',meta)
(ROOT/'index.html').write_text(out,encoding='utf-8')
(ROOT/'layout.json').write_text(json.dumps({k:{x:y for x,y in p.items() if x!='clip'} for k,p in PANELS.items()},ensure_ascii=False,indent=2),encoding='utf-8')
print('SVG bytes:',len(SVG.encode()),'HTML bytes:',len(out.encode()),flush=True)
