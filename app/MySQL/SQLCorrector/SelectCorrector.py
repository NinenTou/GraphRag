import re
from typing import List, Set, Dict

# 假设这些函数为辅助工具函数，实际需要根据SQL解析实现
def get_aggregate_fields(sql: str) -> List[str]:
    # 伪实现：假设使用正则匹配聚合函数
    return re.findall(r'\b(SUM|AVG|COUNT|MIN|MAX)\s*\(.*?\)', sql, flags=re.IGNORECASE)

def get_select_fields(sql: str) -> List[str]:
    # 简单提取SELECT子句的字段（非常简化的版本）
    m = re.search(r'SELECT\s+(.*?)\s+FROM', sql, flags=re.IGNORECASE)
    if m:
        fields = m.group(1).split(',')
        return [f.strip() for f in fields]
    return []

def get_group_by_fields(sql: str) -> List[str]:
    m = re.search(r'GROUP BY\s+(.*?)(ORDER BY|$)', sql, flags=re.IGNORECASE)
    if m:
        fields = m.group(1).split(',')
        return [f.strip() for f in fields]
    return []

def get_order_by_fields(sql: str) -> List[str]:
    m = re.search(r'ORDER BY\s+(.*?)(LIMIT|$)', sql, flags=re.IGNORECASE)
    if m:
        fields = m.group(1).split(',')
        return [f.strip() for f in fields]
    return []

def add_fields_to_select(sql: str, fields: List[str]) -> str:
    """
    在SELECT子句中添加fields。假设SQL格式为：SELECT existing_fields FROM ...，
    我们简单地将需要添加的字段拼接到SELECT字段列表后面。
    """
    m = re.search(r'(SELECT\s+)(.*?)(\s+FROM\s+)', sql, flags=re.IGNORECASE)
    if not m:
        return sql
    select_prefix, current_fields, from_part = m.groups()
    # 拼接新字段（避免重复添加，由调用者处理重复问题）
    new_fields = current_fields + ", " + ", ".join(fields)
    new_sql = select_prefix + new_fields + from_part + sql[m.end():]
    return new_sql

def remove_asterisk_and_add_fields(sql: str, default_fields: Set[str]) -> str:
    """
    将SELECT中的*替换为default_fields字段列表
    """
    # 替换SELECT *为SELECT 默认字段列表
    new_fields = ", ".join(default_fields)
    new_sql = re.sub(r'SELECT\s+\*\s+', f'SELECT {new_fields} ', sql, flags=re.IGNORECASE)
    return new_sql

def deal_alias_to_order_by(sql: str) -> str:
    # 伪实现：假设处理ORDER BY中别名问题，这里直接返回原sql
    return sql

# 模拟环境配置
class Environment:
    def __init__(self, additional_info: str = "false"):
        self.properties = {"s2.corrector.additional.information": additional_info}
    def get_property(self, key: str) -> str:
        return self.properties.get(key, "")

# 假设 ChatQueryContext 和 SemanticParseInfo 用字典模拟
# 数据结构示例：
# semanticParseInfo = {
#     "sql_info": {"correctedS2SQL": "SELECT * FROM orders"},
#     "query_type": "DETAIL",
#     "dataSetId": 1
# }
# chatQueryContext = {
#     "semantic_schema": {
#         "dataSetSchemaMap": {
#             1: {
#                 "tagDefaultMetrics": [{"name": "amount"}],
#                 "tagDefaultDimensions": [{"name": "order_date"}]
#             }
#         }
#     }
# }

class SelectCorrector:
    ADDITIONAL_INFORMATION = "s2.corrector.additional.information"

    def do_correct(self, chat_query_context: Dict, semantic_parse_info: Dict):
        # 获取当前 SQL 语句
        sql_info = semantic_parse_info.get("sql_info", {})
        correct_s2sql = sql_info.get("correctedS2SQL", "")
        # 获取聚合字段和查询字段
        aggregate_fields = get_aggregate_fields(correct_s2sql)
        select_fields = get_select_fields(correct_s2sql)
        # 如果聚合字段数量等于查询字段数量，则不做任何处理
        if aggregate_fields and select_fields and len(aggregate_fields) == len(select_fields):
            return  # 不修改
        # 添加必要的字段到 SELECT 子句
        correct_s2sql = self.add_fields_to_select(chat_query_context, semantic_parse_info, correct_s2sql)
        # 处理 ORDER BY 中的别名
        query_sql = deal_alias_to_order_by(correct_s2sql)
        # 更新语义解析信息中的SQL
        sql_info["correctedS2SQL"] = query_sql
        semantic_parse_info["sql_info"] = sql_info

    def add_fields_to_select(self, chat_query_context: Dict, semantic_parse_info: Dict, correct_s2sql: str) -> str:
        # 先调用添加默认指标和维度字段的方法
        correct_s2sql = self.add_tag_default_fields(chat_query_context, semantic_parse_info, correct_s2sql)
        select_fields = set(get_select_fields(correct_s2sql))
        need_add_fields = set(get_group_by_fields(correct_s2sql))
        
        # 决定是否将ORDER BY字段加入
        env = Environment(additional_info="true")  # 此处示例配置为true
        corrector_additional_info = env.get_property(self.ADDITIONAL_INFORMATION)
        if corrector_additional_info.strip() and corrector_additional_info.strip().lower() == "true":
            need_add_fields.update(get_order_by_fields(correct_s2sql))
        if not select_fields or not need_add_fields:
            return correct_s2sql
        # 去除已存在的字段
        need_add_fields = need_add_fields - select_fields
        if need_add_fields:
            correct_s2sql = add_fields_to_select(correct_s2sql, list(need_add_fields))
        # 更新 SQL 信息
        semantic_parse_info.get("sql_info", {})["correctedS2SQL"] = correct_s2sql
        return correct_s2sql

    def add_tag_default_fields(self, chat_query_context: Dict, semantic_parse_info: Dict, correct_s2sql: str) -> str:
        # 检查SELECT中是否有 * 且查询类型为 DETAIL
        has_asterisk = "*" in correct_s2sql  # 简化判断
        if not (has_asterisk and semantic_parse_info.get("query_type") == "DETAIL"):
            return correct_s2sql
        data_set_id = semantic_parse_info.get("dataSetId")
        # 从chat_query_context中获取数据集schema
        data_set_schema = chat_query_context.get("semantic_schema", {}).get("dataSetSchemaMap", {}).get(data_set_id)
        need_add_default_fields = set()
        if data_set_schema:
            metrics = {elem["name"] for elem in data_set_schema.get("tagDefaultMetrics", [])}
            dimensions = {elem["name"] for elem in data_set_schema.get("tagDefaultDimensions", [])}
            need_add_default_fields.update(metrics)
            need_add_default_fields.update(dimensions)
        if need_add_default_fields:
            correct_s2sql = remove_asterisk_and_add_fields(correct_s2sql, need_add_default_fields)
        return correct_s2sql

# 测试示例
if __name__ == '__main__':
    # 构造示例上下文和语义解析信息
    chat_query_context = {
        "semantic_schema": {
            "dataSetSchemaMap": {
                1: {
                    "tagDefaultMetrics": [{"name": "amount"}],
                    "tagDefaultDimensions": [{"name": "order_date"}]
                }
            }
        }
    }
    semantic_parse_info = {
        "sql_info": {"correctedS2SQL": "SELECT * FROM orders GROUP BY customer"},
        "query_type": "DETAIL",
        "dataSetId": 1
    }
    corrector = SelectCorrector()
    corrector.do_correct(chat_query_context, semantic_parse_info)
    print("校正后的SQL:")
    print(semantic_parse_info["sql_info"]["correctedS2SQL"])