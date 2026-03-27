# -*- coding: utf-8 -*-
"""
数据导入模块
"""
import pandas as pd
import sqlalchemy
from typing import Optional
from sqlalchemy import text


class DataImporter:
    """数据导入类"""

    def __init__(self, engine: sqlalchemy.engine.Engine):
        self.engine = engine

    def import_to_table(self, df: pd.DataFrame, table_name: str,
                        if_exists: str = 'append', index: bool = False) -> int:
        """将DataFrame导入到数据库表"""
        with self.engine.begin() as connection:
            df.to_sql(table_name, connection, if_exists=if_exists, index=index)
        return len(df)

    def import_with_replace(self, df: pd.DataFrame, table_name: str,
                            key_columns: list) -> int:
        """使用REPLACE方式导入（存在则替换）"""
        count = 0
        with self.engine.begin() as connection:
            for _, row in df.iterrows():
                # 构建REPLACE语句
                columns = df.columns.tolist()
                values = [row[col] for col in columns]
                placeholders = ', '.join([':' + str(i) for i in range(len(columns))])
                column_names = ', '.join(columns)

                sql = f"REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
                connection.execute(text(sql), dict(enumerate(values)))
                count += 1
        return count

    def clear_table(self, table_name: str) -> None:
        """清空表数据"""
        with self.engine.begin() as connection:
            connection.execute(text(f"TRUNCATE TABLE {table_name}"))

    def get_table_info(self, table_name: str) -> dict:
        """获取表信息"""
        with self.engine.connect() as connection:
            # 获取行数
            count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()

            # 获取列信息
            columns_result = connection.execute(text(f"DESCRIBE {table_name}"))
            columns = [row[0] for row in columns_result]

        return {
            'table_name': table_name,
            'row_count': row_count,
            'columns': columns
        }

    def execute_update(self, sql: str, params: dict = None) -> int:
        """执行更新SQL"""
        with self.engine.begin() as connection:
            result = connection.execute(text(sql), params or {})
            return result.rowcount
