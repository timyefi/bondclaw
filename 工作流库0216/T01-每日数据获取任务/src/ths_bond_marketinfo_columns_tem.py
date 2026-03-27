import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

from sqlalchemy import create_engine
import time
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

prame_dic = {'ths_remain_duration_y_bond': '',
             'ths_bond_balance_bond': '',
             'ths_specified_date_subject_rating_bond': '100',
             'ths_specified_date_bond_rating_bond': '100',
             'ths_evaluate_yeild_cfets_bond': '',
             'ths_evaluate_yield_shch_bond': '',
             'ths_evaluate_yield_yy_bond': '',
             'ths_yy_default_ratio_bond': '',
             'ths_evaluate_yield_cb_bond': '100',
             'ths_evaluate_yield_cb_bond_exercise': '102',
             'ths_repay_years_cb_bond': '100',
             'ths_repay_years_cb_bond_exercise': '102',
             'ths_evaluate_interest_durcb_bond_exercise': '102',
             'ths_evaluate_spread_durcb_bond_exercise': '102',
             'ths_evaluate_modified_dur_cb_bond_exercise': '102',
             'ths_evaluate_modified_dur_cb_bond': '100',
             'ths_cb_market_implicit_rating_bond': '',
             'ths_subject_latest_rating_yy_bond': '',
             'ths_evaluate_convexity_cb_bond': '102',
             'ths_evaluate_net_price_cb_bond': '102',
             'ths_valuate_full_price_cb_bond': '102'}

duplicate_dic = {
    'ths_evaluate_yield_cb_bond_exercise': 'ths_evaluate_yield_cb_bond',
    'ths_repay_years_cb_bond_exercise': 'ths_repay_years_cb_bond',
    # 'ths_issuer_respond_district_bond_county': 'ths_issuer_respond_district_bond',
    'ths_evaluate_interest_durcb_bond_exercise': 'ths_evaluate_interest_durcb_bond',
    'ths_evaluate_spread_durcb_bond_exercise': 'ths_evaluate_spread_durcb_bond',
    'ths_evaluate_modified_dur_cb_bond_exercise': 'ths_evaluate_modified_dur_cb_bond'
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
        if col != 'trade_code':  # 排除 trade_code 列
            query = f"SELECT trade_code FROM {table_name} WHERE `{col}` IS NULL OR `{col}` = '0000-00-00' OR `{col}` = '';"
            trade_codes = pd.read_sql(query, conn)['trade_code'].tolist()
            null_trade_codes[col] = trade_codes

    return null_trade_codes


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


def perform_updates(null_trade_codes, col, table_name, prame_dic, duplicate_dic, _now_dt, _now_dt1=''):
    # print(1111, null_trade_codes)
    slice_size = 5000  # 每个切片包含的数据数量
    if col == 'all':
        cols = list(null_trade_codes.keys())
        # ['ths_bond_balance_bond', 'ths_cb_market_implicit_rating_bond', 'ths_evaluate_yield_cb_bond_exercise',
        #  'ths_repay_years_cb_bond_exercise']
    elif col == 'head':
        cols = ['ths_bond_balance_bond']
    elif isinstance(col, str):
        cols = [col]
    elif isinstance(col, list):
        cols = col
    else:
        return None
    for _col in cols:
        if _col == 'ths_evaluate_yield_yy_bond':
            now_dt = _now_dt1
        else:
            now_dt = _now_dt
        code_list = null_trade_codes.get(_col, [])
        if len(code_list) == 0:
            print(_col, 'continue')
            continue
        # 计算需要多少个切片
        total_slices = len(code_list) // slice_size + (1 if len(code_list) % slice_size != 0 else 0)

        for i in range(total_slices):
            start_idx = i * slice_size
            end_idx = (i + 1) * slice_size
            current_slice = code_list[start_idx:end_idx]  # 获取当前切片
            _code_str = ",".join(current_slice)

            if _code_str != '':
                _prame_dic = {duplicate_dic.get(i[0], i[0]): i[1] for i in prame_dic.items() if i[0] in [_col]}
                # result = THS.THS_DS(_code_str, ";".join(_prame_dic.keys()), ";".join(_prame_dic.values()), '', now_dt,
                #                     now_dt)
                # if result.errorcode != 0:
                #     print(result.errmsg,
                #           f"""THS.THS_DS('{_code_str}', '{";".join(_prame_dic.keys())}', '{";".join(_prame_dic.values())}','','{now_dt}','{now_dt}')""")
                #     continue

                retry_limit = 5  # 设置重试次数
                retry_interval = 1  # 设置每次重试之间的等待时间（秒）

                for attempt in range(retry_limit):
                    result = THS.THS_DS(_code_str, ";".join(_prame_dic.keys()), ";".join(_prame_dic.values()), '',
                                        now_dt, now_dt)
                    if result.errorcode == 0:
                        break  # 如果成功，跳出循环
                    else:
                        print(result.errmsg,
                              f"""THS.THS_DS('{_code_str}', '{";".join(_prame_dic.keys())}', '{";".join(_prame_dic.values())}','','{now_dt}','{now_dt}')""")
                        if attempt < retry_limit - 1:
                            time.sleep(retry_interval)  # 等待一段时间后重试
                else:
                    print("重试次数已达上限，操作失败。")
                    continue

                # if result.data.empty:
                #     continue
                result = result.data.rename(columns={duplicate_dic.get(_col, _col): _col})

                # if _col == 'ths_issuer_respond_district_bond':
                #     c1 = THS.THS_DS(_code_str,'ths_issuer_respond_district_bond','2','',code_dt,code_dt).data
                #     c2 = THS.THS_DS(_code_str,'ths_issuer_respond_district_bond','3','',code_dt,code_dt).data
                #     c = c.merge(c1, on=['time', 'thscode'])
                #     c = c.merge(c2, on=['time', 'thscode'])
                #     c = c.rename(columns={
                #         'ths_issuer_respond_district_bond_x': 'ths_issuer_respond_district_bond_province',
                #         'ths_issuer_respond_district_bond_y': 'ths_issuer_respond_district_bond_city',
                #         'ths_issuer_respond_district_bond': 'ths_issuer_respond_district_bond_county'
                #     })

            result = result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'})
            # return result
            insert_database(result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'}), table_name, ['DT', 'TRADE_CODE'])
            insert_update_info(result.rename(columns={'time': 'DT', 'thscode': 'TRADE_CODE'}), table_name, 'THS')
            print(_col, result.shape)
            # break


def fetch_trade_codes_within_date_range(conn, table_name, new_dt, date_condition_type=""):
    # 读取表结构以获取列名
    df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 0", conn)
    columns = df.columns

    # 检查是否有多于一个列
    if len(columns) > 1:
        first_column = columns[1]  # 第一列，通常是 trade_code
        other_columns = columns[2:]  # 除了第一列之外的其他列
        # 构建查询在指定日期范围内的数据的 SQL 查询
        # date_condition1 = f"(`ths_interest_begin_date_bond` < '{new_dt}' AND `ths_maturity_date_bond` > '{new_dt}' AND `ths_delist_date_bond` > '{new_dt}' AND `ths_is_issuing_failure_bond` != '是')"
        date_condition1 = f"""(
            (`ths_interest_begin_date_bond` < '{new_dt}' OR `ths_interest_begin_date_bond` IS NULL OR `ths_interest_begin_date_bond` = '0000-00-00') 
            AND 
            (`ths_maturity_date_bond` > '{new_dt}' OR `ths_maturity_date_bond` IS NULL OR `ths_maturity_date_bond` = '0000-00-00') 
            AND 
            (`ths_delist_date_bond` > '{new_dt}' OR `ths_delist_date_bond` IS NULL OR `ths_delist_date_bond` = '0000-00-00') 
            AND 
            `ths_is_issuing_failure_bond` != '是'
        )"""

        if table_name != 'bond.marketinfo_abs':
           _table_name = table_name.replace('marketinfo', 'basicinfo')
           date_condition1 = date_condition1 + f""" AND 
            TRADE_CODE NOT IN ( SELECT trade_code FROM {_table_name} WHERE trade_code != ths_main_sec_code_bond AND ths_main_sec_code_bond IS NOT NULL ) """
        if date_condition_type == 'exclude':
            date_condition2 = f" AND TRADE_CODE NOT IN (SELECT TRADE_CODE from {table_name} where DT = '{new_dt}')"
        elif date_condition_type == 'include':
            date_condition2 = f" AND TRADE_CODE IN (SELECT TRADE_CODE from {table_name} where DT = '{new_dt}')"
        else:
            date_condition2 = ""
        if table_name == 'bond.marketinfo_finance':
            date_condition2 += " AND TRADE_CODE NOT IN (SELECT TRADE_CODE from bond.basicinfo_finance where ths_ths_bond_third_type_bond in ('一般同业存单', '自贸区同业存单'))"
        query = f"SELECT {first_column} FROM {table_name.replace('market', 'basic')} WHERE {date_condition1} {date_condition2}"

        # 执行查询
        trade_codes = pd.read_sql(query, conn)[first_column].tolist()

        # 构建结果字典，每个列名都映射到相同的 trade_code 列表
        return {col: trade_codes for col in other_columns}
    else:
        print("Table has only one column or no columns.")
        return {}


def query_trade_codes(conn, table_name, now_dt, extra_sql='', col='ths_bond_balance_bond'):
    query = f"SELECT TRADE_CODE FROM {table_name} WHERE {col} > 0 and DT = '{now_dt}' {extra_sql}"
    try:
        df = pd.read_sql(query, conn)
        return df['TRADE_CODE'].tolist()
    except Exception as e:
        print(f"发生错误: {e}")
        return []

def split_dict(original_dict, keys_list):
    # 保留列表中指定键的字典
    dict_with_keys = {key: value for key, value in original_dict.items() if key in keys_list}
    # 保留除了列表中指定键外的其他键的字典
    dict_without_keys = {key: value for key, value in original_dict.items() if key not in keys_list}
    
    # 返回两个字典
    return dict_with_keys, dict_without_keys

marketinfo_list = [
                  'marketinfo_abs',
                  'marketinfo_finance',
                #   'marketinfo_rate',
                  'marketinfo_credit'
]
now_dts = pd.read_sql("SELECT DT FROM `stock`.`indexcloseprice` WHERE `TRADE_CODE` = '881001.WI' and dt < '2024-08-30' ORDER BY `DT` DESC limit 31", conn)['DT'].apply(lambda x:x.strftime('%F')).to_list()
for now_dt in now_dts[:-1]:
    print(11111111111, now_dt)
    # now_dt = '2023-11-22'
    for marketinfo_name in marketinfo_list:
        table_name = 'bond.' + marketinfo_name

        # if now_dt == pd.read_sql(f"SELECT max(DT) as DT FROM {table_name}", conn)['DT'].apply(lambda x:x.strftime('%F')).to_list()[0]:
        #     # 补已有空数据
        #     true_trade_codes = fetch_trade_codes_within_date_range(conn, table_name, now_dt, date_condition_type='')
        #     cols = ['ths_cb_market_implicit_rating_bond', 'ths_evaluate_yield_cb_bond_exercise', 'ths_repay_years_cb_bond_exercise']
        #     for col in cols:
        #         true_trade_codes_modify = query_trade_codes(conn, table_name, now_dt, f'and {col} is null')
        #         # 对字典中每个键对应的列表执行交集操作
        #         for key in true_trade_codes:
        #             true_trade_codes[key] = list(set(true_trade_codes[key]) & set(true_trade_codes_modify))
        #         result = perform_updates(true_trade_codes, [col], table_name, prame_dic, duplicate_dic, now_dt)
        # continue
        # else:
        true_trade_codes = fetch_trade_codes_within_date_range(conn, table_name, now_dt, date_condition_type='')

        col = ['ths_evaluate_net_price_cb_bond', 'ths_valuate_full_price_cb_bond']
        
        perform_updates(true_trade_codes, col, table_name, prame_dic, duplicate_dic, now_dt, now_dts[now_dts.index(now_dt)+1])
        





