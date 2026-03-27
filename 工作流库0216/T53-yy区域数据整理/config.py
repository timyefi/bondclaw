# -*- coding: utf-8 -*-
"""
T53-yy区域数据整理 配置文件

本模块包含企业预警通API和数据库连接的配置信息。
敏感信息通过环境变量获取，请确保设置以下环境变量：
- RATINGDOG_USERNAME: 企业预警通用户名
- RATINGDOG_PASSWORD: 企业预警通密码
- RATINGDOG_PHONE_CODE: 国际电话区号（默认86）
- DB_HOST: 数据库主机地址
- DB_PORT: 数据库端口
- DB_USER: 数据库用户名
- DB_PASSWORD: 数据库密码
- DB_NAME: 数据库名称
"""

import os
import sqlalchemy
import sqlalchemy.pool


# ============================================================
# 企业预警通 API 配置
# ============================================================

RATINGDOG_USERNAME = os.environ.get('RATINGDOG_USERNAME', '')
RATINGDOG_PASSWORD = os.environ.get('RATINGDOG_PASSWORD', '')
RATINGDOG_PHONE_CODE = os.environ.get('RATINGDOG_PHONE_CODE', '86')

# API端点
RATINGDOG_LOGIN_URL = 'https://auth.ratingdog.cn/api/TokenAuth/Authenticate'
RATINGDOG_DATA_URL = 'https://host.ratingdog.cn/api/services/app/AdministrativeDivisionData/GetAdministrativeDivisionDatas'


# ============================================================
# 数据库配置
# ============================================================

DB_HOST = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'yq')

# 目标表
SOURCE_TABLE = 'yq.yyqy'
REGION_TABLE = 'yq.xzqh_yy'


# ============================================================
# 数据指标配置
# ============================================================

# 经济指标
ECONOMIC_INDICATORS = [
    "GDP", "GDPGrowthRate", "GDPPerCaptita", "InvestmentInFixedAssets",
    "InvestmentInFixedAssetsGrowthRate", "PermanentResidents", "GDPPerCaptita_model"
]

# 财政指标
FISCAL_INDICATORS = [
    "FiscalSelfsufficiencyRate", "TaxPercentage", "GeneralBudgetRevenue",
    "GeneralBudgetRevenueGrowthRate", "TaxIncome", "TaxIncomeGrowthRate",
    "TransferIncome", "SubsidyIncomeFromSuperiors", "TotalGeneralPublicBudgetRevenue",
    "GeneralBudgetExpenditure", "GeneralBudgetExpenditureGrowthRate",
    "GeneralBudgetRevenueGrowthRate_NaturalCaliber", "TaxIncome_NaturalCaliber",
    "GovernmentFundIncome", "GovernmentFundIncomeGrowthRate", "LandSaleRevenue",
    "GovernmentFundExpenditure", "GeneralDebtLimit", "SpecialDebtLimit",
    "GeneralDebtBalance", "SpecialDebtBalance"
]

# 金融指标
FINANCIAL_INDICATORS = [
    "RMBBalanceOfDeposits", "ForeignCurrencyBalanceOfDeposits",
    "RMBBalanceOfLoad", "ForeignCurrencyBalanceOfLoad",
    "TotalFinancialAssets", "NonperformingLoanRatio"
]

# 隐性债务指标
IMPLICIT_DEBT_INDICATORS = [
    "ImplicitDebtResolution", "YYRatio", "InterestDebt", "SurvivalAmount",
    "ThreeYearsCompositeGrowthRate", "FiveYearsCompositeGrowthRate",
    "InterestDebtYY", "InterestDebtYYBankLoan", "InterestDebtYYBonds",
    "InterestDebtYYNonStandard", "InterestDebtYYOther"
]

# 房地产指标
REAL_ESTATE_INDICATORS = [
    "MHPI_YoY", "MHPI_MoM", "ResidentialHouseTradeArea",
    "ResidentialHouseTradeAmount", "ResidentialHouseTradeAvgPrice",
    "SecondhandResidentialHouseTradeArea"
]

# 城市基础设施指标
INFRASTRUCTURE_INDICATORS = [
    "UrbanArea", "UrbanPopulation", "MetropolitanArea", "MetropolitanPopulation",
    "BuiltUpArea", "InvestInFAIOfCMPF", "NewFixedAssetOfCMPF",
    "LengthOfRoad", "RoadLengthInBuiltUpArea", "RoadSurface", "RoadAreaInBuiltUpArea",
    "NumberOfBridge", "MajorBridgesAndSuperMajorBridges",
    "ComprehensiveProductionCapacityOfTapWater", "LengthOfWaterSupplyPipeline",
    "WaterPopulation", "LengthOfDrainagePipe", "TotalSewageDischarge", "TotalSewageTreatment"
]

# 合并所有指标
ALL_INDICATORS = (
    ECONOMIC_INDICATORS + FISCAL_INDICATORS + FINANCIAL_INDICATORS +
    IMPLICIT_DEBT_INDICATORS + REAL_ESTATE_INDICATORS + INFRASTRUCTURE_INDICATORS
)

# 数据类别
DATA_CATEGORY_TYPES = [1001, 1002, 1003]  # 经济、财政、金融


# ============================================================
# 行政区域配置
# ============================================================

# 直辖市列表
DIRECT_MUNICIPALITIES = ['北京市', '上海市', '天津市', '重庆市']

# 省直辖县级行政区划列表
PROVINCE_DIRECT_COUNTIES = [
    '五家渠市', '北屯市', '双河市', '可克达拉市', '图木舒克市', '新星市', '昆玉市',
    '石河子市', '胡杨河市', '铁门关市', '阿拉尔市', '济源市', '万宁市', '东方市',
    '临高县', '乐东黎族自治县', '五指山市', '保亭黎族苗族自治县', '定安县', '屯昌县',
    '文昌市', '昌江黎族自治县', '澄迈县', '琼中黎族苗族自治县', '琼海市',
    '白沙黎族自治县', '陵水黎族自治县', '仙桃市', '天门市', '潜江市', '神农架林区'
]


# ============================================================
# 辅助函数
# ============================================================

def get_database_engine():
    """
    创建数据库连接引擎

    Returns:
        sqlalchemy.Engine: 数据库连接引擎
    """
    connection_string = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = sqlalchemy.create_engine(
        connection_string,
        poolclass=sqlalchemy.pool.NullPool
    )
    return engine


def get_api_headers(access_token):
    """
    获取企业预警通API请求头

    Args:
        access_token: 认证令牌

    Returns:
        dict: API请求头字典
    """
    headers = {
        ".Aspnetcore.Culture": "zh-Hans",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "Devicechannel": "gclife_bmp_pc",
        "Origin": "https://www.ratingdog.cn",
        "Priority": "u=1, i",
        "Ratingdog.Tenantid": "114",
        "Referer": "https://www.ratingdog.cn/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    return headers


def get_login_headers():
    """
    获取登录API请求头

    Returns:
        dict: 登录请求头字典
    """
    headers = {
        '.Aspnetcore.Culture': 'zh-Hans',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Devicechannel': 'gclife_bmp_pc',
        'Origin': 'https://www.ratingdog.cn',
        'Ratingdog.Tenantid': '114',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    return headers


# ============================================================
# 配置验证
# ============================================================

def validate_config():
    """
    验证配置是否完整

    Returns:
        tuple: (是否有效, 缺失的配置列表)
    """
    missing = []

    if not RATINGDOG_USERNAME:
        missing.append('RATINGDOG_USERNAME')
    if not RATINGDOG_PASSWORD:
        missing.append('RATINGDOG_PASSWORD')
    if not DB_USER:
        missing.append('DB_USER')
    if not DB_PASSWORD:
        missing.append('DB_PASSWORD')

    is_valid = len(missing) == 0
    return is_valid, missing


if __name__ == '__main__':
    # 验证配置
    is_valid, missing = validate_config()
    if is_valid:
        print("配置验证通过")
    else:
        print(f"配置缺失: {missing}")
        print("请设置相应的环境变量")
