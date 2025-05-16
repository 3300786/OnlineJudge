#include <iostream>

struct MegaChunk {
    char data[1024];  // 每个 chunk 1KB
};

// 构造一个一次性展开的超大数组
struct MegaObject {
    MegaChunk chunks[102400];  // 102400 * 1KB = 100MB
};

int main() {
    MegaObject obj;
    std::cout << "Done\n";
    return 0;
}
