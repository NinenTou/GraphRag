from typing import TypedDict, Any, Optional

class State(TypedDict):
    is_single_table: bool
    is_get_correct_sql: bool
    sql_get_iterations: int
    is_prepared_single_table_ask: bool
    is_prepared_multi_table_ask: bool