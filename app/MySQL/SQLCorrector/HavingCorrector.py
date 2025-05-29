import re
import os
from abc import ABC, abstractmethod
from typing import Set, List

class BaseSemanticCorrector(ABC):
    @abstractmethod
    def do_correct(self, chat_query_context, semantic_parse_info):
        pass

class SemanticParseInfo:
    def __init__(self):
        self.data_set = DataSetInfo()
        self.sql_info = SQLInfo()

class SQLInfo:
    def __init__(self):
        self.corrected_s2sql = ""

class DataSetInfo:
    def __init__(self):
        self.data_set_id = 0

class ChatQueryContext:
    def __init__(self):
        self.semantic_schema = SemanticSchema()

class SemanticSchema:
    def get_metrics(self, data_set_id) -> Set[str]:
        # 模拟获取指标集合
        return {"sales", "profit"}

class Environment:
    @property
    def corrector_additional_info(self):
        return os.getenv("S2_CORRECTOR_ADDITIONAL_INFORMATION", "false")

class SqlAddHelper:
    @staticmethod
    def add_having(original_sql: str, metrics: Set[str]) -> str:
        """
        添加 HAVING 子句逻辑
        示例实现：在所有指标后添加 IS NOT NULL 条件
        """
        if not metrics:
            return original_sql
        
        conditions = [f"{metric} IS NOT NULL" for metric in metrics]
        having_clause = " HAVING " + " AND ".join(conditions)
        
        # 简单实现：直接追加到 SQL 末尾（实际需要更精确的语法分析）
        if "HAVING" not in original_sql.upper():
            return original_sql + having_clause
        return original_sql

    @staticmethod
    def add_function_to_select(original_sql: str, expressions: List[str]) -> str:
        """
        将表达式添加到 SELECT 子句
        """
        select_pattern = re.compile(r"SELECT(.*?)FROM", re.IGNORECASE | re.DOTALL)
        match = select_pattern.search(original_sql)
        if not match:
            return original_sql
        
        select_part = match.group(1).strip()
        new_select = f"{select_part}, " + ", ".join(expressions)
        return original_sql.replace(match.group(1), " " + new_select + " ")

class SqlSelectHelper:
    @staticmethod
    def get_having_expression(sql: str) -> List[str]:
        """
        提取 HAVING 子句中的表达式
        """
        having_pattern = re.compile(r"HAVING(.*?)(?:ORDER BY|GROUP BY|$)", re.IGNORECASE | re.DOTALL)
        match = having_pattern.search(sql)
        return [match.group(1).strip()] if match else []

    @staticmethod
    def has_aggregate_function(sql: str) -> bool:
        """
        检查是否存在聚合函数
        """
        agg_pattern = re.compile(r"\b(SUM|AVG|COUNT|MIN|MAX)\b", re.IGNORECASE)
        return bool(agg_pattern.search(sql))

class HavingCorrector(BaseSemanticCorrector):
    def __init__(self):
        self.environment = Environment()

    def do_correct(self, chat_query_context: ChatQueryContext, semantic_parse_info: SemanticParseInfo):
        self._add_having(chat_query_context, semantic_parse_info)
        
        if self.environment.corrector_additional_info.lower() == "true":
            self._add_having_to_select(semantic_parse_info)

    def _add_having(self, chat_query_context: ChatQueryContext, semantic_parse_info: SemanticParseInfo):
        data_set_id = semantic_parse_info.data_set.data_set_id
        metrics = chat_query_context.semantic_schema.get_metrics(data_set_id)
        
        if not metrics:
            return
        
        original_sql = semantic_parse_info.sql_info.corrected_s2sql
        updated_sql = SqlAddHelper.add_having(original_sql, metrics)
        semantic_parse_info.sql_info.corrected_s2sql = updated_sql

    def _add_having_to_select(self, semantic_parse_info: SemanticParseInfo):
        original_sql = semantic_parse_info.sql_info.corrected_s2sql
        
        if not SqlSelectHelper.has_aggregate_function(original_sql):
            return
        
        expressions = SqlSelectHelper.get_having_expression(original_sql)
        if expressions:
            updated_sql = SqlAddHelper.add_function_to_select(original_sql, expressions)
            semantic_parse_info.sql_info.corrected_s2sql = updated_sql

# 示例用法
if __name__ == "__main__":
    # 初始化环境变量
    os.environ["S2_CORRECTOR_ADDITIONAL_INFORMATION"] = "true"
    
    # 创建测试对象
    corrector = HavingCorrector()
    context = ChatQueryContext()
    parse_info = SemanticParseInfo()
    parse_info.sql_info.corrected_s2sql = "SELECT department, SUM(sales) FROM transactions GROUP BY department"
    
    # 执行修正
    corrector.do_correct(context, parse_info)
    
    print("修正后的 SQL:")
    print(parse_info.sql_info.corrected_s2sql)