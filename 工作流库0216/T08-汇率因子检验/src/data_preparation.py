import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
import sqlalchemy
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pyarrow

warnings.filterwarnings('ignore')

# 设置pandas显示选项
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180)

# 数据库连接配置
sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
_cursor = sql_engine.connect()

# 设置时间范围
bd = '2015-01-01'
ed = datetime.now().strftime('%Y-%m-%d')

def get_edb_data(trade_code):
    """从edb.edbdata表获取数据"""
    sql = f"""
    SELECT DT as date, close as value 
    FROM edb.edbdata
    WHERE trade_code='{trade_code}'
    AND DT>='{bd}' AND DT <= '{ed}'
    ORDER BY DT
    """
    df = pd.read_sql(sql, _cursor)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_stock_index_data(trade_code):
    """从stock.marketinfo_index表获取数据"""
    sql = f"""
    SELECT DT as date, close as value 
    FROM stock.indexcloseprice
    WHERE trade_code='{trade_code}'
    AND DT>='{bd}' AND DT <= '{ed}'
    ORDER BY DT
    """
    df = pd.read_sql(sql, _cursor)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_bond_curve_data(trade_code):
    """从bond.marketinfo_curve表获取数据"""
    sql = f"""
    SELECT DT as date, close as value 
    FROM bond.marketinfo_curve
    WHERE trade_code='{trade_code}'
    AND DT>='{bd}' AND DT <= '{ed}'
    ORDER BY DT
    """
    df = pd.read_sql(sql, _cursor)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_all_data():
    """获取所有数据并进行预处理"""
    # 获取因变量：人民币兑美元即期汇率
    usd_cny = get_edb_data('M0067855')
    usd_cny = usd_cny.rename(columns={'value': 'USD_CNY'})
    
    # 获取目标变量
    data_dict = {
        'DR007': get_edb_data('M1006337'),
        'GC007': get_edb_data('M1004515'),
        'CSI300': get_edb_data('M0020209'),
        'WIND_ALL_A': get_stock_index_data('881001.WI'),
        'SME_INDEX': get_stock_index_data('399101.SZ'),
        'HANG_SENG': get_stock_index_data('HSCI.HI'),
        'BOND_10Y': get_bond_curve_data('L001619604'),
        'BOND_1Y': get_bond_curve_data('L001618296'),
        'URBAN_BOND_5Y': get_bond_curve_data('L003759264')
    }
    
    # 合并所有数据
    merged_data = usd_cny.copy()
    for name, df in data_dict.items():
        df = df.rename(columns={'value': name})
        merged_data = pd.merge(merged_data, df, on='date', how='outer')
    
    # 按日期排序
    merged_data = merged_data.sort_values('date')
    
    # 处理缺失值
    merged_data = merged_data.fillna(method='ffill').fillna(method='bfill')
    
    # 转换股票指标：100-原指标
    stock_columns = ['CSI300', 'WIND_ALL_A', 'SME_INDEX', 'HANG_SENG']
    for col in stock_columns:
        merged_data[col] = 100 - merged_data[col]
    
    # 数据质量检查
    print("\n数据时间范围：")
    print(f"开始日期：{merged_data['date'].min()}")
    print(f"结束日期：{merged_data['date'].max()}")
    print(f"数据点数量：{len(merged_data)}")
    
    # 检查缺失值
    missing_values = merged_data.isnull().sum()
    if missing_values.any():
        print("\n存在缺失值的列：")
        print(missing_values[missing_values > 0])
    
    # 基本统计信息
    print("\n基本统计信息：")
    print(merged_data.describe())
    
    return merged_data

if __name__ == "__main__":
    # 获取数据
    data = get_all_data()
    
    # 保存处理后的数据
    data.to_parquet('processed_data.parquet', index=False)
    print("\n数据已保存到 processed_data.parquet")