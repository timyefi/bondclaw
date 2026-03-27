import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

from sqlalchemy import create_engine
import pandas as pd

sql_engine = create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    )
)
conn = sql_engine.connect()
import iFinDPy as THS
from sql_conns_new import insert_update_info, insert_database

THS.THS_iFinDLogin('hznd002', '160401')
# THS.THS_iFinDLogin('hzmd112', '992555')

import pandas as pd
import pymysql

prame_dic = {
    'ths_bond_short_name_bond': '',
    'ths_ths_bond_third_type_bond': '',
    'ths_conceptualsector_bond_type_bond': '',
    'ths_listed_date_bond': '',
    'ths_delist_date_bond': '',
    'ths_nominal_interest_current_bond': '',
    'ths_nominal_interest_at_issuing_bond': '',
    'ths_bond_maturity_theory_bond': '',
    'ths_interest_begin_date_bond': '',
    'ths_maturity_date_bond': '',
    'ths_next_strikedate_bond': '',
    'ths_issue_method_bond': '212',
    'ths_is_cross_mkt_bond': '',
    'ths_issue_total_amt_bond': '',
    'ths_issuer_name_cn_bond': '',
    'ths_actual_controller_name_bond': '',
    'ths_special_clause_explain_bond': '',
    'ths_org_type_bond': '',
    'ths_is_lc_bond': '',
    'ths_issuer_respond_district_bond': '1',
    'ths_issuer_respond_district_bond_province': '1',
    'ths_issuer_respond_district_bond_city': '2',
    'ths_issuer_respond_district_bond_county': '3',
    'ths_is_perpetual_bond': '',
    'ths_is_subordinated_debt_bond': '',
    'ths_grnt_bond': '',
    'ths_urban_platform_area_bond': '',
    'ths_city_bond_administrative_level_yy_bond': '',
    'ths_is_issuing_failure_bond': '',

    # credit新增
    'ths_is_city_invest_debt_yy_bond': '',
    'ths_is_city_invest_debt_ifind_bond': '',
    'ths_object_the_sw_bond': '103',

    # abs
    'ths_project_full_name_bond': '',
    'ths_sponsor_to_original_righter_bond': '0',
    'ths_abs_swi_industry_bond': '0,103',
    'ths_abs_province_bond': '',
    'ths_basic_asset_type_detail_bond': '',
    'ths_b_abs_defiguarantor_bond': '',

    'ths_ipo_actual_issue_total_amt_bond':'',

	# equity
	'ths_stock_code_cbond': '',

    # 统一新增 但不展示
    'ths_main_sec_code_bond': '',
    'ths_bond_isin_code_bond': ''


}

duplicate_dic = {
    'ths_issuer_respond_district_bond_province': 'ths_issuer_respond_district_bond',
    'ths_issuer_respond_district_bond_city': 'ths_issuer_respond_district_bond',
    'ths_issuer_respond_district_bond_county': 'ths_issuer_respond_district_bond'
}


def check_table_quality(conn, table_name):
    """
    检查指定MySQL表的数据质量。

    参数:
    conn: 已经建立的数据库连接对象。
    table_name: 要检查的表名。

    返回:
    DataFrame，列出每一列的空值数量及其所占比例。
    """
    # 获取总行数
    total_rows = pd.read_sql(f"SELECT COUNT(*) FROM {table_name}", conn).iloc[0, 0]

    # 获取列名
    query = f"SELECT * FROM {table_name} LIMIT 1;"
    sample_df = pd.read_sql(query, conn)
    col_names = sample_df.columns.tolist()

    # 对每一列进行空值统计及比例计算
    null_stats = []
    for col in col_names:
        count_query = f"SELECT COUNT(*) FROM {table_name} WHERE `{col}` IS NULL OR `{col}` = '';"
        null_count = pd.read_sql(count_query, conn).iloc[0, 0]
        null_percentage = (null_count / total_rows) * 100
        null_stats.append((col, null_count, null_percentage))

    # 创建DataFrame展示结果
    result_df = pd.DataFrame(null_stats, columns=['Column', 'Null Count', 'Null Percentage'])
    return result_df


def get_null_trade_codes(conn, table_name):
    """
    对于每列为空的行，获取其对应的 trade_code 值。

    参数:
    conn: 数据库连接对象。
    table_name: 表名。

    返回:
    每列为空时对应的 trade_code 值的字典。
    """
    query = f"SELECT * FROM {table_name} LIMIT 1;"
    sample_df = pd.read_sql(query, conn)
    col_names = sample_df.columns.tolist()

    null_trade_codes = {}
    for col in col_names:
        if col != 'trade_code':  # 排除 trade_code 列
            query = f"SELECT trade_code FROM {table_name} WHERE `{col}` IS NULL;"
            # query = f"SELECT trade_code FROM {table_name} WHERE `{col}` IS NULL OR `{col}` = '';"
            trade_codes = pd.read_sql(query, conn)['trade_code'].tolist()
            null_trade_codes[col] = trade_codes

    return null_trade_codes


def get_all_trade_codes(conn, table_name):
    """
    对于每列为空的行，获取其对应的 trade_code 值。

    参数:
    conn: 数据库连接对象。
    table_name: 表名。

    返回:
    每列为空时对应的 trade_code 值的字典。
    """
    query = f"SELECT * FROM {table_name} LIMIT 1;"
    sample_df = pd.read_sql(query, conn)
    col_names = sample_df.columns.tolist()

    all_trade_codes = {}
    for col in col_names:
        if col != 'trade_code':  # 排除 trade_code 列
            query = f"SELECT trade_code FROM {table_name};"
            # query = f"SELECT trade_code FROM {table_name} WHERE `{col}` IS NULL OR `{col}` = '';"
            trade_codes = pd.read_sql(query, conn)['trade_code'].tolist()
            all_trade_codes[col] = trade_codes

    return all_trade_codes


def compare_dataframes(df1, df2):
    """
    比较两个DataFrame，显示数据质量变化。

    参数:
    df1: 更新前的数据质量DataFrame。
    df2: 更新后的数据质量DataFrame。

    返回:
    变化的DataFrame。
    """
    # 合并两个DataFrame以进行比较
    comparison_df = pd.merge(df1, df2, on='Column', suffixes=('_before', '_after'))

    # 计算空值数量的变化
    comparison_df['Null Count Change'] = comparison_df['Null Count_after'] - comparison_df['Null Count_before']

    # 计算空值百分比的变化
    comparison_df['Null Percentage Change'] = comparison_df['Null Percentage_after'] - comparison_df[
        'Null Percentage_before']

    return comparison_df


def perform_updates(null_trade_codes, col, table_name, prame_dic, duplicate_dic):
    slice_size = 1000  # 每个切片包含的数据数量
    if col == 'all':
        cols = list(null_trade_codes.keys())
    elif isinstance(col, str):
        cols = [col]
    elif isinstance(col, list):
        cols = col
    else:
        return None
    for _col in cols:
        code_list = null_trade_codes.get(_col, [])
        if len(code_list) == 0:
            continue
        # 计算需要多少个切片
        total_slices = len(code_list) // slice_size + (1 if len(code_list) % slice_size != 0 else 0)
        code_dt = pd.read_sql("SELECT DT FROM `stock`.`indexcloseprice` WHERE `TRADE_CODE` = '881001.WI' ORDER BY `DT` DESC limit 1", conn)['DT'].apply(lambda x:x.strftime('%F'))[0]
        for i in range(total_slices):
            start_idx = i * slice_size
            end_idx = (i + 1) * slice_size
            current_slice = code_list[start_idx:end_idx]  # 获取当前切片
            _code_str = ",".join(current_slice)

            if _code_str != '':
                _prame_dic = {duplicate_dic.get(i[0], i[0]): i[1] for i in prame_dic.items() if i[0] in [_col]}
                # code_dt = '2023-11-22'
                # print(_code_str, _prame_dic)
                result = THS.THS_DS(_code_str, ";".join(_prame_dic.keys()), ";".join(_prame_dic.values()), '', code_dt,
                                    code_dt)
                if result.errorcode != 0:
                    print(result.errmsg,
                          f"""THS.THS_DS('{_code_str}', '{";".join(_prame_dic.keys())}', '{";".join(_prame_dic.values())}','','{code_dt}','{code_dt}')""")
                    continue
                result = result.data.rename(columns={duplicate_dic.get(_col, _col): _col})

                # if _col == 'ths_issuer_respond_district_bond':
                #     c1 = THS.THS_DS(_code_str,'ths_issuer_respond_district_bond','2','',code_dt,code_dt).data
                #     c2 = THS.THS_DS(_code_str,'ths_issuer_respond_district_bond','3','',code_dt,code_dt).data
                #     c = c.merge(c1, on=['time', 'thscode'])
                #     c = c.merge(c2, on=['time', 'thscode'])
                #     c = c.rename(columns={
                #         'ths_issuer_respond_district_bond_x': 'ths_issuer_respond_district_bond_province',
                #         'ths_issuer_respond_district_bond_y': 'ths_issuer_respond_district_bond_city',
                #         'ths_issuer_respond_district_bond': 'ths_issuer_respond_district_bond_county'
                #     })

            result = result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'})

            del result['DT']
            # c.to_sql('basicinfo', conns, if_exists='append', index=False)
            insert_database(result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'}), table_name, ['TRADE_CODE'])
            insert_update_info(result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'}), table_name, 'THS')
            print(_col, result.shape)


def fetch_rows_with_nulls_except_first_col(conn, table_name):
    # 读取表结构以获取列名
    df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 0", conn)
    columns = df.columns

    # 构建查询除了第一列之外其余列全为空的数据的 SQL 查询
    if len(columns) > 1:
        first_column = columns[0]  # 第一列
        other_columns = columns[1:]  # 除了第一列之外的其他列
        where_clause = ' AND '.join([f"`{col}` IS NULL" for col in other_columns])  # 构建 WHERE 子句
        query = f"SELECT {first_column} FROM {table_name} WHERE {where_clause}"# + " AND TRADE_CODE != '102382914Z01.IB'"
        data = pd.read_sql(query, conn)['trade_code'].tolist()
        # 执行查询并返回结果
        return {i:data for i in other_columns}
    else:
        print("Table has only one column or no columns.")
        return {}


# 待补充
# bond.basicinfo_credit
# ['ths_is_city_invest_debt_ifind_bond',
#  'ths_object_the_sw_bond']

# bond.basicinfo_abs
# ths_project_full_name_bond

basicinfo_list = [
                  'basicinfo_abs',
                  'basicinfo_equity',
                  'basicinfo_finance',
                  'basicinfo_rate',
                  'basicinfo_credit'
]
for basicinfo_name in basicinfo_list:
    table_name = 'bond.' + basicinfo_name
    col = 'all'
    # col = ['ths_listed_date_bond']
    # for i in col:
    #     if i not in prame_dic:
    #         raise KeyError(f"Key not found: {i}")

    quality_df = check_table_quality(conn, table_name)
    print(quality_df)

    # table_name = 'bond.basicinfo_credit'
    # col = ['ths_is_city_invest_debt_yy_bond', 'ths_is_city_invest_debt_ifind_bond', 'ths_object_the_sw_bond']
    # quality_df = check_table_quality(conn, table_name)

    # 二选一：获取每列为空 or 全行为空 的 trade_code 值, 后者用于每日更新
    null_trade_codes_col_null = get_null_trade_codes(conn, table_name)
    null_trade_codes_row_null = fetch_rows_with_nulls_except_first_col(conn, table_name)

    # 执行更新逻辑
    perform_updates(null_trade_codes_col_null, [
        'ths_interest_begin_date_bond',
        'ths_maturity_date_bond',
        'ths_issue_method_bond',
        'ths_issuer_name_cn_bond'], table_name, prame_dic, duplicate_dic)

    all_trade_codes_col = get_all_trade_codes(conn, table_name)
    # 执行更新逻辑
    perform_updates(all_trade_codes_col, ['ths_ths_bond_third_type_bond'], table_name, prame_dic, duplicate_dic)

    # 再次检查表的数据质量，以对比变化
    updated_quality_df = check_table_quality(conn, table_name)
    print(compare_dataframes(quality_df, updated_quality_df))


    # 执行更新逻辑
    perform_updates(null_trade_codes_row_null, col, table_name, prame_dic, duplicate_dic)

    # 再次检查表的数据质量，以对比变化
    updated_quality_df = check_table_quality(conn, table_name)
    print(compare_dataframes(quality_df, updated_quality_df))
