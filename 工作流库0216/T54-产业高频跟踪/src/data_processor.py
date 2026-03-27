# -*- coding: utf-8 -*-
"""
数据处理模块
"""
import pandas as pd
import numpy as np
import sqlalchemy
from typing import Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_STOCK_URL, DB_YQ_URL, DB_BOND_URL


class DataProcessor:
    """数据处理类"""

    def __init__(self):
        self.stock_engine = sqlalchemy.create_engine(
            DB_STOCK_URL, poolclass=sqlalchemy.pool.NullPool
        )
        self.yq_engine = sqlalchemy.create_engine(
            DB_YQ_URL, poolclass=sqlalchemy.pool.NullPool
        )
        self.bond_engine = sqlalchemy.create_engine(
            DB_BOND_URL, poolclass=sqlalchemy.pool.NullPool
        )

    def get_industry_info(self) -> pd.DataFrame:
        """获取产业跟踪指标信息"""
        sql = "SELECT * FROM 产业跟踪指标信息"
        return pd.read_sql(sql, self.yq_engine)

    def get_edb_data(self, trade_code: str, date_end: str) -> pd.DataFrame:
        """获取EDB数据"""
        sql = f"SELECT DT, CLOSE FROM edb.edbdata WHERE TRADE_CODE = '{trade_code}' AND DT <= '{date_end}'"
        return pd.read_sql(sql, self.stock_engine)

    @staticmethod
    def handle_outliers(df: pd.DataFrame) -> pd.DataFrame:
        """处理异常值"""
        if df.empty:
            return df

        Q1 = df['CLOSE'].quantile(0.25)
        Q3 = df['CLOSE'].quantile(0.75)
        IQR = Q3 - Q1

        outliers_indices = df[
            (df['CLOSE'] < (Q1 - 1.5 * IQR)) |
            (df['CLOSE'] > (Q3 + 1.5 * IQR))
        ].index

        df.loc[outliers_indices, 'CLOSE'] = np.nan
        df['CLOSE'] = df['CLOSE'].interpolate(method='linear')
        df.ffill(inplace=True)
        df.bfill(inplace=True)

        return df[['DT', 'CLOSE']]

    @staticmethod
    def calculate_yoy_12ma(trade_code: str, date_end: str, cursor) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """转12月移动平均年同比"""
        df = pd.read_sql(
            f"SELECT DT, CLOSE FROM edb.edbdata WHERE TRADE_CODE = '{trade_code}' AND DT <= '{date_end}'",
            cursor
        )
        df = DataProcessor.handle_outliers(df)

        if df.empty:
            empty_df = pd.DataFrame(columns=['DT', 'CLOSE'])
            return empty_df, empty_df.copy()

        df['DT'] = pd.to_datetime(df['DT'])
        df.set_index('DT', inplace=True)
        df = df.resample('ME').last()
        df1 = df.copy()

        df['CLOSE'] = df['CLOSE'].pct_change(12, fill_method=None) * 100
        df1['CLOSE'] = df1['CLOSE'].pct_change(12, fill_method=None) * 100

        date_range = pd.date_range(start=df.index.min(), end=df.index.max())
        df = df.reindex(date_range)
        df1 = df1.reindex(date_range)

        df['CLOSE'] = df['CLOSE'].interpolate(method='linear')
        df1['CLOSE'] = df1['CLOSE'].interpolate(method='linear')
        df.ffill(inplace=True)
        df1.ffill(inplace=True)

        df.reset_index(inplace=True)
        df1.reset_index(inplace=True)
        df.rename(columns={'index': 'DT'}, inplace=True)
        df1.rename(columns={'index': 'DT'}, inplace=True)

        df.dropna(inplace=True)
        df1.dropna(inplace=True)

        return df[['DT', 'CLOSE']], df1[['DT', 'CLOSE']]

    @staticmethod
    def monthly_yoy_12ma(trade_code: str, date_end: str, cursor) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """月同比12个月移动平均"""
        indicator_x = pd.read_sql(
            f"SELECT DT, CLOSE FROM edb.edbdata WHERE TRADE_CODE = '{trade_code}' AND DT <= '{date_end}' ORDER BY DT DESC",
            cursor
        ).sort_values('DT')
        indicator_x = DataProcessor.handle_outliers(indicator_x)

        if indicator_x.empty:
            empty_df = pd.DataFrame(columns=['DT', 'CLOSE'])
            return empty_df, empty_df.copy()

        indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
        indicator_x.set_index('DT', inplace=True)
        indicator_x = indicator_x.resample('ME').mean()
        indicator_x1 = indicator_x.copy()

        date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
        indicator_x = indicator_x.reindex(date_range)
        indicator_x1 = indicator_x1.reindex(date_range)

        indicator_x['CLOSE'] = indicator_x['CLOSE'].interpolate(method='linear')
        indicator_x1['CLOSE'] = indicator_x1['CLOSE'].interpolate(method='linear')
        indicator_x.ffill(inplace=True)
        indicator_x1.ffill(inplace=True)

        indicator_x.reset_index(inplace=True)
        indicator_x1.reset_index(inplace=True)
        indicator_x.rename(columns={'index': 'DT'}, inplace=True)
        indicator_x1.rename(columns={'index': 'DT'}, inplace=True)

        indicator_x.dropna(inplace=True)
        indicator_x1.dropna(inplace=True)

        return indicator_x[['DT', 'CLOSE']], indicator_x1[['DT', 'CLOSE']]

    @staticmethod
    def highfreq_price_yoy(trade_code: str, date_end: str, cursor) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """高频价格转12月移动平均月均价年同比"""
        indicator_x = pd.read_sql(
            f"SELECT DT, CLOSE FROM edb.edbdata WHERE TRADE_CODE = '{trade_code}' AND DT <= '{date_end}' ORDER BY DT",
            cursor
        )

        if indicator_x.empty:
            empty_df = pd.DataFrame(columns=['DT', 'CLOSE'])
            return empty_df, empty_df.copy()

        indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
        indicator_x.set_index('DT', inplace=True)
        indicator_x = indicator_x.resample('ME').mean()
        indicator_x1 = indicator_x.copy()

        indicator_x['CLOSE'] = indicator_x['CLOSE'].pct_change(12, fill_method=None) * 100
        indicator_x1['CLOSE'] = indicator_x1['CLOSE'].pct_change(12, fill_method=None) * 100

        date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
        indicator_x = indicator_x.reindex(date_range)
        indicator_x1 = indicator_x1.reindex(date_range)

        indicator_x['CLOSE'] = indicator_x['CLOSE'].interpolate(method='linear')
        indicator_x1['CLOSE'] = indicator_x1['CLOSE'].interpolate(method='linear')
        indicator_x.ffill(inplace=True)
        indicator_x1.ffill(inplace=True)

        indicator_x.reset_index(inplace=True)
        indicator_x1.reset_index(inplace=True)
        indicator_x.rename(columns={'index': 'DT'}, inplace=True)
        indicator_x1.rename(columns={'index': 'DT'}, inplace=True)

        indicator_x = DataProcessor.handle_outliers(indicator_x)
        indicator_x1 = DataProcessor.handle_outliers(indicator_x1)

        indicator_x.dropna(inplace=True)
        indicator_x1.dropna(inplace=True)

        return indicator_x[['DT', 'CLOSE']], indicator_x1[['DT', 'CLOSE']]
