import base64, json, re
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from make_draft import wines,rice,src,root

fonts={k:TTFont(p,fontNumber=0) for k,p in [('sans',r'C:\Windows\Fonts\msyh.ttc'),('serif',r'C:\Windows\Fonts\simsun.ttc')]}
cache={}; parts=[]; clips=0
blue='#164b70'; ink='#3e454a'; gray='#7c8992'
def glyph(ch,font):
    key=(font,ch)
    if key not in cache:
        f=fonts[font]; gn=f.getBestCmap().get(ord(ch),'.notdef'); gs=f.getGlyphSet(); pen=SVGPathPen(gs); gs[gn].draw(pen)
        cache[key]=(pen.getCommands(),gs[gn].width,f['head'].unitsPerEm)
    return cache[key]
def width(s,size,font='sans'):
    return sum(glyph(c,font)[1]/glyph(c,font)[2]*size for c in s)
def text(s,x,y,size=36,color=ink,font='sans'):
    for c in s:
        d,adv,upm=glyph(c,font); sc=size/upm
        if d: parts.append(f'<path fill="{color}" d="{d}" transform="translate({x:.2f},{y+size:.2f}) scale({sc:.6f},{-sc:.6f})"/>')
        x+=adv*sc
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
    if crop:
        cx,cy,cw,ch=crop; scale=min(w/cw,h/ch); clips+=1
        parts.append(f'<clipPath id="c{clips}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath><image href="data:image/jpeg;base64,{data}" x="{x-cx*scale}" y="{y-cy*scale}" width="{iw*scale}" height="{ih*scale}" clip-path="url(#c{clips})"/>')
    else:parts.append(f'<image href="data:image/jpeg;base64,{data}" x="{x}" y="{y}" width="{w}" height="{h}"/>')
def section(en,zh,y):
    text(en,72,y,26,gray); y+=62
    y=para(zh,72,y,size=60,line=82,color=blue,font='serif');return y+30

photo('35e68c4c96d65807754ea3ea7d632867.jpg',143,40,794,122,(180,20,680,105))
y=215
text('清华葡萄酒协会 × 乐为酒庄',72,y,32,gray);y+=85
y=para('黄河北岸\n的风土之旅',72,y,size=92,line=123,color=blue,font='serif')
rect(72,y+22,70,3,blue); y+=70
text('探索内蒙古葡萄酒的独特魅力',72,y,36,gray);y+=75
text('品鉴活动招募  /  2026.10.24',72,y,34,blue);y+=95
photo('3bda08add25ef9acbb37a3bf9631acbc.jpg',72,y,936,624);y+=645
text('乐为酒款实拍',72,y,25,gray);y+=85
y=para('提到中国葡萄酒，\n你会想到哪里？',72,y,size=44,line=76,color=blue,font='serif')+30
y=para('宁夏贺兰山、山东蓬莱，还是云南香格里拉？这一次，我们把目光投向内蒙古黄河北岸，去认识一片鲜为人知、却极具潜力的葡萄酒产区。',72,y)+40
rule(y);y+=32
for x,a,b in [(72,'1050 m','葡萄园平均海拔'),(368,'冷凉气候','大陆性气候特征'),(655,'砾质沙壤河滩土','黄河北岸的风土底色')]:
    text(a,x,y,34,blue);text(b,x,y+61,25,gray)
y+=128;rule(y);y+=50
y=para('充足的日照与鲜明的昼夜温差，让美乐、马瑟兰、西拉与赤霞珠，在这片土地上展现出不同的个性。',72,y)+30
y=para('本次清华葡萄酒协会携手乐为酒庄（Lewei），从清新细腻的桃红，到层次丰富的干红，一起探索中国本土风土的多样表达。',72,y)+65
y=section('WINE & ART','每一张酒标，都有一个故事。',y)
y=para('乐为将艺术创作与葡萄酒文化相结合。Gallery系列通过艺术家的酒标创作，讲述关于普洁、蒙古马与草原故乡的故事，让每一瓶酒都成为风土与艺术的共同表达。',72,y)+75
y=section('THE TASTING LIST','正式品鉴酒单',y)
text('5款葡萄酒 · 从桃红到干红，循香而行',72,y,32,gray);y+=90
card_positions=[]
for i,(name,en,file,tag,body) in enumerate(wines+rice):
    if i==5:
        y+=65;y=section('CRAFT RICE WINE','特色精酿米酒',y)
        text('换一种酿造，遇见另一种果香。',72,y,32,gray);y+=90
    card_positions.append(y)
    top=y; x=350
    text(en,x,y,25,gray);y+=58
    text('酝染酿造' if i>=5 else ('乐为' if i==4 else '乐为 Gallery'),x,y,29,gray);y+=53
    y=para(name,x,y,w=658,size=44,line=65,color=blue,font='serif')+17
    rect(x,y+5,3,37,'#acbdc9');text(tag,x+20,y,28,blue);y+=75
    y=para(body,x,y,w=658,size=36,line=68)+48
    end=max(y,top+725)
    # Display the source bottle photograph in a clipped viewport; do not repaint labels.
    cr=(1760,1380,560,1780) if i>=5 else (1840,1250,490,1740)
    photo(file,82,top+25,215,650,cr)
    y=end;rule(y);y+=55
y+=10
rect(72,y,936,300,'#f3f6f8');rect(72,y,4,300,blue)
text('A LITTLE SURPRISE',112,y+35,25,gray)
text('还有2款神秘彩蛋酒款',112,y+95,43,blue,'serif')
para('除了上述7款正式酒单，本次活动还将额外准备2款神秘酒款！',112,y+175,w=855,size=35,line=63)
y+=385
event_start=y; event=[]
# Background inserted before the event text after its height is known.
bg_index=len(parts)
y+=60;y=section('JOIN THE TASTING','这个周六，一起品鉴',y)
for label,value in [('时间','2026年10月24日 · 周六\n15:00—17:00'),('地点','北京市海淀区清华园\n启迪科技大厦 C座 G层'),('分享人','常微 & 王皓泽'),('活动咨询','15137069306')]:
    text(label,72,y+7,29,gray)
    y=para(value,252,y,w=756,size=38,line=68,color=blue)
    if label=='分享人': y=para('乐为葡萄酒联合创始人\n葡萄酒讲师 & 酿酒师',252,y+10,w=756,size=29,line=54,color=gray)
    y+=30;rule(y);y+=34
y+=18
parts.insert(bg_index,f'<rect x="0" y="{event_start}" width="1080" height="{y-event_start}" fill="#f4f7f9"/>')
y+=75
rect(510,y,60,2,blue);y+=38
for s in ['从一杯酒出发，','认识一片土地，听见一个故事。']:
    text(s,(1080-width(s,43,'serif'))/2,y,43,blue,'serif');y+=80
y+=20;s='清华葡萄酒协会 × 乐为酒庄';text(s,(1080-width(s,26))/2,y,26,gray);y+=90
(root/'draft.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="{y}" viewBox="0 0 1080 {y}"><rect width="1080" height="{y}" fill="white"/>'+''.join(parts)+'</svg>',encoding='utf-8')
(root/'layout.json').write_text(json.dumps({'height':y,'cards':card_positions,'event':event_start}))
print(y,card_positions)
