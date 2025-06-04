from .state import State
import logging

def table_processing_node(state: State):
    """Process the table based on whether it's a single table or multiple tables."""
    if state["is_single_table"]:
        logging.info("Processing single table...")
        # 处理单表逻辑
        return {"is_single_table": True}
    else:
        logging.info("Processing multiple tables...")
        # 处理多表逻辑
        return {"sql_get_iterations": False}

def check_sql_get_iterations(state: State) -> str:
    """Determine the next node based on SQL get iterations."""
    if state["sql_get_iterations"] >= 3:
        return "sql_get"
    else:
        return "reporter"