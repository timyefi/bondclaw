import sys
import os
import re
import pandas as pd

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
        round(((sum(收益率4)-sum(收益率1))*100)::numeric,2) as "近7天收益率变化bp",
        round(((sum(收益率4)-sum(收益率2))*100)::numeric,2) as "近1个月收益率变化bp"
    FROM (
        SELECT {outer_group_by_clause}, 收益率1, 收益率2, 收益率3, 收益率4 FROM  
            (SELECT
            A.DT, 
            {inner_select_clause},
            FIRST_VALUE(SUM(A.stdyield*A.balance)/SUM(A.balance)) OVER (PARTITION BY {inner_select_clause} ORDER BY A.dt RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW) AS 收益率1,
            FIRST_VALUE(SUM(A.stdyield*A.balance)/SUM(A.balance)) OVER (PARTITION BY {inner_select_clause} ORDER BY A.dt RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW) AS 收益率2,
            FIRST_VALUE(SUM(A.stdyield*A.balance)/SUM(A.balance)) OVER (PARTITION BY {inner_select_clause} ORDER BY A.dt) AS 收益率3,
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
    return db_manager.execute_query(query)

def main():
    """主执行函数"""
    db_manager_pg = get_tsdb_database_manager()

    # --- 1. 获取日期参数 ---
    bd = '2025-06-22'
    ed = '2025-07-22'
    bd = pd.to_datetime(ed) - pd.DateOffset(days=30)

    target_term = '2'
    trade_dates1_df = db_manager_pg.execute_query(f"""SELECT Distinct dt as "日期" FROM hzcurve_credit WHERE target_term={target_term} and dt <= '{ed}' AND dt >= '{bd}'""")
    trade_dates1_df['日期'] = pd.to_datetime(trade_dates1_df['日期'])
    date_b = trade_dates1_df['日期'].min().strftime('%Y-%m-%d')
    date_e = trade_dates1_df['日期'].max().strftime('%Y-%m-%d')

    # --- 2. 获取并处理源数据 ---
    province_source_df = run_source_query(db_manager_pg, 'province', date_b, date_e, target_term)
    city_source_df = run_source_query(db_manager_pg, 'city', date_b, date_e, target_term)

    # --- 3. 格式化数据 (在Pandas中进行重命名和清理) ---
    province_source_df.rename(columns={'省': 'province'}, inplace=True)
    city_source_df.rename(columns={'省': 'province', '市': 'city'}, inplace=True)

    province_source_df['province'] = province_source_df['province'].apply(clean_province_name)
    city_source_df['province'] = city_source_df['province'].apply(clean_province_name)
    city_source_df['city'] = city_source_df['city'].apply(lambda x: str(x)[0:2])

    province_7d = province_source_df[['province', '近7天收益率变化bp']].rename(columns={'近7天收益率变化bp': 'spread'})
    province_1m = province_source_df[['province', '近1个月收益率变化bp']].rename(columns={'近1个月收益率变化bp': 'spread'})
    city_7d = city_source_df[['province', 'city', '近7天收益率变化bp']].rename(columns={'近7天收益率变化bp': 'spread'})
    city_1m = city_source_df[['province', 'city', '近1个月收益率变化bp']].rename(columns={'近1个月收益率变化bp': 'spread'})

    province_7d['dt'] = date_e
    province_1m['dt'] = date_e
    city_7d['dt'] = date_e
    city_1m['dt'] = date_e

    # --- 4. 输出 ---
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    province_7d.to_csv(os.path.join(output_dir, 'province_spread_change_7d.csv'), index=False, encoding='utf-8-sig')
    province_1m.to_csv(os.path.join(output_dir, 'province_spread_change_1m.csv'), index=False, encoding='utf-8-sig')
    city_7d.to_csv(os.path.join(output_dir, 'city_spread_change_7d.csv'), index=False, encoding='utf-8-sig')
    city_1m.to_csv(os.path.join(output_dir, 'city_spread_change_1m.csv'), index=False, encoding='utf-8-sig')

    print("\n--- 数据转换与输出完成 ---")
    print("省级7天变化数据 (province_spread_change_7d.csv):")
    print(province_7d.head())
    print("\n市级7天变化数据 (city_spread_change_7d.csv):")
    print(city_7d.head())

if __name__ == '__main__':
    main()