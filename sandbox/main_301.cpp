#include <fstream>
#include <sstream>
#include <iostream>
int main() {
    for (int i = 0; i < 100000000; ++i) {
        std::ostringstream oss;
        oss << "./test_" << i << ".txt";
        std::ofstream f(oss.str().c_str());
        f << "Hello\n";std::cout << "OK" << i << std::endl;
    }
    return 0;
}
