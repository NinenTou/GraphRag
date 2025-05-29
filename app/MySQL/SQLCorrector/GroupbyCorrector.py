import re
import logging
from typing import List, Set, Dict

# 初始化日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 模拟辅助函数
def has_distinct(sql: str) -> bool:
    return bool(re.search(r'\bDISTINCT\b', sql, re.IGNORECASE))

def get_select_fields(sql: str) -> List[str]:
    # 简单提取 SELECT 子句中逗号分隔的字段
    m = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
    if m:
        fields = m.group(1).split(',')
        return [f.strip() for f in fields]
    return []

def get_pure_select_fields(sql: str) -> List[str]:
    # 这里与 get_select_fields 相同，实际可能需要剥离别名等
    return get_select_fields(sql)

def get_aggregate_fields(sql: str) -> List[str]:
    # 简单匹配聚合函数中的字段（如 SUM( field ) ）
    return re.findall(r'\b(?:SUM|AVG|COUNT|MIN|MAX)\s*\((.*?)\)', sql, re.IGNORECASE)

def has_group_by(sql: str) -> bool:
    return bool(re.search(r'\bGROUP BY\b', sql, re.IGNORECASE))

def add_group_by(sql: str, group_by_fields: Set[str]) -> str:
    # 假设在 SQL 的末尾添加 GROUP BY 子句
    if group_by_fields:
        group_by_clause = " GROUP BY " + ", ".join(group_by_fields)
        return sql + group_by_clause
    return sql

# 模拟环境获取
class Environment:
    def __init__(self, additional_info: str = "true"):
        self.properties = {"s2.corrector.additional.information": additional_info}
    def get_property(self, key: str) -> str:
        return self.properties.get(key, "")

# 模拟获取维
# 度字段
def get_dimensions(data_set_id: int, semantic_schema: Dict) -> Set[str]:
    # 从 semantic_schema 中获取数据集对应的维度字段
    ds_schema = semantic_schema.get("dataSetSchemaMap", {}).get(data_set_id, {})
    # 假设维度字段存储在 "tagDefaultDimensions" 列表中，每个元素有 "name" 属性
    dimensions = ds_schema.get("tagDefaultDimensions", [])
    return {dim["name"] for dim in dimensions}

# 模拟枚举与常量
class QueryType:
    METRIC = "METRIC"
    DETAIL = "DETAIL"

# 模拟时间维度枚举：这里假设返回中文“日”
class TimeDimensionEnum:
    @staticmethod
    def DAY():
        return "日"

# 定义 BaseSemanticCorrector（此处为空基类，仅作接口定义）
class BaseSemanticCorrector:
    def do_correct(self, chat_query_context: Dict, semantic_parse_info: Dict):
        raise NotImplementedError

# 实现 GroupByCorrector
class GroupByCorrector(BaseSemanticCorrector):

    ADDITIONAL_INFORMATION = "s2.corrector.additional.information"

    def do_correct(self, chat_query_context: Dict, semantic_parse_info: Dict):
        if not self.need_add_group_by(chat_query_context, semantic_parse_info):
            return
        self.add_group_by_fields(chat_query_context, semantic_parse_info)

    def need_add_group_by(self, chat_query_context: Dict, semantic_parse_info: Dict) -> bool:
        # 仅对 METRIC 类型的查询处理
        if semantic_parse_info.get("query_type") != QueryType.METRIC:
            return False

        data_set_id = semantic_parse_info.get("dataSetId")
        sql_info = semantic_parse_info.get("sql_info", {})
        correct_s2sql = sql_info.get("correctedS2SQL", "")
        semantic_schema = chat_query_context.get("semantic_schema", {})

        # 如果存在 DISTINCT，则不添加 GROUP BY
        if has_distinct(correct_s2sql):
            logger.debug("no need to add groupby, existed distinct in s2sql: %s", correct_s2sql)
            return False

        # 获取维度字段
        dimensions = get_dimensions(data_set_id, semantic_schema)
        select_fields = get_select_fields(correct_s2sql)
        if not select_fields or not dimensions:
            return False

        # 如果只有一个 SELECT 字段且它为时间维度（例如“日”），则不添加 GROUP BY
        if len(select_fields) == 1 and select_fields[0] == TimeDimensionEnum.DAY():
            return False

        if has_group_by(correct_s2sql):
            logger.debug("No need to add groupby, existed groupby in s2sql: %s", correct_s2sql)
            return False

        # 检查环境配置
        env = Environment()
        corrector_additional_info = env.get_property(self.ADDITIONAL_INFORMATION)
        if corrector_additional_info.strip() and not corrector_additional_info.strip().lower() == "true":
            return False
        return True

    def add_group_by_fields(self, chat_query_context: Dict, semantic_parse_info: Dict):
        data_set_id = semantic_parse_info.get("dataSetId")
        sql_info = semantic_parse_info.get("sql_info", {})
        correct_s2sql = sql_info.get("correctedS2SQL", "")
        semantic_schema = chat_query_context.get("semantic_schema", {})

        dimensions = get_dimensions(data_set_id, semantic_schema)
        select_fields = get_pure_select_fields(correct_s2sql)
        aggregate_fields = get_aggregate_fields(correct_s2sql)

        # 过滤：仅保留在维度集合中的 SELECT 字段，并排除掉出现在聚合函数中的字段
        group_by_fields = {field for field in select_fields if field in dimensions and field not in aggregate_fields}

        # 调用辅助方法添加 GROUP BY 子句
        new_sql = add_group_by(correct_s2sql, group_by_fields)
        sql_info["correctedS2SQL"] = new_sql
        semantic_parse_info["sql_info"] = sql_info

# 测试示例
if __name__ == '__main__':
    # 构造示例上下文（chatQueryContext）和语义解析信息（semanticParseInfo）
    chat_query_context = {
        "semantic_schema": {
            "dataSetSchemaMap": {
                1: {
                    "tagDefaultDimensions": [{"name": "customer"}, {"name": "order_date"}],
                    "tagDefaultMetrics": [{"name": "amount"}]
                }
            }
        }
    }
    # 示例 SQL：SELECT 部分只有一个字段（例如 customer），不含 GROUP BY
    semantic_parse_info = {
        "query_type": QueryType.METRIC,
        "dataSetId": 1,
        "sql_info": {
            "correctedS2SQL": "SELECT customer FROM orders"
        }
    }
    corrector = GroupByCorrector()
    corrector.do_correct(chat_query_context, semantic_parse_info)
    print("校正后的SQL:")
    print(semantic_parse_info["sql_info"]["correctedS2SQL"])
