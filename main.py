from flask import Flask
from app.login.login import login_bp
from app.register.register import register_bp
from app.chat.chat import chat_bp

app = Flask(__name__, template_folder='./app/web/HTML/', static_folder='./app/web/')

# 配置 Flask-Login
# from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
# from user_login import User
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "/"
# app.secret_key = 'xyz123'

# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(user_id)  # 调用 User 类的静态方法查询数据库

# 注册 Blueprint
app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(chat_bp, url_prefix='/chat')

if __name__ == '__main__':
    app.run(port=3000)