# config.py
class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:yueguangwan520@localhost/SOJ'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'  # 用于 session 管理
