"""Bildproben aus den echten C++-Zeichenbefehlen, kein zweiter Gesichtsalgorithmus.
Benötigt Pillow und c++. Ausgabeordner darf noch nicht existieren.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).parent


def formen(eingaben):
    with tempfile.TemporaryDirectory() as d:
        exe=Path(d,"formen")
        subprocess.run(["c++","-std=c++11","-Wall","-Wextra","-Werror",str(ROOT/"esp32/Gesicht/host.cpp"),"-o",str(exe)],check=True)
        aus=subprocess.check_output([str(exe)],input="".join(" ".join(map(str,z))+"\n" for z in eingaben),text=True)
    return [json.loads(x) for x in aus.splitlines()]


def zeichne(b):
    def rgb(x):return (x>>16&255,x>>8&255,x&255)
    im=Image.new("RGB",(240,240),rgb(b["hintergrund"]));d=ImageDraw.Draw(im)
    for art,x,y,a,bb,c,dd,f in b["formen"]:
        farbe=rgb(f)
        if art==0:d.ellipse((x-a,y-bb,x+a,y+bb),fill=farbe)
        elif art==1:d.line((x,y,a,bb),fill=farbe,width=1)
        elif art==2:d.rectangle((x,y,x+a-1,y+bb-1),fill=farbe)
        elif art==3:d.polygon(((x,y),(a,bb),(c,dd)),fill=farbe)
    font=ImageFont.load_default(size=14)
    d.text((120,43),b["wort"],font=font,anchor="mm",fill=(220,229,236))
    d.text((120,219),b["hinweis"],font=font,anchor="mm",fill=(255,166,122))
    # Runde sichtbare Fläche des Boards. Der reale Treiber zeichnet direkt, ohne Bildpuffer.
    maske=Image.new("L",(240,240),0);ImageDraw.Draw(maske).ellipse((0,0,239,239),fill=255)
    out=Image.new("RGB",im.size,(0,0,0));out.paste(im,mask=maske);return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("ziel",type=Path);a=p.parse_args()
    a.ziel.mkdir(parents=True,exist_ok=False)
    eingaben=[];namen=[]
    for name,flag in (("ruhig",0),("ueberrascht",2),("suchen-vorschau",32),("erklaert-vorschau",64)):
        for richtung,sign in (("kaelter",-1),("waermer",1)):
            for stufe in range(7):
                namen.append(f"{name}-{richtung}-{stufe}.png");eingaben.append((123,370,sign*stufe,0,flag,0))
    for name,z in (("kein-signal",(0,-32768,0,0,0,1)),("anlauf",(1,370,0,0,1,0)),
                   ("woanders-kaelter",(123,370,0,-3,0,0)),("woanders-waermer",(123,370,0,3,0,0)),
                   ("messung-fehlt",(123,-32768,0,0,0,0)),("ausfall",(123,780,5,-2,10,0))):
        namen.append(name+".png");eingaben.append(z)
    bilder=formen(eingaben);manifest=[]
    kontakt=Image.new("RGB",(7*240,9*264),(22,27,33));kd=ImageDraw.Draw(kontakt)
    for i,(name,z,b) in enumerate(zip(namen,eingaben,bilder)):
        im=zeichne(b);pfad=a.ziel/name;im.save(pfad)
        manifest.append(dict(datei=name,eingang=list(z),formen=b,sha256=hashlib.sha256(pfad.read_bytes()).hexdigest()))
        x,y=(i%7)*240,(i//7)*264;kontakt.paste(im,(x,y));kd.text((x+8,y+243),name,fill="white")
    kontakt.save(a.ziel/"uebersicht.png")
    (a.ziel/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(f"{len(bilder)} Bildproben erzeugt")

if __name__=="__main__":main()
