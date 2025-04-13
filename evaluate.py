import subprocess
import os
import shutil
from extensions import db
from app import app
from models import Submission, Problem

WORKDIR = "sandbox"


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

        if not os.path.exists(WORKDIR):
            os.makedirs(WORKDIR)
        language = sub.language or 'cpp'  # 默认语言

        code_path = os.path.join(WORKDIR, f'main_{submission_id}')
        output_path = os.path.join(WORKDIR, f'out_{submission_id}.txt')

        print(sub.language)

        # Docker command setup
        docker_command = ""

        if language == 'cpp' or language == 'C++':

            source_path = code_path + '.cpp'
            exe_path = code_path + '.exe'

            # 保存代码文件
            with open(source_path, 'w', newline='\n') as f:
                f.write(sub.code)

            # 编译命令（在 Docker 中编译）
            docker_compile_command = (
                f"g++ /sandbox/{os.path.basename(source_path)} -o /sandbox/main "
                f"&& chmod +x /sandbox/main"
            )

            # 在 Docker 容器中进行编译
            try:
                docker_compile_result = subprocess.run(
                    [
                        "docker", "run", "--rm",
                        '--network', 'none',  # 禁用网络
                        "-v", f"{os.path.abspath(WORKDIR)}:/sandbox",  # Code files in /sandbox
                        "-v", f"{os.path.abspath(os.path.dirname(prob.input_path))}:/data",
                        # Input/output files in /data
                        "oj_sandbox",  # The Docker image
                        "bash", "-c", docker_compile_command  # Compile command
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=30  # 编译过程单独设置超时
                )

                # 保存 stderr 信息（无论是否错误）
                sub.error_message = docker_compile_result.stderr.decode()

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

            # 运行程序命令（只计算运行时间）
            docker_run_command = (
                f"/sandbox/main < /data/{os.path.basename(prob.input_path)} > /sandbox/{os.path.basename(output_path)}"
            )

            # 使用 Docker 执行程序
            try:
                docker_run_result = subprocess.run(
                    [
                        "docker", "run", "--rm",
                        '--network', 'none',  # 禁用网络
                        "-v", f"{os.path.abspath(WORKDIR)}:/sandbox",  # Code files in /sandbox
                        "-v", f"{os.path.abspath(os.path.dirname(prob.input_path))}:/data",
                        # Input/output files in /data
                        "oj_sandbox",  # The Docker image
                        "bash", "-c", docker_run_command  # Run command
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=prob.time_limit  # 只计算程序运行的时间
                )

                # 保存 stderr 信息（无论是否错误）
                sub.error_message = docker_run_result.stderr.decode()

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

        elif language == 'python' or language == 'Python':
            source_path = code_path + '.py'

            # 保存代码文件
            with open(source_path, 'w', newline='\n') as f:
                f.write(sub.code)

            # Python 运行命令
            docker_command = (
                f"python3 /sandbox/{os.path.basename(source_path)} < /data/{os.path.basename(prob.input_path)} > "
                f"/sandbox/{os.path.basename(output_path)}"
            )

        else:
            sub.status = "Unsupported Language"
            db.session.commit()
            return

        # 调试打印 Docker 命令
        print(f"Docker command: {docker_command}")

        # 使用 Docker 执行程序
        try:
            # 运行 Docker 命令
            docker_run_result = subprocess.run(
                [
                    "docker", "run", "--rm",
                    '--network', 'none',  # 禁用网络
                    "-v", f"{os.path.abspath(WORKDIR)}:/sandbox",  # Code files in /sandbox
                    "-v", f"{os.path.abspath(os.path.dirname(prob.input_path))}:/data",  # Input/output files in /data
                    "oj_sandbox",  # The Docker image
                    "bash", "-c", docker_command  # Command to run
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=prob.time_limit
            )

            # 保存 stderr 信息（无论是否错误）
            sub.error_message = docker_run_result.stderr.decode()

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

        # 对比输出
        with open(output_path, 'r') as user_out, open(prob.output_path, 'r') as std_out:
            user_output = user_out.read().strip()
            std_output = std_out.read().strip()

            if user_output == std_output:
                sub.status = "Accepted"
                sub.error_message = None  # 清空错误信息
            else:
                sub.status = "Wrong Answer"
                sub.error_message = f"Your Output:\n{user_output}\n\nExpected Output:\n{std_output}"

        db.session.commit()
        print(f"Submission #{submission_id} evaluated: {sub.status}")

        # 清理文件
        try:
            os.remove(source_path)
            os.remove(output_path)
            if language == 'cpp' and os.path.exists(exe_path):
                os.remove(exe_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
