import pandas as pd
import os

# 临时存储上传的文件
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}  # 允许的文件扩展名

def allowed_file(filename: str) ->bool:
    """
    检查文件扩展名是否合法
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def jug_file_type(file_path: str) -> pd.DataFrame:
#     """
#     判断表格文件的类型，返回不同 DataFrame
#     """
#     file_extension = os.path.splitext(file_path)[1].lower()  # 获取文件扩展名并转换为小写
#     if file_extension in ['.xls', '.xlsx']:
#         df = pd.read_excel(file_path)
#     elif file_extension == '.csv':
#         df = pd.read_csv(file_path)
#     else:
#         raise ValueError(f"不支持的文件格式: {file_extension}")
#     return df

def jug_file_type(file_path: str) -> dict:
    """
    判断表格文件的类型，返回不同工作表的数据字典
    对于Excel文件：返回 {sheet_name: DataFrame}
    对于CSV文件：返回 {'data': DataFrame}
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension in ['.xls', '.xlsx']:
        # 读取所有工作表
        return pd.read_excel(file_path, sheet_name=None)
    
    elif file_extension == '.csv':
        # 单表文件返回字典格式
        return {'data': pd.read_csv(file_path)}
    
    else:
        raise ValueError(f"不支持的文件格式: {file_extension}")

def detect_date_col(df: pd.DataFrame) -> list:
    """
    混合类型日期列检测
    """
    
    date_cols = []
    for col in df.columns:
        # 浮点型处理
        if df[col].dtype == float:
            int_ratio = (df[col].apply(lambda x: x.is_integer())).mean()
            sample = df[col].head(100).dropna().astype(int)
            
            min_date = pd.to_datetime('1900-01-01').toordinal() + 2
            max_date = pd.to_datetime('today').toordinal()
            
            valid_float = sample.apply(
                lambda x: min_date <= (x + 2) <= max_date
            ).mean()
            
            if int_ratio != 0 and valid_float != 0:
                date_cols.append(col)
        # datetime型处理
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        # 字符串型处理
        elif df[col].dtype == object:
            date_like = df[col].apply(
                lambda s: pd.to_datetime(s, errors='coerce', format='%Y%m%d') is not pd.NaT
                or pd.to_datetime(s, errors='coerce') is not pd.NaT
            ).mean()
            if date_like != 0:
                date_cols.append(col)
    return date_cols