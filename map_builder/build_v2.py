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
P={
 'overview':{'frame':[24,86,174,262],'map':[30,109,162,220],'origin':[0,0],'rotation':0,'bounds':[734000,6571000,861000,6761000],'title':'LA BOURGOGNE','subtitle':'Carte d’ensemble','scale':20000},
 'nuits':{'frame':[208,86,179,708],'map':[214,111,167,655],'origin':[848500,6677800],'rotation':13.3,'title':'CÔTE DE NUITS','subtitle':'De Marsannay à Corgoloin','scale':2000},
 'beaune':{'frame':[397,86,179,708],'map':[403,111,167,655],'origin':[835500,6656000],'rotation':35,'title':'CÔTE DE BEAUNE','subtitle':'De Corton aux Maranges','scale':2000},
 'vosne':{'frame':[24,360,174,204],'map':[30,385,162,128],'origin':[0,0],'rotation':0,'title':'A · VOSNE-ROMANÉE','subtitle':'Les grands crus','scale':250,'names':vosne},
 'montrachet':{'frame':[24,576,174,218],'map':[30,601,162,133],'origin':[0,0],'rotation':0,'title':'B · MONTRACHET','subtitle':'Les cinq grands crus','scale':250,'names':montrachet},
}
P['nuits']['bounds']=narrow_bounds(P['nuits'],'Corgoloin','Marsannay-la-Côte',5700)
P['beaune']['bounds']=narrow_bounds(P['beaune'],'Cheilly-lès-Maranges','Pernand-Vergelesses',6500,left=-.56)
# Keep the complete Corton hill inside the frame, with breathing room.
corton_top=max(local(P['beaune'],x,y)[1] for poly in ([G[id(GC['Corton'])]] if G[id(GC['Corton'])].geom_type=='Polygon' else G[id(GC['Corton'])].geoms) for x,y in poly.exterior.coords)
P['beaune']['bounds'][3]=max(P['beaune']['bounds'][3],corton_top+220)
for key in ['vosne','montrachet']:
    b=unary_union([G[id(GC[n])] for n in P[key]['names']]).bounds
    pad=100 if key=='vosne' else 85
    P[key]['bounds']=[b[0]-pad,b[1]-pad,b[2]+pad,b[3]+pad]
for p in P.values():
    x,y,w,h=p['map'];l,b,r,t=p['bounds'];s=min(w/(r-l),h/(t-b));p['factor']=s
    p['offset']=[x+(w-(r-l)*s)/2,y+(h-(t-b)*s)/2];p['clip']=box(l,b,r,t)
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

add('''<svg xmlns="http://www.w3.org/2000/svg" width="600mm" height="900mm" viewBox="0 0 600 900"><title>Bourgogne — composition 02</title><desc>Cartes de détail de la Côte de Nuits et de la Côte de Beaune, orientées le long de la côte sans déformation. Carte d’ensemble et agrandissements de Vosne et de Montrachet.</desc><defs><style>
text{font-family:Georgia,serif;fill:#373e31}.title{fill:#344a3a}.muted{fill:#746f5d}.italic{font-style:italic}.cru{fill:#743e49;font-style:italic}.halo{paint-order:stroke;stroke:#f3eedc;stroke-width:1.35;stroke-linejoin:round}.line{fill:none;stroke:#8c8168;stroke-width:.24}.leader{fill:none;stroke:#80785f;stroke-width:.22}.town{fill:#344633;stroke:#f5efdf;stroke-width:.4}.frame{fill:#f4efdf;stroke:#948a6b;stroke-width:.4}.water{fill:#5e7e85;font-style:italic}.caps{letter-spacing:.55px}
</style></defs><rect width="600" height="900" fill="#eee7d1"/><rect x="12" y="12" width="576" height="876" fill="none" stroke="#696d50" stroke-width=".8"/><rect x="15" y="15" width="570" height="870" fill="none" stroke="#a39670" stroke-width=".25"/>''')
txt(300,31,'ATLAS DES VIGNOBLES',4.2,'caps title','middle')
txt(300,59,'BOURGOGNE',25,'title','middle',extra='letter-spacing="2"')
txt(300,73,'Climats, villages & grands domaines',5,'italic muted','middle')
line(25,78,575,78)

for key,p in P.items():
    fx,fy,fw,fh=p['frame'];mx,my,mw,mh=p['map']
    add(f'<g id="panel-{key}"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" class="frame"/>')
    txt(fx+fw/2,fy+11,p['title'],5.1 if key in ['nuits','beaune'] else 4.5,'title caps','middle',key)
    txt(fx+fw/2,fy+18,p['subtitle'],3.4,'italic muted','middle',key)
    for cat in ['neighbour','regional','village','premier','grand']:
        for f in areas:
            if f['properties']['class']!=cat:continue
            g=geom(p,f)
            if g is None:continue
            if key=='overview':g=g.simplify(90,preserve_topology=True)
            add(f'<path d="{path(g,p)}" fill="{C[cat]}" fill-rule="evenodd"/>')
    for f in rivers:
        g=geom(p,f)
        if g is not None:add(f'<path d="{path(g,p)}" fill="none" stroke="#77959a" stroke-width="{.3 if key=="overview" else .37}"/>')
    for f in grands:
        g=geom(p,f)
        if g is not None:add(f'<path d="{path(g,p)}" data-name="{esc(f["properties"]["name"])}" fill="{C["grand"]}" fill-rule="evenodd" stroke="#57363b" stroke-width=".18"/>')

    if key in ['nuits','beaune']:
        # Close, individually placed appellation labels; Vosne and Montrachet expand at left.
        labels=[]
        for f in grands:
            name=f['properties']['name']
            if name in vosne+montrachet:continue
            a,b=mapxy(p,*f['properties']['label_xy'])
            if mx<a<mx+mw and my<b<my+mh:labels.append((a,b,name,'grand'))
        for f in extras:
            name=f['properties']['name']
            if 'premier cru' not in name:continue
            a,b=mapxy(p,*f['properties']['label_xy'])
            if mx<a<mx+mw and my<b<my+mh:labels.append((a,b,name.split('premier cru ')[1],'premier'))
        labels.sort(key=lambda z:z[1]);ys=distribute([r[1] for r in labels],6.1,my+22,my+mh-18)
        for (a,b,n,cat),yy in zip(labels,ys):
            tx=fx+6
            size=3.75
            tw=fonts['italic'].getlength(n)/1000*size
            # Keep leaders short; labels sit in the immediately adjacent western margin.
            end=tx+tw+1.5
            line(end,yy-1,a,b,'leader')
            txt(tx,yy,n,size,'cru halo' if cat=='grand' else 'italic muted halo',panel=key)
        ns=nuit_names if key=='nuits' else beaune_names
        pts=[]
        for n in ns:
            a,b=mapxy(p,*towns[n]['xy'])
            if mx<a<mx+mw and my<b<my+mh:pts.append((a,b,n))
        pts.sort(key=lambda z:z[1]);ys=distribute([z[1] for z in pts],7.5,my+6,my+mh-6)
        for (a,b,n),yy in zip(pts,ys):
            display='Monthélie' if n=='Monthelie' else 'Les Maranges' if n=='Cheilly-lès-Maranges' else n
            size=4.8 if n=='Beaune' else 4.1
            tw=fonts['normal'].getlength(display)/1000*size
            tx=min(a+4,fx+fw-5-tw)
            line(a,b,tx,yy-1,'leader');point(a,b)
            txt(tx,yy,display,size,'halo',panel=key)
        # Small-letter reference to inset, outside the dense cru names.
        names=vosne if key=='nuits' else montrachet
        g=unary_union([G[id(GC[n])] for n in names]);b=g.bounds
        corners=[mapxy(p,x,y) for x,y in [(b[0],b[1]),(b[0],b[3]),(b[2],b[3]),(b[2],b[1])]]
        add('<path d="M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in corners)+'Z" fill="none" stroke="#685e44" stroke-width=".45" stroke-dasharray="1.4 1"/>')
        q=min(corners,key=lambda z:z[1]);txt(q[0]-3,q[1]-3,'A' if key=='nuits' else 'B',4.7,'title halo','end',key)

    elif key=='overview':
        for n in overview_names:
            a,b=mapxy(p,*towns[n]['xy']);sz=3.3
            tx=a+2.8;anchor='start';yy=b-1
            if n in ['Auxerre','Vézelay']:tx=a-2.8;anchor='end'
            if n=='Châtillon-sur-Seine':tx=a;anchor='middle';yy=b-4
            if n=='Dijon':tx=a-2;anchor='end';yy=b-2
            if n=='Chalon-sur-Saône':tx=a-2;anchor='end';yy=b+4
            point(a,b,.55);txt(tx,yy,n,sz,'halo',anchor,key)
        # Regional names are accompanied by explicit short geographical anchors.
        for lon,lat,name,dy,dx in [(3.80,47.80,'CHABLIS',-5,0),(4.87,47.2,'CÔTE DE NUITS',-3,-23),(4.83,47.04,'CÔTE DE BEAUNE',2,-24),(4.75,46.77,'CÔTE CHALONNAISE',4,-34),(4.75,46.4,'MÂCONNAIS',1,-21)]:
            a,b=mapxy(p,*forward.transform(lon,lat));txt(a+dx,b+dy,name,3.15,'italic muted','end',key);line(a+dx+2,b+dy-1,a,b,'leader')
        # Indicator strips represent the actual rotated footprint of each detailed panel.
        for k in ['nuits','beaune']:
            q=P[k];l,b,r,t=q['bounds'];ang=-math.radians(q['rotation']);pts=[]
            for xx,yy in [(l,b),(l,t),(r,t),(r,b)]:
                gx=math.cos(ang)*xx-math.sin(ang)*yy+q['origin'][0];gy=math.sin(ang)*xx+math.cos(ang)*yy+q['origin'][1];pts.append(mapxy(p,gx,gy))
            add('<path d="M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in pts)+'Z" fill="none" stroke="#89474e" stroke-width=".35" stroke-dasharray="1 1"/>')
    else:
        # Index numbers free the image area from long fan-shaped leader lines.
        placed=[]
        for i,n in enumerate(p['names'],1):
            f=GC[n];a,b=mapxy(p,*f['properties']['label_xy']);xx,yy=a,b
            for step in range(50):
                if all(math.hypot(xx-x,yy-y)>5 for x,y in placed):break
                angle=step*2.4;rad=2+step*.28;xx=a+math.cos(angle)*rad;yy=b+math.sin(angle)*rad
            if math.hypot(xx-a,yy-b)>.5:line(a,b,xx,yy,'leader')
            number(xx,yy,i);placed.append((xx,yy))
        names=p['names'];start=fy+163 if key=='vosne' else fy+173
        # Two columns of full French names under the enlarged vineyard geometry.
        for i,n in enumerate(names):
            col=i//4 if key=='vosne' else i//3;row=i%4 if key=='vosne' else i%3
            xx=fx+7+col*83;yy=start+row*(7.5 if key=='vosne' else 9)
            txt(xx,yy,str(i+1),3.25,'cru',panel=key)
            ls=wrap(n.replace('-Montrachet','- Montrachet'),71,3.5)
            for j,part in enumerate(ls):txt(xx+5,yy+j*4,part,3.5,'cru',panel=key)
    # Metric scale bar and true north direction after rigid rotation.
    if key in ['vosne','montrachet']:sx=fx+7;sy=fy+153 if key=='vosne' else fy+163
    else:sx=fx+8;sy=fy+fh-10
    sl=p['scale']*p['factor'];line(sx,sy,sx+sl,sy)
    for a in [sx,sx+sl/2,sx+sl]:line(a,sy-1,a,sy+1)
    txt(sx,sy-2,'0',2.9,'muted',panel=key);txt(sx+sl,sy-2,f'{p["scale"]//1000} km' if p['scale']>=1000 else f'{p["scale"]} m',2.9,'muted','end',key)
    # Compute true north rather than treating the rotated grid as north.
    l,b,r,t=p['bounds'];cx,cy=(l+r)/2,(b+t)/2;a=-math.radians(p.get('rotation',0))
    gx=math.cos(a)*cx-math.sin(a)*cy+p['origin'][0];gy=math.sin(a)*cx+math.cos(a)*cy+p['origin'][1]
    lon,lat=inverse.transform(gx,gy);nx,ny=forward.transform(lon,lat+.005);aa,bb=mapxy(p,gx,gy);cc,dd=mapxy(p,nx,ny);angle=math.degrees(math.atan2(dd-bb,cc-aa))+90
    px=fx+fw-10;py=sy-1
    add(f'<g transform="translate({px},{py}) rotate({angle:.4f})"><path d="M0,-7L-1.6,-1L0,-2.2L1.6,-1Z" fill="#46533c"/><path d="M0,-2V2" class="line"/></g>')
    tx=px+math.sin(math.radians(angle))*9;ty=py-math.cos(math.radians(angle))*9
    txt(tx,ty,'N',3,'title','middle',key)
    add('</g>')

# Compact, readable footer: one line of legend and five tightly spaced rows of producers.
line(24,805,576,805)
for x,cat,name in [(26,'grand','Grand cru'),(104,'premier','Premier cru'),(190,'village','Village'),(259,'regional','Régionale')]:
    add(f'<rect x="{x}" y="811" width="7" height="4.4" fill="{C[cat]}" stroke="#84765e" stroke-width=".2"/>');txt(x+10,815,name,3.8)
txt(352,815,'—  Cours d’eau',3.7,'water')
txt(575,815,'Échelles propres à chaque carte',3.3,'italic muted','end')
txt(24,830,'DOMAINES & MAISONS',4,'title caps');txt(576,830,'Sélection proposée · sièges à préciser',3.4,'italic muted','end')
for i,e in enumerate(estates):
    col=i//5;row=i%5;x=24+col*140;y=840+row*6.2
    txt(x,y,e['id'],3.1,'muted');txt(x+7,y,e['name'],3.55)
line(24,871,576,871)
txt(300,878,'Composition 02 · INAO / IGN / BAN, Licence Ouverte · The World Atlas of Wine, 8e éd. · 60 × 90 cm',2.95,'muted','middle')
add('</svg>')
svg=''.join(S)
(ROOT/'composition-v02.svg').write_text(svg,encoding='utf-8');(ROOT/'composition.svg').write_text(svg,encoding='utf-8')
template=(ROOT/'web-template.html').read_text(encoding='utf-8');(ROOT/'index.html').write_text(template.replace('<!-- MAP_SVG -->',svg),encoding='utf-8')
layout={k:{a:b for a,b in p.items() if a!='clip'} for k,p in P.items()}
(ROOT/'layout-v02.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
# Conservative font-metric QA; designed to catch meaningful label overlap without a browser session.
overlaps=[]
for i,a in enumerate(TEXTS):
    if not a['panel']:continue
    for b in TEXTS[i+1:]:
        if a['panel']!=b['panel']:continue
        aa=a['box'];bb=b['box'];w=min(aa[2],bb[2])-max(aa[0],bb[0]);h=min(aa[3],bb[3])-max(aa[1],bb[1])
        if w>.9 and h>.9:overlaps.append({'panel':a['panel'],'a':a['text'],'b':b['text'],'w':round(w,2),'h':round(h,2)})
quality={'version':2,'overlaps':overlaps,'projection':'EPSG:2154','rigid_rotations_deg':{'nuits':13.3,'beaune':35},'detail_scale_ratio_vs_v01':{k:round(P[k]['factor']/.00955555556,2) for k in ['nuits','beaune']},'panels':5,'dimensions_mm':[600,900]}
(ROOT/'checks/layout-v02.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(quality,ensure_ascii=True),flush=True)
