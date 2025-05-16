#include <thread>
void loop() { while (1); }
int main() {
    for (int i = 0; i < 64; ++i)
        std::thread(loop).detach();
    while (1);
}
