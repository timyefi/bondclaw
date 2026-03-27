#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T31 机构行为监测 - 数据同步模块

用于从Excel文件同步数据到数据库。
"""

import os
import logging
from typing import Optional

import pandas as pd

from utils import DatabaseManager, clean_numeric_column, clean_date_column

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_header_row(file_path: str) -> int:
    """
    智能查找Excel文件中的标题行

    Args:
        file_path: Excel文件路径

    Returns:
        int: 标题行索引
    """
    try:
        df_peek = pd.read_excel(file_path, header=None, nrows=10)
        for i, row in df_peek.iterrows():
            if any(isinstance(cell, str) and ('日期' in cell or '机构' in cell) for cell in row.values):
                return i
    except Exception:
        pass
    return 0


def load_and_upload_data(
    file_path: str,
    db_manager: DatabaseManager,
    table_name: str = '现券成交分机构统计表'
) -> int:
    """
    加载Excel文件并上传到数据库

    Args:
        file_path: Excel文件路径
        db_manager: 数据库管理器
        table_name: 目标表名

    Returns:
        int: 插入的记录数
    """
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return 0

    try:
        # 智能查找标题行
        header_row = find_header_row(file_path)
        df = pd.read_excel(file_path, header=header_row)

        # 清理空列
        df.dropna(axis=1, how='all', inplace=True)

        logger.info(f"从 {os.path.basename(file_path)} 加载 {len(df)} 条记录")

        # 处理特殊值
        volume_columns = ['净买入交易量（亿元）', '买入交易量（亿元）', '卖出交易量（亿元）']
        for col in volume_columns:
            if col in df.columns:
                df[col] = clean_numeric_column(df[col])

        # 确保日期格式正确
        if '交易日期' in df.columns:
            df['交易日期'] = clean_date_column(df['交易日期'])

        # 检查表是否存在并去重
        merge_columns = ['交易日期', '机构类型', '期限', '债券类型']

        if db_manager.table_exists(table_name):
            try:
                existing_df = db_manager.execute_query(f"SELECT * FROM `{table_name}`")

                if not existing_df.empty:
                    existing_df['交易日期'] = clean_date_column(existing_df['交易日期'])

                    for col in volume_columns:
                        if col in existing_df.columns:
                            existing_df[col] = clean_numeric_column(existing_df[col])

                    # 去重
                    df_reset = df.reset_index(drop=True)
                    existing_reset = existing_df.reset_index(drop=True)

                    merged_df = pd.merge(df_reset, existing_reset, on=merge_columns, how='left', indicator=True)
                    new_data_df = merged_df[merged_df['_merge'] == 'left_only'].drop('_merge', axis=1)

                    common_columns = [col for col in df_reset.columns if col in new_data_df.columns]
                    new_data_df = new_data_df[common_columns]

                    for col in df_reset.columns:
                        if col not in new_data_df.columns:
                            new_data_df[col] = None

                    new_data_df = new_data_df.reindex(columns=df_reset.columns)
                else:
                    new_data_df = df
            except Exception as e:
                logger.warning(f"去重过程出错: {e}，将上传所有数据")
                new_data_df = df
        else:
            logger.info(f"表 '{table_name}' 不存在，将创建新表")
            new_data_df = df

        if not new_data_df.empty:
            if '交易日期' in new_data_df.columns:
                new_data_df['交易日期'] = clean_date_column(new_data_df['交易日期'])

            logger.info(f"找到 {len(new_data_df)} 条新记录，准备上传...")
            db_manager.insert_dataframe(new_data_df, table_name, if_exists='append')
            return len(new_data_df)
        else:
            logger.info("没有新数据需要上传")
            return 0

    except Exception as e:
        logger.error(f"处理文件 {file_path} 时出错: {e}")
        raise


def sync_institution_data(
    source_dir: str,
    db_manager: DatabaseManager,
    file_pattern: str = None
) -> dict:
    """
    同步机构交易数据

    Args:
        source_dir: 源目录
        db_manager: 数据库管理器
        file_pattern: 文件名模式

    Returns:
        dict: 同步结果统计
    """
    results = {
        'total_files': 0,
        'success_files': 0,
        'total_records': 0,
        'errors': []
    }

    if not os.path.exists(source_dir):
        logger.error(f"源目录不存在: {source_dir}")
        return results

    # 查找Excel文件
    excel_files = []
    for f in os.listdir(source_dir):
        if f.endswith(('.xlsx', '.xls')):
            if file_pattern is None or file_pattern in f:
                excel_files.append(f)

    results['total_files'] = len(excel_files)

    for filename in excel_files:
        file_path = os.path.join(source_dir, filename)
        try:
            records = load_and_upload_data(file_path, db_manager)
            results['success_files'] += 1
            results['total_records'] += records
            logger.info(f"成功同步: {filename}, {records} 条记录")
        except Exception as e:
            results['errors'].append({'file': filename, 'error': str(e)})
            logger.error(f"同步失败: {filename}, 错误: {e}")

    logger.info(f"同步完成: {results['success_files']}/{results['total_files']} 文件, {results['total_records']} 条记录")
    return results


if __name__ == '__main__':
    print("=== 数据同步模块 ===")
    print("用于从Excel文件同步机构交易数据到数据库")
    print("\n使用方法:")
    print("  from data_sync import sync_institution_data")
    print("  results = sync_institution_data(source_dir, db_manager)")
