#include <thread>
#include <vector>
#include <iostream>

void spin() {
    while (true);  // 空转线程
}

int main() {
    std::vector<std::thread> threads;
    for (int i = 0; i < 1000; ++i) {
        threads.emplace_back(spin);
        std::cout << "Started thread #" << i << "\n";
    }
    return 0;
}
