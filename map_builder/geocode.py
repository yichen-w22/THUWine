from pathlib import Path
import requests, json, concurrent.futures, unicodedata
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'sources'/'geocoding'; OUT.mkdir(parents=True,exist_ok=True)
NAMES=['Auxerre','Chablis','Saint-Bris-le-Vineux','Irancy','Vézelay','Tonnerre','Châtillon-sur-Seine','Dijon','Marsannay-la-Côte','Fixin','Gevrey-Chambertin','Morey-Saint-Denis','Chambolle-Musigny','Vougeot','Vosne-Romanée','Flagey-Echézeaux','Nuits-Saint-Georges','Premeaux-Prissey','Comblanchien','Corgoloin','Ladoix-Serrigny','Aloxe-Corton','Pernand-Vergelesses','Savigny-lès-Beaune','Chorey-les-Beaune','Beaune','Pommard','Volnay','Monthelie','Auxey-Duresses','Saint-Romain','Meursault','Puligny-Montrachet','Chassagne-Montrachet','Saint-Aubin','Santenay','Cheilly-lès-Maranges','Chagny','Couches','Bouzeron','Rully','Mercurey','Givry','Buxy','Montagny-lès-Buxy','Chalon-sur-Saône','Tournus','Mâcon','Viré','Clessé','Pouilly-Fuissé','Fuissé','Solutré-Pouilly','Vergisson','Milly-Lamartine','Saint-Vérand']
def norm(s): return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if not unicodedata.combining(c))
def task(name):
    path=OUT/(norm(name)+'.json')
    q={'q':name,'limit':5,'type':'municipality'}
    if path.exists(): j=json.loads(path.read_text(encoding='utf-8'))
    else:
        r=requests.get('https://data.geopf.fr/geocodage/search',params=q,timeout=30); r.raise_for_status(); j=r.json()
        path.write_text(json.dumps(j,ensure_ascii=False),encoding='utf-8')
    fs=[f for f in j['features'] if f['properties'].get('depcode') in ['21','71','89']]
    exact=[f for f in fs if norm(f['properties']['city'])==norm(name)]
    if not exact:
        print('REVIEW',ascii(name),flush=True)
        return {'name':name,'status':'unresolved','results':fs}
    f=exact[0]; p=f['properties']
    return {'name':name,'coordinates':f['geometry']['coordinates'],'xy':[p['x'],p['y']],
        'citycode':p['citycode'],'status':'official_municipality_representative_point',
        'source':'https://data.geopf.fr/geocodage/search','query':q,
        'book_page':55,'retrieved':'2026-11-12'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(task,NAMES))
(ROOT/'data').mkdir(exist_ok=True)
(ROOT/'data'/'villages.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('Resolved',sum(r['status']!='unresolved' for r in rows),'of',len(rows),flush=True)
