// 全局变量
let currentFileId = null;
let isLoading = false;
let inactivityTimer;

document.addEventListener('DOMContentLoaded', function() {
    // 根据当前页面初始化相应的功能
    if (document.getElementById('loginForm')) {
        initLoginPage();
    } else if (document.getElementById('registerForm')) {
        initRegisterPage();
    } else if (document.getElementById('chatMessages')) {
        initChatPage();
    } else if (document.getElementById('forgotPasswordForm')) {
        initForgotPasswordPage();
    }
});

// 初始化登录页面
function initLoginPage() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    // 表单提交
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const code = document.getElementById('code').value;
        
        // 对密码进行哈希处理
        const hashedPassword = await hashPassword(password);
        
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(hashedPassword)}&code=${encodeURIComponent(code)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sessionStorage.setItem('isLoggedIn', 'true');
                sessionStorage.setItem('username', username);
                window.location.href = data.redirect;
            } else {
                errorMessage.textContent = data.message;
            }
        })
        .catch(error => {
            errorMessage.textContent = '登录请求失败，请稍后再试';
            console.error('Error:', error);
        });
    });
}

// 初始化注册页面
function initRegisterPage() {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');
    
    // 表单提交
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // 对密码进行哈希处理
        const hashedPassword = await hashPassword(password);
        print("this")
        fetch('http://127.0.0.1:3000/register/add_register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(hashedPassword)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sessionStorage.setItem('isLoggedIn', 'true');
                sessionStorage.setItem('username', username);
                window.location.href = data.redirect;
            } else {
                errorMessage.textContent = data.message;
            }
        })
        .catch(error => {
            errorMessage.textContent = '注册请求失败，请稍后再试';
            console.error('Error:', error);
        });
    });
}

// 初始化聊天页面
function initChatPage() {
    // 显示用户名
    document.getElementById('usernameDisplay').textContent = `欢迎, ${sessionStorage.getItem('username') || '用户'}`;

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

// 解析Markdown并高亮代码
function renderMarkdown(content) {
    // 配置marked
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (e) {
                    console.error('Error highlighting code:', e);
                }
            }
            return hljs.highlightAuto(code).value;
        },
        langPrefix: 'hljs language-',
        breaks: true,
        gfm: true
    });

    return marked.parse(content);
}

// 创建复制按钮
function createCopyButton(content) {
    const button = document.createElement('button');
    button.className = 'copy-btn';
    button.title = '复制内容';
    button.innerHTML = '<i class="fas fa-copy"></i>';

    button.addEventListener('click', () => {
        navigator.clipboard.writeText(content)
            .then(() => {
                button.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            })
            .catch(err => {
                console.error('复制失败:', err);
            });
    });

    return button;
}

// 添加消息到聊天界面
function addMessageToChat(sender, content) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');

    messageDiv.className = `message ${sender}-message`;

    // 创建消息内容容器
    const messageContent = document.createElement('div');

    // 如果是用户消息
    if (sender === 'user') {
        messageContent.textContent = content;
    }
    // 如果是机器人消息
    else {
        // 解析Markdown内容
        const htmlContent = renderMarkdown(content);
        messageContent.className = 'markdown';
        messageContent.innerHTML = htmlContent;

        // 高亮代码块
        setTimeout(() => {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }, 0);
    }

    // 创建消息元数据
    const messageMeta = document.createElement('div');
    messageMeta.className = 'message-meta';
    messageMeta.textContent = new Date().toLocaleTimeString();

    // 创建操作按钮容器
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'message-actions';

    // 添加复制按钮（对所有消息类型）
    actionsDiv.appendChild(createCopyButton(content));

    // 组装消息元素
    messageDiv.appendChild(actionsDiv);
    messageDiv.appendChild(messageContent);
    messageDiv.appendChild(messageMeta);

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加加载中的消息
function addLoadingMessage(id) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');

    messageDiv.id = id;
    messageDiv.className = 'message bot-message';
    messageDiv.innerHTML = `
        <div class="loading-container">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span style="margin-left: 10px;">正在思考...</span>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 移除加载中的消息
function removeLoadingMessage(id) {
    const messageDiv = document.getElementById(id);
    if (messageDiv) {
        messageDiv.remove();
    }
}

// 密码哈希函数
async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

// 显示错误信息
function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
        errorMessage.style.display = message ? 'block' : 'none';
    }
}

// 显示提示信息
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'toast-message';
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 15px 25px;
        background-color: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);

    // 3秒后自动关闭
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            messageDiv.remove();
        }, 300);
    }, 3000);
}

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translate(-50%, -100%);
            opacity: 0;
        }
        to {
            transform: translate(-50%, 0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translate(-50%, 0);
            opacity: 1;
        }
        to {
            transform: translate(-50%, -100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// 忘记密码页面处理
if (document.getElementById('forgotPasswordForm')) {
    const form = document.getElementById('forgotPasswordForm');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const countdownEl = document.getElementById('countdown');
    const newPasswordGroup = document.getElementById('newPasswordGroup');
    const confirmPasswordGroup = document.getElementById('confirmPasswordGroup');
    const submitBtn = document.getElementById('submitBtn');
    const usernameOrEmailGroup = document.querySelector('.form-group:first-child');
    const verificationCodeGroup = document.querySelector('.verification-code-group');
    let isVerificationStep = true;
    let countdown = 0;
    let verifiedUsernameOrEmail = ''; // 存储已验证的用户名/邮箱

    // 发送验证码
    sendCodeBtn.addEventListener('click', async (e) => {
        e.preventDefault(); // 阻止默认行为
        const usernameOrEmail = document.getElementById('usernameOrEmail').value;
        if (!usernameOrEmail) {
            showMessage('请输入用户名或邮箱', 'danger');
            return;
        }

        if (countdown > 0) return;

        try {
            const response = await fetch('/api/send_reset_code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ usernameOrEmail })
            });

            const data = await response.json();
            if (data.success) {
                startCountdown();
                showMessage('验证码已发送');
            } else {
                showMessage(data.message, 'danger');
            }
        } catch (error) {
            showMessage('发送验证码失败', 'danger');
        }
    });

    // 开始倒计时
    function startCountdown() {
        countdown = 60;
        sendCodeBtn.disabled = true;
        updateCountdown();
        
        const timer = setInterval(() => {
            countdown--;
            updateCountdown();
            if (countdown <= 0) {
                clearInterval(timer);
                sendCodeBtn.disabled = false;
                countdownEl.textContent = '';
            }
        }, 1000);
    }
    
    // 更新倒计时显示
    function updateCountdown() {
        countdownEl.textContent = `${countdown}秒后可重新发送`;
    }

    // 验证验证码
    async function verifyCode() {
        const usernameOrEmail = document.getElementById('usernameOrEmail').value;
        const code = document.getElementById('code').value;

        try {
            const response = await fetch('/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    usernameOrEmail,
                    code
                })
            });

            const data = await response.json();
            if (data.success && data.verified) {
                // 验证成功，显示密码输入框，隐藏用户名和验证码输入框
                isVerificationStep = false;
                verifiedUsernameOrEmail = data.usernameOrEmail;
                usernameOrEmailGroup.style.display = 'none';
                verificationCodeGroup.style.display = 'none';
                newPasswordGroup.style.display = 'block';
                confirmPasswordGroup.style.display = 'block';
                submitBtn.textContent = '重置密码';
                showMessage('验证码正确');
            } else {
                showMessage(data.message, 'danger');
            }
        } catch (error) {
            showMessage('验证失败', 'danger');
        }
    }

    // 重置密码
    async function resetPassword() {
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword !== confirmPassword) {
            showMessage('两次输入的密码不一致', 'danger');
            return;
        }

        try {
            // 对密码进行哈希处理
            const hashedPassword = await hashPassword(newPassword);
            
            const response = await fetch('/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    usernameOrEmail: verifiedUsernameOrEmail,
                    newPassword: hashedPassword,
                    confirmPassword: hashedPassword
                })
            });

            const data = await response.json();
            if (data.success) {
                showMessage('密码重置成功，3秒后跳转到登录页面');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else {
                showMessage(data.message, 'danger');
            }
        } catch (error) {
            showMessage('密码重置失败', 'danger');
        }
    }

    // 按钮点击事件
    submitBtn.addEventListener('click', async (e) => {
        e.preventDefault(); // 阻止表单默认提交行为
        if (isVerificationStep) {
            await verifyCode();
        } else {
            await resetPassword();
        }
    });

    // 表单提交事件
    form.addEventListener('submit', (e) => {
        e.preventDefault(); // 阻止表单默认提交行为
    });
}