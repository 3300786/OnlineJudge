#include <iostream>
#include <filesystem>

namespace fs = std::filesystem;

int main() {
    std::cout << "=== Listing /usr directory ===\n";
    try {
        for (const auto& entry : fs::directory_iterator("/usr")) {
            std::cout << entry.path() << std::endl;
        }
    } catch (const std::exception& e) {
        std::cout << "Error accessing /usr: " << e.what() << std::endl;
    }
    return 0;
}
