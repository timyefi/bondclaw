import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

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
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'bond',
    )
)
conn = sql_engine.connect()

conns = pymysql.connect(**sql_config)
conns.autocommit(1)
SQL = conns.cursor()

import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql
import sys

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
_cursor = sql_engine.connect()


def insert_database(raw: pd.DataFrame, db: str, key_list: list, mode='UPDATE', dt_type='DATE'):
    """
    :param raw:
    :param db:
    :param key_list:
    :param mode: 'update' or 'replace'
    :return:
    """
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
        if len(key_list) > 0:
            for key in key_list:
                col2.remove(key)

        update_str = ','.join(f'`{x}` = VALUES(`{x}`)' for x in col2)
        SQL.executemany(
            f"INSERT INTO {db} (`{'`,`'.join(x for x in col)}`) VALUES (%s{', %s' * (len(raw.columns) - 1)}) ON DUPLICATE KEY UPDATE {update_str}",
            processed_values)

    elif mode == 'REPLACE':
        SQL.executemany(
            f"REPLACE INTO {db} VALUES (%s{', %s' * (len(final_table.columns) - 1)})", processed_values)

    else:
        raise Exception('SELECT MODE IN (UPDATE, REPLACE)')


# 批量计算curve_abs

import numpy as np
import pandas as pd
from pymysql import cursors
from sqlalchemy import VARCHAR, Date, DECIMAL

# dt = _setting['dt']
# target_term = float(_setting['target_term'])
# sf_db = _setting['sf_db']
# sf_lc = _setting['sf_lc']
# sf_syl = _setting['sf_syl']
# qy = "','".join(x for x in ['-'.join(filter(None, i)) for i in _setting['qy']])
# name_com=_setting['name_com']
# fxfs="','".join(_setting['fxfs'])
# is_yx="','".join(_setting['is_yx'])
# yhpj="','".join(_setting['yhpj'])
# list1 = "','".join(_setting['list1'])

# dt='2023-12-01'
# target_term = 2.0
sf_db = 'db1'
sf_lc = 'lc1'
sf_syl = 'syl1'
# sf_cz = 'cz1'
# sf_xz = 'xz3'
name_com = '无'
fxfs = str("公募','私募")
is_yx = str("是','否")
# fxfs=str(('公募'))
# is_yx=str(('否'))
sf_syl = 'syl1'
qy = str("ALL")
yhpj = str("AA-','AA','AA+','AA(2)','AAA")
list1 = str("是','否")


def df_175_calc(data):
    x11 = 0.749999997
    x22 = 3
    x1 = 1
    x2 = 2
    df = data[data['曲线期限'] == x1]
    df['y1'] = data[data['曲线期限'] == x1]['收益率'].values
    df['y2'] = data[data['曲线期限'] == x2]['收益率'].values
    df['y11'] = data[data['曲线期限'] == x11]['收益率'].values
    df['y22'] = data[data['曲线期限'] == x22]['收益率'].values
    df['d1'] = (df['y2'] - df['y11']) / 2 / (x2 - x11)
    df['d2'] = (df['y22'] - df['y1']) / 2 / (x22 - x1)
    df['175'] = hermite_interpolation(1.75, x1, x2, df['y1'], df['y2'], df['d1'], df['d2'])
    df['曲线期限'] = 1.75
    df['收益率'] = df['175']
    return pd.concat(
        [data, df.drop(['y1', 'y2', 'y11', 'y22', 'd1', 'd2', '175'], axis=1)],
        ignore_index=True)


# 中债插值公式
def hermite_interpolation(x, x1, x2, y1, y2, d1, d2):
    h = x2 - x1
    t = (x - x1) / h
    H1 = 1 - 3 * t ** 2 + 2 * t ** 3
    H2 = 3 * t ** 2 - 2 * t ** 3
    H3 = t - 2 * t ** 2 + t ** 3
    H4 = -t ** 2 + t ** 3
    y_x = y1 * H1 + y2 * H2 + d1 * H3 + d2 * H4

    return np.round(y_x, 4)


# 定义平均的函数
def weighted_average(x):
    x = x[x['标准化收益率'] > 0]
    if sf_syl == 'syl1':
        return np.sum(x['标准化收益率'] * x['债券余额']) / np.sum(x['债券余额'])  # np.average公式在处理权重有nan的情况时容易遇到问题
    else:
        return np.average(x['标准化收益率'])


trade_dates_list = pd.read_sql(f"""SELECT DISTINCT
                                DT 
                            FROM
                                `bond`.`marketinfo_abs` 
                            WHERE
                                ths_bond_balance_bond > 0
                            ORDER BY
                                DT DESC
                            limit 3
                          """, _cursor)
step_size = 50  # 设置每次遍历的日期数量
total_rows = trade_dates_list.shape[0] 
for start_index in range(0, total_rows, step_size):
    # 计算这次循环的结束索引，注意不能超出总行数
    end_index = min(start_index + step_size, total_rows)
    batch_trade_dates = trade_dates_list[start_index:end_index]
    print(f'{start_index} - {end_index}')
    # 将 'DT' 列转换为 datetime 对象，并格式化为字符串
    batch_trade_dates['DT'] = pd.to_datetime(batch_trade_dates['DT'])
    formatted_dates = batch_trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
    # 将日期列表转换为用逗号分隔的字符串（如果需要）
    unique_dates = "','".join(formatted_dates)

# for index, row in trade_dates_list[:].iterrows():
#     trade_dates = trade_dates_list[index:index + 1]
#     print(row['DT'], datetime.datetime.today())
#     trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])
#     trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
#     unique_dates = "','".join(x for x in trade_dates)

    data_main = pd.read_sql(f"""
    SELECT A.*,B.*,目标期限,
    CASE 
        when abs分类='银行信贷资产' then '个人住房'
        when abs分类='租赁保理综合' then '对公贷款'
        when abs分类='类REITs' or abs分类='城投' or abs分类='央国企供应链' or abs分类='房地产' or abs分类='建筑供应链' or abs分类='其他' then '企业资产'
        else '消费金融'
    end as 所需曲线
    FROM
        (SELECT dt AS 日期,
                trade_code,
                ths_bond_balance_bond AS 债券余额,
                ths_evaluate_yield_cb_bond_exercise AS 行权估值,
                # ths_repay_years_cb_bond_exercise AS 行权剩余期限,
                CASE 
                    WHEN ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN ths_evaluate_modified_dur_cb_bond_exercise
                    ELSE ths_evaluate_interest_durcb_bond_exercise + ths_evaluate_spread_durcb_bond_exercise
                END AS 行权剩余期限,
                ths_cb_market_implicit_rating_bond AS 隐含评级
                FROM bond.marketinfo_abs
                WHERE dt IN ('{unique_dates}') 
                    AND ths_evaluate_yield_cb_bond_exercise>0
                    AND ths_cb_market_implicit_rating_bond IN ('AAA','AAA-','AA+','AA','AA(2)','AA-')
                    AND (ths_evaluate_modified_dur_cb_bond_exercise>0 OR ths_evaluate_interest_durcb_bond_exercise>0)
					AND ths_bond_balance_bond>0 AND ths_bond_balance_bond is not null AND ths_bond_balance_bond!=''
        )A
        LEFT JOIN
    (SELECT
        a.TRADE_CODE AS 代码1,
        a.发行方式,
        CASE
            WHEN b.担保人是否城投 = '是' or c.原始权益人是否城投='是' or d.差额支付承诺人是否城投='是' THEN '城投'
            WHEN a.底层资产类型 like '%%互联网%%' then '消金小贷'
            WHEN a.底层资产类型 like '%%信用卡%%' or a.底层资产类型 like '%%不良%%' then '银行信贷资产'
            WHEN a.底层资产类型 like '%%REITs%%' then 'REITs'
            WHEN a.底层资产类型 !='' then '租赁保理综合'
            WHEN a.abs行业分类 like '%%银行%%' or a.abs行业分类 like '%%银行%%' or d.差额支付承诺人行业 like '%%银行%%' or a.原始权益人 like '%%银行%%' or a.差额支付承诺人 like '%%银行%%' or a.担保人 like '%%银行%%' then '银行信贷资产'
            WHEN b.担保人行业 like '%%建筑%%' then '建筑供应链'
            WHEN b.担保人行业 like '%%房地产%%' then '房地产'
            WHEN b.担保人行业 like '%%金融%%' or b.担保人行业 like '%%综合%%' then '租赁保理综合'
                    WHEN d.差额支付承诺人行业 like '%%建筑%%' then '建筑供应链'
            WHEN d.差额支付承诺人行业 like '%%房地产%%' then '房地产'
            WHEN d.差额支付承诺人行业 like '%%金融%%' or d.差额支付承诺人行业 like '%%综合%%' then '租赁保理综合'
                    WHEN a.abs行业分类 like '%%建筑%%' then '建筑供应链'
                    WHEN a.abs行业分类 like '%%房地产%%' then '房地产'
                    WHEN a.abs行业分类 like '%%金融%%' or a.abs行业分类 like '%%综合%%' then '租赁保理综合'
                    WHEN a.原始权益人 like '%%租赁%%' then '租赁保理综合'
                    WHEN a.原始权益人 like '%%京东%%' then '消金小贷'
                    WHEN e.发行人是否国企 = '是' or f.差额支付承诺人是否国企 = '是' or g.担保人是否国企 = '是' then '央国企供应链'
            else '其他'
        END AS abs分类
        FROM (
                SELECT
                        TRADE_CODE,
                        ths_issue_method_bond AS 发行方式,
                        SUBSTRING_INDEX(ths_b_abs_defiguarantor_bond,',',1) as 担保人,
                        SUBSTRING_INDEX(ths_sponsor_to_original_righter_bond,';',1) as 原始权益人,
                        SUBSTRING_INDEX(ths_b_abs_defiguarantor_bond,',',1) as 差额支付承诺人,
                        SUBSTRING_INDEX(ths_abs_swi_industry_bond, ';', 1)as abs行业分类,
                        ths_basic_asset_type_detail_bond as 底层资产类型
                FROM bond.basicinfo_abs
                ) a
                LEFT JOIN (
                        SELECT DISTINCT ths_issuer_name_cn_bond as 发行人1, ths_is_city_invest_debt_yy_bond as 担保人是否城投, ths_object_the_sw_bond as 担保人行业
                        FROM bond.basicinfo_credit WHERE ths_issuer_name_cn_bond !=''
                ) b ON a.担保人 = b.发行人1
                left JOIN (
                        SELECT DISTINCT ths_issuer_name_cn_bond as 发行人2, ths_is_city_invest_debt_yy_bond as 原始权益人是否城投
                        FROM bond.basicinfo_credit WHERE ths_issuer_name_cn_bond !=''
                ) c ON a.原始权益人 = c.发行人2
        left JOIN (
                        SELECT DISTINCT ths_issuer_name_cn_bond as 发行人3, ths_is_city_invest_debt_yy_bond as 差额支付承诺人是否城投, ths_object_the_sw_bond as 差额支付承诺人行业
                        FROM bond.basicinfo_credit WHERE ths_issuer_name_cn_bond !=''
                ) d ON a.差额支付承诺人 = d.发行人3
                left JOIN (
                        SELECT 公司名称, 是否国企 as 发行人是否国企
                        FROM bond.basicinfo_issuer
                ) e ON a.原始权益人 = e.公司名称
                left JOIN (
                        SELECT 公司名称 as 公司名称1, 是否国企 as 差额支付承诺人是否国企
                        FROM bond.basicinfo_issuer
                ) f ON a.差额支付承诺人 = f.公司名称1
                left JOIN (
                        SELECT 公司名称 as 公司名称2, 是否国企 as 担保人是否国企
                        FROM bond.basicinfo_issuer
                ) g ON a.担保人 = g.公司名称2
    )B
    ON A.trade_code=B.代码1
    CROSS JOIN (
    SELECT 0.083333333 AS 目标期限
    UNION ALL
    SELECT 0.24999999899999997
    UNION ALL
    SELECT 0.49999999799999995
    UNION ALL
    SELECT 0.749999997
    UNION ALL
    SELECT 1.0
    UNION ALL
    SELECT 1.75
    UNION ALL
    SELECT 2.0
    UNION ALL
    SELECT 3.0
    UNION ALL
    SELECT 4.0
    UNION ALL
    SELECT 5.0
    UNION ALL
    SELECT 7
    UNION ALL
    SELECT 10
    UNION ALL
    SELECT 15
    UNION ALL
    SELECT 20
    UNION ALL
    SELECT 30
    ) 目标期限""", _cursor)

    # 取曲线数据
    data_curve = pd.read_sql(f"""
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 NOT LIKE '%%中债资产支持%%')
        )
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 NOT LIKE '%%中债资产支持%%')
        )
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            CASE
                WHEN classify2 LIKE '%%个人住房%%' THEN '个人住房'
                WHEN classify2 LIKE '%%对公贷款%%' THEN '对公贷款'
                WHEN classify2 LIKE '%%企业资产%%' THEN '企业资产'
                ELSE '消费金融'
            END AS 曲线名称,
            SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1, CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1) AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
        WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 NOT LIKE '%%中债资产支持%%')
    ) B ON A.trade_code1 = B.TRADE_CODE
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '个人住房' AS 曲线名称,
            'AA+' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
        WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
    ) B ON A.trade_code1 = B.TRADE_CODE
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '个人住房' AS 曲线名称,
            'AA' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
        WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
    ) B ON A.trade_code1 = B.TRADE_CODE
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN (
            SELECT trade_code
            FROM bond.basicinfo_curve
            WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
        )
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '个人住房' AS 曲线名称,
            'AA-' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
        WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
    ) B ON A.trade_code1 = B.TRADE_CODE
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '对公贷款' AS 曲线名称,
            'AAA-' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
    ) B ON A.trade_code1 = B.TRADE_CODE
    WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%对公贷款%%' AND classify2 LIKE '%%AAA%%')
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '消费金融' AS 曲线名称,
            'AAA-' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
    ) B ON A.trade_code1 = B.TRADE_CODE
    WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%消费金融%%' AND classify2 LIKE '%%AAA%%')
    UNION ALL
    SELECT A.*, B.*
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt IN ('{unique_dates}')
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt IN ('{unique_dates}')
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
            '个人住房' AS 曲线名称,
            'AAA-' AS 隐含评级1,
            classify2,
            LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1) * (
                (RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12 + (RIGHT(SEC_NAME, 1) = '年')
            ) AS 曲线期限
        FROM bond.basicinfo_curve
    ) B ON A.trade_code1 = B.TRADE_CODE
    WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%资产支持%%' AND classify2 LIKE '%%个人住房%%')
    """, _cursor)

    data_curve = df_175_calc(data_curve)

    data_curve['日期1'] = pd.to_datetime(data_curve['日期1'])
    data_main['日期'] = pd.to_datetime(data_main['日期'])

    p_yhpj_values = data_main['隐含评级'].values  # 转换为 NumPy 数组
    bond_term_values = data_main['行权剩余期限'].values

    terms1 = np.array([0,0.083333333,0.24999999899999997,0.49999999799999995,0.749999997,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])
    min_terms1 = min(terms1)
    max_terms1 = max(terms1)
    term_length1 = len(terms1)
    mask1 = np.logical_or(np.in1d(data_main['行权剩余期限'].values, terms1),
                        np.logical_or(data_main['行权剩余期限'].values < np.min(terms1),
                                        data_main['行权剩余期限'].values > np.max(terms1)))

    merge0 = data_main.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '目标期限'],
                            how='left')
    data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0.loc[merge0[merge0['收益率'] > 0].index, '收益率']
    f_df01 = data_main[mask1]
    merge01 = f_df01.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '行权剩余期限'],
                        how='left')
    data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01.loc[merge01[merge01['收益率'] > 0].index, '收益率']

    data_main.loc[data_main[~mask1].index.tolist(), 'x1_m1'] = np.max(
        np.where(bond_term_values[~mask1][:, np.newaxis] >= terms1, terms1, min_terms1), axis=1)
    data_main.loc[data_main[~mask1].index.tolist(), 'x2_m1'] = np.min(
        np.where(bond_term_values[~mask1][:, np.newaxis] <= terms1, terms1, max_terms1), axis=1)
    insert_points_x1m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x1_m1'].values[:, np.newaxis], side='left')
    insert_points_x2m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x2_m1'].values[:, np.newaxis], side='right')
    data_main.loc[data_main[~mask1].index.tolist(), 'x11_m1'] = terms1[
        np.where(insert_points_x1m1 > 0, insert_points_x1m1 - 1, 0)]
    data_main.loc[data_main[~mask1].index.tolist(), 'x22_m1'] = terms1[
        np.where(insert_points_x2m1 < term_length1, insert_points_x2m1, term_length1 - 1)]

    f_df02 = data_main[~mask1]
    merge02x1 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x1_m1'],
                            how='left')
    data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1.loc[
        merge02x1[merge02x1['收益率'] > 0].index, '收益率']
    merge02x2 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x2_m1'],
                            how='left')
    data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2.loc[
        merge02x2[merge02x2['收益率'] > 0].index, '收益率']
    merge02x11 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x11_m1'],
                            how='left')
    data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11.loc[
        merge02x11[merge02x11['收益率'] > 0].index, '收益率']
    merge02x22 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x22_m1'],
                            how='left')
    data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22.loc[
        merge02x22[merge02x22['收益率'] > 0].index, '收益率']
    data_main.loc[data_main[~mask1].index.tolist(), 'd1_m1'] = (data_main.loc[~mask1, 'yx2_m1'] - data_main.loc[
        ~mask1, 'yx11_m1']) / (2 * (data_main.loc[~mask1, 'x2_m1'] - data_main.loc[~mask1, 'x11_m1']))
    data_main.loc[data_main[~mask1].index.tolist(), 'd2_m1'] = (data_main.loc[~mask1, 'yx22_m1'] - data_main.loc[
        ~mask1, 'yx1_m1']) / (2 * (data_main.loc[~mask1, 'x22_m1'] - data_main.loc[~mask1, 'x1_m1']))
    data_main.loc[f_df02.index, '原期限收益率'] = hermite_interpolation(data_main.loc[~mask1, '行权剩余期限'],
                                                                data_main.loc[~mask1, 'x1_m1'],
                                                                data_main.loc[~mask1, 'x2_m1'],
                                                                data_main.loc[~mask1, 'yx1_m1'],
                                                                data_main.loc[~mask1, 'yx2_m1'],
                                                                data_main.loc[~mask1, 'd1_m1'],
                                                                data_main.loc[~mask1, 'd2_m1'])

    data_main['标准化收益率'] = (
            data_main['行权估值'] + (data_main['目标期限收益率'] - data_main['原期限收益率'])).fillna(0)

    data_main['债券余额'] = pd.to_numeric(data_main['债券余额'], errors='coerce')
    data_main = data_main[['日期', 'trade_code', '债券余额', '隐含评级', '标准化收益率', '目标期限']].rename(columns={
        '日期': 'DT',
        'trade_code': 'TRADE_CODE',
        '债券余额': 'balance',
        '隐含评级': 'imrating_calc',
        '标准化收益率': 'stdyield'
    })

    # 按目标期限拆分 DataFrame
    # target_terms = [0.49999999799999995, 1.0, 1.75, 2.0, 3.0, 4.0, 5.0]
    target_terms = [0.083333333, 0.24999999899999997,0.49999999799999995, 0.749999997,1.0, 1.75, 2.0, 3.0, 4.0, 5.0,7,10,15,20,30]

    data_frames = []
    for term in target_terms:
        term_str = str(term)  # 将目标期限转换为字符串
        df_term = data_main[data_main['目标期限'] == term].copy()
        df_term = df_term.drop(columns=['目标期限'])
        data_frames.append(df_term)

    # 定义表格名称
    table_names = ['bond.hzcurve_abs_0083', 'bond.hzcurve_abs_025', 'bond.hzcurve_abs_05','bond.hzcurve_abs_075', 'bond.hzcurve_abs_1', 'bond.hzcurve_credit_175','bond.hzcurve_abs_2','bond.hzcurve_abs_3','bond.hzcurve_abs_4','bond.hzcurve_abs_5','bond.hzcurve_abs_7','bond.hzcurve_abs_10','bond.hzcurve_abs_15','bond.hzcurve_abs_20','bond.hzcurve_abs_30']

    # 定义表格字段类型
    column_types = {'DT': Date, 'TRADE_CODE': VARCHAR(15), 'balance': DECIMAL(5, 2), 'imrating_calc': VARCHAR(5),
                    'stdyield': DECIMAL(5, 3)}

    # 写入数据库
    for table_name, df in zip(table_names, data_frames):
        insert_database(
            df[(df['stdyield'] != 0) & (df['stdyield'] != '0') & (df['stdyield'] != '') & (df['stdyield'].notna())],
            table_name, ['TRADE_CODE', 'DT'])
    print('完成abs1')

########################## 批量计算curve_finance

import numpy as np
import pandas as pd
from pymysql import cursors
from sqlalchemy import VARCHAR, Date, DECIMAL

# dt = _setting['dt']
# target_term = float(_setting['target_term'])
# sf_db = _setting['sf_db']
# sf_lc = _setting['sf_lc']
# sf_syl = _setting['sf_syl']
# qy = "','".join(x for x in ['-'.join(filter(None, i)) for i in _setting['qy']])
# name_com=_setting['name_com']
# fxfs="','".join(_setting['fxfs'])
# is_yx="','".join(_setting['is_yx'])
# yhpj="','".join(_setting['yhpj'])
# list1 = "','".join(_setting['list1'])

# dt='2023-12-01'
# target_term = 2.0
sf_db = 'db1'
sf_lc = 'lc1'
sf_syl = 'syl1'
# sf_cz = 'cz1'
# sf_xz = 'xz3'
name_com = '无'
fxfs = str("公募','私募")
is_yx = str("是','否")
# fxfs=str(('公募'))
# is_yx=str(('否'))
sf_syl = 'syl1'
qy = str("ALL")
yhpj = str("AA-','AA','AA+','AA(2)','AAA")
list1 = str("是','否")


# 中债插值公式
def hermite_interpolation(x, x1, x2, y1, y2, d1, d2):
    h = x2 - x1
    t = (x - x1) / h
    H1 = 1 - 3 * t ** 2 + 2 * t ** 3
    H2 = 3 * t ** 2 - 2 * t ** 3
    H3 = t - 2 * t ** 2 + t ** 3
    H4 = -t ** 2 + t ** 3
    y_x = y1 * H1 + y2 * H2 + d1 * H3 + d2 * H4

    return np.round(y_x, 4)


# 定义平均的函数
def weighted_average(x):
    x = x[x['标准化收益率'] > 0]
    if sf_syl == 'syl1':
        return np.sum(x['标准化收益率'] * x['债券余额']) / np.sum(x['债券余额'])  # np.average公式在处理权重有nan的情况时容易遇到问题
    else:
        return np.average(x['标准化收益率'])

step_size = 50  # 设置每次遍历的日期数量
total_rows = trade_dates_list.shape[0] 
for start_index in range(0, total_rows, step_size):
    # 计算这次循环的结束索引，注意不能超出总行数
    end_index = min(start_index + step_size, total_rows)
    batch_trade_dates = trade_dates_list[start_index:end_index]
    print(f'{start_index} - {end_index}')
    # 将 'DT' 列转换为 datetime 对象，并格式化为字符串
    batch_trade_dates['DT'] = pd.to_datetime(batch_trade_dates['DT'])
    formatted_dates = batch_trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
    # 将日期列表转换为用逗号分隔的字符串（如果需要）
    unique_dates = "','".join(formatted_dates)
# for index, row in trade_dates_list[:].iterrows():
#     trade_dates = trade_dates_list[index:index + 1]
#     print(row['DT'], datetime.datetime.today())
#     trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])
#     trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
#     unique_dates = "','".join(x for x in trade_dates)
    data_main = pd.read_sql(f"""
    SELECT A.*,B.*,'其他' AS 所需曲线,
        目标期限
        FROM
        (SELECT dt AS 日期,
        trade_code,
        ths_bond_balance_bond AS 债券余额,
        ths_evaluate_yield_cb_bond_exercise AS 行权估值,
        # ths_repay_years_cb_bond_exercise AS 行权剩余期限,
        CASE 
            WHEN ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN ths_evaluate_modified_dur_cb_bond_exercise
            ELSE ths_evaluate_interest_durcb_bond_exercise + ths_evaluate_spread_durcb_bond_exercise
        END AS 行权剩余期限,
        ths_cb_market_implicit_rating_bond AS 隐含评级
        FROM 
        bond.marketinfo_finance
        WHERE dt IN ('{unique_dates}') 
            AND trade_code IN (SELECT DISTINCT trade_code FROM `bond`.`basicinfo_finance` 
                            WHERE ths_ths_bond_third_type_bond = '其他非银金融机构债')
            AND ths_evaluate_yield_cb_bond_exercise>0
            AND ths_cb_market_implicit_rating_bond IN ('AAA','AAA-','AA+','AA','AA-')
            AND (ths_evaluate_modified_dur_cb_bond_exercise>0 OR ths_evaluate_interest_durcb_bond_exercise>0)
			AND ths_bond_balance_bond>0 AND ths_bond_balance_bond is not null AND ths_bond_balance_bond!=''
        )A LEFT JOIN
            (SELECT 
            trade_code AS 代码1,
            ths_issue_method_bond AS 发行方式,
            ths_issuer_name_cn_bond AS 发行人名称,
            ths_is_perpetual_bond AS 是否永续,
            ths_is_subordinated_debt_bond AS 是否次级,
            ths_ths_bond_third_type_bond AS 债券类型,
            ths_org_type_bond AS 机构类型
            FROM bond.basicinfo_finance
        )B     
        ON A.trade_code=B.代码1
        CROSS JOIN (
        SELECT 0.083333333 AS 目标期限
        UNION ALL
        SELECT 0.24999999899999997
        UNION ALL
        SELECT 0.49999999799999995
        UNION ALL
        SELECT 0.749999997
        UNION ALL
        SELECT 1.0
        UNION ALL
        SELECT 1.75
        UNION ALL
        SELECT 2.0
        UNION ALL
        SELECT 3.0
        UNION ALL
        SELECT 4.0
        UNION ALL
        SELECT 5.0
        UNION ALL
        SELECT 7
        UNION ALL
        SELECT 10
        UNION ALL
        SELECT 15
        UNION ALL
        SELECT 20
        UNION ALL
        SELECT 30
    ) 目标期限
    WHERE 债券类型 = '其他非银金融机构债' AND 机构类型 NOT LIKE '%%银行%%' AND 机构类型 NOT LIKE '%%证券公司%%' AND 机构类型 NOT LIKE '%%保险%%'

    UNION ALL
        SELECT A.*,B.*,
        CASE
            WHEN 机构类型 LIKE '%%银行%%' THEN '银行'
            WHEN 机构类型 LIKE '%%证券公司%%' THEN '证券'
            WHEN 机构类型 LIKE '%%保险%%' THEN '保险'
        END AS 所需曲线,
        目标期限
        FROM
        (SELECT dt AS 日期,
        trade_code,
        ths_bond_balance_bond AS 债券余额,
        ths_evaluate_yield_cb_bond_exercise AS 行权估值,
        # ths_repay_years_cb_bond_exercise AS 行权剩余期限,
        CASE 
            WHEN ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN ths_evaluate_modified_dur_cb_bond_exercise
            ELSE ths_evaluate_interest_durcb_bond_exercise + ths_evaluate_spread_durcb_bond_exercise
        END AS 行权剩余期限,
        ths_cb_market_implicit_rating_bond AS 隐含评级
        FROM 
        bond.marketinfo_finance
        WHERE dt IN ('{unique_dates}') 
            AND ths_evaluate_yield_cb_bond_exercise>0
            AND ths_cb_market_implicit_rating_bond IN ('AAA','AAA-','AA+','AA','AA-')
            AND (ths_evaluate_modified_dur_cb_bond_exercise>0 OR ths_evaluate_interest_durcb_bond_exercise>0)
			AND ths_bond_balance_bond>0 AND ths_bond_balance_bond is not null AND ths_bond_balance_bond!=''
        )A LEFT JOIN
            (SELECT 
            trade_code AS 代码1,
            ths_issue_method_bond AS 发行方式,
            ths_issuer_name_cn_bond AS 发行人名称,
            ths_is_perpetual_bond AS 是否永续,
            ths_is_subordinated_debt_bond AS 是否次级,
            ths_ths_bond_third_type_bond AS 债券类型,
            ths_org_type_bond AS 机构类型
            FROM bond.basicinfo_finance
        )B ON A.trade_code=B.代码1
        CROSS JOIN (
        SELECT 0.083333333 AS 目标期限
        UNION ALL
        SELECT 0.24999999899999997
        UNION ALL
        SELECT 0.49999999799999995
        UNION ALL
        SELECT 0.749999997
        UNION ALL
        SELECT 1.0
        UNION ALL
        SELECT 1.75
        UNION ALL
        SELECT 2.0
        UNION ALL
        SELECT 3.0
        UNION ALL
        SELECT 4.0
        UNION ALL
        SELECT 5.0
        UNION ALL
        SELECT 7
        UNION ALL
        SELECT 10
        UNION ALL
        SELECT 15
        UNION ALL
        SELECT 20
        UNION ALL
        SELECT 30
    ) 目标期限
    WHERE 机构类型 LIKE '%%银行%%' OR 机构类型 LIKE '%%证券公司%%' OR 机构类型 LIKE '%%保险%%'
    """, _cursor)

    # 取曲线数据
    data_curve = pd.read_sql(f"""
        SELECT A.*,B.*,'其他' AS 曲线名称 FROM
        (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%非存款类金融机构%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%非存款类金融机构%%')))A LEFT JOIN
        (SELECT TRADE_CODE, 
        '否' AS 是否永续1,
        CASE WHEN classify2 LIKE '%%二级资本%%' THEN '是' ELSE '否' END AS 是否次级1,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    UNION ALL
        SELECT A.*,B.*,'其他' AS 曲线名称 FROM
        (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%非存款类金融机构%%' AND classify2 LIKE '%%AAA-%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}')
        AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%非存款类金融机构%%' AND classify2 LIKE '%%AAA-%%')))A LEFT JOIN
        (SELECT TRADE_CODE, 
        '否' AS 是否永续1,
        CASE WHEN classify2 LIKE '%%二级资本%%' THEN '是' ELSE '否' END AS 是否次级1,
        'AAA' AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    UNION ALL
        SELECT A.*,B.*,'银行' AS 曲线名称 FROM
        (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%商业银行%%' AND classify2 NOT LIKE '%%次级%%' AND classify2 NOT LIKE '%%存单%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%商业银行%%' AND classify2 NOT LIKE '%%次级%%' AND classify2 NOT LIKE '%%存单%%')))A LEFT JOIN
        (SELECT TRADE_CODE, 
        CASE WHEN classify2 LIKE '%%无固定期限%%' THEN '是' ELSE '否' END AS 是否永续1,
        CASE WHEN classify2 LIKE '%%二级资本%%' THEN '是' ELSE '否' END AS 是否次级1,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    UNION ALL
        SELECT A.*,B.*,'证券' AS 曲线名称 FROM
        (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
            (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%证券公司%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
            (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%证券公司%%')))A LEFT JOIN
        (SELECT TRADE_CODE,
        '否' AS 是否永续1,
        CASE WHEN classify2 LIKE '%%次级%%' THEN '是' ELSE '否' END AS 是否次级1,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    UNION ALL
        SELECT A.*,B.*,'证券' AS 曲线名称 FROM
        (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
            (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%证券公司%%' AND classify2 LIKE '%%(AA)%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
            (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%证券公司%%' AND classify2 LIKE '%%(AA)%%')))A LEFT JOIN
        (SELECT TRADE_CODE,
        '否' AS 是否永续1,
        CASE WHEN classify2 LIKE '%%次级%%' THEN '是' ELSE '否' END AS 是否次级1,
        'AA-' AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    UNION ALL
        SELECT A.*,B.*,'保险' AS 曲线名称 FROM
            (SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%保险%%'))
        UNION
            SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率 from bond.marketinfo_curve_history_adjusted WHERE dt IN ('{unique_dates}') AND TRADE_CODE IN
        (SELECT trade_code FROM bond.basicinfo_curve WHERE (classify2 LIKE '%%中债%%' AND classify2 LIKE '%%保险%%')))A LEFT JOIN
        (SELECT TRADE_CODE,
        '否' AS 是否永续1,
        '否' AS 是否次级1,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365 + (RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve)B on A.trade_code1=B.TRADE_CODE
    """, _cursor)

    data_curve = df_175_calc(data_curve)

    data_curve['日期1'] = pd.to_datetime(data_curve['日期1'])
    data_main['日期'] = pd.to_datetime(data_main['日期'])

    p_yhpj_values = data_main['隐含评级'].values  # 转换为 NumPy 数组
    bond_term_values = data_main['行权剩余期限'].values

    terms1 = np.array([0,0.083333333,0.24999999899999997,0.49999999799999995,0.749999997,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])
    min_terms1 = min(terms1)
    max_terms1 = max(terms1)
    term_length1 = len(terms1)
    mask1 = np.logical_or(np.in1d(data_main['行权剩余期限'].values, terms1),
                        np.logical_or(data_main['行权剩余期限'].values < np.min(terms1),
                                        data_main['行权剩余期限'].values > np.max(terms1)))

    f_df01 = data_main[mask1]

    f_c1 = data_curve[(data_curve['是否永续1'] == '否') & (data_curve['是否次级1'] == '否')]
    merge0 = data_main.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '目标期限'], how='left')
    data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0.loc[merge0[merge0['收益率'] > 0].index, '收益率']
    merge01 = f_df01.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '行权剩余期限'], how='left')
    data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01.loc[merge01[merge01['收益率'] > 0].index, '收益率']
    data_main.loc[data_main[~mask1].index.tolist(), 'x1_m1'] = np.max(
        np.where(bond_term_values[~mask1][:, np.newaxis] >= terms1, terms1, min_terms1), axis=1)
    data_main.loc[data_main[~mask1].index.tolist(), 'x2_m1'] = np.min(
        np.where(bond_term_values[~mask1][:, np.newaxis] <= terms1, terms1, max_terms1), axis=1)
    insert_points_x1m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x1_m1'].values[:, np.newaxis], side='left')
    insert_points_x2m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x2_m1'].values[:, np.newaxis], side='right')
    data_main.loc[data_main[~mask1].index.tolist(), 'x11_m1'] = terms1[
        np.where(insert_points_x1m1 > 0, insert_points_x1m1 - 1, 0)]
    data_main.loc[data_main[~mask1].index.tolist(), 'x22_m1'] = terms1[
        np.where(insert_points_x2m1 < term_length1, insert_points_x2m1, term_length1 - 1)]

    f_df02 = data_main[~mask1]
    merge02x1 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x1_m1'],
                            how='left')
    data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1.loc[
        merge02x1[merge02x1['收益率'] > 0].index, '收益率']
    merge02x2 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x2_m1'],
                            how='left')
    data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2.loc[
        merge02x2[merge02x2['收益率'] > 0].index, '收益率']
    merge02x11 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x11_m1'],
                            how='left')
    data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11.loc[
        merge02x11[merge02x11['收益率'] > 0].index, '收益率']
    merge02x22 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x22_m1'],
                            how='left')
    data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22.loc[
        merge02x22[merge02x22['收益率'] > 0].index, '收益率']

    f_df_yx = data_main[(data_main['是否次级'] == '是')]
    f_df01 = data_main[mask1 & (data_main['是否次级'] == '是')]
    f_c1 = data_curve[(data_curve['是否次级1'] == '是')]
    merge0 = f_df01.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '目标期限'], how='left')
    data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0.loc[merge0[merge0['收益率'] > 0].index, '收益率']
    merge01 = f_df01.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '行权剩余期限'], how='left')
    data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01.loc[merge01[merge01['收益率'] > 0].index, '收益率']

    f_df02 = data_main[(~mask1) & (data_main['是否次级'] == '是')]
    merge02x1 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x1_m1'],
                            how='left')
    data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1.loc[
        merge02x1[merge02x1['收益率'] > 0].index, '收益率']
    merge02x2 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x2_m1'],
                            how='left')
    data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2.loc[
        merge02x2[merge02x2['收益率'] > 0].index, '收益率']
    merge02x11 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x11_m1'],
                            how='left')
    data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11.loc[
        merge02x11[merge02x11['收益率'] > 0].index, '收益率']
    merge02x22 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x22_m1'],
                            how='left')
    data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22.loc[
        merge02x22[merge02x22['收益率'] > 0].index, '收益率']

    f_df_yx = data_main[data_main['是否永续'] == '是']
    f_df01 = data_main[mask1 & (data_main['是否永续'] == '是')]
    f_c1 = data_curve[(data_curve['是否永续1'] == '是')]
    merge0 = f_df01.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '目标期限'], how='left')
    data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0.loc[merge0[merge0['收益率'] > 0].index, '收益率']
    merge01 = f_df01.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', '行权剩余期限'], how='left')
    data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01.loc[merge01[merge01['收益率'] > 0].index, '收益率']

    f_df02 = data_main[(~mask1) & (data_main['是否永续'] == '是')]
    merge02x1 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x1_m1'],
                            how='left')
    data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1.loc[
        merge02x1[merge02x1['收益率'] > 0].index, '收益率']
    merge02x2 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x2_m1'],
                            how='left')
    data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2.loc[
        merge02x2[merge02x2['收益率'] > 0].index, '收益率']
    merge02x11 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x11_m1'],
                            how='left')
    data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11.loc[
        merge02x11[merge02x11['收益率'] > 0].index, '收益率']
    merge02x22 = f_df02.join(f_c1.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限']), on=['日期', '所需曲线', '隐含评级', 'x22_m1'],
                            how='left')
    data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22.loc[
        merge02x22[merge02x22['收益率'] > 0].index, '收益率']

    f_df01 = data_main[mask1]
    merge0 = data_main.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                            on=['日期', '所需曲线', '隐含评级', '目标期限', '是否永续', '是否次级'], how='left')
    data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0.loc[merge0[merge0['收益率'] > 0].index, '收益率']
    merge01 = f_df01.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                        on=['日期', '所需曲线', '隐含评级', '行权剩余期限', '是否永续', '是否次级'], how='left')
    data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01.loc[merge01[merge01['收益率'] > 0].index, '收益率']
    f_df02 = data_main[~mask1]
    merge02x1 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                            on=['日期', '所需曲线', '隐含评级', 'x1_m1', '是否永续', '是否次级'], how='left')
    data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1.loc[
        merge02x1[merge02x1['收益率'] > 0].index, '收益率']
    merge02x2 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                            on=['日期', '所需曲线', '隐含评级', 'x2_m1', '是否永续', '是否次级'], how='left')
    data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2.loc[
        merge02x2[merge02x2['收益率'] > 0].index, '收益率']
    merge02x11 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                            on=['日期', '所需曲线', '隐含评级', 'x11_m1', '是否永续', '是否次级'], how='left')
    data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11.loc[
        merge02x11[merge02x11['收益率'] > 0].index, '收益率']
    merge02x22 = f_df02.join(data_curve.set_index(['日期1', '曲线名称', '隐含评级1', '曲线期限', '是否永续1', '是否次级1']),
                            on=['日期', '所需曲线', '隐含评级', 'x22_m1', '是否永续', '是否次级'], how='left')
    data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22.loc[
        merge02x22[merge02x22['收益率'] > 0].index, '收益率']

    data_main.loc[f_df02.index, 'd1_m1'] = (data_main.loc[f_df02.index, 'yx2_m1'] - data_main.loc[
        f_df02.index, 'yx11_m1']) / (2 * (data_main.loc[f_df02.index, 'x2_m1'] - data_main.loc[f_df02.index, 'x11_m1']))
    data_main.loc[f_df02.index, 'd2_m1'] = (data_main.loc[f_df02.index, 'yx22_m1'] - data_main.loc[
        f_df02.index, 'yx1_m1']) / (2 * (data_main.loc[f_df02.index, 'x22_m1'] - data_main.loc[f_df02.index, 'x1_m1']))
    data_main.loc[f_df02.index, '原期限收益率'] = hermite_interpolation(data_main.loc[f_df02.index, '行权剩余期限'],
                                                                data_main.loc[f_df02.index, 'x1_m1'],
                                                                data_main.loc[f_df02.index, 'x2_m1'],
                                                                data_main.loc[f_df02.index, 'yx1_m1'],
                                                                data_main.loc[f_df02.index, 'yx2_m1'],
                                                                data_main.loc[f_df02.index, 'd1_m1'],
                                                                data_main.loc[f_df02.index, 'd2_m1'])
    data_main['标准化收益率'] = (
            data_main['行权估值'] + (data_main['目标期限收益率'] - data_main['原期限收益率'])).fillna(0)

    data_main['债券余额'] = pd.to_numeric(data_main['债券余额'], errors='coerce')

    data_main = data_main[['日期', 'trade_code', '债券余额', '隐含评级', '标准化收益率', '目标期限']].rename(columns={
        '日期': 'DT',
        'trade_code': 'TRADE_CODE',
        '债券余额': 'balance',
        '隐含评级': 'imrating_calc',
        '标准化收益率': 'stdyield'
    })
    # 按目标期限拆分 DataFrame
    # target_terms = [0.49999999799999995, 1.0, 1.75, 2.0, 3.0, 4.0, 5.0]
    target_terms = [0.083333333, 0.24999999899999997,0.49999999799999995, 0.749999997,1.0, 1.75, 2.0, 3.0, 4.0, 5.0,7,10,15,20,30]

    data_frames = []
    for term in target_terms:
        term_str = str(term)  # 将目标期限转换为字符串
        df_term = data_main[data_main['目标期限'] == term].copy()
        df_term = df_term.drop(columns=['目标期限'])
        data_frames.append(df_term)

    # 定义表格名称
    # table_names = ['bond.hzcurve_finance_05', 'bond.hzcurve_finance_1', 'bond.hzcurve_finance_175',
    #                'bond.hzcurve_finance_2', 'bond.hzcurve_finance_3', 'bond.hzcurve_finance_4', 'bond.hzcurve_finance_5']

    table_names = ['bond.hzcurve_finance_0083', 'bond.hzcurve_finance_025', 'bond.hzcurve_finance_05','bond.hzcurve_finance_075', 'bond.hzcurve_finance_1', 'bond.hzcurve_finance_175','bond.hzcurve_finance_2','bond.hzcurve_finance_3','bond.hzcurve_finance_4','bond.hzcurve_finance_5','bond.hzcurve_finance_7','bond.hzcurve_finance_10','bond.hzcurve_finance_15','bond.hzcurve_finance_20','bond.hzcurve_finance_30']

    # 定义表格字段类型
    column_types = {'DT': Date, 'TRADE_CODE': VARCHAR(15), 'balance': DECIMAL(5, 2), 'imrating_calc': VARCHAR(5),
                    'stdyield': DECIMAL(5, 3)}

    # 写入数据库
    for table_name, df in zip(table_names, data_frames):
        insert_database(
            df[(df['stdyield'] != 0) & (df['stdyield'] != '0') & (df['stdyield'] != '') & (df['stdyield'].notna())],
            table_name, ['TRADE_CODE', 'DT'])

from datetime import datetime, date, timedelta, time
import numpy as np
import pandas as pd
import datetime
import os
import warnings
import pymysql
from sqlalchemy import create_engine
import time
import sys
from pymysql import cursors
import requests
import json

print(datetime.datetime.today())

target_term = 2.0
sf_db = 'db1'
sf_lc = 'lc1'
sf_syl = 'syl1'
# sf_cz = 'cz1'
# sf_xz = 'xz3'
name_com = '无'
fxfs = str("公募','私募")
is_yx = str("是','否")
# fxfs=str(('公募'))
# is_yx=str(('否'))
sf_syl = 'syl1'
qy = str("ALL")
yhpj = str("AA-','AA','AA+','AA(2)','AAA")
list1 = str("是','否")


# 中债插值公式
def hermite_interpolation(x, x1, x2, y1, y2, d1, d2):
    h = x2 - x1
    t = (x - x1) / h
    H1 = 1 - 3 * t ** 2 + 2 * t ** 3
    H2 = 3 * t ** 2 - 2 * t ** 3
    H3 = t - 2 * t ** 2 + t ** 3
    H4 = -t ** 2 + t ** 3
    y_x = y1 * H1 + y2 * H2 + d1 * H3 + d2 * H4

    return np.round(y_x, 4)


# 定义平均的函数
def weighted_average(x):
    x = x[x['标准化收益率'] > 0]
    if sf_syl == 'syl1':
        return np.sum(x['标准化收益率'] * x['债券余额']) / np.sum(x['债券余额'])  # np.average公式在处理权重有nan的情况时容易遇到问题
    else:
        return np.average(x['标准化收益率'])

step_size = 50  # 设置每次遍历的日期数量
total_rows = trade_dates_list.shape[0] 
for start_index in range(0, total_rows, step_size):
    # 计算这次循环的结束索引，注意不能超出总行数
    end_index = min(start_index + step_size, total_rows)
    batch_trade_dates = trade_dates_list[start_index:end_index]
    print(f'{start_index} - {end_index}')
    # 将 'DT' 列转换为 datetime 对象，并格式化为字符串
    batch_trade_dates['DT'] = pd.to_datetime(batch_trade_dates['DT'])
    formatted_dates = batch_trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
    # 将日期列表转换为用逗号分隔的字符串（如果需要）
    unique_dates = "','".join(formatted_dates)
# for index, row in trade_dates_list[:].iterrows():
#     trade_dates = trade_dates_list[index:index + 1]
#     print(row['DT'], datetime.datetime.today())
#     trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])
#     trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
#     unique_dates = "','".join(x for x in trade_dates)

    data_main = pd.read_sql(f"""SELECT A.*, B.*,目标期限
    FROM (
        SELECT
            dt AS 日期,
            trade_code,
            ths_bond_balance_bond AS 债券余额,
            ths_evaluate_yield_cb_bond_exercise AS 中债行权估值,
            # ths_repay_years_cb_bond_exercise AS 中债行权剩余期限,
            CASE 
                WHEN ths_evaluate_modified_dur_cb_bond_exercise > 0 THEN ths_evaluate_modified_dur_cb_bond_exercise
                ELSE ths_evaluate_interest_durcb_bond_exercise + ths_evaluate_spread_durcb_bond_exercise
            END AS 中债行权剩余期限,
            ths_cb_market_implicit_rating_bond AS 隐含评级
        FROM
            bond.marketinfo_credit
        WHERE
            dt IN ('{unique_dates}')
            AND ths_evaluate_yield_cb_bond_exercise > 0
            AND ths_cb_market_implicit_rating_bond IN ('AAA','AAA-','AA+','AA','AA(2)','AA-')
            AND (ths_evaluate_modified_dur_cb_bond_exercise>0 OR ths_evaluate_interest_durcb_bond_exercise>0)
			AND ths_bond_balance_bond>0 AND ths_bond_balance_bond is not null AND ths_bond_balance_bond!=''
    ) A
    LEFT JOIN (
        SELECT
            trade_code AS 代码1,
            ths_issue_method_bond AS 发行方式,
            ths_is_perpetual_bond AS 是否永续,
            ths_is_subordinated_debt_bond AS 是否次级,
            ths_urban_platform_area_bond AS 所属区域,
            ths_is_city_invest_debt_yy_bond AS 是否城投,
            ths_object_the_sw_bond AS 行业分类
        FROM
            bond.basicinfo_credit
    ) B ON A.trade_code = B.代码1
        CROSS JOIN (
        SELECT 0.083333333 AS 目标期限
        UNION ALL
        SELECT 0.24999999899999997
        UNION ALL
        SELECT 0.49999999799999995
        UNION ALL
        SELECT 0.749999997
        UNION ALL
        SELECT 1.0
        UNION ALL
        SELECT 1.75
        UNION ALL
        SELECT 2.0
        UNION ALL
        SELECT 3.0
        UNION ALL
        SELECT 4.0
        UNION ALL
        SELECT 5.0
        UNION ALL
        SELECT 7
        UNION ALL
        SELECT 10
        UNION ALL
        SELECT 15
        UNION ALL
        SELECT 20
        UNION ALL
        SELECT 30
    ) 目标期限""", _cursor)
    # CROSS JOIN (
    #     SELECT 0.49999999799999995 AS 目标期限
    #     UNION ALL
    #     SELECT 1.0
    #     UNION ALL
    #     SELECT 1.75
    #     UNION ALL
    #     SELECT 2.0
    #     UNION ALL
    #     SELECT 3.0
    #     UNION ALL
    #     SELECT 4.0
    #     UNION ALL
    #     SELECT 5.0
    # ) 目标期限""", _cursor)

    []

    # 取曲线数据
    data_curve = pd.read_sql(f"""
    SELECT A.*, B.*,'是' AS 是否城投1 
    FROM (
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve
        WHERE dt in ('{unique_dates}')
            AND TRADE_CODE IN
        (
                SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND classify2 LIKE '%%城投债%%')
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        FROM bond.marketinfo_curve_history_adjusted
        WHERE dt in ('{unique_dates}')
            AND TRADE_CODE IN
        (
                SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND classify2 LIKE '%%城投债%%')
    ) A
    LEFT JOIN (
        SELECT TRADE_CODE, 
        CASE 
            WHEN classify2 LIKE '%%非公开%%' THEN '私募' 
            ELSE '公募' 
        END AS 发行方式1,
        CASE 
            WHEN classify2 LIKE '%%可续期%%' THEN '是' 
            ELSE '否' 
        END AS 是否永续1,
        '否' AS 是否次级1,
        SUBSTRING(
            REPLACE(classify2, '＋', '+'), 
            LOCATE('(', REPLACE(classify2, '＋', '+')) + 1,
            CHAR_LENGTH(classify2) - LOCATE('(', REPLACE(classify2, '＋', '+')) - 1
        ) AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365+(RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限
        FROM bond.basicinfo_curve
    ) B ON A.trade_code1 = B.TRADE_CODE

    UNION

    SELECT A.*,B.*,'否' AS 是否城投1
    FROM(
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        from bond.marketinfo_curve 
        WHERE dt IN ('{unique_dates}')
            AND TRADE_CODE IN
        (
                SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND (classify2 LIKE '%%产业%%' or classify2 LIKE '%%中短期%%'))
        UNION
        SELECT DT AS 日期1, trade_code AS trade_code1, CLOSE AS 收益率
        from bond.marketinfo_curve_history_adjusted 
        WHERE dt IN ('{unique_dates}')
            AND TRADE_CODE IN
        (
                SELECT trade_code FROM bond.basicinfo_curve WHERE classify2 LIKE '%%中债%%' AND (classify2 LIKE '%%产业%%' or classify2 LIKE '%%中短期%%'))
        )A
        LEFT JOIN(
            SELECT TRADE_CODE, 
            CASE WHEN classify2 LIKE '%%非公开%%' THEN '私募' ELSE '公募' END AS 发行方式1,
            CASE WHEN classify2 LIKE '%%可续期%%' THEN '是' ELSE '否' END AS 是否永续1,
            CASE WHEN classify2 LIKE '%%次级可续期%%' THEN '是' ELSE '否' END AS 是否次级1,
        SUBSTRING(REPLACE(classify2, '＋', '+'), LOCATE('(', REPLACE(classify2, '＋', '+'))+1,CHAR_LENGTH(classify2)-LOCATE('(', REPLACE(classify2, '＋', '+'))-1)
        AS 隐含评级1,
        LEFT(SUBSTRING_INDEX(SEC_NAME, ':', -1), CHAR_LENGTH(SUBSTRING_INDEX(SEC_NAME, ':', -1)) - 1)*((RIGHT(SEC_NAME, 1) = '天') / 365+(RIGHT(SEC_NAME, 1) = '月') / 12+(RIGHT(SEC_NAME, 1) = '年')) AS 曲线期限 from bond.basicinfo_curve
    )B on A.trade_code1=B.TRADE_CODE

    """, _cursor)

    data_curve = df_175_calc(data_curve)

    data_main.loc[(data_main['隐含评级'] == 'AA(2)') & (data_main['是否城投'] == '否'), '是否城投'] = '是'
    data_main.loc[(data_main['隐含评级'] == 'AAA-') & (data_main['是否城投'] == '是'), '是否城投'] = '否'

    data_curve['日期1'] = pd.to_datetime(data_curve['日期1'])
    data_main['日期'] = pd.to_datetime(data_main['日期'])

    p_yhpj_values = data_main['隐含评级'].values  # 转换为 NumPy 数组
    p_sm_values = data_main['发行方式'].values
    p_yx_values = data_main['是否永续'].values
    bond_term_values = data_main['中债行权剩余期限'].values

    terms1 = np.array([0,0.083333333,0.24999999899999997,0.49999999799999995,0.749999997,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30])
    min_terms1 = min(terms1)
    max_terms1 = max(terms1)
    term_length1 = len(terms1)
    mask1 = np.logical_or(np.in1d(data_main['中债行权剩余期限'].values, terms1),
                          np.logical_or(data_main['中债行权剩余期限'].values < np.min(terms1),
                                        data_main['中债行权剩余期限'].values > np.max(terms1)))

    # 公募都用公募否否，私募都用私募否否，永续都用永续，再有细分匹配

    f_df1 = data_main[data_main['发行方式'] == '公募']
    f_df2 = data_main[data_main['发行方式'] == '私募']
    f_df3 = data_main[data_main['是否永续'] == '是']

    f_df11 = data_main[mask1 & (data_main['发行方式'] == '公募')]
    f_df21 = data_main[mask1 & (data_main['发行方式'] == '私募')]
    f_df31 = data_main[mask1 & (data_main['是否永续'] == '是')]
    f_df01 = data_main[mask1]

    f_c1 = data_curve[(data_curve['发行方式1'] == '公募') & (data_curve['是否永续1'] == '否') & (data_curve['是否次级1'] == '否')]
    f_c2 = data_curve[(data_curve['发行方式1'] == '私募') & (data_curve['是否永续1'] == '否') & (data_curve['是否次级1'] == '否')]
    f_c3 = data_curve[(data_curve['发行方式1'] == '公募') & (data_curve['是否永续1'] == '是') & (data_curve['是否次级1'] == '否')]

    merge1 = f_df1.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge2 = f_df2.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge3 = f_df3.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge0 = data_main.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                            on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', '目标期限'], how='left')
    
    if not merge1[merge1['收益率'] > 0].empty:
        data_main.loc[merge1[merge1['收益率'] > 0].index, '目标期限收益率'] = merge1['收益率']
    if not merge2[merge2['收益率'] > 0].empty:
        data_main.loc[merge2[merge2['收益率'] > 0].index, '目标期限收益率'] = merge2['收益率']
    if not merge3[merge3['收益率'] > 0].empty:
        data_main.loc[merge3[merge3['收益率'] > 0].index, '目标期限收益率'] = merge3['收益率']
    if not merge0[merge0['收益率'] > 0].empty:
        data_main.loc[merge0[merge0['收益率'] > 0].index, '目标期限收益率'] = merge0['收益率']

    merge11 = f_df11.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge21 = f_df21.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge31 = f_df31.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge01 = f_df01.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                          on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', '中债行权剩余期限'], how='left')
    if not merge11[merge11['收益率'] > 0].empty:
        data_main.loc[merge11[merge11['收益率'] > 0].index, '原期限收益率'] = merge11['收益率']
    if not merge21[merge21['收益率'] > 0].empty:
        data_main.loc[merge21[merge21['收益率'] > 0].index, '原期限收益率'] = merge21['收益率']
    if not merge31[merge31['收益率'] > 0].empty:
        data_main.loc[merge31[merge31['收益率'] > 0].index, '原期限收益率'] = merge31['收益率']
    if not merge01[merge01['收益率'] > 0].empty:
        data_main.loc[merge01[merge01['收益率'] > 0].index, '原期限收益率'] = merge01['收益率']

    data_main.loc[data_main[~mask1].index.tolist(), 'x1_m1'] = np.max(
        np.where(bond_term_values[~mask1][:, np.newaxis] >= terms1, terms1, min_terms1), axis=1)
    data_main.loc[data_main[~mask1].index.tolist(), 'x2_m1'] = np.min(
        np.where(bond_term_values[~mask1][:, np.newaxis] <= terms1, terms1, max_terms1), axis=1)
    insert_points_x1m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x1_m1'].values[:, np.newaxis], side='left')
    insert_points_x2m1 = np.searchsorted(terms1, data_main.loc[~mask1, 'x2_m1'].values[:, np.newaxis], side='right')
    data_main.loc[data_main[~mask1].index.tolist(), 'x11_m1'] = terms1[
        np.where(insert_points_x1m1 > 0, insert_points_x1m1 - 1, 0)]
    data_main.loc[data_main[~mask1].index.tolist(), 'x22_m1'] = terms1[
        np.where(insert_points_x2m1 < term_length1, insert_points_x2m1, term_length1 - 1)]

    f_df12 = data_main[(~mask1) & (data_main['发行方式'] == '公募')]
    f_df22 = data_main[(~mask1) & (data_main['发行方式'] == '私募')]
    f_df32 = data_main[(~mask1) & (data_main['是否永续'] == '是')]
    f_df02 = data_main[~mask1]

    merge12x1 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x1_m1'],
                            how='left')
    merge22x1 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x1_m1'],
                            how='left')
    merge32x1 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x1_m1'],
                            how='left')
    merge02x1 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                            on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x1_m1'], how='left')
    if not merge12x1[merge12x1['收益率'] > 0].empty:
        data_main.loc[merge12x1[merge12x1['收益率'] > 0].index, 'yx1_m1'] = merge12x1['收益率']
    if not merge22x1[merge22x1['收益率'] > 0].empty:
        data_main.loc[merge22x1[merge22x1['收益率'] > 0].index, 'yx1_m1'] = merge22x1['收益率']
    if not merge32x1[merge32x1['收益率'] > 0].empty:
        data_main.loc[merge32x1[merge32x1['收益率'] > 0].index, 'yx1_m1'] = merge32x1['收益率']
    if not merge02x1[merge02x1['收益率'] > 0].empty:
        data_main.loc[merge02x1[merge02x1['收益率'] > 0].index, 'yx1_m1'] = merge02x1['收益率']

    merge12x2 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge22x2 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge32x2 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge02x2 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                            on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x2_m1'], how='left')
    if not merge12x2[merge12x2['收益率'] > 0].empty:
        data_main.loc[merge12x2[merge12x2['收益率'] > 0].index, 'yx2_m1'] = merge12x2['收益率']
    if not merge22x2[merge22x2['收益率'] > 0].empty:
        data_main.loc[merge22x2[merge22x2['收益率'] > 0].index, 'yx2_m1'] = merge22x2['收益率']
    if not merge32x2[merge32x2['收益率'] > 0].empty:
        data_main.loc[merge32x2[merge32x2['收益率'] > 0].index, 'yx2_m1'] = merge32x2['收益率']
    if not merge02x2[merge02x2['收益率'] > 0].empty:
        data_main.loc[merge02x2[merge02x2['收益率'] > 0].index, 'yx2_m1'] = merge02x2['收益率']

    merge12x11 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge22x11 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge32x11 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge02x11 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                             on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x11_m1'], how='left')

    if not merge12x11[merge12x11['收益率'] > 0].empty:
        data_main.loc[merge12x11[merge12x11['收益率'] > 0].index, 'yx11_m1'] = merge12x11['收益率']
    if not merge22x11[merge22x11['收益率'] > 0].empty:
        data_main.loc[merge22x11[merge22x11['收益率'] > 0].index, 'yx11_m1'] = merge22x11['收益率']
    if not merge32x11[merge32x11['收益率'] > 0].empty:
        data_main.loc[merge32x11[merge32x11['收益率'] > 0].index, 'yx11_m1'] = merge32x11['收益率']
    if not merge02x11[merge02x11['收益率'] > 0].empty:
        data_main.loc[merge02x11[merge02x11['收益率'] > 0].index, 'yx11_m1'] = merge02x11['收益率']

    merge12x22 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge22x22 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge32x22 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge02x22 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                             on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x22_m1'], how='left')

    if not merge12x22[merge12x22['收益率'] > 0].empty:
        data_main.loc[merge12x22[merge12x22['收益率'] > 0].index, 'yx22_m1'] = merge12x22['收益率']
    if not merge22x22[merge22x22['收益率'] > 0].empty:
        data_main.loc[merge22x22[merge22x22['收益率'] > 0].index, 'yx22_m1'] = merge22x22['收益率']
    if not merge32x22[merge32x22['收益率'] > 0].empty:
        data_main.loc[merge32x22[merge32x22['收益率'] > 0].index, 'yx22_m1'] = merge32x22['收益率']
    if not merge02x22[merge02x22['收益率'] > 0].empty:
        data_main.loc[merge02x22[merge02x22['收益率'] > 0].index, 'yx22_m1'] = merge02x22['收益率']

    data_main.loc[f_df02.index, 'd1_m1'] = (data_main.loc[~mask1, 'yx2_m1'] - data_main.loc[~mask1, 'yx11_m1']) / (
                2 * (data_main.loc[~mask1, 'x2_m1'] - data_main.loc[~mask1, 'x11_m1'])).array
    data_main.loc[f_df02.index, 'd2_m1'] = (data_main.loc[~mask1, 'yx22_m1'] - data_main.loc[~mask1, 'yx1_m1']) / (
                2 * (data_main.loc[~mask1, 'x22_m1'] - data_main.loc[~mask1, 'x1_m1'])).array
    data_main.loc[f_df02.index, '原期限收益率'] = hermite_interpolation(data_main.loc[~mask1, '中债行权剩余期限'],
                                                                  data_main.loc[~mask1, 'x1_m1'],
                                                                  data_main.loc[~mask1, 'x2_m1'],
                                                                  data_main.loc[~mask1, 'yx1_m1'],
                                                                  data_main.loc[~mask1, 'yx2_m1'],
                                                                  data_main.loc[~mask1, 'd1_m1'],
                                                                  data_main.loc[~mask1, 'd2_m1']).array

    data_main['标准化收益率'] = (
            data_main['中债行权估值'] + (data_main['目标期限收益率'] - data_main['原期限收益率'])).fillna(0)

    data_main['债券余额'] = pd.to_numeric(data_main['债券余额'], errors='coerce')

    data_main = data_main[['日期', 'trade_code', '债券余额', '隐含评级', '标准化收益率', '目标期限']].rename(columns={
        '日期': 'DT',
        'trade_code': 'TRADE_CODE',
        '债券余额': 'balance',
        '隐含评级': 'imrating_calc',
        '标准化收益率': 'stdyield'
    })
    # 按目标期限拆分 DataFrame
    # target_terms = [0.49999999799999995, 1.0, 1.75, 2.0, 3.0, 4.0, 5.0]
    target_terms = [0.083333333, 0.24999999899999997,0.49999999799999995, 0.749999997,1.0, 1.75, 2.0, 3.0, 4.0, 5.0,7,10,15,20,30]

    data_frames = []
    for term in target_terms:
        term_str = str(term)  # 将目标期限转换为字符串
        df_term = data_main[data_main['目标期限'] == term].copy()
        df_term = df_term.drop(columns=['目标期限'])
        data_frames.append(df_term)

    # 定义表格名称
    # table_names = ['bond.hzcurve_credit_05', 'bond.hzcurve_credit_1', 'bond.hzcurve_credit_175',
    #                'bond.hzcurve_credit_2', 'bond.hzcurve_credit_3', 'bond.hzcurve_credit_4', 'bond.hzcurve_credit_5']
    table_names = ['bond.hzcurve_credit_0083', 'bond.hzcurve_credit_025', 'bond.hzcurve_credit_05','bond.hzcurve_credit_075', 'bond.hzcurve_credit_1', 'bond.hzcurve_credit_175','bond.hzcurve_credit_2','bond.hzcurve_credit_3','bond.hzcurve_credit_4','bond.hzcurve_credit_5','bond.hzcurve_credit_7','bond.hzcurve_credit_10','bond.hzcurve_credit_15','bond.hzcurve_credit_20','bond.hzcurve_credit_30']

    # 写入数据库
    for table_name, df in zip(table_names, data_frames):
        insert_database(
            df[(df['stdyield'] != 0) & (df['stdyield'] != '0') & (df['stdyield'] != '') & (df['stdyield'].notna())],
            table_name, ['TRADE_CODE', 'DT'])


