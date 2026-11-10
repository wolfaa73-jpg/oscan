#pragma once
#include <stdint.h>
#include <stdio.h>

// Selbsterkundung: Der Knoten sucht unter freien Pins selbst einen, der ihn kühlt, und setzt ihn
// danach bei Wärme ein. Hier stehen nur die Entscheidungen, ohne GPIO. Welche Pins überhaupt in
// Frage kommen und was sie schalten, steht im Sketch. So lässt sich der Ablauf am Rechner prüfen und
// mit selbsterkundung.py vergleichen. Alles ist ganzzahlig, damit Gerät und Python exakt gleich rechnen.
//
// Ein Versuch hat zwei Phasen. In der ersten bleibt alles, wie es ist, ruhe Takte lang. Dann wird
// ein Pin umgeschaltet, und es folgen an Takte. Verglichen werden die letzten mittel Takte beider
// Phasen. Die Wirkung eines Pins ist die Temperatur mit ihm an minus die ohne ihn. Je Pin zählen die
// letzten fenster Versuche. Ein Pin kühlt, wenn es mindestens drei sind und ihr Mittel auch nach
// Abzug von zwei Standardfehlern noch um mehr als schwelle kühlt.
//
// Ohne bekannten Kühler erkundet der Knoten: zufällige Reihenfolge, jeder Pin einmal je Runde, ein
// verdächtiger Pin wird sofort nachgeprüft. Mit Kühler regelt er: an ab warm, aus ab 1 °C darunter,
// frühestens mittel Takte nach dem letzten Schalten. Nach je pruefe Takten Regelung prüft er im
// Wechsel den Kühler selbst, indem er ihn umschaltet, und einen anderen Pin. Kühlt der Kühler nicht
// mehr, etwa weil der Lüfter umgesteckt wurde, erkundet er wieder.
struct Erkundung {
    static const unsigned maxPins = 24, maxFenster = 8, maxZeilen = 4, zeilenLaenge = 96;
    static const int32_t maxTemp = 2000;  // Zehntelgrad; was darüber liegt, zählt wie ein fehlender Messwert
    enum Urteil : uint8_t { OFFEN, VERDACHT, KUEHLT, KEINE };

    // nummern: die Kandidaten, aufsteigend. warm: Zehntelgrad, ab denen der Kühler läuft.
    bool starte(const uint8_t *nummern, unsigned anzahl, uint32_t ruhe, uint32_t an, uint32_t mittel,
                uint32_t schwelle, uint32_t fenster, uint32_t pruefe, uint32_t saat, int32_t warm) {
        if (!anzahl || anzahl > maxPins || !mittel || mittel > ruhe || mittel > an || ruhe > 3600 || an > 3600
            || !schwelle || schwelle > 1000 || fenster < 3 || fenster > maxFenster || pruefe > 86400 || !saat)
            return false;
        for (unsigned i = 1; i < anzahl; ++i)
            if (nummern[i] <= nummern[i - 1]) return false;
        *this = Erkundung();
        n = anzahl;
        for (unsigned i = 0; i < n; ++i) {
            nummer[i] = nummern[i];
            runde[i] = static_cast<uint8_t>(i);
        }
        ruheTakte = ruhe;
        anTakte = an;
        mittelTakte = mittel;
        schwelleDc = schwelle;
        fensterGroesse = fenster;
        pruefeTakte = pruefe;
        zufall = saat;
        warmDc = warm;
        rundePos = n;  // die erste Wahl mischt
        aktiv_ = true;
        return true;
    }

    // Alles aus, ohne Meldung. Die Kandidaten bleiben bekannt, bis die nächste Erkundung startet.
    void beende() {
        aktiv_ = false;
        for (unsigned i = 0; i < n; ++i) ein[i] = false;
        zeilenZahl = 0;
    }

    bool aktiv() const { return aktiv_; }
    unsigned anzahl() const { return n; }
    uint8_t pin(unsigned i) const { return nummer[i]; }
    bool an(unsigned i) const { return ein[i]; }
    unsigned zeilen() const { return zeilenZahl; }
    const char *zeile(unsigned i) const { return text[i]; }

    // Ein Körpertakt, nach der Messung. Danach gelten an() und zeile() bis zum nächsten Takt.
    void takt(uint32_t t, bool gueltig, int32_t temp) {
        zeilenZahl = 0;
        if (!aktiv_) return;
        if (temp < 0 || temp > maxTemp) gueltig = false;
        if (phase == REGEL) {
            regle(t, gueltig, temp);
            if (pruefeTakte && ++seitPruefung >= pruefeTakte) beginne();
            return;
        }
        ++schritt;
        const uint32_t laenge = phase == VOR ? ruheTakte : anTakte;
        if (schritt > laenge - mittelTakte && gueltig) {
            summe += temp;
            ++zahl;
        }
        if (schritt < laenge) return;
        if (phase == VOR) schalteUm(t); else werteAus(t);
    }

private:
    enum Modus : uint8_t { ERKUNDEN, EINSATZ };
    enum Phase : uint8_t { VOR, NACH, REGEL };

    void beginne() {
        phase = VOR;
        schritt = 0;
        summe = 0;
        zahl = 0;
    }

    void regeln(bool neu) {
        phase = REGEL;
        seitPruefung = 0;
        if (neu) pruefeKuehler = true;  // die erste Prüfung gilt dem neuen Kühler selbst
    }

    // Ende der ersten Phase: Ziel wählen und umschalten.
    void schalteUm(uint32_t t) {
        vorSumme = summe;
        vorZahl = zahl;
        if (modus == ERKUNDEN) {
            ziel = waehle();
            probe = true;
        } else {
            unsigned anderer = 0;
            probe = !pruefeKuehler && anderen(anderer);
            ziel = probe ? anderer : kuehler;
            pruefeKuehler = !pruefeKuehler;
        }
        abschalten = ein[ziel];  // nur beim Kühler möglich: er lief, der Versuch schaltet ihn aus
        schalte(t, ziel, !abschalten, probe ? "PROBE" : "PRUEFUNG");
        phase = NACH;
        schritt = 0;
        summe = 0;
        zahl = 0;
    }

    // Ende der zweiten Phase: Wirkung merken, dann erkunden oder regeln.
    void werteAus(uint32_t t) {
        if (probe) schalte(t, ziel, false, "PROBE");
        const bool vollstaendig = vorZahl == mittelTakte && zahl == mittelTakte;
        int32_t wirkung = 0;
        if (vollstaendig) {
            wirkung = abschalten ? vorSumme - summe : summe - vorSumme;
            merke(ziel, wirkung);
        }
        meldeVersuch(t, vollstaendig, wirkung);
        unsigned bester = 0;
        const bool gefunden = besterKuehler(bester);
        if (modus == ERKUNDEN) {
            if (gefunden) {
                modus = EINSATZ;
                kuehler = bester;
                regeln(true);
            } else {
                beginne();
            }
            return;
        }
        if (!gefunden || bester != kuehler) {
            if (ein[kuehler]) schalte(t, kuehler, false, "WECHSEL");
            if (!gefunden) {
                modus = ERKUNDEN;
                beginne();
                return;
            }
            kuehler = bester;
            regeln(true);
            return;
        }
        regeln(false);
    }

    void regle(uint32_t t, bool gueltig, int32_t temp) {
        if (!gueltig || t - letzterWechsel[kuehler] < mittelTakte) return;
        if (!ein[kuehler] && temp >= warmDc) schalte(t, kuehler, true, "EINSATZ");
        else if (ein[kuehler] && temp <= warmDc - 10) schalte(t, kuehler, false, "EINSATZ");
    }

    void schalte(uint32_t t, unsigned i, bool wert, const char *grund) {
        ein[i] = wert;
        letzterWechsel[i] = t;
        if (zeilenZahl < maxZeilen)
            snprintf(text[zeilenZahl++], zeilenLaenge, "PIN,%lu,%u,%d,%s", static_cast<unsigned long>(t),
                     static_cast<unsigned>(nummer[i]), wert ? 1 : 0, grund);
    }

    unsigned waehle() {
        unsigned beste = n;
        for (unsigned i = 0; i < n; ++i)
            if (urteil(i) == VERDACHT && (beste == n || kleinerMittel(i, beste))) beste = i;
        return beste < n ? beste : ausRunde();
    }

    bool anderen(unsigned &i) {
        if (n < 2) return false;
        do i = ausRunde(); while (i == kuehler);
        return true;
    }

    unsigned ausRunde() {
        if (rundePos >= n) {
            for (unsigned i = n - 1; i > 0; --i) {
                const unsigned j = zufallszahl() % (i + 1);
                const uint8_t x = runde[i];
                runde[i] = runde[j];
                runde[j] = x;
            }
            rundePos = 0;
        }
        return runde[rundePos++];
    }

    uint32_t zufallszahl() {
        zufall ^= zufall << 13;
        zufall ^= zufall >> 17;
        zufall ^= zufall << 5;
        return zufall;
    }

    void merke(unsigned i, int32_t wirkung) {
        werte[i][kopf[i]] = wirkung;
        kopf[i] = static_cast<uint8_t>((kopf[i] + 1) % fensterGroesse);
        if (static_cast<uint32_t>(versuche[i]) < fensterGroesse) ++versuche[i];
    }

    int64_t summeVon(unsigned i) const {
        int64_t s = 0;
        for (unsigned j = 0; j < static_cast<unsigned>(versuche[i]); ++j) s += werte[i][j];
        return s;
    }

    int64_t quadrateVon(unsigned i) const {
        int64_t q = 0;
        for (unsigned j = 0; j < static_cast<unsigned>(versuche[i]); ++j) q += static_cast<int64_t>(werte[i][j]) * werte[i][j];
        return q;
    }

    // Mittel m = s/k, Standardfehler e mit e² = (k·q - s²) / (k²·(k-1)). Kühlt heißt m + 2e <= -schwelle.
    // Mit a = -s - k·schwelle·mittel ist das a >= 0 und a²·(k-1) >= 4·(k·q - s²), ganz ohne Wurzel.
    Urteil urteil(unsigned i) const {
        const int64_t k = versuche[i], s = summeVon(i), q = quadrateVon(i);
        const int64_t a = -s - k * static_cast<int64_t>(schwelleDc) * mittelTakte;
        if (k >= 3 && a >= 0 && a * a * (k - 1) >= 4 * (k * q - s * s)) return KUEHLT;
        if (k >= 1 && a >= 0 && k < fensterGroesse) return VERDACHT;
        return k >= 3 ? KEINE : OFFEN;
    }

    bool kleinerMittel(unsigned i, unsigned j) const {
        return summeVon(i) * versuche[j] < summeVon(j) * versuche[i];
    }

    bool besterKuehler(unsigned &bester) const {
        bool gefunden = false;
        for (unsigned i = 0; i < n; ++i)
            if (urteil(i) == KUEHLT && (!gefunden || kleinerMittel(i, bester))) {
                bester = i;
                gefunden = true;
            }
        return gefunden;
    }

    // Halbe aufwärts, vom Betrag her, so wie rund() in selbsterkundung.py.
    static long rund(int64_t a, int64_t b) {
        return static_cast<long>(a >= 0 ? (2 * a + b) / (2 * b) : -((-2 * a + b) / (2 * b)));
    }

    static uint64_t wurzel(uint64_t x) {
        uint64_t r = 0, bit = static_cast<uint64_t>(1) << 62;
        while (bit > x) bit >>= 2;
        while (bit) {
            if (x >= r + bit) {
                x -= r + bit;
                r = (r >> 1) + bit;
            } else {
                r >>= 1;
            }
            bit >>= 2;
        }
        return r;
    }

    // VERSUCH,takt,pin,art,vor_hg,nach_hg,wirkung_hg,mittel_hg,streuung_hg,anzahl,urteil, Temperaturen
    // in Hundertstelgrad. Fehlte ein Messwert, stehen vor, nach und Wirkung als "-", und der Versuch zählt nicht.
    void meldeVersuch(uint32_t t, bool vollstaendig, int32_t wirkung) {
        static const char *const urteile[] = {"OFFEN", "VERDACHT", "KUEHLT", "KEINE"};
        if (zeilenZahl >= maxZeilen) return;
        const int64_t k = versuche[ziel], s = summeVon(ziel), q = quadrateVon(ziel), m = mittelTakte;
        const long mittelHg = k ? rund(s * 10, k * m) : 0;
        const unsigned long streuungHg =
            k >= 2 ? static_cast<unsigned long>(wurzel(static_cast<uint64_t>((k * q - s * s) * 100 / (k * (k - 1) * m * m))))
                   : 0;
        char *z = text[zeilenZahl++];
        const int n0 = snprintf(z, zeilenLaenge, "VERSUCH,%lu,%u,%s,", static_cast<unsigned long>(t),
                                static_cast<unsigned>(nummer[ziel]), abschalten ? "AUS" : "AN");
        if (n0 < 0 || n0 >= static_cast<int>(zeilenLaenge)) return;
        if (vollstaendig)
            snprintf(z + n0, zeilenLaenge - n0, "%ld,%ld,%ld,%ld,%lu,%u,%s", rund(static_cast<int64_t>(vorSumme) * 10, m),
                     rund(static_cast<int64_t>(summe) * 10, m), rund(static_cast<int64_t>(wirkung) * 10, m), mittelHg,
                     streuungHg, static_cast<unsigned>(k), urteile[urteil(ziel)]);
        else
            snprintf(z + n0, zeilenLaenge - n0, "-,-,-,%ld,%lu,%u,%s", mittelHg, streuungHg, static_cast<unsigned>(k),
                     urteile[urteil(ziel)]);
    }

    bool aktiv_ = false;
    Modus modus = ERKUNDEN;
    Phase phase = VOR;
    unsigned n = 0;
    uint8_t nummer[maxPins] = {};
    uint8_t runde[maxPins] = {};
    unsigned rundePos = 0;
    bool ein[maxPins] = {};
    uint32_t letzterWechsel[maxPins] = {};
    int32_t werte[maxPins][maxFenster] = {};
    uint8_t versuche[maxPins] = {};
    uint8_t kopf[maxPins] = {};
    uint32_t ruheTakte = 0, anTakte = 0, mittelTakte = 0, schwelleDc = 0, fensterGroesse = 0, pruefeTakte = 0;
    uint32_t zufall = 0;
    int32_t warmDc = 0;
    uint32_t schritt = 0, zahl = 0, vorZahl = 0, seitPruefung = 0;
    int32_t summe = 0, vorSumme = 0;
    unsigned ziel = 0, kuehler = 0;
    bool probe = false, abschalten = false, pruefeKuehler = false;
    unsigned zeilenZahl = 0;
    char text[maxZeilen][zeilenLaenge] = {};
};
