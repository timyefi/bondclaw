import json
import requests
import time
from datetime import datetime, date, timedelta, time
from sqlalchemy import VARCHAR, Date, DECIMAL
from pymysql import cursors
import sys
import os
import datetime
import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

目标期限 = pd.Series(np.arange(0, 30.01, 0.01))
# 创建一个DataFrame，其中包含这个序列
df_target_term = pd.DataFrame({'target_term': 目标期限})
terms1 = np.array([0, 0.083333333, 0.24999999899999997, 0.49999999799999995, 0.749999997, 1, 2, 3, 4,
                   5, 6, 7, 8, 9, 10, 15, 20, 30])

min_terms1 = min(terms1)
max_terms1 = max(terms1)
term_length1 = len(terms1)


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

for index, row in trade_dates_list[:].iterrows():
    trade_dates = trade_dates_list[index:index + 1]
    trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])
    trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
    unique_dates = "','".join(x for x in trade_dates)

    data_main.loc[(data_main['隐含评级'] == 'AA(2)') & (
        data_main['是否城投'] == '否'), '是否城投'] = '是'
    data_main.loc[(data_main['隐含评级'] == 'AAA-') &
                  (data_main['是否城投'] == '是'), '是否城投'] = '否'

    data_curve['日期1'] = pd.to_datetime(data_curve['日期1'])
    data_main['日期'] = pd.to_datetime(data_main['日期'])
    bond_term_values = data_main['中债行权剩余期限'].values
    p_yhpj_values = data_main['隐含评级'].values  # 转换为 NumPy 数组
    p_sm_values = data_main['发行方式'].values
    p_yx_values = data_main['是否永续'].values
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

    f_c1 = data_curve[(data_curve['发行方式1'] == '公募') & (
        data_curve['是否永续1'] == '否') & (data_curve['是否次级1'] == '否')]
    f_c2 = data_curve[(data_curve['发行方式1'] == '私募') & (
        data_curve['是否永续1'] == '否') & (data_curve['是否次级1'] == '否')]
    f_c3 = data_curve[(data_curve['发行方式1'] == '公募') & (
        data_curve['是否永续1'] == '是') & (data_curve['是否次级1'] == '否')]

    merge1 = f_df1.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge2 = f_df2.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge3 = f_df3.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '目标期限'],
                        how='left')
    merge0 = data_main.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                            on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', '目标期限'], how='left')

    if not merge1[merge1['收益率'] > 0].empty:
        data_main.loc[merge1[merge1['收益率'] > 0].index,
                      '目标期限收益率'] = merge1['收益率']
    if not merge2[merge2['收益率'] > 0].empty:
        data_main.loc[merge2[merge2['收益率'] > 0].index,
                      '目标期限收益率'] = merge2['收益率']
    if not merge3[merge3['收益率'] > 0].empty:
        data_main.loc[merge3[merge3['收益率'] > 0].index,
                      '目标期限收益率'] = merge3['收益率']
    if not merge0[merge0['收益率'] > 0].empty:
        data_main.loc[merge0[merge0['收益率'] > 0].index,
                      '目标期限收益率'] = merge0['收益率']

    merge11 = f_df11.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge21 = f_df21.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge31 = f_df31.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', '中债行权剩余期限'],
                          how='left')
    merge01 = f_df01.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                          on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', '中债行权剩余期限'], how='left')
    if not merge11[merge11['收益率'] > 0].empty:
        data_main.loc[merge11[merge11['收益率'] > 0].index,
                      '原期限收益率'] = merge11['收益率']
    if not merge21[merge21['收益率'] > 0].empty:
        data_main.loc[merge21[merge21['收益率'] > 0].index,
                      '原期限收益率'] = merge21['收益率']
    if not merge31[merge31['收益率'] > 0].empty:
        data_main.loc[merge31[merge31['收益率'] > 0].index,
                      '原期限收益率'] = merge31['收益率']
    if not merge01[merge01['收益率'] > 0].empty:
        data_main.loc[merge01[merge01['收益率'] > 0].index,
                      '原期限收益率'] = merge01['收益率']

    data_main.loc[data_main[~mask1].index.tolist(), 'x1_m1'] = np.max(
        np.where(bond_term_values[~mask1][:, np.newaxis] >= terms1, terms1, min_terms1), axis=1)
    data_main.loc[data_main[~mask1].index.tolist(), 'x2_m1'] = np.min(
        np.where(bond_term_values[~mask1][:, np.newaxis] <= terms1, terms1, max_terms1), axis=1)
    insert_points_x1m1 = np.searchsorted(
        terms1, data_main.loc[~mask1, 'x1_m1'].values[:, np.newaxis], side='left')
    insert_points_x2m1 = np.searchsorted(
        terms1, data_main.loc[~mask1, 'x2_m1'].values[:, np.newaxis], side='right')
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
        data_main.loc[merge12x1[merge12x1['收益率'] >
                                0].index, 'yx1_m1'] = merge12x1['收益率']
    if not merge22x1[merge22x1['收益率'] > 0].empty:
        data_main.loc[merge22x1[merge22x1['收益率'] >
                                0].index, 'yx1_m1'] = merge22x1['收益率']
    if not merge32x1[merge32x1['收益率'] > 0].empty:
        data_main.loc[merge32x1[merge32x1['收益率'] >
                                0].index, 'yx1_m1'] = merge32x1['收益率']
    if not merge02x1[merge02x1['收益率'] > 0].empty:
        data_main.loc[merge02x1[merge02x1['收益率'] >
                                0].index, 'yx1_m1'] = merge02x1['收益率']

    merge12x2 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge22x2 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge32x2 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x2_m1'],
                            how='left')
    merge02x2 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                            on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x2_m1'], how='left')
    if not merge12x2[merge12x2['收益率'] > 0].empty:
        data_main.loc[merge12x2[merge12x2['收益率'] >
                                0].index, 'yx2_m1'] = merge12x2['收益率']
    if not merge22x2[merge22x2['收益率'] > 0].empty:
        data_main.loc[merge22x2[merge22x2['收益率'] >
                                0].index, 'yx2_m1'] = merge22x2['收益率']
    if not merge32x2[merge32x2['收益率'] > 0].empty:
        data_main.loc[merge32x2[merge32x2['收益率'] >
                                0].index, 'yx2_m1'] = merge32x2['收益率']
    if not merge02x2[merge02x2['收益率'] > 0].empty:
        data_main.loc[merge02x2[merge02x2['收益率'] >
                                0].index, 'yx2_m1'] = merge02x2['收益率']

    merge12x11 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge22x11 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge32x11 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x11_m1'],
                             how='left')
    merge02x11 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                             on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x11_m1'], how='left')

    if not merge12x11[merge12x11['收益率'] > 0].empty:
        data_main.loc[merge12x11[merge12x11['收益率'] >
                                 0].index, 'yx11_m1'] = merge12x11['收益率']
    if not merge22x11[merge22x11['收益率'] > 0].empty:
        data_main.loc[merge22x11[merge22x11['收益率'] >
                                 0].index, 'yx11_m1'] = merge22x11['收益率']
    if not merge32x11[merge32x11['收益率'] > 0].empty:
        data_main.loc[merge32x11[merge32x11['收益率'] >
                                 0].index, 'yx11_m1'] = merge32x11['收益率']
    if not merge02x11[merge02x11['收益率'] > 0].empty:
        data_main.loc[merge02x11[merge02x11['收益率'] >
                                 0].index, 'yx11_m1'] = merge02x11['收益率']

    merge12x22 = f_df12.join(f_c1.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge22x22 = f_df22.join(f_c2.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge32x22 = f_df32.join(f_c3.set_index(['日期1', '隐含评级1', '是否城投1', '曲线期限']), on=['日期', '隐含评级', '是否城投', 'x22_m1'],
                             how='left')
    merge02x22 = f_df02.join(data_curve.set_index(['日期1', '隐含评级1', '发行方式1', '是否永续1', '是否次级1', '是否城投1', '曲线期限']),
                             on=['日期', '隐含评级', '发行方式', '是否永续', '是否次级', '是否城投', 'x22_m1'], how='left')

    if not merge12x22[merge12x22['收益率'] > 0].empty:
        data_main.loc[merge12x22[merge12x22['收益率'] >
                                 0].index, 'yx22_m1'] = merge12x22['收益率']
    if not merge22x22[merge22x22['收益率'] > 0].empty:
        data_main.loc[merge22x22[merge22x22['收益率'] >
                                 0].index, 'yx22_m1'] = merge22x22['收益率']
    if not merge32x22[merge32x22['收益率'] > 0].empty:
        data_main.loc[merge32x22[merge32x22['收益率'] >
                                 0].index, 'yx22_m1'] = merge32x22['收益率']
    if not merge02x22[merge02x22['收益率'] > 0].empty:
        data_main.loc[merge02x22[merge02x22['收益率'] >
                                 0].index, 'yx22_m1'] = merge02x22['收益率']

    data_main.loc[f_df02.index, 'd1_m1'] = (data_main.loc[~mask1, 'yx2_m1'] - data_main.loc[~mask1, 'yx11_m1']) / (
        2 * (data_main.loc[~mask1, 'x2_m1'] - data_main.loc[~mask1, 'x11_m1'])).array
    data_main.loc[f_df02.index, 'd2_m1'] = (data_main.loc[~mask1, 'yx22_m1'] - data_main.loc[~mask1, 'yx1_m1']) / (
        2 * (data_main.loc[~mask1, 'x22_m1'] - data_main.loc[~mask1, 'x1_m1'])).array
    data_main.loc[f_df02.index, '原期限收益率'] = hermite_interpolation(data_main.loc[~mask1, '中债行权剩余期限'],
                                                                  data_main.loc[~mask1,
                                                                                'x1_m1'],
                                                                  data_main.loc[~mask1,
                                                                                'x2_m1'],
                                                                  data_main.loc[~mask1,
                                                                                'yx1_m1'],
                                                                  data_main.loc[~mask1,
                                                                                'yx2_m1'],
                                                                  data_main.loc[~mask1,
                                                                                'd1_m1'],
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
    target_terms = [0.49999999799999995, 1.0, 1.75, 2.0, 3.0, 4.0, 5.0]

    data_frames = []
    for term in target_terms:
        term_str = str(term)  # 将目标期限转换为字符串
        df_term = data_main[data_main['目标期限'] == term].copy()
        df_term = df_term.drop(columns=['目标期限'])
        data_frames.append(df_term)
