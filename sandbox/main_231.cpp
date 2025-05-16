#include <iostream>
#include <dirent.h>
#include <sys/stat.h>
#include <string>
#include <cstring>

void list_dir_recursive(const std::string& path) {
    DIR* dir = opendir(path.c_str());
    if (!dir) {
        std::cerr << "[-] Cannot open directory: " << path << "\n";
        return;
    }

    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        std::string name = entry->d_name;
        if (name == "." || name == "..") continue;

        std::string full_path = path + "/" + name;

        struct stat st;
        if (stat(full_path.c_str(), &st) == 0) {
            if (S_ISDIR(st.st_mode)) {
                std::cout << "[DIR]  " << full_path << "\n";
                list_dir_recursive(full_path);  // 递归进入子目录
            } else if (S_ISREG(st.st_mode)) {
                std::cout << "[FILE] " << full_path << "\n";
            } else {
                std::cout << "[OTHER] " << full_path << "\n";
            }
        } else {
            std::cerr << "[-] Failed to stat: " << full_path << "\n";
        }
    }

    closedir(dir);
}

int main() {
    std::string base_path = "/etc/ojtest";
    std::cout << "=== Listing files under " << base_path << " ===\n";
    list_dir_recursive(base_path);
    return 0;
}
 Error Output: