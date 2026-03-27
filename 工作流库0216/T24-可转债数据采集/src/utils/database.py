from sqlalchemy import create_engine, text
import pandas as pd
from typing import Optional
import logging

class Database:
    def __init__(self, config: dict):
        self.logger = logging.getLogger('database')
        self.config = config
        self.engine = self._create_engine()
        
    def _create_engine(self):
        """创建数据库引擎"""
        conn_str = (
            f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
        return create_engine(conn_str)
        
    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """执行查询"""
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(text(query), conn, params=params)
        except Exception as e:
            self.logger.error(f"执行查询失败: {str(e)}")
            raise
            
    def execute_update(self, query: str, params: Optional[dict] = None):
        """执行更新"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query), params or {})
        except Exception as e:
            self.logger.error(f"执行更新失败: {str(e)}")
            raise
            
    def save_dataframe(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """保存DataFrame到数据库"""
        try:
            with self.engine.begin() as conn:
                df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        except Exception as e:
            self.logger.error(f"保存DataFrame失败: {str(e)}")
            raise