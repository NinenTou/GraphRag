import pymysql
from pymysql.constants import CLIENT
import pandas as pd
import threading
import re
import config
import logging
from ..excel.ExcelProcess import jug_file_type, detect_date_col
from agent.build import build_graph
from agent.workflow import State

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
        # client_flag = CLIENT.MULTI_STATEMENTS, 
        # cursorclass = pymysql.cursors.DictCursor
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

def create_data_table(file: str) -> list:
    """
    在MySQL中创建数据表并插入数据，支持单表和多表Excel文件
    graph工作流从这里开始
    """
    # 获取工作表数据字典 {表名: DataFrame}
    dfs_dict = jug_file_type(file)
    connection = get_user_db_connection()
    table_names = list()
    initial_state = {
    "is_single_table": len(dfs_dict) == 1,
    "is_get_correct_sql": False,
    "sql_get_iterations": 0,
    "is_prepared_single_table_ask": False,
    "is_prepared_multi_table_ask": False
    }

    record_state(initial_state)

    try:
        with connection.cursor() as cursor:
            # 循环处理每个工作表
            for table_name, df in dfs_dict.items():
                # 安全处理表名（防止SQL注入）
                safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
                if not safe_table_name:
                    safe_table_name = f"table_{hash(table_name)}"  # 生成唯一表名
                
                cursor.execute(f"DROP TABLE IF EXISTS `{safe_table_name}`")
                
                # 检测日期列
                date_list = detect_date_col(df)
                
                # 处理列名：解决空列名和重复列名问题
                original_columns = df.columns.tolist()
                new_columns = []
                col_name_counter = {}  # 跟踪每个列名出现的次数
                
                # 第一遍：处理空列名
                for i, col in enumerate(original_columns):
                    # 处理空列名
                    if pd.isna(col) or col == "":
                        new_col = f"column_{i}"
                    else:
                        # 安全过滤列名
                        new_col = re.sub(r'[^a-zA-Z0-9_]', '', str(col))
                        # 如果过滤后为空
                        if new_col == "":
                            new_col = f"column_{i}"
                    
                    # 添加到新列名列表
                    new_columns.append(new_col)
                
                # 第二遍：处理重复列名
                final_columns = []
                for col in new_columns:
                    if col not in col_name_counter:
                        col_name_counter[col] = 1
                        final_columns.append(col)
                    else:
                        col_name_counter[col] += 1
                        final_columns.append(f"{col}_{col_name_counter[col]}")
                
                # 更新DataFrame列名
                df.columns = final_columns
                
                # 更新日期列列表（使用新列名）
                updated_date_list = []
                for i, col in enumerate(original_columns):
                    if col in date_list:
                        updated_date_list.append(final_columns[i])
                
                # 动态创建表
                columns = []
                for col_name, dtype in df.dtypes.items():
                    if col_name in updated_date_list:
                        sql_type = 'DATETIME'
                    elif 'int' in str(dtype):
                        sql_type = 'INT'
                    elif 'float' in str(dtype):
                        sql_type = 'FLOAT'
                    else:
                        sql_type = 'VARCHAR(255)'
                    columns.append(f"`{col_name}` {sql_type}")
                
                columns_sql = ", ".join(columns)
                create_table_sql = f"CREATE TABLE IF NOT EXISTS `{safe_table_name}` ({columns_sql});"
                cursor.execute(create_table_sql)
                
                # 准备插入数据
                safe_columns = [f"`{col}`" for col in df.columns]  # 列名已安全，直接使用
                placeholders = ", ".join(["%s"] * len(df.columns))
                insert_sql = f"INSERT INTO `{safe_table_name}` ({', '.join(safe_columns)}) VALUES ({placeholders})"
                
                # 批量插入数据（提高性能）
                data_to_insert = []
                for row in df.itertuples(index=False, name=None):
                    row = tuple(None if pd.isna(x) else x for x in row)
                    data_to_insert.append(row)
                
                # 使用executemany批量插入
                if data_to_insert:
                    cursor.executemany(insert_sql, data_to_insert)
                    print(f"表 {safe_table_name} 已成功插入 {len(data_to_insert)} 行数据。")
                else:
                    print(f"表 {safe_table_name} 为空，跳过数据插入。")
                
                table_names.append(safe_table_name)
        
        connection.commit()
        print("所有数据已成功插入MySQL数据库。")
    
    except Exception as e:
        connection.rollback()
        print("数据插入失败:", e)
        # 打印更详细的错误信息
        if hasattr(e, 'args') and len(e.args) > 1:
            print("错误详细信息:", e.args[1])
        raise
    
    finally:
        threading.Thread(target=run_workflow, args=(initial_state, )).start()
        connection.close()
        return table_names

def delete_state_table(connection: pymysql.Connection):
    """
    从MySQL中删除state数据表数据
    """

    table_name = config.DB_STATEBASE
    drop_table_sql = f"DELETE FROM {table_name}`;"
    try:
        with connection.cursor() as cursor:
            cursor.execute(drop_table_sql)
        connection.commit()
        logging.info(f"表 {table_name} 删除成功！")
    except Exception as e:
        connection.rollback()
        logging.info("删除表失败:", e)

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

def get_state():
    """
    获取当前工作流状态
    """
    connection = get_user_db_connection()
    cur = connection.cursor()
    try:
        cur.execute("SELECT * FROM state")
        result = cur.fetchone()
        if result:
            return State(
                is_single_table=result[0],
                is_get_correct_sql=result[1],
                sql_get_iterations=result[2],
                is_prepared_single_table_ask=result[3],
                is_prepared_multi_table_ask=result[4]
            )
        else:
            return None
    except Exception as e:
        print(f"Error fetching state: {str(e)}")
        return None
    finally:
        cur.close()
        connection.close()

def record_state(state: State):
    """记录State状态到数据库的活动日志表
    
    Args:
        state (State): 当前工作流对象
    """
    
    # 创建数据库连接
    connection = get_user_db_connection()
    cur = connection.cursor()
    delete_state_table(connection)
    try:
        cur.execute("""
            REPLACE INTO state (
            is_single_table,
            is_get_correct_sql,
            sql_get_iterations,
            is_prepared_single_table_ask,
            is_prepared_multi_table_ask)
            values (%s, %s, %s, %s, %s)
        """, (state["is_single_table"], state["is_get_correct_sql"], state["sql_get_iterations"], state["is_prepared_single_table_ask"], state["is_prepared_multi_table_ask"]))
        connection.commit()
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
    finally:
        cur.close()
        connection.close() 