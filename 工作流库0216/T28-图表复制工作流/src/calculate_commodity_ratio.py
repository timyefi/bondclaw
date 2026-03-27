#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计算商品指数与金融资产比率并插入到"全球实物资产比金融资产"表中

计算公式：
    CRB CMDT Index / (0.5 * (FLOT US Equity + .EARNREV G Index))

数据处理流程：
1. 从edb.edbdata表中查询三个TRADE_CODE的数据
2. 对数据进行日度插值，确保日期对齐
3. 计算比值并按基准调整
4. 转换为周度数据，取每周最后一个自然日
5. 插入到"全球实物资产比金融资产"表中
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.utils.database import DatabaseManager
from common.config.database import get_predefined_database_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_data_from_database():
    """
    从数据库查询所需数据
    
    Returns:
        tuple: (crb_data, flot_data, earnrev_data) 三个DataFrame
    """
    logger.info("开始从数据库查询数据...")
    
    # 使用yq数据库配置
    config = get_predefined_database_config('yq')
    db_manager = DatabaseManager(config)
    
    try:
        # 查询三个指数的数据
        trade_codes = ['CRB CMDT Index', 'FLOT US Equity', '.EARNREV G Index']
        data_frames = {}
        
        for trade_code in trade_codes:
            sql = """
            SELECT DT, CLOSE, TRADE_CODE
            FROM edb.edbdata
            WHERE TRADE_CODE = %s
            AND DT >= %s
            ORDER BY DT
            """
            
            params = (
                trade_code,
                '2020-11-12'
            )
            
            df = db_manager.execute_query(sql, params)
            df['DT'] = pd.to_datetime(df['DT'])
            df = df.set_index('DT')
            data_frames[trade_code] = df
            logger.info(f"查询到 {trade_code} 数据 {len(df)} 条")
        
        return (
            data_frames['CRB CMDT Index'],
            data_frames['FLOT US Equity'], 
            data_frames['.EARNREV G Index']
        )
        
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        raise
    finally:
        db_manager.close()


def process_data(crb_df, flot_df, earnrev_df):
    """
    处理数据：插值、计算比值、基准调整
    
    Args:
        crb_df: CRB数据DataFrame
        flot_df: FLOT数据DataFrame
        earnrev_df: EARNREV数据DataFrame
        
    Returns:
        pd.DataFrame: 处理后的数据，包含dt和close列
    """
    logger.info("开始处理数据...")
    
    # 合并三个数据集
    merged_df = pd.concat([
        crb_df['CLOSE'].rename('CRB'),
        flot_df['CLOSE'].rename('FLOT'),
        earnrev_df['CLOSE'].rename('EARNREV')
    ], axis=1)
    
    # 对缺失数据进行插值
    merged_df = merged_df.interpolate(method='linear')
    
    # 删除仍有缺失值的行
    merged_df = merged_df.dropna()
    
    logger.info(f"合并后数据共 {len(merged_df)} 条记录")
    
    # 计算比值：CRB / (0.5 * (FLOT + EARNREV))
    merged_df['ratio'] = merged_df['CRB'] / (0.5 * (merged_df['FLOT'] + merged_df['EARNREV']))
    
    # 基准调整
    # 找到2020-11-12的比值
    base_date = pd.to_datetime('2020-11-12')
    if base_date in merged_df.index:
        base_value = merged_df.loc[base_date, 'ratio']
        target_base_value = 0.09427710843373494
        adjustment_factor = target_base_value / base_value
        merged_df['close'] = merged_df['ratio'] * adjustment_factor
        logger.info(f"基准调整因子: {adjustment_factor}")
    else:
        logger.warning("未找到基准日期2020-11-12的数据，使用原始比值")
        merged_df['close'] = merged_df['ratio']
    
    # 创建结果DataFrame
    result_df = pd.DataFrame({
        'dt': merged_df.index,
        'close': merged_df['close']
    })
    
    return result_df


def convert_to_weekly(data_df):
    """
    转换为周度数据，取每周最后一个自然日
    
    Args:
        data_df: 日度数据DataFrame
        
    Returns:
        pd.DataFrame: 周度数据DataFrame
    """
    logger.info("开始转换为周度数据...")
    
    # 确保dt列为datetime类型
    data_df['dt'] = pd.to_datetime(data_df['dt'])
    data_df = data_df.set_index('dt')
    
    # 按周重采样，取每周最后一个值
    weekly_df = data_df.resample('W').last()
    
    # 重置索引
    weekly_df = weekly_df.reset_index()
    
    # 重命名列
    weekly_df.columns = ['dt', 'close']
    
    # 删除缺失值
    weekly_df = weekly_df.dropna()
    
    logger.info(f"周度数据共 {len(weekly_df)} 条记录")
    return weekly_df


def insert_to_database(data_df):
    """
    将数据插入到"全球实物资产比金融资产"表中
    
    Args:
        data_df: 要插入的数据DataFrame
    """
    logger.info("开始插入数据到数据库...")
    
    # 过滤掉基准日期2020-11-12的数据
    base_date = pd.to_datetime('2020-11-12')
    data_df = data_df[data_df['dt'] > base_date]
    
    if len(data_df) == 0:
        logger.warning("没有需要插入的数据")
        return
    
    logger.info(f"需要插入 {len(data_df)} 条记录")
    
    # 使用yq数据库配置
    config = get_predefined_database_config('yq')
    db_manager = DatabaseManager(config)
    
    try:
        # 检查目标表是否存在
        if not db_manager.table_exists('全球实物资产比金融资产'):
            logger.warning("目标表 '全球实物资产比金融资产' 不存在")
            return
        
        # 删除已存在的日期数据，避免重复
        for _, row in data_df.iterrows():
            delete_sql = """
            DELETE FROM `全球实物资产比金融资产`
            WHERE dt = :dt
            """
            db_manager.execute_sql(delete_sql, {'dt': row['dt']})
        
        # 插入数据
        rows_inserted = db_manager.insert_dataframe(
            data_df,
            '全球实物资产比金融资产',
            if_exists='append',
            chunksize=1000
        )
        
        logger.info(f"成功插入 {rows_inserted} 条记录")
        
    except Exception as e:
        logger.error(f"数据插入失败: {e}")
        raise
    finally:
        db_manager.close()


def main():
    """主函数"""
    try:
        logger.info("开始执行商品指数比率计算任务...")
        
        # 1. 查询数据
        crb_data, flot_data, earnrev_data = get_data_from_database()
        
        # 2. 处理数据
        processed_data = process_data(crb_data, flot_data, earnrev_data)
        
        # 3. 转换为周度数据
        weekly_data = convert_to_weekly(processed_data)
        
        # 4. 插入数据库
        insert_to_database(weekly_data)
        
        logger.info("任务执行完成")
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}")
        raise


if __name__ == "__main__":
    main()