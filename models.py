# models.py
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
    role = db.Column(db.String(50), nullable=False, default='user')  # 新增role字段，默认是普通用户
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    blog = db.Column(db.String(150), unique=True, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Problem(db.Model):
    __tablename__ = 'problems'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    input_path = db.Column(db.String(128), nullable=False)
    output_path = db.Column(db.String(128), nullable=False)
    time_limit = db.Column(db.Integer, default=2)  # 秒
    memory_limit = db.Column(db.Integer, default=64)  # MB
    tags = db.relationship('Tag', secondary='problem_tags', back_populates='problems')
    difficulty = db.Column(db.String(32), nullable=False, default='easy')  # easy, medium, hard

    def __repr__(self):
        return f"<Problem {self.title}>"


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'))
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), default='C++')
    status = db.Column(db.String(20), default='Pending')  # Pending, Accepted, WA, CE, TLE
    submit_time = db.Column(db.DateTime, default=db.func.now())
    error_message = db.Column(db.Text)  # 存储运行或编译时的错误输出
    user = db.relationship('User', backref=db.backref('submissions', lazy=True))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=True)  # 修正为 'contests.id'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 添加这个字段

    def __repr__(self):
        return f'<Submission {self.id}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    problems = db.relationship('Problem', secondary='problem_tags', back_populates='tags')

    def __repr__(self):
        return f"<Tag {self.name}>"


class ProblemTag(db.Model):
    __tablename__ = 'problem_tags'
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)


class Contest(db.Model):
    __tablename__ = 'contests'  # 修正表名为 'contests'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    problems = db.relationship('Problem', secondary='contest_problems', backref='contests')
    registrations = db.relationship('ContestRegistration', backref='contest', cascade='all, delete-orphan')


contest_problems = db.Table('contest_problems',
                            db.Column('contest_id', db.Integer, db.ForeignKey('contests.id')),  # 修正为 'contests.id'
                            db.Column('problem_id', db.Integer, db.ForeignKey('problems.id'))
                            )


class ContestRegistration(db.Model):
    __tablename__ = 'contest_registrations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'))  # 修正为 'contests.id'
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='contest_registrations')


class ContestRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    contest_id = db.Column(db.Integer, db.ForeignKey('contests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)

    submit_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 正确建立关系
    contest = db.relationship('Contest', backref='rankings')
    user = db.relationship('User')
    problem = db.relationship('Problem')

