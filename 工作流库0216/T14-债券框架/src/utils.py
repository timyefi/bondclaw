# -*- coding: utf-8 -*-
"""
债券框架 - 数据获取模块
"""

import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy.pool import NullPool

import sys
sys.path.insert(0, str(__file__).replace('src\\utils.py', ''))
import config


def get_sql_engine():
    """获取数据库连接引擎"""
    return sqlalchemy.create_engine(
        config.get_database_url(),
        poolclass=NullPool
    )


def get_yield_curve_data(code, start_date=None, end_date=None):
    """
    获取国债收益率数据

    参数:
        code: 收益率曲线代码
        start_date: 开始日期
        end_date: 结束日期

    返回:
        pd.DataFrame: 包含日期和收益率数据
    """
    sql_engine = get_sql_engine()
    sql = f"""
    SELECT dt, close
    FROM bond.marketinfo_curve
    WHERE trade_code='{code}'
    """
    df = pd.read_sql(sql, sql_engine)
    df['dt'] = pd.to_datetime(df['dt'])
    if start_date:
        df = df[df['dt'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['dt'] <= pd.to_datetime(end_date)]
    df.columns = ['date', 'yield_rate']
    return df


def get_standardized_data(code, start_date=None, end_date=None):
    """
    标准化取数函数，对任何code可输出剔除异常值、插值到日度、
    并方便与国债收益率日度数据进行回归检验的dataframe

    参数:
        code: 因子代码
        start_date: 开始日期
        end_date: 结束日期

    返回:
        pd.DataFrame: 包含日期和标准化后的因子值
    """
    sql_engine = get_sql_engine()
    sql = f"""
    SELECT dt, close
    FROM bond.marketinfo_curve
    WHERE trade_code='{code}'
    UNION
    SELECT dt, close
    FROM edb.edbdata
    WHERE trade_code='{code}'
    """

    df = pd.read_sql(sql, sql_engine)
    df['dt'] = pd.to_datetime(df['dt'])

    if start_date:
        df = df[df['dt'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['dt'] <= pd.to_datetime(end_date)]

    # 异常值处理
    df = df.dropna()
    mean = df['close'].mean()
    std = df['close'].std()
    df = df[(df['close'] > mean - 3*std) & (df['close'] < mean + 3*std)]

    df.columns = ['date', 'value']
    return df


def load_financial_data(factor_code, start_date=None):
    """加载资金因子数据"""
    if start_date is None:
        start_date = config.ANALYSIS_START
    sql_engine = get_sql_engine()

    sql = f"""
    SELECT dt, close
    FROM (
        SELECT dt, close
        FROM bond.marketinfo_curve
        WHERE trade_code='{factor_code}'
        UNION ALL
        SELECT dt, close
        FROM edb.edbdata
        WHERE trade_code='{factor_code}'
    ) t
    WHERE dt >= '{start_date}'
    ORDER BY dt
    """
    df = pd.read_sql(sql, sql_engine).rename(columns={'close': 'fund_rate'})
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.set_index('dt')
    return df.sort_index()


def load_yield_data(yield_code, start_date=None):
    """加载收益率曲线数据"""
    if start_date is None:
        start_date = config.ANALYSIS_START
    sql_engine = get_sql_engine()

    sql = f"""
    SELECT dt, close AS yield_rate
    FROM bond.marketinfo_curve
    WHERE trade_code='{yield_code}' AND dt >= '{start_date}'
    """
    df = pd.read_sql(sql, sql_engine)
    df['dt'] = pd.to_datetime(df['dt'])
    df = df.set_index('dt')
    return df.sort_index()


def get_curve_options_data():
    """获取曲线选项数据"""
    sql_engine = get_sql_engine()
    sql = '''SELECT
    CASE
        WHEN INSTR(SEC_NAME, ':') > 0 THEN
            CASE
                WHEN LEFT(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), 2) = '中债' THEN
                    CASE
                        WHEN INSTR(REPLACE(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '中债', ''), '(') > 0 THEN
                            SUBSTRING(REPLACE(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '中债', ''), 1, INSTR(REPLACE(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '中债', ''), '(') - 1)
                        ELSE
                            REPLACE(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '中债', '')
                    END
                ELSE
                    CASE
                        WHEN INSTR(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '(') > 0 THEN
                            SUBSTRING(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), 1, INSTR(SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1), '(') - 1)
                        ELSE
                            SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, ':') - 1)
                    END
            END
        ELSE
            CASE
                WHEN LEFT(SEC_NAME, 2) = '中债' THEN
                    CASE
                        WHEN INSTR(REPLACE(SEC_NAME, '中债', ''), '(') > 0 THEN
                            SUBSTRING(REPLACE(SEC_NAME, '中债', ''), 1, INSTR(REPLACE(SEC_NAME, '中债', ''), '(') - 1)
                        ELSE
                            REPLACE(SEC_NAME, '中债', '')
                    END
                ELSE
                    CASE
                        WHEN INSTR(SEC_NAME, '(') > 0 THEN
                            SUBSTRING(SEC_NAME, 1, INSTR(SEC_NAME, '(') - 1)
                        ELSE
                            SEC_NAME
                    END
            END
    END AS SEC_NAME,
    LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * ((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限,
    concat(
        SUBSTRING_INDEX(
            SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1, LOCATE(')', REPLACE(classify2, '＋', '+'))-LOCATE('(', REPLACE(classify2, '＋', '+'))-1),
            ' ',
            1
        ),
        ''
    ) AS 隐含评级
    FROM bond.basicinfo_curve
    '''
    with sql_engine.connect() as conn:
        df_curve = pd.read_sql(sql, conn)
    df_curve['隐含评级'] = df_curve['隐含评级'].str.replace(r'[^a-zA-Z\+\-]', '', regex=True)
    df_curve = df_curve[df_curve['SEC_NAME'].notna() & (df_curve['SEC_NAME'] != '')]
    return df_curve


def build_curve_options_json(df_curve):
    """构建曲线选项JSON结构"""
    series_list = []
    for sec_name in df_curve['SEC_NAME'].unique():
        level1 = {
            "label": sec_name,
            "value": sec_name,
            "children": []
        }
        df_sec_name = df_curve[df_curve['SEC_NAME'] == sec_name]
        for curve_duration in df_sec_name['曲线期限'].unique():
            level2 = {
                "label": str(curve_duration) + "年",
                "value": str(curve_duration),
                "children": []
            }
            df_duration = df_sec_name[df_sec_name['曲线期限'] == curve_duration]
            for implicit_rating in df_duration['隐含评级'].unique():
                level3 = {
                    "label": implicit_rating,
                    "value": implicit_rating
                }
                level2["children"].append(level3)
            level1["children"].append(level2)
        series_list.append(level1)
    return {"_series": series_list}
