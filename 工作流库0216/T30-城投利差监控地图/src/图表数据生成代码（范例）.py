import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta, time
import re

ed = _setting['dt']

def clean_province_name(name):
    """最终的省级名称清理函数"""
    if pd.isna(name):
        return name
    return re.sub(r'省|市|自治区|回族自治区|维吾尔自治区|壮族自治区', '', name)

def run_source_query(db_manager, level, date_b, date_e, target_term):
    """最终、最可靠的SQL查询版本"""
    
    inner_select_clause = "C.省"
    outer_group_by_clause = "省"

    if level == 'city':
        inner_select_clause = "C.省, C.市"
        outer_group_by_clause = "省, 市"

    query = f"""
    SELECT 
        {outer_group_by_clause},
        avg(收益率4) as 收益率
    FROM (
        SELECT {outer_group_by_clause}, 收益率4 FROM  
            (SELECT
            A.DT, 
            {inner_select_clause},
            LAST_VALUE(SUM(A.stdyield*A.balance)/SUM(A.balance)) OVER (PARTITION BY {inner_select_clause} ORDER BY A.dt) AS 收益率4
            FROM hzcurve_credit A
            LEFT JOIN (SELECT * FROM tc最新所属曲线 WHERE 日期 = (SELECT MAX(日期) FROM tc最新所属曲线)) D ON A.trade_code=D.trade_code
            LEFT JOIN 曲线代码 B ON D.代码=B.代码
            LEFT JOIN basicinfo_xzqh_ct C ON B.子类=C.城投区域
            WHERE A.dt >='{date_b}' and B.大类='城投' AND A.target_term='{target_term}' AND A.balance>0 AND C.省 IS NOT NULL AND C.市 IS NOT NULL
            GROUP BY {inner_select_clause}, A.dt
            ) SQ
        WHERE SQ.DT='{date_e}'
    ) AS subquery
    GROUP BY {outer_group_by_clause}
    """
    return pd.read_sql(query,db_manager)


db_manager_pg = _cursor_pg
bd = pd.to_datetime(ed) - pd.DateOffset(days=30)

target_term = '2'
trade_dates1_df = pd.read_sql(f"""SELECT Distinct dt as "日期" FROM hzcurve_credit WHERE target_term={target_term} and dt <= '{ed}' AND dt >= '{bd}'""",db_manager_pg)
trade_dates1_df['日期'] = pd.to_datetime(trade_dates1_df['日期'])
date_b = trade_dates1_df['日期'].min().strftime('%Y-%m-%d')
date_e = trade_dates1_df['日期'].max().strftime('%Y-%m-%d')

# --- 2. 获取并处理源数据 ---
province_source_df = run_source_query(db_manager_pg, 'province', date_b, date_e, target_term)
city_source_df = run_source_query(db_manager_pg, 'city', date_b, date_e, target_term)

# --- 3. 格式化数据 (在Pandas中进行重命名和清理) ---
province_source_df.rename(columns={'省': 'name'}, inplace=True)
city_source_df.rename(columns={'省': 'PROVINCE', '市': 'CITY'}, inplace=True)

province_source_df['name'] = province_source_df['name'].apply(clean_province_name)
city_source_df['PROVINCE'] = city_source_df['PROVINCE'].apply(clean_province_name)
city_source_df['CITY'] = city_source_df['CITY'].apply(lambda x: str(x)[0:2])

province = province_source_df[['name', '收益率']].rename(columns={'收益率': 'value'})
city = city_source_df[['PROVINCE', 'CITY', '收益率']].rename(columns={'收益率': 'CLOSE'})

province['dt'] = date_e
city['dt'] = date_e
province['value']=round(province['value'],2)
city['CLOSE']=round(city['CLOSE'],2)
min_value=province['value'].min()
max_value=province['value'].max()

# --- 4. 新增：计算每个省份的最大和最小值 ---
province_stats = city.groupby('PROVINCE')['CLOSE'].agg([('min_value', 'min'), ('max_value', 'max')]).reset_index()
province_stats.rename(columns={'PROVINCE': 'name'}, inplace=True)

title='平均收益率%（隐含AA-及以上）'
