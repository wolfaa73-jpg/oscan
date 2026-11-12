// Host-Export derselben Zeichenbefehle, die das C3 zeichnet.
#include <cstdio>
#include "../Gemeinsam/GesichtFormen.h"
int main() {
    unsigned t,bits;int temp,g,w,fehlt;
    while(scanf("%u %d %d %d %u %d",&t,&temp,&g,&w,&bits,&fehlt)==6) {
        EmpfindenPaket::Zustand z;z.takt=t;z.temp=temp;z.gerade=g;z.woanders=w;z.bits=bits;
        if(!EmpfindenPaket::gueltig(z))return 2;
        const auto b=Gesicht::zeichne(z,fehlt);
        printf("{\"hintergrund\":%u,\"wort\":\"%s\",\"hinweis\":\"%s\",\"formen\":[",b.hintergrund,b.wort,b.hinweis);
        for(unsigned i=0;i<b.n;++i) {
            const auto &f=b.formen[i];if(i)printf(",");
            printf("[%d,%d,%d,%d,%d,%d,%d,%u]",int(f.art),f.x,f.y,f.a,f.b,f.c,f.d,f.farbe);
        }
        printf("]}\n");
    }
}
