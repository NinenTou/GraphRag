// 文件上传处理
const fileInput = document.getElementById('excel-file');
const fileIndicator = document.getElementById('file-indicator');

fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        // 显示文件信息
        fileIndicator.style.display = 'flex';
        fileIndicator.querySelector('.file-name').textContent = file.name;
        fileIndicator.querySelector('.file-size').textContent = 
            (file.size / 1024 / 1024).toFixed(2) + ' MB';

        // 发送文件到后端
        fetch('http://127.0.0.1:3000/chat/upload', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                addMessage('bot', data.message); // 显示后端返回的消息
                if (data.data_preview) {
                    addMessage('bot', `以下是文件的前5行数据：\n${data.data_preview}`);
                }
            } else if (data.error) {
                addMessage('bot', `文件上传失败：${data.error}`);
            }
        })
        .catch(error => {
            addMessage('bot', '文件上传失败，请检查网络连接。');
            console.error(error);
        });
    }
});

// 聊天功能
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addMessage('user', text);
    chatInput.value = '';

    // 发送问题到后端
    fetch('http://127.0.0.1:3000/chat/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: text }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            addMessage('bot', data.response); // 显示后端返回的答案
        } else if (data.error) {
            addMessage('bot', `请求失败：${data.error}`);
        }
    })
    .catch(error => {
        addMessage('bot', '请求失败，请检查网络连接。');
        console.error(error);
    });
}

function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${type}-message`;
    bubble.innerHTML = type === 'bot' 
        ? `<i class="fas fa-robot"></i> ${text}`
        : text;

    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    
    // 自动滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}