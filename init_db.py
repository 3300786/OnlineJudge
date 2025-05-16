from app import app
from models import User, Problem, Submission
from extensions import db
from werkzeug.security import generate_password_hash
import os


# 示例：生成一个简单的输入输出文件
def create_sample_files(problem_id):
    input_file = f"data/{problem_id}.in"
    output_file = f"data/{problem_id}.out"
    os.makedirs('data', exist_ok=True)  # 确保目录存在
    with open(input_file, 'w') as f:
        f.write("1 2")  # 示例输入：1 + 2

    with open(output_file, 'w') as f:
        f.write("3")  # 示例输出：1 + 2 = 3


with app.app_context():
    db.drop_all()  # 清除旧表
    db.create_all()  # 创建新表
    print("Tables created.")

    # 创建样本问题
    p1 = Problem(
        title="A + B Problem",
        description="Given two integers A and B, output their sum.",
        input_path="data/1.in",
        output_path="data/1.out",
        time_limit=1,
        memory_limit=64
    )
    db.session.add(p1)
    create_sample_files(1)
    db.session.commit()

    # 检查是否有管理员用户，如果没有，则创建一个
    admin_exists = User.query.filter_by(role='admin').first()  # 查找是否已经有管理员
    if not admin_exists:
        admin_password_hash = generate_password_hash("123456")  # 对密码进行哈希处理
        admin_user = User(
            username="admin",  # 管理员用户名
            email="admin@example.com",  # 管理员邮箱
            password_hash=admin_password_hash,  # 使用哈希后的密码
            role="admin"  # 设置角色为管理员
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
