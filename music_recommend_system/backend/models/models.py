from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

# 用户模型
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    preferred_style = db.Column(db.String(100), default="")
    register_time = db.Column(db.DateTime, default=datetime.now)

    # 密码加密
    def set_password(self, password):
        self.password = hashlib.sha256(password.encode()).hexdigest()
    
    # 验证密码
    def check_password(self, password):
        return self.password == hashlib.sha256(password.encode()).hexdigest()

# 歌曲模型
class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    song_id = db.Column(db.String(20), unique=True, nullable=False)
    song_name = db.Column(db.String(100), nullable=False)
    singer = db.Column(db.String(50), nullable=False)
    album = db.Column(db.String(100), default="未知专辑")
    style = db.Column(db.String(50), nullable=False)
    play_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)

# 用户行为模型
class UserBehavior(db.Model):
    __tablename__ = 'user_behaviors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.String(20), nullable=False)
    behavior_type = db.Column(db.String(20), nullable=False)  # play/collect/comment
    behavior_time = db.Column(db.DateTime, default=datetime.now)
    play_duration = db.Column(db.Integer, default=0)  # 播放时长（秒）
    comment_content = db.Column(db.Text, default="")