from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List

# 状态机的数据结构定义
class State(TypedDict):
    is_single_table: bool
    sql_get_iterations: int

def _build_base_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)
    builder.add_edge(START, "table_processing")
    builder.add_node("table_processing", table_processing)
    builder.add_edge("sql_get", sql_get)
    builder.add_edge("reporter", reporter)
    builder.add_edge("reporter", END)
    return builder

def build_graph():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile()
