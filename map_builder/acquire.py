"""Cache a bounded official WFS extract; reruns reuse every successful page."""
from pathlib import Path
import json, time, requests, concurrent.futures

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'sources' / 'ign'
RAW.mkdir(parents=True, exist_ok=True)
BASE = 'https://data.geopf.fr/wfs/ows'

def get_json(label, params):
    path = RAW / (label + '.json')
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    last = None
    for attempt in range(3):
        try:
            r = requests.get(BASE, params=params, timeout=(15, 50))
            r.raise_for_status()
            data = r.json()
            path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            (RAW / (label + '.request.json')).write_text(json.dumps({'url':r.url,'retrieved':'2026-11-12'},indent=2),encoding='utf-8')
            return data
        except Exception as e:
            last = e
            print(label, 'retry', attempt + 1, str(e)[:100], flush=True)
    raise last

def collection(label, typename, bbox=None, cql=None):
    p = {'service':'WFS','version':'2.0.0','request':'GetFeature',
         'typeNames':typename,'outputFormat':'application/json','srsName':'EPSG:2154',
         'count':1000,'startIndex':0}
    if bbox: p['bbox'] = bbox + ',EPSG:4326'
    if cql: p['cql_filter'] = cql
    first = get_json(label + '_00000', p)
    total = int(first['numberMatched'])
    print(label, 'matched', total, flush=True)
    batches = [first]
    def fetch(start):
        q = dict(p, startIndex=start)
        v = get_json(label + '_' + str(start).zfill(5), q)
        print(label, start, len(v['features']), flush=True)
        return v
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        batches += list(pool.map(fetch, range(1000,total,1000)))
    features = [f for b in batches for f in b['features']]
    assert len(features) == total, (label,len(features),total)
    assert len({f['id'] for f in features}) == total, 'Duplicate WFS records'
    result = {'type':'FeatureCollection','features':features,'crs':first.get('crs'),
              'source':BASE,'retrieved':'2026-11-12','numberMatched':total}
    (RAW / (label + '.geojson')).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    return result

if __name__ == '__main__':
    import sys
    job = sys.argv[1] if len(sys.argv)>1 else 'aoc'
    if job == 'aoc':
        collection('aoc_bourgogne','AOC-VITICOLES:aire_parcellaire','3.45,46.15,5.35,48.12')
    elif job == 'rivers':
        names = ['la Saône',"l’Yonne","l'Yonne",'le Serein',"l'Armançon",'la Dheune',"l'Ouche",'la Vouge','le Meuzin','la Bouzaize','la Grosne']
        quoted = ','.join("'"+n.replace("'","''")+"'" for n in names)
        cql = 'BBOX(geometrie,3.45,46.15,5.35,48.12,\'EPSG:4326\') AND cpx_toponyme_de_cours_d_eau IN ('+quoted+')'
        collection('rivers_bourgogne','BDCARTO_V5:troncon_hydrographique',cql=cql)
