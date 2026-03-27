#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T31 机构行为监测 - 配置模块

配置文件包含数据库连接配置、图表配置参数、机构类型配置等。
所有敏感信息必须通过环境变量获取。
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """数据库配置数据类"""
    user: str = None
    password: str = None
    host: str = None
    port: str = '3306'
    database: str = None
    charset: str = 'utf8'

    def __post_init__(self):
        """从环境变量获取敏感信息"""
        self.user = self.user or os.environ.get('DB_USER', '')
        self.password = self.password or os.environ.get('DB_PASSWORD', '')
        self.host = self.host or os.environ.get('DB_HOST', 'localhost')
        self.port = os.environ.get('DB_PORT', self.port)
        self.database = self.database or os.environ.get('DB_NAME', 'bond')

    def get_connection_url(self) -> str:
        """获取数据库连接URL"""
        return f'mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}'


@dataclass
class ChartConfig:
    """图表配置数据类"""
    name: str
    title: str
    description: str
    chart_type: str  # bar, line, heatmap, treemap, sankey, etc.
    data_source: str
    params: Dict[str, Any] = field(default_factory=dict)


# 机构类型配置
INSTITUTION_TYPES = [
    '大型商业银行/政策性银行',
    '股份制商业银行',
    '城市商业银行',
    '农村金融机构',
    '证券公司',
    '基金公司及产品',
    '保险公司',
    '境外机构',
    '其他'
]

# 期限分类配置
TENOR_CATEGORIES = [
    '<=1Y',
    '1-3Y',
    '3-5Y',
    '5-7Y',
    '7-10Y',
    '10-15Y',
    '15-20Y',
    '20-30Y',
    '>30Y'
]

# 债券大类配置
BOND_ASSET_CLASSES = {
    '利率债': ['国债', '地方政府债', '央行票据'],
    '金融债': ['金融债', '同业存单'],
    '信用债': ['中期票据', '企业债', '公司债', '短期融资券', 'ABS', '城投债']
}

# 省份列表配置
PROVINCES = [
    '北京', '天津', '河北', '山西', '内蒙古',
    '辽宁', '吉林', '黑龙江', '上海', '江苏',
    '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '广西',
    '海南', '重庆', '四川', '贵州', '云南',
    '西藏', '陕西', '甘肃', '青海', '宁夏',
    '新疆'
]

# 14个监测图表配置
CHART_CONFIGS = [
    ChartConfig(
        name='chart1_daily_net_trading',
        title='图表1-各机构类型每日净交易量',
        description='展示各机构类型在指定日期的净买入交易量（买入-卖出）',
        chart_type='bar',
        data_source='现券成交分机构统计表',
        params={'date': None, 'group_by': '机构类型'}
    ),
    ChartConfig(
        name='chart2_trading_matrix',
        title='图表2-机构间交易矩阵',
        description='展示机构间买卖双方交易规模的矩阵热力图',
        chart_type='heatmap',
        data_source='dealtinfo + 现券成交分机构统计表',
        params={'date': None, 'simulate_parties': True}
    ),
    ChartConfig(
        name='chart3_tenor_preference',
        title='图表3-机构期限偏好分析',
        description='展示指定机构对不同期限债券的交易偏好',
        chart_type='treemap',
        data_source='现券成交分机构统计表',
        params={'date': None, 'institution_type': None}
    ),
    ChartConfig(
        name='chart4_bond_type_preference',
        title='图表4-机构券种偏好分析',
        description='展示指定机构对不同券种的交易偏好',
        chart_type='treemap',
        data_source='现券成交分机构统计表',
        params={'date': None, 'institution_type': None}
    ),
    ChartConfig(
        name='chart5_market_share_timeseries',
        title='图表5-市场份额时序分析',
        description='展示各机构市场份额随时间的变化趋势',
        chart_type='line',
        data_source='现券成交分机构统计表',
        params={'start_date': None, 'end_date': None}
    ),
    ChartConfig(
        name='chart6_trading_hotspots',
        title='图表6-机构交易热点分析',
        description='展示指定机构最活跃的债券交易',
        chart_type='bar',
        data_source='dealtinfo + 现券成交分机构统计表',
        params={'date': None, 'institution_type': None, 'top_n': 10}
    ),
    ChartConfig(
        name='chart7_city_invest_spread_heatmap',
        title='图表7-全国城投利差热力图',
        description='展示全国各省城投债相对国债的信用利差',
        chart_type='heatmap',
        data_source='dealtinfo + basicinfo_credit',
        params={'date': None}
    ),
    ChartConfig(
        name='chart8_core_behavior_index',
        title='图表8-市场核心行为指数',
        description='展示RFY Premium、Herding Index、Duration Net Flow等指数',
        chart_type='line',
        data_source='dealtinfo + basicinfo_*',
        params={'start_date': None, 'end_date': None}
    ),
    ChartConfig(
        name='chart9_risk_pricing',
        title='图表9-市场风险定价',
        description='展示期限利差和信用利差的变化趋势',
        chart_type='line',
        data_source='dealtinfo + basicinfo_*',
        params={'start_date': None, 'end_date': None}
    ),
    ChartConfig(
        name='chart10_behavior_scorecard',
        title='图表10-机构行为记分卡',
        description='展示指定机构的核心行为指标评分',
        chart_type='scorecard',
        data_source='dealtinfo + basicinfo_*',
        params={'date': None, 'institution_type': None}
    ),
    ChartConfig(
        name='chart11_fund_leverage_thermometer',
        title='图表11-资金面与杠杆温度计',
        description='展示回购余额、回购利率等资金面指标',
        chart_type='scorecard',
        data_source='edb.edbdata + bond.marketinfo_curve',
        params={'date': None}
    ),
    ChartConfig(
        name='chart12_asset_flow',
        title='图表12-机构大类券种配置流向',
        description='展示指定机构在各券种上的资金净流入',
        chart_type='waterfall',
        data_source='现券成交分机构统计表',
        params={'start_date': None, 'end_date': None, 'institution_type': None}
    ),
    ChartConfig(
        name='chart13_top_active_bonds',
        title='图表13-十大活跃券追踪',
        description='展示市场上最活跃的债券TOP10',
        chart_type='bar',
        data_source='dealtinfo + basicinfo_*',
        params={'start_date': None, 'end_date': None, 'top_n': 10}
    ),
    ChartConfig(
        name='chart14_city_invest_fund_source',
        title='图表14-区域城投债资金来源',
        description='展示指定省份城投债的资金来源机构分布',
        chart_type='sankey',
        data_source='现券成交分机构统计表 + basicinfo_credit',
        params={'start_date': None, 'end_date': None, 'province': None}
    )
]


def get_default_db_config() -> DatabaseConfig:
    """获取默认数据库配置"""
    return DatabaseConfig(database='bond')


def get_chart_config(chart_name: str) -> ChartConfig:
    """根据图表名称获取配置"""
    for config in CHART_CONFIGS:
        if config.name == chart_name:
            return config
    raise ValueError(f"未找到图表配置: {chart_name}")


def get_all_chart_configs() -> List[ChartConfig]:
    """获取所有图表配置"""
    return CHART_CONFIGS


# 期限映射函数配置
def map_tenor_to_category(term_str: str) -> str:
    """
    将期限文本转换为分类

    Args:
        term_str: 期限字符串，如 '5Y+', '180D'

    Returns:
        str: 期限分类
    """
    import re

    if term_str is None:
        return '1-3Y'  # 默认

    if 'Y+' in term_str:
        match = re.match(r'(\d+\.?\d*)Y', term_str)
        if match:
            years = float(match.group(1))
        else:
            years = float(term_str.replace('Y', '').replace('+NY', ''))

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


if __name__ == '__main__':
    # 测试配置
    print("=== 机构行为监测配置测试 ===")
    print(f"机构类型数量: {len(INSTITUTION_TYPES)}")
    print(f"图表配置数量: {len(CHART_CONFIGS)}")

    # 测试期限映射
    test_tenors = ['0.5Y+', '2Y+', '5Y+', '10Y+', '30Y+', '180D']
    print("\n期限映射测试:")
    for tenor in test_tenors:
        print(f"  {tenor} -> {map_tenor_to_category(tenor)}")

    # 测试债券类型映射
    test_bond_types = ['国债', '金融债', '中期票据', '企业债']
    print("\n债券类型映射测试:")
    for bond_type in test_bond_types:
        print(f"  {bond_type} -> {map_bond_type_to_asset_class(bond_type)}")
