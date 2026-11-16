"""Use cadastral commune boundaries to avoid generalized boundaries across small climats."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip
import json
import sys
import time
import requests

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'sources/professional'
sys.path.insert(0,r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely import transform,make_valid
from shapely.geometry import shape,mapping
from pyproj import Transformer
project=Transformer.from_crs(4326,2154,always_xy=True)
source=json.loads((CACHE/'communes.geojson').read_text(encoding='utf-8'))

def acquire(feature):
    code=feature['properties']['code_insee']
    url=f'https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/21/{code}/cadastre-{code}-communes.json.gz'
    path=CACHE/f'cadastre-{code}-communes.geojson'
    for attempt in range(3):
        try:
            if not path.exists():
                response=requests.get(url,timeout=(15,40))
                response.raise_for_status()
                path.write_bytes(gzip.decompress(response.content))
            data=json.loads(path.read_text(encoding='utf-8'))
            assert len(data['features'])==1
            record=data['features'][0]
            geometry=make_valid(transform(shape(record['geometry']),project.transform,interleaved=False))
            properties=dict(feature['properties'])
            properties.update(source=url,source_dataset='DGFiP / Etalab cadastre',retrieved='2026-11-14',
                              license='Licence Ouverte 2.0',cadastral_update=record['properties']['updated'])
            return {'type':'Feature','geometry':mapping(geometry),'properties':properties}
        except Exception:
            if attempt==2:raise
            time.sleep(1)

with ThreadPoolExecutor(max_workers=5) as executor:
    features=list(executor.map(acquire,source['features']))
(CACHE/'cadastral_communes_l93.geojson').write_text(json.dumps({
    'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'EPSG:2154'}},
    'features':features},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Cadastral commune boundaries prepared',len(features),flush=True)
