import sqlparse
import re
from sqlparse.sql import Where, Comparison, Identifier
from ...MySQL import database
from sqlparse.tokens import Token

# 日期字段格式化 SQL
date_format = f"""ALTER TABLE rag.data ADD COLUMN order_date DATE;

UPDATE rag.data
SET order_date = STR_TO_DATE(SUBSTRING_INDEX({{}}, ' ', 1), '%Y-%m-%d');

ALTER TABLE rag.data DROP COLUMN {{}};
ALTER TABLE rag.data CHANGE COLUMN order_date {{}} DATE;
"""

def extract_time_fields(sql):
    """
    使用 sqlparse 分析 SQL 语句，从 WHERE 子句中提取可能表示时间字段的标识符。
      1. 解析 SQL 并定位 WHERE 子句。
      2. 递归遍历 WHERE 子句中的 token，查找 Comparison 类型的 token。
      3. 从 Comparison token 中提取左侧的字段名，
         如果字段名中包含“时间”或“time”（忽略大小写），或者整个比较表达式中出现日期函数（如 DATE_SUB、CURDATE），
         则认为该字段可能为时间字段，将其加入结果集合。
    """
    statements = sqlparse.parse(sql)
    if not statements:
        return []
    
    stmt = statements[0]
    time_fields = set()
    
    # 定位 WHERE 子句
    where_clause = None
    for token in stmt.tokens:
        if isinstance(token, Where):
            where_clause = token
            break
    if where_clause is None:
        return []
    
    # 定义递归处理函数，遍历 token
    def recursive_extract(token):
        if isinstance(token, Comparison):
            # 获取比较表达式左侧的标识符
            left_token = token.token_first(skip_cm=True)
            field_name = ""
            if isinstance(left_token, Identifier):
                field_name = left_token.get_real_name() or ""
            else:
                field_name = left_token.value.strip() if left_token else ""
            # 判断字段名是否包含中文“时间”或者英文“time”
            if "时间" in field_name or "time" in field_name.lower():
                time_fields.add(field_name)
            # 如果整个比较表达式中包含日期函数，也加入该字段
            if re.search(r"DATE_SUB|CURDATE", token.value, re.IGNORECASE):
                time_fields.add(field_name)
        elif token.is_group:
            # 递归遍历子 token
            for subtoken in token.tokens:
                recursive_extract(subtoken)
    
    # 遍历 WHERE 子句中的所有 token
    for token in where_clause.tokens:
        recursive_extract(token)
    
    for field in time_fields:
        database.excute_sql(date_format.format(field, field, field))