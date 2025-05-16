#include <unistd.h>
#include <iostream>

int main() {
    int count = 0;
    for (int i = 0; i < 5000000; ++i) {
        pid_t pid = fork();
        if (pid == 0) {
            std::cout << "Child process " << i << ": PID = " << getpid() << std::endl;
            _exit(0);
        }
        count++;
    }
    std::cout << "Forked " << count << " processes.\n";
    return 0;
}
