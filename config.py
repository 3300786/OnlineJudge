# config.py
class Config:
    SQLALCHEMY_DATABASE_URI = "mysql://aecreator:Yueguangwan520%40@localhost:3306/soj"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'  # 用于 session 管理
