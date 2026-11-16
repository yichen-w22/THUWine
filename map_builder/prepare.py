from pathlib import Path
import sys, json, collections, re
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely import make_valid
from pyproj import Transformer

DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
RAW=ROOT/'sources'/'ign'
GC=['Chambertin','Chambertin-Clos de Bèze','Chapelle-Chambertin','Charmes-Chambertin','Griotte-Chambertin','Latricières-Chambertin','Mazis-Chambertin','Mazoyères-Chambertin','Ruchottes-Chambertin','Clos Saint-Denis','Clos de la Roche','Clos des Lambrays','Clos de Tart','Bonnes-Mares','Musigny','Clos de Vougeot ou Clos Vougeot','Echezeaux','Grands-Echezeaux','Richebourg','Romanée-Conti','Romanée-Saint-Vivant','La Romanée','La Tâche','La Grande Rue','Corton','Corton-Charlemagne','Charlemagne','Montrachet','Chevalier-Montrachet','Bâtard-Montrachet','Bienvenues-Bâtard-Montrachet','Criots-Bâtard-Montrachet','Chablis Grand Cru']
def name_gc(s): return {'Echezeaux':'Échezeaux','Grands-Echezeaux':'Grands Échezeaux','Clos de Vougeot ou Clos Vougeot':'Clos de Vougeot'}.get(s,s)
VILLAGES=['Marsannay','Fixin','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Vosne-Romanée','Nuits-Saint-Georges','Côte de Nuits-Villages','Ladoix','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-lès-Beaune','Beaune','Pommard','Volnay','Monthélie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Maranges','Côte de Beaune','Côte de Beaune-Villages','Chablis','Petit Chablis','Irancy','Saint-Bris','Vézelay','Bouzeron','Rully','Mercurey','Givry','Montagny','Pouilly-Fuissé','Pouilly-Loché','Pouilly-Vinzelles','Saint-Véran','Viré-Clessé']
raw=json.loads((RAW/'aoc_bourgogne.geojson').read_text(encoding='utf-8'))
group=collections.defaultdict(list); grand=collections.defaultdict(list); selected=collections.defaultdict(list)
regional=collections.defaultdict(list)
climats=['Gevrey-Chambertin premier cru Clos Saint-Jacques','Chambolle-Musigny premier cru Les Amoureuses','Nuits-Saint-Georges premier cru Les Saint-Georges','Meursault premier cru Les Perrières','Pommard premier cru Les Rugiens Bas','Volnay premier cru Clos des Ducs','Beaune premier cru Clos des Mouches']
for f in raw['features']:
    tokens=f['properties']['denom'].split(','); g=shape(f['geometry'])
    if not g.is_valid: g=make_valid(g)
    if g.is_empty: continue
    grands=[s for s in GC if s in tokens]
    if grands: category='grand'
    elif any('premier cru' in s.lower() for s in tokens): category='premier'
    elif any(s in tokens for s in VILLAGES): category='village'
    elif any('Beaujolais' in s for s in tokens): category='neighbour'
    else: category='regional'
    group[category].append(g)
    for n in grands: grand[n].append(g)
    for n in climats:
        if n in tokens: selected[n].append(g)
    for n in ['Bourgogne Hautes Côtes de Nuits','Bourgogne Hautes Côtes de Beaune','Bourgogne Côtes du Couchois']:
        if n in tokens: regional[n].append(g)

def feat(g,props):
    return {'type':'Feature','geometry':mapping(g),'properties':props}
def fc(fs): return {'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:EPSG::2154'}},'features':fs}
def save(n,j): (DATA/n).write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def union(gs): return unary_union(gs)

layers=[]
for k,gs in group.items():
    print('Dissolve',k,len(gs),flush=True)
    g=union(gs)
    layers.append(feat(g.simplify(8,preserve_topology=True),{'class':k,'source':'INAO / IGN WFS','record_count':len(gs)}))
save('appellations_l93.geojson',fc(layers))
features=[]
for k,gs in grand.items():
    g=union(gs); p=g.representative_point()
    page=66 if 'Chambertin' in k or k in ['Clos Saint-Denis','Clos de la Roche','Clos des Lambrays','Clos de Tart'] else 64 if k not in ['Corton','Corton-Charlemagne','Charlemagne','Montrachet','Chevalier-Montrachet','Bâtard-Montrachet','Bienvenues-Bâtard-Montrachet','Criots-Bâtard-Montrachet','Chablis Grand Cru'] else 63 if 'Corton' in k or k=='Charlemagne' else 60 if 'Montrachet' in k else 55
    features.append(feat(g.simplify(.5),{'name':name_gc(k),'source_name':k,'class':'grand','label_xy':[p.x,p.y],'area_m2':round(g.area,1),'book_page':page,'pdf_page':page+4,'source':'INAO / IGN WFS','status':'official_geometry_book_crosscheck_in_progress'}))
save('grands_crus_l93.geojson',fc(features))
extras=[]
for k,gs in {**selected,**regional}.items():
    g=union(gs); p=g.representative_point()
    extras.append(feat(g.simplify(2),{'name':k,'label_xy':[p.x,p.y],'source':'INAO / IGN WFS'}))
save('selected_climats_l93.geojson',fc(extras))

r=json.loads((RAW/'rivers_bourgogne.geojson').read_text(encoding='utf-8'))
rivers=collections.defaultdict(list)
for f in r['features']: rivers[f['properties']['cpx_toponyme_de_cours_d_eau']].append(shape(f['geometry']))
save('rivers_l93.geojson',fc([feat(union(gs).simplify(12),{'name':k,'source':'IGN BD CARTO V5'}) for k,gs in rivers.items()]))

v=json.loads((DATA/'villages.json').read_text(encoding='utf-8'))
for r in v:
    if r['name']=='Saint-Aubin' and r['status']=='unresolved':
        import requests
        j=requests.get('https://data.geopf.fr/geocodage/search',params={'q':'Saint-Aubin','citycode':'21541','type':'municipality','limit':1},timeout=30).json()
        f=j['features'][0]; p=f['properties']; assert p['citycode']=='21541'
        r.update(xy=[p['x'],p['y']],coordinates=f['geometry']['coordinates'],citycode=p['citycode'],status='official_municipality_representative_point',source='https://data.geopf.fr/geocodage/search')
    # Pouilly-Fuisse is an appellation, never a municipality. Keep unresolved row out of town layer.
    if r['name']=='Pouilly-Fuissé': r.update(status='appellation_not_municipality',entity_type='appellation')
save('villages.json',v)

report={'source_record_count':len(raw['features']),'grand_cru_count':len(features),'missing_grand_cru_names':[x for x in GC if x not in grand],'river_names':list(rivers),'selected_climat_matches':list(selected),'projection':'EPSG:2154','simplification_m':{'overview_and_main':8,'grand_cru':0.5},'source_date':'Retrieved 2026-11-12; WFS publication vintage not specified','note':'INAO eligible appellation areas, not actual planted land or producer ownership. Overlapping grand cru eligibility retained in individual geometries.'}
save('data_quality.json',report)
print(json.dumps(report,ensure_ascii=True),flush=True)
