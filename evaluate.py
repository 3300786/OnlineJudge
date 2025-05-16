import subprocess
import os
import shutil
import uuid
from datetime import datetime
from extensions import db
from app import app
from models import Submission, Problem

WORKDIR = "sandbox"
MAX_CODE_LENGTH = 65536  # 64KB 的代码上限
MAX_TEMPLATE_COUNT = 50  # 如果 "template" 出现过多，就可能是模板炸弹
MAX_LOG_LENGTH = 4096  # 限制 Docker 返回日志长度


def evaluate_submission(submission_id):
    with app.app_context():
        print(f"Starting evaluation for submission {submission_id}")
        sub = Submission.query.get(submission_id)
        if not sub:
            print("Submission not found.")
            return

        prob = Problem.query.get(sub.problem_id)
        if not prob:
            print("Problem not found.")
            return

        # 判断代码长度是否合理
        if len(sub.code) > MAX_CODE_LENGTH:
            sub.status = "Rejected"
            sub.error_message = "Code exceeds maximum allowed length."
            db.session.commit()
            return

        # 检查危险关键字过多出现，防止模板炸弹
        if sub.code.lower().count("template") > MAX_TEMPLATE_COUNT:
            sub.status = "Rejected"
            sub.error_message = "Excessive template usage detected - possible compilation bomb."
            db.session.commit()
            return

        # 创建工作目录
        if not os.path.exists(WORKDIR):
            os.makedirs(WORKDIR)

        language = (sub.language or "cpp").lower()

        # 生成唯一 ID 后缀，防止文件覆盖
        uid = str(uuid.uuid4())[:8]
        code_path = os.path.join(WORKDIR, f"main_{submission_id}_{uid}")
        output_path = os.path.join(WORKDIR, f"out_{submission_id}_{uid}.txt")
        input_filename = os.path.basename(prob.input_path)
        input_dir = os.path.abspath(os.path.dirname(prob.input_path))
        docker_image = "oj_sandbox"

        # 公共 Docker 选项和安全选项
        network_opts = ["--network", "none"]
        # 使用 --mount 方式挂载, 将 WORKDIR 挂载为读写目录 (/sandbox)；将输入目录挂载为只读 (/data)；将 /tmp 挂载为 tmpfs
        volume_opts = [
            "--mount", f"type=bind,source={os.path.abspath(WORKDIR)},target=/sandbox",
            "--mount", f"type=bind,source={input_dir},target=/data,readonly",
            "--mount", "type=tmpfs,destination=/tmp"
        ]
        security_opts = [
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "--read-only",  # 设置容器根文件系统为只读
            "-u", "nobody"  # 使用非 root 用户
        ]

        # 针对编译和运行分别设置资源限制
        compile_limits = [
            "--memory", "512m",  # 编译阶段给予512MB内存
            "--cpus", "1.0",
            "--pids-limit", "128",
            "--ulimit", "cpu=2",  # 限制 CPU 时间
            "--ulimit", "fsize=1000000",  # 限制输出文件大小
            "--ulimit", "stack=1048576",  # 限制栈大小（1MB）
            "--ulimit", "nproc=32"  # 限制进程/线程数
        ]
        run_limits = [
            "--memory", f"{prob.memory_limit}m",  # 运行阶段内存限制来自题目要求
            "--cpus", "1.0",
            "--pids-limit", "64",
            "--ulimit", "cpu=2",
            "--ulimit", "fsize=1000000"
        ]

        # 针对 C++ 代码
        if language in ['cpp', 'c++']:
            source_path = code_path + ".cpp"
            exe_path = code_path + ".exe"
            with open(source_path, 'w', newline='\n') as f:
                f.write(sub.code)

            # 编译命令（加入 -ftemplate-depth=32 和 -Werror 以防范炸弹）
            compile_cmd = (
                f"g++ -ftemplate-depth=32 -Werror /sandbox/{os.path.basename(source_path)} -o /sandbox/main "
                f"&& chmod +x /sandbox/main"
            )
            try:
                docker_compile_result = subprocess.run(
                    ["docker", "run", "--rm", "--init"] + network_opts + compile_limits + security_opts + volume_opts +
                    [docker_image, "bash", "-c", compile_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30
                )
                # 截断日志，防止输出过长
                compile_err = docker_compile_result.stderr.decode()
                if len(compile_err) > MAX_LOG_LENGTH:
                    compile_err = compile_err[:MAX_LOG_LENGTH] + "..."
                sub.error_message = compile_err

                if docker_compile_result.returncode != 0:
                    sub.status = "Compile Error"
                    db.session.commit()
                    return
            except subprocess.TimeoutExpired:
                sub.status = "Compile Timeout"
                sub.error_message = "Compilation timed out."
                db.session.commit()
                return
            except Exception as e:
                sub.status = "Compile Error"
                sub.error_message = str(e)
                db.session.commit()
                return

            # 设置运行命令：在运行阶段限制栈大小，防止无限递归
            run_cmd = f"ulimit -s 65536 && /sandbox/main < /data/{input_filename} > /sandbox/{os.path.basename(output_path)}"
            try:
                docker_run_result = subprocess.run(
                    ["docker", "run", "--rm", "--init"] + network_opts + run_limits + security_opts + volume_opts +
                    [docker_image, "bash", "-c", run_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=prob.time_limit
                )
                run_err = docker_run_result.stderr.decode()
                if len(run_err) > MAX_LOG_LENGTH:
                    run_err = run_err[:MAX_LOG_LENGTH] + "..."
                sub.error_message = run_err

                stderr_output = sub.error_message.lower()
                if "segmentation fault" in stderr_output or "core dumped" in stderr_output:
                    sub.status = "Runtime Error"
                    sub.error_message = "Segmentation fault (stack overflow or invalid memory access)."
                    db.session.commit()
                    return

                if docker_run_result.returncode != 0:
                    sub.status = "Runtime Error"
                    db.session.commit()
                    return

            except subprocess.TimeoutExpired:
                sub.status = "Time Limit Exceeded"
                sub.error_message = "Execution timed out."
                db.session.commit()
                return
            except Exception as e:
                sub.status = "Runtime Error"
                sub.error_message = str(e)
                db.session.commit()
                return

        # 针对 Python 代码
        elif language == 'python':
            source_path = code_path + ".py"
            with open(source_path, 'w', newline='\n') as f:
                f.write(sub.code)

            # 针对 Python 代码也进行简单的危险调用检测
            forbidden_keywords = ['os.system(', 'subprocess']
            if any(keyword.lower() in sub.code.lower() for keyword in forbidden_keywords):
                sub.status = "Rejected"
                sub.error_message = "Dangerous system calls detected in submission."
                db.session.commit()
                return

            docker_cmd = (
                f"python3 /sandbox/{os.path.basename(source_path)} "
                f"< /data/{input_filename} > /sandbox/{os.path.basename(output_path)}"
            )
            try:
                docker_run_result = subprocess.run(
                    ["docker", "run", "--rm", "--init"] + network_opts + run_limits + security_opts + volume_opts +
                    [docker_image, "bash", "-c", docker_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=prob.time_limit * 2
                )
                py_run_err = docker_run_result.stderr.decode()
                if len(py_run_err) > MAX_LOG_LENGTH:
                    py_run_err = py_run_err[:MAX_LOG_LENGTH] + "..."
                sub.error_message = py_run_err

                if docker_run_result.returncode != 0:
                    sub.status = "Runtime Error"
                    db.session.commit()
                    return
            except subprocess.TimeoutExpired:
                sub.status = "Time Limit Exceeded"
                sub.error_message = "Execution timed out."
                db.session.commit()
                return
            except Exception as e:
                sub.status = "Runtime Error"
                sub.error_message = str(e)
                db.session.commit()
                return

        else:
            sub.status = "Unsupported Language"
            db.session.commit()
            return

        # 对比输出结果
        try:
            with open(output_path, 'r') as user_out, open(prob.output_path, 'r') as std_out:
                user_output = user_out.read().strip()
                std_output = std_out.read().strip()

            if user_output == std_output:
                sub.status = "Accepted"
                sub.error_message = None
            else:
                sub.status = "Wrong Answer"
                sub.error_message = f"Your Output:\n{user_output}\n\nExpected Output:\n{std_output}"

            db.session.commit()
        except Exception as e:
            sub.status = "Error Comparing Output"
            sub.error_message = str(e)
            db.session.commit()

        print(f"Submission #{submission_id} evaluated: {sub.status}")

        # 清理生成的临时文件
        try:
            for f in [source_path, output_path]:
                if f and os.path.exists(f):
                    os.remove(f)
            if language in ['cpp', 'c++'] and os.path.exists(exe_path):
                os.remove(exe_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
