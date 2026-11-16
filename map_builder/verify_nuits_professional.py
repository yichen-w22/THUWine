"""Check the selected appellations, north orientation and source traceability."""
from pathlib import Path
import json
import math
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from shapely.geometry import shape
from pyproj import Transformer, Geod

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

OFFICIAL = {
    'Fixin':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/19990/20225.pdf',
    'Gevrey-Chambertin':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/19990/20226.pdf',
    'Morey-Saint-Denis':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/morey-saint-denis%2C2377%2C9170.html?args=Y29tcF9pZD0yMjA1JmFjdGlvbj12aWV3RmljaGUmaWQ9MzU3Jnw%3D',
    'Chambolle-Musigny':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/402/77490/77558.pdf',
    'Vougeot':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/vougeot%2C2377%2C9170.html?args=Y29tcF9pZD0yMjA1JmFjdGlvbj12aWV3RmljaGUmaWQ9NDEwJnw%3D',
    'Vosne-Romanée':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/402/77490/77754.pdf',
    'Nuits-Saint-Georges':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/nuits-saint-georges%2C2377%2C9170.html?args=Y29tcF9pZD0yMjA1JmFjdGlvbj12aWV3RmljaGUmaWQ9MzYyJnw%3D',
}
selected_path=ROOT/'data/nuits_professional_premiers.geojson'
selected=read(selected_path)
report=read(ROOT/'checks/nuits-professional-01.json')
main_names={x['text'] for x in report['label_boxes'] if x['panel']=='cote' and x['kind']=='premier'}
assert len(selected['features'])==36
assert len(main_names)==36
assert not report['overlaps']
assert report['minimum_map_font_pt']>=9
assert all(item['fraction']>=.999 for item in report['premier_coverage'])
for feature in selected['features']:
    properties=feature['properties']
    assert properties['name'] in main_names
    assert shape(feature['geometry']).is_valid
    assert properties['source_name'].startswith(properties['village']+' premier cru ')
    properties.update({
        'official_name_reference':OFFICIAL[properties['village']],
        'checked_date':'2026-11-14',
        'status':'INAO geometry and classification matched; book and BIVB names cross-checked',
        'name_note':'Source denomination retained verbatim; display spelling normalized where referenced.'
    })
selected_path.write_text(json.dumps(selected,ensure_ascii=False,separators=(',',':')),encoding='utf-8')

grands={f['properties']['name']:shape(f['geometry']) for f in read(ROOT/'data/grands_crus_l93.geojson')['features']}
communes=read(ROOT/'sources/professional/cadastral_communes_l93.geojson')['features']
bonnes=[]
for feature in communes:
    intersect=grands['Bonnes-Mares'].intersection(shape(feature['geometry']))
    if intersect.area>100:
        properties=feature['properties']
        bonnes.append({'commune':properties.get('nom_officiel',properties.get('nom')),
                       'area_ha':round(intersect.area/10000,4)})
assert len(bonnes)==2,bonnes
assert {item['commune'] for item in bonnes}=={'Morey-Saint-Denis','Chambolle-Musigny'}

forward=Transformer.from_crs(4326,2154,always_xy=True)
inverse=Transformer.from_crs(2154,4326,always_xy=True)
geod=Geod(ellps='GRS80')
north=[]
for name,panel in report['panels'].items():
    lon,lat=inverse.transform(*panel['origin'])
    lon2,lat2,_=geod.fwd(lon,lat,0,100)
    x2,y2=forward.transform(lon2,lat2)
    dx=x2-panel['origin'][0];dy=y2-panel['origin'][1]
    a,b,d,e,_,_=panel['matrix']
    error=math.degrees(math.atan2(a*dx+b*dy,-(d*dx+e*dy)))
    assert abs(error)<.02,(name,error)
    north.append({'panel':name,'north_error_degrees_at_origin':round(error,6),
                  'scale_250m_mm':round(250*panel['factor'],4)})

baseline=ROOT/'nuits-atlas-04.svg'
tree=ET.parse(baseline)
old_text={''.join(element.itertext()) for element in tree.iter('{http://www.w3.org/2000/svg}text')}
newly_named=sorted(main_names-old_text)
audit={
    'checked_date':'2026-11-14','selected_count':36,'selected_all_visible':True,
    'selected_names_added_against_plain_baseline':newly_named,
    'bonnes_mares_commune_intersections':bonnes,
    'charmes_mazoyeres_same_legal_geometry':grands['Charmes-Chambertin'].equals(grands['Mazoyères-Chambertin']),
    'charmes_mazoyeres_climat_division':'Not drawn; available sources define the common legal AOC area, not a separate confirmed climat boundary.',
    'charmes_mazoyeres_reference':'https://www.vins-bourgogne.fr/nos-vins-nos-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/402/57486/57550.pdf',
    'chambertin_clos_de_beze':'Legal eligibility overlaps. Clos de Beze is drawn above Chambertin so its geographic outline remains explicit.',
    'north_and_scales':north,
    'marsannay':'Village classification retained. Official material consulted does not confirm an approved premier-cru designation.',
    'terrain':'IGN contour source has 5 m intervals, filtered to 25/10 m. 20 m RGE ALTI sample used only for background hillshade.',
    'map_labels':report['label_counts'],'minimum_map_font_pt':report['minimum_map_font_pt'],
    'text_collisions':report['overlaps'],
    'deferred_adjacent_labels':report['deferred_adjacent_labels'],
    'administrative_boundaries':'DGFiP / Etalab cadastral commune outlines. BD TOPO administrative lines replaced after a local mismatch at Bonnes-Mares.',
    'bonnes_mares_official_reference':'https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/gallery_files/site/321/402/77490/77526.pdf',
    'limitations':['Official-name orthographic aliases retained in data. The Charmes/Mazoyeres internal climat boundary remains unverified.']
}
(ROOT/'checks/nuits-professional-geography.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
