from openai import OpenAI
import os

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key="sk-WKwpwTsxJvLJnu5CcfJPfh7Eflb8wzKJkcAyLeYz3au2nMjB",
    base_url="https://api.chatanywhere.tech/v1"
)

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "123456" 
DB_USERBASE = "rag"
DB_PORT = 3306
DB_DATABASE = "data"

UPLOAD_FOLDER = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads'))