import pymysql
from pymysql.constants import CLIENT
import pandas as pd
import config
from ..excel.ExcelProcess import jug_file_type, detect_date_col

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

def create_data_table(file: str):
    """
    在MySQL中创建数据表并插入数据
    """
    df = jug_file_type(file)
    connection = get_user_db_connection()
    delete_data_table(connection)
    date_list = detect_date_col(df)
    try:
        with connection.cursor() as cursor:
            table_name = config.DB_DATABASE
            columns = []
            for col_name, dtype in df.dtypes.items():
                if col_name in date_list:
                    sql_type = 'DATETIME'
                elif 'int' in str(dtype):
                    sql_type = 'INT'
                elif 'float' in str(dtype):
                    sql_type = 'FLOAT'
                else:
                    sql_type = 'VARCHAR(255)'
                columns.append(f"`{col_name}` {sql_type}")
            columns_sql = ", ".join(columns)
            create_table_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns_sql});"
            cursor.execute(create_table_sql)

            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in df.columns])}) VALUES ({placeholders})"

            for row in df.itertuples(index=False, name=None):
                row = tuple(None if pd.isna(x) else x for x in row)
                cursor.execute(insert_sql, row)

        connection.commit()
        print("数据已成功插入 MySQL 数据库。")

    except Exception as e:
        connection.rollback()
        print("数据插入失败:", e)

    finally:
        connection.close()

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