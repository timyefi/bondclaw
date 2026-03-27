# -*- coding: utf-8 -*-
#用益信托网
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
import numpy as np
from sqlalchemy import inspect, MetaData, Table, Column, Text, text
from datetime import datetime, timedelta, date
from iFinDPy import *
from WindPy import w


sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)

w.start()
THS_iFinDLogin('nylc082','491448') 

TABLE_NAME = '金融资负'  # 将表名定义为常量

def check_and_fix_column_names():
    """检查金融资负表的列名，如果发现是col_0这样的格式就恢复正确的列名"""
    with sql_engine.begin() as connection:
        # 获取当前表的列名
        inspector = inspect(sql_engine)
        current_columns = [col['name'] for col in inspector.get_columns(TABLE_NAME)]
        
        # 检查是否存在col_开头的列名
        col_pattern_columns = [col for col in current_columns if col.startswith('col_')]
        if col_pattern_columns:
            print("检测到列名异常，开始修复...")
            # 查询原始的列名映射
            mapping_query = """
            SELECT DISTINCT column_name, column_comment 
            FROM information_schema.columns 
            WHERE table_schema = 'yq' 
            AND table_name = '金融资负' 
            AND column_comment != ''
            """
            mapping_df = pd.read_sql(mapping_query, connection)
            column_mapping = dict(zip(mapping_df['column_name'], mapping_df['column_comment']))
            
            # 修复列名
            for col in col_pattern_columns:
                if col in column_mapping:
                    connection.execute(text(f"ALTER TABLE `{TABLE_NAME}` CHANGE `{col}` `{column_mapping[col]}` FLOAT;"))
            print("列名修复完成")

def pro_data(wsd_data,dt_begin,code):
    if len(wsd_data)==1:
        wsd_data.index=[dt_begin]
    wsd_data.columns=[code]
    print(wsd_data)
    wsd_data = wsd_data.reset_index().rename(columns={'index': 'dt'})
    # 将 dt 列转换为 datetime 对象，并剔除转失败的行
    wsd_data['dt'] = pd.to_datetime(wsd_data['dt'], errors='coerce')
    wsd_data = wsd_data.dropna(subset=['dt'])
    
    # 过滤掉日期小于 dt0 的数据
    wsd_data = wsd_data[wsd_data['dt'] >= pd.to_datetime(dt_begin)]
    
    # 将 NaN 值替换为 None
    wsd_data = wsd_data.replace({pd.NA: None, pd.NaT: None, float('nan'): None})
    if wsd_data.empty:
        print("No valid data to insert.")
        return

    # 只保留每个月最新的数据
    wsd_data['year_month'] = wsd_data['dt'].dt.strftime('%Y-%m')
    wsd_data = wsd_data.sort_values('dt').groupby('year_month').last().reset_index()
    wsd_data = wsd_data.drop('year_month', axis=1)

    inspector = inspect(sql_engine)
    table_exists = inspector.has_table('金融资负')
    if table_exists:
        # 获取现有表的列名
        existing_columns = inspector.get_columns('金融资负')
        existing_columns_names = [col['name'] for col in existing_columns]
        # 获取df_news的列名
        wsd_data_columns = wsd_data.columns.tolist()

        # 检查并添加缺失的列
        for col in wsd_data_columns:
            if col not in existing_columns_names:
                with sql_engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE 金融资负 ADD COLUMN {col} Float;"))

        # 构建INSERT INTO ... ON DUPLICATE KEY UPDATE语句
        columns = wsd_data_columns
        insert_columns = ', '.join(columns)
        update_columns = ', '.join([f"{col} = VALUES({col})" for col in columns])

        insert_query = text(f"""
        INSERT INTO yq.金融资负 ({insert_columns})
        VALUES ({', '.join([f':{col}' for col in columns])})
        ON DUPLICATE KEY UPDATE {update_columns};
        """)
        # 打印调试信息
        print("Generated SQL Query:")
        print(insert_query)
        print("Sample Data Row:")
        print(wsd_data.iloc[0].to_dict())

        # 插入或更新数据
        with sql_engine.begin() as connection:
            for _, row in wsd_data.iterrows():
                try:
                    connection.execute(insert_query,  row.to_dict())
                except Exception as e:
                    print(f"Error inserting row: {row}")
                    print(e)
        print('更新完成')


# 获取当前日期  
current_date = datetime.now()
start_date = datetime(2024, 6, 1)

# 在开始处理数据前先检查并修复列名
check_and_fix_column_names()

# current_date1 = current_date - timedelta(days=1)
# dt=current_date1.strftime('%Y%m%d')
dt1=current_date.strftime('%Y-%m-%d')
# dt0=start_date.strftime('%Y-%m-%d')

def validate_data_quality(code, dt, value, connection):
    """验证数据质量，包括合理性检查和历史趋势分析"""
    # 获取最近6个月的有效历史数据
    history_query = f"""
    SELECT dt, {code} as value
    FROM yq.金融资负
    WHERE {code} IS NOT NULL AND {code} != ''
    AND dt <= :dt
    ORDER BY dt DESC
    LIMIT 6
    """
    history = pd.read_sql(text(history_query), connection, params={'dt': dt})
    
    if history.empty:
        return True, None
    
    # 1. 计算历史变化率（只考虑有效数据之间的变化）
    history['value_change'] = history['value'].pct_change() * -1  # 因为是倒序排列所以要乘-1
    
    # 2. 计算历史统计指标（忽略空值）
    mean_change = history['value_change'].mean()
    std_change = history['value_change'].std()
    
    # 3. 计算当前值相对于最近有效值的变化率
    if len(history) > 1:
        current_change = (value - history['value'].iloc[0]) / history['value'].iloc[0]
        
        # 4. 设置异常阈值（3个标准差）
        threshold = 3 * std_change if not pd.isna(std_change) else 1.0  # 如果没有足够的历史数据，使用100%作为默认阈值
        
        # 5. 检查是否异常
        if abs(current_change) > abs(threshold):
            return False, f"数据变化率({current_change:.2%})超过阈值({threshold:.2%})"
            
        # 6. 检查是否与历史趋势相反
        if len(history) >= 3:
            # 只考虑有效的变化率
            valid_changes = history['value_change'].dropna()
            if not valid_changes.empty:
                historical_trend = np.sign(valid_changes.mean())
                current_trend = np.sign(current_change)
                if historical_trend * current_trend < 0 and abs(current_change) > abs(valid_changes.mean()) * 2:
                    return False, f"数据变化方向与历史趋势相反且变化幅度({abs(current_change):.2%})超过历史平均({abs(valid_changes.mean()):.2%})的2倍"
    
    return True, None

def check_data_version(code, dt, value, connection):
    """检查数据版本，判断是否需要更新"""
    version_query = """
    SELECT 
        a.value,
        a.fetch_time,
        a.status,
        (SELECT COUNT(*) 
         FROM 金融资负_更新日志 b 
         WHERE b.code = a.code 
         AND b.dt = a.dt 
         AND b.fetch_time > a.fetch_time) as revision_count
    FROM 金融资负_更新日志 a
    WHERE a.code = :code 
    AND a.dt = :dt
    AND a.status != 'REJECTED'
    ORDER BY a.fetch_time DESC
    LIMIT 1
    """
    version_info = pd.read_sql(text(version_query), connection, params={'code': code, 'dt': dt})
    
    if version_info.empty:
        return True, 0, None  # 首次数据，允许更新
        
    last_version = version_info.iloc[0]
    
    # 如果修订次数过多，需要人工审核
    if last_version['revision_count'] >= 3:
        return False, last_version['revision_count'], "数据修订次数过多，需要人工审核"
        
    # 如果最后一次更新状态是PENDING，检查时间间隔
    if last_version['status'] == 'PENDING':
        time_since_last_update = datetime.now() - pd.to_datetime(last_version['fetch_time'])
        if time_since_last_update.total_seconds() < 3600:  # 1小时内
            return False, last_version['revision_count'], "距离上次更新时间过短"
            
    return True, last_version['revision_count'], None

def validate_and_log_data(code, dt, value, source, connection):
    """验证数据并记录日志"""
    current_time = datetime.now()
    status = 'PENDING'
    reason = None

    # 1. 检查数据版本
    can_update, revision_count, version_reason = check_data_version(code, dt, value, connection)
    if not can_update:
        status = 'REJECTED'
        reason = version_reason
        print(f"数据版本检查未通过: {reason}")
    else:
        # 2. 检查是否存在更新的数据
        check_query = """
        SELECT value, fetch_time, status
        FROM 金融资负_更新日志
        WHERE dt = :dt AND code = :code
        ORDER BY fetch_time DESC
        LIMIT 1
        """
        existing = pd.read_sql(text(check_query), connection, params={'dt': dt, 'code': code})
        
        if not existing.empty:
            last_update = existing.iloc[0]
            # 如果在同一天内已经有更新记录
            if last_update['fetch_time'].date() == current_time.date():
                if last_update['value'] == value:
                    status = 'REJECTED'
                    reason = '同一天内重复推送相同数据'
                else:
                    status = 'PENDING'
                    reason = '同一天内数据值发生变化'
            else:
                # 检查是否是重复推送上月数据
                if last_update['value'] == value:
                    status = 'REJECTED'
                    reason = '重复推送上月数据'
        
        # 3. 进行数据质量验证
        if status == 'PENDING':
            is_valid, quality_reason = validate_data_quality(code, dt, value, connection)
            if not is_valid:
                status = 'REJECTED'
                reason = quality_reason
    
    # 记录日志，添加版本信息
    log_query = """
    INSERT INTO 金融资负_更新日志 (dt, code, value, source, fetch_time, status, reason, revision_number)
    VALUES (:dt, :code, :value, :source, :fetch_time, :status, :reason, :revision_number)
    """
    connection.execute(text(log_query), {
        'dt': dt,
        'code': code,
        'value': value,
        'source': source,
        'fetch_time': current_time,
        'status': status,
        'reason': reason,
        'revision_number': revision_count + 1
    })
    
    # 如果是被拒绝的更新，记录到异常日志
    if status == 'REJECTED':
        log_anomaly(code, dt, value, source, reason, connection)
    
    return status == 'PENDING'

def log_anomaly(code, dt, value, source, reason, connection):
    """记录数据异常情况"""
    try:
        # 先确保临时表不存在
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_historical_data"))
        
        # 创建临时表存储历史数据
        create_temp_table = """
        CREATE TEMPORARY TABLE temp_historical_data AS (
            SELECT {code} as value
            FROM 金融资负
            WHERE dt <= :dt AND {code} IS NOT NULL
            ORDER BY dt DESC
            LIMIT 6
        )
        """
        
        # 创建临时表
        connection.execute(text(create_temp_table.format(code=code)), {
            'dt': dt
        })
        
        # 获取统计数据
        stats_query = """
        SELECT 
            MAX(CASE WHEN row_num = 1 THEN value END) as last_value,
            AVG(value) as historical_mean,
            STDDEV(value) as historical_std
        FROM (
            SELECT value, (@row_num := @row_num + 1) as row_num
            FROM temp_historical_data, (SELECT @row_num := 0) as r
        ) t
        """
        
        stats_df = pd.read_sql(text(stats_query), connection)
        last_value = stats_df['last_value'].iloc[0]
        historical_mean = stats_df['historical_mean'].iloc[0]
        historical_std = stats_df['historical_std'].iloc[0]
        
        # 计算变化率
        value_change = None
        if last_value is not None and last_value != 0:
            value_change = (value - last_value) / last_value
        
        # 插入异常日志
        insert_query = """
        INSERT INTO 金融资负_异常日志 (
            dt, code, value, source, detect_time, reason,
            last_value, value_change, historical_mean, historical_std
        ) VALUES (
            :dt, :code, :value, :source, :detect_time, :reason,
            :last_value, :value_change, :historical_mean, :historical_std
        )
        """
        
        connection.execute(text(insert_query), {
            'dt': dt,
            'code': code,
            'value': value,
            'source': source,
            'detect_time': datetime.now(),
            'reason': reason,
            'last_value': last_value,
            'value_change': value_change,
            'historical_mean': historical_mean,
            'historical_std': historical_std
        })
        
        # 清理临时表
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_historical_data"))
        
    except Exception as e:
        # 确保在发生错误时也清理临时表
        try:
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_historical_data"))
        except:
            pass
        print(f"记录异常日志时出错: {str(e)}")

def generate_data_quality_report(start_date=None, end_date=None, connection=None):
    """生成数据质量报告"""
    if connection is None:
        connection = sql_engine.connect()
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 先确保临时表不存在
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_daily_stats"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_rejection_reasons"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_anomaly_stats"))
        
        # 创建临时表存储每日统计数据
        create_daily_stats = """
        CREATE TEMPORARY TABLE temp_daily_stats AS (
            SELECT 
                DATE(fetch_time) as report_date,
                COUNT(*) as total_updates,
                SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_updates,
                COUNT(DISTINCT code) as affected_indicators,
                COUNT(DISTINCT CASE WHEN status = 'REJECTED' THEN code ELSE NULL END) as rejected_indicators
            FROM 金融资负_更新日志
            WHERE fetch_time BETWEEN :start_date AND :end_date
            GROUP BY DATE(fetch_time)
        )
        """
        
        # 创建临时表存储拒绝原因统计
        create_rejection_stats = """
        CREATE TEMPORARY TABLE temp_rejection_reasons AS (
            SELECT 
                DATE(fetch_time) as report_date,
                reason,
                COUNT(*) as reason_count
            FROM 金融资负_更新日志
            WHERE status = 'REJECTED' 
            AND fetch_time BETWEEN :start_date AND :end_date
            GROUP BY DATE(fetch_time), reason
        )
        """
        
        # 创建临时表存储异常统计
        create_anomaly_stats = """
        CREATE TEMPORARY TABLE temp_anomaly_stats AS (
            SELECT 
                DATE(detect_time) as report_date,
                COUNT(*) as anomaly_count,
                COUNT(DISTINCT code) as anomaly_indicators,
                AVG(ABS(value_change)) as avg_change_magnitude
            FROM 金融资负_异常日志
            WHERE detect_time BETWEEN :start_date AND :end_date
            GROUP BY DATE(detect_time)
        )
        """
        
        # 创建临时表
        connection.execute(text(create_daily_stats), {
            'start_date': start_date,
            'end_date': end_date
        })
        connection.execute(text(create_rejection_stats), {
            'start_date': start_date,
            'end_date': end_date
        })
        connection.execute(text(create_anomaly_stats), {
            'start_date': start_date,
            'end_date': end_date
        })
        
        # 最终查询
        report_query = """
        SELECT 
            d.report_date,
            d.total_updates,
            d.rejected_updates,
            d.affected_indicators,
            d.rejected_indicators,
            a.anomaly_count,
            a.anomaly_indicators,
            a.avg_change_magnitude,
            GROUP_CONCAT(CONCAT(r.reason, ': ', r.reason_count) SEPARATOR '; ') as rejection_details
        FROM temp_daily_stats d
        LEFT JOIN temp_anomaly_stats a ON d.report_date = a.report_date
        LEFT JOIN temp_rejection_reasons r ON d.report_date = r.report_date
        GROUP BY d.report_date
        ORDER BY d.report_date DESC
        """
        
        # 执行最终查询
        report_df = pd.read_sql(text(report_query), connection)
        
        # 清理临时表
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_daily_stats"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_rejection_reasons"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_anomaly_stats"))
        
        return report_df
        
    except Exception as e:
        # 确保在发生错误时也清理临时表
        try:
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_daily_stats"))
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_rejection_reasons"))
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_anomaly_stats"))
        except:
            pass
        print(f"生成数据质量报告时出错: {str(e)}")
        return pd.DataFrame()

def check_data_quality_alerts(connection=None):
    """检查是否需要发出数据质量警报"""
    if connection is None:
        connection = sql_engine.connect()
    
    # 1. 检查高频率拒绝
    rejection_alert_query = """
    SELECT 
        code,
        COUNT(*) as rejection_count,
        GROUP_CONCAT(DISTINCT reason SEPARATOR '; ') as reasons
    FROM 金融资负_更新日志
    WHERE status = 'REJECTED'
    AND fetch_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY code
    HAVING rejection_count >= 3
    """
    
    rejection_alerts = pd.read_sql(text(rejection_alert_query), connection)
    
    # 2. 检查异常值模式
    anomaly_alert_query = """
    SELECT 
        code,
        COUNT(*) as anomaly_count,
        AVG(ABS(value_change)) as avg_change,
        GROUP_CONCAT(DISTINCT reason SEPARATOR '; ') as reasons
    FROM 金融资负_异常日志
    WHERE detect_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY code
    HAVING anomaly_count >= 2
    """
    
    anomaly_alerts = pd.read_sql(text(anomaly_alert_query), connection)
    
    # 3. 检查数据更新延迟
    delay_alert_query = """
    SELECT 
        t.code,
        t.last_update_date,
        DATEDIFF(CURDATE(), t.last_update_date) as days_delay
    FROM (
        SELECT 
            code,
            MAX(dt) as last_update_date
        FROM 金融资负_更新日志
        WHERE status = 'PENDING'
        GROUP BY code
    ) t
    WHERE DATEDIFF(CURDATE(), t.last_update_date) > 45
    """
    
    delay_alerts = pd.read_sql(text(delay_alert_query), connection)
    
    alerts = {
        'rejection_alerts': rejection_alerts,
        'anomaly_alerts': anomaly_alerts,
        'delay_alerts': delay_alerts
    }
    
    return alerts

def monitor_data_quality():
    """监控数据质量并生成报告"""
    try:
        with sql_engine.begin() as connection:
            # 生成数据质量报告
            report = generate_data_quality_report(connection=connection)
            
            # 检查警报
            alerts = check_data_quality_alerts(connection=connection)
            
            # 记录监控结果
            monitoring_summary = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_indicators_monitored': len(code_list),
                'alerts': {
                    'high_rejection': len(alerts['rejection_alerts']),
                    'anomaly_patterns': len(alerts['anomaly_alerts']),
                    'update_delays': len(alerts['delay_alerts'])
                },
                'report_summary': {
                    'total_updates': report['total_updates'].sum(),
                    'total_rejections': report['rejected_updates'].sum(),
                    'affected_indicators': report['affected_indicators'].sum()
                }
            }
            
            # 将监控结果保存到数据库
            monitoring_query = """
            INSERT INTO 金融资负_监控日志 (
                monitor_time, 
                indicators_count,
                rejection_alerts,
                anomaly_alerts,
                delay_alerts,
                total_updates,
                total_rejections,
                report_data
            ) VALUES (
                :timestamp,
                :indicators_count,
                :rejection_alerts,
                :anomaly_alerts,
                :delay_alerts,
                :total_updates,
                :total_rejections,
                :report_data
            )
            """
            
            connection.execute(text(monitoring_query), {
                'timestamp': monitoring_summary['timestamp'],
                'indicators_count': monitoring_summary['total_indicators_monitored'],
                'rejection_alerts': monitoring_summary['alerts']['high_rejection'],
                'anomaly_alerts': monitoring_summary['alerts']['anomaly_patterns'],
                'delay_alerts': monitoring_summary['alerts']['update_delays'],
                'total_updates': monitoring_summary['report_summary']['total_updates'],
                'total_rejections': monitoring_summary['report_summary']['total_rejections'],
                'report_data': json.dumps(monitoring_summary)
            })
            
            return monitoring_summary, alerts, report
            
    except Exception as e:
        print(f"监控数据质量时出错: {str(e)}")
        return None, None, None

def compare_historical_data(code, start_date, end_date, connection):
    """比较指定时间段内的数据变化"""
    try:
        # 先确保临时表不存在
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_current_data"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_update_history"))
        
        # 创建临时表存储当前数据
        create_current_data = """
        CREATE TEMPORARY TABLE temp_current_data AS (
            SELECT dt, {code} as value
            FROM 金融资负
            WHERE dt BETWEEN :start_date AND :end_date
            AND {code} IS NOT NULL
        )
        """
        
        # 创建临时表存储更新历史
        create_update_history = """
        CREATE TEMPORARY TABLE temp_update_history AS (
            SELECT 
                dt,
                value,
                fetch_time,
                status,
                revision_number,
                source
            FROM 金融资负_更新日志
            WHERE code = :code
            AND dt BETWEEN :start_date AND :end_date
            ORDER BY dt, fetch_time
        )
        """
        
        # 创建临时表
        connection.execute(text(create_current_data.format(code=code)), {
            'start_date': start_date,
            'end_date': end_date
        })
        connection.execute(text(create_update_history), {
            'code': code,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # 最终查询
        compare_query = """
        SELECT 
            c.dt,
            c.value as current_value,
            GROUP_CONCAT(
                CONCAT(
                    DATE_FORMAT(h.fetch_time, '%Y-%m-%d %H:%i'),
                    '|',
                    h.value,
                    '|',
                    h.status,
                    '|',
                    h.source,
                    '|',
                    h.revision_number
                )
                ORDER BY h.fetch_time
                SEPARATOR ';'
            ) as update_history
        FROM temp_current_data c
        LEFT JOIN temp_update_history h ON c.dt = h.dt
        GROUP BY c.dt, c.value
        ORDER BY c.dt
        """
        
        # 执行最终查询
        history_df = pd.read_sql(text(compare_query), connection)
        
        # 清理临时表
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_current_data"))
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_update_history"))
        
        return history_df
        
    except Exception as e:
        # 确保在发生错误时也清理临时表
        try:
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_current_data"))
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_update_history"))
        except:
            pass
        print(f"比较历史数据时出错: {str(e)}")
        return pd.DataFrame()

def analyze_data_corrections(code, start_date=None, end_date=None, connection=None):
    """分析数据修正模式"""
    if connection is None:
        connection = sql_engine.connect()
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 先确保临时表不存在
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_value_changes"))
        
        # 创建临时表存储值变化
        create_value_changes = """
        CREATE TEMPORARY TABLE temp_value_changes AS (
            SELECT 
                dt,
                code,
                value,
                fetch_time,
                status,
                @prev_value := @curr_value as prev_value,
                @curr_value := value as curr_value,
                revision_number
            FROM 金融资负_更新日志,
            (SELECT @prev_value := NULL, @curr_value := NULL) as vars
            WHERE code = :code
            AND dt BETWEEN :start_date AND :end_date
            ORDER BY dt, fetch_time
        )
        """
        
        # 最终查询
        correction_query = """
        SELECT 
            dt,
            MIN(fetch_time) as first_update,
            MAX(fetch_time) as last_update,
            COUNT(*) as update_count,
            MIN(value) as min_value,
            MAX(value) as max_value,
            MAX(revision_number) as max_revision,
            SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejection_count,
            GROUP_CONCAT(
                CASE 
                    WHEN prev_value IS NOT NULL 
                    THEN CONCAT(
                        ROUND((value - prev_value) / prev_value * 100, 2),
                        '%'
                    )
                    ELSE NULL 
                END
                ORDER BY fetch_time
                SEPARATOR ','
            ) as value_changes
        FROM temp_value_changes
        GROUP BY dt
        HAVING update_count > 1
        ORDER BY dt DESC
        """
        
        # 创建临时表
        connection.execute(text(create_value_changes), {
            'code': code,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # 执行最终查询
        corrections_df = pd.read_sql(text(correction_query), connection)
        
        # 清理临时表
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_value_changes"))
        
        return corrections_df
        
    except Exception as e:
        # 确保在发生错误时也清理临时表
        try:
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_value_changes"))
        except:
            pass
        print(f"分析数据修正时出错: {str(e)}")
        return pd.DataFrame()

def track_data_revisions(code, dt, connection):
    """追踪特定数据点的修订历史"""
    try:
        # 先确保临时表不存在
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_revision_history"))
        
        # 创建临时表存储修订历史
        create_revision_history = """
        CREATE TEMPORARY TABLE temp_revision_history AS (
            SELECT 
                fetch_time,
                value,
                status,
                reason,
                source,
                revision_number,
                @prev_value := @curr_value as prev_value,
                @curr_value := value as curr_value
            FROM 金融资负_更新日志,
            (SELECT @prev_value := NULL, @curr_value := NULL) as vars
            WHERE code = :code AND dt = :dt
            ORDER BY fetch_time
        )
        """
        
        # 最终查询
        revision_query = """
        SELECT 
            fetch_time,
            value,
            status,
            reason,
            source,
            revision_number,
            CASE 
                WHEN prev_value IS NOT NULL 
                THEN ROUND((value - prev_value) / prev_value * 100, 2)
                ELSE NULL 
            END as change_percentage
        FROM temp_revision_history
        """
        
        # 创建临时表
        connection.execute(text(create_revision_history), {
            'code': code,
            'dt': dt
        })
        
        # 执行最终查询
        revisions_df = pd.read_sql(text(revision_query), connection)
        
        # 清理临时表
        connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_revision_history"))
        
        return revisions_df
        
    except Exception as e:
        # 确保在发生错误时也清理临时表
        try:
            connection.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_revision_history"))
        except:
            pass
        print(f"追踪数据修订时出错: {str(e)}")
        return pd.DataFrame()

def restore_historical_version(code, dt, target_revision, connection):
    """恢复到特定版本的数据"""
    # 首先获取目标版本的数据
    version_query = """
    SELECT value, source, fetch_time
    FROM 金融资负_更新日志
    WHERE code = :code 
    AND dt = :dt 
    AND revision_number = :revision
    AND status = 'PENDING'
    """
    
    version_data = pd.read_sql(text(version_query), connection, params={
        'code': code,
        'dt': dt,
        'revision': target_revision
    })
    
    if version_data.empty:
        print(f"未找到修订版本 {target_revision} 的有效数据")
        return False
        
    # 记录恢复操作
    restore_query = """
    INSERT INTO 金融资负_更新日志 (
        dt, code, value, source, fetch_time, status, reason, revision_number
    ) VALUES (
        :dt, :code, :value, :source, :fetch_time, 'PENDING', 
        :reason, (SELECT MAX(revision_number) + 1 FROM 金融资负_更新日志 WHERE code = :code AND dt = :dt)
    )
    """
    
    try:
        connection.execute(text(restore_query), {
            'dt': dt,
            'code': code,
            'value': version_data['value'].iloc[0],
            'source': version_data['source'].iloc[0],
            'fetch_time': datetime.now(),
            'reason': f"恢复到修订版本 {target_revision} (原始时间: {version_data['fetch_time'].iloc[0]})"
        })
        
        # 更新主表数据
        update_query = f"""
        UPDATE 金融资负
        SET {code} = :value
        WHERE dt = :dt
        """
        
        connection.execute(text(update_query), {
            'value': version_data['value'].iloc[0],
            'dt': dt
        })
        
        print(f"成功恢复到修订版本 {target_revision}")
        return True
        
    except Exception as e:
        print(f"恢复历史版本时出错: {str(e)}")
        return False

def get_data(code, type):
    try:
        # 修改查询以获取最近的有效数据
        query = f"""
        SELECT dt, {code} as value
        FROM yq.金融资负
        WHERE {code} IS NOT NULL AND {code} != ''
        ORDER BY dt DESC
        LIMIT 1
        """
        with sql_engine.begin() as connection:
            dates = pd.read_sql(query, con=connection)
        dt0 = dates['dt'].iloc[0] if not dates.empty else datetime(2015,1,31)
        last_value = dates['value'].iloc[0] if not dates.empty and not pd.isna(dates['value'].iloc[0]) else None
        dt0 = pd.to_datetime(dt0)  # 确保是datetime格式
        last_month_end = dt0 + pd.offsets.MonthEnd(0)  # 获取当月最后一天
        print(f"\n处理代码 {code}:")
        print(f"数据库最近有效记录: 日期={dt0.strftime('%Y-%m-%d')}, 值={last_value}")
    except Exception as e:
        print(f"获取历史数据时出错: {str(e)}")
        dt0=datetime(2015,1,31)
        last_month_end = dt0 + pd.offsets.MonthEnd(0)
        last_value = None

    if dt0<=current_date:
        # 在处理数据之前先检查数据质量警报和历史修订情况
        with sql_engine.begin() as connection:
            # 检查警报
            alerts = check_data_quality_alerts(connection)
            if code in alerts['rejection_alerts']['code'].values:
                print(f"警告: {code} 在过去24小时内有多次拒绝记录")
            if code in alerts['anomaly_alerts']['code'].values:
                print(f"警告: {code} 在过去24小时内有多次异常值记录")
            if code in alerts['delay_alerts']['code'].values:
                print(f"警告: {code} 的数据更新已经延迟")
            
            # 检查最近的数据修订情况
            recent_corrections = analyze_data_corrections(
                code, 
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'),
                connection
            )
            if not recent_corrections.empty:
                print(f"\n最近30天内的数据修订情况:")
                print(f"- 修订次数最多的日期: {recent_corrections['dt'].iloc[0]}, 次数: {recent_corrections['update_count'].iloc[0]}")
                print(f"- 最大修订幅度: {recent_corrections['value_changes'].iloc[0]}")
        
        if type==1:
            # Wind EDB接口 - 使用两个月的查询来确保获取日期信息
            # 扩大查询范围到3个月，以确保能获取到最近的有效数据
            last_month_start = (current_date.replace(day=1) - timedelta(days=90)).replace(day=1)
            error_code, wsd_data = w.edb(f"{code}", last_month_start.strftime('%Y-%m-%d'), current_date.strftime('%Y-%m-%d'), usedf=True)
            
            if error_code == 0 and not wsd_data.empty:
                try:
                    # 检查是否是单月数据格式（索引是代码）
                    if wsd_data.index[0] == code:
                        current_value = wsd_data['CLOSE'].iloc[0]
                        print(f"Wind返回单月数据: 值={current_value}")
                        print(f"对比已有值: 新值={current_value}, 已有值={last_value}")
                        
                        # 只有在值发生变化时才更新
                        if last_value is None or abs(current_value - last_value) > 0.01:
                            with sql_engine.begin() as connection:
                                if validate_and_log_data(code, dt0, current_value, 'Wind', connection):
                                    # 只有当验证通过时才更新数据
                                    pro_data(wsd_data, last_month_end.strftime('%Y-%m-%d'), code)
                                else:
                                    print(f"数据验证未通过，不进行更新")
                        else:
                            print(f"数据未变化，不更新")
                    else:
                        # 尝试将索引转换为日期类型
                        wsd_data.index = pd.to_datetime(wsd_data.index)
                        # 过滤掉空值并获取最新数据
                        valid_data = wsd_data.dropna()
                        if not valid_data.empty:
                            latest_date = valid_data.index.max()
                            latest_data = valid_data.loc[[latest_date]]
                            current_value = latest_data['CLOSE'].iloc[0]
                            
                            print(f"Wind返回数据: 日期={latest_date.strftime('%Y-%m-%d')}, 值={current_value}")
                            print(f"比较月份: Wind={latest_date.strftime('%Y-%m')}, 最近有效数据={last_month_end.strftime('%Y-%m')}")
                            
                            # 严格检查日期和值
                            is_new_month = pd.to_datetime(latest_date).to_period('M') > last_month_end.to_period('M')
                            is_value_changed = last_value is None or abs(current_value - last_value) > 0.01
                            
                            if is_new_month:
                                if is_value_changed:
                                    print(f"发现新数据: 新月份={latest_date.strftime('%Y-%m')}, 新值={current_value}, 最近有效值={last_value}")
                                    latest_data.index = [code]
                                    with sql_engine.begin() as connection:
                                        if validate_and_log_data(code, latest_date, current_value, 'Wind', connection):
                                            # 只有当验证通过时才更新数据
                                            pro_data(latest_data, last_month_end.strftime('%Y-%m-%d'), code)
                                        else:
                                            print(f"数据验证未通过，不进行更新")
                                else:
                                    print(f"拒绝更新: 虽然是新月份，但值未变化 (新值={current_value}, 最近有效值={last_value})")
                            else:
                                print(f"拒绝更新: 不是新月份 (Wind={latest_date.strftime('%Y-%m')}, 最近有效数据={last_month_end.strftime('%Y-%m')})")
                        else:
                            print(f"Wind返回的数据中没有有效值")
                except Exception as e:
                    print(f"处理Wind数据时出错: {str(e)}")
                    print("原始数据:")
                    print(wsd_data)
            else:
                print(f"Wind接口返回错误: {error_code}")
        else:
            # 同花顺接口
            # 扩大查询范围到3个月
            three_months_ago = last_month_end - pd.DateOffset(months=3)
            df = THS_EDB(code, '', three_months_ago.strftime('%Y-%m-%d'), current_date.strftime('%Y-%m-%d'))
            if df.data is not None:
                df = df.data
                if not df.empty and 'time' in df.columns:
                    try:
                        # 确保日期类型的正确转换
                        df['time'] = pd.to_datetime(df['time'])
                        # 过滤掉空值
                        df = df.dropna(subset=['value'])
                        if not df.empty:
                            latest_date = df['time'].max()
                            current_value = df.loc[df['time'] == latest_date, 'value'].iloc[0]
                            
                            print(f"同花顺返回数据: 日期={latest_date.strftime('%Y-%m-%d')}, 值={current_value}")
                            print(f"比较月份: 同花顺={latest_date.strftime('%Y-%m')}, 最近有效数据={last_month_end.strftime('%Y-%m')}")
                            
                            # 修改日期比较逻辑，确保类型一致
                            latest_period = latest_date.to_period('M')
                            print(f'latest_period:{latest_period}')    
                            last_month_period = last_month_end.to_period('M')
                            print(f'last_month_period:{last_month_period}')
                            is_new_month = latest_period > last_month_period
                            
                            # 确保数值比较时的类型一致
                            current_value = float(current_value)
                            print(f'current_value:{current_value}')
                            is_value_changed = last_value is None or abs(float(current_value) - float(last_value)) > 0.01
                            print(f'is_value_changed:{is_value_changed}')
                            
                            if is_new_month:
                                if is_value_changed:
                                    print(f"发现新数据: 新月份={latest_date.strftime('%Y-%m')}, 新值={current_value}, 最近有效值={last_value}")
                                    df = df[['time','value']]
                                    df.columns = ['index',code]
                                    df.set_index('index',inplace=True)
                                    with sql_engine.begin() as connection:
                                        if validate_and_log_data(code, latest_date, current_value, 'THS', connection):
                                            # 只有当验证通过时才更新数据
                                            pro_data(df, last_month_end.strftime('%Y-%m-%d'), code)
                                        else:
                                            print(f"数据验证未通过，不进行更新")
                                else:
                                    print(f"拒绝更新: 虽然是新月份，但值未变化 (新值={current_value}, 最近有效值={last_value})")
                            else:
                                print(f"拒绝更新: 不是新月份 (同花顺={latest_period}, 最近有效数据={last_month_period})")
                        else:
                            print(f"同花顺返回的数据中没有有效值")
                    except Exception as e:
                        print(f"处理同花顺数据时出错: {str(e)}")
                        print("原始数据:")
                        print(df)
                else:
                    print(f'同花顺接口未返回有效数据')

def update_historical_data(code, type, start_date, end_date):
    """
    更新指定时间区间的历史数据
    
    参数:
    code: str, 数据代码
    type: int, 1表示Wind接口，2表示同花顺接口
    start_date: str, 开始日期，格式'YYYY-MM-DD'
    end_date: str, 结束日期，格式'YYYY-MM-DD'
    """
    try:
        # 转换日期字符串为datetime对象
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        print(f"\n更新历史数据 - 代码: {code}")
        print(f"时间区间: {start_date} 至 {end_date}")
        
        if type == 1:
            # 使用Wind EDB接口获取历史数据
            error_code, wsd_data = w.edb(f"{code}", start_date, end_date, usedf=True)
            
            if error_code == 0 and not wsd_data.empty:
                try:
                    if wsd_data.index[0] == code:
                        # 单值数据处理
                        pro_data(wsd_data, start_date, code)
                    else:
                        # 多值数据处理
                        wsd_data.index = pd.to_datetime(wsd_data.index)
                        pro_data(wsd_data, start_date, code)
                    print(f"历史数据更新完成")
                except Exception as e:
                    print(f"处理Wind历史数据时出错: {str(e)}")
                    print("原始数据:")
                    print(wsd_data)
            else:
                print(f"Wind接口返回错误: {error_code}")
        else:
            # 使用同花顺接口获取历史数据
            df = THS_EDB(code, '', start_date, end_date)
            if df.data is not None:
                df = df.data
                if not df.empty and 'time' in df.columns:
                    try:
                        df['time'] = pd.to_datetime(df['time'])
                        df = df[['time', 'value']]
                        df.columns = ['index', code]
                        df.set_index('index', inplace=True)
                        pro_data(df, start_date, code)
                        print(f"历史数据更新完成")
                    except Exception as e:
                        print(f"处理同花顺历史数据时出错: {str(e)}")
                        print("原始数据:")
                        print(df)
                else:
                    print(f'同花顺接口未返回有效数据')
    except Exception as e:
        print(f"更新历史数据时出错: {str(e)}")

def update_historical_fund_data(code, start_date, end_date):
    """
    更新基金净申购的历史数据
    
    参数:
    code: str, 基金代码
    start_date: str, 开始日期，格式'YYYY-MM-DD'
    end_date: str, 结束日期，格式'YYYY-MM-DD'
    """
    try:
        print(f"\n更新基金历史数据 - 代码: {code}")
        print(f"时间区间: {start_date} 至 {end_date}")
        
        wsd_data = w.wsd(code, "mf_netinflow", start_date, end_date, "unit=1")
        if wsd_data.ErrorCode == 0:
            dates = pd.date_range(start=start_date, end=end_date)
            df = pd.DataFrame()
            
            for i, date in enumerate(dates):
                if i < len(wsd_data.Data[0]):  # 确保有对应的数据
                    dt_str = date.strftime('%Y-%m-%d')
                    jsg = wsd_data.Data[0][i]
                    if not pd.isna(jsg):  # 只处理非空值
                        temp_df = pd.DataFrame({'dt': [dt_str], 'trade_code': [code], '净申购': [jsg]})
                        df = pd.concat([df, temp_df], ignore_index=True)
            
            if not df.empty:
                with sql_engine.begin() as connection:
                    # 先删除该时间段的旧数据
                    delete_query = text("""
                        DELETE FROM 基金净申购 
                        WHERE trade_code = :code 
                        AND dt BETWEEN :start_date AND :end_date
                    """)
                    connection.execute(delete_query, {
                        'code': code,
                        'start_date': start_date,
                        'end_date': end_date
                    })
                    
                    # 插入新数据
                    df.to_sql("基金净申购", con=connection, index=False, if_exists='append')
                print(f"基金历史数据更新完成")
            else:
                print(f"没有有效的历史数据需要更新")
        else:
            print(f"Wind接口返回错误: {wsd_data.ErrorCode}")
    except Exception as e:
        print(f"更新基金历史数据时出错: {str(e)}")

code_list=["M0001538","M0001527","M0251904","M0001528","M0001529","M0001530","M0062047","M0062845","M0062846","M0251905","M0001533","M0001534","M0251906","M0251907","M0062848","M0001536","M0001537","M0001557","M0001539","M0061954","M0001540","M0251908","M0001542","M0001545","M0251909","M0001543","M0001547","M0001541","M0001544","M0001548","M0001549","M0001550","M0001551","M0251910","M0251911","M0001552","M0251912","M0061955","M0001554","M0150191","M0062849","M0001556","M0251956","M0251940","M0251941","M0251942","M0251943","M0251944","M0251945","M0251946","M0251947","M0251948","M0251949","M0251950","M0251951","M0251952","M0251953","M0251954","M0251955","M0251977","M0251957","M0251958","M0251959","M0251960","M0251961","M0251962","M0251963","M0251964","M0251965","M0333070","M0333071","M0251966","M0333072","M0251967","M0251968","M0251969","M0251970","M0251971","M0251972","M0251973","M0333073","M0251974","M0251975","M0251976","M0048455","M0048441","M0252060","M0062879","M0048445","M0252061","M0252062","M0062881","M0062876","M0048442","M0048443","M0048444","M0062878","M0252063","M0252064","M0252065","M0252066","M0048451","M0252068","M0048452","M0048453","M0048454","M0048471","M0048456","M0061993","M0048457","M0048466","M0061994","M0061995","M0061996","M0048468","M0150196","M0062883","M0252069","M0048469","M0048470","M0009940","M0043410","M0043412","M0043411","M0043413","M0009947","M0009969","M0043417","M0043418","M0009978","M0043419","M0001380","M0001382","M0001384","M0001386","M0010131","M0001485","M0001486","M0001487","M0001488","M0001489","M0001490","M0001491","M0001492","M0001494","M0001493","M0001495","M0001496","M0001497","M0001504","M0001498","M0001499","M0001500","M5639029","M5639030","M5639031","M5639032","M5639033","M5639034","M5639035","J3426133","M0010125","M5525755","M5525756","M5525757","M5525758","M5525759","M5525760","M5525761","M5525762","M6179494","M6094230","M6094231","Y7375557","M0001705","M0001724","M5449834","M5524595","M5207551",'M0001680','M0001684','M0001685','M0001686','M0001687','M0001688','M0001689','M0001690','M0068054','M0001697','M0001698','M0001699','M0001700','M0001701','M0001702']

for code in code_list:
    get_data(code,1)
    # update_historical_data(code, 1, "2010-01-01", "2015-01-01")


code_list=['S004345997','S004346069','S004346029','S004345944','S004346101']
for code in code_list:
    get_data(code,2)
    # update_historical_data(code, 2, "2010-01-01", "2015-01-01")

current_date = datetime.now()
dt=current_date.strftime('%Y-%m-%d')
codes=['511090.SH','511130.SH']
for code in codes:
    wsd_data=w.wsd(code, "mf_netinflow", dt, dt, "unit=1")
    jsg=wsd_data.Data[0][0]
    df=pd.DataFrame()
    df = pd.concat([df, pd.DataFrame({'dt':[dt],'trade_code':[code],'净申购':[jsg]})], ignore_index=True)
    try:
        with sql_engine.begin() as connection:
            df.to_sql("基金净申购",con=connection,index=False,if_exists='append')
    except:
        print(f'{dt} {code} 重复')

# 示例使用方法（注释掉，需要时可以取消注释使用）
# # 更新金融资负表的历史数据
#   # Wind数据
# update_historical_data("S004345997", 2, "2023-01-01", "2023-12-31")  # 同花顺数据
# # 更新基金净申购的历史数据
# update_historical_fund_data("511090.SH", "2023-01-01", "2023-12-31")