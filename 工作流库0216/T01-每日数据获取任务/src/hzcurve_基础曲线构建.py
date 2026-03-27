# -*- coding: utf-8 -*-
import warnings
import numpy as np
import pandas as pd
import pymysql
import datetime
from datetime import datetime
import time as time_module
import os
import sys
from sqlalchemy import create_engine,text
from iFinDPy import *
from tqdm import tqdm
import sys

warnings.filterwarnings('ignore')

sql_config = {
    'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'hz_work',
    'passwd': 'Hzinsights2015',
    'db': 'stock',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

sql_engine = create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' %(
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    )
)
mysql_conn = pymysql.connect(**sql_config)
mysql_conn.autocommit(1)
mysql_cursor = mysql_conn.cursor()
THS_iFinDLogin('hznd002', '160401')

import psycopg2
from psycopg2.extras import execute_values
postgres_config = {
    'host': '139.224.201.106',
    'user': 'postgres',
    'password': 'hzinsights2015',
    'dbname': 'tsdb',
    'port': '18032'
}
postgres_conn = psycopg2.connect(**postgres_config)
postgres_cursor = postgres_conn.cursor()

def insert_database(raw: pd.DataFrame, db: str, key_list: list, mode='UPDATE', dt_type='DATE'):
    """
    :param raw:
    :param db:
    :param key_list:
    :param mode: 'update' or 'replace'
    :return:
    """
    print("insert_database")
    if 'DT' in raw.columns:
        if dt_type == 'DATE':
            raw['DT'] = raw['DT'].apply(lambda x: str(x)[:10])
    final_table = raw.where(raw.notnull(), None)  # 将NAN，Nan转换为None
    values = final_table.values.tolist()
    processed_values = []
    for row in values:
        processed_row = []
        for item in row:
            if item is None or (isinstance(item, float) and np.isnan(item)):
                processed_row.append(None)  # 替换为 None
            else:
                processed_row.append(item)
        processed_values.append(processed_row)
    if mode == 'UPDATE':
        col = raw.columns.tolist()
        col2 = col.copy()
        print(col2)
        print(key_list)
        if len(key_list) > 0:
            for key in key_list:
                col2.remove(key)
        print(col2)

        update_str = ','.join(f'`{x}` = VALUES(`{x}`)' for x in col2)
        placeholders = ','.join(['%s'] * len(raw.columns))  # 使用正确数量的占位符
        sql = f"INSERT INTO {db} (`{'`,`'.join(x for x in col)}`) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_str}"
        print(sql)  # 调试用
        mysql_cursor.executemany(sql, processed_values)

    elif mode == 'REPLACE':
        mysql_cursor.executemany(
            f"REPLACE INTO {db} VALUES (%%s{', %%s' * (len(final_table.columns) - 1)})", processed_values)

    else:
        raise Exception('SELECT MODE IN (UPDATE, REPLACE)')

def hermite_interpolation4(x, x1, x2, y1, y2, d1, d2):
    h = x2 - x1
    t = (x - x1) / h
    H1 = 1 - 3 * t ** 2 + 2 * t ** 3
    H2 = 3 * t ** 2 - 2 * t ** 3
    H3 = t - 2 * t ** 2 + t ** 3
    H4 = -t ** 2 + t ** 3
    y_x = y1 * H1 + y2 * H2 + d1 * H3 + d2 * H4

    return np.round(y_x, 4)
def update_basicinfo():
    print("开始更新最新评级...")
    sql=f"""
    INSERT INTO 最新评级(trade_code, 评级)
    SELECT 
        m.trade_code, 
        m.ths_cb_market_implicit_rating_bond as 评级
    FROM 
        bond.marketinfo_credit m
    where m.dt = (select max(dt) from bond.marketinfo_credit)
    and m.ths_cb_market_implicit_rating_bond is not null
    union 
    SELECT 
        m.trade_code, 
        m.ths_cb_market_implicit_rating_bond as 评级
    FROM 
        bond.marketinfo_finance m
    where m.dt = (select max(dt) from bond.marketinfo_finance)
    and m.ths_cb_market_implicit_rating_bond is not null
    union 
    SELECT 
        m.trade_code, 
        m.ths_cb_market_implicit_rating_bond as 评级
    FROM 
        bond.marketinfo_abs m
    where m.trade_code not like 'S%%'
    and m.dt = (select max(dt) from bond.marketinfo_abs)
    and m.ths_cb_market_implicit_rating_bond is not null
    on DUPLICATE key UPDATE 评级=VALUES(评级)
    """
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql))
    
    print("开始更新城投债最新信息")

    sql=f"""
    INSERT INTO basicinfo_all (trade_code,大类,子类,隐含评级,外评,发行方式,是否永续,是否次级,是否二永)
    SELECT
        A.ths_main_sec_code_bond as trade_code,
        '城投' as 大类,
        max(A.ths_urban_platform_area_bond) as 子类,
        max(C.评级) as 隐含评级,
        max(case when B.rating_issuer is not null then B.rating_issuer
           else B.rating_bond end) as 外评,
        max(A.ths_issue_method_bond) as 发行方式,
        max(A.ths_is_perpetual_bond) as 是否永续,
        max(A.ths_is_subordinated_debt_bond) as 是否次级,
        max(case when (A.ths_is_perpetual_bond='是' or A.ths_is_subordinated_debt_bond ='是') then '是'
        else '否' end) as 是否二永
        FROM basicinfo_credit A
        left join bond.basicinfo_外评 B on A.trade_code=B.trade_code
        left join bond.最新评级 C on A.trade_code=C.trade_code
        where ths_is_city_invest_debt_yy_bond='是'
        and A.ths_main_sec_code_bond !=''
        and A.ths_main_sec_code_bond is not null
        group by A.ths_main_sec_code_bond
    on DUPLICATE key UPDATE 大类=VALUES(大类),子类=VALUES(子类),隐含评级=VALUES(隐含评级),外评=VALUES(外评),发行方式=VALUES(发行方式),是否永续=VALUES(是否永续),是否次级=VALUES(是否次级),是否二永=VALUES(是否二永)"""
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql))

    print("开始更新产业债最新信息")
    sql="""
    INSERT INTO basicinfo_all (trade_code,大类,子类,隐含评级,外评,发行方式,是否永续,是否次级,是否二永)
    SELECT
        A.ths_main_sec_code_bond as trade_code,
        '产业' as 大类,
        max(CASE
            WHEN A.ths_object_the_sw_bond LIKE '%%证券%%' THEN '非银金融--多元金融--其他多元金融'
            WHEN A.ths_object_the_sw_bond LIKE '%%保险%%' THEN '非银金融--多元金融--其他多元金融'
            ELSE A.ths_object_the_sw_bond END) as 子类,
        max(C.评级) as 隐含评级,
        max(case when B.rating_issuer is not null then B.rating_issuer
           else B.rating_bond end) as 外评,
        max(A.ths_issue_method_bond) as 发行方式,
        max(A.ths_is_perpetual_bond) as 是否永续,
        max(A.ths_is_subordinated_debt_bond) as 是否次级,
        max(case when (A.ths_is_perpetual_bond='是' or A.ths_is_subordinated_debt_bond ='是') then '是'
        else '否' end) as 是否二永
        FROM basicinfo_credit A
        left join bond.最新评级 C on A.trade_code=C.trade_code
        left join bond.basicinfo_外评 B on A.trade_code=B.trade_code
        where ths_is_city_invest_debt_yy_bond='否'
        and ths_object_the_sw_bond not LIKE '%%银行%%'
        and A.ths_main_sec_code_bond !=''
        and A.ths_main_sec_code_bond is not null
        group by A.ths_main_sec_code_bond
    on DUPLICATE key UPDATE 大类=VALUES(大类),子类=VALUES(子类),隐含评级=VALUES(隐含评级),外评=VALUES(外评),发行方式=VALUES(发行方式),是否永续=VALUES(是否永续),是否次级=VALUES(是否次级),是否二永=VALUES(是否二永)"""
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql))

    print("开始更新金融债最新信息")     
    sql="""
    INSERT INTO basicinfo_all (trade_code,大类,子类,隐含评级,外评,发行方式,是否永续,是否次级,是否二永)
    SELECT
        A.ths_main_sec_code_bond as trade_code,
        '金融' as 大类,
        max(CASE
            WHEN A.ths_org_type_bond LIKE '%%银行%%' THEN '银行'
            WHEN A.ths_org_type_bond LIKE '%%证券公司%%' THEN '证券公司'
            WHEN A.ths_org_type_bond LIKE '%%保险%%' THEN '保险' 
            WHEN A.ths_ths_bond_third_type_bond = '其他非银金融机构债' THEN '其他'       
        END) AS 子类,
        max(C.评级) as 隐含评级,
        max(case when B.rating_issuer is not null then B.rating_issuer
           else B.rating_bond end) as 外评,
        max(A.ths_issue_method_bond) as 发行方式,
        max(A.ths_is_perpetual_bond) as 是否永续,
        max(A.ths_is_subordinated_debt_bond) as 是否次级,
        max(case when (A.ths_is_perpetual_bond='是' or A.ths_is_subordinated_debt_bond ='是') then '是'
        else '否' end) as 是否二永
        FROM basicinfo_finance A
        left join bond.最新评级 C on A.trade_code=C.trade_code
        left join bond.basicinfo_外评 B on A.trade_code=B.trade_code
        where A.ths_main_sec_code_bond !=''
        and A.ths_main_sec_code_bond is not null
        group by A.ths_main_sec_code_bond
    on DUPLICATE key UPDATE 大类=VALUES(大类),子类=VALUES(子类),隐含评级=VALUES(隐含评级),外评=VALUES(外评),发行方式=VALUES(发行方式),是否永续=VALUES(是否永续),是否次级=VALUES(是否次级),是否二永=VALUES(是否二永)"""
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql))

    sql="""
    INSERT INTO basicinfo_all (trade_code,大类,子类,隐含评级,外评,发行方式,是否永续,是否次级,是否二永)
    SELECT
        A.ths_main_sec_code_bond as trade_code,
        '金融' as 大类,
        '银行' as 子类,
        max(C.评级) as 隐含评级,
        max(case when B.rating_issuer is not null then B.rating_issuer
           else B.rating_bond end) as 外评,
        max(A.ths_issue_method_bond) as 发行方式,
        max(A.ths_is_perpetual_bond) as 是否永续,
        max(A.ths_is_subordinated_debt_bond) as 是否次级,
        max(case when (A.ths_is_perpetual_bond='是' or A.ths_is_subordinated_debt_bond ='是') then '是'
        else '否' end) as 是否二永
        FROM basicinfo_credit A
        left join bond.最新评级 C on A.trade_code=C.trade_code
        left join bond.basicinfo_外评 B on A.trade_code=B.trade_code
        where ths_is_city_invest_debt_yy_bond='否'
        and ths_object_the_sw_bond LIKE '%%银行%%'
        and A.ths_main_sec_code_bond !=''
        and A.ths_main_sec_code_bond is not null
        group by A.ths_main_sec_code_bond
    on DUPLICATE key UPDATE 大类=VALUES(大类),子类=VALUES(子类),隐含评级=VALUES(隐含评级),外评=VALUES(外评),发行方式=VALUES(发行方式),是否永续=VALUES(是否永续),是否次级=VALUES(是否次级),是否二永=VALUES(是否二永)"""
    with sql_engine.begin() as _cursor:
        _cursor.execute(text(sql))
        
    print("开始更新ABS最新信息")
    with sql_engine.begin() as _cursor:
        # 获取总数据量
        total_count = pd.read_sql("""
            SELECT COUNT(*) as count FROM bond.basicinfo_abs 
            WHERE ths_main_sec_code_bond is not null 
            AND ths_main_sec_code_bond != ''
            AND trade_code not like 'S%%'
        """, _cursor)['count'].iloc[0]

        # 创建辅助临时表(只创建一次)
        print("创建临时表...")
        sql_create_temp_guarantor = """
        CREATE TEMPORARY TABLE IF NOT EXISTS temp_guarantor AS
        SELECT DISTINCT 
            ths_issuer_name_cn_bond AS 发行人,
            ths_is_city_invest_debt_yy_bond AS 担保人是否城投,
            ths_object_the_sw_bond AS 担保人行业
        FROM bond.basicinfo_credit
        WHERE ths_issuer_name_cn_bond != ''
        AND ths_issuer_name_cn_bond is not null
        """
        _cursor.execute(text(sql_create_temp_guarantor))

        sql_create_temp_original_owner = """
        CREATE TEMPORARY TABLE IF NOT EXISTS temp_original_owner AS
        SELECT DISTINCT 
            ths_issuer_name_cn_bond AS 发行人,
            ths_is_city_invest_debt_yy_bond AS 原始权益人是否城投
        FROM bond.basicinfo_credit
        WHERE ths_issuer_name_cn_bond != ''
        AND ths_issuer_name_cn_bond is not null
        """
        _cursor.execute(text(sql_create_temp_original_owner))

    print(f"\n2. 开始更新ABS信息 (总数据量: {total_count})...")
    batch_size = 1000
    progress_bar = tqdm(total=total_count, desc="处理进度")
    
    for offset in range(0, total_count, batch_size):
        with sql_engine.begin() as _cursor:
            # 每批次创建基础信息临时表
            sql_create_temp_basicinfo = f"""
            CREATE TEMPORARY TABLE IF NOT EXISTS temp_basicinfo AS
            SELECT
                A.trade_code,
                A.ths_bond_short_name_bond AS 简称,
                A.ths_issue_method_bond AS 发行方式,
                A.ths_b_abs_defiguarantor_bond AS 担保人,
                A.ths_sponsor_to_original_righter_bond AS 原始权益人,
                A.ths_abs_swi_industry_bond AS abs行业分类,
                A.ths_basic_asset_type_detail_bond AS 底层资产类型,
                C.评级 AS 隐含评级,
                CASE WHEN B.rating_issuer IS NOT NULL THEN B.rating_issuer
                    ELSE B.rating_bond END AS 外评
            FROM bond.basicinfo_abs A
            LEFT JOIN bond.最新评级 C ON A.trade_code = C.trade_code
            LEFT JOIN bond.basicinfo_外评 B ON A.trade_code = B.trade_code
            WHERE A.ths_main_sec_code_bond is not null
            AND A.ths_main_sec_code_bond != ''
            AND A.trade_code not like 'S%'
            LIMIT {batch_size} OFFSET {offset}
            """
            _cursor.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_basicinfo"))
            _cursor.execute(text(sql_create_temp_basicinfo))

            # 执行插入操作
            sql_insert = """
            INSERT INTO basicinfo_all (trade_code, 大类, 子类, 隐含评级, 外评, 发行方式, 是否永续, 是否次级, 是否二永)
            SELECT 
                a.trade_code,
                'ABS' AS 大类,
                CASE
                    WHEN MAX(CASE WHEN b.担保人是否城投 = '是' THEN 1 ELSE 0 END) > 0 OR 
                         MAX(CASE WHEN c.原始权益人是否城投 = '是' THEN 1 ELSE 0 END) > 0 THEN '城投'
                    WHEN MAX(CASE WHEN a.底层资产类型 LIKE '%互联网%' THEN 1 ELSE 0 END) > 0 THEN '消金小贷'
                    WHEN MAX(CASE WHEN a.底层资产类型 LIKE '%信用卡%' OR a.底层资产类型 LIKE '%不良%' THEN 1 ELSE 0 END) > 0 THEN '银行信贷资产'
                    WHEN MAX(CASE WHEN a.底层资产类型 LIKE '%REITs%' THEN 1 ELSE 0 END) > 0 THEN 'REITs'
                    WHEN MAX(CASE WHEN a.底层资产类型 != '' THEN 1 ELSE 0 END) > 0 THEN '租赁保理综合'
                    WHEN MAX(CASE WHEN a.abs行业分类 LIKE '%银行%' THEN 1 ELSE 0 END) > 0 THEN '银行信贷资产'
                    WHEN MAX(CASE WHEN b.担保人行业 LIKE '%建筑%' THEN 1 ELSE 0 END) > 0 THEN '建筑供应链'
                    WHEN MAX(CASE WHEN b.担保人行业 LIKE '%房地产%' THEN 1 ELSE 0 END) > 0 THEN '房地产'
                    WHEN MAX(CASE WHEN b.担保人行业 LIKE '%多元金融%' OR b.担保人行业 LIKE '%综合%' OR b.担保人行业 = '' THEN 1 ELSE 0 END) > 0 THEN '租赁保理综合'
                    ELSE '央国企供应链'
                END AS 子类,
                a.隐含评级,
                a.外评,
                a.发行方式,
                '否' AS 是否永续,
                '否' AS 是否次级,
                '否' AS 是否二永
            FROM temp_basicinfo a
            LEFT JOIN temp_guarantor b ON a.担保人 LIKE CONCAT('%', b.发行人, '%')
            LEFT JOIN temp_original_owner c ON a.原始权益人 LIKE CONCAT('%', c.发行人, '%')
            GROUP BY a.trade_code, a.隐含评级, a.外评, a.发行方式
            ON DUPLICATE KEY UPDATE 
                大类 = VALUES(大类),
                子类 = VALUES(子类),
                隐含评级 = VALUES(隐含评级),
                外评 = VALUES(外评),
                发行方式 = VALUES(发行方式),
                是否永续 = VALUES(是否永续),
                是否次级 = VALUES(是否次级),
                是否二永 = VALUES(是否二永)
            """
            _cursor.execute(text(sql_insert))

        # 更新进度条
        progress_bar.update(min(batch_size, total_count - offset))

    # 所有批次处理完后,清理临时表
    with sql_engine.begin() as _cursor:
        _cursor.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_basicinfo"))
        _cursor.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_guarantor"))
        _cursor.execute(text("DROP TEMPORARY TABLE IF EXISTS temp_original_owner"))
    
    progress_bar.close()
    print("ABS信息更新完成")

    print("开始更新基础曲线...")
    sqls=["""
    -- 首先创建一个临时表来存储要插入的数据
    CREATE TEMPORARY TABLE temp_table AS
    SELECT distinct b.大类, b.子类, b.隐含评级, '全部' as 外评, b.发行方式, b.是否二永, t.term as 目标期限
    FROM bond.basicinfo_all b
    CROSS JOIN yq.目标期限1 t
    WHERE b.隐含评级 in ('AAA+','AAA','AAA-','AA+','AA','AA(2)','AA-')
    and b.子类 is not null
    and b.大类 is not null
    """,
    """
    UPDATE bond.basicinfo_hzcurve hz
    JOIN temp_table tt ON hz.大类 = tt.大类
        AND hz.子类 = tt.子类
        AND hz.隐含评级 = tt.隐含评级
        AND hz.外评 = tt.外评
        AND hz.发行方式 = tt.发行方式
        AND hz.是否二永 = tt.是否二永
        AND hz.目标期限 = tt.目标期限
    SET hz.大类 = CASE WHEN hz.大类!= tt.大类 THEN tt.大类 ELSE hz.大类 END,
        hz.子类 = CASE WHEN hz.子类!= tt.子类 THEN tt.子类 ELSE hz.子类 END,
        hz.隐含评级 = CASE WHEN hz.隐含评级!= tt.隐含评级 THEN tt.隐含评级 ELSE hz.隐含评级 END,
        hz.外评 = CASE WHEN hz.外评!= tt.外评 THEN tt.外评 ELSE hz.外评 END,
        hz.发行方式 = CASE WHEN hz.发行方式!= tt.发行方式 THEN tt.发行方式 ELSE hz.发行方式 END,
        hz.是否二永 = CASE WHEN hz.是否二永!= tt.是否二永 THEN tt.是否二永 ELSE hz.是否二永 END,
        hz.目标期限 = CASE WHEN hz.目标期限!= tt.目标期限 THEN tt.目标期限 ELSE hz.目标期限 END;""",
    """
    -- 将临时表中不存在于目标表中的记录插入到目标表中
    INSERT INTO bond.basicinfo_hzcurve (大类, 子类, 隐含评级, 外评, 发行方式, 是否二永, 目标期限)
    SELECT 大类, 子类, 隐含评级, 外评, 发行方式, 是否二永, 目标期限 from
    (SELECT tt.大类, tt.子类, tt.隐含评级, tt.外评, tt.发行方式, tt.是否二永, tt.目标期限,hz.大类 as 大类1,
    hz.子类 as 子类1, hz.隐含评级 as 隐含评级1, hz.外评 as 外评1, hz.发行方式 as 发行方式1, hz.是否二永 as 是否二永1, hz.目标期限 as 目标期限1
    FROM temp_table tt
    LEFT JOIN bond.basicinfo_hzcurve hz ON tt.大类 = hz.大类
        AND tt.子类 = hz.子类
        AND tt.隐含评级 = hz.隐含评级
        AND tt.外评 = hz.外评
        AND tt.发行方式 = hz.发行方式
        AND tt.是否二永 = hz.是否二永
        AND tt.目标期限 = hz.目标期限)sq
    WHERE sq.大类1 IS NULL;""",
    """
    -- 删除临时表
    DROP TEMPORARY TABLE temp_table;
    """]
    with sql_engine.begin() as _cursor:
        for sql in sqls:
            _cursor.execute(text(sql))

def process_batch(trade_codes_batch):
    # 将列表转换为以分号分隔的字符串
    codes_str = ','.join(trade_codes_batch)
    try:
        # 批量获取数据
        df = THS_BD(codes_str, 
                    'ths_bond_latest_credict_rating_bond;ths_subject_latest_credit_rating_bond',
                    '100,100;100,100')
        df = df.data
        if df is not None:
            df = df[['thscode', 'ths_bond_latest_credict_rating_bond',
                    'ths_subject_latest_credit_rating_bond']]
            df.columns = ['trade_code', 'rating_bond', 'rating_issuer']
            print(f"成功处理 {len(df)} 条记录")
            return df
    except Exception as e:
        print(f"处理批次时出错: {e}")
    return None

def update_外评():
    print("开始更新外评...")
    """
    从数据库中查询 trade_code，然后对每个 trade_code 调用 THS_BD 接口获取外评信息，
    将获取到的外评信息插入到 bond.basicinfo_外评 中。
    """
    sql="""
    select distinct trade_code from bond.basicinfo_credit
    where trade_code is not null and trade_code !=''
    union
    select distinct trade_code from bond.basicinfo_finance
    where trade_code is not null and trade_code !=''
    union
    select distinct trade_code from bond.basicinfo_abs
    where trade_code is not null and trade_code !=''
    union
    select distinct trade_code from bond.basicinfo_equity
    where trade_code is not null and trade_code !=''
    """
    with sql_engine.begin() as _cursor:
        trade_codes=pd.read_sql(sql,_cursor)['trade_code'].tolist()
    # 将trade_codes分成每批1000个的批次
    batch_size = 1000
    batches = [trade_codes[i:i + batch_size] for i in range(0, len(trade_codes), batch_size)]

    all_results = []
    for i, batch in enumerate(batches, 1):
        print(f"处理批次 {i}/{len(batches)}, 包含 {len(batch)} 个代码")
        result_df = process_batch(batch)
        if result_df is not None:
            all_results.append(result_df)

    # 合并所有结果
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        # 插入数据库
        table_names = ['bond.basicinfo_外评']
        insert_database(
            final_df[(final_df['rating_bond'] != 0) & (final_df['rating_issuer'] != '0')],
            table_names[0], 
            ['trade_code']
        )
        print(f"总共处理完成 {len(final_df)} 条记录")

def get_hzcurve_df(processnum,batchsize=100):
    sql=f"""
    SELECT 
        h.TRADE_CODE as 曲线代码,
        h.大类,
        h.子类,
        h.隐含评级,
        h.外评,
        h.发行方式,
        h.是否二永,
        h.目标期限,
        b.trade_code,
				m.dt,
				m.ths_bond_balance_bond AS 债券余额,
					m.ths_evaluate_yield_cb_bond_exercise AS 中债行权估值,
				CASE 
						WHEN m.ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN m.ths_evaluate_modified_dur_cb_bond_exercise
						ELSE m.ths_evaluate_interest_durcb_bond_exercise + m.ths_evaluate_spread_durcb_bond_exercise
				END AS 中债行权剩余期限,
				m.ths_cb_market_implicit_rating_bond AS 市场隐含评级
    FROM 
		(SELECT * 
		from basicinfo_hzcurve 
		limit {batchsize}
        offset {processnum*batchsize})
		h
    LEFT JOIN basicinfo_all b ON 
        (h.大类 = '全部' OR h.大类 = b.大类) AND
        (h.子类 = '全部' OR h.子类 = b.子类) AND
        (h.隐含评级 = '全部' OR h.隐含评级 = b.隐含评级) AND
        (h.外评 = '全部' OR h.外评 = b.外评) AND
        (h.发行方式 = '全部' OR h.发行方式 = b.发行方式) AND
        (h.是否二永 = '全部' OR h.是否二永 = b.是否二永)
		LEFT JOIN marketinfo_credit m ON b.trade_code = m.trade_code
        where m.dt is not null
		order by 曲线代码
    union
        SELECT 
        h.TRADE_CODE as 曲线代码,
        h.大类,
        h.子类,
        h.隐含评级,
        h.外评,
        h.发行方式,
        h.是否二永,
        h.目标期限,
        b.trade_code,
				m.dt,
				m.ths_bond_balance_bond AS 债券余额,
					m.ths_evaluate_yield_cb_bond_exercise AS 中债行权估值,
				CASE 
						WHEN m.ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN m.ths_evaluate_modified_dur_cb_bond_exercise
						ELSE m.ths_evaluate_interest_durcb_bond_exercise + m.ths_evaluate_spread_durcb_bond_exercise
				END AS 中债行权剩余期限,
				m.ths_cb_market_implicit_rating_bond AS 市场隐含评级
    FROM 
		(SELECT * 
		from basicinfo_hzcurve 
		limit {batchsize}
        offset {processnum*batchsize})
		h
    LEFT JOIN basicinfo_all b ON 
        (h.大类 = '全部' OR h.大类 = b.大类) AND
        (h.子类 = '全部' OR h.子类 = b.子类) AND
        (h.隐含评级 = '全部' OR h.隐含评级 = b.隐含评级) AND
        (h.外评 = '全部' OR h.外评 = b.外评) AND
        (h.发行方式 = '全部' OR h.发行方式 = b.发行方式) AND
        (h.是否二永 = '全部' OR h.是否二永 = b.是否二永)
		LEFT JOIN marketinfo_finance m ON b.trade_code = m.trade_code
    where m.dt is not null
		order by 曲线代码
    union
        SELECT 
        h.TRADE_CODE as 曲线代码,
        h.大类,
        h.子类,
        h.隐含评级,
        h.外评,
        h.发行方式,
        h.是否二永,
        h.目标期限,
        b.trade_code,
				m.dt,
				m.ths_bond_balance_bond AS 债券余额,
					m.ths_evaluate_yield_cb_bond_exercise AS 中债行权估值,
				CASE 
						WHEN m.ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN m.ths_evaluate_modified_dur_cb_bond_exercise
						ELSE m.ths_evaluate_interest_durcb_bond_exercise + m.ths_evaluate_spread_durcb_bond_exercise
				END AS 中债行权剩余期限,
				m.ths_cb_market_implicit_rating_bond AS 市场隐含评级
    FROM 
		(SELECT * 
		from basicinfo_hzcurve 
		limit {batchsize}
        offset {processnum*batchsize})
		h
    LEFT JOIN basicinfo_all b ON 
        (h.大类 = '全部' OR h.大类 = b.大类) AND
        (h.子类 = '全部' OR h.子类 = b.子类) AND
        (h.隐含评级 = '全部' OR h.隐含评级 = b.隐含评级) AND
        (h.外评 = '全部' OR h.外评 = b.外评) AND
        (h.发行方式 = '全部' OR h.发行方式 = b.发行方式) AND
        (h.是否二永 = '全部' OR h.是否二永 = b.是否二永)
		LEFT JOIN marketinfo_abs m ON b.trade_code = m.trade_code
    where m.dt is not null
		order by 曲线代码
    """
    with sql_engine.begin() as _cursor:
       df=pd.read_sql(sql,_cursor)
    return df

def get_all_marketinfo(withterm,dt,yhpj):
    if withterm==1:
        text=',t.term as 目标期限'
    else:
        text=''
    sql=f"""SELECT A.*, 
    B.大类,
    B.子类,
    A.隐含评级,
    B.外评,
    B.发行方式,
    B.是否二永{text}
    FROM (
        SELECT
            dt AS 日期,
            trade_code,
            ths_bond_balance_bond AS 债券余额,
            ths_evaluate_yield_cb_bond_exercise AS 中债行权估值,
            CASE 
                WHEN ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN ths_evaluate_modified_dur_cb_bond_exercise
                ELSE ths_evaluate_interest_durcb_bond_exercise + ths_evaluate_spread_durcb_bond_exercise
            END AS 中债行权剩余期限,
            ths_cb_market_implicit_rating_bond AS 隐含评级
        FROM
            bond.marketinfo_credit
        WHERE
            dt ='{dt}'
            AND ths_evaluate_yield_cb_bond_exercise > 0
            AND ths_cb_market_implicit_rating_bond IN ('{yhpj}')
            AND (ths_evaluate_modified_dur_cb_bond_exercise>0 OR ths_evaluate_interest_durcb_bond_exercise>0)
    INNER JOIN bond.basicinfo_all B ON A.trade_code = B.trade_code
    """
    if withterm==1:
        sql+="""
        CROSS JOIN yq.目标期限 t
        """
    with sql_engine.begin() as _cursor:
        df=pd.read_sql(sql,_cursor)
    return df

def get_zzcurve(dt):
    sql="""
    SELECT
    A.dt,
    A.收益率,
    B.发行方式,
    B.是否二永,
    B.隐含评级,
    B.曲线期限, 
    '城投' AS 大类
    FROM (
        SELECT DT,trade_code, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt ='{dt}'
        AND TRADE_CODE IN
        (
        SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND classify2 LIKE '%%城投债%%')
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE,
        CASE
            WHEN classify2 LIKE '%%非公开%%' THEN '私募'
            ELSE '公募'
        END AS 发行方式,
        CASE
            WHEN classify2 LIKE '%%可续期%%' THEN '是'
            ELSE '否'
        END AS 是否二永
        SUBSTRING(
            REPLACE(classify2, '＋', '+'),
            LOCATE('(', REPLACE(classify2, '＋', '+')) + 1,
            CHAR_LENGTH(classify2) - LOCATE('(',
                        REPLACE(classify2, '＋', '+')) - 1
        ) AS 隐含评级,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365+(RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限
        FROM bond.basicinfo_curve
    ) B ON A.trade_code= B.TRADE_CODE
    UNION
    SELECT 
    A.dt,
    A.收益率,
    B.发行方式,
    B.是否二永,
    B.隐含评级,
    B.曲线期限,
    '产业' AS 大类
    FROM(
        SELECT dt, trade_code, CLOSE AS 收益率
        from bond.marketinfo_curve
        WHERE dt ='{dt}'
            AND TRADE_CODE IN
        (
                SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND (classify2 LIKE '%%产业%%' or classify2 LIKE '%%企业%%'))
        )A
    LEFT JOIN(
        SELECT TRADE_CODE,
        CASE WHEN classify2 LIKE '%%非公开%%' THEN '私募' ELSE '公募' END AS 发行方式,
        CASE WHEN classify2 LIKE '%%次级可续期%%' THEN '是' ELSE '否' END AS 是否二永,
    SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+')
                )+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
    AS 隐含评级,
    LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365+(RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 
    from bond.basicinfo_curve
    )B on A.trade_code=B.TRADE_CODE
    UNION
    SELECT 
    A.dt,
    A.收益率,
    '公募' as 发行方式,
    '否' as 是否二永,
    B.隐含评级,
    B.曲线期限,
    'ABS' AS 大类
    FROM (
        SELECT dt, trade_code, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt ='{dt}'
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 NOT LIKE '%%中债资产支持%%')
        )
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1, CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1) AS 隐含评级,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
        WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 NOT LIKE '%%中债资产支持%%')
    ) B ON A.trade_code = B.TRADE_CODE
    UNION
    A.dt,
    A.收益率,
    '公募' as 发行方式,
    B.是否二永,
    B.隐含评级,
    B.曲线期限,
    '金融' AS 大类
    FROM
        (SELECT dt, trade_code, CLOSE AS 收益率 from bond.marketinfo_curve 
        WHERE dt ='{dt}' 
        AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%商业银行%%' AND classify2 NOT LIKE '%%次级%%' AND classify2 NOT LIKE '%%存单%%')))A 
    LEFT JOIN
        (SELECT TRADE_CODE, 
        CASE WHEN classify2 LIKE '%%二级资本%%' THEN '是' ELSE '否' END AS 是否二永,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 
        from bond.basicinfo_curve
    )B 
    on A.trade_code=B.TRADE_CODE
    """
    with sql_engine.begin() as _cursor:
        df=pd.read_sql(sql,_cursor)
    return df

def merge_curve(data_curve1, data_curve2, df_target, term_row, yield_row):
    #将两个曲线数据集进行合并
    merge_target = df_target.join(data_curve1.set_index(['dt', '隐含评级', '大类', '发行方式', '是否永续', '是否次级', '曲线期限']), on=[
                                  'dt', '隐含评级', '大类', '发行方式', '是否永续', '是否次级', term_row], how='left', rsuffix='_1')
    if not merge_target[merge_target['收益率'] > 0].empty:
        data_curve2.loc[merge_target.index,
                        yield_row] = merge_target['收益率']
    return data_curve2

def cal_curve(data_curve1, data_curve2):
    #插值补齐曲线
    terms1 = np.array([0, 0.083333333, 0.24999999899999997, 0.49999999799999995, 0.749999997, 1, 2, 3, 4,
                       5, 6, 7, 8, 9, 10, 15, 20, 30])
    min_terms1 = min(terms1)
    max_terms1 = max(terms1)
    term_length1 = len(terms1)
    curve_term_values = data_curve2['曲线期限'].values
    mask_interm = np.logical_or(np.in1d(data_curve2['曲线期限'].values, terms1),
                                np.logical_or(data_curve2['曲线期限'].values < np.min(terms1),
                                              data_curve2['曲线期限'].values > np.max(terms1)))
    df_interm = data_curve2[mask_interm]
    df_outterm = data_curve2[~mask_interm]

    data_curve2 = merge_curve(data_curve1, data_curve2,
                            df_interm, '曲线期限', '收益率')

    data_curve2.loc[df_outterm.index.tolist(), 'x1_m1'] = np.max(
        np.where(curve_term_values[~mask_interm][:, np.newaxis] >= terms1, terms1, min_terms1), axis=1)
    data_curve2.loc[df_outterm.index.tolist(), 'x2_m1'] = np.min(
        np.where(curve_term_values[~mask_interm][:, np.newaxis] <= terms1, terms1, max_terms1), axis=1)
    insert_points_x1m1 = np.searchsorted(
        terms1, data_curve2.loc[~mask_interm, 'x1_m1'].values[:, np.newaxis], side='left')
    insert_points_x2m1 = np.searchsorted(
        terms1, data_curve2.loc[~mask_interm, 'x2_m1'].values[:, np.newaxis], side='right')
    data_curve2.loc[data_curve2[~mask_interm].index.tolist(), 'x11_m1'] = terms1[
        np.where(insert_points_x1m1 > 0, insert_points_x1m1 - 1, 0)]
    data_curve2.loc[data_curve2[~mask_interm].index.tolist(), 'x22_m1'] = terms1[
        np.where(insert_points_x2m1 < term_length1, insert_points_x2m1, term_length1 - 1)]
    df_outterm = data_curve2[~mask_interm]
    data_curve2 = merge_curve(data_curve1, data_curve2,
                            df_outterm, 'x1_m1', 'yx1_m1')
    data_curve2 = merge_curve(data_curve1, data_curve2,
                            df_outterm, 'x2_m1', 'yx2_m1')
    data_curve2 = merge_curve(data_curve1, data_curve2,
                            df_outterm, 'x11_m1', 'yx11_m1')
    data_curve2 = merge_curve(data_curve1, data_curve2,
                            df_outterm, 'x22_m1', 'yx22_m1')

    data_curve2.loc[df_outterm.index, 'd1_m1'] = (data_curve2.loc[df_outterm.index, 'yx2_m1'] - data_curve2.loc[df_outterm.index, 'yx11_m1']) / (
        2 * (data_curve2.loc[df_outterm.index, 'x2_m1'] - data_curve2.loc[df_outterm.index, 'x11_m1'])).array

    data_curve2.loc[df_outterm.index, 'd2_m1'] = (data_curve2.loc[df_outterm.index, 'yx22_m1'] - data_curve2.loc[df_outterm.index, 'yx1_m1']) / (
        2 * (data_curve2.loc[df_outterm.index, 'x22_m1'] - data_curve2.loc[df_outterm.index, 'x1_m1'])).array

    df_outterm = data_curve2[~mask_interm]
    df_outterm_yx2ord2null = df_outterm.query(
        'yx2_m1.isnull() or d2_m1.isnull()')
    df_outterm_yx2d2notnull = df_outterm.query(
        'yx2_m1.notnull() and d2_m1.notnull()')
    data_curve2.loc[df_outterm_yx2ord2null.index, 'yx22_m1'] = (
        data_curve2.loc[df_outterm_yx2ord2null.index, 'yx2_m1'])

    data_curve2.loc[df_outterm_yx2ord2null.index, 'd2_m1'] = (data_curve2.loc[df_outterm.index, 'yx2_m1'] - data_curve2.loc[df_outterm.index, 'yx11_m1']) / (
        2 * (data_curve2.loc[df_outterm.index, 'x2_m1'] - data_curve2.loc[df_outterm.index, 'x11_m1'])).array

    data_curve2.loc[df_outterm.index, '收益率'] = hermite_interpolation4(
        data_curve2.loc[df_outterm.index,
                        '曲线期限'],
        data_curve2.loc[df_outterm.index,
                        'x1_m1'],
        data_curve2.loc[df_outterm.index,
                        'x2_m1'],
        data_curve2.loc[df_outterm.index,
                        'yx1_m1'],
        data_curve2.loc[df_outterm.index,
                        'yx2_m1'],
        data_curve2.loc[df_outterm.index,
                        'd1_m1'],
        data_curve2.loc[df_outterm.index,
                        'd2_m1']).array
    return data_curve2

def get_unique_dates(conn, table_name,dt,condition):
    query = f"SELECT DISTINCT dt FROM {table_name} where dt>'{dt}' and {condition} is not null order by dt"
    df = pd.read_sql(query, conn)
    distinct_dts = set(row for row in df['dt'])
    return distinct_dts
def migrate_data_to_postgres(sql_engine, postgres_conn, table_names, target_table):
    print(f"开始将数据迁移至PostgreSQL表 {target_table}...")
    
    for table_name in table_names:
        with sql_engine.begin() as _cursor:
            distinct_dts_mysql = get_unique_dates(_cursor, table_name, '2013-12-31', 'balance')
        
        table_name_pos = table_name.replace('bond.','')
        distinct_dts_postgres = get_unique_dates(postgres_conn, table_name_pos, '2013-12-31', 'balance')
        difference_dates = distinct_dts_mysql - distinct_dts_postgres
        
        total_dates = len(difference_dates)
        print(f"需要迁移的日期数量: {total_dates}")
        
        for i, date in enumerate(sorted(difference_dates), 1):
            print(f"正在处理 {i}/{total_dates}: {date}", end='\r')
            # 读取特定日期的数据
            query = f"SELECT * FROM {table_name} WHERE DT = '{date}'"
            with sql_engine.begin() as _cursor:
                df = pd.read_sql(query, _cursor)

            print(date, target_table)
            if not df.empty:
                # 准备批量插入的数据
                # 构建 INSERT 语句
                insert_query = '''
                    INSERT INTO public.target_table1111 (dt, trade_code, close,balance) 
                    VALUES %s ON CONFLICT (dt, trade_code) 
                    DO NOTHING
                '''.replace('target_table1111', target_table)
                # 执行批量插入
                postgres_cursor = postgres_conn.cursor()
                data = df[['dt', 'trade_code', 'close', 'balance']].values.tolist()

                execute_values(postgres_cursor, insert_query, data)
                print(f"migrate_data_to_postgres for date: {date}")

        postgres_conn.commit()
        print(f"完成批次处理，已更新至 {date}")

def migrate_data_to_mysql(sql_engine, postgres_conn, table_names, target_table):
    print(f"开始将数据从PostgreSQL迁移至MySQL表 {target_table}...")
    
    for table_name in table_names:
        table_name_mysql = 'bond.' + table_name
        with sql_engine.begin() as _cursor:
            distinct_dts_mysql = get_unique_dates(_cursor, table_name_mysql, '2013-12-31', 'close')
        
        distinct_dts_postgres = get_unique_dates(postgres_conn, table_name, '2013-12-31', 'close')
        difference_dates = distinct_dts_postgres - distinct_dts_mysql
        
        total_dates = len(difference_dates)
        print(f"需要迁移的日期数量: {total_dates}")
        
        for i, date in enumerate(sorted(difference_dates), 1):
            print(f"正在处理 {i}/{total_dates}: {date}", end='\r')
            # 读取特定日期的数据
            query = f"SELECT * FROM {table_name} WHERE DT = '{date}'"
            with sql_engine.begin() as _cursor:
                df = pd.read_sql(query, postgres_conn)

            if not df.empty:
                # 准备批量插入的数据
                # 构建 INSERT 语句
                insert_query = f'''
                    INSERT INTO {target_table} (dt, trade_code, close, balance) 
                    VALUES (%s, %s, %s, %s)
                    on duplicate key update balance=VALUES(balance), close=VALUES(close)
                '''
                # 执行批量插入
                data = df[['dt', 'trade_code', 'close', 'balance']].values.tolist()
                def convert_nan_to_none(data_tuple):
                    return tuple(None if isinstance(x, float) and np.isnan(x) else x for x in data_tuple)
                # 转换整个data列表
                data = [convert_nan_to_none(row) for row in data]

                with mysql_conn.cursor() as _cursor:
                    _cursor.executemany(insert_query, data)
                print(f"migrate_data_to_mysql for date: {date}")

        postgres_conn.commit()

def check_mysql_status(sql_engine):
    """检查MySQL状态"""
    try:
        with sql_engine.begin() as conn:
            # 检查进程状态
            process_list = pd.read_sql("""
                SELECT id, user, host, db, command, time, state, info 
                FROM information_schema.processlist 
                WHERE command != 'Sleep'
                ORDER BY time DESC
            """, conn)
            
            # 检查锁等待
            locks = pd.read_sql("""
                SELECT * FROM information_schema.innodb_locks
            """, conn)
            
            # 检查InnoDB状态
            innodb_status = pd.read_sql("SHOW ENGINE INNODB STATUS", conn)
            
            return {
                'processes': process_list,
                'locks': locks,
                'innodb_status': innodb_status
            }
    except Exception as e:
        print(f"检查MySQL状态时出错: {e}")
        return None

def update_mysql_marketinfo_hzcurve(sql_engine):
    print("开始更新MySQL marketinfo_hzcurve...")
    start_time = time_module.time()
    last_check_time = start_time
    check_interval = 300  # 每5分钟检查一次MySQL状态
    
    with sql_engine.begin() as _cursor:
        distinct_dts = pd.read_sql("""
            SELECT DISTINCT dt FROM bond.marketinfo_credit
            where dt not in (select distinct dt from bond.marketinfo_hzcurve where balance is not null)
            and dt>'2013-12-31'
            """, con=_cursor, parse_dates=['dt'])
    
    total_dates = len(distinct_dts)
    print(f"需要处理的日期总数: {total_dates}")
    
    batch_size = 20
    for i in range(0, total_dates, batch_size):
        batch_start_time = time_module.time()
        current_batch = distinct_dts['dt'][i:i + batch_size]
        batch_dts = "','".join(current_batch.dt.strftime('%Y-%m-%d'))
        maxdt = max(current_batch)
        
        print(f"\n处理批次 {i//batch_size + 1}/{(total_dates+batch_size-1)//batch_size}")
        print(f"日期范围: {min(current_batch)} 到 {maxdt}")
        
        # 检查是否需要进行MySQL状态检查
        current_time = time_module.time()
        if current_time - last_check_time > check_interval:
            print("\n执行MySQL状态检查...")
            status = check_mysql_status(sql_engine)
            if status:
                # 检查长时间运行的查询
                # long_running = status['processes'][status['processes']['time'] > 300]
                # if not long_running.empty:
                #     print("\n发现长时间运行的查询:")
                #     print(long_running[['id', 'time', 'state', 'info']].to_string())
                
                # 检查锁等待
                if not status['locks'].empty:
                    print("\n发现锁等待:")
                    print(status['locks'].to_string())
                
                # 如果发现问题，给出建议
                if not long_running.empty or not status['locks'].empty:
                    print("\n建议操作:")
                    print("1. 考虑终止长时间运行的查询")
                    print("2. 检查是否需要优化索引")
                    print("3. 考虑调整批处理大小")
                    
                    # # 询问是否继续
                    # response = input("\n是否继续执行? (y/n): ")
                    # if response.lower() != 'y':
                    #     print("用户选择终止执行")
                    #     return
            
            last_check_time = current_time
        
        try:
            # 对每个dt执行查询并插入数据
            insert_market_sql = f"""
            INSERT INTO bond.marketinfo_hzcurve (dt, trade_code, balance)
            SELECT C.dt, A.trade_code, SUM(COALESCE(C.ths_bond_balance_bond,0)) AS balance
            FROM bond.basicinfo_hzcurve A
            LEFT JOIN bond.basicinfo_all B ON A.大类=B.大类 AND A.子类=B.子类
                                            AND A.发行方式=B.发行方式 AND A.是否二永=B.是否二永
            LEFT JOIN bond.marketinfo3 C ON B.trade_code=C.trade_code AND A.隐含评级=C.隐含评级 
                                            AND A.`目标期限` = (
                CASE 
                    when C.久期<0.125 then 0.083
                    when C.久期<0.375 then 0.25
                    when C.久期<0.625 then 0.5
                    when C.久期<0.875 then 0.75
                    when C.久期<1.5 then 1
                    when C.久期<2.5 then 2
                    when C.久期<3.5 then 3
                    when C.久期<4.5 then 4
                    when C.久期<6 then 5
                    when C.久期<8.5 then 7
                    when C.久期<12.5 then 10
                    when C.久期<17.5 then 15
                    when C.久期<25 then 20
                    ELSE 30 
                END
            )
            WHERE C.dt in ('{batch_dts}')
            and C.ths_bond_balance_bond>0
            GROUP BY A.trade_code, C.dt
            on DUPLICATE key UPDATE balance=VALUES(balance);
            """
            
            with sql_engine.begin() as _cursor:
                _cursor.execute(text(insert_market_sql))
            
            batch_end_time = time_module.time()
            batch_duration = batch_end_time - batch_start_time
            
            # 计算进度和预估剩余时间
            progress = (i + batch_size) / total_dates * 100
            avg_batch_time = batch_duration
            remaining_batches = (total_dates - (i + batch_size)) / batch_size
            estimated_time = remaining_batches * avg_batch_time
            
            print(f"批次耗时: {batch_duration:.2f}秒")
            print(f"总进度: {progress:.2f}%")
            print(f"预估剩余时间: {timedelta(seconds=int(estimated_time))}")
            
        except Exception as e:
            print(f"\n处理批次时出错: {e}")
            print("尝试继续处理下一批次...")
            continue
    
    total_duration = time_module.time() - start_time
    print(f"\n所有更新完成!")
    print(f"总耗时: {timedelta(seconds=int(total_duration))}")

def update_postgres_marketinfo_hzcurve(postgres_conn):
    print("开始更新PostgreSQL marketinfo_hzcurve...")
    
    sql = """REFRESH MATERIALIZED VIEW mv_distinct_dt"""
    postgres_cursor = postgres_conn.cursor()
    postgres_cursor.execute(sql)
    postgres_conn.commit()
    print("已刷新物化视图")
    
    distinct_dts = pd.read_sql("""
        SELECT DISTINCT dt FROM mv_distinct_dt
        where dt not in (select distinct dt from marketinfo_hzcurve where close is not null) 
        order by dt
        """, con=postgres_conn)
    
    total_dates = len(distinct_dts)
    print(f"需要处理的日期总数: {total_dates}")
    
    for i, a_dt in enumerate(distinct_dts['dt'], 1):
        print(f"处理进度: {i}/{total_dates} ({a_dt})", end='\r')
        # 对每个dt执行查询并插入数据
        insert_market_sql = f"""
        INSERT INTO marketinfo_hzcurve (dt, trade_code, close)
        SELECT C.dt, A.trade_code, SUM(COALESCE(C.balance,0) * COALESCE(C.stdyield,0)) / SUM(COALESCE(C.balance,0)) AS close
        FROM basicinfo_hzcurve A
        LEFT JOIN basicinfo_all B ON A.大类 = B.大类 AND A.子类 = B.子类
        AND A.发行方式 = B.发行方式 AND A.是否二永 = B.是否二永
        LEFT JOIN hzcurve_credit C ON B.trade_code = C.trade_code AND A.隐含评级 = C.imrating_calc
        AND A.目标期限 = C.target_term
        where C.dt='{a_dt}'
        and C.balance>0 and C.balance is not null and C.balance!='NaN'
        GROUP BY C.dt,A.trade_code
        ON CONFLICT(dt, trade_code)
        DO UPDATE SET close = EXCLUDED.close;
        """
        # 注意：你需要将省略的SELECT句部分替换为完整的语句，与原存储过程中的一致
        postgres_cursor.execute(insert_market_sql)  # 假设你已经构建了完整的SQL语句
        postgres_conn.commit()
        print(f"完成批次处理，已更新至 {a_dt}")
        if i % 10 == 0:  # 每处理10条显示一次详细进度
            print(f"\n已完成 {i} 条数据处理，当前日期: {a_dt}")

# 清空 PostgreSQL 表
def clear_postgres_table(table_name, postgres_conn):
    try:
        cursor = postgres_conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        postgres_conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error clearing PostgreSQL table: {e}")


# 数据迁移函数
def migrate_data(mysql_table, postgres_table, mysql_engine=sql_engine, postgres_conn=postgres_conn):
    try:
        with sql_engine.begin() as _cursor:
            # 从 MySQL 读取数据
            df = pd.read_sql(f"SELECT * FROM {mysql_table}", _cursor)

        # 清空 PostgreSQL 表
        clear_postgres_table(postgres_table, postgres_conn)

        # 将 DataFrame 转换为元组列表
        data_tuples = list(df.itertuples(index=False, name=None))

        # 构建 SQL 插入语句
        columns = ', '.join(df.columns)
        insert_query = f'INSERT INTO {postgres_table} ({columns}) VALUES %s'

        # 使用 psycopg2 进行批量插入
        cursor = postgres_conn.cursor()
        execute_values(cursor, insert_query, data_tuples)
        postgres_conn.commit()  # 使用连接对象来提交事务
        cursor.close()

        print(f"Data migrated successfully from {mysql_table} to {postgres_table}")

    except (psycopg2.Error, pd.io.sql.DatabaseError) as e:
        print(f"Error in data migration: {e}")
     
        


# 主执行流程
def main():
    update_basicinfo()
    today = datetime.today()
    if today.day == 1:
        update_外评()
    # 执行数据迁移
    for i in ['bond.basicinfo_all','bond.basicinfo_hzcurve']:
        print(f'迁移{i}')
        migrate_data(i, i.split('.')[1])
    
    print("开始执行曲线更新流程...")
    
    print("\n1. 更新MySQL marketinfo_hzcurve")
    update_mysql_marketinfo_hzcurve(sql_engine)
    
    print("\n2. 迁移数据至PostgreSQL")
    migrate_data_to_postgres(sql_engine, postgres_conn, ['bond.marketinfo_hzcurve'], 'marketinfo_hzcurve')
    
    print("\n3. 更新PostgreSQL marketinfo_hzcurve")
    update_postgres_marketinfo_hzcurve(postgres_conn)
    
    print("\n4. 迁移数据回MySQL")
    migrate_data_to_mysql(sql_engine, postgres_conn, ['marketinfo_hzcurve'], 'bond.marketinfo_hzcurve')
    
    print("\n所有更新流程已完成!")

if __name__ == "__main__":
    main()