document.addEventListener('DOMContentLoaded', function() {
    // 导航菜单切换
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.profile-section');

    navItems.forEach(item => {
        item.addEventListener('click', function() {
            // 移除所有active类
            navItems.forEach(nav => nav.classList.remove('active'));
            sections.forEach(section => section.classList.remove('active'));

            // 添加active类到当前项
            this.classList.add('active');
            const sectionId = this.dataset.section;
            document.getElementById(sectionId).classList.add('active');
        });
    });

    // 获取用户信息
    fetch('/api/profile')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 更新基本信息
                document.getElementById('username').textContent = data.username;
                document.getElementById('email').textContent = data.email;
                document.getElementById('currentEmail').textContent = data.email;
                document.getElementById('registerTime').textContent = new Date(data.register_time).toLocaleString();
                document.getElementById('chatCount').textContent = data.chat_count;

                // 加载文件列表
                loadFileList();
            } else {
                alert('获取用户信息失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('获取用户信息时发生错误');
        });

    // 返回聊天按钮事件
    document.getElementById('backToChat').addEventListener('click', function() {
        window.location.href = '/chat';
    });

    // 发送邮箱验证码
    document.getElementById('sendEmailCode').addEventListener('click', function() {
        const newEmail = document.getElementById('newEmail').value;
        const currentEmail = document.getElementById('currentEmail').textContent;
        
        if (!newEmail) {
            alert('请输入新邮箱');
            return;
        }

        // 验证新邮箱是否与当前邮箱相同
        if (newEmail === currentEmail) {
            alert('新邮箱不能与当前邮箱相同');
            return;
        }

        // 禁用按钮
        this.disabled = true;

        fetch('/api/send_email_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: newEmail,
                type: 'change_email'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('验证码已发送到新邮箱');
                startCountdown(this);
            } else {
                alert('发送验证码失败：' + data.message);
                this.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('发送验证码时发生错误');
            this.disabled = false;
        });
    });

    // 修改邮箱
    document.getElementById('changeEmailBtn').addEventListener('click', function() {
        const newEmail = document.getElementById('newEmail').value;
        const code = document.getElementById('emailCode').value;

        if (!newEmail || !code) {
            alert('请填写完整信息');
            return;
        }

        fetch('/api/change_email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                new_email: newEmail,
                code: code
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('邮箱修改成功！');
                document.getElementById('currentEmail').textContent = newEmail;
                document.getElementById('email').textContent = newEmail;
                // 清空输入框
                document.getElementById('newEmail').value = '';
                document.getElementById('emailCode').value = '';
            } else {
                alert('邮箱修改失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('修改邮箱时发生错误');
        });
    });

    // 密码哈希处理函数
    async function hashPassword(password) {
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    }

    // 发送密码修改验证码
    document.getElementById('sendPasswordCode').addEventListener('click', async function() {
        const currentPassword = document.getElementById('currentPassword').value;
        if (!currentPassword) {
            alert('请输入当前密码');
            return;
        }

        // 禁用按钮
        this.disabled = true;

        // 对当前密码进行哈希处理
        const hashedPassword = await hashPassword(currentPassword);

        fetch('/api/send_password_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_password: hashedPassword
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('验证码已发送到您的邮箱');
                startCountdown(this);
            } else {
                alert('发送验证码失败：' + data.message);
                this.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('发送验证码时发生错误');
            this.disabled = false;
        });
    });

    // 验证验证码
    document.getElementById('verifyPasswordCode').addEventListener('click', async function() {
        const code = document.getElementById('passwordCode').value;
        const currentPassword = document.getElementById('currentPassword').value;
        
        if (!code) {
            alert('请输入验证码');
            return;
        }

        // 对当前密码进行哈希处理
        const hashedPassword = await hashPassword(currentPassword);

        fetch('/api/verify_password_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code,
                old_password: hashedPassword
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 隐藏当前密码输入区域
                document.getElementById('currentPassword').closest('.form-group').style.display = 'none';
                // 隐藏验证码区域（包括标签、输入框、发送按钮和倒计时）
                document.querySelector('#password-settings .verification-code-group').style.display = 'none';
                // 隐藏验证按钮
                document.querySelector('#password-settings .verification-button-group').style.display = 'none';
                // 显示新密码输入区域
                document.getElementById('newPasswordGroup').style.display = 'block';
            } else {
                alert('验证码错误：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('验证码验证时发生错误');
        });
    });

    // 修改密码
    document.getElementById('changePasswordBtn').addEventListener('click', async function() {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const code = document.getElementById('passwordCode').value;

        if (!currentPassword || !newPassword || !confirmPassword || !code) {
            alert('请填写完整信息');
            return;
        }

        if (newPassword !== confirmPassword) {
            alert('两次输入的新密码不一致！');
            return;
        }

        // 显示加载状态
        const button = this;
        const originalText = button.textContent;
        button.textContent = '正在修改...';
        button.disabled = true;

        // 对密码进行哈希处理
        const hashedOldPassword = await hashPassword(currentPassword);
        const hashedNewPassword = await hashPassword(newPassword);

        fetch('/api/change_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_password: hashedOldPassword,
                new_password: hashedNewPassword,
                code: code
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('密码修改成功！请重新登录');
                // 清空所有输入框
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmPassword').value = '';
                document.getElementById('passwordCode').value = '';
                // 跳转到登录页面
                window.location.href = '/login';
            } else {
                alert('密码修改失败：' + data.message);
                // 恢复按钮状态
                button.textContent = originalText;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('密码修改时发生错误');
            // 恢复按钮状态
            button.textContent = originalText;
            button.disabled = false;
        });
    });

    // 加载文件列表
    function loadFileList() {
        fetch('/api/files')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const fileList = document.getElementById('fileList');
                    fileList.innerHTML = '';

                    data.files.forEach(file => {
                        const fileItem = document.createElement('div');
                        fileItem.className = 'file-item';
                        fileItem.innerHTML = `
                            <span>${file.name}</span>
                            <span>${new Date(file.upload_time).toLocaleString()}</span>
                            <div class="file-actions">
                                <button class="file-action-btn preview-btn" data-id="${file.id}">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="file-action-btn report-btn" data-id="${file.id}">
                                    <i class="fas fa-file-alt"></i>
                                </button>
                                <button class="file-action-btn delete-btn" data-id="${file.id}">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        `;
                        fileList.appendChild(fileItem);
                    });

                    // 添加预览、报告和删除事件
                    document.querySelectorAll('.preview-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const fileId = this.dataset.id;
                            previewFile(fileId);
                        });
                    });

                    document.querySelectorAll('.report-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const fileId = this.dataset.id;
                            generateReport(fileId);
                        });
                    });

                    document.querySelectorAll('.delete-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            if (confirm('确定要删除这个文件吗？')) {
                                const fileId = this.dataset.id;
                                deleteFile(fileId);
                            }
                        });
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('加载文件列表时发生错误');
            });
    }

    // 删除文件
    function deleteFile(fileId) {
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
                alert('文件删除成功');
                loadFileList();
            } else {
                alert('文件删除失败：' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('删除文件时发生错误');
        });
    }

    // 倒计时功能
    function startCountdown(button) {
        let countdown = 60;
        const countdownEl = document.createElement('div');
        countdownEl.className = 'countdown';
        button.parentNode.appendChild(countdownEl);
        
        const timer = setInterval(() => {
            countdown--;
            countdownEl.textContent = `${countdown}秒后可重新发送`;
            
            if (countdown <= 0) {
                clearInterval(timer);
                button.disabled = false;
                button.textContent = '发送验证码';
                countdownEl.remove();
            }
        }, 1000);
    }

    // 添加预览文件函数
    async function previewFile(fileId) {
        try {
            const response = await fetch(`/preview/${fileId}`);
            if (!response.ok) {
                throw new Error('预览失败');
            }
            const html = await response.text();
            
            // 显示预览容器
            const previewContainer = document.getElementById('previewContainer');
            const previewContent = document.getElementById('previewContent');
            const previewTitle = document.getElementById('previewTitle');
            const downloadReportBtn = document.getElementById('downloadReport');
            previewTitle.textContent = '预览文件';
            previewContent.innerHTML = html;
            previewContainer.style.display = 'block';
            downloadReportBtn.style.display = 'none';  // 隐藏导出Word按钮
            
            // 添加关闭按钮事件
            document.getElementById('closePreview').addEventListener('click', function() {
                previewContainer.style.display = 'none';
                previewContent.innerHTML = '';
                downloadReportBtn.style.display = 'block';  // 恢复显示导出Word按钮
            });
        } catch (error) {
            alert('预览文件失败：' + error.message);
        }
    }

    // 添加生成报告函数
    async function generateReport(fileId) {
        try {
            // 显示加载状态
            const fileItem = document.querySelector(`.file-item .report-btn[data-id="${fileId}"]`).closest('.file-item');
            const originalHtml = fileItem.innerHTML;
            fileItem.innerHTML = `<div class="loading-indicator">正在生成报告，请稍候...</div>`;
            
            const response = await fetch(`/api/generate_report/${fileId}`);
            if (!response.ok) {
                throw new Error('生成报告失败');
            }
            const data = await response.json();
            
            // 恢复原始显示
            fileItem.innerHTML = originalHtml;
            
            // 重新绑定事件监听器
            const previewBtn = fileItem.querySelector('.preview-btn');
            const reportBtn = fileItem.querySelector('.report-btn');
            const deleteBtn = fileItem.querySelector('.delete-btn');
            
            previewBtn.addEventListener('click', function() {
                const fileId = this.dataset.id;
                previewFile(fileId);
            });
            
            reportBtn.addEventListener('click', function() {
                const fileId = this.dataset.id;
                generateReport(fileId);
            });
            
            deleteBtn.addEventListener('click', function() {
                if (confirm('确定要删除这个文件吗？')) {
                    const fileId = this.dataset.id;
                    deleteFile(fileId);
                }
            });
            
            if (data.success) {
                // 显示报告内容
                const previewContainer = document.getElementById('previewContainer');
                const previewContent = document.getElementById('previewContent');
                const previewTitle = document.getElementById('previewTitle');
                const downloadReportBtn = document.getElementById('downloadReport');
                previewTitle.textContent = '报告预览';
                // 添加 markdown-body 类并渲染 Markdown
                previewContent.className = 'preview-content markdown-body';
                previewContent.innerHTML = marked.parse(data.report);
                previewContainer.style.display = 'block';
                downloadReportBtn.style.display = 'block';  // 显示导出Word按钮
                
                // 保存当前报告ID，用于下载
                document.getElementById('downloadReport').setAttribute('data-id', fileId);
                
                // 添加关闭按钮事件
                document.getElementById('closePreview').addEventListener('click', function() {
                    previewContainer.style.display = 'none';
                    previewContent.innerHTML = '';
                    previewContent.className = 'preview-content';
                });

                // 添加下载按钮事件
                document.getElementById('downloadReport').addEventListener('click', function() {
                    window.location.href = `/api/download_report/${fileId}`;
                });
            } else {
                alert('生成报告失败：' + data.message);
            }
        } catch (error) {
            alert('生成报告失败：' + error.message);
        }
    }

    // 添加下载报告函数
    async function downloadReport(fileId) {
        try {
            const response = await fetch(`/api/download_report/${fileId}`);
            if (!response.ok) {
                throw new Error('下载报告失败');
            }
            
            // 获取文件名
            const filename = response.headers.get('Content-Disposition').split('filename=')[1];
            const blob = await response.blob();
            
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = decodeURIComponent(filename);
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            alert('下载报告失败：' + error.message);
        }
    }
}); 