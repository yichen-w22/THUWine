from pathlib import Path
r=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
s=(r/'build_nuits_insets.py').read_text(encoding='utf-8')
needle="GC={f['properties']['name']:f for f in grands}"
insert='''# Display-only selection: omit peripheral regional polygons in the
# southwest of the main map. Original geographical data remain intact.
regional_main={};regional_omitted=[]
for f in areas:
    if f['properties']['class']!='regional':continue
    source=G[id(f)];parts=list(source.geoms) if hasattr(source,'geoms') else [source];keep=[]
    for part in parts:
        q=part.representative_point()
        omit=839000<q.x<844600 and 6666500<q.y<6674500
        if omit:regional_omitted.append({'bounds':list(part.bounds),'area_m2':round(part.area,2)})
        else:keep.append(part)
    regional_main[id(f)]=unary_union(keep)
'''
assert needle in s;s=s.replace(needle,insert+needle)
s=s.replace("g=rotate(G[id(f)],p.get('rotation',0),origin=p['origin'])", "source=regional_main.get(id(f),G[id(f)]) if p is P['cote'] else G[id(f)]\n    g=rotate(source,p.get('rotation',0),origin=p['origin'])")
s=s.replace('nuits-atlas-02','nuits-atlas-03')
s=s.replace("'regional_layer':'muted_main_omitted_insets'", "'regional_layer':'muted_main_with_southwest_selection_omitted_insets','regional_polygons_omitted':regional_omitted")
s=s.replace("'gc_count':len(coverage)", "'regional_polygons_omitted':len(regional_omitted),'gc_count':len(coverage)")
(r/'build_nuits_focus.py').write_text(s,encoding='utf-8')
print('Prepared selective regional background')
