document.addEventListener("DOMContentLoaded", function() {
    initChatPage();
});

function initChatPage() {
    // 显示用户名
    const params = new URLSearchParams(location.search);
    document.getElementById('usernameDisplay').textContent = `欢迎, ${params.get('username') || '用户'}`;

    // 初始化文件上传功能
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');

    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            uploadFile(this.files[0]);
            this.value = ''; // 重置input
        }
    });

    // 初始化退出功能
    document.getElementById('logoutBtn').addEventListener('click', function() {
        fetch('/logout', { method: 'GET' })
            .then(() => {
                sessionStorage.clear();
                window.location.href = '/login';
            });
    });

    // 初始化发送消息功能
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');

    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 初始化无操作超时检测
    initInactivityTimer();

    // 加载用户文件和聊天历史
    loadFiles();
}

// 初始化无操作计时器
function initInactivityTimer() {
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(logoutDueToInactivity, 30 * 60 * 1000); // 30分钟
    }

    function logoutDueToInactivity() {
        alert('由于长时间无操作，您已自动退出登录');
        fetch('/logout', { method: 'GET' })
            .then(() => {
                sessionStorage.clear();
                window.location.href = '/login';
            });
    }

    // 添加事件监听器
    ['mousemove', 'keypress', 'click', 'scroll'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer);
    });

    // 初始化计时器
    resetInactivityTimer();
}

// 上传文件
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/files', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadFiles();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('文件上传失败');
    });
}

// 加载文件列表
function loadFiles() {
    fetch('/api/files')
        .then(response => {
            if (response.status === 401) {
                // 会话过期
                sessionStorage.clear();
                window.location.href = '/login';
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                renderFiles(data.files);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 渲染文件列表
function renderFiles(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';

    if (files.length === 0) {
        fileList.innerHTML = '<div class="no-files">暂无上传文件</div>';
        currentFileId = null;
        return;
    }

    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = `file-item ${file.id == currentFileId ? 'active-file' : ''}`;
        fileItem.innerHTML = `
            <div class="file-name" title="${file.name}">${file.name}</div>
            <div class="file-actions">
                <button class="file-action-btn select-btn" data-id="${file.id}">
                    <i class="fas fa-check"></i>
                </button>
                <button class="file-action-btn delete-btn" data-id="${file.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        fileList.appendChild(fileItem);
    });

    // 添加选择文件事件
    document.querySelectorAll('.select-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const fileId = this.getAttribute('data-id');
            selectFile(fileId);
        });
    });

    // 添加删除文件事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const fileId = this.getAttribute('data-id');
            deleteFile(fileId);
        });
    });

    // 如果没有选中文件，默认选中第一个
    if (!currentFileId && files.length > 0) {
        selectFile(files[0].id);
    }
}

// 选择文件
function selectFile(fileId) {
    currentFileId = fileId;
    loadFiles(); // 重新渲染文件列表以更新选中状态

    // 可以在这里加载与文件相关的聊天历史
}

// 删除文件
function deleteFile(fileId) {
    if (!confirm('确定要删除这个文件吗？')) return;

    fetch('/api/files', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_id: fileId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 如果删除的是当前选中的文件，清空当前选中
            if (fileId === currentFileId) {
                currentFileId = null;
            }
            loadFiles();
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('文件删除失败');
    });
}

// 发送消息
function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message || isLoading) return;

    // 添加到聊天界面
    addMessageToChat('user', message);
    messageInput.value = '';

    // 显示加载中的消息
    const loadingId = 'loading-' + Date.now();
    addLoadingMessage(loadingId);
    isLoading = true;

    // 发送到服务器
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question: message,
            file_id: currentFileId
        })
    })
    .then(response => {
        if (response.status === 401) {
            // 会话过期
            sessionStorage.clear();
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        removeLoadingMessage(loadingId);
        isLoading = false;

        if (data && data.success) {
            addMessageToChat('bot', data.answer);
        } else if (data) {
            addMessageToChat('bot', `错误: ${data.message}`);
        }
    })
    .catch(error => {
        removeLoadingMessage(loadingId);
        isLoading = false;
        console.error('Error:', error);
        addMessageToChat('bot', '请求失败，请稍后再试');
    });
}