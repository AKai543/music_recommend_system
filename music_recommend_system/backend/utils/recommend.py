import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from models.models import UserBehavior, Song, User
from .data_utils import get_song_detail

# 构建用户-歌曲评分矩阵
def build_user_song_matrix():
    # 获取所有用户行为
    behaviors = UserBehavior.query.all()
    if not behaviors:
        return None, None
    
    # 转换为DataFrame
    behavior_data = [
        {
            "user_id": b.user_id,
            "song_id": b.song_id,
            "behavior_type": b.behavior_type,
            "play_duration": b.play_duration
        }
        for b in behaviors
    ]
    df = pd.DataFrame(behavior_data)
    
    # 生成评分：播放≥30秒记3分，收藏记5分，默认1分
    def get_score(row):
        if row['behavior_type'] == 'collect':
            return 5
        elif row['behavior_type'] == 'play' and row['play_duration'] >= 30:
            return 3
        else:
            return 1
    
    df['score'] = df.apply(get_score, axis=1)
    
    # 构建用户-歌曲矩阵
    user_song_matrix = df.pivot_table(
        index='user_id',
        columns='song_id',
        values='score',
        fill_value=0
    )
    return user_song_matrix, df

# 基于物品的协同过滤推荐
def item_based_recommend(user_id, top_n=10):
    user_song_matrix, df = build_user_song_matrix()
    if user_song_matrix is None or user_id not in user_song_matrix.index:
        # 无行为数据，返回热门歌曲
        from .data_utils import get_hot_songs
        return get_hot_songs(top_n)
    
    # 1. 获取用户评分过的歌曲
    user_scores = user_song_matrix.loc[user_id]
    rated_songs = user_scores[user_scores > 0].index.tolist()
    if not rated_songs:
        from .data_utils import get_hot_songs
        return get_hot_songs(top_n)
    
    # 2. 构建歌曲-用户矩阵（用于计算歌曲相似度）
    song_user_matrix = user_song_matrix.T
    
    # 3. 计算歌曲相似度（余弦相似度）
    song_similarity = cosine_similarity(song_user_matrix)
    song_similarity_df = pd.DataFrame(
        song_similarity,
        index=song_user_matrix.index,
        columns=song_user_matrix.index
    )
    
    # 4. 生成推荐
    song_scores = {}
    for song in rated_songs:
        # 跳过相似度为1的自身
        similar_songs = song_similarity_df[song].drop(song)
        # 筛选用户未评分的歌曲
        similar_songs = similar_songs[~similar_songs.index.isin(user_song_matrix.columns[user_song_matrix.loc[user_id] > 0])]
        # 加权评分（相似度 * 用户对该歌曲的评分）
        for sim_song, sim_score in similar_songs.items():
            if sim_song not in song_scores:
                song_scores[sim_song] = 0
            song_scores[sim_song] += sim_score * user_scores[song]
    
    # 排序并取前N
    sorted_songs = sorted(song_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    # 转换为歌曲详情
    recommend_list = []
    for song_id, _ in sorted_songs:
        song_detail = get_song_detail(song_id)
        if song_detail:
            recommend_list.append(song_detail)
    return recommend_list

# 基于内容的推荐（风格匹配）
def content_based_recommend(user_id, top_n=10):
    from .data_utils import check_music_file_exists
    
    # 获取用户偏好风格
    user = User.query.get(user_id)
    if not user or not user.preferred_style:
        # 无偏好，返回热门歌曲
        from .data_utils import get_hot_songs
        return get_hot_songs(top_n)
    
    # 按风格筛选歌曲
    preferred_styles = user.preferred_style.split(',')
    recommended_songs = []
    selected_song_ids = set()
    
    # 确保每个选中的曲风至少推荐一首歌曲
    for style in preferred_styles:
        # 为每个风格选择最高评分的歌曲
        style_song = Song.query.filter_by(style=style).order_by(Song.rating.desc()).first()
        if style_song and style_song.song_id not in selected_song_ids:
            recommended_songs.append(style_song)
            selected_song_ids.add(style_song.song_id)
    
    # 如果已经满足推荐数量要求，直接返回
    if len(recommended_songs) >= top_n:
        # 添加音乐文件信息
        songs_with_music = []
        for song in recommended_songs[:top_n]:
            has_music, music_path = check_music_file_exists(song.song_name, song.singer)
            songs_with_music.append({
                "song_id": song.song_id,
                "song_name": song.song_name,
                "singer": song.singer,
                "album": song.album,
                "style": song.style,
                "play_count": song.play_count,
                "rating": song.rating,
                "has_music_file": has_music,
                "music_file_path": music_path
            })
        
        # 排序：有音乐文件的排在前面，然后按评分排序
        songs_with_music.sort(key=lambda x: (not x["has_music_file"], -x["rating"]))
        return songs_with_music
    
    # 否则，从所有符合条件的歌曲中选择剩余的高评分歌曲（去重）
    remaining_slots = top_n - len(recommended_songs)
    all_qualified_songs = Song.query.filter(
        Song.style.in_(preferred_styles),
        ~Song.song_id.in_(selected_song_ids)
    ).order_by(Song.rating.desc()).limit(remaining_slots).all()
    
    # 合并结果
    recommended_songs.extend(all_qualified_songs)
    
    # 添加音乐文件信息
    songs_with_music = []
    for song in recommended_songs:
        has_music, music_path = check_music_file_exists(song.song_name, song.singer)
        songs_with_music.append({
            "song_id": song.song_id,
            "song_name": song.song_name,
            "singer": song.singer,
            "album": song.album,
            "style": song.style,
            "play_count": song.play_count,
            "rating": song.rating,
            "has_music_file": has_music,
            "music_file_path": music_path
        })
    
    # 排序：有音乐文件的排在前面，然后按评分排序
    songs_with_music.sort(key=lambda x: (not x["has_music_file"], -x["rating"]))
    return songs_with_music

# 融合推荐（物品协同+内容推荐）
def hybrid_recommend(user_id, top_n=10):
    from .data_utils import get_hot_songs
    
    # 检查用户是否有设置曲风偏好
    user = User.query.get(user_id)
    if user and user.preferred_style:
        # 获取用户偏好曲风
        preferred_styles = user.preferred_style.split(',')
        
        # 有曲风偏好，优先使用内容推荐（权重0.7），物品协同作为辅助（权重0.3）
        content_rec = content_based_recommend(user_id, top_n * 2)
        item_rec = item_based_recommend(user_id, top_n * 2)
        
        # 如果内容推荐有结果，优先使用内容推荐为主的融合
        if content_rec:
            # 过滤物品协同推荐结果，只保留用户偏好曲风的歌曲
            filtered_item_rec = [song for song in item_rec if song['style'] in preferred_styles]
            
            # 去重并加权融合（内容推荐权重0.7，物品协同权重0.3）
            song_dict = {}
            # 内容推荐结果（优先）
            for i, song in enumerate(content_rec):
                score = (top_n * 2 - i) * 0.7  # 排名越前得分越高
                song_dict[song['song_id']] = {"song": song, "score": score}
            # 物品协同结果（辅助）
            for i, song in enumerate(filtered_item_rec):
                score = (top_n * 2 - i) * 0.3
                if song['song_id'] in song_dict:
                    song_dict[song['song_id']]['score'] += score
                else:
                    song_dict[song['song_id']] = {"song": song, "score": score}
            
            # 排序取前N
            sorted_songs = sorted(song_dict.values(), key=lambda x: x['score'], reverse=True)[:top_n]
            
            # 进一步排序：有音乐文件的排在前面
            result = [item['song'] for item in sorted_songs]
            result.sort(key=lambda x: (not x["has_music_file"], -x["score"] if "score" in x else -x["rating"]))
            return result
    
    # 没有曲风偏好，返回热门歌曲
    return get_hot_songs(top_n)