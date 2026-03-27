import pandas as pd
import pymysql
from sqlalchemy import create_engine
from sql_conns_new import insert_update_info, insert_database

sql_engine = create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    ), pool_size=20, max_overflow=10, pool_timeout=10, pool_recycle=3600
)
conn = sql_engine.connect()

update_querys = [
    f"""
    delete from bond.basicinfo_credit
        WHERE trade_code in (select trade_code from bond.basicinfo_equity)
    """,
    f"""
    UPDATE bond.basicinfo_credit
        SET ths_is_city_invest_debt_yy_bond = '否'
        WHERE ths_issuer_name_cn_bond='中国国家铁路集团有限公司'
    """,
    f"""
    UPDATE bond.basicinfo_credit
        SET ths_urban_platform_area_bond =
        CASE
            WHEN ths_city_bond_administrative_level_yy_bond LIKE '%%区县%%' THEN
                CONCAT(ths_issuer_respond_district_bond_province, '-', ths_issuer_respond_district_bond_city, '-', ths_issuer_respond_district_bond_county)
            WHEN ths_city_bond_administrative_level_yy_bond LIKE '%%省%%' THEN
                CONCAT(ths_issuer_respond_district_bond_province)
            ELSE
                CONCAT(ths_issuer_respond_district_bond_province, '-', ths_issuer_respond_district_bond_city)
        END
        WHERE ths_is_city_invest_debt_yy_bond = '是'
        AND ths_urban_platform_area_bond = ''
    """,
    f"""
    UPDATE bond.basicinfo_credit bic
        JOIN marketinfo_credit mic ON bic.TRADE_CODE = mic.TRADE_CODE
        SET bic.ths_is_city_invest_debt_yy_bond = '否'
        WHERE mic.ths_cb_market_implicit_rating_bond = 'AAA-'
        AND bic.ths_is_city_invest_debt_yy_bond = '是'
    """,
    f"""
    UPDATE bond.basicinfo_credit bic
        JOIN marketinfo_credit mic ON bic.TRADE_CODE = mic.TRADE_CODE
        SET bic.ths_is_city_invest_debt_yy_bond = '是'
        WHERE mic.ths_cb_market_implicit_rating_bond = 'AA(2)'
        AND bic.ths_is_city_invest_debt_yy_bond <> '是'""",
    f"""
    UPDATE bond.basicinfo_credit bic
          JOIN marketinfo_credit mic ON bic.TRADE_CODE = mic.TRADE_CODE
          SET bic.ths_is_city_invest_debt_yy_bond = '是'
          WHERE mic.ths_cb_market_implicit_rating_bond = 'AA(2)'
          AND bic.ths_is_city_invest_debt_yy_bond <> '是'""",
    f"""
    INSERT IGNORE INTO basicinfo_xzqh_ct (城投区域, 省, 市, 区县)
    SELECT
        DISTINCT ths_urban_platform_area_bond AS 城投区域,
        SUBSTRING_INDEX(ths_urban_platform_area_bond, '-', 1) AS 省,
        SUBSTRING_INDEX(SUBSTRING_INDEX(ths_urban_platform_area_bond, '-', 2), '-', -1) AS 市,
        SUBSTRING_INDEX(ths_urban_platform_area_bond, '-', -1) AS 区县
    FROM
        basicinfo_credit
    WHERE
        ths_urban_platform_area_bond IS NOT NULL
    """,
    f"""
    INSERT IGNORE bond.basicinfo_industrytype1
    SELECT
        ths_object_the_sw_bond AS 申万行业,
        SUBSTRING_INDEX(SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 1), '--', -1) AS 申万一级,
        CASE 
            WHEN SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 2) = SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 1) 
            THEN NULL 
            ELSE SUBSTRING_INDEX(SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 2), '--', -1) 
        END AS 申万二级,
        CASE 
            WHEN SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 3) = SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 2) 
            THEN NULL 
            ELSE SUBSTRING_INDEX(SUBSTRING_INDEX(ths_object_the_sw_bond, '--', 3), '--', -1) 
        END AS 申万三级,
        B.一级分类,
        B.二级分类,
        B.三级分类,
        B.四级分类
    FROM (
        SELECT DISTINCT ths_object_the_sw_bond
        FROM basicinfo_credit
        WHERE ths_object_the_sw_bond IS NOT NULL
    ) A
    LEFT JOIN basicinfo_industrytype B ON SUBSTRING_INDEX(SUBSTRING_INDEX(A.ths_object_the_sw_bond, '--', 1), '--', -1) = B.四级分类
    """]


# update_querys += [
#     f"""
#         TRUNCATE 最新评级
#     """,
#     f"""
#         INSERT IGNORE  INTO 最新评级(trade_code, 评级)
#         SELECT 
#             m.trade_code, 
#             m.ths_cb_market_implicit_rating_bond as 评级
#         FROM 
#             bond.marketinfo_credit m
#         INNER JOIN (
#             SELECT 
#                 TRADE_CODE, 
#                 MAX(DT) as MaxDT
#             FROM 
#                 bond.marketinfo_credit 
#             GROUP BY 
#                 TRADE_CODE
#         ) AS subquery ON m.TRADE_CODE = subquery.TRADE_CODE AND m.DT = subquery.MaxDT
#         left JOIN basicinfo_credit b ON m.TRADE_CODE = b.TRADE_CODE      
#         union 
#         SELECT 
#             m.trade_code, 
#             m.ths_cb_market_implicit_rating_bond as 评级
#         FROM 
#             bond.marketinfo_finance m
#         INNER JOIN (
#             SELECT 
#                 TRADE_CODE, 
#                 MAX(DT) as MaxDT
#             FROM 
#                 bond.marketinfo_finance 
#             GROUP BY 
#                 TRADE_CODE
#         ) AS subquery ON m.TRADE_CODE = subquery.TRADE_CODE AND m.DT = subquery.MaxDT
#         left JOIN basicinfo_finance b ON m.TRADE_CODE = b.TRADE_CODE
#     """]

for update_query in update_querys:
    try:
        conn.execute(update_query)
    except Exception as e:
        print(e)
conn.close()