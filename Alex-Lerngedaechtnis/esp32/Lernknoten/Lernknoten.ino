// Serieller Replay-Prüfstand. Eine vollständige Zeile löst genau eine Beobachtung aus.
#include "Knoten.h"
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
char zeile[32];
size_t laenge = 0;
bool verwerfen = false;
const char *const namen[] = {"OK", "SCHWACH", "AUSFALL"};

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
    if (strcmp(zeile, "SICHERN") == 0) return lernstand(true);
    if (strcmp(zeile, "LADEN") == 0) return lernstand(false);
    if (strcmp(zeile, "NEUER_LAUF") == 0) {
        knoten.neuerLauf();
        Serial.println(bereit);
        return true;
    }
    char *text = zeile;
    uint32_t takt = 0;
    if (*text < '0' || *text > '9') return false;
    while (*text >= '0' && *text <= '9') {
        const unsigned ziffer = *text++ - '0';
        if (takt > (UINT32_MAX - ziffer) / 10) return false;
        takt = takt * 10 + ziffer;
    }
    if (*text++ != ',') return false;
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
