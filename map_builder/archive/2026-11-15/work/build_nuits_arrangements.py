from copy import deepcopy
from pathlib import Path
import html
import json
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r'C:/Users/32697/Documents/Codex/2026-11-12/wo/work/gislibs')
from PIL import ImageFont
from shapely import make_valid
from shapely.affinity import rotate, scale, translate
from shapely.geometry import box, shape

ROOT = Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
OUT = Path(r'C:/Users/32697/Documents/Codex/2026-11-12/wo/outputs')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

source = ET.parse(ROOT / 'nuits-atlas-04.svg').getroot()
layout = json.loads((ROOT / 'layout-nuits-atlas-04.json').read_text(encoding='utf-8'))
groups = {node.attrib['id'].removeprefix('panel-'): node for node in source
          if node.attrib.get('id', '').startswith('panel-')}
main_crop = [160, 96, 320, 682]
font = ImageFont.truetype('C:/Windows/Fonts/georgia.ttf', 1000)

choices = [
    {'id': 'A', 'title': 'Atlas à droite', 'main': [30, 100, 340, 682],
     'overview': [405, 100, 165, 170], 'gevrey': [405, 280, 165, 245],
     'vosne': [405, 537, 165, 249]},
    {'id': 'B', 'title': 'Atlas à gauche', 'main': [230, 100, 340, 682],
     'overview': [30, 100, 170, 175], 'gevrey': [30, 287, 170, 240],
     'vosne': [30, 539, 170, 247]},
    {'id': 'C', 'title': 'Répartition diagonale', 'main': [120, 100, 340, 682],
     'overview': [442, 620, 128, 166], 'gevrey': [31, 100, 156, 282],
     'vosne': [401, 300, 169, 293]},
    {'id': 'D', 'title': 'Deux grands détails', 'main': [30, 100, 365, 682],
     'overview': [31, 100, 128, 175], 'gevrey': [383, 100, 187, 315],
     'vosne': [383, 435, 187, 351]},
]


def serialize(element):
    return ET.tostring(element, encoding='unicode')


def placement(source_box, target_box):
    sx, sy, sw, sh = source_box
    tx, ty, tw, th = target_box
    factor = min(tw / sw, th / sh)
    x = tx + (tw - sw * factor) / 2
    y = ty + (th - sh * factor) / 2
    return {'factor': factor, 'translate': [x - sx * factor, y - sy * factor],
            'frame': [x, y, sw * factor, sh * factor]}


def transform_geometry(geometry, placement_info):
    result = scale(geometry, xfact=placement_info['factor'],
                   yfact=placement_info['factor'], origin=(0, 0))
    return translate(result, *placement_info['translate'])


def svg_text(x, y, value, size=4, anchor='middle', extra=''):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'{extra}>{html.escape(value)}</text>')


def use_panel(key, destination, definition_id):
    source_box = main_crop if key == 'cote' else layout[key]['frame']
    placed = placement(source_box, destination)
    factor = placed['factor']
    dx, dy = placed['translate']
    markup = (f'<g transform="translate({dx:.5f},{dy:.5f}) scale({factor:.6f})">'
              f'<use href="#{definition_id}"/></g>')
    return markup, placed


definitions = ''.join(serialize(child) for child in source.find(f'{{{NS}}}defs'))
definitions += '<clipPath id="main-window"><rect x="160" y="96" width="320" height="682"/></clipPath>'
for key, node in groups.items():
    clone = deepcopy(node)
    clone.attrib['id'] = f'source-{key}'
    if key == 'cote':
        clone.attrib['clip-path'] = 'url(#main-window)'
    definitions += serialize(clone)

# Keep the established title, legend, producer selection, and page border.
furniture = ''.join(serialize(node) for node in source
                    if node.tag.rsplit('}', 1)[-1] not in ['defs', 'title', 'desc', 'g'])

main_features = json.loads((ROOT / 'data/grands_crus_l93.geojson').read_text(encoding='utf-8'))['features']
main = layout['cote']
projected_grands = []
for feature in main_features:
    geometry = make_valid(shape(feature['geometry']))
    geometry = translate(rotate(geometry, main['rotation'], origin=main['origin']),
                         -main['origin'][0], -main['origin'][1])
    if not geometry.intersects(box(*main['bounds'])):
        continue
    geometry = scale(geometry, xfact=main['factor'], yfact=-main['factor'], origin=(0, 0))
    geometry = translate(geometry, main['offset'][0] - main['bounds'][0] * main['factor'],
                         main['offset'][1] + main['bounds'][3] * main['factor'])
    projected_grands.append((feature['properties']['name'], geometry))

labels = []
for node in groups['cote']:
    if node.tag.rsplit('}', 1)[-1] != 'text' or not node.text:
        continue
    x, y = float(node.attrib['x']), float(node.attrib['y'])
    if not (160 <= x <= 480 and 96 <= y <= 778):
        continue
    size = float(node.attrib['font-size'])
    width = font.getlength(node.text) / 1000 * size
    anchor = node.attrib.get('text-anchor', 'start')
    left = x - width if anchor == 'end' else x - width / 2 if anchor == 'middle' else x
    labels.append((node.text, box(left, y - size * .82, left + width, y + size * .23)))

checks = []
pages = []
for choice in choices:
    parts = [furniture, '<rect x="24" y="86" width="552" height="708" class="frame"/>']
    main_markup, main_placement = use_panel('cote', choice['main'], 'source-cote')
    parts.append(main_markup)
    placed_insets = {}
    for key in ['overview', 'gevrey', 'vosne']:
        markup, placed = use_panel(key, choice[key], f'source-{key}')
        parts.append(markup)
        placed_insets[key] = placed

    # Each complete main map uses the same scale and the same north orientation.
    scale_x = choice['main'][0] + 8
    scale_y = 788
    scale_length = 2000 * main['factor'] * main_placement['factor']
    parts.append(f'<path d="M{scale_x},{scale_y}h{scale_length}M{scale_x},{scale_y-1}v2M{scale_x+scale_length},{scale_y-1}v2" class="line"/>')
    parts.append(svg_text(scale_x, scale_y-2, '0', 2.9, 'start', 'class="muted"'))
    parts.append(svg_text(scale_x+scale_length, scale_y-2, '2 km', 2.9, 'end', 'class="muted"'))
    north_x = choice['main'][0] + choice['main'][2] - 15
    parts.append(f'<path d="M{north_x},113l-1.6,6 1.6,-1.2 1.6,1.2Z" fill="#46533c"/>')
    parts.append(svg_text(north_x, 110, 'N', 3, extra='class="title"'))

    blocked_labels, blocked_grands = [], []
    for key, placed in placed_insets.items():
        x, y, width, height = placed['frame']
        frame = box(x, y, x + width, y + height)
        for text, bounds in labels:
            if transform_geometry(bounds, main_placement).intersection(frame).area > .5:
                blocked_labels.append([text, key])
        for name, geometry in projected_grands:
            if transform_geometry(geometry, main_placement).intersection(frame).area > .01:
                blocked_grands.append([name, key])
    checks.append({'choice': choice['id'], 'main_scale_relative_to_v04': main_placement['factor'],
                   'labels_obscured': blocked_labels, 'grands_crus_obscured': blocked_grands,
                   'insets': placed_insets})
    body = ''.join(parts)
    pages.append(body)
    svg = (f'<svg xmlns="{NS}" width="600mm" height="900mm" viewBox="0 0 600 900">'
           f'<defs>{definitions}</defs>{body}</svg>')
    (ROOT / f'nuits-arrangement-{choice["id"]}.svg').write_text(svg, encoding='utf-8')

sheet = [f'<svg xmlns="{NS}" width="1240" height="1990" viewBox="0 0 1240 1990">',
         f'<defs>{definitions}</defs><rect width="1240" height="1990" fill="#dddcd3"/>',
         svg_text(620, 36, 'CÔTE DE NUITS · QUATRE COMPOSITIONS', 20),
         svg_text(620, 62, 'Même échelle pour la carte principale · Nord en haut', 11)]
for index, (choice, page) in enumerate(zip(choices, pages)):
    x = 10 + index % 2 * 620
    y = 86 + index // 2 * 947
    sheet.append(f'<g transform="translate({x},{y})">')
    sheet.append(svg_text(0, 20, f'{choice["id"]} · {choice["title"]}', 17, 'start'))
    sheet.append(f'<g transform="translate(0,35)">{page}</g></g>')
sheet.append('</svg>')
sheet_svg = ''.join(sheet)
(ROOT / 'nuits-arrangements.svg').write_text(sheet_svg, encoding='utf-8')
(OUT / 'Nuits-arrangements.svg').write_text(sheet_svg, encoding='utf-8')
(ROOT / 'nuits-arrangements.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Côte de Nuits — compositions</title><style>body{margin:0;background:#dddcd3}svg{display:block;width:100%;height:auto}</style>' + sheet_svg, encoding='utf-8')
(ROOT / 'checks/nuits-arrangements.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(checks, ensure_ascii=True))
