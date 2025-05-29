from . import database
from ..LLMs import ChatgptQuery
from .SQLCorrector import DateCorrector, SQLCorrector
import config
import re

prompt_template = (
        "请根据提供的表格表头将下面的自然语言问题转换成SQL查询语句：\n表头：{schema}\n自然语言问题：{query}\n"
        "注意！只输出SQL语句，不需要额外解释。"
    )

structure_sql = f"""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = '{config.DB_USERBASE}' AND TABLE_NAME = '{config.DB_DATABASE}';
        """

messages = [{"role": "system", "content": "你是一个专业数据库工程师，根据用户问题和数据库结构生成标准SQL。"}]

def llms_generate_sql(nl_query):
    """
    先使用LLMs生成SQL查询语句
    """
    db_schema = "Table: rag.data" + str("(" + ", ".join(d["COLUMN_NAME"] for d in database.get_table_data(structure_sql)) + ")")
    prompt = prompt_template.format(schema = db_schema, query = nl_query)
    sql_query = ChatgptQuery.chat_with_gpt(messages, prompt)

    # 正则匹配SQL语句
    match = re.search(r"(SELECT .*?;)", sql_query, re.DOTALL)
    sql_query = match.group(1) if match else ""
    return sql_query, db_schema

def llms_correction_sql(nl_query: str, sql_query: str, db_schema: str) -> str:
    """
    通过大语言模型修正生成的SQL
    """
    # 日期修正
    # DateCorrector.extract_time_fields(sql_query)
    # corrected_sql = sql_query

    # SQL修正
    corrected_sql = SQLCorrector.SQLcorrect(nl_query, db_schema, sql_query)
    return corrected_sql

def nl2sql(nl_query: str) -> str:
    """
    通过LLMs和规则修正生成SQL查询语句
    """
    initial_sql, db_schema = llms_generate_sql(nl_query)
    final_sql = llms_correction_sql(nl_query, initial_sql, db_schema)
    return final_sql