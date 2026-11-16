from pathlib import Path
r=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
s=(r/'build_v2.py').read_text(encoding='utf-8')
start=s.index('P={');end=s.index('for p in P.values():',start)
s=s[:start]+'''P={
 'nuits':{'frame':[24,86,270,708],'map':[31,112,256,654],'origin':[848000,6677800],'title':'CÔTE DE NUITS','subtitle':'De Marsannay à Corgoloin','scale':2000,'extent':[843000,6665800,853500,6689800]},
 'beaune':{'frame':[304,86,272,708],'map':[311,112,258,392],'origin':[835500,6656000],'title':'CÔTE DE BEAUNE','subtitle':'De Corton aux Maranges','scale':2000,'extent':[824500,6643500,845000,6668300]},
 'overview':{'frame':[31,113,112,172],'map':[36,138,102,126],'origin':[800000,6665000],'extent':[734000,6571000,861000,6761000],'title':'LA BOURGOGNE','subtitle':'Situation de la Côte d’Or','scale':20000},
 'vosne':{'frame':[160,550,127,236],'map':[166,575,115,128],'origin':[848000,6675800],'title':'A · VOSNE-ROMANÉE','subtitle':'Les grands crus','scale':250,'names':vosne},
 'montrachet':{'frame':[318,535,244,251],'map':[325,562,127,190],'origin':[832300,6650900],'title':'B · MONTRACHET','subtitle':'Les cinq grands crus','scale':250,'names':montrachet},
}
for key,p in P.items():
    # Geographic north at the map centre, correcting Lambert-93 convergence only.
    gx,gy=p['origin'];lon,lat=inverse.transform(gx,gy);nx,ny=forward.transform(lon,lat+.005)
    p['rotation']=math.degrees(math.atan2(nx-gx,ny-gy))
    if key in ['vosne','montrachet']:
        from shapely.affinity import translate
        g=translate(rotate(unary_union([G[id(GC[n])] for n in p['names']]),p['rotation'],origin=p['origin']),-gx,-gy)
        l,b,r,t=g.bounds;pad=100 if key=='vosne' else 85
        p['bounds']=[l-pad,b-pad,r+pad,t+pad]
    else:
        l,b,r,t=p['extent'];corners=[local(p,x,y) for x,y in [(l,b),(l,t),(r,b),(r,t)]]
        p['bounds']=[min(a for a,b in corners),min(b for a,b in corners),max(a for a,b in corners),max(b for a,b in corners)]
''' +s[end:]
s=s.replace('Bourgogne — composition 02','Côte d’Or — étude orientée au nord')
s=s.replace('Cartes de détail de la Côte de Nuits et de la Côte de Beaune, orientées le long de la côte sans déformation. Carte d’ensemble et agrandissements de Vosne et de Montrachet.','Côte de Nuits et Côte de Beaune orientées au nord géographique. Situation en Bourgogne et agrandissements des grands crus.')
s=s.replace("txt(300,59,'BOURGOGNE',25", "txt(300,59,'CÔTE D’OR',25")
s=s.replace("'Climats, villages & grands domaines'","'Bourgogne · Climats, villages & grands domaines'")
s=s.replace("p['title'],5.1 if key in ['nuits','beaune'] else 4.5", "p['title'],5.1 if key in ['nuits','beaune'] else 3.5 if key in ['overview','vosne'] else 4.5")
s=s.replace("p['subtitle'],3.4", "p['subtitle'],2.9 if key=='overview' else 3.4")
s=s.replace("labels.sort(key=lambda z:z[1]);ys=distribute([r[1] for r in labels],6.1,my+22,my+mh-18)", "labels.sort(key=lambda z:z[1]);ys=distribute([r[1] for r in labels],6.1,300 if key=='nuits' else my+22,my+mh-18)")
# Village labels near the lower Nuits inset go to the west of their point.
s=s.replace("tx=min(a+4,fx+fw-5-tw)", "tx=min(a+4,fx+fw-5-tw)\n            if key=='nuits' and yy>545:tx=max(fx+7,a-tw-4)")
ov_start=s.index("    elif key=='overview':")
ov_end=s.index("    else:\n        # Index numbers",ov_start)
s=s[:ov_start]+'''    elif key=='overview':
        for n in ['Auxerre','Chablis','Dijon','Beaune','Chalon-sur-Saône','Mâcon']:
            a,b=mapxy(p,*towns[n]['xy']);tx=a-2;anchor='end';yy=b
            if n=='Chablis':tx=a+2;anchor='start';yy=b-2
            if n=='Auxerre':yy=b+4
            if n=='Beaune':yy=b+4
            point(a,b,.5);txt(tx,yy,n,2.9,'halo',anchor,key)
        # The location inset links the two independent detailed map frames.
        for k in ['nuits','beaune']:
            q=P[k];l,b,r,t=q['bounds'];ang=-math.radians(q['rotation']);pts=[]
            for xx,yy in [(l,b),(l,t),(r,t),(r,b)]:
                gx=math.cos(ang)*xx-math.sin(ang)*yy+q['origin'][0];gy=math.sin(ang)*xx+math.cos(ang)*yy+q['origin'][1];pts.append(mapxy(p,gx,gy))
            add('<path d="M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in pts)+'Z" fill="none" stroke="#89474e" stroke-width=".45"/>')
''' +s[ov_end:]
st=s.index("        names=p['names'];start=");en=s.index('    # Metric scale bar',st)
s=s[:st]+'''        # Keys occupy each inset's available space rather than a repeated left column.
        for i,n in enumerate(p['names']):
            if key=='vosne':xx=fx+7;yy=fy+168+i*7
            else:xx=fx+143;yy=fy+68+i*23
            txt(xx,yy,str(i+1),3.25,'cru',panel=key)
            ls=wrap(n,106 if key=='vosne' else 87,3.5)
            for j,part in enumerate(ls):txt(xx+5,yy+j*4.5,part,3.5,'cru',panel=key)
''' +s[en:]
s=s.replace("if key in ['vosne','montrachet']:sx=fx+7;sy=fy+153 if key=='vosne' else fy+163\n    else:sx=fx+8;sy=fy+fh-10", "if key=='vosne':sx=fx+7;sy=fy+155\n    elif key=='beaune':sx=fx+10;sy=516\n    else:sx=fx+8;sy=fy+fh-10")
# All requested details must fit their map frame; measure retained GC area and north error.
st=s.index("quality={'version':2")
en=s.index("print(json.dumps",st)
s=s[:st]+'''from shapely.affinity import translate
coverage=[]
for key in ['nuits','beaune']:
    p=P[key]
    for n,f in GC.items():
        if n=='Chablis Grand Cru':continue
        belongs_beaune=n in montrachet+['Corton','Corton-Charlemagne','Charlemagne']
        if (key=='beaune')!=belongs_beaune:continue
        g=translate(rotate(G[id(f)],p['rotation'],origin=p['origin']),-p['origin'][0],-p['origin'][1])
        coverage.append({'panel':key,'name':n,'fraction':round(g.intersection(p['clip']).area/g.area,6)})
quality={'version':'cote-north-01','overlaps':overlaps,'projection':'EPSG:2154','north_up':True,'meridian_corrections':{k:p['rotation'] for k,p in P.items()},'grands_crus_coverage':coverage,'panels':5,'dimensions_mm':[600,900]}
(ROOT/'checks/layout-cote-north-01.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
''' +s[en:]
s=s.replace("for i,e in enumerate(estates):", "for i,e in enumerate([e for e in estates if e['region'] in ['Côte de Nuits','Côte de Beaune']]):")
s=s.replace("col=i//5;row=i%5", "col=i//4;row=i%4")
s=s.replace("txt(x,y,e['id']", "txt(x,y,f'{i+1:02}'")
s=s.replace('Composition 02 · INAO','Côte d’Or · Étude de composition · INAO')
s=s.replace('composition-v02.svg','cote-north-01.svg').replace('layout-v02.json','layout-cote-north-01.json')
s=s.replace("tx=fx+6\n            size=3.75", "size=3.75\n            tx=fx+6")
s=s.replace("end=tx+tw+1.5", "tx=max(fx+7,a-tw-12)\n            end=tx+tw+1.5")
s=s.replace("q[0]-3,q[1]-3,'A' if key=='nuits' else 'B'", "q[0]-3,q[1]-(3 if key=='nuits' else 10),'A' if key=='nuits' else 'B'")
s=s.replace("q[0]-3,q[1]-(3 if key=='nuits' else 10)", "(max(a for a,b in corners)+6) if key=='nuits' else q[0]-3,q[1]-(9 if key=='nuits' else 10)")
(r/'build_cote_north.py').write_text(s,encoding='utf-8')
print('Created build_cote_north.py')
