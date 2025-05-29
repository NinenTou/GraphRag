print("Initializing package...") # 初始化包...
from .LLMs.ChatgptQuery import chat_with_gpt, chat_with_gpt_stream
from .MySQL.database import get_user_db_connection,create_data_table
from .excel.ExcelProcess import jug_file_type, allowed_file, UPLOAD_FOLDER