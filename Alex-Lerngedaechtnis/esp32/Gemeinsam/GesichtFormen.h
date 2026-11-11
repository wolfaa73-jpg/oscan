#pragma once
#include "EmpfindenPaket.h"
#include <initializer_list>
namespace Gesicht {
// Kleine feste Liste von Zeichenbefehlen, kein Bildpuffer. C3 und Host benutzen dieselbe Funktion.
enum Art { ELLIPSE, LINIE, RECHTECK, DREIECK };
struct Form {Art art; int16_t x,y,a,b,c,d; uint32_t farbe;};
struct Bild { Form formen[20]; unsigned n=0; uint32_t hintergrund=0x111921;
    const char *wort="ruhig"; const char *hinweis="";
    void add(Art art,int x,int y,int a,int b,int c,int d,uint32_t f) {
        if(n<20) formen[n++]={art,int16_t(x),int16_t(y),int16_t(a),int16_t(b),int16_t(c),int16_t(d),f};
    }
};
inline Bild zeichne(const EmpfindenPaket::Zustand &z,bool fehlt=false) {
    using namespace EmpfindenPaket;
    Bild b;
    if(fehlt) { b.wort="KEIN SIGNAL"; b.hinweis="warte auf Knoten";
        b.add(LINIE,90,90,150,150,0,0,0x89949c);b.add(LINIE,150,90,90,150,0,0,0x89949c);return b; }
    b.hintergrund=z.woanders<0?0x101e32:z.woanders>0?0x2c1d13:0x111921;
    b.hinweis=z.bits&AUSFALL?"AUSFALL":z.bits&SCHWACH?"SCHWACH":z.bits&VOLL?"PROTOKOLL VOLL":"";
    if(z.bits&ANLAUF || z.temp==-32768) {b.wort=z.temp==-32768?"MESSUNG FEHLT":"ANLAUF";
        b.add(LINIE,65,110,95,110,0,0,0xb7c0c6);b.add(LINIE,145,110,175,110,0,0,0xb7c0c6);return b;}
    const unsigned a=z.gerade<0?-z.gerade:z.gerade, stufe=a>6?6:a;
    const int rx=10+int(stufe)*2, ry=7+int(stufe)*3;
    const uint32_t farbe=z.gerade<0?0x83cfff:z.gerade>0?0xffc17a:0xdce5ec;
    b.wort=z.bits&SUCHT?"am Suchen":z.bits&ERKLAERT?"erklaert":z.bits&UEBERRASCHT?"ueberrascht":"ruhig";
    for(int x:{78,162}) {
        b.add(ELLIPSE,x,105,rx,ry+(z.bits&UEBERRASCHT?4:0),0,0,farbe);
        b.add(ELLIPSE,x+(z.bits&SUCHT?4:0),105,3,5,0,0,0x111921);
    }
    if(z.gerade) { // Richtungsdreieck bleibt auch in Graustufen lesbar.
        const int spitze=z.gerade>0?157:179, basis=z.gerade>0?179:157;
        b.add(DREIECK,120,spitze,110,basis,130,basis,farbe);
    } else b.add(LINIE,108,167,132,167,0,0,farbe);
    if(z.bits&ERKLAERT) {b.add(LINIE,109,140,118,148,0,0,farbe);b.add(LINIE,118,148,133,132,0,0,farbe);}
    if(z.bits&SUCHT) for(int x:{110,120,130})b.add(ELLIPSE,x,143,2,2,0,0,farbe);
    b.hinweis=z.bits&AUSFALL?"AUSFALL":z.bits&SCHWACH?"SCHWACH":z.bits&VOLL?"PROTOKOLL VOLL":"";
    return b;
}
}
