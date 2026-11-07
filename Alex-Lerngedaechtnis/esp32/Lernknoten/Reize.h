#pragma once
#include <stdint.h>

// Reize im Takt des Körpers, hier nur ihr Ablauf. Was sie bewirken, Speicher belegen oder
// die Hauptschleife anhalten, steht im Sketch. So lässt sich der Ablauf am Rechner prüfen.
// Halten und Pause zählen Takte, mindestens einen und höchstens 3600.
inline bool reizTakte(uint32_t n) { return n >= 1 && n <= 3600; }

// Leck: belegt je Takt einen Block, bis der Sketch meldet, dass kein Block mehr über den
// Boden passt. Dieser Takt ist der erste von halten Takten am Boden. Im Takt danach gibt
// es alles frei, das ist der erste von pause Takten ohne Leck. Dann wächst es wieder.
//
// Der freie Speicher liegt in mehreren Stücken. Am Boden bleibt in jedem ein Rest, der für
// einen ganzen Block zu klein ist. Ist über dem Boden noch genug frei, aber kein Stück groß
// genug, nimmt der Sketch kleinere Blöcke, siehe kleiner(). Sonst hinge der Boden davon ab,
// wie der Speicher gerade zerstückelt ist: Am 6. November liefen so 81 von 209 tiefen
// Durchgängen nicht bis unter die Ausfallgrenze, in stundenlangen Blöcken.
//
// Mit flach und muster hat nicht jeder Durchgang denselben Boden. Bit n des Musters gilt für
// Durchgang n, nach 32 Durchgängen von vorn. Ein gesetztes Bit hält schon am flachen Boden an.
// So ändert ein Vorzeichen seine Bedeutung: Mal folgt auf knappen Speicher voller, mal nicht.
struct Leck {
    enum Aktion : uint8_t { NICHTS, BELEGEN, FREIGEBEN };
    // Blöcke ab 1 KiB, damit 512 Blöcke für jeden Speicher reichen. Mindestens 8 KiB bleiben
    // frei für Ausgabe, LED und Lastaufgabe. Das ist eine gewählte Reserve, keine gemessene.
    static constexpr uint32_t minBlock = 1024, maxBlock = 65536, minBoden = 8192;
    uint32_t block = 0, boden = 0;  // Byte je Block, Byte, die in diesem Durchgang frei bleiben

    // flach 0 heißt: jeder Durchgang geht bis untergrenze.
    bool starte(uint32_t b, uint32_t untergrenze, uint32_t h, uint32_t p, uint32_t f = 0, uint32_t m = 0) {
        if (!f) f = untergrenze;
        if (b < minBlock || b > maxBlock || untergrenze < minBoden || f < untergrenze
            || !reizTakte(h) || !reizTakte(p)) return false;
        block = b;
        tief = untergrenze;
        flach = f;
        muster = m;
        durchgang = 0;
        boden = waehle();
        halten = h;
        pause = p;
        rest = 0;
        phase = WAECHST;
        return true;
    }

    Aktion takt() {
        if (phase == RUHT && !rest) {
            phase = WAECHST;
            durchgang = (durchgang + 1) % 32;
            boden = waehle();
        }
        switch (phase) {
        case WAECHST:
            return BELEGEN;
        case HAELT:
            if (rest) {
                --rest;
                return NICHTS;
            }
            phase = RUHT;
            rest = pause - 1;
            return FREIGEBEN;
        case RUHT:
            --rest;
            return NICHTS;
        default:
            return NICHTS;
        }
    }

    // Nächstkleinerer Versuch, wenn ein Block dieser Größe in kein freies Stück passt: die Hälfte,
    // bis minBlock. 0 heißt, es gibt keinen kleineren mehr.
    static uint32_t kleiner(uint32_t groesse) { return groesse / 2 >= minBlock ? groesse / 2 : 0; }

    // Der Sketch konnte nicht belegen: Boden erreicht.
    void voll() {
        if (phase != WAECHST) return;
        phase = HAELT;
        rest = halten - 1;
    }

private:
    enum Phase : uint8_t { AUS, WAECHST, HAELT, RUHT };
    uint32_t waehle() const { return (muster >> durchgang) & 1u ? flach : tief; }
    Phase phase = AUS;
    uint32_t halten = 0, pause = 0, rest = 0, tief = 0, flach = 0, muster = 0, durchgang = 0;
};

// Bremse: Die Hauptschleife steht je Takt einmal still, start, start + schritt, ... ms.
// Sobald bis erreicht ist, halten Takte lang bis, dann pause Takte gar nicht, dann von vorn.
// Unter einer Sekunde, damit beim üblichen Takt von 1 s kein Takt ausfällt.
struct Bremse {
    static constexpr uint32_t maxMs = 900;

    bool starte(uint32_t s, uint32_t d, uint32_t b, uint32_t h, uint32_t p) {
        if (!d || !b || b > maxMs || s > b || !reizTakte(h) || !reizTakte(p)) return false;
        start = s;
        schritt = d;
        bis = b;
        halten = h;
        pause = p;
        ms = s;
        rest = 0;
        phase = STEIGT;
        return true;
    }

    // Wie lange die Schleife bis zum nächsten Takt einmal stillsteht, 0 heißt gar nicht.
    uint32_t takt() {
        if (phase == RUHT && !rest) {
            phase = STEIGT;
            ms = start;
        }
        switch (phase) {
        case STEIGT: {
            const uint32_t jetzt = ms;
            if (jetzt >= bis) {
                phase = HAELT;
                rest = halten - 1;
                return bis;
            }
            ms = bis - jetzt > schritt ? jetzt + schritt : bis;
            return jetzt;
        }
        case HAELT:
            if (rest) {
                --rest;
                return bis;
            }
            phase = RUHT;
            rest = pause - 1;
            return 0;
        case RUHT:
            --rest;
            return 0;
        default:
            return 0;
        }
    }

private:
    enum Phase : uint8_t { AUS, STEIGT, HAELT, RUHT };
    Phase phase = AUS;
    uint32_t start = 0, schritt = 0, bis = 0, halten = 0, pause = 0, ms = 0, rest = 0;
};
