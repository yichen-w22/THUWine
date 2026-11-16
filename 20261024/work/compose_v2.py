import base64, json, re, ast
from html import escape
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
root=Path(__file__).resolve().parent
src=Path(r'C:\Users\32697\Desktop\thuwine\20261024')
original=ast.parse((root/'make_draft.py').read_text(encoding='utf-8'))
data={n.targets[0].id:ast.literal_eval(n.value) for n in original.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ['wines','rice']}
wines=data['wines']; rice=data['rice']
wines.append(('甘肃霞多丽干白葡萄酒','WHITE / 06','aec3821ab6a6853dab9cc9d862f9d27c.jpg','100% 霞多丽 · 甘肃武威','葡萄来自甘肃武威，在内蒙古酒庄酿造。带皮启动发酵后分离，在旧橡木桶中发酵，并与酒泥接触6个月。柠檬、桃子与蜜瓜果香中带有清新的植物气息，酸度柔和，酒体轻盈，些许咸鲜感增添了层次。'))
rice=[(n,'RICE WINE / '+str(i+7).zfill(2),f,t,b) for i,(n,e,f,t,b) in enumerate(rice)]

fonts={k:TTFont(p,fontNumber=0) for k,p in [('sans',r'C:\Windows\Fonts\Dengl.ttf'),('serif',r'C:\Windows\Fonts\simsun.ttc')]}
cache={}; parts=[]; clips=0; editable_text=[]; checkpoints={}
blue='#6b343e'; ink='#3e3b3b'; gray='#817875'
def glyph(ch,font):
    key=(font,ch)
    if key not in cache:
        f=fonts[font]; gn=f.getBestCmap().get(ord(ch),'.notdef'); gs=f.getGlyphSet(); pen=SVGPathPen(gs); gs[gn].draw(pen)
        cache[key]=(pen.getCommands(),gs[gn].width,f['head'].unitsPerEm)
    return cache[key]
def width(s,size,font='sans'):
    return sum(glyph(c,font)[1]/glyph(c,font)[2]*size for c in s)
def text(s,x,y,size=36,color=ink,font='sans',bold=False):
    start=len(parts); original_x=x
    for c in s:
        d,adv,upm=glyph(c,font); sc=size/upm
        if d:
            stroke=f' stroke="{color}" stroke-width="{1.5/sc:.4f}" stroke-linejoin="round" paint-order="stroke fill"' if bold else ''
            parts.append(f'<path fill="{color}"{stroke} d="{d}" transform="translate({x:.2f},{y+size:.2f}) scale({sc:.6f},{-sc:.6f})"/>')
        x+=adv*sc
    family='DengXian Light' if font=='sans' else 'SimSun'
    weight='700' if bold else '400'
    editable_text.append((start,len(parts),f'<text x="{original_x}" y="{y+size}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{color}">{escape(s)}</text>'))
def para(s,x,y,w=936,size=39,line=73,color=ink,font='sans'):
    lines=[]; current=''
    for c in re.findall(r'[0-9]+(?:[.–—:][0-9]+)*(?:%|℃)?|[A-Za-z]+|.',s,flags=re.S):
        if c=='\n': lines.append(current);current='';continue
        if width(current+c,size,font)>w and current and c not in '，。！？；：、）》”：': lines.append(current);current=''
        current+=c
    if current:lines.append(current)
    for l in lines:text(l,x,y,size,color,font);y+=line
    return y
def rect(x,y,w,h,color):parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
def rule(y,x=72,w=936):rect(x,y,w,1,'#d9e1e6')
def photo(name,x,y,w,h,crop=None):
    global clips
    from PIL import Image
    p=src/name
    iw,ih=Image.open(p).size
    data=base64.b64encode(p.read_bytes()).decode()
    mime='image/png' if p.suffix.lower()=='.png' else 'image/jpeg'
    if crop:
        cx,cy,cw,ch=crop; scale=min(w/cw,h/ch); clips+=1
        parts.append(f'<clipPath id="c{clips}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath><image href="data:{mime};base64,{data}" x="{x-cx*scale}" y="{y-cy*scale}" width="{iw*scale}" height="{ih*scale}" clip-path="url(#c{clips})"/>')
    else:parts.append(f'<image href="data:{mime};base64,{data}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
def section(en,zh,y):
    text(en,72,y,26,gray); y+=62
    y=para(zh,72,y,size=60,line=82,color=blue,font='serif');return y+30

photo('35e68c4c96d65807754ea3ea7d632867.jpg',143,40,794,122,(180,20,680,105))
y=215
text('清华葡萄酒协会 × 乐为酒庄',72,y,32,gray);y+=85
for title in ['黄河北岸的','风土之旅']:
    text(title,(1080-width(title,112,'serif'))/2,y,112,blue,'serif',bold=True);y+=140
rect(72,y+22,70,3,blue); y+=70
text('探索内蒙古葡萄酒的独特魅力',72,y,36,gray);y+=75
text('品鉴活动招募  /  2026.10.24',72,y,34,blue);y+=95
checkpoints['terroir']=y
y=section('01 / TERROIR','风土介绍',y)
y=para('提到中国葡萄酒，\n你会想到哪里？',72,y,size=44,line=76,color=blue,font='serif')+30
y=para('宁夏贺兰山、山东蓬莱，还是云南香格里拉？这一次，我们把目光投向内蒙古黄河北岸，去认识一片鲜为人知、却极具潜力的葡萄酒产区。',72,y)+40
photo('7f1365a14400ac1dfa6c4e8ecfe23b75.jpg',72,y,936,936,(0,1380,2296,2296));y+=966
text('黄河北岸 · 葡萄园与酒庄',72,y,26,gray);y+=78
checkpoints['facts']=y
rule(y);y+=38
for center,a,b in [(228,'1050 m','葡萄园平均海拔'),(540,'冷凉气候','大陆性气候特征'),(852,'砾质沙壤河滩土','黄河北岸的风土底色')]:
    text(a,center-width(a,40)/2,y,40,blue)
    text(b,center-width(b,28)/2,y+71,28,gray)
y+=142;rule(y);y+=50
y=para('充足的日照与鲜明的昼夜温差，让美乐、马瑟兰、西拉与赤霞珠，在这片土地上展现出不同的个性。',72,y)+30
y=para('本次清华葡萄酒协会携手乐为酒庄（Lewei），从清新细腻的桃红，到层次丰富的干红，一起探索中国本土风土的多样表达。',72,y)+65
checkpoints['winery']=y
y=section('02 / WINERY','酒庄介绍',y)
y=para('内蒙古瑞沃酒庄位于呼和浩特市托克托县，创立于2013年，葡萄园占地约1000亩。这里的葡萄园坐落于黄河北岸坡地，以砾质沙壤河滩土为风土底色。',72,y)+35
photo(Path(r'C:\Users\32697\Desktop\dfa1323fad5354a877ddfda3fd8eae74.jpg'),72,y,936,468,(0,1190,1320,660));y+=503
text('瑞沃酒庄园景',72,y,26,gray);y+=78
y=para('乐为品牌由来自内蒙古的葡萄酒讲师常微与酿酒师王皓泽共同创立。品牌扎根内蒙古的文化与风土，从蒙古族文化中汲取灵感，希望将这里的优质葡萄酒带给更多人。',72,y)+48
y=para('每一张酒标，都有一个故事。',72,y,size=48,line=78,color=blue,font='serif')+20
y=para('乐为将艺术创作与葡萄酒文化相结合。Gallery系列通过艺术家的酒标创作，讲述关于普洁、蒙古马与草原故乡的故事，让每一瓶酒都成为风土与艺术的共同表达。',72,y)+75
photo(root/'wine-group.jpg',72,y,936,624);y+=654
text('乐为酒款与艺术酒标',72,y,26,gray);y+=80
checkpoints['speaker']=y
photo(Path(r'C:\Users\32697\Desktop\99aaa42af4fcc0139498243c59aa6f40.jpg'),72,y,936,620.45);y+=655
text('本次分享人 · 王皓泽',72,y,35,blue);y+=65
y=para('乐为联合创始人、瑞沃酒庄酿酒师\n与葡萄酒讲师常微一同分享风土、酿造与酒标背后的故事。',72,y,size=33,line=62,color=gray)+70
checkpoints['wines']=y
y=section('03 / WINE LIST','酒款介绍',y)
text('6款葡萄酒 · 桃红、干红与干白的风味探索',72,y,32,gray);y+=90
card_positions=[]
for i,(name,en,file,tag,body) in enumerate(wines+rice):
    if i==len(wines):
        checkpoints['rice']=y
        y+=65;y=section('CRAFT RICE WINE','特色精酿米酒',y)
        text('换一种酿造，遇见另一种果香。',72,y,32,gray);y+=90
    card_positions.append(y)
    top=y; x=350
    text(en,x,y,25,gray);y+=58
    brand='酝染酿造' if i>=len(wines) else ('乐为 Nomadic' if i==5 else ('乐为' if i==4 else '乐为 Gallery'))
    text(brand,x,y,29,gray);y+=53
    y=para(name,x,y,w=658,size=44,line=65,color=blue,font='serif')+17
    rect(x,y+5,3,37,'#acbdc9');text(tag,x+20,y,28,blue);y+=75
    y=para(body,x,y,w=658,size=36,line=68)+48
    end=max(y,top+725)
    # Display the source bottle photograph in a clipped viewport; do not repaint labels.
    cr=(1760,1380,560,1780) if i>=len(wines) else (1840,1250,490,1740)
    photo(file,82,top+25,215,650,cr)
    y=end;rule(y);y+=55
y+=10
checkpoints['surprise']=y
rect(72,y,936,235,'#f7f3f2');rect(72,y,4,235,blue)
text('A LITTLE SURPRISE',112,y+35,25,gray)
para('上述酒单外，还有两支神秘酒款，敬请期待！',112,y+100,w=855,size=38,line=68)
y+=320
event_start=y
y=section('04 / JOIN US','报名细节',y)
text('10月24日，周六下午，一起探索中国风土。',72,y,34,blue);y+=85
# Use the supplied original panel so the horse, typography, and right alignment remain exact.
photo('35e68c4c96d65807754ea3ea7d632867.jpg',0,y,1080,695.52,(0,1040,1000,644))
rect(772,y+9,260,53,'#ffffff')
s='分享人 Lecturer';text(s,1000-width(s,33),y+16,33,blue)
y+=716

checkpoints['notice']=y
y+=40
text('温馨提示',72,y,48,'#000000','serif');y+=85
y=para('座位有限，本活动仅限报名人员参加，报名确认以支付成功为准。报名者付款后，因报名者自身原因不能参加本次活动，费用不退，参加资格可以自行转让。',72,y,size=36,line=68)+65
checkpoints['sponsor']=y
text('特别鸣谢',72,y,48,'#000000','serif');y+=85
y=para('感谢TusStar启迪之星对本活动的场地赞助',72,y,size=37,line=68,color=ink)+35
support=Path(r'C:\Users\32697\Documents\xwechat_files\wxid_32na4151f83112_a08e\temp\RWTemp\2026-10\9e20f478899dc29eb19741386f9343c8')
photo(support/'f3e880868df9ee3be79f7b417f12be97.png',150,y,780,253);y+=310
y=para('启迪孵化器源于1999年成立的清华创业园，是清华大学科技园的企业服务平台，是启迪控股下属的专业孵化器公司。2002年，启迪孵化器被认定为首批国家级孵化器，成功探索“孵化＋投资”的发展模式和专业孵化器的发展方向，并在多年的探索与实践中不断完善其发展内涵。',72,y,size=34,line=65)+35
y=para('启迪之星在集群式创新理论的指导下已经构建了孵化基地200＋个，覆盖90＋个城市，其中海外15个城市，孵化载体面积超过90万平方米的创新孵化网络，累计获得国家级资质认定的基地62家，其中国家级孵化器18家、国家级众创空间等资质27项。通过启迪之星众创空间及孵化器等平台培育2万余家创业企业，其中365家企业获评“专精特新”企业。',72,y,size=34,line=65)+60
checkpoints['responsible']=y
photo(support/'ed1338c9b818dd42581aaa5fe1e641c6.jpg',72,y,936,566);y+=605
y=para('理性饮酒，适度享乐。酗酒可能影响健康及人际关系。',72,y,size=34,line=65,color=ink)+15
y+=75
rect(510,y,60,2,'#000000');y+=38
for s in ['从一杯酒出发，','认识一片土地，听见一个故事。']:
    text(s,(1080-width(s,43,'serif'))/2,y,43,'#000000','serif');y+=80
y+=20;s='清华葡萄酒协会 × 乐为酒庄';text(s,(1080-width(s,26))/2,y,26,gray);y+=90
head=f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{y}" viewBox="0 0 1080 {y}"><rect width="1080" height="{y}" fill="white"/>'
(root/'approved.svg').write_text(head+''.join(parts)+'</svg>',encoding='utf-8')
editable=list(parts)
for start,end,markup in reversed(editable_text): editable[start:end]=[markup]
(root/'draft-v2.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>乐为品鉴活动 · 网页修改稿</title><style>body{margin:0;background:#eeeae8}svg{display:block;margin:auto;max-width:100%;height:auto}text{cursor:text;user-select:text}</style>'+head+''.join(editable)+'</svg></html>',encoding='utf-8')
(root/'layout-v2.json').write_text(json.dumps({'height':y,'cards':card_positions,'event':event_start,**checkpoints}))
print(y,card_positions)
