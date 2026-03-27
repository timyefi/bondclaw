#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T31 机构行为监测 - 工具函数模块

包含可复用的辅助函数，如数据库操作、数据清洗、可视化等。
"""

import os
import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== 数据库工具 ==============

class DatabaseManager:
    """简化版数据库管理器"""

    def __init__(self, connection_url: str = None):
        """
        初始化数据库管理器

        Args:
            connection_url: SQLAlchemy连接URL
        """
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool

        self.connection_url = connection_url or self._get_default_connection_url()
        self.engine = None

        if self.connection_url:
            try:
                self.engine = create_engine(
                    self.connection_url,
                    poolclass=NullPool,
                    echo=False,
                    pool_recycle=3600
                )
                logger.info("数据库连接已建立")
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                raise

    def _get_default_connection_url(self) -> str:
        """从环境变量获取默认连接URL"""
        user = os.environ.get('DB_USER', '')
        password = os.environ.get('DB_PASSWORD', '')
        host = os.environ.get('DB_HOST', 'localhost')
        port = os.environ.get('DB_PORT', '3306')
        database = os.environ.get('DB_NAME', 'bond')

        if not all([user, password, host]):
            logger.warning("数据库配置不完整，请设置环境变量")
            return None

        return f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8'

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        执行查询并返回DataFrame

        Args:
            sql: SQL查询语句

        Returns:
            pd.DataFrame: 查询结果
        """
        if self.engine is None:
            raise ValueError("数据库未连接")

        try:
            df = pd.read_sql(sql, self.engine)
            logger.info(f"查询执行成功，返回 {len(df)} 行数据")
            return df
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            self.execute_query("SELECT 1")
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("数据库连接已关闭")


# ============== 数据清洗工具 ==============

def clean_numeric_column(series: pd.Series, default_value: float = 0.0) -> pd.Series:
    """
    清洗数值列，将特殊值转换为数值

    Args:
        series: 数据列
        default_value: 默认值

    Returns:
        pd.Series: 清洗后的数据列
    """
    # 替换 '--' 为 NaN
    series = series.replace('--', np.nan)
    # 转换为数值类型
    series = pd.to_numeric(series, errors='coerce')
    # 填充默认值
    return series.fillna(default_value)


def clean_date_column(series: pd.Series) -> pd.Series:
    """
    清洗日期列

    Args:
        series: 日期列

    Returns:
        pd.Series: 清洗后的日期列
    """
    return pd.to_datetime(series).dt.date


def get_valid_date_range(end_date: str = None, days: int = 30) -> Tuple[str, str]:
    """
    获取有效的日期范围

    Args:
        end_date: 结束日期，默认为今天
        days: 天数

    Returns:
        Tuple[str, str]: (开始日期, 结束日期)
    """
    if end_date:
        ed = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        ed = datetime.now()

    sd = ed - timedelta(days=days)

    return sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d')


# ============== 期限映射工具 ==============

def map_tenor_to_category(term_str: str) -> str:
    """
    将期限文本转换为分类

    Args:
        term_str: 期限字符串，如 '5Y+', '180D'

    Returns:
        str: 期限分类
    """
    if term_str is None:
        return '1-3Y'  # 默认

    if 'Y+' in term_str:
        match = re.match(r'(\d+\.?\d*)Y', term_str)
        if match:
            years = float(match.group(1))
        else:
            try:
                years = float(term_str.replace('Y', '').replace('+NY', ''))
            except ValueError:
                return '1-3Y'

        if years <= 1:
            return '<=1Y'
        if years <= 3:
            return '1-3Y'
        if years <= 5:
            return '3-5Y'
        if years <= 7:
            return '5-7Y'
        if years <= 10:
            return '7-10Y'
        if years <= 15:
            return '10-15Y'
        if years <= 20:
            return '15-20Y'
        if years <= 30:
            return '20-30Y'
        return '>30Y'

    elif 'D' in term_str:
        match = re.match(r'(\d+\.?\d*)D', term_str)
        if match:
            days = float(match.group(1))
            years = days / 365
            if years <= 1:
                return '<=1Y'
        return '1-3Y'

    return '1-3Y'  # 默认


def parse_tenor_to_years(tenor_str: str) -> float:
    """
    将期限字符串转换为年数

    Args:
        tenor_str: 期限字符串

    Returns:
        float: 年数
    """
    if isinstance(tenor_str, str):
        if 'Y' in tenor_str:
            try:
                return float(tenor_str.replace('Y', ''))
            except ValueError:
                pass
        if 'D' in tenor_str:
            try:
                return float(tenor_str.replace('D', '')) / 365
            except ValueError:
                pass
    return np.nan


# ============== 债券类型映射工具 ==============

BOND_ASSET_CLASSES = {
    '利率债': ['国债', '地方政府债', '央行票据'],
    '金融债': ['金融债', '同业存单'],
    '信用债': ['中期票据', '企业债', '公司债', '短期融资券', 'ABS', '城投债']
}


def map_bond_type_to_asset_class(bond_type_str: str) -> str:
    """
    将债券类型映射到大类资产

    Args:
        bond_type_str: 债券类型

    Returns:
        str: 大类资产名称
    """
    for asset_class, bond_types in BOND_ASSET_CLASSES.items():
        if bond_type_str in bond_types:
            return asset_class
    return '信用债'  # 默认


def clean_province_name(name: str) -> str:
    """
    清理省份名称

    Args:
        name: 省份名称

    Returns:
        str: 清理后的省份名称
    """
    if pd.isna(name):
        return name
    return re.sub(r'省|市|自治区|回族自治区|维吾尔自治区|壮族自治区', '', name)


# ============== 可视化工具 ==============

def setup_chinese_font():
    """设置中文字体支持"""
    import matplotlib.pyplot as plt
    import matplotlib as mpl

    # Windows系统常用中文字体
    font_names = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi']

    for font_name in font_names:
        try:
            mpl.rcParams['font.sans-serif'] = [font_name]
            mpl.rcParams['axes.unicode_minus'] = False
            logger.info(f"已设置中文字体: {font_name}")
            return True
        except Exception:
            continue

    logger.warning("未找到合适的中文字体")
    return False


def format_number(value: float, decimal_places: int = 2) -> str:
    """
    格式化数字显示

    Args:
        value: 数值
        decimal_places: 小数位数

    Returns:
        str: 格式化后的字符串
    """
    if abs(value) >= 100000000:  # 亿
        return f"{value / 100000000:.{decimal_places}f}亿"
    elif abs(value) >= 10000:  # 万
        return f"{value / 10000:.{decimal_places}f}万"
    else:
        return f"{value:.{decimal_places}f}"


# ============== 模拟交易对手工具 ==============

def simulate_trading_parties(
    dealtinfo_df: pd.DataFrame,
    stats_df: pd.DataFrame,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    模拟交易对手（买卖双方机构类型）

    Args:
        dealtinfo_df: 交易明细数据
        stats_df: 机构交易统计数据（用于概率分布）
        random_seed: 随机种子

    Returns:
        pd.DataFrame: 增加了买方和卖方机构类型的数据
    """
    np.random.seed(random_seed)

    def get_prob_dist(stats_df, tenor, bond_type, trade_side):
        """计算买/卖方的概率分布"""
        market_slice = stats_df[
            (stats_df['期限'] == tenor) & (stats_df['债券类型'] == bond_type)
        ]
        col = 'buy_vol' if trade_side == 'buy' else 'sell_vol'
        total_vol = market_slice[col].sum()

        if total_vol == 0:
            market_slice = stats_df
            total_vol = market_slice[col].sum()
            if total_vol == 0:
                return None

        market_slice = market_slice.copy()
        market_slice['prob'] = market_slice[col] / total_vol
        return market_slice[['机构类型', 'prob']]

    def assign_party_type(row):
        # 获取买方概率分布并抽样
        buy_dist = get_prob_dist(stats_df, row['tenor_category'], row['bond_type'], 'buy')
        if buy_dist is not None:
            row['party_type_b'] = np.random.choice(buy_dist['机构类型'].values, p=buy_dist['prob'].values)
        else:
            row['party_type_b'] = '未知'

        # 获取卖方概率分布并抽样
        sell_dist = get_prob_dist(stats_df, row['tenor_category'], row['bond_type'], 'sell')
        if sell_dist is not None:
            row['party_type_s'] = np.random.choice(sell_dist['机构类型'].values, p=sell_dist['prob'].values)
        else:
            row['party_type_s'] = '未知'

        return row

    # 应用模拟
    result_df = dealtinfo_df.apply(lambda row: assign_party_type(row), axis=1)
    return result_df


# ============== 导出工具 ==============

def export_to_json(df: pd.DataFrame, filepath: str):
    """
    导出DataFrame到JSON文件

    Args:
        df: 数据框
        filepath: 文件路径
    """
    df.to_json(filepath, orient='records', force_ascii=False, indent=2)
    logger.info(f"数据已导出到: {filepath}")


def export_to_csv(df: pd.DataFrame, filepath: str):
    """
    导出DataFrame到CSV文件

    Args:
        df: 数据框
        filepath: 文件路径
    """
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logger.info(f"数据已导出到: {filepath}")


if __name__ == '__main__':
    # 测试工具函数
    print("=== 工具函数测试 ===")

    # 测试期限映射
    test_tenors = ['0.5Y+', '2Y+', '5Y+', '10Y+', '30Y+', '180D', '360D']
    print("\n期限映射测试:")
    for tenor in test_tenors:
        print(f"  {tenor} -> {map_tenor_to_category(tenor)}")

    # 测试债券类型映射
    test_bond_types = ['国债', '金融债', '中期票据', '企业债', '同业存单']
    print("\n债券类型映射测试:")
    for bond_type in test_bond_types:
        print(f"  {bond_type} -> {map_bond_type_to_asset_class(bond_type)}")

    # 测试日期范围
    sd, ed = get_valid_date_range(days=30)
    print(f"\n日期范围测试: {sd} ~ {ed}")

    # 测试数字格式化
    test_values = [123, 12345, 123456789, -123456789]
    print("\n数字格式化测试:")
    for value in test_values:
        print(f"  {value} -> {format_number(value)}")
