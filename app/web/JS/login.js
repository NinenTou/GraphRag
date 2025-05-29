// script.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            // 发送登录请求到后端
            fetch('http://127.0.0.1:3000/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({username, password }),
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.message === '登录成功') {
                    console.log('用户信息：', data.user);
                    window.location.href = 'http://127.0.0.1:3000/chat?username=' + encodeURIComponent(username);
                }
            })
            .catch(error => {
                console.error('登录失败：', error);
            });
        });
    }
});