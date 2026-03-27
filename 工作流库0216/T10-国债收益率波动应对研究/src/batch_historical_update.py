import pandas as pd
import numpy as np
import sqlalchemy
from datetime import datetime, timedelta
import warnings
import argparse
import sys
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
TEN_YEAR_BOND_CODE = 'L001619604'  # 10年国债代码
ONE_YEAR_BOND_CODE = 'L001618296'  # 1年国债代码
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
        return avg_concentration
    else:
        return None

def get_yield_data_for_date(cursor, bond_code, target_date, days_back=LOOKBACK_DAYS):
    """
    获取指定日期往前days_back天的收益率数据
    
    Args:
        cursor: 数据库连接
        bond_code: 债券代码
        target_date: 目标日期
        days_back: 往前追溯的天数
    
    Returns:
        DataFrame: 包含dt和CLOSE列的数据
    """
    start_date = target_date - timedelta(days=days_back)
    
    query = f"""
    SELECT dt, CLOSE 
    FROM bond.marketinfo_curve 
    WHERE trade_code = '{bond_code}' 
    AND dt BETWEEN '{start_date}' AND '{target_date}'
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

def get_date_range_from_db(cursor, bond_code):
    """获取数据库中指定债券的日期范围"""
    try:
        query = f"""
        SELECT MIN(dt) as min_date, MAX(dt) as max_date 
        FROM bond.marketinfo_curve 
        WHERE trade_code = '{bond_code}'
        """
        result = pd.read_sql(query, cursor)
        min_date = pd.to_datetime(result['min_date'].iloc[0]).date() if not pd.isna(result['min_date'].iloc[0]) else None
        max_date = pd.to_datetime(result['max_date'].iloc[0]).date() if not pd.isna(result['max_date'].iloc[0]) else None
        return min_date, max_date
    except Exception as e:
        print(f"获取日期范围失败: {e}")
        return None, None

def get_existing_indicator_dates(cursor):
    """获取已存在的指标日期列表"""
    try:
        query = f"""
        SELECT dt FROM bond.{TABLE_NAME} ORDER BY dt
        """
        result = pd.read_sql(query, cursor)
        return set(pd.to_datetime(result['dt']).dt.date.tolist()) if not result.empty else set()
    except:
        # 表可能不存在
        return set()

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
        insert_sql = f"""
        REPLACE INTO bond.{TABLE_NAME} (dt, concentration_90pct) 
        VALUES ('{target_date}', {concentration_value})
        """
        cursor.execute(insert_sql)
        return True
    except Exception as e:
        print(f"保存指标到数据库失败 ({target_date}): {e}")
        return False

def generate_date_list(start_date, end_date):
    """生成日期列表"""
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    return date_list

def batch_update_historical_indicators(cursor, bond_code, start_date, end_date, force_update=False):
    """
    批量更新历史指标
    
    Args:
        cursor: 数据库连接
        bond_code: 债券代码
        start_date: 起始日期
        end_date: 结束日期
        force_update: 是否强制更新已存在的数据
    """
    print(f"开始批量更新历史90%行情占比指标...")
    print(f"债券代码: {bond_code}")
    print(f"日期范围: {start_date} 到 {end_date}")
    print(f"强制更新: {'是' if force_update else '否'}")
    
    # 获取已存在的指标日期
    existing_dates = get_existing_indicator_dates(cursor) if not force_update else set()
    print(f"数据库中已存在 {len(existing_dates)} 个指标日期")
    
    # 生成需要处理的日期列表
    all_dates = generate_date_list(start_date, end_date)
    target_dates = [d for d in all_dates if force_update or d not in existing_dates]
    
    print(f"需要处理 {len(target_dates)} 个日期")
    
    if not target_dates:
        print("没有需要处理的日期，退出。")
        return
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, target_date in enumerate(target_dates):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"进度: {i + 1}/{len(target_dates)} ({(i + 1) / len(target_dates) * 100:.1f}%)")
        
        # 获取数据
        df_data = get_yield_data_for_date(cursor, bond_code, target_date, LOOKBACK_DAYS)
        
        if df_data.empty or len(df_data) < 10:  # 至少需要10天数据
            skip_count += 1
            continue
        
        # 计算指标
        concentration_90pct = calculate_90pct_concentration(df_data)
        
        if concentration_90pct is None:
            skip_count += 1
            continue
        
        # 保存到数据库
        if save_indicator_to_db(cursor, target_date, concentration_90pct):
            success_count += 1
        else:
            error_count += 1
    
    # 提交所有更改
    try:
        cursor.connection.commit()
        print(f"\n批量更新完成!")
        print(f"成功: {success_count} 个")
        print(f"跳过: {skip_count} 个")
        print(f"错误: {error_count} 个")
    except Exception as e:
        print(f"提交数据失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量补充历史90%行情占比指标')
    parser.add_argument('--start-date', type=str, help='起始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--bond-code', type=str, default=TEN_YEAR_BOND_CODE, 
                       help=f'债券代码 (默认: {TEN_YEAR_BOND_CODE})')
    parser.add_argument('--days', type=int, help='从最新数据日期往前推多少天')
    parser.add_argument('--force', action='store_true', help='强制更新已存在的数据')
    
    args = parser.parse_args()
    
    # 连接数据库
    try:
        cursor = get_db_connection()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return
    
    try:
        # 创建表
        create_table_if_not_exists(cursor)
        
        # 确定日期范围
        if args.start_date and args.end_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        elif args.days:
            # 从数据库获取最新日期
            min_date, max_date = get_date_range_from_db(cursor, args.bond_code)
            if max_date is None:
                print("无法获取数据库中的日期范围")
                return
            end_date = max_date
            start_date = end_date - timedelta(days=args.days)
        else:
            # 默认：处理所有可用数据
            min_date, max_date = get_date_range_from_db(cursor, args.bond_code)
            if min_date is None or max_date is None:
                print("无法获取数据库中的日期范围")
                return
            # 从最早日期+90天开始（确保有足够的历史数据）
            start_date = min_date + timedelta(days=LOOKBACK_DAYS)
            end_date = max_date
        
        if start_date > end_date:
            print("起始日期不能晚于结束日期")
            return
        
        # 执行批量更新
        batch_update_historical_indicators(cursor, args.bond_code, start_date, end_date, args.force)
        
        # 显示最近几天的指标
        try:
            recent_query = f"""
            SELECT dt, concentration_90pct 
            FROM bond.{TABLE_NAME} 
            ORDER BY dt DESC 
            LIMIT 10
            """
            recent_data = pd.read_sql(recent_query, cursor)
            print("\n最近10天的指标值:")
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