#pragma once
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#ifdef __clang__
#pragma STDC FP_CONTRACT OFF
#endif

// Float32-Zwilling: empfinden.py. Kein GPIO, kein Heap, portabler Stand ohne Padding.
struct Empfinden {
    static const unsigned standBytes = 60;
    static const uint32_t magie = 0x31464d45;
    static float anteilM() { return 1.0f - static_cast<float>(0.9988454217380301); }
    static float anteilL() { return 1.0f - static_cast<float>(0.9998074776513175); }  // 1 h, v2
    static float anteilW() { return 1.0f - static_cast<float>(0.9999919774953673); }  // Maßband woanders, 1 Tag
    static float anteilG() { return 1.0f - static_cast<float>(0.9998074776513175); }
    void starte() { *this = Empfinden(); aktiv_ = true; }
    void beende() { aktiv_ = false; text[0] = 0; }
    bool aktiv() const { return aktiv_; }
    void neustart() { boot = 0; g = w = 0; }
    const char *zeile() const { return text; }
    int gerade() const { return g; }
    int woanders() const { return w; }
    bool anlauf() const { return n <= 1800 || boot == 0; }  // v2: kein stummer Wiederanlauf
    static int stufe(float d, float mass, int vor = 0) {
        const float a = fabsf(d);
        float grenze = 2.0f * mass;
        int s = 0, richtung = d < 0 ? -1 : 1;
        while (s < 30 && a >= grenze) { ++s; grenze *= 2.0f; }
        if (!s && vor * richtung > 0 && a >= 1.5f * mass) s = 1;
        return richtung * s;
    }
    static uint32_t plus(uint32_t x) { return x < 16777215 ? x + 1 : x; }
    static void lerne(float d, float mass, float alpha, float boden, uint32_t &zahl, float &q) {
        if (fabsf(d) >= 4.0f * mass) return;
        zahl = plus(zahl);
        q += alpha * (d * d - q);
        if (q < boden) q = boden;
    }
    void takt(uint32_t t, bool gueltig, int32_t temp, bool hatFehler, float mittel) {
        text[0] = 0;
        if (!aktiv_) return;
        gueltig = gueltig && temp >= -1000 && temp <= 2000 && (!hatFehler || isfinite(mittel));
        if (gueltig) {
            const float x = static_cast<float>(temp) / 10.0f;
            n = plus(n); boot = plus(boot);
            if (!init) { M = L = x; init = true; }
            M += anteilM() * (x - M);
            L += anteilL() * (x - L);
        }
        const float mg = sqrtf(qg), mw = sqrtf(qw), d = M - L;
        g = gueltig && !anlauf() && hatFehler ? stufe(mittel, mg, g) : 0;
        w = gueltig && !anlauf() ? stufe(d, mw, w) : 0;
        if (gueltig && boot > 600) {
            if (hatFehler) lerne(mittel, mg, anteilG(), .04f, ng, qg);
            lerne(d, mw, anteilW(), .25f, nw, qw);
        }
        snprintf(text, sizeof(text), "EMPFINDEN,%lu,%d,%d,%d,%d,%ld,%ld,%ld,%ld",
                 static_cast<unsigned long>(t), g, w, anlauf() ? 1 : 0, gueltig ? 1 : 0,
                 milli(mg), milli(mw), milli(M), milli(L));
    }
    static long milli(float x) { return lround(static_cast<double>(x) * 1000.0); }
    static uint32_t summe(const uint8_t *p, unsigned size) {
        uint32_t s = 0; while (size--) s = 31u * s + *p++; return s;
    }
    static void put(uint8_t *p, uint32_t x) { for (unsigned i = 0; i < 4; ++i) p[i] = x >> (8*i); }
    static uint32_t get(const uint8_t *p) {
        uint32_t x = 0; for (unsigned i = 0; i < 4; ++i) x |= uint32_t(p[i]) << (8*i); return x;
    }
    void exportiere(uint8_t *p) const {
        const uint32_t u[] = {magie, 1, n, ng, nw, boot, init ? 1u : 0u, aktiv_ ? 1u : 0u,
                               static_cast<uint32_t>(g), static_cast<uint32_t>(w)};
        for (unsigned i = 0; i < 10; ++i) put(p + 4*i, u[i]);
        const float f[] = {M, L, qg, qw};
        for (unsigned i = 0; i < 4; ++i) { uint32_t bits; memcpy(&bits, &f[i], 4); put(p+40+4*i, bits); }
        put(p+56, summe(p, 56));
    }
    bool importiere(const uint8_t *p, unsigned size = standBytes) {
        if (size != standBytes || get(p) != magie || get(p+4) != 1 || get(p+56) != summe(p,56)) return false;
        Empfinden neu;
        neu.n=get(p+8); neu.ng=get(p+12); neu.nw=get(p+16); neu.boot=get(p+20);
        if (neu.n>16777215 || neu.ng>16777215 || neu.nw>16777215 || neu.boot>neu.n || get(p+24)>1 || get(p+28)>1) return false;
        neu.init=get(p+24); neu.aktiv_=get(p+28);
        neu.g=static_cast<int32_t>(get(p+32)); neu.w=static_cast<int32_t>(get(p+36));
        if (neu.g < -30 || neu.g>30 || neu.w < -30 || neu.w>30) return false;
        float *f[] = {&neu.M, &neu.L, &neu.qg, &neu.qw};
        for (unsigned i=0;i<4;++i) { uint32_t bits=get(p+40+4*i); memcpy(f[i], &bits,4); if (!isfinite(*f[i])) return false; }
        if (neu.M < -100 || neu.M>200 || neu.L < -100 || neu.L>200 || neu.qg<.04f || neu.qw<.25f || neu.qg>1e8f || neu.qw>1e8f) return false;
        *this=neu; return true;
    }
private:
    uint32_t n=0, ng=0, nw=0, boot=0;
    bool init=false, aktiv_=false;
    int g=0,w=0;
    float M=0,L=0,qg=.04f,qw=.25f;
    char text[128]={};
};
