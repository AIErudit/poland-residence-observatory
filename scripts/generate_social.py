"""Render share-card PNGs with Pillow. Does not use remote images or fonts."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets'

def font(size,serif=False):
    candidates=([Path('C:/Windows/Fonts/georgia.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')] if serif else [Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')])
    for p in candidates:
        if p.exists(): return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)

def lines(draw,text,f,maxwidth):
    result=[];line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if draw.textlength(candidate,font=f)>maxwidth and line:
            result.append(line);line=word
        else:line=candidate
    if line:result.append(line)
    return result

def card(name,value,context,caveat):
    image=Image.new('RGB',(1200,630),'#f5f4ee');d=ImageDraw.Draw(image)
    d.rectangle((0,0,18,630),fill='#0c6556')
    d.text((65,45),'RESIDENCE OBSERVATORY  /  POLSKA',font=font(22),fill='#182d31')
    d.line((65,98,1135,98),fill='#182d31',width=2)
    d.text((60,122),value,font=font(104,True),fill='#0c6556')
    y=265
    for line in lines(d,context,font(29),1040):
        d.text((65,y),line,font=font(29),fill='#182d31');y+=41
    y=max(y+23,405)
    for line in lines(d,caveat,font(21),1040)[:4]:
        d.text((65,y),line,font=font(21),fill='#5d6b69');y+=29
    d.line((65,564,1135,564),fill='#d6dcd3',width=1)
    d.text((65,583),'Dane · definicja · źródło     |     aierudit.github.io/poland-residence-observatory',font=font(18),fill='#5d6b69')
    image.save(OUT/name,optimize=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    card('social.png','Pobyt w liczbach.','16 województw. Czasy postępowań, sprawy w toku i statystyki sądów.','Źródła urzędowe i jawne ograniczenia. Niezależne opracowanie danych. Wersja: 20.10.2026.')
    for c in json.loads((ROOT/'site/claims.json').read_text(encoding='utf-8')):
        card(f'fact-{c["id"]}.png',c['preview_value'],c['preview_context'],c['caveat_pl'])
    print('Rendered 5 social preview cards (1200 × 630).')

if __name__=='__main__':main()
