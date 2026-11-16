from pathlib import Path
r=Path(r'C:/Users/32697/Desktop/thuwine/map_builder')
s=(r/'build_cote_north.py').read_text(encoding='utf-8')
st=s.index('P={');en=s.index('for key,p in P.items():',st)
s=s[:st]+'''P={
 'cote':{'frame':[24,86,552,708],'map':[31,108,538,658],'origin':[840000,6666500],'title':'','subtitle':'','scale':5000,'extent':[823000,6643500,855000,6689800]},
 'overview':{'frame':[31,108,140,210],'map':[37,133,128,161],'origin':[800000,6665000],'extent':[734000,6571000,861000,6761000],'title':'LA BOURGOGNE','subtitle':'Situation de la Côte d’Or','scale':20000},
 'vosne':{'frame':[446,348,124,225],'map':[452,373,112,128],'origin':[848000,6675800],'title':'A · VOSNE-ROMANÉE','subtitle':'Les grands crus','scale':250,'names':vosne},
 'montrachet':{'frame':[387,586,183,200],'map':[394,612,169,112],'origin':[832300,6650900],'title':'B · MONTRACHET','subtitle':'Les cinq grands crus','scale':250,'names':montrachet},
}
''' +s[en:]
s=s.replace("if key in ['nuits','beaune']:", "if key=='cote':")
s=s.replace("5.1 if key in ['nuits','beaune'] else 3.5", "5.1 if key=='cote' else 3.5")
s=s.replace("300 if key=='nuits' else my+22", "my+22")
s=s.replace("ns=nuit_names if key=='nuits' else beaune_names", "ns=nuit_names+beaune_names")
s=s.replace("if key=='nuits' and yy>545:tx=max(fx+7,a-tw-4)", "if n in ['Pernand-Vergelesses','Savigny-lès-Beaune','Saint-Romain','Auxey-Duresses','Saint-Aubin','Premeaux-Prissey','Comblanchien','Corgoloin']:tx=max(fx+7,a-tw-4)")
st=s.index('        # Small-letter reference to inset');en=s.index("    elif key=='overview':",st)
s=s[:st]+'''        for letter,names in [('A',vosne),('B',montrachet)]:
            g=unary_union([G[id(GC[n])] for n in names]);b=g.bounds
            corners=[mapxy(p,x,y) for x,y in [(b[0],b[1]),(b[0],b[3]),(b[2],b[3]),(b[2],b[1])]]
            add('<path d="M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in corners)+'Z" fill="none" stroke="#685e44" stroke-width=".45" stroke-dasharray="1.4 1"/>')
            q=min(corners,key=lambda z:z[1]);txt(q[0]-4,(max(b for a,b in corners)+6) if letter=='A' else q[1]-6,letter,4.7,'title halo','end',key)
        txt(327,147,'CÔTE DE NUITS',5.5,'title caps halo','middle',key)
        txt(152,557,'CÔTE DE BEAUNE',5.5,'title caps halo','middle',key)

''' +s[en:]
s=s.replace("for k in ['nuits','beaune']:", "for k in ['cote']:")
s=s.replace("else:xx=fx+143;yy=fy+68+i*23", "else:xx=fx+7+(i//3)*87;yy=fy+163+(i%3)*10")
s=s.replace("106 if key=='vosne' else 87", "106 if key=='vosne' else 74")
s=s.replace("elif key=='beaune':sx=fx+10;sy=516", "elif key=='montrachet':sx=fx+7;sy=fy+145")
# A single map frame and transform covers both Nuits and Beaune, including their junction.
s=s.replace("for key in ['nuits','beaune']:", "for key in ['cote']:")
s=s.replace("        if (key=='beaune')!=belongs_beaune:continue\n",'')
s=s.replace("'panels':5", "'panels':4,'continuous_main_map':True,'shared_main_scale':True")
s=s.replace('cote-north-01','cote-connected-01')
s=s.replace('Côte de Nuits et Côte de Beaune orientées au nord géographique.', 'Une carte continue de la Côte de Nuits et de la Côte de Beaune, à la même échelle et orientée au nord géographique.')
s=s.replace("'Échelles propres à chaque carte'", "'Carte principale continue · Nord en haut'")
s=s.replace('print(json.dumps(quality,ensure_ascii=True),flush=True)', "print(json.dumps({'version':quality['version'],'overlaps':overlaps,'gc_count':len(coverage),'minimum_gc_coverage':min(c['fraction'] for c in coverage)},ensure_ascii=True),flush=True)")
s=s.replace("g=translate(g,-p['origin'][0],-p['origin'][1])", "g=make_valid(translate(g,-p['origin'][0],-p['origin'][1]))")
s=s.replace("px=fx+fw-10;py=sy-1", "px=fx+fw-10;py=115 if key=='cote' else sy-1")
s=s.replace("quality={'version':", "inset_occlusions=[]\nfor label in TEXTS:\n    if label['panel']!='cote':continue\n    for k in ['overview','vosne','montrachet']:\n        x,y,w,h=P[k]['frame']\n        if box(*label['box']).intersection(box(x,y,x+w,y+h)).area>.3:inset_occlusions.append({'text':label['text'],'inset':k})\nquality={'inset_occlusions':inset_occlusions,'version':")
s=s.replace("'gc_count':len(coverage)", "'inset_occlusions':inset_occlusions,'gc_count':len(coverage)")
(r/'build_cote_connected.py').write_text(s,encoding='utf-8')
print('Created continuous-map renderer')
