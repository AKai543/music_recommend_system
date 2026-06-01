from flask import Flask, request, jsonify
from flask_cors import CORS
from models.models import db, User, UserBehavior, Song
from utils.data_utils import init_song_data, get_hot_songs, get_song_detail
from utils.recommend import hybrid_recommend
import os

# 初始化Flask应用
app = Flask(__name__)
# 配置数据库（SQLite，无需额外安装）
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'music_recommend.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'music_recommend_2025'
# 设置UTF-8编码
app.config['JSON_AS_ASCII'] = False

# 跨域支持
CORS(app)

# 添加音乐文件夹的静态文件服务
music_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '音乐')
app.static_folder = 'static'
# 添加音乐文件夹作为静态资源目录
@app.route('/music/<path:filename>')
def serve_music(filename):
    from flask import send_from_directory
    return send_from_directory(music_dir, filename)

# 初始化数据库
db.init_app(app)

# 创建数据库表
with app.app_context():
    db.create_all()
    # 初始化歌曲数据（每次运行都重新加载）
    import os
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'music_data.csv')
    init_song_data(data_path)

# ------------------- 接口 -------------------
# 1. 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    preferred_style = data.get('preferred_style', "")
    
    # 校验参数
    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({"code": 400, "message": "用户名已存在"}), 400
    
    # 创建用户
    user = User(username=username)
    user.set_password(password)
    user.preferred_style = preferred_style
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "code": 201,
        "message": "注册成功",
        "data": {"user_id": user.id, "username": user.username}
    }), 201

# 2. 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # 校验参数
    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400
    
    # 验证用户
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"code": 401, "message": "用户名或密码错误"}), 401
    
    return jsonify({
        "code": 200,
        "message": "登录成功",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "preferred_style": user.preferred_style
        }
    }), 200

# 3. 获取热门歌曲
@app.route('/api/hot_songs', methods=['GET'])
def hot_songs():
    top_n = request.args.get('top_n', 20, type=int)
    hot_songs_list = get_hot_songs(top_n)
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": {"hot_songs": hot_songs_list}
    }), 200

# 4. 获取个性化推荐
@app.route('/api/personal_recommend', methods=['GET'])
def personal_recommend():
    user_id = request.args.get('user_id', type=int)
    top_n = request.args.get('top_n', 10, type=int)
    
    if not user_id:
        return jsonify({"code": 400, "message": "user_id不能为空"}), 400
    
    # 生成推荐
    recommend_list = hybrid_recommend(user_id, top_n)
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": {"recommend_list": recommend_list}
    }), 200

# 5. 上报用户行为
@app.route('/api/behavior', methods=['POST'])
def report_behavior():
    data = request.json
    user_id = data.get('user_id')
    song_id = data.get('song_id')
    behavior_type = data.get('behavior_type')
    play_duration = data.get('play_duration', 0)
    comment_content = data.get('comment_content', "")
    
    # 校验参数
    if not user_id or not song_id or not behavior_type:
        return jsonify({"code": 400, "message": "user_id、song_id、behavior_type不能为空"}), 400
    
    # 检查行为类型
    if behavior_type not in ['play', 'collect', 'comment']:
        return jsonify({"code": 400, "message": "behavior_type只能是play/collect/comment"}), 400
    
    # 创建行为记录
    behavior = UserBehavior(
        user_id=user_id,
        song_id=song_id,
        behavior_type=behavior_type,
        play_duration=play_duration,
        comment_content=comment_content
    )
    db.session.add(behavior)
    db.session.commit()
    
    # 更新歌曲播放量（如果是播放行为）
    if behavior_type == 'play':
        song = Song.query.filter_by(song_id=song_id).first()
        if song:
            song.play_count += 1
            db.session.commit()
    
    return jsonify({
        "code": 200,
        "message": "上报成功",
        "data": {"behavior_id": behavior.id}
    }), 200

# 6. 获取歌曲详情
@app.route('/api/song_detail', methods=['GET'])
def song_detail():
    song_id = request.args.get('song_id')
    if not song_id:
        return jsonify({"code": 400, "message": "song_id不能为空"}), 400
    
    detail = get_song_detail(song_id)
    if not detail:
        return jsonify({"code": 404, "message": "歌曲不存在"}), 404
    
    return jsonify({
        "code": 200,
        "message": "查询成功",
        "data": detail
    }), 200

# 7. 更新用户偏好
@app.route('/api/user/preferences', methods=['PUT'])
def update_preferences():
    data = request.json
    user_id = data.get('user_id')
    preferred_style = data.get('preferred_style', "")
    
    if not user_id:
        return jsonify({"code": 400, "message": "user_id不能为空"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "message": "用户不存在"}), 404
    
    user.preferred_style = preferred_style
    db.session.commit()
    
    return jsonify({
        "code": 200,
        "message": "更新成功",
        "data": {
            "user_id": user.id,
            "username": user.username,
            "preferred_style": user.preferred_style
        }
    }), 200

# ------------------- 启动服务 -------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)