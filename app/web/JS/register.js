document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            // 发送注册请求到后端
            fetch('http://127.0.0.1:3000/register/add_register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({username, password}),
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.message === '注册成功') {
                    window.location.href = 'http://127.0.0.1:3000';
                }
            })
            .catch(error => {
                console.error('注册失败：', error);
            });
        });
    }
});