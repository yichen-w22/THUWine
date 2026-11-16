"""First decorative proof, reusing the accepted D composition verbatim."""
from pathlib import Path
from copy import deepcopy
import math
import random
import xml.etree.ElementTree as ET

BASE = Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
WORK = Path(__file__).resolve().parent
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

def node(markup):
    return ET.fromstring(f'<g xmlns="{NS}">{markup}</g>')

root = ET.parse(BASE / 'nuits-arrangement-D.svg').getroot()
defs = root.find(f'{{{NS}}}defs')
original_geometry = [e.attrib['d'] for e in root.iter() if 'data-name' in e.attrib]
decor_defs = node('''
<linearGradient id="vellum" x1="0" y1="0" x2="1" y2="1">
 <stop stop-color="#e2cf9f"/><stop offset=".28" stop-color="#f5ebd0"/>
 <stop offset=".75" stop-color="#efe1bb"/><stop offset="1" stop-color="#dcca9d"/>
</linearGradient>
<radialGradient id="paper-light"><stop stop-color="#fbf3dc"/><stop offset="1" stop-color="#eee0bc"/></radialGradient>
<linearGradient id="ribbon" x2="0" y2="1"><stop stop-color="#f9edcf"/><stop offset="1" stop-color="#e4cfa2"/></linearGradient>
<pattern id="engraving" width="1.6" height="1.6" patternUnits="userSpaceOnUse">
 <path d="M-.4,.4L.4,-.4M0,1.6L1.6,0M1.2,2L2,1.2" stroke="#442d29" stroke-width=".10" opacity=".23"/>
</pattern>
<g id="vine-leaf" stroke="#5d6140" stroke-linejoin="round">
 <path d="M0,0C-3,-2 -7,-1 -9,-5L-6,-6 -10,-10 -5,-9 -5,-15 -1,-12 2,-18 4,-12 9,-14 8,-9 13,-8 9,-5 11,-2C7,-1 3,-2 0,0Z" fill="#89916a" stroke-width=".36"/>
 <path d="M0,0L2,-16M0,-2L-7,-9M1,-5L-3,-11M1,-3L9,-7M2,-8L7,-12" fill="none" stroke-width=".25"/>
 <path d="M-2,-3l-4,-2M-3,-5l-4,-2M4,-4l4,-1M4,-6l4,-2" fill="none" stroke-width=".15"/>
</g>
<g id="grape-bunch" stroke="#573c3b" stroke-width=".24">
 <path d="M0,-4Q2,-10 5,-12" fill="none" stroke="#65573d" stroke-width=".65"/>
</g>
''')
for e in list(decor_defs):
    defs.append(e)
bunch = defs.find(f"{{{NS}}}g[@id='grape-bunch']")
for x,y,r in [(-4,0,3.1),(1,-1,3.2),(5,2,3),(-7,4,3),(-2,5,3.3),(3,7,3.2),(-4,10,3),(0,12,3),(1,17,2.6)]:
    bunch.append(node(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#80525b"/><path d="M{x-r*.6},{y-r*.15}q0,{-r*.6} {r*.6},{-r*.6}" fill="none" stroke="#c3a19a" stroke-width=".35"/>'))

style = defs.find(f'{{{NS}}}style')
style.text += '''
text{fill:#493e30}.title{fill:#4c4830}.muted{fill:#7e6a4e}
.frame{fill:#f2e6c9;stroke:#8c7450;stroke-width:.45}
.halo{stroke:#f2e6c9}.line{stroke:#8c7450}.leader{stroke:#806a50}
.cru{fill:#733c48}.inset-callout{stroke:#f2e6c9}.water{fill:#5c7b81}
'''

# Replace page furniture while retaining every map transformation and its contents.
for e in list(root):
    tag=e.tag.rsplit('}',1)[-1]
    if tag=='rect' and (e.attrib.get('width') in ['600','576','570']):
        root.remove(e)
    elif tag=='text' and float(e.attrib.get('y',999))<80:
        root.remove(e)
    elif tag=='path' and e.attrib.get('d','').startswith('M25.00,78.00'):
        root.remove(e)
    elif tag=='text' and 'The World Atlas' in (e.text or ''):
        e.text='INAO / IGN / BAN · Licence Ouverte · L’Atlas mondial du vin, 8e éd. · Épreuve de style · 60 × 90 cm'

paper = node('<rect width="600" height="900" fill="url(#vellum)"/><rect x="22" y="84" width="556" height="714" fill="url(#paper-light)"/>')
root.insert(1,paper)

# Transparent engraving is restricted to the sourced grand-cru polygons.
for panel_id in ['source-cote','source-gevrey','source-vosne']:
    panel = defs.find(f"{{{NS}}}g[@id='{panel_id}']")
    for e in list(panel):
        if 'data-name' in e.attrib:
            hatch=deepcopy(e)
            hatch.attrib.pop('data-name')
            hatch.attrib.update(fill='url(#engraving)',stroke='none')
            panel.insert(list(panel).index(e)+1,hatch)

ornaments=[]
def add(s):
    ornaments.append(s)

# A narrow grapevine border keeps botanical ornament outside all map panels.
add('<g id="botanical-border" fill="none" stroke="#71583d">')
add('<rect x="5" y="5" width="590" height="890" stroke-width="1.1"/><rect x="7" y="7" width="586" height="886" stroke-width=".24"/><rect x="21" y="21" width="558" height="858" stroke-width=".45"/>')
for side in [0,1]:
    add(f'<g transform="translate({600 if side else 0},0) scale({-1 if side else 1},1)">')
    add('<path d="M14,28'+''.join(f'Q{5 if i%2 else 23},{y+14} 14,{y+28}' for i,y in enumerate(range(28,840,28)))+'" stroke-width=".65"/>')
    for i,y in enumerate(range(48,859,38)):
        add(f'<use href="#vine-leaf" transform="translate(14,{y}) rotate({65 if i%2 else -75}) scale(.48)"/>')
        if i%4==0:
            add(f'<use href="#grape-bunch" transform="translate(13,{y+14}) scale(.40)"/>')
        add(f'<path d="M14,{y}q9,-7 7,-12q-4,-4 -5,1q0,3 3,2" stroke-width=".2"/>')
    add('</g>')
for y in [14,886]:
    add(f'<path d="M28,{y}Q160,{y-5} 300,{y}T572,{y}" stroke-width=".6"/>')
    for x in range(42,571,28):
        add(f'<use href="#vine-leaf" transform="translate({x},{y}) rotate({-65 if y<100 else 115}) scale(.40)"/>')
add('</g>')

# Scroll cartouche and botanical corner sprays.
add('''<g id="title-cartouche" stroke="#796143" stroke-linejoin="round">
<path d="M96,38L58,32 67,49 56,65 99,61M504,38L542,32 533,49 544,65 501,61" fill="#b89a6c" stroke-width=".65"/>
<path d="M96,38L79,47 97,61M504,38L521,47 503,61" fill="#90734f" stroke-width=".4"/>
<path d="M94,28Q300,20 506,28L506,66Q300,74 94,66Z" fill="url(#ribbon)" stroke-width=".8"/>
<path d="M99,32Q300,24 501,32L501,62Q300,70 99,62Z" fill="none" stroke-width=".22"/>
</g>
<text x="300" y="20" font-size="3.6" text-anchor="middle" letter-spacing="1.5">ATLAS DES VIGNOBLES DE BOURGOGNE</text>
<text x="300" y="55" font-size="22" text-anchor="middle" fill="#4a3a2d" letter-spacing="1.8">CÔTE DE NUITS</text>
<text x="300" y="79" font-size="4.4" text-anchor="middle" font-style="italic">De Marsannay à Premeaux-Prissey</text>''')
for x,flip in [(45,1),(555,-1)]:
    add(f'<g transform="translate({x},54) scale({flip},1)"><path d="M-10,17Q-23,-20 15,-28M-18,-5Q-29,-16 -23,-28" fill="none" stroke="#70603c" stroke-width=".7"/>')
    for a,b,r,s in [(-12,-10,-45,.8),(-3,-22,10,.8),(-22,-16,-65,.65),(-7,1,45,.65)]:
        add(f'<use href="#vine-leaf" transform="translate({a},{b}) rotate({r}) scale({s})"/>')
    add('<use href="#grape-bunch" transform="translate(-17,1) scale(.8)"/></g>')

# Restrained corner filigree sits within the clear margins of the inset frames.
for x,y,w,h in [(31,100,128,175),(389.37234,100,174.25532,315),(383,448.39645,187,324.2071)]:
    add(f'<rect x="{x+1.4}" y="{y+1.4}" width="{w-2.8}" height="{h-2.8}" fill="none" stroke="#a58b5f" stroke-width=".18"/>')
    for cx,cy,ang in [(x+2,y+2,0),(x+w-2,y+2,90),(x+w-2,y+h-2,180),(x+2,y+h-2,270)]:
        add(f'<path transform="translate({cx},{cy}) rotate({ang})" d="M0,11V0H11M2,8Q2,2 8,2M2,2L5,5" fill="none" stroke="#7e6844" stroke-width=".35"/>')

# A wine vignette occupies verified empty space west of the vineyard belt.
add('''<g id="wine-vignette" transform="translate(102,346)" stroke="#786145" stroke-linecap="round" stroke-linejoin="round">
<path d="M-44,44Q0,48 46,44M-39,46Q0,50 41,46" fill="none" stroke-width=".25"/>
<path d="M-26,-2C-35,10 -35,28 -26,42Q-7,48 11,42C19,25 19,10 11,-2Z" fill="#dbc297" stroke-width=".7"/>
<ellipse cx="-7.5" cy="-2" rx="18.5" ry="5.5" fill="#e9d6ad" stroke-width=".6"/>
<path d="M-26,0Q-14,4 11,0M-23,-5L7,1M-14,-7L-5,3M-23,3Q-30,22 -23,43M-13,4Q-17,24 -13,45M-3,4Q-2,24 -3,45M7,3Q14,24 7,43" fill="none" stroke-width=".35"/>
<path d="M-31,8Q-9,14 16,8L17,12Q-8,19 -32,12ZM-32,31Q-7,37 17,31L16,35Q-9,42 -30,35Z" fill="#938f70" stroke-width=".5"/>
<path d="M23,39V7Q23,1 28,-3V-22H34V-3Q39,1 39,7V39Q31,43 23,39Z" fill="#727d56" stroke-width=".5"/>
<path d="M28,-18H34M26,10V36" fill="none" stroke="#d6cba3" stroke-width=".5"/>
<path d="M24,15H38V29H24Z" fill="#e1cda5" stroke-width=".25"/>
<path d="M26,19H36M27,22H35M28,25H34" stroke-width=".22"/>
<path d="M43,17Q44,29 49,29Q54,29 55,17ZM49,29V40M43,41Q49,39 55,41" fill="none" stroke-width=".6"/>
<path d="M-31,-10Q-14,-50 22,-45M-8,-38Q-9,-54 -26,-58M10,-45Q19,-59 33,-53" fill="none" stroke-width=".85"/>
<use href="#vine-leaf" transform="translate(-10,-36) rotate(-55) scale(1.25)"/>
<use href="#vine-leaf" transform="translate(7,-43) rotate(55) scale(1.05)"/>
<use href="#vine-leaf" transform="translate(-25,-54) rotate(-25) scale(.8)"/>
<use href="#grape-bunch" transform="translate(-17,-29) scale(1.15)"/>
<path d="M23,-45q15,-14 20,-5q4,8 -4,8q-5,-1 -2,-5M-25,-37q-20,2 -16,12q4,6 7,0" fill="none" stroke-width=".3"/>
</g>''')

# Decorative compass rose occupies a clear area, with geographic north at top.
add('<g id="compass-rose" transform="translate(105,447)" stroke="#7b694c" fill="none">')
add('<circle r="16" stroke-width=".3"/><circle r="14.8" stroke-width=".16"/>')
for angle in range(0,360,45):
    length=24 if angle%90==0 else 13
    add(f'<g transform="rotate({angle})"><path d="M0,{-length}L3,0H0Z" fill="#746d49" stroke-width=".3"/><path d="M0,{-length}L-3,0H0Z" fill="#e6d6b0" stroke-width=".3"/></g>')
add('<circle r="2" fill="#8a5355" stroke-width=".4"/><g stroke="none"><text x="0" y="-29" text-anchor="middle" font-size="5">N</text><text x="31" y="1.5" text-anchor="middle" font-size="3.5">E</text><text x="0" y="33" text-anchor="middle" font-size="3.5">S</text><text x="-31" y="1.5" text-anchor="middle" font-size="3.5">O</text></g></g>')
root.append(node(''.join(ornaments)))

# Small, low-contrast flecks give the proof texture while remaining vector objects.
rng=random.Random(19)
flecks=[]
for i in range(2200):
    x,y=rng.uniform(8,592),rng.uniform(8,892)
    flecks.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rng.uniform(.035,.18):.3f}"/>')
root.append(node('<g id="paper-grain" fill="#8d6d42" opacity=".085">'+''.join(flecks)+'</g>'))
assert original_geometry == [e.attrib['d'] for e in root.iter() if 'data-name' in e.attrib]
svg=ET.tostring(root,encoding='unicode')
(WORK/'nuits-D-decorated-01.svg').write_text(svg,encoding='utf-8')
(WORK/'nuits-D-decorated-01.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Côte de Nuits</title><style>body{margin:0;background:#d9c7a3}svg{display:block;width:100%;height:auto}</style>'+svg,encoding='utf-8')
print(f'Decorated proof created. Verified {len(original_geometry)} named geographic paths preserved.')
