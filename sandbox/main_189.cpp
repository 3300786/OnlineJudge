#include <filesystem>
#include <iostream>

int main() {
    const char* paths[] = {
        "/home/judge/data",
        "/var/lib/mysql",
        "/var/log",
        "/domjudge/problems",
        "/tmp",
        "/var/lib/docker",
        "/etc/domjudge",
        "/home/sandbox",
        "/var/www/html"
    };

    for (const auto& path : paths) {
        std::cout << "[*] Checking: " << path << " ... ";
        if (std::filesystem::exists(path)) {
            std::cout << "FOUND ✅\n";
        } else {
            std::cout << "NOT FOUND ❌\n";
        }
    }

    return 0;
}
