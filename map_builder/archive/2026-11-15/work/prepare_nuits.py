from pathlib import Path
import sys,json
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
from shapely import make_valid
r=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
# Preserve exact WFS names and book context alongside display spellings.
selected=['Fixin premier cru Clos de la Perrière','Fixin premier cru Clos du Chapitre',
 'Nuits-Saint-Georges premier cru Les Saints-Georges','Nuits-Saint-Georges premier cru Les Vaucrains',
 'Nuits-Saint-Georges premier cru Les Cailles','Nuits-Saint-Georges premier cru Aux Boudots',
 'Nuits-Saint-Georges premier cru Clos de la Maréchale','Vosne-Romanée premier cru Aux Malconsorts',
 'Vosne-Romanée premier cru Les Beaux Monts']
raw=json.loads((r/'sources/ign/aoc_bourgogne.geojson').read_text(encoding='utf-8'))['features']
supp=[]
for name in selected:
    fs=[f for f in raw if name in f['properties']['denom'].split(',')]
    assert fs,name
    g=unary_union([make_valid(shape(f['geometry'])) for f in fs]);pt=g.representative_point()
    supp.append({'type':'Feature','geometry':mapping(g),'properties':{'name':name,'display_name':name.replace('Les Saints-Georges','Les Saint-Georges'),'label_xy':[pt.x,pt.y],'source':'INAO / IGN WFS, cached 2026-11-12','book_context_page':67 if name.startswith('Fixin') else 64}})
(r/'data/nuits_selected_premiers_l93.geojson').write_text(json.dumps({'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:EPSG::2154'}},'features':supp},ensure_ascii=False),encoding='utf-8')
s=(r/'build_cote_connected.py').read_text(encoding='utf-8')
s=s.replace("towns={t['name']", "extras+=read('nuits_selected_premiers_l93.geojson')['features']\ntowns={t['name']")
st=s.index('P={');en=s.index('for key,p in P.items():',st)
s=s[:st]+'''gevrey=['Chambertin','Chambertin-Clos de Bèze','Mazis-Chambertin','Ruchottes-Chambertin','Chapelle-Chambertin','Griotte-Chambertin','Charmes-Chambertin','Mazoyères-Chambertin','Latricières-Chambertin']
nuits_grands=[n for n in GC if n not in montrachet+['Corton','Corton-Charlemagne','Charlemagne','Chablis Grand Cru']]
P={
 'cote':{'frame':[24,86,552,708],'map':[31,108,538,658],'origin':[847000,6678000],'title':'','subtitle':'','scale':2000,'extent':[839500,6666800,855000,6691300]},
 'overview':{'frame':[31,108,128,175],'map':[37,132,116,129],'origin':[800000,6665000],'extent':[734000,6571000,861000,6761000],'title':'LA BOURGOGNE','subtitle':'Situation de la Côte de Nuits','scale':20000},
 'gevrey':{'frame':[31,300,190,232],'map':[38,325,85,180],'origin':[849000,6681500],'title':'A · GEVREY-CHAMBERTIN','subtitle':'Les neuf grands crus','scale':250,'names':gevrey},
 'vosne':{'frame':[420,540,150,246],'map':[427,566,136,136],'origin':[848000,6675800],'title':'B · VOSNE-ROMANÉE','subtitle':'Les huit grands crus','scale':250,'names':vosne},
}
''' +s[en:]
s=s.replace("if key in ['vosne','montrachet']:","if 'names' in p:")
s=s.replace('Côte d’Or — étude orientée au nord','Côte de Nuits — étude de composition')
s=s.replace('Une carte continue de la Côte de Nuits et de la Côte de Beaune, à la même échelle et orientée au nord géographique.', 'Carte continue de la Côte de Nuits, orientée au nord géographique. Composition inspirée des planches 64 à 67 de L’Atlas mondial du vin, 8e édition.')
s=s.replace("'CÔTE D’OR',25", "'CÔTE DE NUITS',23")
s=s.replace("'Bourgogne · Climats, villages & grands domaines'", "'Bourgogne · De Marsannay à Corgoloin'")
s=s.replace("else 3.5 if key in ['overview','vosne'] else 4.5", "else 3.5 if key=='overview' else 4.3")
s=s.replace("if name in vosne+montrachet:continue", "if name in vosne+gevrey:continue")
s=s.replace("name=f['properties']['name']\n            if 'premier cru'", "name=f['properties'].get('display_name',f['properties']['name'])\n            if 'premier cru'")
s=s.replace('ns=nuit_names+beaune_names',"ns=nuit_names+['Flagey-Echézeaux']")
s=s.replace("['Pernand-Vergelesses','Savigny-lès-Beaune','Saint-Romain','Auxey-Duresses','Saint-Aubin','Premeaux-Prissey','Comblanchien','Corgoloin']", "['Comblanchien','Corgoloin']")
s=s.replace("for letter,names in [('A',vosne),('B',montrachet)]:", "for letter,names in [('A',gevrey),('B',vosne)]:")
s=s.replace("        txt(327,147,'CÔTE DE NUITS',5.5,'title caps halo','middle',key)\n        txt(152,557,'CÔTE DE BEAUNE',5.5,'title caps halo','middle',key)", "")
st=s.index("        # Keys occupy");en=s.index('    sl=p[',st)
s=s[:st]+'''        for i,n in enumerate(p['names']):
            if key=='vosne':xx=fx+7;yy=fy+181+i*7
            else:xx=fx+100;yy=fy+55+i*16
            txt(xx,yy,str(i+1),3.25,'cru',panel=key)
            ls=wrap(n,131 if key=='vosne' else 78,3.5)
            for j,part in enumerate(ls):txt(xx+5,yy+j*4.5,part,3.5,'cru',panel=key)
    if key=='vosne':sx=fx+7;sy=fy+165
    elif key=='gevrey':sx=fx+7;sy=fy+220
    else:sx=fx+8;sy=fy+fh-10
''' +s[en:]
s=s.replace("e['region'] in ['Côte de Nuits','Côte de Beaune']", "e['region']=='Côte de Nuits'")
s=s.replace('col=i//4;row=i%4;x=24+col*140', 'col=i//3;row=i%3;x=24+col*184')
s=s.replace('Côte d’Or · Étude de composition', 'Côte de Nuits · Étude de composition')
s=s.replace("if n=='Chablis Grand Cru':continue", "if n not in nuits_grands:continue")
s=s.replace("['overview','vosne','montrachet']", "['overview','gevrey','vosne']")
s=s.replace('cote-connected-01','nuits-atlas-01')
s=s.replace("'shared_main_scale':True", "'shared_main_scale':True,'book_layout_reference':'book pages 64–67; PDF pages 68–71'")
s=s.replace("(max(b for a,b in corners)+6) if letter=='A' else q[1]-6", "max(b for a,b in corners)+7")
(r/'build_nuits_atlas.py').write_text(s,encoding='utf-8')
print('Prepared Nuits layout and nine additional first-growth geometries')
