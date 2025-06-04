import pymysql
from pymysql.constants import CLIENT
import pandas as pd
import threading
import re
import config
from ..excel.ExcelProcess import jug_file_type, detect_date_col
from ...agent import build_graph

def run_workflow(initial_state):
    """在工作线程中运行工作流"""
    result = build_graph().invoke(initial_state)

def get_user_db_connection():
    """
    获取用户数据库连接
    """
    return pymysql.connect(
        host = config.DB_HOST,
        user = config.DB_USER,
        password = config.DB_PASSWORD,
        database = config.DB_USERBASE,
        port = config.DB_PORT,
        client_flag = CLIENT.MULTI_STATEMENTS, 
        cursorclass = pymysql.cursors.DictCursor
    )

# def create_data_table(file: str):
#     """
#     在MySQL中创建数据表并插入数据，判断是否单表还是多表
#     """
#     df = jug_file_type(file)
#     connection = get_user_db_connection()
#     delete_data_table(connection)
#     date_list = detect_date_col(df)
#     try:
#         with connection.cursor() as cursor:
#             table_name = config.DB_DATABASE
#             columns = []
#             for col_name, dtype in df.dtypes.items():
#                 if col_name in date_list:
#                     sql_type = 'DATETIME'
#                 elif 'int' in str(dtype):
#                     sql_type = 'INT'
#                 elif 'float' in str(dtype):
#                     sql_type = 'FLOAT'
#                 else:
#                     sql_type = 'VARCHAR(255)'
#                 columns.append(f"`{col_name}` {sql_type}")
#             columns_sql = ", ".join(columns)
#             create_table_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns_sql});"
#             cursor.execute(create_table_sql)

#             placeholders = ", ".join(["%s"] * len(df.columns))
#             insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in df.columns])}) VALUES ({placeholders})"

#             for row in df.itertuples(index=False, name=None):
#                 row = tuple(None if pd.isna(x) else x for x in row)
#                 cursor.execute(insert_sql, row)

#         connection.commit()
#         print("数据已成功插入 MySQL 数据库。")

#     except Exception as e:
#         connection.rollback()
#         print("数据插入失败:", e)

#     finally:
#         connection.close()

def create_data_tables(file: str):
    """
    在MySQL中创建数据表并插入数据，支持单表和多表Excel文件，graph工作流从这里开始
    """
    # 获取工作表数据（字典形式，key为表名，value为DataFrame）
    dfs_dict = jug_file_type(file)
    
    connection = get_user_db_connection()
    delete_data_table(connection)
    
    initial_state = {
        "is_single_table": len(dfs_dict) == 1,
        "is_get_correct_sql": False,
        "sql_get_iterations": 0,
        }
    
    try:
        with connection.cursor() as cursor:
            # 循环处理每个工作表
            for table_name, df in dfs_dict.items():
                # 安全处理表名（防止SQL注入）
                safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
                if not safe_table_name:
                    safe_table_name = f"table_{hash(table_name)}"  # 生成唯一表名
                
                # 删除旧表（如果存在）
                cursor.execute(f"DROP TABLE IF EXISTS `{safe_table_name}`")
                
                # 检测日期列
                date_list = detect_date_col(df)
                
                # 动态创建表
                columns = []
                for col_name, dtype in df.dtypes.items():
                    # 安全处理列名
                    safe_col_name = re.sub(r'[^a-zA-Z0-9_]', '', col_name)
                    
                    if col_name in date_list:
                        sql_type = 'DATETIME'
                    elif 'int' in str(dtype):
                        sql_type = 'INT'
                    elif 'float' in str(dtype):
                        sql_type = 'FLOAT'
                    else:
                        sql_type = 'VARCHAR(255)'
                    columns.append(f"`{safe_col_name}` {sql_type}")
                
                columns_sql = ", ".join(columns)
                create_table_sql = f"CREATE TABLE `{safe_table_name}` ({columns_sql});"
                cursor.execute(create_table_sql)
                
                # 准备插入数据
                safe_columns = [f"`{re.sub(r'[^a-zA-Z0-9_]', '', col)}`" for col in df.columns]
                placeholders = ", ".join(["%s"] * len(df.columns))
                insert_sql = f"INSERT INTO `{safe_table_name}` ({', '.join(safe_columns)}) VALUES ({placeholders})"
                
                # 批量插入数据（提高性能）
                data_to_insert = []
                for row in df.itertuples(index=False, name=None):
                    row = tuple(None if pd.isna(x) else x for x in row)
                    data_to_insert.append(row)
                
                # 使用executemany批量插入
                cursor.executemany(insert_sql, data_to_insert)
                print(f"表 {safe_table_name} 已成功插入 {len(data_to_insert)} 行数据。")
        
        connection.commit()
        print("所有数据已成功插入MySQL数据库。")
    
    except Exception as e:
        connection.rollback()
        print("数据插入失败:", e)
        raise  # 重新抛出异常以便上层处理
    
    finally:
        connection.close()
        threading.Thread(target=run_workflow, args=(initial_state)).start()

def delete_data_table(connection: pymysql.Connection):
    """
    从MySQL中删除data数据表
    """

    table_name = config.DB_DATABASE
    drop_table_sql = f"DROP TABLE IF EXISTS `{table_name}`;"
    try:
        with connection.cursor() as cursor:
            cursor.execute(drop_table_sql)
        connection.commit()
        print(f"表 {table_name} 删除成功！")
    except Exception as e:
        connection.rollback()
        print("删除表失败:", e)

def get_table_data(sql :str):
    """
    MySQL获取数据表数据
    """
    connection = get_user_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
    finally:
        connection.close()
    return result

def excute_sql(sql):
    """
    执行SQL语句
    """
    connection = get_user_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
    except Exception as e:
        return "Error", str(e)
    finally:
        connection.commit()
        connection.close()

def log_activity(username, activity_type, description):
    """记录用户活动
    
    Args:
        username: 用户名
        activity_type: 活动类型
        description: 活动描述
    """
    
    # 创建数据库连接
    connection = get_user_db_connection()
    cur = connection.cursor()
    try:
        cur.execute("""
            INSERT INTO activity_logs (user_name, activity_type, description)
            VALUES (%s, %s, %s)
        """, (username, activity_type, description))
        connection.commit()
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
    finally:
        cur.close()
        connection.close() 