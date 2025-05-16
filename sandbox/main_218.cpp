#include <cstdlib>
#include <iostream>
#include <string>

int main() {
    std::string base = "/tmp/ojtest";

    // 创建 base 目录
    std::string mkdir_cmd = "mkdir -p " + base;
    system(mkdir_cmd.c_str());

    // 创建多个子目录并生成文件
    for (int i = 0; i < 100; ++i) { // 100个子目录
        std::string subdir = base + "/dir" + std::to_string(i);
        std::string mkdir_sub = "mkdir -p " + subdir;
        system(mkdir_sub.c_str());

        for (int j = 0; j < 10; ++j) { // 每个子目录 10 个文件，总共 1000 个
            std::string filepath = subdir + "/file" + std::to_string(j) + ".txt";
            std::string cmd = "echo test > " + filepath;
            system(cmd.c_str());
        }
    }

    std::cout << "[+] Finished creating 1000 files under " << base << "\n";
    return 0;
}
