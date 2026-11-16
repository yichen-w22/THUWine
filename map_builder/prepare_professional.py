"""Acquire the bounded IGN context and prepare explicitly matched named premiers crus."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import time
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union
from shapely import make_valid

CACHE = ROOT / 'sources' / 'professional'
CACHE.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'data'
WFS = 'https://data.geopf.fr/wfs/ows'
BOUNDS = [843000, 6668200, 854000, 6690400]
EXTENT = box(*BOUNDS)

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

def request(url, params, path):
    if path.exists():
        return path.read_bytes()
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, timeout=(15, 60))
            response.raise_for_status()
            if response.content.lstrip().startswith(b'<?xml') and params.get('request') == 'GetFeature':
                raise ValueError(response.text[:500])
            path.write_bytes(response.content)
            save(path.with_suffix('.request.json'), {'url':response.url, 'retrieved':'2026-11-14', 'license':'Licence Ouverte 2.0'})
            return response.content
        except Exception as error:
            print(path.name, 'attempt', attempt+1, str(error)[:130], flush=True)
            if attempt == 3:
                raise
            time.sleep(2)

def acquire(name, layer):
    destination = CACHE / f'{name}.geojson'
    if destination.exists():
        return name, len(json.loads(destination.read_text(encoding='utf-8'))['features'])
    params = {'service':'WFS','version':'2.0.0','request':'GetFeature','typeNames':layer,
              'outputFormat':'application/json','srsName':'EPSG:2154',
              'bbox':','.join(map(str, BOUNDS))+',EPSG:2154','count':1000,'startIndex':0}
    first = json.loads(request(WFS, params, CACHE / f'{name}_00000.json'))
    total = int(first['numberMatched'])
    print(name, total, 'features', flush=True)
    features = first['features']
    for start in range(1000,total,1000):
        params['startIndex'] = start
        page = json.loads(request(WFS, params, CACHE / f'{name}_{start:05}.json'))
        features += page['features']
    assert len(features) == total
    assert len({f['id'] for f in features}) == total
    save(destination, {'type':'FeatureCollection','features':features,'source':layer,'retrieved':'2026-11-14'})
    return name,total

SELECTION = {
 'Fixin': [('Clos de la Perrière',None),('Clos du Chapitre',None),('Clos Napoléon',None),('Hervelets','Les Hervelets')],
 'Gevrey-Chambertin': [('Clos Saint-Jacques',None),('Les Cazetiers',None),('Lavaut Saint-Jacques',None),('Combe au Moine',None),('Champeaux',None),('Aux Combottes',None)],
 'Morey-Saint-Denis': [('Monts Luisants',None),('Les Millandes',None),('Les Chaffots',None),('Clos Sorbè',None)],
 'Chambolle-Musigny': [('Les Amoureuses',None),('Les Charmes',None),('Les Fuées',None),('Les Cras',None),('Les Baudes',None)],
 'Vougeot': [('Les Petits Vougeots',None),('Le Clos Blanc','Clos Blanc')],
 'Vosne-Romanée': [('Aux Malconsorts',None),('Les Suchots',None),('Aux Brulées','Aux Brûlées'),('Aux Raignots','Aux Reignots'),('Cros Parantoux',None),('Les Beaux Monts',None),('Les Petis Monts','Les Petits Monts')],
 'Nuits-Saint-Georges': [('Les Saints-Georges','Les Saint-Georges'),('Les Vaucrains',None),('Les Cailles',None),('Aux Boudots',None),('Aux Murgers',None),('Aux Perdrix',None),('Clos de la Maréchale',None),('Clos Arlot',"Clos de l’Arlot")],
}

def prepare_parcels():
    raw = json.loads((ROOT/'sources/ign/aoc_bourgogne.geojson').read_text(encoding='utf-8'))['features']
    selected = {f'{village} premier cru {name}':(village,display or name) for village, names in SELECTION.items() for name,display in names}
    matched = {name:[] for name in selected}
    all_premiers = {}
    village_geometries = {name:[] for name in SELECTION}
    village_geometries['Marsannay'] = []
    for feature in raw:
        names = feature['properties']['denom'].split(',')
        wanted = [name for name in names if name in selected or name in village_geometries or any(name.startswith(v+' premier cru ') for v in SELECTION)]
        if not wanted:
            continue
        geometry = make_valid(shape(feature['geometry']))
        if not geometry.intersects(EXTENT):
            continue
        for name in wanted:
            if name in matched:
                matched[name].append(geometry)
            if name in village_geometries:
                village_geometries[name].append(geometry)
            if ' premier cru ' in name:
                all_premiers.setdefault(name,[]).append(geometry)
    features = []
    for name,geometries in matched.items():
        if not geometries:
            alternatives=sorted({n for f in raw for n in f['properties']['denom'].split(',') if n.startswith(name.split(' premier cru')[0]+' premier cru')})
            raise ValueError((name,alternatives))
        geometry = unary_union(geometries)
        point = geometry.representative_point()
        village,display = selected[name]
        features.append({'type':'Feature','geometry':mapping(geometry.simplify(.35,preserve_topology=True)),
          'properties':{'name':display,'source_name':name,'village':village,'class':'premier',
          'label_xy':[point.x,point.y],'area_m2':geometry.area,'book_pages':[66,67] if village in ['Fixin','Gevrey-Chambertin','Morey-Saint-Denis'] else [64,65],
          'source':'INAO / IGN WFS, cached 2026-11-12','status':'exact_source_name_match'}})
    assert len(features)==36
    save(DATA/'nuits_professional_premiers.geojson',{'type':'FeatureCollection','features':features})
    adjacent=[]
    for name,geometries in all_premiers.items():
        village,display=name.split(' premier cru ')
        geometry=unary_union(geometries)
        point=geometry.representative_point()
        adjacent.append({'type':'Feature','geometry':mapping(geometry.simplify(.35)), 'properties':{
          'source_name':name,'name':selected.get(name,(village,display))[1],'village':village,
          'class':'premier','label_xy':[point.x,point.y],'source':'INAO / IGN WFS'}})
    save(DATA/'nuits_all_named_premiers.geojson',{'type':'FeatureCollection','features':adjacent})
    appellations=[]
    for name,geometries in village_geometries.items():
        geometry=unary_union(geometries).intersection(EXTENT)
        appellations.append({'type':'Feature','geometry':mapping(geometry.simplify(2)), 'properties':{'name':name,'source':'INAO / IGN WFS'}})
    save(DATA/'nuits_village_appellations.geojson',{'type':'FeatureCollection','features':appellations})
    print('Prepared 36 premiers crus and',len(appellations),'village AOC areas',flush=True)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='parcels':
        prepare_parcels()
    else:
        jobs = [('roads','BDTOPO_V3:troncon_de_route'),('railways','BDTOPO_V3:troncon_de_voie_ferree'),
                ('forest','BDTOPO_V3:zone_de_vegetation'),('buildings','BDTOPO_V3:batiment'),
                ('communes','BDTOPO_V3:commune'),('contours','ELEVATION.CONTOUR.LINE:courbe'),
                ('toponyms','BDCARTO_V5:detail_orographique'),('places','BDCARTO_V5:zone_d_habitation')]
        with ThreadPoolExecutor(max_workers=4) as executor:
            for result in executor.map(lambda job:acquire(*job),jobs):
                print(result,flush=True)
