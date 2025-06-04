from typing import TypedDict

# 状态机的数据结构定义
class State(TypedDict):
    is_single_table: bool
    is_get_correct_sql: bool
    sql_get_iterations: int