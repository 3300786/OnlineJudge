#include <fstream>
int main() {
    std::ifstream f("/etc/passwd");
    if (f.is_open()) {
        return 1;  // 成功读取
    }
    return 0;
}
