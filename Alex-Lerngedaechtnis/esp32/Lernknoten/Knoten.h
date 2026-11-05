#pragma once
#include <math.h>
#include <stdint.h>
#include <string.h>
#include <float.h>

enum Zustand : uint8_t { OKAY, SCHWACH, AUSFALL, UNBEKANNT };

struct Entscheidung {
    bool sofort;
    bool warnung;
};

// Werte entsprechen dem Regelbyte im Format AG01 und REGELN in kern.py.
enum class Regel : uint8_t { ZEIT = 1, KONTEXT = 2, ERBE = 3 };

class Knoten {
public:
    explicit Knoten(Regel r = Regel::ZEIT) : regel(r),
        faktor(pow(0.5, r == Regel::ZEIT ? 1.0 / 24.0 : 1.0 / 6.0)) {
        // Wie ERBE in kern.py: drei feste Beobachtungen SCHWACH -> AUSFALL.
        if (r == Regel::ERBE) erbe[SCHWACH][AUSFALL] = 3.0;
    }

    // Portables Format AG01. Die Zahlen werden einzeln in Little Endian kodiert.
    static constexpr unsigned standBytes = 86;
    bool exportiere(uint8_t *p) const {
        static_assert(sizeof(double) == 8 && DBL_MANT_DIG == 53, "binary64 erforderlich");
        if (!letzterTakt) return false;
        memcpy(p, "AG01", 4);
        p[4] = static_cast<uint8_t>(regel);
        p[5] = static_cast<uint8_t>(letzterZustand) + 1;
        schreibe(p + 6, letzterTakt, 4);
        for (unsigned i = 0; i < 9; ++i) {
            uint64_t bits = 0;
            memcpy(&bits, &gewichte[i / 3][i % 3], 8);
            schreibe(p + 10 + i * 8, bits, 8);
        }
        schreibe(p + 82, crc32(p, 82), 4);
        return true;
    }

    bool importiere(const uint8_t *p) {
        if (letzterTakt || memcmp(p, "AG01", 4) || p[4] != static_cast<uint8_t>(regel)
            || p[5] < 1 || p[5] > 3 || lese(p + 82, 4) != crc32(p, 82)) return false;
        const uint32_t takt = static_cast<uint32_t>(lese(p + 6, 4));
        if (!takt) return false;
        double matrix[3][3];
        double summe = 0;
        for (unsigned i = 0; i < 9; ++i) {
            uint64_t bits = lese(p + 10 + i * 8, 8);
            double wert;
            memcpy(&wert, &bits, 8);
            if (!isfinite(wert) || wert < 0 || wert > takt) return false;
            summe += wert;
            matrix[i / 3][i % 3] = wert;
        }
        if (summe > takt) return false;
        memcpy(gewichte, matrix, sizeof(matrix));
        letzterTakt = takt;
        letzterZustand = static_cast<Zustand>(p[5] - 1);
        return true;
    }

    uint32_t takt() const { return letzterTakt; }

    void neuerLauf() {
        for (auto &zeile : gewichte) {
            for (double &wert : zeile) wert = 0.0;
        }
        letzterTakt = 0;
        letzterZustand = UNBEKANNT;
    }

    bool schritt(uint32_t takt, Zustand jetzt, Entscheidung &ausgabe) {
        if (takt <= letzterTakt || jetzt >= UNBEKANNT) return false;
        const uint32_t abstand = takt - letzterTakt;
        const Zustand vorher = abstand == 1 ? letzterZustand : UNBEKANNT;
        if (regel != Regel::ZEIT) {
            if (vorher != UNBEKANNT) {
                for (double &wert : gewichte[vorher]) wert *= faktor;
            }
        } else {
            const double zerfall = abstand == 1 ? faktor : pow(faktor, abstand);
            for (auto &zeile : gewichte) {
                for (double &wert : zeile) wert *= zerfall;
            }
        }
        if (vorher != UNBEKANNT) gewichte[vorher][jetzt] += 1.0;
        // Summenfolge wie in Gedaechtnis.schaetze, damit beide Seiten bitgleich rechnen.
        const double *zeile = gewichte[jetzt];
        const double *geerbt = erbe[jetzt];
        const double beleg = (zeile[OKAY] + geerbt[OKAY]) + (zeile[SCHWACH] + geerbt[SCHWACH])
                           + (zeile[AUSFALL] + geerbt[AUSFALL]);
        ausgabe.sofort = jetzt == AUSFALL && vorher != AUSFALL;
        ausgabe.warnung = jetzt != AUSFALL && beleg >= 3.0
                       && (zeile[AUSFALL] + geerbt[AUSFALL]) / beleg >= 0.6;
        letzterTakt = takt;
        letzterZustand = jetzt;
        return true;
    }

private:
    static uint64_t lese(const uint8_t *p, unsigned n) {
        uint64_t wert = 0;
        for (unsigned i = 0; i < n; ++i) wert |= static_cast<uint64_t>(p[i]) << (8 * i);
        return wert;
    }
    static void schreibe(uint8_t *p, uint64_t wert, unsigned n) {
        for (unsigned i = 0; i < n; ++i) p[i] = static_cast<uint8_t>(wert >> (8 * i));
    }
    static uint32_t crc32(const uint8_t *p, unsigned n) {
        uint32_t crc = 0xffffffffu;
        for (unsigned i = 0; i < n; ++i) {
            crc ^= p[i];
            for (unsigned bit = 0; bit < 8; ++bit)
                crc = (crc & 1) ? (crc >> 1) ^ 0xedb88320u : crc >> 1;
        }
        return ~crc;
    }
    double gewichte[3][3] = {};
    double erbe[3][3] = {};  // fester Teil der Regel, nie im Gerätestand gespeichert
    const Regel regel;
    const double faktor;
    uint32_t letzterTakt = 0;
    Zustand letzterZustand = UNBEKANNT;
};
