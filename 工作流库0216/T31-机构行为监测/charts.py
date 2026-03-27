#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T31 机构行为监测 - 核心逻辑模块

包含14个监测图表的数据处理和生成函数。
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from config import (
    INSTITUTION_TYPES, TENOR_CATEGORIES, BOND_ASSET_CLASSES, PROVINCES,
    map_tenor_to_category, map_bond_type_to_asset_class
)
from utils import (
    DatabaseManager, clean_numeric_column, clean_date_column,
    get_valid_date_range, simulate_trading_parties, clean_province_name
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InstitutionBehaviorMonitor:
    """机构行为监测核心类"""

    def __init__(self, db_manager: DatabaseManager = None):
        """
        初始化监测器

        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self._cache = {}

    # ============== 图表1: 各机构类型每日净交易量 ==============

    def get_chart1_daily_net_trading(
        self,
        date: str = None
    ) -> pd.DataFrame:
        """
        图表1: 各机构类型每日净交易量

        Args:
            date: 交易日期，格式 'YYYY-MM-DD'

        Returns:
            pd.DataFrame: 包含 name(机构类型), value(净买入量) 两列
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        sql = f"""
        SELECT
            `机构类型`,
            `净买入交易量（亿元）`
        FROM
            bond.`现券成交分机构统计表`
        WHERE
            `交易日期` = '{date}';
        """

        df = self.db_manager.execute_query(sql)

        # 数据清洗
        df['净买入交易量（亿元）'] = clean_numeric_column(df['净买入交易量（亿元）'])

        # 按机构类型分组聚合
        df_result = df.groupby('机构类型')['净买入交易量（亿元）'].sum().reset_index()
        df_result.rename(columns={'机构类型': 'name', '净买入交易量（亿元）': 'value'}, inplace=True)

        logger.info(f"图表1: 获取 {date} 的机构净交易量数据，共 {len(df_result)} 条")
        return df_result

    # ============== 图表2: 机构间交易矩阵 ==============

    def get_chart2_trading_matrix(
        self,
        date: str = None
    ) -> Dict[str, Any]:
        """
        图表2: 机构间交易矩阵

        Args:
            date: 交易日期

        Returns:
            Dict: 包含 heatmap_data 和 categories_table
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 获取机构交易统计数据（用于概率模拟）
        stats_sql = f"""
        SELECT `机构类型`, `期限`, `债券类型`,
               avg(`买入交易量（亿元）`) AS buy_vol,
               avg(`卖出交易量（亿元）`) AS sell_vol
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` <= '{date}'
          AND `交易日期` >= DATE_SUB('{date}', INTERVAL 14 DAY)
        GROUP BY `交易日期`, `机构类型`;
        """
        stats_df = self.db_manager.execute_query(stats_sql)
        stats_df['buy_vol'] = clean_numeric_column(stats_df['buy_vol'])
        stats_df['sell_vol'] = clean_numeric_column(stats_df['sell_vol'])

        # 获取交易明细数据
        dealtinfo_sql = f"""
        SELECT TRADE_CODE, transaction_amount/10000 as transaction_amount, remaining_term
        FROM bond.dealtinfo
        WHERE DT = (select max(DT) from bond.dealtinfo where DT<= '{date}');
        """
        dealtinfo_df = self.db_manager.execute_query(dealtinfo_sql)

        # 获取债券基本信息
        basicinfo_sql = """
        SELECT trade_code, ths_ths_bond_third_type_bond AS bond_type
        FROM bond.basicinfo_credit
        UNION ALL
        SELECT trade_code, ths_ths_bond_third_type_bond AS bond_type
        FROM bond.basicinfo_finance
        UNION ALL
        SELECT trade_code, ths_ths_bond_third_type_bond AS bond_type
        FROM bond.basicinfo_rate;
        """
        basicinfo_df = self.db_manager.execute_query(basicinfo_sql)

        # 合并交易数据和债券类型
        dealtinfo_df = pd.merge(dealtinfo_df, basicinfo_df,
                                left_on='TRADE_CODE', right_on='trade_code', how='left')

        # 添加期限分类
        dealtinfo_df['tenor_category'] = dealtinfo_df['remaining_term'].apply(map_tenor_to_category)

        # 模拟交易对手
        dealtinfo_enhanced_df = simulate_trading_parties(dealtinfo_df, stats_df)

        # 生成交易矩阵
        trade_matrix = dealtinfo_enhanced_df.pivot_table(
            index='party_type_s',
            columns='party_type_b',
            values='transaction_amount',
            aggfunc='sum'
        ).fillna(0)

        # 格式化为热力图数据
        heatmap_data = []
        seller_types = trade_matrix.index.tolist()
        buyer_types = trade_matrix.columns.tolist()

        for y, seller in enumerate(seller_types):
            for x, buyer in enumerate(buyer_types):
                amount = trade_matrix.loc[seller, buyer]
                heatmap_data.append({
                    'x': x,
                    'y': y,
                    'value': float(amount),
                    'value2': round(float(amount), 2)
                })

        categories_table = [
            {'type': 'cat', 'v': buyer_types},
            {'type': 'cat2', 'v': seller_types},
            {'type': 'date', 'v': date}
        ]

        logger.info(f"图表2: 生成交易矩阵，卖方 {len(seller_types)} 类，买方 {len(buyer_types)} 类")

        return {
            'final': heatmap_data,
            'categories_table': categories_table,
            'text': f'数据截止 {date}'
        }

    # ============== 图表3: 机构期限偏好分析 ==============

    def get_chart3_tenor_preference(
        self,
        date: str = None,
        institution_type: str = '大型商业银行/政策性银行'
    ) -> pd.DataFrame:
        """
        图表3: 机构期限偏好分析

        Args:
            date: 交易日期
            institution_type: 机构类型

        Returns:
            pd.DataFrame: 包含 name(期限), value(交易量), percent(占比)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        sql = f"""
        SELECT `期限`, `买入交易量（亿元）` as buy_vol, `卖出交易量（亿元）` as sell_vol
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` = '{date}' AND `机构类型` = '{institution_type}';
        """

        df = self.db_manager.execute_query(sql)

        # 数据清洗
        df['buy_vol'] = clean_numeric_column(df['buy_vol'])
        df['sell_vol'] = clean_numeric_column(df['sell_vol'])

        # 计算总交易量
        df['total_vol'] = df['buy_vol'] + df['sell_vol']

        # 过滤掉没有交易的期限
        df_result = df[df['total_vol'] > 0].copy()

        # 计算占比
        total_volume = df_result['total_vol'].sum()
        if total_volume > 0:
            df_result['percentage'] = (df_result['total_vol'] / total_volume) * 100
        else:
            df_result['percentage'] = 0

        df_result.rename(columns={'期限': 'name', 'total_vol': 'value', 'percentage': 'percent'}, inplace=True)

        logger.info(f"图表3: 获取 {institution_type} 的期限偏好数据，共 {len(df_result)} 条")
        return df_result[['name', 'value', 'percent']]

    # ============== 图表4: 机构券种偏好分析 ==============

    def get_chart4_bond_type_preference(
        self,
        date: str = None,
        institution_type: str = '大型商业银行/政策性银行'
    ) -> pd.DataFrame:
        """
        图表4: 机构券种偏好分析

        Args:
            date: 交易日期
            institution_type: 机构类型

        Returns:
            pd.DataFrame: 包含 name(券种), value(交易量), percent(占比)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        sql = f"""
        SELECT `债券类型`, `买入交易量（亿元）` as buy_vol, `卖出交易量（亿元）` as sell_vol
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` = '{date}' AND `机构类型` = '{institution_type}';
        """

        df = self.db_manager.execute_query(sql)

        # 数据清洗
        df['buy_vol'] = clean_numeric_column(df['buy_vol'])
        df['sell_vol'] = clean_numeric_column(df['sell_vol'])

        # 计算总交易量
        df['total_vol'] = df['buy_vol'] + df['sell_vol']

        # 过滤
        df_result = df[df['total_vol'] > 0].copy()

        # 计算占比
        total_volume = df_result['total_vol'].sum()
        if total_volume > 0:
            df_result['percentage'] = (df_result['total_vol'] / total_volume) * 100
        else:
            df_result['percentage'] = 0

        df_result.rename(columns={'债券类型': 'name', 'total_vol': 'value', 'percentage': 'percent'}, inplace=True)

        logger.info(f"图表4: 获取 {institution_type} 的券种偏好数据，共 {len(df_result)} 条")
        return df_result[['name', 'value', 'percent']]

    # ============== 图表5: 市场份额时序分析 ==============

    def get_chart5_market_share_timeseries(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        图表5: 市场份额时序分析

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 透视表，每列为一种机构类型，每行为一个日期
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        sql = f"""
        SELECT `交易日期`, `机构类型`, `买入交易量（亿元）` as buy_vol, `卖出交易量（亿元）` as sell_vol
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` BETWEEN '{start_date}' AND '{end_date}';
        """

        df = self.db_manager.execute_query(sql)

        # 数据清洗
        df['buy_vol'] = clean_numeric_column(df['buy_vol'])
        df['sell_vol'] = clean_numeric_column(df['sell_vol'])

        # 计算总交易量
        df['total_vol'] = df['buy_vol'] + df['sell_vol']

        # 计算每日市场总交易量
        daily_total = df.groupby('交易日期')['total_vol'].sum().reset_index()
        daily_total.rename(columns={'total_vol': 'market_total_vol'}, inplace=True)

        # 计算每日各机构总交易量
        daily_inst = df.groupby(['交易日期', '机构类型'])['total_vol'].sum().reset_index()

        # 合并
        df_final = pd.merge(daily_inst, daily_total, on='交易日期')

        # 计算市场份额
        df_final['market_share_percent'] = (df_final['total_vol'] / df_final['market_total_vol']) * 100

        # 透视
        df_chart = df_final.pivot(index='交易日期', columns='机构类型', values='market_share_percent').fillna(0)

        logger.info(f"图表5: 获取市场份额时序数据，{len(df_chart)} 天")
        return df_chart

    # ============== 图表6: 机构交易热点分析 ==============

    def get_chart6_trading_hotspots(
        self,
        date: str = None,
        institution_type: str = '大型商业银行/政策性银行',
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        图表6: 机构交易热点分析

        Args:
            date: 交易日期
            institution_type: 机构类型
            top_n: 返回前N只债券

        Returns:
            pd.DataFrame: 活跃债券统计
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 获取机构交易统计
        stats_sql = f"""
        SELECT `机构类型`, `期限`, `债券类型`,
               avg(`买入交易量（亿元）`) as buy_vol,
               avg(`卖出交易量（亿元）`) as sell_vol
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` <= '{date}'
          AND `交易日期` >= DATE_SUB('{date}', INTERVAL 14 DAY)
          AND `机构类型` = '{institution_type}'
        GROUP BY `机构类型`, `债券类型`, `期限`;
        """
        stats_df = self.db_manager.execute_query(stats_sql)
        stats_df['buy_vol'] = clean_numeric_column(stats_df['buy_vol'])
        stats_df['sell_vol'] = clean_numeric_column(stats_df['sell_vol'])

        # 获取交易明细
        dealtinfo_sql = f"""
        SELECT d.TRADE_CODE, d.SEC_NAME,
               COALESCE(bc.ths_ths_bond_third_type_bond, bf.ths_ths_bond_third_type_bond, br.ths_ths_bond_third_type_bond) AS bond_type,
               d.transaction_amount/10000 as transaction_amount,
               d.remaining_term
        FROM bond.dealtinfo d
        LEFT JOIN bond.basicinfo_credit bc ON d.TRADE_CODE = bc.trade_code
        LEFT JOIN bond.basicinfo_finance bf ON d.TRADE_CODE = bf.trade_code
        LEFT JOIN bond.basicinfo_rate br ON d.TRADE_CODE = br.trade_code
        WHERE d.DT = (select max(DT) from bond.dealtinfo where DT<= '{date}')
            AND (bc.trade_code IS NOT NULL OR bf.trade_code IS NOT NULL OR br.trade_code IS NOT NULL);
        """
        dealtinfo_df = self.db_manager.execute_query(dealtinfo_sql)

        # 添加期限分类
        dealtinfo_df['tenor_category'] = dealtinfo_df['remaining_term'].apply(map_tenor_to_category)

        # 获取活跃组合
        active_combinations = stats_df[['期限', '债券类型']].drop_duplicates()

        # 筛选匹配的交易
        filtered_trades = []
        for _, combo in active_combinations.iterrows():
            matched = dealtinfo_df[
                (dealtinfo_df['tenor_category'] == combo['期限']) &
                (dealtinfo_df['bond_type'] == combo['债券类型'])
            ].copy()
            if not matched.empty:
                filtered_trades.append(matched)

        if filtered_trades:
            filtered_df = pd.concat(filtered_trades, ignore_index=True)

            # 模拟买卖方向
            np.random.seed(42)
            filtered_df = filtered_df.copy()
            filtered_df['is_buy'] = np.random.choice([True, False], size=len(filtered_df))

            # 计算统计
            bond_stats = []
            for sec_name in filtered_df['SEC_NAME'].dropna().unique():
                sec_trades = filtered_df[filtered_df['SEC_NAME'] == sec_name]
                buy_amount = sec_trades[sec_trades['is_buy']]['transaction_amount'].sum()
                sell_amount = sec_trades[~sec_trades['is_buy']]['transaction_amount'].sum()
                total_amount = buy_amount + sell_amount

                bond_stats.append({
                    'name': sec_name,
                    'buy_amount': buy_amount,
                    'sell_amount': sell_amount,
                    'total_amount': total_amount,
                    'net_buy': buy_amount - sell_amount,
                    'value': total_amount
                })

            df_result = pd.DataFrame(bond_stats)
            df_result = df_result.sort_values(by='total_amount', ascending=False).head(top_n)
        else:
            df_result = pd.DataFrame(columns=['name', 'buy_amount', 'sell_amount', 'total_amount', 'net_buy', 'value'])

        logger.info(f"图表6: 获取 {institution_type} 的交易热点，返回 {len(df_result)} 只债券")
        return df_result

    # ============== 图表7: 全国城投利差热力图 ==============

    def get_chart7_city_invest_spread_heatmap(
        self,
        date: str = None
    ) -> pd.DataFrame:
        """
        图表7: 全国城投利差热力图

        Args:
            date: 交易日期

        Returns:
            pd.DataFrame: 各省份城投债利差
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        # 获取城投债交易数据
        city_bond_sql = f"""
        SELECT d.DT, d.weighted_YTM,
               b.ths_issuer_respond_district_bond_province AS province,
               b.ths_bond_maturity_theory_bond AS tenor
        FROM bond.dealtinfo d
        JOIN bond.basicinfo_credit b ON d.TRADE_CODE = b.trade_code
        WHERE d.DT = '{date}' AND b.ths_is_city_invest_debt_yy_bond = '是';
        """
        df_city = self.db_manager.execute_query(city_bond_sql)

        # 获取国债收益率
        rate_bond_sql = f"""
        SELECT tenor, AVG(weighted_YTM) as risk_free_rate
        FROM (
            SELECT d.weighted_YTM, b.ths_bond_maturity_theory_bond AS tenor
            FROM bond.dealtinfo d
            JOIN bond.basicinfo_rate b ON d.TRADE_CODE = b.trade_code
            WHERE d.DT = '{date}'
        ) as subquery
        GROUP BY tenor;
        """
        df_rate = self.db_manager.execute_query(rate_bond_sql)

        # 合并计算利差
        df_merged = pd.merge(df_city, df_rate, on='tenor', how='left')
        df_merged.dropna(subset=['weighted_YTM', 'risk_free_rate'], inplace=True)
        df_merged['spread'] = (df_merged['weighted_YTM'] - df_merged['risk_free_rate']) * 100  # BP

        # 按省份聚合
        df_result = df_merged.groupby('province')['spread'].mean().reset_index()
        df_result['province'] = df_result['province'].apply(clean_province_name)
        df_result.rename(columns={'province': 'name', 'spread': 'value'}, inplace=True)

        logger.info(f"图表7: 获取城投利差数据，共 {len(df_result)} 个省份")
        return df_result

    # ============== 图表8: 市场核心行为指数 ==============

    def get_chart8_core_behavior_index(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        图表8: 市场核心行为指数

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: RFY、Herding、Duration Flow指数
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # RFY Premium计算
        rfi_sql = f"""
        SELECT d.DT, d.WEIGHTED_YTM as yield, d.TRANSACTION_AMOUNT as deal_amount,
               b.ths_rating_credit_rating_bond AS rating
        FROM bond.dealtinfo d
        JOIN bond.basicinfo_credit b ON d.TRADE_CODE = b.trade_code
        WHERE d.DT BETWEEN '{start_date}' AND '{end_date}'
        """
        df_rfi = self.db_manager.execute_query(rfi_sql)
        df_rfi.dropna(subset=['yield', 'deal_amount', 'rating'], inplace=True)

        if not df_rfi.empty:
            # 计算基准收益率
            df_rfi['weighted_yield_sum'] = df_rfi['yield'] * df_rfi['deal_amount']
            benchmark = df_rfi.groupby(['DT', 'rating']).agg(
                benchmark_yield=('weighted_yield_sum', 'sum'),
                total_deal=('deal_amount', 'sum')
            ).reset_index()
            benchmark['benchmark_yield'] = benchmark['benchmark_yield'] / benchmark['total_deal']

            # 计算RFY Premium
            df_rfi = pd.merge(df_rfi, benchmark[['DT', 'rating', 'benchmark_yield']], on=['DT', 'rating'])
            df_rfi['rfi_premium'] = df_rfi['yield'] - df_rfi['benchmark_yield']

            # 每日市场平均
            df_rfi['weighted_premium'] = df_rfi['rfi_premium'] * df_rfi['deal_amount']
            market_rfi = df_rfi.groupby('DT').agg(
                total_premium=('weighted_premium', 'sum'),
                total_deal=('deal_amount', 'sum')
            ).reset_index()
            market_rfi['market_rfi_index'] = market_rfi['total_premium'] / market_rfi['total_deal']
        else:
            market_rfi = pd.DataFrame(columns=['DT', 'market_rfi_index'])

        # 注意: Herding Index和Duration Flow需要更多数据
        # 这里简化为返回RFI指数

        df_result = market_rfi[['DT', 'market_rfi_index']].rename(columns={
            'DT': 'date',
            'market_rfi_index': 'rfi_premium'
        })

        logger.info(f"图表8: 获取核心行为指数，{len(df_result)} 天")
        return df_result

    # ============== 图表9: 市场风险定价 ==============

    def get_chart9_risk_pricing(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        图表9: 市场风险定价

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 期限利差和信用利差
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 期限利差 (10Y - 1Y 国债)
        term_sql = f"""
        SELECT DT, TRADE_CODE, b.ths_bond_maturity_theory_bond as tenor, WEIGHTED_YTM as yield
        FROM bond.dealtinfo d
        JOIN bond.basicinfo_rate b ON d.TRADE_CODE = b.trade_code
        WHERE d.DT BETWEEN '{start_date}' AND '{end_date}' AND b.ths_bond_type_bond = '国债';
        """
        df_term = self.db_manager.execute_query(term_sql)

        def get_tenor_approx(tenor_str):
            if tenor_str is None:
                return None
            if '10Y' in tenor_str:
                return 10
            if '1Y' in tenor_str:
                return 1
            return None

        df_term['tenor_approx'] = df_term['tenor'].apply(get_tenor_approx)
        df_term.dropna(subset=['tenor_approx', 'yield'], inplace=True)

        daily_yields = df_term.groupby(['DT', 'tenor_approx'])['yield'].mean().unstack()

        if 10 in daily_yields.columns and 1 in daily_yields.columns:
            daily_yields['term_spread'] = daily_yields[10] - daily_yields[1]
        else:
            daily_yields['term_spread'] = None

        df_term_spread = daily_yields[['term_spread']].reset_index()

        # 信用利差
        credit_sql = f"""
        SELECT d.DT, d.WEIGHTED_YTM as yield
        FROM bond.dealtinfo d
        JOIN bond.basicinfo_credit b ON d.TRADE_CODE = b.trade_code
        WHERE d.DT BETWEEN '{start_date}' AND '{end_date}'
            AND b.ths_rating_credit_rating_bond = 'AA+'
            AND b.ths_bond_type_bond = '中期票据'
            AND b.ths_bond_maturity_theory_bond LIKE '%3Y%';
        """
        df_credit = self.db_manager.execute_query(credit_sql)
        daily_mtn = df_credit.groupby('DT')['yield'].mean().reset_index().rename(columns={'yield': 'mtn_yield'})

        # 3Y国债
        df_3y = df_term[df_term['tenor'].str.contains('3Y', na=False) & (df_term['tenor_approx'] != 10) & (df_term['tenor_approx'] != 1)]
        daily_gov = df_3y.groupby('DT')['yield'].mean().reset_index().rename(columns={'yield': 'gov_yield'})

        df_credit_spread = pd.merge(daily_mtn, daily_gov, on='DT', how='inner')
        df_credit_spread['credit_spread'] = (df_credit_spread['mtn_yield'] - df_credit_spread['gov_yield']) * 100

        # 合并
        df_result = pd.merge(df_term_spread, df_credit_spread[['DT', 'credit_spread']], on='DT', how='outer')
        df_result.rename(columns={'DT': 'date'}, inplace=True)
        df_result = df_result.sort_values('date').ffill()

        logger.info(f"图表9: 获取风险定价数据，{len(df_result)} 天")
        return df_result

    # ============== 图表10: 机构行为记分卡 ==============

    def get_chart10_behavior_scorecard(
        self,
        date: str = None,
        institution_type: str = '基金公司及产品'
    ) -> pd.DataFrame:
        """
        图表10: 机构行为记分卡

        Args:
            date: 交易日期
            institution_type: 机构类型

        Returns:
            pd.DataFrame: 各指标评分
        """
        # 简化实现，返回模拟数据
        # 实际实现需要完整的数据支持
        scorecard_data = {
            'indicator': ['RFY Premium', 'Herding Index', 'Net Flow Duration'],
            'value': [0.05, 0.2, 3.5],
            'change': [0.01, -0.05, 0.2]
        }

        df_result = pd.DataFrame(scorecard_data)
        logger.info(f"图表10: 生成 {institution_type} 的行为记分卡")
        return df_result

    # ============== 图表11: 资金面与杠杆温度计 ==============

    def get_chart11_fund_leverage_thermometer(
        self,
        date: str = None
    ) -> Dict[str, Any]:
        """
        图表11: 资金面与杠杆温度计

        Args:
            date: 交易日期

        Returns:
            Dict: 资金面指标
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        sd = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # 银行间回购余额
        interbank_sql = f"""
        SELECT A.dt, sum(A.close) as interbank_repo_balance
        FROM edb.edbdata A
        WHERE A.dt >= '{sd}' AND A.dt <= '{date}' AND A.trade_code ='M0041739'
        GROUP BY A.dt ORDER BY dt
        """
        df_interbank = self.db_manager.execute_query(interbank_sql)

        # 交易所回购余额
        exchange_sql = f"""
        SELECT A.dt, sum(A.close*1000/100000000) as exchange_repo_balance
        FROM edb.edbdata A
        WHERE A.dt >= '{sd}' AND A.dt <= '{date}'
          AND A.trade_code in ('M0340576','M0340580','M0340581')
        GROUP BY A.dt ORDER BY dt
        """
        df_exchange = self.db_manager.execute_query(exchange_sql)

        # 回购利率
        rate_sql = f"""
        SELECT A.DT, A.CLOSE AS DR007, B.CLOSE AS R007
        FROM (SELECT * FROM bond.marketinfo_curve WHERE TRADE_CODE='L001619493' AND DT>='{sd}') A
        LEFT JOIN (SELECT * FROM bond.marketinfo_curve WHERE TRADE_CODE='L004369617' AND DT>='{sd}') B
        ON A.DT=B.DT WHERE A.DT <= '{date}'
        """
        df_rates = self.db_manager.execute_query(rate_sql)

        # 合并数据
        df_balances = pd.merge(df_interbank, df_exchange, on='dt', how='outer')
        df_balances.sort_values('dt', inplace=True)
        df_balances.ffill(inplace=True)
        df_balances['total_repo_balance'] = df_balances['interbank_repo_balance'].fillna(0) + df_balances['exchange_repo_balance'].fillna(0)

        df_final = pd.merge(df_balances, df_rates, left_on='dt', right_on='DT', how='outer')
        df_final.sort_values('dt', inplace=True)
        df_final.ffill(inplace=True)

        # 取最新数据
        if not df_final.empty:
            latest = df_final.tail(1).iloc[0]
            result = {
                'date': latest['dt'],
                'total_repo_balance': latest['total_repo_balance'],
                'dr007': latest['DR007'],
                'r007': latest['R007']
            }
        else:
            result = {'date': date, 'total_repo_balance': 0, 'dr007': 0, 'r007': 0}

        logger.info(f"图表11: 获取资金面数据")
        return result

    # ============== 图表12: 机构大类券种配置流向 ==============

    def get_chart12_asset_flow(
        self,
        start_date: str = None,
        end_date: str = None,
        institution_type: str = '基金公司及产品'
    ) -> pd.DataFrame:
        """
        图表12: 机构大类券种配置流向

        Args:
            start_date: 开始日期
            end_date: 结束日期
            institution_type: 机构类型

        Returns:
            pd.DataFrame: 大类资产净流入
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        sql = f"""
        SELECT `债券类型` as bond_type,
               SUM(`买入交易量（亿元）`) as total_buy,
               SUM(`卖出交易量（亿元）`) as total_sell
        FROM bond.`现券成交分机构统计表`
        WHERE `交易日期` BETWEEN '{start_date}' AND '{end_date}'
          AND `机构类型` = '{institution_type}'
        GROUP BY `债券类型`;
        """

        df = self.db_manager.execute_query(sql)
        df['total_buy'] = clean_numeric_column(df['total_buy'])
        df['total_sell'] = clean_numeric_column(df['total_sell'])
        df['net_flow'] = df['total_buy'] - df['total_sell']

        # 映射到大类资产
        df['asset_class'] = df['bond_type'].apply(map_bond_type_to_asset_class)

        df_result = df.groupby('asset_class')['net_flow'].sum().reset_index()
        df_result.rename(columns={'asset_class': 'name', 'net_flow': 'value'}, inplace=True)

        logger.info(f"图表12: 获取 {institution_type} 的大类资产流向")
        return df_result

    # ============== 图表13: 十大活跃券追踪 ==============

    def get_chart13_top_active_bonds(
        self,
        start_date: str = None,
        end_date: str = None,
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        图表13: 十大活跃券追踪

        Args:
            start_date: 开始日期
            end_date: 结束日期
            top_n: 返回数量

        Returns:
            pd.DataFrame: 活跃债券列表
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        sql = f"""
        SELECT d.TRADE_CODE,
               COALESCE(bc.SEC_NAME, bf.SEC_NAME, br.SEC_NAME) AS SEC_NAME,
               d.transaction_amount/10000 as transaction_amount,
               d.DT
        FROM bond.dealtinfo d
        LEFT JOIN bond.basicinfo_credit bc ON d.TRADE_CODE = bc.trade_code
        LEFT JOIN bond.basicinfo_finance bf ON d.TRADE_CODE = bf.trade_code
        LEFT JOIN bond.basicinfo_rate br ON d.TRADE_CODE = br.trade_code
        WHERE d.DT BETWEEN '{start_date}' AND '{end_date}'
            AND (bc.trade_code IS NOT NULL OR bf.trade_code IS NOT NULL OR br.trade_code IS NOT NULL)
            AND COALESCE(bc.SEC_NAME, bf.SEC_NAME, br.SEC_NAME) IS NOT NULL;
        """

        df = self.db_manager.execute_query(sql)

        if not df.empty:
            bond_stats = df.groupby('SEC_NAME').agg({
                'transaction_amount': 'sum',
                'TRADE_CODE': 'count'
            }).reset_index()
            bond_stats.rename(columns={
                'SEC_NAME': 'name',
                'transaction_amount': 'total_amount',
                'TRADE_CODE': 'trade_count'
            }, inplace=True)

            bond_stats['total_buy'] = bond_stats['total_amount'] / 2
            bond_stats['total_sell'] = bond_stats['total_amount'] / 2
            bond_stats['net_buy'] = 0
            bond_stats['type'] = '成交金额TOP10'
            bond_stats['value'] = bond_stats['total_amount']

            df_result = bond_stats.sort_values('total_amount', ascending=False).head(top_n)
        else:
            df_result = pd.DataFrame(columns=['name', 'total_amount', 'trade_count', 'total_buy', 'total_sell', 'net_buy', 'type', 'value'])

        logger.info(f"图表13: 获取十大活跃券，返回 {len(df_result)} 只")
        return df_result

    # ============== 图表14: 区域城投债资金来源 ==============

    def get_chart14_city_invest_fund_source(
        self,
        start_date: str = None,
        end_date: str = None,
        province: str = '江苏'
    ) -> pd.DataFrame:
        """
        图表14: 区域城投债资金来源

        Args:
            start_date: 开始日期
            end_date: 结束日期
            province: 省份

        Returns:
            pd.DataFrame: 资金来源桑基图数据
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

        # 获取省份城投债列表
        city_bond_sql = f"""
        SELECT DISTINCT `债券简称` as sec_name
        FROM bond.basicinfo_credit
        WHERE ths_is_city_invest_debt_yy_bond = '是'
          AND ths_issuer_respond_district_bond_province = '{province}';
        """
        df_city_bonds = self.db_manager.execute_query(city_bond_sql)
        city_bond_list = tuple(df_city_bonds['sec_name'].tolist())

        if city_bond_list:
            flow_sql = f"""
            SELECT `机构类型` as source, SUM(`买入交易量（亿元）`) as value
            FROM bond.`现券成交分机构统计表`
            WHERE `交易日期` BETWEEN '{start_date}' AND '{end_date}'
              AND `债券简称` IN {city_bond_list}
            GROUP BY `机构类型`;
            """
            df_result = self.db_manager.execute_query(flow_sql)
        else:
            df_result = pd.DataFrame(columns=['source', 'value'])

        df_result.dropna(inplace=True)
        df_result = df_result[df_result['value'] > 0]
        df_result['target'] = province

        logger.info(f"图表14: 获取 {province} 城投债资金来源，{len(df_result)} 个来源")
        return df_result


# ============== 便捷函数 ==============

def create_monitor(db_url: str = None) -> InstitutionBehaviorMonitor:
    """创建监测器实例"""
    db_manager = DatabaseManager(db_url) if db_url else DatabaseManager()
    return InstitutionBehaviorMonitor(db_manager)


if __name__ == '__main__':
    print("=== 机构行为监测核心逻辑模块 ===")
    print("包含14个监测图表的数据处理函数:")
    print("1. 图表1 - 各机构类型每日净交易量")
    print("2. 图表2 - 机构间交易矩阵")
    print("3. 图表3 - 机构期限偏好分析")
    print("4. 图表4 - 机构券种偏好分析")
    print("5. 图表5 - 市场份额时序分析")
    print("6. 图表6 - 机构交易热点分析")
    print("7. 图表7 - 全国城投利差热力图")
    print("8. 图表8 - 市场核心行为指数")
    print("9. 图表9 - 市场风险定价")
    print("10. 图表10 - 机构行为记分卡")
    print("11. 图表11 - 资金面与杠杆温度计")
    print("12. 图表12 - 机构大类券种配置流向")
    print("13. 图表13 - 十大活跃券追踪")
    print("14. 图表14 - 区域城投债资金来源")
