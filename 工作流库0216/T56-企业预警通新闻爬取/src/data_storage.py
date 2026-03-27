# -*- coding: utf-8 -*-
"""
数据存储模块
"""
import pandas as pd
import sqlalchemy
from sqlalchemy import inspect, text
from typing import Optional
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_YQ_URL, NEWS_CONFIG


class DataStorage:
    """数据存储类"""

    def __init__(self, engine: sqlalchemy.engine.Engine = None):
        if engine is None:
            self.engine = sqlalchemy.create_engine(
                DB_YQ_URL, poolclass=sqlalchemy.pool.NullPool
            )
        else:
            self.engine = engine

        self._setup_logging()

    def _setup_logging(self):
        """配置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        inspector = inspect(self.engine)
        return inspector.has_table(table_name)

    def get_table_columns(self, table_name: str) -> list:
        """获取表列名"""
        inspector = inspect(self.engine)
        if self.table_exists(table_name):
            columns = inspector.get_columns(table_name)
            return [col['name'] for col in columns]
        return []

    def add_column_if_not_exists(self, table_name: str, column_name: str,
                                  column_type: str = 'TEXT') -> None:
        """添加列（如果不存在）"""
        existing_columns = self.get_table_columns(table_name)
        if column_name not in existing_columns:
            with self.engine.begin() as connection:
                connection.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                )
            self.logger.info(f"添加列: {column_name}")

    def save_news(self, df: pd.DataFrame, table_name: str = None) -> int:
        """保存新闻数据到数据库"""
        if df.empty:
            self.logger.warning("没有数据需要保存")
            return 0

        table_name = table_name or NEWS_CONFIG['table_name']

        # 转换数据类型为字符串
        df = df.astype(str)

        # 检查并添加缺失的列
        if self.table_exists(table_name):
            existing_columns = self.get_table_columns(table_name)
            df_columns = df.columns.tolist()

            for col in df_columns:
                if col not in existing_columns:
                    self.add_column_if_not_exists(table_name, col)

        # 保存数据
        try:
            with self.engine.begin() as connection:
                df.to_sql(table_name, connection, if_exists='append', index=False)
            self.logger.info(f"成功保存 {len(df)} 条数据到 {table_name}")
            return len(df)
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            return 0

    def get_existing_ids(self, table_name: str, id_column: str = 'id') -> set:
        """获取已存在的ID集合"""
        if not self.table_exists(table_name):
            return set()

        query = f"SELECT DISTINCT {id_column} FROM {table_name}"
        with self.engine.connect() as connection:
            result = connection.execute(text(query))
            return {row[0] for row in result}

    def remove_duplicates(self, df: pd.DataFrame, table_name: str,
                          id_column: str = 'id') -> pd.DataFrame:
        """去除已存在的重复数据"""
        existing_ids = self.get_existing_ids(table_name, id_column)
        if id_column in df.columns and existing_ids:
            df = df[~df[id_column].isin(existing_ids)]
            self.logger.info(f"去除 {len(existing_ids)} 条重复数据")
        return df
