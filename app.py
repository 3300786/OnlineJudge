# app.py
from flask import Flask, render_template, jsonify
from config import Config
from functools import wraps
from datetime import datetime
from flask import request, redirect, url_for, session, flash
from models import User, Problem, Submission, Tag, Contest, ContestRanking, ContestRegistration, Announcement, BlogPost
from extensions import db, migrate
from threading import Thread
import os
from math import ceil
from sqlalchemy import func, desc, asc, text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate.init_app(app, db)


# db = SQLAlchemy(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role  # 设置角色
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))


# app.py
from flask import request, render_template
from models import Problem, Tag


# routes.py
@app.route('/problem_list')
def problem_list():
    search_input = request.args.get('search_input', '')  # 获取搜索框的输入
    tag_filter = request.args.get('tag_filter')
    difficulty_filter = request.args.get('difficulty_filter')

    query = Problem.query
    # 按照标题过滤
    if search_input:
        query = query.filter(Problem.title.like(f'%{search_input}%'))

    # 筛选标签
    if tag_filter:
        query = query.filter(Problem.tags.any(name=tag_filter))

    # 筛选难度
    if difficulty_filter:
        query = query.filter(Problem.difficulty == difficulty_filter)

    problems = query.all()
    tags = Tag.query.all()  # 获取所有标签用于筛选
    # 统计每道题的通过数量
    for problem in problems:
        problem.accepted_count = Submission.query.filter_by(
            problem_id=problem.id,
            status='Accepted'  # 或你数据库中的 AC 状态标识，比如 "AC"
        ).distinct(Submission.user_id).count()
    return render_template('problem_list.html', problems=problems, tags=tags, tag_filter=tag_filter,
                           difficulty_filter=difficulty_filter, search_input=search_input)


@app.route('/problem/<int:problem_id>')
def problem_detail(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    contest_id = request.args.get('contest_id', type=int)  # 👈 从 URL 拿到 contest_id
    return render_template('problem_detail.html', problem=problem, contest_id=contest_id)


@app.route('/submit/<int:problem_id>', methods=['GET', 'POST'])
def submit(problem_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('login'))

    problem = Problem.query.get_or_404(problem_id)
    contest_id = request.args.get('contest_id', type=int) or request.form.get('contest_id', type=int)

    if request.method == 'POST':
        code = request.form['code']
        language = request.form['language']
        new_submission = Submission(
            user_id=session['user_id'],
            problem_id=problem.id,
            code=code,
            language=language,
            status='Pending',
            contest_id=contest_id
        )
        db.session.add(new_submission)
        db.session.commit()

        # 启动评测线程
        def process_submission(submission_id):
            from evaluate import evaluate_submission
            evaluate_submission(submission_id)

            from models import Submission, ContestRanking, db
            submission = Submission.query.get(submission_id)
            if submission and submission.contest_id and submission.status == 'Accepted':
                exists = ContestRanking.query.filter_by(
                    contest_id=submission.contest_id,
                    user_id=submission.user_id,
                    problem_id=submission.problem_id
                ).first()
                if not exists:
                    db.session.add(ContestRanking(
                        contest_id=submission.contest_id,
                        user_id=submission.user_id,
                        problem_id=submission.problem_id,
                        submit_time=submission.submit_time
                    ))
                    db.session.commit()

        Thread(target=process_submission, args=(new_submission.id,)).start()
        return redirect(url_for('submission_status', submission_id=new_submission.id))

    return render_template('submit.html', problem=problem, contest_id=contest_id)


@app.route('/submission/<int:submission_id>')
def submission_status(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return render_template('submission_status.html', submission=submission)


@app.route('/create_problem', methods=['GET', 'POST'])
def create_problem():
    if request.method == 'POST':
        title = request.form['title']
        # ...处理其他字段
        tag_string = request.form.get('tags', '')  # 获取标签字符串
        tag_list = [t.strip() for t in tag_string.split(',') if t.strip()]  # 拆分并清洗

        # 处理标签创建与关联
        tags = []
        for tag_name in tag_list:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags.append(tag)
        description = request.form['description']
        time_limit = request.form['time_limit']
        memory_limit = request.form['memory_limit']

        input_file = request.files['input_file']
        output_file = request.files['output_file']
        difficulty = request.form['difficulty']

        # 保存输入输出文件
        input_filename = f"input_{title}.txt"
        output_filename = f"output_{title}.txt"
        input_file.save(os.path.join('data', input_filename))
        output_file.save(os.path.join('data', output_filename))

        # 保存题目信息到数据库
        new_problem = Problem(
            title=title,
            tags=tags,
            description=description,
            input_path=os.path.join('data', input_filename),
            output_path=os.path.join('data', output_filename),
            time_limit=time_limit,
            memory_limit=memory_limit,
            difficulty=difficulty
        )

        db.session.add(new_problem)
        db.session.commit()

        return redirect(url_for('index'))  # 可以跳转到题目列表页

    return render_template('create_problem.html')


@app.route('/my_submissions')
def user_submissions():
    if 'user_id' not in session:
        flash('Please log in to view submissions.')
        return redirect(url_for('login'))

    submissions = Submission.query.filter_by(user_id=session['user_id']).order_by(Submission.submit_time.desc()).all()
    return render_template('my_submissions.html', submissions=submissions)


@app.route('/user_history/<int:user_id>')
def user_history(user_id):
    user = User.query.get_or_404(user_id)
    submissions = Submission.query.filter_by(user_id=user.id).all()

    total_submissions = len(submissions)
    accepted_submissions = sum(1 for sub in submissions if sub.status == "Accepted")

    return render_template('user_history.html', user=user, submissions=submissions,
                           total_submissions=total_submissions,
                           accepted_submissions=accepted_submissions)


@app.route('/leaderboard')
def leaderboard():
    users = User.query.all()
    user_stats = []

    for user in users:
        submissions = Submission.query.filter_by(user_id=user.id, status="Accepted").all()
        # 使用 set 保证每道题只计一次
        solved_problems = set(sub.problem_id for sub in submissions)
        total_ac = len(solved_problems)
        user_stats.append((user, total_ac))

    # 排序：通过题数多的在前
    user_stats.sort(key=lambda x: x[1], reverse=True)

    return render_template('leaderboard.html', user_stats=user_stats)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # 检查用户是否登录
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # 获取用户输入的信息
        new_username = request.form['username']
        new_email = request.form['email']
        new_blog = request.form['blog']
        # 更新用户信息
        user.username = new_username
        user.email = new_email
        user.blog = new_blog
        # 保存修改
        db.session.commit()

        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_history', user_id=user.id))

    return render_template('edit_profile.html', user=user)


# 创建一个装饰器，检查用户角色
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('index'))  # 如果不是管理员，重定向回主页
        return f(*args, **kwargs)

    return decorated_function


# 在需要管理员权限的路由中使用装饰器
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()  # 获取所有用户
    contests = Contest.query.all()
    problems = Problem.query.all()
    print(users)
    print(contests)
    print(problems)
    return render_template('admin_dashboard.html', users=users, contests=contests, problems=problems)


@app.route('/admin/contest/delete/<int:contest_id>', methods=['POST'])
@admin_required
def admin_delete_contest(contest_id):
    contest = Contest.query.get_or_404(contest_id)
    db.session.delete(contest)
    db.session.commit()
    flash("Contest deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/problem/delete/<int:problem_id>', methods=['POST'])
@admin_required
def admin_delete_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    db.session.delete(problem)
    db.session.commit()
    flash("Problem deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Cannot delete an admin user.", "error")
        return redirect(url_for('admin_dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin_dashboard'))


# 修改用户角色的路由
@app.route('/admin/update_role/<int:user_id>', methods=['POST'])
@admin_required
def update_role(user_id):
    user = User.query.get(user_id)
    if user:
        new_role = request.form['role']
        user.role = new_role  # 修改角色
        db.session.commit()  # 提交更改
    return redirect(url_for('admin_dashboard'))


@app.route('/submission_status_json/<int:submission_id>')
def submission_status_json(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    # 返回 JSON 数据，包括状态和错误信息（如果有的话）
    return jsonify({
        'status': submission.status,
        'error_message': submission.error_message or "",
        'submit_time': submission.submit_time.strftime("%Y-%m-%d %H:%M"),
        'language': submission.language,
        'problem_id': submission.problem_id
    })


@app.route('/tags', methods=['GET'])
def get_tags():
    tags = Tag.query.all()
    return jsonify([tag.name for tag in tags])


@app.route('/problem/<int:problem_id>/tags', methods=['POST'])
def add_tags_to_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    tag_names = request.json.get('tags', [])

    # 查找现有标签
    tags = Tag.query.filter(Tag.name.in_(tag_names)).all()

    # 创建新标签（如果不存在的话）
    for tag_name in tag_names:
        if not any(tag.name == tag_name for tag in tags):
            tag = Tag(name=tag_name)
            db.session.add(tag)
            tags.append(tag)

    # 将标签关联到问题
    problem.tags.extend(tags)
    db.session.commit()

    return jsonify({'message': 'Tags added successfully.'})


@app.route('/create_contest', methods=['GET', 'POST'])
def create_contest():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        problem_ids = request.form.getlist('problem_ids')

        contest = Contest(title=title, description=description, start_time=start_time, end_time=end_time,
                          creator_id=session.get('user_id'))

        for pid in problem_ids:
            problem = Problem.query.get(int(pid))
            if problem:
                contest.problems.append(problem)

        db.session.add(contest)
        db.session.commit()

        flash("Contest created successfully!", "success")
        return redirect(url_for('contest_list'))

    problems = Problem.query.all()
    return render_template('create_contest.html', problems=problems)


@app.route('/contests')
def contest_list():
    # 获取 GET 参数
    status_filter = request.args.get('status_filter', '')
    search_input = request.args.get('search_input', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 20

    # 构建基础查询
    query = Contest.query

    # 关键字搜索
    if search_input:
        query = query.filter(Contest.title.ilike(f"%{search_input}%"))

    # 状态筛选
    now = datetime.utcnow()
    if status_filter == 'upcoming':
        query = query.filter(Contest.start_time > now)
    elif status_filter == 'running':
        query = query.filter(Contest.start_time <= now, Contest.end_time >= now)
    elif status_filter == 'ended':
        query = query.filter(Contest.end_time < now)

    # 分页处理
    total = query.count()
    contests = query.order_by(Contest.start_time.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()

    # 为每个 contest 添加 status 字段（传给前端使用）
    for contest in contests:
        if contest.start_time > now:
            contest.status = 'upcoming'
        elif contest.start_time <= now and contest.end_time >= now:
            contest.status = 'running'
        else:
            contest.status = 'ended'

    return render_template(
        'contest_list.html',
        contests=contests,
        status_filter=status_filter,
        search_input=search_input,
        page=page,
        total_pages=ceil(total / per_page)
    )


from models import Submission  # 确保导入了 Submission 模型


@app.route('/contest/<int:contest_id>', methods=['GET'])
def contest_detail(contest_id):
    if 'user_id' not in session:
        flash("Please log in to view contest details.")
        return redirect(url_for('login'))

    contest = Contest.query.get_or_404(contest_id)

    registered = ContestRegistration.query.filter_by(
        user_id=session['user_id'],
        contest_id=contest.id
    ).first()

    # 将 A, B, C 赋值给题目
    for idx, problem in enumerate(contest.problems):
        problem.letter = chr(idx + 65)

    # 查询当前用户在这场比赛中的所有提交
    submissions = Submission.query.filter_by(
        user_id=session['user_id'],
        contest_id=contest.id
    ).all()

    # 构建题目标记字典
    problem_status = {}  # key: problem_id, value: 'accepted' / 'wrong'

    for s in submissions:
        if s.problem_id not in problem_status:
            if s.status == 'Accepted':
                problem_status[s.problem_id] = 'accepted'
            else:
                problem_status[s.problem_id] = 'wrong'
        else:
            if problem_status[s.problem_id] != 'accepted' and s.status == 'Accepted':
                problem_status[s.problem_id] = 'accepted'  # 优先标记为正确
    print(problem_status)
    return render_template('contest_detail.html',
                           contest=contest,
                           registered=registered,
                           problem_status=problem_status)  # 把状态传给前端


@app.route('/contest/<int:contest_id>/ranking')
def contest_ranking(contest_id):
    contest = Contest.query.get_or_404(contest_id)

    # 获取所有报名用户
    registered_users = db.session.query(User).join(ContestRegistration).filter(
        ContestRegistration.contest_id == contest_id
    ).all()

    # 获取比赛题目
    contest_problems = contest.problems

    # 初始化排名数据结构
    rankings = []

    for user in registered_users:
        user_entry = {
            'user_id': user.username,
            'problems': {},
            'correct_count': 0,
            'total_penalty': 0
        }

        for problem in contest_problems:
            # 获取该用户该题目的所有提交记录（按时间排序）
            submissions = Submission.query.filter_by(
                user_id=user.id,
                problem_id=problem.id,
                contest_id=contest.id  # 关键！确保是比赛内提交
            ).order_by(Submission.submit_time).all()

            wrong_attempts = 0
            accepted_time = None

            for submission in submissions:
                if submission.status == 'Accepted':
                    accepted_time = (submission.submit_time - contest.start_time).total_seconds() // 60
                    break
                else:
                    wrong_attempts += 1

            if accepted_time is not None:
                user_entry['problems'][
                    problem.id] = f"+{wrong_attempts}({int(accepted_time)})" if wrong_attempts else f"+({int(accepted_time)})"
                user_entry['correct_count'] += 1
                user_entry['total_penalty'] += int(accepted_time + wrong_attempts * 20)
            elif wrong_attempts > 0:
                user_entry['problems'][problem.id] = f"-{wrong_attempts}"
            else:
                user_entry['problems'][problem.id] = ""

        rankings.append(user_entry)

    # 按照题数多 -> 罚时少 排序
    rankings.sort(key=lambda x: (-x['correct_count'], x['total_penalty']))

    # 添加名次
    for i, entry in enumerate(rankings, start=1):
        entry['rank'] = i
    page = request.args.get('page', 1, type=int)
    per_page = 20
    total_pages = ceil(len(rankings) / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    paged_rankings = rankings[start:end]

    return render_template(
        "contest_ranking.html",
        contest=contest,
        rankings=paged_rankings,
        problems=contest_problems,
        total_pages=total_pages,
        page=page
    )


@app.route('/register_contest/<int:contest_id>', methods=['POST'])
def register_contest(contest_id):
    if 'user_id' not in session:
        flash("Please log in to register for contests.")
        return redirect(url_for('login'))

    existing = ContestRegistration.query.filter_by(
        user_id=session['user_id'], contest_id=contest_id
    ).first()

    if existing:
        flash("You have already registered for this contest.")
    else:
        registration = ContestRegistration(
            user_id=session['user_id'],
            contest_id=contest_id,
            registered_at=datetime.utcnow()
        )
        db.session.add(registration)
        db.session.commit()
        flash("Successfully registered for the contest!")

    return redirect(url_for('contest_detail', contest_id=contest_id))


@app.route('/community/announcements')
def announcements():
    # 获取所有公告，按创建时间倒序排序
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()

    # 获取当前用户（如果已登录）
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    return render_template('announcements.html', announcements=announcements, user=user)


@app.route('/community/announcements/create', methods=['GET', 'POST'])
@admin_required
def create_announcement():
    if 'user_id' not in session or User.query.get(session['user_id']).role != 'admin':
        flash('You do not have permission to create an announcement.')
        return redirect(url_for('announcements'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        admin_id = session['user_id']

        new_announcement = Announcement(
            title=title,
            content=content,
            admin_id=admin_id
        )
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement created successfully.')
        return redirect(url_for('announcements'))

    return render_template('create_announcement.html')


@app.route('/community/blogs')
def blogs():
    # 获取所有博客文章
    blogs = BlogPost.query.all()
    return render_template('blogs.html', blogs=blogs)


@app.route('/community/blogs/<int:user_id>')
def user_blogs(user_id):
    # 获取特定用户的博客文章
    user = User.query.get_or_404(user_id)
    blogs = BlogPost.query.filter_by(user_id=user.id).all()
    return render_template('user_blogs.html', user=user, blogs=blogs)


@app.route('/community/blogs/create', methods=['GET', 'POST'])
def create_blog():
    if 'user_id' not in session:
        flash('Please log in to create a blog.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']

        new_blog_post = BlogPost(
            title=title,
            content=content,
            user_id=user_id
        )
        db.session.add(new_blog_post)
        db.session.commit()
        flash('Blog post created successfully.')
        return redirect(url_for('blogs'))

    return render_template('create_blog.html')


@app.route('/community/blog/<int:blog_id>')
def view_blog(blog_id):
    # 获取指定博客
    blog = BlogPost.query.get_or_404(blog_id)
    return render_template('view_blog.html', blog=blog)


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
