from flask import Flask, Blueprint, render_template, jsonify, url_for, request
from flask_cors import CORS
import os
import config
from ..MySQL import database

app = Flask(__name__)
CORS(app)
register_bp = Blueprint('register', __name__)

@register_bp.route('/')
def form():
    return render_template('register.html')

@register_bp.route('/add_register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    connect = database.get_user_db_connection()
    cur = connect.cursor()
    try:
        cur.execute("INSERT INTO user (user_name, password) VALUES (%s, %s)", 
                    (username, password))
        connect.commit()
        cur.close()
            
        # 创建用户上传目录
        user_upload_dir = os.path.join(config.UPLOAD_FOLDER, username)
        if not os.path.exists(user_upload_dir):
            os.makedirs(user_upload_dir)
        return jsonify({'message': '注册成功'}), 201
    
    except Exception as e:
        connect.rollback()
        cur.close()
        return jsonify({'success': False, 'message': '注册失败，用户名可能已被使用'}), 400