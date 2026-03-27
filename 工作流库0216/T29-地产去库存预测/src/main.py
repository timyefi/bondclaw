
import warnings
warnings.filterwarnings('ignore')


import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
import os
import sys
# 添加项目根目录到Python路径
def get_connection_url(db_config,db_type):
        """
        获取数据库连接URL
        
        Args:
            driver: 数据库驱动，例如 'pymysql' for MySQL, 'psycopg2' for PostgreSQL
        
        Returns:
            str: SQLAlchemy连接URL
        """
        if db_type == 'mysql':
            driver = 'pymysql'
            return f'mysql+{driver}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}'
        elif db_type == 'postgresql':
            driver = 'psycopg2'
            return f'postgresql+{driver}://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}'
        else:
            raise ValueError(f"不支持的数据库类型: {db_config['db_type']}")

def get_edb_data(trade_codes):
    """获取edb数据库中的时间序列数据"""
    db_config = {
        'user': 'hz_work',
        'password': 'Hzinsights2015',
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': '3306',
        'database': 'edb',
        'charset': 'utf8mb4'
    }
    engine = create_engine(get_connection_url(db_config,'mysql'))
    # 将trade_codes列表转换为元组以满足SQLAlchemy的要求
    placeholders = ','.join(['%s'] * len(trade_codes))
    query = f"SELECT dt, trade_code, close FROM edb.edbdata WHERE trade_code IN ({placeholders}) ORDER BY dt"

    print("正在从edb数据库获取数据...")
    df = pd.read_sql(query, engine, params=tuple(trade_codes))
    df['dt'] = pd.to_datetime(df['dt'])
    
    # 转换为宽表格式
    pivot_df = df.pivot(index='dt', columns='trade_code', values='close')
    print(f"获取数据成功，数据范围：{pivot_df.index.min()} 到 {pivot_df.index.max()}")
    
    return pivot_df


def calculate_monthly_values(df):
    """计算月度值和累计值"""
    print("计算月度值和历史累计值...")
    
    # 重置1月份的累计值（年初归零）
    df_monthly = pd.DataFrame(index=df.index)
    
    for col in ['S0049264', 'S0049296', 'S0049585', 'S0029669']:
        df_reset = df[col].copy()
        
        # 检测年初重置点（当前值小于前一个值时）
        # 注意：可能存在1月份数据断开的情况，1月可能不公布数据，2月集中公布1-2月的累计值
        diff_values = df_reset.diff()
        reset_points = diff_values < 0
        
        # 计算当月值
        monthly_values = diff_values.fillna(df_reset)
        # 在重置点用原值作为当月值
        monthly_values[reset_points] = df_reset[reset_points]
        
        df_monthly[f'{col}_monthly'] = monthly_values
    
    # 计算历史累计值
    df_monthly['S0049264_hist_cum'] = df_monthly['S0049264_monthly'].cumsum()
    df_monthly['S0049296_hist_cum'] = df_monthly['S0049296_monthly'].cumsum()
    
    return df_monthly


def calculate_inventory_estimate(df, df_monthly):
    """计算住宅库存估算值"""
    print("计算住宅库存估算值...")
    
    # 住宅库存估算值 = S0029674 * (期房历史累计 + 现房历史累计) / 期房历史累计
    inventory_estimate = df['S0029674'] * \
        (df_monthly['S0049296_hist_cum'] + df_monthly['S0049264_hist_cum']) / \
        df_monthly['S0049296_hist_cum']
    
    return inventory_estimate


def calculate_rolling_indicators(df_monthly):
    """计算12个月滚动指标"""
    print("计算12个月滚动指标...")
    
    rolling_data = pd.DataFrame(index=df_monthly.index)
    
    # 销售12个月滚动
    rolling_data['s1'] = df_monthly['S0049264_monthly'].rolling(window=12, min_periods=1).sum()  # 现房销售
    rolling_data['s2'] = df_monthly['S0049296_monthly'].rolling(window=12, min_periods=1).sum()  # 期房销售
    rolling_data['s3'] = rolling_data['s1'] + rolling_data['s2']  # 总销售
    
    # 竣工12个月滚动
    rolling_data['completion_12m'] = df_monthly['S0049585_monthly'].rolling(window=12, min_periods=1).sum()
    
    # 新开工12个月滚动
    rolling_data['new_starts_12m'] = df_monthly['S0029669_monthly'].rolling(window=12, min_periods=1).sum()
    
    return rolling_data


def trend_forecast(data, forecast_start_date, forecast_end_date):
    """趋势线性回归预测"""
    print("执行趋势线性回归预测...")
    
    # 将预测开始日期转换为datetime类型以确保正确的比较
    forecast_start_dt = pd.to_datetime(forecast_start_date)
    
    # 准备训练数据（指定日期及之后）
    train_data = data[data.index >= forecast_start_dt].dropna()
    
    if len(train_data) < 2:
        # 如果指定日期后的数据不足，尝试使用最近的24个月数据
        print("指定日期后的训练数据点不足，尝试使用最近的24个月数据...")
        train_data = data.tail(24).dropna()
        
        if len(train_data) < 2:
            raise ValueError(f"训练数据点不足，无法进行预测。数据范围: {data.index.min()} 到 {data.index.max()}")
    
    # 创建时间变量
    train_data = train_data.copy()
    train_data['time'] = range(len(train_data))
    
    # 创建预测日期范围
    last_date = data.index.max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), 
                                end=forecast_end_date, freq='M')
    
    # 线性回归模型
    model = LinearRegression()
    X_train = train_data[['time']]
    y_train = train_data.iloc[:, 0]  # 第一列数据
    
    model.fit(X_train, y_train)
    
    # 预测
    future_time = range(len(train_data), len(train_data) + len(future_dates))
    future_values = model.predict(np.array(future_time).reshape(-1, 1))
    
    # 创建预测结果
    forecast_df = pd.DataFrame(index=future_dates, data=future_values, columns=[data.columns[0]])
    
    return forecast_df


def sales_completion_destocking_forecast(inventory_estimate, rolling_data, forecast_start_date, forecast_end_date):
    """销售-竣工去化预测"""
    print("执行销售-竣工去化预测...")
    
    # 获取销售和竣工的趋势预测
    s3_forecast = trend_forecast(rolling_data[['s3']], forecast_start_date, forecast_end_date)
    completion_forecast = trend_forecast(rolling_data[['completion_12m']], forecast_start_date, forecast_end_date)
    
    # 计算月度销售和竣工
    monthly_sales = s3_forecast['s3'] / 12
    monthly_completion = completion_forecast['completion_12m'] / 12
    
    # 计算月度去化值（销售 - 竣工）
    monthly_destocking = monthly_sales - monthly_completion
    
    # 从最后实际库存开始，逐月计算
    last_inventory = inventory_estimate.dropna().iloc[-1]
    inventory_forecast = []
    
    for destocking in monthly_destocking:
        if len(inventory_forecast) == 0:
            new_inventory = last_inventory - destocking
        else:
            new_inventory = inventory_forecast[-1] - destocking
        inventory_forecast.append(new_inventory)
    
    return pd.Series(inventory_forecast, index=monthly_destocking.index)


def create_final_dataframe(df, rolling_data, inventory_estimate, forecast_start_date, forecast_end_date):
    """创建最终结果DataFrame"""
    print("创建最终结果DataFrame...")
    
    # 1. 趋势预测
    inventory_trend_forecast = trend_forecast(
        inventory_estimate.to_frame('inventory'), forecast_start_date, forecast_end_date
    )
    s3_trend_forecast = trend_forecast(rolling_data[['s3']], forecast_start_date, forecast_end_date)
    completion_trend_forecast = trend_forecast(rolling_data[['completion_12m']], forecast_start_date, forecast_end_date)
    new_starts_trend_forecast = trend_forecast(rolling_data[['new_starts_12m']], forecast_start_date, forecast_end_date)
    
    # 2. 销售-竣工去化预测
    inventory_destocking_forecast = sales_completion_destocking_forecast(
        inventory_estimate, rolling_data, forecast_start_date, forecast_end_date
    )
    
    # 3. 合并历史和预测数据
    all_dates = pd.date_range(start=df.index.min(), end=forecast_end_date, freq='M')
    final_df = pd.DataFrame(index=all_dates)
    
    # 住宅库存趋势预测口径
    final_df['住宅库存趋势预测口径'] = pd.concat([
        inventory_estimate, 
        inventory_trend_forecast['inventory']
    ]).reindex(all_dates)
    
    # 住宅库存去化预测口径
    final_df['住宅库存去化预测口径'] = pd.concat([
        inventory_estimate,
        inventory_destocking_forecast
    ]).reindex(all_dates)
    
    # 住宅销售12个月滚动
    final_df['住宅销售12个月滚动'] = pd.concat([
        rolling_data['s3'],
        s3_trend_forecast['s3']
    ]).reindex(all_dates)
    
    # 住宅竣工12个月滚动
    final_df['住宅竣工12个月滚动'] = pd.concat([
        rolling_data['completion_12m'],
        completion_trend_forecast['completion_12m']
    ]).reindex(all_dates)
    
    # 住宅新开工12个月滚动
    final_df['住宅新开工12个月滚动'] = pd.concat([
        rolling_data['new_starts_12m'],
        new_starts_trend_forecast['new_starts_12m']
    ]).reindex(all_dates)
    
    # 计算库销比
    final_df['库销比（趋势推演）'] = final_df['住宅库存趋势预测口径'] / (final_df['住宅销售12个月滚动'] / 12)
    final_df['库销比（销售-竣工去化）'] = final_df['住宅库存去化预测口径'] / (final_df['住宅销售12个月滚动'] / 12)
    
    return final_df


# 定义数据代码
trade_codes = [
    'S0029674',  # 中国:商品房待售面积:住宅:累计值
    'S0049264',  # 商品房销售面积:住宅:现房:累计值
    'S0049296',  # 商品房销售面积:住宅:期房:累计值
    'S0049585',  # 中国:房屋竣工面积:住宅:累计值
    'S0029669',  # 中国:房屋新开工面积:住宅:累计值
]

# 预测参数
# 预测开始日期为当前日期的3年前
import datetime
current_date = datetime.date.today()
forecast_start_date = (current_date - datetime.timedelta(days=3*365)).strftime('%Y-%m-%d')
forecast_end_date = '2027-12-31'


# 1. 获取数据
df = get_edb_data(trade_codes)

# 2. 计算月度值
df_monthly = calculate_monthly_values(df)

# 3. 计算库存估算值
inventory_estimate = calculate_inventory_estimate(df, df_monthly)

# 4. 计算滚动指标
rolling_data = calculate_rolling_indicators(df_monthly)

# 5. 创建最终结果
final_df = create_final_dataframe(
    df, rolling_data, inventory_estimate, 
    forecast_start_date, forecast_end_date
)
