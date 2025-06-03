import os 
from flask import Flask, Blueprint, render_template, jsonify, request
from flask_cors import CORS

from ..excel import ExcelProcess
from ..MySQL import NL2SQL, database

app = Flask(__name__)
CORS(app)
chat_bp = Blueprint('chat', __name__)

file_path = None

@chat_bp.route('/')
# @login_required 
def form():
    return render_template('chat.html')

# 文件上传接口
@chat_bp.route('/upload', methods=['POST'])
def upload_file():
    global file_path
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not ExcelProcess.allowed_file(file.filename):
        return jsonify({"error": "请上传表格"}), 400

    file_path = os.path.join(ExcelProcess.UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        database.create_data_table(file_path)
        os.remove(file_path)
        return jsonify({
            "message": "文件上传成功",
        })
    except Exception as e:
        return jsonify({"error": f"文件解析失败: {str(e)}"}), 500

# 聊天查询接口
@chat_bp.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    if file_path is None:
        return jsonify({"error": "请先上传 Excel 文件"}), 400

    sql = NL2SQL.nl2sql(question)
    reply = None
    return jsonify({"response": sql})
