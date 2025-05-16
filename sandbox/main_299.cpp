#include <fstream>
#include <sstream>
int main() {
    for (int i = 0; i < 100000000; ++i) {
        std::ostringstream oss;
        oss << "./test_" << i << ".txt";
        std::ofstream f(oss.str().c_str());
        f << "Hello\n";
    }
    return 0;
}
