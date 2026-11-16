from pathlib import Path
r=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
s=(r/'build_nuits_atlas.py').read_text(encoding='utf-8')
s=s.replace("'regional':'#d8d1b6'", "'regional':'#e8e3d3'")
s=s.replace("'map':[38,325,85,180]", "'map':[85,328,82,174]")
s=s.replace("'frame':[420,540,150,246],'map':[427,566,136,136]", "'frame':[380,554,190,232],'map':[434,582,82,174]")
# No regional parcel pattern in the detailed insets. Neighbouring higher-level
# vineyards remain faint context; selected grands crus keep the full colour.
s=s.replace("    for cat in ['neighbour','regional','village','premier','grand']:\n", "    for cat in ['neighbour','regional','village','premier','grand']:\n        if key in ['gevrey','vosne'] and cat in ['neighbour','regional','grand']:continue\n")
s=s.replace("add(f'<path d=\"{path(g,p)}\" fill=\"{C[cat]}\" fill-rule=\"evenodd\"/>')", "opacity=.22 if key in ['gevrey','vosne'] and cat!='grand' else 1\n            add(f'<path d=\"{path(g,p)}\" fill=\"{C[cat]}\" fill-opacity=\"{opacity}\" fill-rule=\"evenodd\"/>')")
s=s.replace("    for f in grands:\n        g=geom(p,f)", "    for f in grands:\n        if key in ['gevrey','vosne'] and f['properties']['name'] not in p['names']:continue\n        g=geom(p,f)")
st=s.index('    else:\n        # Index numbers');en=s.index('    sl=p[',st)
s=s[:st]+'''    else:
        # The map remains at the centre; full names sit beside their actual
        # locations in monotone north-to-south order on each side.
        west=set(['Chambertin','Chambertin-Clos de Bèze','Mazis-Chambertin','Ruchottes-Chambertin','Latricières-Chambertin'] if key=='gevrey' else ['Richebourg','La Romanée','Romanée-Conti','La Grande Rue','La Tâche'])
        left_x=fx+47;right_x=fx+fw-47
        for side in ['west','east']:
            items=[]
            for n in p['names']:
                if key=='gevrey' and n=='Mazoyères-Chambertin':continue
                if (n in west)!=(side=='west'):continue
                a,b=mapxy(p,*GC[n]['properties']['label_xy']);items.append((a,b,n))
            items.sort(key=lambda z:z[1])
            ys=distribute([b for a,b,n in items],15,fy+43,fy+fh-40)
            for (a,b,n),yy in zip(items,ys):
                # Wrap only at real word/hyphen boundaries while preserving
                # the full French name and its spelling.
                size=3.65;maxw=40
                pieces=n.replace('-', '- ').split();lines=['']
                for word in pieces:
                    candidate=(lines[-1]+('' if lines[-1].endswith('-') else ' ')+word).strip()
                    if lines[-1] and fonts['italic'].getlength(candidate)/1000*size>maxw:lines.append(word)
                    else:lines[-1]=candidate
                if key=='gevrey' and n=='Charmes-Chambertin':lines=['Charmes-Chambertin','/ Mazoyères-Chambertin']
                if n=='Chambertin-Clos de Bèze':lines=['Chambertin-','Clos de Bèze']
                x=left_x if side=='west' else right_x;anchor='end' if side=='west' else 'start'
                lx=x+2 if side=='west' else x-2
                end_y=yy-1.2
                line(lx,end_y,a,b,'leader')
                add(f'<circle cx="{a:.2f}" cy="{b:.2f}" r=".55" fill="#f6efdc" stroke="#743e49" stroke-width=".15"/>')
                for j,part in enumerate(lines):txt(x,yy+(j-(len(lines)-1)/2)*4.5,part,size,'cru',anchor,key)
        line(fx+8,fy+fh-25,fx+fw-8,fy+fh-25)
        if key=='gevrey':txt(fx+54,fy+fh-11,'Charmes / Mazoyères : aire INAO commune.',2.9,'italic muted',panel=key)
    sx=fx+8;sy=fy+fh-10
''' +s[en:]
s=s.replace('nuits-atlas-01','nuits-atlas-02')
s=s.replace("'version':'nuits-atlas-02'", "'version':'nuits-atlas-02','inset_labels':'direct_names_two_sides','regional_layer':'muted_main_omitted_insets'")
(r/'build_nuits_insets.py').write_text(s,encoding='utf-8')
print('Prepared inset revision 02')
