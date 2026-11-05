// Der Test benutzt denselben Sketch. Nur die serielle Schnittstelle wird ersetzt.
#include <iostream>
#include <fstream>
#include <cstring>
#include <cstdlib>

// Dateibackend nur im Hostprüfstand. Getrennte Testprozesse simulieren einen Neustart.
struct Preferences {
    const char *pfad = nullptr;
    bool begin(const char *, bool) {
        pfad = std::getenv("ALEX_TEST_NVS");
        return pfad != nullptr;
    }
    size_t getBytesLength(const char *) {
        std::ifstream f(pfad, std::ios::binary | std::ios::ate);
        return f ? static_cast<size_t>(f.tellg()) : 0;
    }
    size_t getBytes(const char *, void *p, size_t n) {
        std::ifstream f(pfad, std::ios::binary);
        return f.read(static_cast<char *>(p), n) ? n : 0;
    }
    size_t putBytes(const char *, const void *p, size_t n) {
        std::ofstream f(pfad, std::ios::binary);
        f.write(static_cast<const char *>(p), n);
        f.close();
        return f ? n : 0;
    }
    void end() {}
};
struct HostSerial {
    void begin(unsigned) {}
    int available() { return std::cin.peek() == EOF ? 0 : 1; }
    int read() { return std::cin.get(); }
    template<typename T> void print(T wert) { std::cout << wert; }
    void println(const char *text) { std::cout << text << '\n'; }
} Serial;
#include "Lernknoten/Lernknoten.ino"

int main() {
    setup();
    loop();
}
