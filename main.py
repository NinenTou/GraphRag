from flask import Flask
from app.login.login import login_bp
from app.register.register import register_bp
from app.chat.chat import chat_bp

app = Flask(__name__, template_folder='./app/web/HTML/', static_folder='./app/web/')

# 注册 Blueprint
app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(register_bp, url_prefix='/register')
app.register_blueprint(chat_bp, url_prefix='/chat')

if __name__ == '__main__':
    app.run(port=3000)