from pathlib import Path

root = Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
source = (root / 'build_nuits_focus.py').read_text(encoding='utf-8')
source = source.replace("'map':[31,108,538,658]", "'map':[31,96,538,682]")
source = source.replace("'extent':[839500,6666800,855000,6691300]", "'extent':[843600,6668800,853000,6689900]")
source = source.replace("'frame':[31,300,190,232],'map':[85,328,82,174]", "'frame':[31,296,156,282],'map':[38,322,142,230]")
source = source.replace("'frame':[380,554,190,232],'map':[434,582,82,174]", "'frame':[401,493,169,293],'map':[408,519,155,240]")
source = source.replace("'Bourgogne · De Marsannay à Corgoloin'", "'Bourgogne · De Marsannay à Premeaux-Prissey'")
source = source.replace("ns=nuit_names+['Flagey-Echézeaux']", "ns=[name for name in nuit_names if name not in ['Comblanchien','Corgoloin']]+['Flagey-Echézeaux']")

start = source.index('    else:\n        # The map remains at the centre')
end = source.index('    sx=fx+8;sy=fy+fh-10', start)
replacement = '''    else:
        # Large parcels carry their names. Tiny parcels use nearby callouts.
        inset_lines = {
            'Chambertin':['Chambertin'],
            'Chambertin-Clos de Bèze':['Chambertin-','Clos de Bèze'],
            'Mazis-Chambertin':['Mazis-','Chambertin'],
            'Ruchottes-Chambertin':['Ruchottes-','Chambertin'],
            'Chapelle-Chambertin':['Chapelle-','Chambertin'],
            'Griotte-Chambertin':['Griotte-','Chambertin'],
            'Charmes-Chambertin':['Charmes-Chambertin','/ Mazoyères-','Chambertin'],
            'Latricières-Chambertin':['Latricières-','Chambertin'],
            'Échezeaux':['Échezeaux'],
            'Grands Échezeaux':['Grands','Échezeaux'],
            'Richebourg':['Richebourg'],
            'Romanée-Saint-Vivant':['Romanée-','Saint-Vivant'],
            'La Tâche':['La Tâche'],
        }
        outside = {'gevrey':['Ruchottes-Chambertin','Mazis-Chambertin','Griotte-Chambertin'],
                   'vosne':['La Romanée','Romanée-Conti','La Grande Rue']}[key]
        for name in p['names']:
            if name in outside or name=='Mazoyères-Chambertin':continue
            x,y=mapxy(p,*GC[name]['properties']['label_xy'])
            lines=inset_lines.get(name,[name])
            font_size=3.5 if key=='gevrey' else 3.8
            parcel=geom(p,GC[name])
            label_width=max(fonts['italic'].getlength(part)/1000*font_size for part in lines)+.8
            label_height=len(lines)*4.4+.8
            half_width=label_width/p['factor']/2
            half_height=label_height/p['factor']/2
            left,bottom,right,top=parcel.bounds
            candidates=[local(p,*GC[name]['properties']['label_xy'])]
            candidates += [(left+(right-left)*i/12,bottom+(top-bottom)*j/12) for i in range(1,12) for j in range(1,12)]
            best=None
            original=candidates[0]
            for candidate_x,candidate_y in candidates:
                footprint=box(candidate_x-half_width,candidate_y-half_height,candidate_x+half_width,candidate_y+half_height)
                fraction=parcel.intersection(footprint).area/footprint.area
                distance=math.hypot(candidate_x-original[0],candidate_y-original[1])
                score=(round(fraction,5),-distance)
                if best is None or score>best[0]:best=(score,candidate_x,candidate_y)
            x,y=maplocal(p,best[1],best[2])
            for index,part in enumerate(lines):
                baseline=y+(index-(len(lines)-1)/2)*4.4+1.2
                txt(x,baseline,part,font_size,'inset-name','middle',key)
        callouts=[]
        for name in outside:
            x,y=mapxy(p,*GC[name]['properties']['label_xy'])
            callouts.append((x,y,name))
        callouts.sort(key=lambda item:item[1])
        positions=distribute([y for x,y,name in callouts],13,fy+43,fy+fh-39)
        for (x,y,name),baseline in zip(callouts,positions):
            right=name=='Griotte-Chambertin'
            parcel=geom(p,GC[name])
            left,bottom,right_bound,top=parcel.bounds
            west_edge=maplocal(p,left,0)[0]
            east_edge=maplocal(p,right_bound,0)[0]
            label_x=min(fx+fw-30,east_edge+5) if right else max(fx+28,west_edge-5)
            if key=='gevrey' and name in ['Ruchottes-Chambertin','Mazis-Chambertin']:label_x=fx+46
            anchor='start' if right else 'end'
            lines=inset_lines.get(name,[name])
            line(label_x-2 if right else label_x+2,baseline-1,x,y,'leader')
            add(f'<circle cx="{x:.2f}" cy="{y:.2f}" r=".5" fill="#f6efdc" stroke="#743e49" stroke-width=".15"/>')
            for index,part in enumerate(lines):
                txt(label_x,baseline+(index-(len(lines)-1)/2)*4.2,part,3.6,'cru inset-callout',anchor,key)
        line(fx+8,fy+fh-25,fx+fw-8,fy+fh-25)
        if key=='gevrey':txt(fx+40,fy+fh-11,'Charmes / Mazoyères : aire INAO commune.',2.9,'italic muted',panel=key)
'''
source = source[:start] + replacement + source[end:]
source = source.replace('.caps{letter-spacing:.55px}', '.caps{letter-spacing:.55px}.inset-callout{paint-order:stroke;stroke:#f4efdf;stroke-width:.5}.inset-name{fill:#fff3dc;font-style:italic;paint-order:stroke;stroke:#814751;stroke-width:.3;stroke-linejoin:round}')
source = source.replace('nuits-atlas-03', 'nuits-atlas-04')
source = source.replace("'inset_labels':'direct_names_two_sides'", "'inset_labels':'large_parcels_inside_small_parcels_callouts','main_extent_description':'Marsannay to Premeaux-Prissey'")
source = source.replace("'gc_count':len(coverage)", "'scale_ratio_vs_previous':round(P['cote']['factor']/.026453694659702855,3),'inset_scale_ratios':{'gevrey':round(P['gevrey']['factor']/.08237805441867246,3),'vosne':round(P['vosne']['factor']/.07481536227313211,3)},'gc_count':len(coverage)")
(root / 'build_nuits_compact.py').write_text(source, encoding='utf-8')
print('Prepared enlarged main map and compact insets')
