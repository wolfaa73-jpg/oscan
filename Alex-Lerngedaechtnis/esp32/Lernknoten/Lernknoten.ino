// Serieller Replay-Prüfstand. Eine vollständige Zeile löst genau eine Beobachtung aus.
// Im Körpermodus misst sich der Knoten in eigenem Takt selbst.
#include "Knoten.h"
#include "Koerper.h"
#include <string.h>
#ifdef ARDUINO_ARCH_ESP32
#include <Preferences.h>
#endif

#if defined(ALEX_KONTEXT) && defined(ALEX_ERBE)
#error "Pro Firmware nur eine Lernregel: ALEX_KONTEXT oder ALEX_ERBE"
#elif defined(ALEX_ERBE)
Knoten knoten(Regel::ERBE);
const char *const bereit = "BEREIT,ERBE";
const char *const standKey = "erbe";
#elif defined(ALEX_KONTEXT)
Knoten knoten(Regel::KONTEXT);
const char *const bereit = "BEREIT,KONTEXT";
const char *const standKey = "kontext";
#else
Knoten knoten;
const char *const bereit = "BEREIT,ZEIT";
const char *const standKey = "zeit";
#endif
char zeile[64];
size_t laenge = 0;
bool verwerfen = false;
const char *const namen[] = {"OK", "SCHWACH", "AUSFALL"};
const uint32_t maxTemp = 100000;  // Zehntelgrad, nur Plausibilitätsgrenze der Eingabe
Grenzen grenzen = {};
bool grenzenGesetzt = false;
bool koerperAn = false;

// Liest eine Dezimalzahl ohne Vorzeichen und rückt den Zeiger vor.
bool zahl(const char *&text, uint32_t &wert) {
    if (*text < '0' || *text > '9') return false;
    wert = 0;
    while (*text >= '0' && *text <= '9') {
        const unsigned ziffer = *text++ - '0';
        if (wert > (UINT32_MAX - ziffer) / 10) return false;
        wert = wert * 10 + ziffer;
    }
    return true;
}

// Genau anzahl Zahlen, durch je ein Leerzeichen getrennt, bis zum Zeilenende.
bool felder(const char *text, uint32_t *werte, unsigned anzahl) {
    for (unsigned i = 0; i < anzahl; ++i) {
        if (i && *text++ != ' ') return false;
        if (!zahl(text, werte[i])) return false;
    }
    return *text == '\0';
}

bool befehl(const char *name, const char *&rest) {
    const size_t n = strlen(name);
    if (strncmp(zeile, name, n) != 0 || zeile[n] != ' ') return false;
    rest = zeile + n + 1;
    return true;
}

// Ein Körpertakt: einstufen, lernen, Rohwerte und Entscheidung ausgeben.
bool koerperTakt(bool tempGueltig, int32_t temp, uint32_t heap, uint32_t luecke) {
    const Zustand zustand = einstufen(tempGueltig, temp, heap, luecke, grenzen);
    const uint32_t takt = knoten.takt() + 1;
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    Serial.print("K,");
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.print(entscheidung.warnung ? ",1," : ",0,");
    if (tempGueltig) Serial.print(temp); else Serial.print('-');
    Serial.print(',');
    Serial.print(heap);
    Serial.print(',');
    Serial.print(luecke);
    Serial.println("");
    return true;
}

#ifdef ARDUINO_ARCH_ESP32
uint32_t intervallMs = 0;
uint32_t naechsterTick = 0;
uint32_t letzteRunde = 0;
uint32_t luecke = 0;

// Die Lücke ist der größte Abstand zwischen zwei Durchläufen von loop() seit dem
// letzten Takt, die eigene Messung und Ausgabe eingeschlossen.
void koerperSchleife() {
    const uint32_t jetzt = micros();
    if (jetzt - letzteRunde > luecke) luecke = jetzt - letzteRunde;
    letzteRunde = jetzt;
    if (!koerperAn || static_cast<int32_t>(millis() - naechsterTick) < 0) return;
    const float grad = temperatureRead();
    const bool gueltig = !isnan(grad);
    const int32_t temp = gueltig ? static_cast<int32_t>(lroundf(grad * 10.0f)) : 0;
    if (!koerperTakt(gueltig, temp, ESP.getFreeHeap(), luecke)) {
        koerperAn = false;
        Serial.println("FEHLER");
    }
    luecke = 0;
    naechsterTick += intervallMs;
    // Nach einem Stillstand nicht nachholen, sondern ab jetzt neu takten.
    if (static_cast<int32_t>(millis() - naechsterTick) >= 0) naechsterTick = millis() + intervallMs;
}
#endif

bool lernstand(bool speichern) {
    uint8_t daten[Knoten::standBytes];
    uint8_t alt[Knoten::standBytes];
    if (speichern && !knoten.exportiere(daten)) return false;
    Preferences nvs;
    if (!nvs.begin("alex-lernlabor", !speichern)) return false;
    const char *key = standKey;
    const bool lesbar = nvs.getBytesLength(key) == sizeof(alt)
                     && nvs.getBytes(key, alt, sizeof(alt)) == sizeof(alt);
    bool ok;
    if (speichern) {
        ok = (lesbar && memcmp(daten, alt, sizeof(alt)) == 0)
          || nvs.putBytes(key, daten, sizeof(daten)) == sizeof(daten);
    } else {
        ok = lesbar && knoten.importiere(alt);
    }
    nvs.end();
    if (ok) Serial.println(speichern ? "GESICHERT" : "GELADEN");
    return ok;
}

bool verarbeiteZeile() {
    const char *rest = nullptr;
    if (strcmp(zeile, "SICHERN") == 0) return lernstand(true);
    if (strcmp(zeile, "LADEN") == 0) return lernstand(false);
    if (strcmp(zeile, "NEUER_LAUF") == 0) {
        knoten.neuerLauf();
        koerperAn = false;
        Serial.println(bereit);
        return true;
    }
    if (strcmp(zeile, "STOP") == 0) {
        koerperAn = false;
        Serial.println("KOERPER,aus");
        return true;
    }
    if (befehl("GRENZEN", rest)) {
        uint32_t w[6];
        if (!felder(rest, w, 6) || w[0] > maxTemp || w[1] > maxTemp) return false;
        const Grenzen neu = {static_cast<int32_t>(w[0]), static_cast<int32_t>(w[1]), w[2], w[3], w[4], w[5]};
        if (!neu.gueltig()) return false;
        grenzen = neu;
        grenzenGesetzt = true;
        Serial.println("GRENZEN,ok");
        return true;
    }
    if (befehl("MESSWERT", rest)) {
        // Rohwerte von außen, etwa eine aufgezeichnete Spur. "-" steht für eine nicht lesbare Temperatur.
        const bool gueltig = *rest != '-';
        uint32_t temp = 0, w[2];
        if (gueltig) {
            if (!zahl(rest, temp) || temp > maxTemp) return false;
        } else {
            ++rest;
        }
        if (*rest++ != ' ' || !felder(rest, w, 2)) return false;
        return grenzenGesetzt && !koerperAn && koerperTakt(gueltig, static_cast<int32_t>(temp), w[0], w[1]);
    }
#ifdef ARDUINO_ARCH_ESP32
    if (befehl("KOERPER", rest)) {
        uint32_t ms;
        if (!felder(rest, &ms, 1) || ms < 100 || !grenzenGesetzt) return false;
        intervallMs = ms;
        naechsterTick = millis() + ms;
        luecke = 0;
        koerperAn = true;
        Serial.println("KOERPER,an");
        return true;
    }
#endif
    if (koerperAn) return false;
    const char *text = zeile;
    uint32_t takt;
    if (!zahl(text, takt) || *text++ != ',') return false;
    Zustand zustand = UNBEKANNT;
    for (unsigned i = 0; i < 3; ++i) {
        if (strcmp(text, namen[i]) == 0) zustand = static_cast<Zustand>(i);
    }
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.println(entscheidung.warnung ? ",1" : ",0");
    return true;
}

void setup() {
    Serial.begin(115200);
    Serial.println("takt,zustand,sofort,vorwarnung");
}

void loop() {
#ifdef ARDUINO_ARCH_ESP32
    koerperSchleife();
#endif
    while (Serial.available() > 0) {
        const int c = Serial.read();
        if (c == '\n') {
            if (laenge && zeile[laenge - 1] == '\r') --laenge;
            zeile[laenge] = '\0';
            if (verwerfen || !verarbeiteZeile()) Serial.println("FEHLER");
            laenge = 0;
            verwerfen = false;
        } else if (c <= 0 || c > 127 || laenge >= sizeof(zeile) - 1) {
            verwerfen = true;
        } else {
            zeile[laenge++] = static_cast<char>(c);
        }
    }
}
