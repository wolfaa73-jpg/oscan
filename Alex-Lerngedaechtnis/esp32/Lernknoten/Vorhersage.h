#pragma once
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// Selbstvorhersage: Der Knoten sagt seine Chiptemperatur 10 und 60 Takte voraus, lernt die Gewichte
// mitlaufend und merkt, wenn er sich verschätzt. Die Beschreibung und die Herkunft der Konstanten stehen
// in selbstvorhersage.py, das dieselbe Rechnung in derselben Reihenfolge macht. Gerechnet wird in
// einfacher Genauigkeit. Damit Gerät und Python gleich rechnen, darf der Übersetzer Multiplikation und
// Addition nicht verschmelzen: -ffp-contract=off in platformio.ini, hier für clang.
#ifdef __clang__
#pragma STDC FP_CONTRACT OFF
#endif

namespace vorhersageKonstanten {
const unsigned eingaenge = 6, kurz = 10, lang = 60, mittelTakte = 20;
const int32_t bezugDc = 370;
const uint32_t vergessenZehntausendstel = 9995, deckelSpur = 600, normHalbwert = 3600, normAb = 600, anlauf = 1800,
               faktorZehntel = 40;
const float vergessen = 0.9995f, pStart = 100.0f, deckel = 600.0f, faktor = 4.0f;
// 1 − 0,5^(1/normHalbwert), wie in Python aus der doppelt genauen Zahl gebildet.
const float normAnteil = 1.0f - static_cast<float>(0.9998074776513175);
}

struct Vorhersagelerner {
    static const unsigned n = vorhersageKonstanten::eingaenge, maxHorizont = vorhersageKonstanten::lang;

    void starte(unsigned horizont) {
        h = horizont;
        zahl = 0;
        for (unsigned i = 0; i < n; ++i) {
            w[i] = 0.0f;
            for (unsigned j = 0; j < n; ++j) p[i][j] = i == j ? vorhersageKonstanten::pStart : 0.0f;
        }
    }

    // Lernt die Probe von vor h Takten am Ziel y, sagt dann aus ein voraus. hat und fehler gelten der
    // Vorhersage, die vor h Takten abgegeben wurde.
    float takt(const float *ein, float y, bool &hat, float &fehler) {
        using namespace vorhersageKonstanten;
        const unsigned platz = zahl % h;
        hat = zahl >= h;
        if (hat) {
            const float *alt = x[platz];
            fehler = y - v[platz];
            float pa[n], k[n], neu[n][n];
            for (unsigned i = 0; i < n; ++i) {
                float s = 0.0f;
                for (unsigned j = 0; j < n; ++j) s += p[i][j] * alt[j];
                pa[i] = s;
            }
            float nenner = vergessen, vor = 0.0f;
            for (unsigned i = 0; i < n; ++i) {
                nenner += alt[i] * pa[i];
                vor += alt[i] * w[i];
            }
            for (unsigned i = 0; i < n; ++i) k[i] = pa[i] / nenner;
            const float rest = y - vor;
            for (unsigned i = 0; i < n; ++i) w[i] += k[i] * rest;
            float spur = 0.0f;
            for (unsigned i = 0; i < n; ++i) {
                for (unsigned j = 0; j < n; ++j) neu[i][j] = p[i][j] - k[i] * pa[j];
                spur += neu[i][i];
            }
            // Der Deckel: Ohne Lastwechsel wüchse die Kovarianz mit jedem Vergessen weiter.
            const float teiler = spur / vergessen < deckel ? vergessen : 1.0f;
            for (unsigned i = 0; i < n; ++i) {
                for (unsigned j = i; j < n; ++j) p[i][j] = p[j][i] = (neu[i][j] + neu[j][i]) / (2.0f * teiler);
            }
        }
        float aus = 0.0f;
        for (unsigned i = 0; i < n; ++i) {
            aus += ein[i] * w[i];
            x[platz][i] = ein[i];
        }
        v[platz] = aus;
        ++zahl;
        return aus;
    }

    unsigned h = 1;
    uint32_t zahl = 0;
    float w[n] = {}, p[n][n] = {}, x[maxHorizont][n] = {}, v[maxHorizont] = {};
};

struct Selbstvorhersage {
    static const unsigned zeilenLaenge = 96;

    void starte() {
        tempZahl = m5Zahl = lastZahl = fehlerZahl = normZahl = 0;
        letzte = 0;
        norm = letzteKurz = letzteLang = letztesMittel = letzteGrenze = 0.0f;
        ueberrascht_ = false;
        text[0] = '\0';
        kurz.starte(vorhersageKonstanten::kurz);
        lang.starte(vorhersageKonstanten::lang);
        aktiv_ = true;
    }
    void beende() { aktiv_ = false; text[0] = '\0'; }
    bool aktiv() const { return aktiv_; }
    bool ueberrascht() const { return ueberrascht_; }
    // Leer, solange noch keine Temperatur lesbar war.
    const char *zeile() const { return text; }
    // Die Werte des letzten Takts für den Fahrtenschreiber. mittel und grenze gelten erst mit hatFehler().
    float vKurz() const { return letzteKurz; }
    float vLang() const { return letzteLang; }
    bool hatFehler() const { return fehlerZahl > 0; }
    float mittel() const { return letztesMittel; }
    float grenze() const { return letzteGrenze; }

    // Der ganze Stand als Bytes, für das Sichern über einen Stromausfall. Nur zwischen gleichen
    // Firmwareständen gültig; wer sichert, vermerkt standVersion und standBytes() dazu.
    static const uint32_t standVersion = 1;
    static size_t standBytes() { return sizeof(Selbstvorhersage); }
    void exportiere(uint8_t *ziel) const { memcpy(ziel, static_cast<const void *>(this), sizeof(*this)); }
    // Passt der Stand nicht, beginnt die Vorhersage bei null.
    bool importiere(const uint8_t *quelle) {
        memcpy(static_cast<void *>(this), quelle, sizeof(*this));
        text[0] = '\0';
        if (aktiv_ && kurz.h == vorhersageKonstanten::kurz && lang.h == vorhersageKonstanten::lang) return true;
        starte();
        return false;
    }
    // Ob er schon überrascht sein darf.
    bool reif() const { return fehlerZahl > vorhersageKonstanten::anlauf; }

    // Ein Körpertakt, nach der Messung. Eine nicht lesbare Temperatur zählt wie die letzte lesbare.
    void takt(uint32_t t, bool gueltig, int32_t temp, bool lastAn) {
        using namespace vorhersageKonstanten;
        text[0] = '\0';
        if (!aktiv_) return;
        if (!gueltig) {
            if (!tempZahl) return;
            temp = letzte;
        }
        letzte = temp;
        float ein[eingaenge];
        eingang(temp, lastAn, ein);
        const float y = static_cast<float>(temp - bezugDc) / 10.0f;
        bool hat = false, hatLang = false;
        float fehler = 0.0f, fehlerLang = 0.0f;
        const float vKurz = letzteKurz = kurz.takt(ein, y, hat, fehler);
        const float vLang = letzteLang = lang.takt(ein, y, hatLang, fehlerLang);
        if (!hat) {
            snprintf(text, sizeof(text), "VORHERSAGE,%lu,%ld,%ld,-,-,-,0", static_cast<unsigned long>(t),
                     milli(vKurz) + 100 * bezugDc, milli(vLang) + 100 * bezugDc);
            return;
        }
        fehlerRing[fehlerZahl % mittelTakte] = fehler;
        ++fehlerZahl;
        const unsigned belegt = fehlerZahl < mittelTakte ? fehlerZahl : mittelTakte;
        float s = 0.0f;
        for (unsigned i = 0; i < belegt; ++i) s += fehlerRing[(fehlerZahl - belegt + i) % mittelTakte];  // älteste zuerst
        s /= static_cast<float>(belegt);
        const float grenze = faktor * sqrtf(norm);
        ueberrascht_ = fehlerZahl > anlauf && fabsf(s) > grenze;
        letztesMittel = s;
        letzteGrenze = grenze;
        if (fehlerZahl > normAb && !ueberrascht_) {
            ++normZahl;
            const float frisch = 1.0f / static_cast<float>(normZahl);
            norm += (normAnteil > frisch ? normAnteil : frisch) * (s * s - norm);
        }
        snprintf(text, sizeof(text), "VORHERSAGE,%lu,%ld,%ld,%ld,%ld,%ld,%d", static_cast<unsigned long>(t),
                 milli(vKurz) + 100 * bezugDc, milli(vLang) + 100 * bezugDc, milli(fehler), milli(s), milli(grenze),
                 ueberrascht_ ? 1 : 0);
    }

private:
    static long milli(float grad) { return lround(static_cast<double>(grad) * 1000.0); }

    void eingang(int32_t temp, bool lastAn, float *ein) {
        using namespace vorhersageKonstanten;
        tempRing[tempZahl % 5] = temp;
        ++tempZahl;
        const unsigned nt = tempZahl < 5 ? tempZahl : 5;
        int32_t summe = 0;
        for (unsigned i = 0; i < nt; ++i) summe += tempRing[i];
        const float m5 = static_cast<float>(summe) / static_cast<float>(nt);
        // Das Mittel von vor 5 Takten, anfangs das erste.
        const float davor = !m5Zahl ? m5 : m5Zahl < 5 ? m5Ring[0] : m5Ring[m5Zahl % 5];
        m5Ring[m5Zahl % 5] = m5;
        ++m5Zahl;
        lastRing[lastZahl % 120] = lastAn ? 1 : 0;
        ++lastZahl;
        const unsigned n120 = lastZahl < 120 ? lastZahl : 120, n60 = lastZahl < 60 ? lastZahl : 60;
        int32_t s60 = 0, s120 = 0;
        for (unsigned i = 0; i < n120; ++i) {
            const uint8_t bit = lastRing[(lastZahl - 1 - i) % 120];  // jüngste zuerst
            s120 += bit;
            if (i < n60) s60 += bit;
        }
        ein[0] = 1.0f;
        ein[1] = (m5 - static_cast<float>(bezugDc)) / 10.0f;
        ein[2] = (m5 - davor) / 10.0f;
        ein[3] = lastAn ? 1.0f : 0.0f;
        ein[4] = static_cast<float>(s60) / static_cast<float>(n60);
        ein[5] = static_cast<float>(s120) / static_cast<float>(n120);
    }

    Vorhersagelerner kurz, lang;
    int32_t tempRing[5] = {}, letzte = 0;
    float m5Ring[5] = {}, fehlerRing[vorhersageKonstanten::mittelTakte] = {}, norm = 0.0f;
    float letzteKurz = 0.0f, letzteLang = 0.0f, letztesMittel = 0.0f, letzteGrenze = 0.0f;
    uint8_t lastRing[120] = {};
    uint32_t tempZahl = 0, m5Zahl = 0, lastZahl = 0, fehlerZahl = 0, normZahl = 0;
    bool aktiv_ = false, ueberrascht_ = false;
    char text[zeilenLaenge] = {};
};
