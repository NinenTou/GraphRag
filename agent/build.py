from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state import State
from .workflow import table_processing_node
# , sql_get_node, err_reporter_node, correct_reporter_node

def _build_base_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)
    builder.add_edge(START, "table_processing")
    builder.add_node("table_processing", table_processing_node)
    builder.add_conditional_edges(
        "table_processing",
        lambda state: "is_single_table" if state["sql_get_iterations"] > 0 else "reporter"
    )
    # builder.add_node("sql_get", sql_get_node)
    # builder.add_conditional_edges(
    #     "sql_get",
    #     lambda state: "sql_get" if state["sql_get_iterations"] > 1 else "reporter"
    # )
    # builder.add_node("err_reporter", err_reporter_node)
    # builder.add_node("correct_reporter", correct_reporter_node)
    # builder.add_edge("err_reporter", END)
    # builder.add_edge("correct_reporter", END)
    return builder

def build_graph():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile(checkpointer=MemorySaver(), interrupt_after=["table_processing"])