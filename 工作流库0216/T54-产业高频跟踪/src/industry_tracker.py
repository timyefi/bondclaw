# -*- coding: utf-8 -*-
"""
行业跟踪模块
"""
import pandas as pd
import numpy as np
from typing import Tuple
from .wavelet_analyzer import WaveletAnalyzer


class IndustryTracker:
    """行业景气度跟踪类"""

    def __init__(self, basic_info: pd.DataFrame):
        self.basic_info = basic_info
        self.wavelet_analyzer = WaveletAnalyzer()

    def get_industry_config(self, industry: str) -> dict:
        """获取行业配置"""
        row = self.basic_info[self.basic_info['行业'] == industry]
        if row.empty:
            raise ValueError(f"未找到行业: {industry}")

        return {
            'period_cycle': row['周期天数'].iloc[0],
            'period_trend': row['趋势天数'].iloc[0],
            'level': row['level'].iloc[0],
            'trade_code': row['trade_code'].iloc[0],
            'name': row['名称'].iloc[0]
        }

    def calculate_indicator(self, df: pd.DataFrame, industry: str) -> pd.DataFrame:
        """计算行业指标分位点和趋势"""
        if df.empty:
            return pd.DataFrame(columns=['行业', '指标名称', 'DT', '分位点', '趋势'])

        config = self.get_industry_config(industry)

        if len(df) < abs(int(config['period_cycle'])):
            return pd.DataFrame(columns=['行业', '指标名称', 'DT', '分位点', '趋势'])

        values = df['CLOSE'].values
        percentile, trend = self.wavelet_analyzer.get_cycle_value(
            values,
            config['period_cycle'],
            config['period_trend'],
            config['level']
        )

        result = pd.DataFrame(columns=['行业', '指标名称', 'DT', '分位点', '趋势'])
        result.loc[0] = [
            industry,
            config['name'],
            df['DT'].iloc[-1],
            percentile,
            trend
        ]

        return result

    @staticmethod
    def merge_indicators(df_list: list, weights: list = None) -> pd.DataFrame:
        """合并多个指标"""
        if not df_list:
            return pd.DataFrame()

        if weights is None:
            weights = [1.0 / len(df_list)] * len(df_list)

        merged = df_list[0][['DT']].copy()
        merged['CLOSE'] = 0

        for df, weight in zip(df_list, weights):
            df_temp = df.copy()
            df_temp['DT'] = pd.to_datetime(df_temp['DT'])
            df_temp.set_index('DT', inplace=True)
            merged = merged.merge(
                df_temp[['CLOSE']],
                left_on=pd.to_datetime(merged['DT']),
                right_index=True,
                how='left',
                suffixes=('', '_new')
            )
            merged['CLOSE'] = merged['CLOSE'].fillna(0) + merged.get('CLOSE_new', 0).fillna(0) * weight

        return merged[['DT', 'CLOSE']]

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据"""
        df = df.copy()
        mean = df['CLOSE'].mean()
        std = df['CLOSE'].std()
        if std != 0:
            df['CLOSE'] = (df['CLOSE'] - mean) / std
        return df
