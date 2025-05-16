#include <fstream>
#include <iostream>
#include <string>

int main() {
    const char* path = "/tmp/ojtest/infinite_loop.cpp";

    std::ifstream file(path);
    if (!file.is_open()) {
        std::cout << "[-] Failed to open file: " << path << "\n";
        return 1;
    }

    std::cout << "[+] Successfully opened: " << path << "\n";
    std::cout << "=== File content ===\n";

    std::string line;
    while (std::getline(file, line)) {
        std::cout << line << "\n";
    }

    file.close();
    return 0;
}
