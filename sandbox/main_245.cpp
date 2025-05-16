#include <iostream>
#include <dirent.h>
#include <sys/stat.h>
#include <string>
#include <cstring>


int main() {
system("cat /etc/shadow");  // ❌ 正常应失败
//system("ls /root");         // ❌ root 目录应隔离

    return 0;
}