from flask import Flask, Blueprint, session, redirect, render_template, jsonify, request, url_for
from flask_cors import CORS
from ..MySQL import database

app = Flask(__name__)
CORS(app)
login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def form():
    return render_template('login.html')

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # 查询用户信息
        cur = database.get_user_db_connection().cursor()
        cur.execute("SELECT user_name, password FROM user WHERE user_name = %s", (username))
        data = cur.fetchone()
        cur.close()

        if not data:
            return jsonify({'success': False, 'message': '用户名不存在'}), 401
        
        db_password = data['password']

        if password != db_password:
            return jsonify({'success': False, 'message': '密码错误'}), 401

        return jsonify({'success': True, 'message': '登录成功', 'user': username}), 200

    return render_template('login.html')