import pandas as pd
from models.models import Song, db
import os

# 初始化歌曲数据（从CSV导入）
def init_song_data(csv_path):
    # 清空现有数据
    Song.query.delete()
    db.session.commit()
    
    # 读取CSV
    df = pd.read_csv(csv_path)
    # 导入数据库
    for _, row in df.iterrows():
        song = Song(
            song_id=row['song_id'],
            song_name=row['song_name'],
            singer=row['singer'],
            album=row['album'],
            style=row['style'].strip(),
            play_count=row['play_count'],
            rating=row['rating']
        )
        db.session.add(song)
    db.session.commit()
    print(f"初始化完成，共导入 {len(df)} 首歌曲")

# 检查音乐文件是否存在

def check_music_file_exists(song_name, singer):
    # 音乐文件存储路径
    music_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "音乐")
    
    # 获取所有音乐文件
    if not os.path.exists(music_dir):
        return False, None
    
    music_files = os.listdir(music_dir)
    
    # 构建可能的文件名格式（考虑不同的格式）
    possible_formats = [
        f"{song_name}.mp3",
        f"{singer} - {song_name}.mp3",
        f"{singer}-{song_name}.mp3",
        f"{song_name} - {singer}.mp3",
        f"{song_name}-{singer}.mp3"
    ]
    
    # 检查文件是否存在
    for fmt in possible_formats:
        file_path = os.path.join(music_dir, fmt)
        if os.path.exists(file_path):
            # 返回Flask服务的音乐文件路径
            return True, f"http://localhost:5000/music/{fmt}"
    
    # 尝试更宽松的匹配（不考虑歌手）
    for file in music_files:
        if song_name in file and file.endswith('.mp3'):
            return True, f"http://localhost:5000/music/{file}"
    
    return False, None

# 获取热门歌曲（按播放量排序，有音乐文件的排在前面）
def get_hot_songs(top_n=20):
    # 先获取所有歌曲
    all_songs = Song.query.all()
    
    # 为每个歌曲添加音乐文件信息
    songs_with_music = []
    for song in all_songs:
        has_music, music_path = check_music_file_exists(song.song_name, song.singer)
        songs_with_music.append({
            "song": song,
            "has_music": has_music,
            "music_path": music_path
        })
    
    # 排序：有音乐文件的排在前面，然后按播放量排序
    songs_with_music.sort(key=lambda x: (not x["has_music"], -x["song"].play_count))
    
    # 取前top_n首
    top_songs = songs_with_music[:top_n]
    
    return [
        {
            "song_id": song["song"].song_id,
            "song_name": song["song"].song_name,
            "singer": song["song"].singer,
            "album": song["song"].album,
            "style": song["song"].style,
            "play_count": song["song"].play_count,
            "rating": song["song"].rating,
            "has_music_file": song["has_music"],
            "music_file_path": song["music_path"]
        }
        for song in top_songs
    ]

# 获取歌曲详情
def get_song_detail(song_id):
    song = Song.query.filter_by(song_id=song_id).first()
    if not song:
        return None
    
    # 检查音乐文件是否存在
    has_music, music_path = check_music_file_exists(song.song_name, song.singer)
    
    return {
        "song_id": song.song_id,
        "song_name": song.song_name,
        "singer": song.singer,
        "album": song.album,
        "style": song.style,
        "play_count": song.play_count,
        "rating": song.rating,
        "has_music_file": has_music,
        "music_file_path": music_path
    }