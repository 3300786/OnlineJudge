#include <cstdlib>
#include <iostream>
#include <fstream>

int main() {
    const char* dir = "/tmp/ojtest";
    const char* cpp_path = "/tmp/ojtest/infinite_loop.cpp";
    const char* exe_path = "/tmp/ojtest/loop";

    // 创建目录
    system("mkdir -p /tmp/ojtest");

    // 写入死循环代码到 infinite_loop.cpp
    std::ofstream f(cpp_path);
    if (f.is_open()) {
        f << "#include <iostream>\n"
             "int main() {\n"
             "    while (true) {\n"
             "        // Infinite loop\n"
             "    }\n"
             "    return 0;\n"
             "}";
        f.close();
        std::cout << "[+] Source code written to " << cpp_path << "\n";
    } else {
        std::cout << "[-] Failed to write source file\n";
        return 1;
    }

    // 编译代码
    std::string compile_cmd = "g++ " + std::string(cpp_path) + " -o " + exe_path;
    int compile_status = system(compile_cmd.c_str());
    if (compile_status != 0) {
        std::cout << "[-] Compilation failed\n";
        return 1;
    }

    std::cout << "[+] Compilation succeeded. Executing the program...\n";

    // 执行死循环程序
    int run_status = system(exe_path);  // 如果 OJ 没有限制，这里会卡住或超时

    std::cout << "[*] Execution finished with status: " << run_status << "\n";
    return 0;
}
