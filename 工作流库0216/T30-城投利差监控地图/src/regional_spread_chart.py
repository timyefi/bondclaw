

import numpy as np
import pandas as pd
import itertools

def get_regional_spread_data(_setting, _cursor_pg):
    """
    计算区域利差数据，生成省级和市级两个DataFrame

    Args:
        _setting (dict): 包含日期和目标期限的设置
        _cursor_pg: PostgreSQL数据库连接

    Returns:
        tuple: 包含raw1, raw2, title的元组
    """

    # --- Part 1: 日期和查询参数设置 ---
    bd = _setting['dt']['startDT']
    ed = _setting['dt']['endDT']
    target_term = str(_setting['target_term'])

    trade_dates = pd.read_sql(f"""SELECT max(dt) as dt FROM hzcurve_credit
                            WHERE target_term='{target_term}' and dt <= '{ed}' AND dt >= '{bd}'""", _cursor_pg)
    date_e = trade_dates['dt'].iloc[0].strftime('%Y-%m-%d')

    max_curve_date_df = pd.read_sql("SELECT MAX(日期) as max_date FROM tc最新所属曲线", _cursor_pg)
    max_curve_date = max_curve_date_df['max_date'].iloc[0].strftime('%Y-%m-%d')

    # --- Part 2: SQL查询 ---
    query = f"""
    WITH base_data AS (
        SELECT
            C.省,
            C.市, -- 尝试获取市级数据
            A.stdyield,
            A.balance
        FROM hzcurve_credit A
        LEFT JOIN (SELECT * FROM tc最新所属曲线 WHERE 日期 = '{max_curve_date}') D ON A.trade_code = D.trade_code
        LEFT JOIN 曲线代码 B ON D.代码 = B.代码
        LEFT JOIN basicinfo_xzqh_ct C ON B.子类 = C.城投区域
        WHERE
            A.dt = '{date_e}'
            AND B.大类 = '城投'
            AND A.target_term = '{target_term}'
            AND A.balance > 0
            AND C.省 IS NOT NULL
    )
    SELECT
        省,
        市,
        stdyield,
        balance
    FROM base_data;
    """

    # --- Part 3: 数据处理 ---
    result = pd.read_sql(query, _cursor_pg)

    # 1. 生成 raw1 (省级)
    raw1 = _generate_raw1(result, date_e)

    # 2. 生成 raw2 (市级)
    raw2 = _generate_raw2(result, date_e)

    # 3. 生成标题
    title = date_e + ' 存续城投利差地图'

    return raw1, raw2, title

def _generate_raw1(result, date_e):
    """生成省级数据 (raw1)"""
    raw1_df = result.groupby('省').apply(lambda x: np.average(x['stdyield'], weights=x['balance'])).reset_index(name='value')
    raw1_df['value'] = round(raw1_df['value'] * 100, 0)
    raw1 = raw1_df.rename(columns={'省': 'name'})
    raw1['dt'] = date_e
    raw1 = raw1[['name', 'dt', 'value']]

    raw1['name'] = raw1['name'].apply(lambda x: str(x).replace('省', '').replace('市', '').replace('自治区', ''))
    raw1['name'] = raw1['name'].apply(lambda x: str(x)[0:2])
    raw1.loc[raw1['name'] == '内蒙', 'name'] = '内蒙古'
    raw1.loc[raw1['name'] == '黑龙', 'name'] = '黑龙江'
    return raw1

def _generate_raw2(result, date_e):
    """生成市级数据 (raw2)"""
    if '市' in result.columns and not result['市'].isnull().all():
        raw2_df = result.groupby(['省', '市']).apply(lambda x: np.average(x['stdyield'], weights=x['balance'])).reset_index(name='CLOSE')
        raw2_df['CLOSE'] = round(raw2_df['CLOSE'] * 100, 0)
        raw2 = raw2_df.rename(columns={'省': 'PROVINCE', '市': 'CITY'})
        raw2['DT'] = date_e
        raw2 = raw2[['PROVINCE', 'DT', 'CITY', 'CLOSE']]
        
        raw2['PROVINCE'] = raw2['PROVINCE'].apply(lambda x: str(x)[0:2])
        raw2.loc[raw2['PROVINCE'] == '内蒙', 'PROVINCE'] = '内蒙古'
        raw2.loc[raw2['PROVINCE'] == '黑龙', 'PROVINCE'] = '黑龙江'
        raw2['CITY'] = raw2['CITY'].apply(lambda x: str(x)[0:2])
        return raw2
    else:
        return pd.DataFrame(columns=['PROVINCE', 'DT', 'CITY', 'CLOSE'])

# # --- 使用示例 ---
# # 在您的环境中，您需要提供 _setting 和 _cursor_pg
# # raw1, raw2, title = get_regional_spread_data(_setting, _cursor_pg)
# # print("--- raw1 (省级数据) ---")
# # print(raw1)
# # print("\n--- raw2 (市级数据) ---")
# # print(raw2)
# # print(f"\n--- 标题 ---\n{title}")
