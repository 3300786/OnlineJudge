#include <iostream>
#include <dirent.h>
#include <cstring>
#include <vector>
#include <string>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>

bool is_directory(const std::string& path) {
    struct stat info;
    return stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode);
}

void recursive_scan(const std::string& base, const std::vector<std::string>& keywords) {
    DIR* dir = opendir(base.c_str());
    if (!dir) return;

    struct dirent* entry;
    while ((entry = readdir(dir)) != nullptr) {
        std::string name = entry->d_name;
        if (name == "." || name == "..") continue;

        std::string fullpath = base + "/" + name;

        for (const auto& k : keywords) {
            if (fullpath.find(k) != std::string::npos) {
                std::cout << "[*] Found: " << fullpath << "\n";
                break;
            }
        }

        if (is_directory(fullpath)) {
            // 为了防止无限递归（符号链接形成环），跳过符号链接目录
            struct stat st;
            if (lstat(fullpath.c_str(), &st) == 0 && S_ISLNK(st.st_mode)) continue;

            recursive_scan(fullpath, keywords);
        }
    }

    closedir(dir);
}

int main() {
    std::vector<std::string> keywords = {
        "mysql", "mysqld", "my.cnf", "passwd", "shadow"
    };

    std::cout << "=== Deep scanning from / ===\n";
    recursive_scan("/", keywords);

    return 0;
}
