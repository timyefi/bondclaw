import pandas as pd
import numpy as np
import sqlalchemy
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# --- 数据库配置 ---
def get_db_connection():
    """创建数据库连接"""
    sql_engine = sqlalchemy.create_engine(
        'mysql+pymysql://%s:%s@%s:%s/%s' % (
            'hz_work',
            'Hzinsights2015',
            'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            '3306',
            'bond',
        ), poolclass=sqlalchemy.pool.NullPool
    )
    return sql_engine.connect()

# --- 配置参数 ---
TEN_YEAR_BOND_CODE = 'L001619604'  # 10年国债代码（可根据需要修改为1年期：L001618296）
LOOKBACK_DAYS = 90  # 回看天数
TABLE_NAME = 'market_concentration_90pct'  # 结果保存表名

def calculate_90pct_concentration(df_period):
    """
    计算90%行情时间占比指标
    
    Args:
        df_period: 包含'CLOSE'列的DataFrame，已按时间排序
    
    Returns:
        float: 90%行情时间占比（0-1之间的值）
    """
    if len(df_period) < 2:
        return None
    
    # 计算每日收益率变化 (BP)
    df_period = df_period.copy()
    df_period['change_bp'] = df_period['CLOSE'].diff() * 100
    df_period = df_period.dropna(subset=['change_bp'])
    
    if len(df_period) == 0:
        return None
    
    changes_bp = df_period['change_bp'].values
    
    # 分离正值和负值变化的绝对值
    positive_changes_abs = np.abs(changes_bp[changes_bp > 0])
    negative_changes_abs = np.abs(changes_bp[changes_bp < 0])
    
    concentration_ratios = []
    
    # 计算正值变化的90%集中度
    if len(positive_changes_abs) > 0:
        positive_sorted = np.sort(positive_changes_abs)[::-1]  # 大到小排序
        positive_cumsum = np.cumsum(positive_sorted)
        total_positive = positive_cumsum[-1]
        
        if total_positive > 0:
            # 找到累计和达到总和90%的位置
            target_90pct = 0.9 * total_positive
            days_for_90pct = np.argmax(positive_cumsum >= target_90pct) + 1
            concentration_ratio_positive = days_for_90pct / len(positive_sorted)
            concentration_ratios.append(concentration_ratio_positive)
    
    # 计算负值变化的90%集中度
    if len(negative_changes_abs) > 0:
        negative_sorted = np.sort(negative_changes_abs)[::-1]  # 大到小排序
        negative_cumsum = np.cumsum(negative_sorted)
        total_negative = negative_cumsum[-1]
        
        if total_negative > 0:
            # 找到累计和达到总和90%的位置
            target_90pct = 0.9 * total_negative
            days_for_90pct = np.argmax(negative_cumsum >= target_90pct) + 1
            concentration_ratio_negative = days_for_90pct / len(negative_sorted)
            concentration_ratios.append(concentration_ratio_negative)
    
    # 计算两个比例的平均值
    if len(concentration_ratios) > 0:
        avg_concentration = np.mean(concentration_ratios)
        return avg_concentration/2
    else:
        return None

def get_latest_data_date(cursor):
    """获取数据库中最新的数据日期"""
    try:
        query = f"""
        SELECT MAX(dt) as latest_date 
        FROM bond.marketinfo_curve 
        WHERE trade_code = '{TEN_YEAR_BOND_CODE}'
        """
        result = pd.read_sql(query, cursor)
        latest_date = result['latest_date'].iloc[0]
        if pd.isna(latest_date):
            return None
        return pd.to_datetime(latest_date).date()
    except Exception as e:
        print(f"获取最新数据日期失败: {e}")
        return None

def get_yield_data(cursor, end_date, days_back=LOOKBACK_DAYS):
    """
    获取指定日期往前days_back天的收益率数据
    
    Args:
        cursor: 数据库连接
        end_date: 结束日期
        days_back: 往前追溯的天数
    
    Returns:
        DataFrame: 包含dt和CLOSE列的数据
    """
    start_date = end_date - timedelta(days=days_back)
    
    query = f"""
    SELECT dt, CLOSE 
    FROM bond.marketinfo_curve 
    WHERE trade_code = '{TEN_YEAR_BOND_CODE}' 
    AND dt BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY dt
    """
    
    try:
        df = pd.read_sql(query, cursor)
        df['dt'] = pd.to_datetime(df['dt'])
        df['CLOSE'] = pd.to_numeric(df['CLOSE'], errors='coerce')
        df = df.dropna(subset=['CLOSE'])
        return df
    except Exception as e:
        print(f"获取收益率数据失败: {e}")
        return pd.DataFrame()

def check_indicator_exists(cursor, target_date):
    """检查指定日期的指标是否已存在"""
    try:
        query = f"""
        SELECT COUNT(*) as count 
        FROM bond.{TABLE_NAME} 
        WHERE dt = '{target_date}'
        """
        result = pd.read_sql(query, cursor)
        return result['count'].iloc[0] > 0
    except:
        # 表可能不存在，返回False
        return False

def create_table_if_not_exists(cursor):
    """创建结果保存表（如果不存在）"""
    try:
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS bond.{TABLE_NAME} (
            dt DATE PRIMARY KEY,
            concentration_90pct DECIMAL(10,6),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Market 90pct concentration indicator'
        """
        cursor.execute(create_table_sql)
        print(f"表 {TABLE_NAME} 已确保存在")
    except Exception as e:
        print(f"创建表失败: {e}")

def save_indicator_to_db(cursor, target_date, concentration_value):
    """保存指标到数据库"""
    try:
        # 使用 REPLACE INTO 来处理可能的重复数据
        insert_sql = f"""
        REPLACE INTO bond.{TABLE_NAME} (dt, concentration_90pct) 
        VALUES ('{target_date}', {concentration_value})
        """
        cursor.execute(insert_sql)
        cursor.connection.commit()
        print(f"已保存 {target_date} 的90%行情占比指标: {concentration_value:.4f}")
    except Exception as e:
        print(f"保存指标到数据库失败: {e}")

def main():
    """主函数"""
    print("开始计算90%行情时间占比指标...")
    print(f"使用债券代码: {TEN_YEAR_BOND_CODE}")
    print(f"回看天数: {LOOKBACK_DAYS}")
    
    # 连接数据库
    try:
        cursor = get_db_connection()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return
    
    try:
        # 创建表（如果不存在）
        create_table_if_not_exists(cursor)
        
        # 获取最新数据日期
        latest_date = get_latest_data_date(cursor)
        if latest_date is None:
            print("无法获取最新数据日期")
            return
        
        # 计算目标日期（昨天）
        yesterday = latest_date
        print(f"计算目标日期: {yesterday}")
        
        # 检查是否已存在该日期的指标
        if check_indicator_exists(cursor, yesterday):
            print(f"日期 {yesterday} 的指标已存在，将进行更新")
        
        # 获取过去90天的数据
        df_data = get_yield_data(cursor, yesterday, LOOKBACK_DAYS)
        
        if df_data.empty:
            print("未获取到足够的历史数据")
            return
        
        print(f"获取到 {len(df_data)} 天的历史数据，日期范围: {df_data['dt'].min().date()} 到 {df_data['dt'].max().date()}")
        
        # 计算90%行情时间占比
        concentration_90pct = calculate_90pct_concentration(df_data)
        
        if concentration_90pct is None:
            print("计算90%行情时间占比失败：数据不足或无有效变化")
            return
        
        print(f"计算完成，90%行情时间占比: {concentration_90pct:.4f} ({concentration_90pct*100:.2f}%)")
        
        # 保存到数据库
        save_indicator_to_db(cursor, yesterday, concentration_90pct)
        
        # 显示最近几天的指标（用于验证）
        try:
            recent_query = f"""
            SELECT dt, concentration_90pct 
            FROM bond.{TABLE_NAME} 
            ORDER BY dt DESC 
            LIMIT 5
            """
            recent_data = pd.read_sql(recent_query, cursor)
            print("\n最近5天的指标值:")
            print(recent_data.to_string(index=False))
        except:
            print("无法查询最近的指标值")
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
    finally:
        cursor.close()
        print("数据库连接已关闭")

if __name__ == '__main__':
    main() 