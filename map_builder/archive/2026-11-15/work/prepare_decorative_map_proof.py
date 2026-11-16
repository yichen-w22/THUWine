from pathlib import Path
import xml.etree.ElementTree as ET

root_dir = Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
work = Path(__file__).resolve().parent
ns = 'http://www.w3.org/2000/svg'
ET.register_namespace('', ns)
root = ET.parse(root_dir / 'nuits-arrangement-D.svg').getroot()
changes = {
    '#source-gevrey': (570, 100, 570, 104),
    '#source-vosne': (570, 448.39645, 570, 390),
}
for element in list(root):
    use = element.find(f'{{{ns}}}use')
    if use is None or use.get('href') not in changes:
        continue
    anchor_x, anchor_y, target_x, target_y = changes[use.get('href')]
    wrapper = ET.Element(f'{{{ns}}}g', {
        'transform': f'translate({target_x-.85*anchor_x},{target_y-.85*anchor_y}) scale(.85)'
    })
    index = list(root).index(element)
    root.remove(element)
    wrapper.append(element)
    root.insert(index, wrapper)
root.set('aria-label', 'Côte de Nuits — composition D, détails réduits')
ET.ElementTree(root).write(work / 'nuits-d-proof-base.svg', encoding='utf-8', xml_declaration=True)
print('Prepared D composition with inset width and height reduced by 15 percent.')
