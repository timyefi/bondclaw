# -*- coding: utf-8 -*-
"""
Trade Code映射模块
"""
import pandas as pd
import sqlalchemy
from typing import Optional
import re


class TradeCodeMapper:
    """Trade Code映射类"""

    def __init__(self, engine: sqlalchemy.engine.Engine):
        self.engine = engine

    def get_mapping_table(self) -> pd.DataFrame:
        """从多个表获取trade_code映射"""
        query = """
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_credit
        UNION ALL
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_finance
        UNION ALL
        SELECT trade_code, ths_issuer_name_cn_bond FROM basicinfo_abs
        """
        return pd.read_sql(query, self.engine)

    def create_mapping_dict(self) -> dict:
        """创建发行人名称到trade_code的映射字典"""
        df = self.get_mapping_table()
        # 取每个发行人名称对应的最后一个trade_code
        mapping = df.groupby('ths_issuer_name_cn_bond')['trade_code'].last().to_dict()
        return mapping

    def map_trade_codes(self, df: pd.DataFrame, name_column: str = 'ths_issuer_name_cn_bond',
                        target_column: str = 'trade_code') -> pd.DataFrame:
        """根据发行人名称映射trade_code"""
        df = df.copy()
        mapping = self.create_mapping_dict()
        df[target_column] = df[name_column].map(mapping)
        return df

    @staticmethod
    def contains_chinese(text: str) -> bool:
        """检查字符串是否包含中文字符"""
        if pd.isna(text):
            return False
        return bool(re.search(r'[\u4e00-\u9fa5]', str(text)))

    @staticmethod
    def filter_chinese_trade_codes(df: pd.DataFrame, column: str = 'trade_code') -> pd.DataFrame:
        """过滤掉trade_code包含中文的行"""
        mask = df[column].apply(TradeCodeMapper.contains_chinese)
        return df[~mask]

    @staticmethod
    def filter_empty_values(df: pd.DataFrame, columns: list) -> pd.DataFrame:
        """过滤空值"""
        for col in columns:
            df = df[df[col].notna() & (df[col] != '')]
        return df
