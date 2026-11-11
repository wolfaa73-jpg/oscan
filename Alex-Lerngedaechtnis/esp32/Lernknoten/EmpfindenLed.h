#pragma once
#include <stdint.h>

// Reine Zuordnung, keine Uhr und kein GPIO. Phase aus dem Körpertakt, vier Sekunden.
// Die langsame Schicht erhält jeden vierten Takt einen eigenen gedämpften Farbimpuls.
namespace EmpfindenLed {
struct Farbe { uint8_t r, g, b; };
struct Muster { Farbe gerade, woanders; bool langsam; };
inline unsigned betrag(int x) { return static_cast<unsigned>(x < 0 ? -int64_t(x) : x); }
inline Farbe richtung(int wort, unsigned hell) {
    return wort < 0 ? Farbe{0, static_cast<uint8_t>(hell / 4), static_cast<uint8_t>(hell)}
                   : Farbe{static_cast<uint8_t>(hell), static_cast<uint8_t>(hell / 4), 0};
}
inline Muster muster(int gerade, int woanders, bool anlauf, bool voll) {
    if (voll) return {{4,0,4}, {4,0,4}, false};
    if (anlauf) return {{2,2,2}, {2,2,2}, false};
    const unsigned stufe = betrag(gerade), ort = betrag(woanders);
    const unsigned hell[] = {2,3,4,6,8,12,16};
    const Farbe a = gerade ? richtung(gerade, hell[stufe > 6 ? 6 : stufe]) : Farbe{0,2,0};
    const Farbe b = woanders ? richtung(woanders, ort >= 4 ? 4 : ort+1) : a;
    return {a,b,woanders != 0};
}
inline Farbe bild(const Muster &m, uint32_t takt) {
    return m.langsam && takt % 4 == 3 ? m.woanders : m.gerade;
}
}
