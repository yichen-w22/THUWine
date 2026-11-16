"""Editorial evidence and the proposed (not yet approved) estate selection."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent; D=ROOT/'data'
rows=[
('François Raveneau','Chablis','Chablis',55,'https://www.chablis.fr/carte-interactive-des-vins-de-chablis/carte-interactive-des-vins-de-chablis,2787,10482.html'),
('Vincent Dauvissat','Chablis','Chablis',55,'https://www.chablis.fr/visitez/les-maisons-et-domaines/dauvissat-vincent-chablis-89800,3297,16015.html?args=Y29tcF9pZD0yNTc1JmFjdGlvbj12aWV3RmljaGUmaWQ9VklOQk9VMDAwMDIwMTIxNyZ8'),
('Armand Rousseau','Gevrey-Chambertin','Côte de Nuits',66,'https://mobile.domaine-rousseau.com/contact'),
('Dujac','Morey-Saint-Denis','Côte de Nuits',66,'https://www.dujac.com/contact'),
('Clos de Tart','Morey-Saint-Denis','Côte de Nuits',66,'https://www.clos-de-tart.com/fr/contact'),
('Georges Roumier','Chambolle-Musigny','Côte de Nuits',65,'https://www.roumier.com/fr_FR/mentions-legales'),
('Comte Georges de Vogüé','Chambolle-Musigny','Côte de Nuits',65,'https://annuaire-entreprises.data.gouv.fr/entreprise/778173518'),
('Domaine de la Romanée-Conti','Vosne-Romanée','Côte de Nuits',64,'https://www.romanee-conti.fr/fr/mentions'),
('Leroy','Vosne-Romanée','Côte de Nuits',58,None),
('Méo-Camuzet','Vosne-Romanée','Côte de Nuits',58,'https://www.meo-camuzet.com/fr/contacts'),
('Faiveley','Nuits-Saint-Georges','Côte de Nuits',55,'https://domaine-faiveley.com/contact/'),
('Louis Latour','Beaune','Côte de Beaune',55,'https://www.louislatour.com/fr/contact'),
('Joseph Drouhin','Beaune','Côte de Beaune',62,'https://www.drouhin.com/fr_FR/contacts'),
('Comtes Lafon','Meursault','Côte de Beaune',69,None),
('Roulot','Meursault','Côte de Beaune',60,'https://www.vins-bourgogne.fr/vignerons-savoir-faire/femmes-et-hommes-passionnes/roulot-meursault-21190,2397,9211.html?args=Y29tcF9pZD0xNDA2JmFjdGlvbj12aWV3RmljaGUmaWQ9VklOQk9VMDAwMDIwMTAxNCZ8'),
('Leflaive','Puligny-Montrachet','Côte de Beaune',69,'https://www.leflaive.fr/fr_FR/mentions-legales'),
('de Villaine','Bouzeron','Côte Chalonnaise',68,'https://boutique.de-villaine.com/fr_FR/page/mentions-legales'),
('François Lumpp','Givry','Côte Chalonnaise',68,'https://francoislumpp.com/fr/contact/'),
('Château Fuissé','Fuissé','Mâconnais',70,'https://chateau-fuisse.fr/contact/'),
('Guffens-Heynen','Vergisson','Mâconnais',70,None)]
estates=[]
for i,(name,commune,region,page,url) in enumerate(rows,1):
    estates.append({'id':f'{i:02d}','name':name,'commune':commune,'region':region,
        'book_context_page':page,'book_context_pdf_page':page+4,
        'book_context_note':'Page de contexte géographique, ne constitue pas à elle seule une attestation du producteur.',
        'supplementary_source':url,'selection_status':'proposed','site_coordinates':None,
        'site_status':'precise_estate_location_pending','display_policy':'index_only_no_unverified_point'})
(D/'estates.json').write_text(json.dumps(estates,ensure_ascii=False,indent=2),encoding='utf-8')

sections=[
 {'book_pages':[54,55],'pdf_pages':[58,59],'title':'Bourgogne','findings':['La Côte d’Or réunit la Côte de Nuits au nord et la Côte de Beaune au sud.','Une même exploitation peut posséder des parcelles dans plusieurs villages : le siège du domaine et ses vignes sont deux objets différents.','La carte générale inclut le Beaujolais au sud ; il reste ici un voisin de contexte.']},
 {'book_pages':[56,57,58],'pdf_pages':[60,61,62],'title':'Côte d’Or et hiérarchie','findings':['Le relief, les combes et les sols doivent expliquer visuellement la continuité de la côte.','Les Hautes-Côtes forment des vignobles distincts à l’ouest de la côte principale.','Les limites de propriété illustrées à Richebourg ne doivent pas être confondues avec les limites d’appellation.','Le livre mentionne 31 grands crus en exploitation en Côte d’Or ; ce décompte ne doit pas remplacer les 32 AOC juridiques de Côte d’Or, dont Charlemagne.']},
 {'book_pages':[59],'pdf_pages':[63],'title':'Côte de Beaune méridionale','findings':['Santenay et Chassagne-Montrachet assurent la transition méridionale.','Les planches détaillées sont tournées de 45 à 90 degrés selon la page ; ne pas les assembler sans réorientation.']},
 {'book_pages':[60,61],'pdf_pages':[64,65],'title':'Montrachet, Meursault et Volnay','findings':['Séparer les villages Puligny-Montrachet et Chassagne-Montrachet du grand cru Montrachet.','Prévoir un agrandissement pour les cinq grands crus du groupe Montrachet.','Perrières à Meursault et les grands climats de Volnay sont des premiers crus, non des grands crus.']},
 {'book_pages':[62,63],'pdf_pages':[66,67],'title':'Beaune et Corton','findings':['La ville de Beaune ne possède pas de grand cru ; les grands crus apparaissent plus au nord sur la colline de Corton.','Corton et Corton-Charlemagne peuvent présenter des aires éligibles qui se superposent : préserver les appartenances multiples.']},
 {'book_pages':[64,65],'pdf_pages':[68,69],'title':'Nuits-Saint-Georges, Vosne et Chambolle','findings':['Les Saint-Georges et Les Amoureuses doivent rester classés premiers crus.','Séparer le Clos de Vougeot du village de Vougeot et du domaine propriétaire.','La Romanée, Romanée-Conti et Romanée-Saint-Vivant sont des appellations distinctes.','Réserver un agrandissement à Vosne-Romanée pour les petits grands crus.']},
 {'book_pages':[66,67],'pdf_pages':[70,71],'title':'Morey, Gevrey, Fixin et Marsannay','findings':['Les neuf grands crus de Gevrey et les clos de Morey imposent une gestion attentive des étiquettes.','Bonnes-Mares déborde sur Morey-Saint-Denis : ne pas découper le grand cru selon les communes.','Les données de classement de Marsannay seront vérifiées lors de la finalisation.']},
 {'book_pages':[68],'pdf_pages':[72],'title':'Côte Chalonnaise','findings':['Faire apparaître Bouzeron, Rully, Mercurey, Givry et Montagny.','Bouzeron est associé à l’aligoté ; Montagny aux blancs.','Le livre fournit des repères pour de Villaine et François Lumpp.']},
 {'book_pages':[69],'pdf_pages':[73],'title':'Mâconnais','findings':['Viré-Clessé, Saint-Véran et les appellations Pouilly doivent être différenciés.','La Saône constitue un repère de paysage à l’est ; ne pas plaquer une frontière régionale artificielle sur ses berges.']},
 {'book_pages':[70,71],'pdf_pages':[74,75],'title':'Pouilly-Fuissé','findings':['Le livre décrit encore la promotion en premier cru comme un projet.','Actualisation BIVB : 22 climats classés premiers crus depuis le 21 novembre 2020.','Les roches de Solutré et Vergisson sont des repères de relief réels, à traiter à la phase de style.']}
]
sources=[
 {'id':'book','title':'L’Atlas mondial du vin, 8e édition, édition chinoise','location':r'C:\Users\32697\Desktop\thuwine\世界葡萄酒地图.pdf','pages':'Livre 54–71 / PDF 58–75','method':'Lecture visuelle des 18 pages ; images conservées localement. Aucune transcription OCR automatique prétendue.'},
 {'id':'inao','title':'INAO — Délimitation parcellaire des AOC viticoles','url':'https://www.data.gouv.fr/datasets/delimitation-parcellaire-des-aoc-viticoles-de-linao','service':'https://data.geopf.fr/wfs/ows','layer':'AOC-VITICOLES:aire_parcellaire','license':'Licence Ouverte','retrieved':'2026-11-12','caution':'La date du service WFS ne garantit pas la même édition que le ZIP du 9 novembre 2026. Géométries informatives ; les plans officiels font foi.'},
 {'id':'hydro','title':'IGN — BD CARTO V5, tronçons hydrographiques','url':'https://data.geopf.fr/wfs/ows','layer':'BDCARTO_V5:troncon_hydrographique','license':'Licence Ouverte','retrieved':'2026-11-12'},
 {'id':'places','title':'IGN / Base Adresse Nationale — géocodage des communes','url':'https://data.geopf.fr/geocodage/search','retrieved':'2026-11-12','caution':'Points représentatifs de communes ; ne pas les réutiliser comme coordonnées des domaines.'},
 {'id':'pf-update','title':'BIVB — Pouilly-Fuissé et ses 22 premiers crus','url':'https://www.bourgogne-wines.com/wine-and-terroir/bourgogne-and-its-appellations/gallery_files/site/321/402/57644/71032.pdf'},
 {'id':'chablis','title':'BIVB — Cartes de Chablis','url':'https://www.chablis-wines.com/downloads/maps,1873,7714.html','caution':'Un Chablis Grand Cru, sept climats ; le périmètre du livre retenu ne comporte pas de planche détaillée autonome de Chablis.'}
]
(D/'research.json').write_text(json.dumps({'sections':sections,'sources':sources,'next_checks':['Adresses exactes des 20 domaines','Plan de contrôle des 33 AOC grands crus et leurs recouvrements','Relief et occupation du sol','Actualité des premiers crus et de Marsannay','Compléter les trois premiers crus non appariés par nom exact']},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'stage.json').write_text(json.dumps({'stage':1,'name':'composition','awaiting':'user_composition_review','style_approved':False,'print_ready':False,'final_exports_generated':False},indent=2),encoding='utf-8')
print('Editorial metadata: 20 proposed estates, 10 book sections, 6 source records.')
