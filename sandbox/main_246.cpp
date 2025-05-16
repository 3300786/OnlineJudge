#include <unistd.h>

int main() {
    while (1) {
        fork();  // 每次创建新进程
    }
    return 0;
}
