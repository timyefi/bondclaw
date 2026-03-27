import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import text
from datetime import datetime, date, timedelta
import psycopg2
import time


_cursor_pg='postgresql://postgres:hzinsights2015@139.224.201.106:18032/tsdb'

def trans_sql(sql1):
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    sql_engine = sqlalchemy.create_engine(
        'mysql+pymysql://%s:%s@%s:%s/%s' % (
            'hz_work',
            'Hzinsights2015',
            'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            '3306',
            'bond',
        ), poolclass=sqlalchemy.pool.NullPool
    )
    _cursor = sql_engine.connect()
    while retry_count < max_retries:
        try:
            # 开始事务
            trans = _cursor.begin()
            try:
                # 执行UPDATE语句
                _cursor.execute(sql1)
                # 提交事务
                trans.commit()

            except Exception as e:
                # 如果出错，回滚事务
                trans.rollback()
                raise e

            break  # 如果成功，则退出循环

        except Exception as e:
            print(f"Error: {e}")
            print(sql1)
            retry_count += 1
            time.sleep(1)  # 休眠一秒后重试

def trans_sql1(sql1):
    print('开始pg任务', sql1)
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    # 连接数据库
    connection = psycopg2.connect(
        host="139.224.201.106",
        port=18032,
        user="postgres",
        password="hzinsights2015",
        database="tsdb"
    )

    # Create a cursor
    cursor = connection.cursor()

    # Loop for retries
    while retry_count < max_retries:
        try:
            # Start transaction
            connection.autocommit = False
            cursor.execute(sql1)
            # Commit transaction
            connection.commit()
            print('Task completed successfully')
            break  # If successful, break the loop

        except Exception as e:
            print(f"Error: {e}")
            print(sql1)
            retry_count += 1
            print(f'Retry attempt {retry_count}, waiting for 1 second...')
            time.sleep(1)  # Wait for 1 second before retrying

        finally:
            # Close the cursor and connection to free resources
            cursor.close()
            connection.close()

    if retry_count == max_retries:
        print("Max retries reached. Operation failed.")

def trans_sql2(sql1):
    # 循环重试
    max_retries = 3  # 设置最大重试次数
    retry_count = 0
    # 连接数据库
    connection = psycopg2.connect(
        host="139.224.201.106",
        port=18032,
        user="postgres",
        password="hzinsights2015",
        database="hzcurve"
    )

    # 创建游标
    _cursor1 = connection.cursor()
    while retry_count < max_retries:
        try:
            # 开始事务
            connection.autocommit = False  # 禁用自动提交
            _cursor1.execute(sql1)
            # 提交事务
            connection.commit()

            break  # 如果成功，则退出循环

        except Exception as e:
            print(f"Error: {e}")
            print(sql1)
            retry_count += 1
            time.sleep(1)  # 休眠一秒后重试
    else:
        print("Max retries reached. Operation failed.")

trans_sql1(f"""TRUNCATE 债券新分类""")
trans_sql1(f"""
        INSERT INTO 债券新分类 (trade_code,是否城投,行业,区域,金融机构类型,abs类型,发行方式,是否永续,是否次级)
        SELECT
            trade_code,
            ths_is_city_invest_debt_yy_bond as 是否城投,
            CASE
                WHEN ths_object_the_sw_bond LIKE '%%银行%%' THEN '' 
                WHEN ths_object_the_sw_bond LIKE '%%证券%%' THEN '非银金融--多元金融--其他多元金融'
                WHEN ths_object_the_sw_bond LIKE '%%保险%%' THEN '非银金融--多元金融--其他多元金融'
                ELSE ths_object_the_sw_bond 
            END AS 行业,
            ths_urban_platform_area_bond as 区域,
            CASE
                WHEN ths_object_the_sw_bond LIKE '%%银行%%' THEN '银行' 
                ELSE '' END AS 金融机构类型,
            '' as ABS类型,
            ths_issue_method_bond as 发行方式,
            ths_is_perpetual_bond as 是否永续,
            ths_is_subordinated_debt_bond as 是否次级
            FROM basicinfo_credit
            UNION
            SELECT
            trade_code,
            '' as 是否城投,
            '' as 行业,
            '' as 区域,
            CASE
                WHEN ths_org_type_bond LIKE '%%银行%%' THEN '银行'
                WHEN ths_org_type_bond LIKE '%%证券公司%%' THEN '证券公司'
                WHEN ths_org_type_bond LIKE '%%保险%%' THEN '保险' 
                WHEN ths_ths_bond_third_type_bond = '其他非银金融机构债' THEN '其他'       
            END AS 金融机构类型,
            '' as ABS类型,
            ths_issue_method_bond as 发行方式,
            ths_is_perpetual_bond as 是否永续,
            ths_is_subordinated_debt_bond as 是否次级
            FROM basicinfo_finance
            UNION
            SELECT
                a.trade_code,
                '' as 是否城投,
                '' as 行业,
                '' as 区域,
                '' AS 金融机构类型,
                CASE
                    WHEN SUM(CASE WHEN b.担保人是否城投 = '是' THEN 1 ELSE 0 END) > 0 OR SUM(CASE WHEN c.原始权益人是否城投 = '是' THEN 1 ELSE 0 END) > 0 THEN '城投'
                    WHEN SUM(CASE WHEN a.底层资产类型 LIKE '%%互联网%%' THEN 1 ELSE 0 END) > 0 THEN '消金小贷'
                    WHEN SUM(CASE WHEN a.底层资产类型 LIKE '%%信用卡%%' OR a.底层资产类型 LIKE '%%不良%%' THEN 1 ELSE 0 END) > 0 THEN '银行信贷资产'
                    WHEN SUM(CASE WHEN a.底层资产类型 LIKE '%%REITs%%' THEN 1 ELSE 0 END) > 0 THEN 'REITs'
                    WHEN SUM(CASE WHEN a.底层资产类型 != '' THEN 1 ELSE 0 END) > 0 THEN '租赁保理综合'
                    WHEN SUM(CASE WHEN a.abs行业分类 LIKE '%%银行%%' THEN 1 ELSE 0 END) > 0 THEN '银行信贷资产'
                    WHEN SUM(CASE WHEN b.担保人行业 LIKE '%%建筑%%' THEN 1 ELSE 0 END) > 0 THEN '建筑供应链'
                    WHEN SUM(CASE WHEN b.担保人行业 LIKE '%%房地产%%' THEN 1 ELSE 0 END) > 0 THEN '房地产'
                    WHEN SUM(CASE WHEN b.担保人行业 LIKE '%%多元金融%%' OR b.担保人行业 LIKE '%%综合%%' OR b.担保人行业 = '' THEN 1 ELSE 0 END) > 0 THEN '租赁保理综合'
            ELSE '央国企供应链'
                END AS ABS类型,
                a.发行方式,
                '否' as 是否永续,
                '否' as 是否次级
            FROM 
            ( 
                SELECT
                    trade_code,
                    ths_bond_short_name_bond as 简称,
                    ths_issue_method_bond as 发行方式,
                    ths_b_abs_defiguarantor_bond as 担保人,
                    ths_sponsor_to_original_righter_bond as 原始权益人,
                    ths_abs_swi_industry_bond as abs行业分类,
                    ths_basic_asset_type_detail_bond as 底层资产类型
                FROM basicinfo_abs
            )a
            LEFT JOIN (
                SELECT DISTINCT ths_issuer_name_cn_bond as 发行人, ths_is_city_invest_debt_yy_bond as 担保人是否城投, ths_object_the_sw_bond as 担保人行业
                FROM basicinfo_credit WHERE ths_issuer_name_cn_bond !=''
            ) b ON a.担保人 LIKE '%%' || b.发行人 || '%%'
            left JOIN (
                SELECT DISTINCT ths_issuer_name_cn_bond as 发行人, ths_is_city_invest_debt_yy_bond as 原始权益人是否城投
                FROM basicinfo_credit WHERE ths_issuer_name_cn_bond !=''
            ) c ON a.原始权益人 LIKE '%%' || c.发行人 || '%%'
						GROUP BY trade_code,a.发行方式 ON CONFLICT (trade_code) DO NOTHING""")



trans_sql1(f"""TRUNCATE TC最新所属曲线""")
trans_sql1(f"""
    INSERT INTO TC最新所属曲线 (trade_code, 代码,日期)
    SELECT
        A.trade_code,
        CASE
            WHEN B.是否城投='否' AND B.行业!='' THEN
                concat('产业','_',B.行业, '_', A.imrating_calc, '_', B.发行方式, '_', B.是否永续, '_', B.是否次级, '_', '否')
            WHEN B.是否城投='是' AND B.区域!='' THEN
                concat('城投','_',B.区域, '_', A.imrating_calc, '_', B.发行方式, '_', B.是否永续, '_', B.是否次级, '_', '否')
            WHEN B.金融机构类型!='' THEN
                concat('金融','_',B.金融机构类型, '_', A.imrating_calc, '_', B.发行方式, '_', B.是否永续, '_', B.是否次级, '_', '否')
            WHEN B.ABS类型!='' THEN
                concat('ABS','_',B.ABS类型, '_', A.imrating_calc, '_', B.发行方式, '_', B.是否永续, '_', B.是否次级, '_', '否')
        END AS 代码,
        '2024-2-28' as 日期
    FROM (SELECT
            trade_code,
            last(imrating_calc, dt) as imrating_calc
        FROM hzcurve_credit
        WHERE target_term=2
        and stdyield > 0
        GROUP BY trade_code) A
    LEFT JOIN 债券新分类 B 
    ON A.trade_code = B.trade_code;
    """)


trans_sql1(f"""TRUNCATE 曲线代码""")
trans_sql1(f"""
INSERT INTO 曲线代码 (代码, 大类, 子类, 评级, 发行方式, 是否永续, 是否次级, 清单)
SELECT DISTINCT
  "代码",
  split_part("代码", '_', 1) AS 大类,
  split_part("代码", '_', 2) AS 子类,
  split_part("代码", '_', 3) AS 评级,
  split_part("代码", '_', 4) AS 发行方式,
  split_part("代码", '_', 5) AS 是否永续,
  split_part("代码", '_', 6) AS 是否次级,
  split_part("代码", '_', 7) AS 清单
FROM TC最新所属曲线
where 代码 is not null;""")



trans_sql1(f"""
INSERT INTO basicinfo_industrytype1(申万行业, 申万一级, 申万二级, 申万三级, 一级分类,二级分类,三级分类,四级分类)
SELECT
ths_object_the_sw_bond as 申万行业,
split_part(ths_object_the_sw_bond, '--', 1) as 申万一级,
split_part(ths_object_the_sw_bond, '--', 2) as 申万二级,
split_part(ths_object_the_sw_bond, '--', 3) as 申万三级,
B.一级分类,
B.二级分类,
B.三级分类,
B.四级分类
from(
select 
distinct ths_object_the_sw_bond
from basicinfo_credit
WHERE ths_object_the_sw_bond is not NULL) A
LEFT JOIN basicinfo_industrytype B
ON split_part(A.ths_object_the_sw_bond, '--', 1)=B.四级分类
ON CONFLICT (申万行业) DO NOTHING""")

trans_sql1(f"""
INSERT INTO new_hzcurve_credit
SELECT dt, trade_code, balance, imrating_calc, target_term, stdyield FROM hzcurve_credit
WHERE dt = (SELECT MAX(dt) FROM hzcurve_credit);""")

trans_sql1(f"""
INSERT INTO new_hzcurve_credit
SELECT dt, trade_code, balance, imrating_calc, target_term, stdyield FROM hzcurve_credit_long
WHERE dt = (SELECT MAX(dt) FROM hzcurve_credit_long);""")