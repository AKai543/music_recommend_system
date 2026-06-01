# 检查数据库中各曲风的歌曲数量
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.models import Song, db
from app import app

with app.app_context():
    # 获取总歌曲数
    total_songs = Song.query.count()
    print(f'总歌曲数: {total_songs}')
    
    # 获取所有曲风
    songs = Song.query.all()
    styles = set(s.style for s in songs)
    print(f'所有曲风: {styles}')
    
    # 统计每个曲风的歌曲数量
    for style in sorted(styles):
        count = Song.query.filter_by(style=style).count()
        print(f'{style} 曲风歌曲数: {count}')
        
    # 显示部分歌曲的风格信息（用于调试）
    print('\n示例歌曲风格信息:')
    sample_songs = Song.query.limit(5).all()
    for song in sample_songs:
        print(f'歌曲: {song.song_name}, 歌手: {song.singer}, 风格: {song.style}')