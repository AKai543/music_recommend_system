// API基础URL
const API_BASE_URL = 'http://localhost:5000/api';

// 工具函数：获取存储的用户信息
function getUserInfo() {
    return JSON.parse(localStorage.getItem('userInfo'));
}

// 工具函数：存储用户信息
function setUserInfo(userInfo) {
    localStorage.setItem('userInfo', JSON.stringify(userInfo));
}

// 工具函数：清除用户信息
function clearUserInfo() {
    localStorage.removeItem('userInfo');
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 根据当前页面执行不同的初始化
    const currentPage = window.location.pathname.split('/').pop();
    
    if (currentPage === 'login.html') {
        initLogin();
    } else if (currentPage === 'register.html') {
        initRegister();
    } else if (currentPage === 'index.html') {
        initIndex();
    }
});

// 登录页面初始化
function initLogin() {
    const loginForm = document.getElementById('loginForm');
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // 发送登录请求
        fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                // 登录成功，存储用户信息并跳转到首页
                setUserInfo(data.data);
                window.location.href = 'index.html';
            } else {
                // 登录失败，显示错误信息
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('登录失败:', error);
            alert('登录失败，请检查网络连接');
        });
    });
}

// 注册页面初始化
function initRegister() {
    const registerForm = document.getElementById('registerForm');
    
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const preferredStyle = document.getElementById('preferredStyle').value;
        
        // 发送注册请求
        fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password, preferred_style: preferredStyle })
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 201) {
                // 注册成功，跳转到登录页面
                alert('注册成功，请登录');
                window.location.href = 'login.html';
            } else {
                // 注册失败，显示错误信息
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('注册失败:', error);
            alert('注册失败，请检查网络连接');
        });
    });
}

// 首页初始化
function initIndex() {
    const userInfo = getUserInfo();
    
    // 检查用户是否登录
    if (!userInfo) {
        window.location.href = 'login.html';
        return;
    }
    
    // 显示用户名
    document.getElementById('username').textContent = userInfo.username;
    
    // 退出登录事件
    document.getElementById('logoutBtn').addEventListener('click', function() {
        clearUserInfo();
        window.location.href = 'login.html';
    });
    
    // 初始化曲风选择按钮
    const styleButtons = document.querySelectorAll('.style-btn');
    const selectedStyles = new Set();
    const updateStyleBtn = document.getElementById('updateStyleBtn');
    
    // 如果有用户偏好，显示在按钮上
    if (userInfo.preferred_style) {
        const userStyles = userInfo.preferred_style.split(',');
        userStyles.forEach(style => {
            selectedStyles.add(style);
            // 找到对应的按钮并添加选中状态
            const button = Array.from(styleButtons).find(btn => btn.getAttribute('data-style') === style);
            if (button) {
                button.classList.add('selected');
            }
        });
    }
    
    // 按钮点击事件：切换选中状态
    styleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const style = this.getAttribute('data-style');
            if (selectedStyles.has(style)) {
                selectedStyles.delete(style);
                this.classList.remove('selected');
            } else {
                selectedStyles.add(style);
                this.classList.add('selected');
            }
        });
    });
    
    // 更新偏好按钮事件：提交选中的曲风
    updateStyleBtn.addEventListener('click', function() {
        const preferredStyle = Array.from(selectedStyles).join(',');
        updateUserPreferences(userInfo.user_id, preferredStyle);
    });
    
    // 获取推荐歌曲
    getRecommendSongs(userInfo.user_id);
    
    // 获取热门歌曲
    getHotSongs();
}

// 更新用户偏好
function updateUserPreferences(userId, preferredStyle) {
    const messageDiv = document.getElementById('styleMessage');
    
    fetch(`${API_BASE_URL}/user/preferences`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId, preferred_style: preferredStyle })
    })
    .then(response => response.json())
    .then(data => {
        if (data.code === 200) {
            // 更新成功，更新本地存储的用户信息
            const userInfo = getUserInfo();
            userInfo.preferred_style = preferredStyle;
            setUserInfo(userInfo);
            
            // 显示成功消息
            messageDiv.textContent = '偏好更新成功！';
            messageDiv.style.color = 'green';
            
            // 重新获取推荐歌曲
            getRecommendSongs(userId);
        } else {
            // 更新失败
            messageDiv.textContent = '更新失败：' + data.message;
            messageDiv.style.color = 'red';
        }
    })
    .catch(error => {
        console.error('更新偏好失败:', error);
        messageDiv.textContent = '更新失败，请检查网络连接';
        messageDiv.style.color = 'red';
    });
}

// 获取推荐歌曲
function getRecommendSongs(userId) {
    const recommendList = document.getElementById('recommendList');
    
    fetch(`${API_BASE_URL}/personal_recommend?user_id=${userId}&top_n=10`)
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                renderSongList(recommendList, data.data.recommend_list);
            } else {
                recommendList.innerHTML = '<p>获取推荐歌曲失败</p>';
            }
        })
        .catch(error => {
            console.error('获取推荐歌曲失败:', error);
            recommendList.innerHTML = '<p>获取推荐歌曲失败，请检查网络连接</p>';
        });
}

// 获取热门歌曲
function getHotSongs() {
    const hotList = document.getElementById('hotList');
    
    fetch(`${API_BASE_URL}/hot_songs?top_n=20`)
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                renderSongList(hotList, data.data.hot_songs);
            } else {
                hotList.innerHTML = '<p>获取热门歌曲失败</p>';
            }
        })
        .catch(error => {
            console.error('获取热门歌曲失败:', error);
            hotList.innerHTML = '<p>获取热门歌曲失败，请检查网络连接</p>';
        });
}

// 渲染歌曲列表
function renderSongList(container, songs) {
    if (songs.length === 0) {
        container.innerHTML = '<p>暂无歌曲</p>';
        return;
    }
    
    container.innerHTML = songs.map(song => `
        <div class="song-item" onclick="window.location.href='play.html?song_id=${song.song_id}'" style="cursor: pointer;">
            <h3>${song.song_name}</h3>
            <p>歌手：${song.singer}</p>
            <p>专辑：${song.album}</p>
            <p>风格：${song.style}</p>
            <p>播放量：${song.play_count}</p>
            <p>评分：${song.rating}</p>
            <span class="song-style">${song.style}</span>
            ${song.has_music_file ? '<span style="color: green; font-size: 12px;">(可播放)</span>' : ''}
        </div>
    `).join('');
}

