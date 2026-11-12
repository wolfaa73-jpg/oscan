#pragma once
#include <stdint.h>
#include <stddef.h>

namespace EmpfindenPaket {
constexpr unsigned bytes=12, kanal=6;
constexpr uint8_t ANLAUF=1, UEBERRASCHT=2, SCHWACH=4, AUSFALL=8, VOLL=16, SUCHT=32, ERKLAERT=64;
struct Zustand { uint32_t takt=0; int16_t temp=-32768; int8_t gerade=0, woanders=0; uint8_t bits=0; };
inline uint8_t crc(const uint8_t *p, unsigned n) {
    uint8_t c=0;
    while(n--) { c ^= *p++; for(unsigned i=0;i<8;++i) c=static_cast<uint8_t>((c<<1)^((c&128)?7:0)); }
    return c;
}
inline bool gueltig(const Zustand &z) {
    return (z.temp==-32768 || (z.temp>=-1000 && z.temp<=2000)) && z.gerade>=-30 && z.gerade<=30
        && z.woanders>=-30 && z.woanders<=30 && !(z.bits&128)
        && !((z.bits&SCHWACH)&&(z.bits&AUSFALL))
        && !((z.bits&SUCHT)&&(z.bits&ERKLAERT))
        && !((z.bits&(SUCHT|ERKLAERT))&&(z.bits&UEBERRASCHT));
}
inline bool packe(const Zustand &z,uint8_t *p) {
    if (!gueltig(z)) return false;
    p[0]=0x4f;p[1]=1;
    for(unsigned i=0;i<4;++i)p[2+i]=z.takt>>(8*i);
    const uint16_t t=static_cast<uint16_t>(z.temp);p[6]=t;p[7]=t>>8;
    p[8]=static_cast<uint8_t>(z.gerade);p[9]=static_cast<uint8_t>(z.woanders);p[10]=z.bits;p[11]=crc(p,11);
    return true;
}
inline int16_t signed16(unsigned x) { return static_cast<int16_t>(x<32768?int(x):int(x)-65536); }
inline int8_t signed8(unsigned x) { return static_cast<int8_t>(x<128?int(x):int(x)-256); }
inline bool entpacke(const uint8_t *p,size_t n,Zustand &z) {
    if (n!=bytes || p[0]!=0x4f || p[1]!=1 || p[11]!=crc(p,11)) return false;
    Zustand neu;
    for(unsigned i=0;i<4;++i)neu.takt|=uint32_t(p[2+i])<<(8*i);
    neu.temp=signed16(unsigned(p[6])|(unsigned(p[7])<<8));neu.gerade=signed8(p[8]);neu.woanders=signed8(p[9]);neu.bits=p[10];
    if (!gueltig(neu))return false;
    z=neu;return true;
}
// Derselbe Zeitpunkt wird durch Duplikate nicht frisch. Neustarts nach Empfangspause sind erlaubt.
struct Empfang {
    static constexpr uint32_t frist=5000;
    Zustand zustand;
    uint32_t zeit=0; bool hat=false;
    bool alt(uint32_t jetzt) const {return !hat || uint32_t(jetzt-zeit)>=frist;}
    bool uebernehme(const Zustand &z,uint32_t jetzt) {
        if (!gueltig(z))return false;
        const uint32_t delta=z.takt-zustand.takt;
        if (hat && (!delta || (!alt(jetzt) && delta>=0x80000000u)))return false;
        zustand=z;zeit=jetzt;hat=true;return true;
    }
};
}
