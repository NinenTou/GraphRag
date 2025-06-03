from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END

# 1. 修正状态定义：移除所有Annotated注解
class PizzaState(TypedDict):
    order_id: str
    size: str
    flour_type: str
    sauce: str
    extra_cheese: bool
    toppings: List[str]
    dough_ready: bool          # 直接使用普通类型
    dough_size: str            # 直接使用普通类型
    sauce_added: bool          # 直接使用普通类型
    cheese_added: bool         # 直接使用普通类型
    cheese_amount: str         # 直接使用普通类型
    baking_complete: bool      # 直接使用普通类型

pizza_workflow = StateGraph(PizzaState)

# 2. 节点函数保持不变
def prepare_dough(state: PizzaState) -> dict:
    print(f"准备 {state['flour_type']} 面粉面团")
    return {"dough_ready": True, "dough_size": state["size"]}

def add_sauce(state: PizzaState) -> dict:
    print(f"添加{state['sauce']}酱")
    return {"sauce_added": True}

def add_cheese(state: PizzaState) -> dict:
    print("撒上奶酪")
    return {"cheese_added": True}

def add_extra_cheese(state: PizzaState) -> dict:
    print("添加双倍奶酪")
    return {"cheese_amount": "double"}

def baking(state: PizzaState) -> dict:
    print(f"烘烤{state['size']}披萨")
    return {"baking_complete": True}

# 3. 注册节点保持不变
pizza_workflow.add_node("prepare_dough", prepare_dough)
pizza_workflow.add_node("add_sauce", add_sauce)
pizza_workflow.add_node("add_cheese", add_cheese)
pizza_workflow.add_node("add_extra_cheese", add_extra_cheese)
pizza_workflow.add_node("baking_node", baking)

# 4. 标准边保持不变
pizza_workflow.add_edge(START, "prepare_dough")
pizza_workflow.add_edge("prepare_dough", "add_sauce")
pizza_workflow.add_edge("add_sauce", "add_cheese")

# 5. 修正条件边：确保返回值与映射键匹配
def check_cheese_preference(state: PizzaState) -> str:
    # 返回的字符串必须匹配条件边映射的键
    return "add_extra_cheese" if state["extra_cheese"] else "baking_node"

pizza_workflow.add_conditional_edges(
    "add_cheese",
    check_cheese_preference,
    {
        "add_extra_cheese": "add_extra_cheese", 
        "baking_node": "baking_node"  # 键名与函数返回值一致
    }
)

# 6. 结束路径保持不变
pizza_workflow.add_edge("add_extra_cheese", "baking_node")
pizza_workflow.add_edge("baking_node", END)

# 7. 编译并执行
compiled_workflow = pizza_workflow.compile()
initial_state = {
    "order_id": "12345", "size": "大号", "flour_type": "全麦",
    "sauce": "番茄", "extra_cheese": True, "toppings": ["蘑菇", "橄榄", "青椒"],
    # 初始化所有状态字段（添加缺失的字段）
    "dough_ready": False, "dough_size": "", 
    "sauce_added": False, "cheese_added": False, "cheese_amount": "",
    "baking_complete": False
}
final_state = compiled_workflow.invoke(initial_state)
print("最终状态:", final_state)