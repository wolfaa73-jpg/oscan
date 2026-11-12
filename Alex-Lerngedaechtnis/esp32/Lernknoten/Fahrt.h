#pragma once
#include <math.h>
#include <stdint.h>

// Fahrtenschreiber: Ein Satz je Körpertakt, 16 Byte, niederwertiges Byte zuerst. So schreibt ihn der
// Knoten unterwegs in seinen Flash, fahrt.py liest ihn wieder. Temperaturen in Zehntelgrad (Messwert) und
// Hundertstelgrad (Vorhersagen, Mittel des Fehlers, Grenze).
//   0  uint32  Takt der Fahrt, zählt über Neustarts weiter
//   4  int16   Temperatur in Zehntelgrad, -32768 = nicht lesbar
//   6  uint8   Bits: 1 Last, 2 überrascht, 4 Vorwarnung, 8 sofort, 16+32 Zustand, 64 erster Takt nach
//              einem Neustart, 128 noch kein Fehlerwert (Mittel und Grenze sind dann 0)
//   7  uint8   beim ersten Takt nach einem Neustart dessen Grund (esp_reset_reason), dazu 128, wenn das
//              Gedächtnis der Vorhersage dabei bei null begann; sonst 0
//   8  int16   Vorhersage für in 10 Takten
//  10  int16   Vorhersage für in 60 Takten
//  12  int16   Mittel des Fehlers
//  14  int16   Grenze
struct Fahrtsatz {
    static const unsigned bytes = 16;
    // Nach so vielen Takten schreibt der Knoten Sätze und Stand in den Flash. Was danach bis zu einem
    // Stromausfall kam, ist verloren, für das Protokoll und für sein Gedächtnis gleichermaßen.
    static const unsigned block = 30;

    // Zwei signed Stufen in Byte 7, nur außerhalb Neustarts. 7 bedeutet mindestens 7.
    static unsigned nibble(int s) { return static_cast<unsigned>((s < -7 ? -7 : s > 7 ? 7 : s) + 8); }
    static void empfinden(uint8_t *p, int gerade, int woanders) {
        if (!(p[6] & 64)) p[7] = static_cast<uint8_t>(nibble(gerade) | (nibble(woanders) << 4));
    }

    static int16_t hundertstel(float grad) {
        const long wert = lround(static_cast<double>(grad) * 100.0);
        return static_cast<int16_t>(wert > 32767 ? 32767 : wert < -32767 ? -32767 : wert);
    }

    static void packe(uint8_t *ziel, uint32_t takt, bool gueltig, int32_t tempDc, bool last, bool ueberrascht,
                      bool warnung, bool sofort, unsigned zustand, bool neustart, unsigned grund, bool beiNull, float vKurz,
                      float vLang, bool hatFehler, float mittel, float grenze) {
        const int32_t temp = !gueltig ? -32768 : tempDc > 32767 ? 32767 : tempDc < -32767 ? -32767 : tempDc;
        const uint8_t bits = static_cast<uint8_t>((last ? 1 : 0) | (ueberrascht ? 2 : 0) | (warnung ? 4 : 0)
                                                  | (sofort ? 8 : 0) | ((zustand & 3u) << 4) | (neustart ? 64 : 0)
                                                  | (hatFehler ? 0 : 128));
        const int16_t werte[4] = {hundertstel(vKurz + 37.0f), hundertstel(vLang + 37.0f),
                                  static_cast<int16_t>(hatFehler ? hundertstel(mittel) : 0),
                                  static_cast<int16_t>(hatFehler ? hundertstel(grenze) : 0)};
        for (unsigned i = 0; i < 4; ++i) ziel[i] = static_cast<uint8_t>(takt >> (8 * i));
        ziel[4] = static_cast<uint8_t>(temp & 0xFF);
        ziel[5] = static_cast<uint8_t>((temp >> 8) & 0xFF);
        ziel[6] = bits;
        ziel[7] = static_cast<uint8_t>(neustart ? (grund & 127u) | (beiNull ? 128u : 0u) : 0u);
        for (unsigned i = 0; i < 4; ++i) {
            ziel[8 + 2 * i] = static_cast<uint8_t>(werte[i] & 0xFF);
            ziel[9 + 2 * i] = static_cast<uint8_t>((werte[i] >> 8) & 0xFF);
        }
    }
};

// V2 erweitert den unveränderten 16-Byte-Satz um ein eigenes Reizfeld.
// Exportkopf: OSCFAHRT, uint32 Version 2, uint32 Satzgröße 20 (little endian).
// Byte 16: Reizbits inkl. 32 = Sende-API-Fehler; 17/18 reserviert 0;
// Byte 19: 1 = Reizfeld vorhanden, 0 = unbekannt (konvertierter Altsatz).
struct FahrtV2 {
    static const unsigned bytes = 20, kopfBytes = 16;
    static void kopf(uint8_t *p) {
        const uint8_t k[kopfBytes] = {'O','S','C','F','A','H','R','T',2,0,0,0,20,0,0,0};
        for(unsigned i=0;i<kopfBytes;++i)p[i]=k[i];
    }
    static void reize(uint8_t *p, unsigned reiz, bool bekannt=true) {
        p[16]=bekannt ? static_cast<uint8_t>(reiz) : 0;
        p[17]=p[18]=0;p[19]=bekannt ? 1 : 0;
    }
};
