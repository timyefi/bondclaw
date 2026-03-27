import pandas as pd
import sqlalchemy
import random
import scipy.stats as stats
import pywt
from pandas.tseries.offsets import DateOffset
from cyhs import *
import time
#内部数据库取数
import pandas as pd
import sqlalchemy
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

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
_cursor_pg='postgresql://postgres:hzinsights2015@139.224.107.113:18032/tsdb'
# # df=pd.read_excel(r"C:\Users\timye\Desktop\城投债发行与到期一览.xlsx")
# # df.to_sql('城投债规模', con=_cursor, if_exists='replace', index=False)

sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'stock',
    ), poolclass=sqlalchemy.pool.NullPool
)
conns = sql_engine.connect()
cursor = conns
sql_engine1 = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)
conns1 = sql_engine1.connect()
cursor1 = conns1
pandas_fetch_all = pd.read_sql

import pandas as pd
import sqlalchemy
import random
import scipy.stats as stats
import pywt
from pandas.tseries.offsets import DateOffset
from cyhs import *
import time


basic_p=pd.read_sql("""select * from 产业跟踪指标信息""",conns1)

def pro_df(df,df1,hy):
    df['行业']=hy
    values = df['CLOSE'].values
    wavelet = pywt.Wavelet('db2')
    coeffs = pywt.wavedec(values, wavelet)
    # 初始化一个空的 DataFrame 用于存放所有结果
    all_df = pd.DataFrame()
    for i in range(len(coeffs)):
        recon = pywt.waverec(coeffs[:i+1] + [np.zeros_like(c) for c in coeffs[i+1:]], wavelet)
        # 获取两者之间的最小长度
        min_length = min(len(recon), len(df['CLOSE']))

        # 创建一个新的 DataFrame，其中包含 recon、日期和level
        recon_df = pd.DataFrame({
            'DT': df['DT'].iloc[-min_length:],
            '行业': df['行业'].iloc[-min_length:],
            'RECON': recon[-min_length:],
            'level': i  # 添加level列
        })
        # 将结果添加到总的 DataFrame 中
        all_df = pd.concat([all_df, recon_df])
    # 创建一个新的 DataFrame，其中包含 recon、日期和level
    recon_df = pd.DataFrame({
        'DT': df['DT'],
        '行业': df['行业'],
        'RECON': df1[-len(df):]['CLOSE'],
        'level': '原值'  # 添加level列
    })
    # 将结果添加到总的 DataFrame 中
    all_df = pd.concat([all_df, recon_df])
    # 重命名列名
    all_df.columns=['DT', '行业', 'CLOSE', 'level']
    return all_df

def 处理异常值(df):
    df['z_score'] = (df['CLOSE'] - df['CLOSE'].mean()) / df['CLOSE'].std()

    # 找出异常值的索引
    outliers_indices = df[np.abs(df['z_score']) > 10].index

    # 对于每个异常值
    for idx in outliers_indices:
        # 如果它不是第一个和最后一个数据点
        if idx > 0 and idx < len(df) - 1:
            # 用前后值的差值替代
            df.at[idx, 'CLOSE'] = (df.at[idx - 1, 'CLOSE'] + df.at[idx + 1, 'CLOSE']) / 2.0
    df=df[['DT','CLOSE']]
    return df
def update_all_ind(date_end,basic_p):
    date_end=date_end
    basic_p=basic_p
    final_hf = pd.DataFrame()
    hy='轨交设备'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=月同比12个月移动平均(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='农化制品'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='白酒'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=百分制月环比转12月移动平均年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='白色家电'
    df1,dfa1=转12月移动平均年同比('S0029658', date_end)
    df2,dfa2=转12月移动平均年同比('S5616249', date_end)
    df3,dfa3=转12月移动平均年同比('S5616357', date_end)
    df4,dfa4=转12月移动平均年同比('S5616432', date_end)
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    df3['DT'] = pd.to_datetime(df3['DT'])
    df4['DT'] = pd.to_datetime(df4['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    dfa3['DT'] = pd.to_datetime(dfa3['DT'])
    dfa4['DT'] = pd.to_datetime(dfa4['DT'])
    df1.set_index('DT', inplace=True)
    df2.set_index('DT', inplace=True)
    df3.set_index('DT', inplace=True)
    df4.set_index('DT', inplace=True)
    dfa1.set_index('DT', inplace=True)
    dfa2.set_index('DT', inplace=True)
    dfa3.set_index('DT', inplace=True)
    dfa4.set_index('DT', inplace=True)
    min_date = min(df1.index.min(), df2.index.min(), df3.index.min(), df4.index.min())
    max_date = max(df1.index.max(), df2.index.max(), df3.index.max(), df4.index.max())
    idx = pd.date_range(start=min_date, end=max_date, freq='M')

    df1 = df1.reindex(idx)
    df2 = df2.reindex(idx)
    df3 = df3.reindex(idx)
    df4 = df4.reindex(idx)
    dfa1 = dfa1.reindex(idx)
    dfa2 = dfa2.reindex(idx)
    dfa3 = dfa3.reindex(idx)
    dfa4 = dfa4.reindex(idx)

    df = df1.merge(df2, left_index=True, right_index=True, how='outer',suffixes=('1', '2'))
    df = df.merge(df3, left_index=True, right_index=True, how='outer',suffixes=('', '3'))
    df = df.merge(df4, left_index=True, right_index=True, how='outer',suffixes=('', '4'))
    dfa = dfa1.merge(dfa2, left_index=True, right_index=True, how='outer',suffixes=('1', '2'))
    dfa = dfa.merge(dfa3, left_index=True, right_index=True, how='outer',suffixes=('', '3'))
    dfa = dfa.merge(dfa4, left_index=True, right_index=True, how='outer',suffixes=('', '4'))

    df = df.ffill()
    dfa = dfa.ffill()
    df.loc[:, 'CLOSE']=df['CLOSE1']*0.5+df['CLOSE2']*1/3+df['CLOSE']*1/3+df['CLOSE4']*1/3
    dfa.loc[:, 'CLOSE']=dfa['CLOSE1']*0.5+dfa['CLOSE2']*1/3+dfa['CLOSE']*1/3+dfa['CLOSE4']*1/3
    df=df[['CLOSE']]
    dfa=dfa[['CLOSE']]
    df.reset_index(inplace=True)
    dfa.reset_index(inplace=True)
    df.columns=['DT','CLOSE']
    dfa.columns=['DT','CLOSE']
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='半导体'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='保险'
    # 日期计算
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='乘用车'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='电力'
    # 日期计算
    # 发电量 年累计值
    df1,dfa1 = 转12月移动平均年同比('S0027014', date_end, 11)
    # 动力煤价格 日度
    df2,dfa2 = 高频价格转12月移动平均月均价年同比('S5130999', date_end)
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    df=df1.merge(df2,on='DT',how='left')
    dfa=dfa1.merge(dfa2,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']-df['CLOSE_y']
    dfa.loc[:, 'CLOSE']=dfa['CLOSE_x']-dfa['CLOSE_y']
    df=df[['DT','CLOSE']]
    dfa=dfa[['DT','CLOSE']]
    df=df[200:]
    dfa=dfa[200:]
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='电网设备'
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='房地产开发'
    # 商品房销售面积 年累计值
    df1,dfa1 = 转12月移动平均年同比('S0029658', date_end, 11)
    df1=df1[365:]
    dfa1=dfa1[365:]
    # 房屋新开工面积 累计同比
    df2,dfa2 = 月同比12个月移动平均('S0073293', date_end)
    df1['CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2['CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    dfa1['CLOSE'] = (dfa1['CLOSE'] - dfa1['CLOSE'].mean())/dfa1['CLOSE'].std()
    dfa2['CLOSE'] = (dfa2['CLOSE'] - dfa2['CLOSE'].mean())/dfa2['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    df=df1.merge(df2,on='DT',how='left')
    dfa=dfa1.merge(dfa2,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']/2+df['CLOSE_y']/2
    dfa.loc[:, 'CLOSE']=dfa['CLOSE_x']/2+dfa['CLOSE_y']/2
    df=df[['DT','CLOSE']]
    dfa=dfa[['DT','CLOSE']]
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='家居用品'
    # 日期计算
    # 商品房销售面积 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='风电设备'
    # 新增风电装机容量 年累计值
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='工程机械'
    # 工业增加值 当月同比
    df1,dfa1 = 转12月移动平均年同比('M0000545', date_end, 11)
    # 挖掘机销量 当月值
    df2,dfa2 = 月同比12个月移动平均('S6002167', date_end)
    df1['CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2['CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    dfa1['CLOSE'] = (dfa1['CLOSE'] - dfa1['CLOSE'].mean())/dfa1['CLOSE'].std()
    dfa2['CLOSE'] = (dfa2['CLOSE'] - dfa2['CLOSE'].mean())/dfa2['CLOSE'].std()

    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    df=df1.merge(df2,on='DT',how='left')
    dfa=dfa1.merge(dfa2,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']/2+df['CLOSE_y']/2
    dfa.loc[:, 'CLOSE']=dfa['CLOSE_x']/2+dfa['CLOSE_y']/2
    df=df[['DT','CLOSE']]
    dfa=dfa[['DT','CLOSE']]
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='工业金属'
    # 铜价格 日度
    df1,dfa1 = 转12月移动平均年同比('S0181392', date_end, 11)
    # 铝价格 日度
    df2,dfa2 = 月同比12个月移动平均('S0181382', date_end)
    df1.loc[:, 'CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2.loc[:, 'CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    dfa1.loc[:, 'CLOSE'] = (dfa1['CLOSE'] - dfa1['CLOSE'].mean())/dfa1['CLOSE'].std()
    dfa2.loc[:, 'CLOSE'] = (dfa2['CLOSE'] - dfa2['CLOSE'].mean())/dfa2['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    df=df1.merge(df2,on='DT',how='left')
    dfa=dfa1.merge(dfa2,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']/2+df['CLOSE_y']/2
    dfa.loc[:, 'CLOSE']=dfa['CLOSE_x']/2+dfa['CLOSE_y']/2
    df=df[['DT','CLOSE']]
    dfa=dfa[['DT','CLOSE']]
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='光伏设备'
    # 硅料价格 周度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    # 日期计算
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='光学光电子'
    # 光电子器件产量 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='国有大型银行'
    df1,dfa1 = 月同比12个月移动平均('M0043417', date_end)
    df2,dfa2 = 月同比12个月移动平均('M0096870', date_end)
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    dfa1['DT'] = pd.to_datetime(dfa1['DT'])
    dfa2['DT'] = pd.to_datetime(dfa2['DT'])
    df11=df1.merge(df2,on='DT',how='left')
    dfa11=dfa1.merge(dfa2,on='DT',how='left')
    df11.loc[:, 'CLOSE']=df11['CLOSE_x']*df11['CLOSE_y']
    dfa11.loc[:, 'CLOSE']=dfa11['CLOSE_x']*dfa11['CLOSE_y']
    df11=df11[['DT','CLOSE']]
    dfa11=dfa11[['DT','CLOSE']]
    df11_shifted = df11.copy()
    dfa11_shifted = dfa11.copy()
    df11.set_index('DT', inplace=True)
    dfa11.set_index('DT', inplace=True)
    df11_shifted.set_index('DT', inplace=True)
    dfa11_shifted.set_index('DT', inplace=True)
    df11_shifted.index = df11_shifted.index + DateOffset(years=1)
    dfa11_shifted.index = dfa11_shifted.index + DateOffset(years=1)
    df11_shifted = df11_shifted.resample('D').mean()
    dfa11_shifted = dfa11_shifted.resample('D').mean()
    # 将原始DataFrame和偏移后的DataFrame合并
    df11_merged = pd.merge(df11, df11_shifted, left_index=True, right_index=True, suffixes=('', '_1_year_ago'))
    dfa11_merged = pd.merge(dfa11, dfa11_shifted, left_index=True, right_index=True, suffixes=('', '_1_year_ago'))
    # 计算年同比
    df11_merged['YoY'] = (df11_merged['CLOSE'] - df11_merged['CLOSE_1_year_ago'])*100 / df11_merged['CLOSE_1_year_ago']
    dfa11_merged['YoY'] = (dfa11_merged['CLOSE'] - dfa11_merged['CLOSE_1_year_ago'])*100 / dfa11_merged['CLOSE_1_year_ago']
    df11_merged.reset_index(inplace=True)
    dfa11_merged.reset_index(inplace=True)
    df11=df11_merged[['DT','YoY']].rename(columns={'YoY':'CLOSE'})
    dfa11=dfa11_merged[['DT','YoY']].rename(columns={'YoY':'CLOSE'})

    df11.dropna(inplace=True)
    dfa11.dropna(inplace=True)
    # 中长期贷款余额 当月值
    df3,dfa3 = 月同比12个月移动平均('M0043418', date_end)
    # 5年LPR
    df4,dfa4 = 月同比12个月移动平均('M0331299', date_end)
    df3['DT'] = pd.to_datetime(df3['DT'])
    df4['DT'] = pd.to_datetime(df4['DT'])
    dfa3['DT'] = pd.to_datetime(dfa3['DT'])
    dfa4['DT'] = pd.to_datetime(dfa4['DT'])
    df12=df3.merge(df4,on='DT',how='left')
    dfa12=dfa3.merge(dfa4,on='DT',how='left')
    df12.loc[:, 'CLOSE']=df12['CLOSE_x']*df12['CLOSE_y']
    dfa12.loc[:, 'CLOSE']=dfa12['CLOSE_x']*dfa12['CLOSE_y']
    df12=df12[['DT','CLOSE']]
    dfa12=dfa12[['DT','CLOSE']]
    df12_shifted = df12.copy()
    dfa12_shifted = dfa12.copy()

    df12.set_index('DT', inplace=True)
    dfa12.set_index('DT', inplace=True)
    df12_shifted.set_index('DT', inplace=True)
    dfa12_shifted.set_index('DT', inplace=True)
    df12_shifted.index = df12_shifted.index + DateOffset(years=1)
    dfa12_shifted.index = dfa12_shifted.index + DateOffset(years=1)
    df12_shifted = df12_shifted.resample('D').mean()
    dfa12_shifted = dfa12_shifted.resample('D').mean()
    # 将原始DataFrame和偏移后的DataFrame合并
    df12_merged = pd.merge(df12, df12_shifted, left_index=True, right_index=True, suffixes=('', '_1_year_ago'))
    dfa12_merged = pd.merge(dfa12, dfa12_shifted, left_index=True, right_index=True, suffixes=('', '_1_year_ago'))
    # 计算年同比
    df12_merged['YoY'] = (df12_merged['CLOSE'] - df12_merged['CLOSE_1_year_ago'])*100 / df12_merged['CLOSE_1_year_ago']
    dfa12_merged['YoY'] = (dfa12_merged['CLOSE'] - dfa12_merged['CLOSE_1_year_ago'])*100 / dfa12_merged['CLOSE_1_year_ago']
    df12_merged.reset_index(inplace=True)
    dfa12_merged.reset_index(inplace=True)
    df12=df12_merged[['DT','YoY']].rename(columns={'YoY':'CLOSE'})
    dfa12=dfa12_merged[['DT','YoY']].rename(columns={'YoY':'CLOSE'})
    df12.dropna(inplace=True)
    dfa12.dropna(inplace=True)
    df=df11.merge(df12,on='DT',how='left')
    dfa=dfa11.merge(dfa12,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']*0.5+df['CLOSE_y']*0.5
    dfa.loc[:, 'CLOSE']=dfa['CLOSE_x']*0.5+dfa['CLOSE_y']*0.5
    df=df[['DT','CLOSE']]
    dfa=dfa[['DT','CLOSE']]
    df.dropna(inplace=True)
    dfa.dropna(inplace=True)
    df=pro_df(df,dfa,hy)
    print(df[df['DT']=='2024-03-31'])
    final_hf = pd.concat([final_hf, df], ignore_index=True)
    print(final_hf[(final_hf['DT']=='2024-03-31')&(final_hf['行业']=='国有大型银行')])

    hy='航运港口'
    # 上海出口集装箱运价指数 周度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='化学原料'
    # 聚乙烯 日度
    df1,df11 = 高频价格转12月移动平均月均价年同比('S0181390', date_end)
    # 聚丙烯 日度
    df2,df21 = 高频价格转12月移动平均月均价年同比('S0203119', date_end)
    df1.loc[:, 'CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2.loc[:, 'CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    df11.loc[:, 'CLOSE'] = (df11['CLOSE'] - df11['CLOSE'].mean())/df11['CLOSE'].std()
    df21.loc[:, 'CLOSE'] = (df21['CLOSE'] - df21['CLOSE'].mean())/df21['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    df11['DT'] = pd.to_datetime(df11['DT'])
    df21['DT'] = pd.to_datetime(df21['DT'])
    df=df1.merge(df2,on='DT',how='left')
    df1=df11.merge(df21,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']/2+df['CLOSE_y']/2
    df1.loc[:, 'CLOSE']=df1['CLOSE_x']/2+df1['CLOSE_y']/2
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='化学制品'
    # 化学原料及化学制品工业增加值 当月同比
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    # 日期计算
    df,df1=月同比12个月移动平均(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='化学制药'
    # 日期计算
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code, date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='炼化及贸易'
    # 原油现货价 日度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='煤炭开采'
    # 焦炭价格 日度
    df1,df11 = 高频价格转12月移动平均月均价年同比('S0181380', date_end)
    # 动力煤价格 日度
    df2,df21 = 高频价格转12月移动平均月均价年同比('S5130999', date_end)
    df1.loc[:, 'CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2.loc[:, 'CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    df11.loc[:, 'CLOSE'] = (df11['CLOSE'] - df11['CLOSE'].mean())/df11['CLOSE'].std()  
    df21.loc[:, 'CLOSE'] = (df21['CLOSE'] - df21['CLOSE'].mean())/df21['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    df11['DT'] = pd.to_datetime(df11['DT'])
    df21['DT'] = pd.to_datetime(df21['DT'])
    df=df1.merge(df2,on='DT',how='left')
    df1=df11.merge(df21,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']/2+df['CLOSE_y']/2
    df1.loc[:, 'CLOSE']=df1['CLOSE_x']/2+df1['CLOSE_y']/2
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='能源金属'
    # 金属锂价格 日度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='农产品加工'
    # 社零餐饮收入 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[450:]
    df1=df1[450:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='调味发酵品'
    # 社零餐饮收入 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[450:]
    df1=df1[450:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='普钢'
    # 螺纹钢价格 日度
    df1,df11 = 高频价格转12月移动平均月均价年同比('S5707798', date_end)
    # 铁矿石价格 日度
    df2,df21 = 高频价格转12月移动平均月均价年同比('S0186244', date_end)
    # 焦炭价格 日度
    df3,df31 = 高频价格转12月移动平均月均价年同比('S0181380', date_end)
    df1.loc[:, 'CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2.loc[:, 'CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    df3.loc[:, 'CLOSE']= (df3['CLOSE'] - df3['CLOSE'].mean())/df3['CLOSE'].std()
    df11.loc[:, 'CLOSE'] = (df11['CLOSE'] - df11['CLOSE'].mean())/df11['CLOSE'].std()
    df21.loc[:, 'CLOSE'] = (df21['CLOSE'] - df21['CLOSE'].mean())/df21['CLOSE'].std()
    df31.loc[:, 'CLOSE'] = (df31['CLOSE'] - df31['CLOSE'].mean())/df31['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    df3['DT'] = pd.to_datetime(df3['DT'])
    df11['DT'] = pd.to_datetime(df11['DT'])
    df21['DT'] = pd.to_datetime(df21['DT'])
    df31['DT'] = pd.to_datetime(df31['DT'])
    df=df1.merge(df2,on='DT',how='left')
    df=df.merge(df3,on='DT',how='left')
    df1=df11.merge(df21,on='DT',how='left')
    df1=df1.merge(df31,on='DT',how='left')
    df.loc[:, 'CLOSE']=df['CLOSE_x']-1.6*df['CLOSE_y']-0.5*df['CLOSE']
    df1.loc[:, 'CLOSE']=df1['CLOSE_x']-1.6*df1['CLOSE_y']-0.5*df1['CLOSE']
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='汽车零部件'
    # 汽车产量 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='软件开发'
    # 软件业务收入 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='水泥'
    # 水泥价格 日度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='通信服务'
    # 通信业务收入 年累计值*
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='物流'
    # 物流总额 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[550:]
    df1=df1[550:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='消费电子'
    # 手机出货量 年累计值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=df[365:]
    df1=df1[365:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='小金属'
    # 稀土价格 日度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='养殖业'
    # 生猪价格 周度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='一般零售'
    # 中国:社会消费品零售总额 当月值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='医疗器械'
    # 彩超出口金额 当月值
    df1,df11 = 转12月移动平均年同比('S6262650', date_end)
    # 监护仪出口金额 当月值
    df2,df21 = 转12月移动平均年同比('S6262655', date_end)
    # 治疗器出口金额 当月值
    df3,df31 = 转12月移动平均年同比('X0418731', date_end)
    df1.loc[:, 'CLOSE'] = (df1['CLOSE'] - df1['CLOSE'].mean())/df1['CLOSE'].std()
    df2.loc[:, 'CLOSE'] = (df2['CLOSE'] - df2['CLOSE'].mean())/df2['CLOSE'].std()
    df3.loc[:, 'CLOSE'] = (df3['CLOSE'] - df3['CLOSE'].mean())/df3['CLOSE'].std()
    df11.loc[:, 'CLOSE'] = (df11['CLOSE'] - df11['CLOSE'].mean())/df11['CLOSE'].std()
    df21.loc[:, 'CLOSE'] = (df21['CLOSE'] - df21['CLOSE'].mean())/df21['CLOSE'].std()
    df31.loc[:, 'CLOSE'] = (df31['CLOSE'] - df31['CLOSE'].mean())/df31['CLOSE'].std()
    df1['DT'] = pd.to_datetime(df1['DT'])
    df2['DT'] = pd.to_datetime(df2['DT'])
    df3['DT'] = pd.to_datetime(df3['DT'])
    df11['DT'] = pd.to_datetime(df11['DT'])
    df21['DT'] = pd.to_datetime(df21['DT'])
    df31['DT'] = pd.to_datetime(df31['DT'])
    df=df1.merge(df2,on='DT',how='left')
    df=df.merge(df3,on='DT',how='left')
    df1=df11.merge(df21,on='DT',how='left')
    df1=df1.merge(df31,on='DT',how='left')
    df.loc[:, 'CLOSE']=(df['CLOSE_x']+df['CLOSE_y']+df['CLOSE'])/3
    df1.loc[:, 'CLOSE']=(df1['CLOSE_x']+df1['CLOSE_y']+df1['CLOSE'])/3
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='证券'
    # 股票成交金额 当月值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=转12月移动平均年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='中药'
    # 中药材价格指数 日度
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1=高频价格转12月移动平均月均价年同比(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)


    hy='专用设备'
    # 弘则产能指数
    sql = f"""
    SELECT TRADE_CODE,DT,CLOSE FROM edb.EDBDATA WHERE TRADE_CODE IN ('S6012632','S6012633','S6012634','S6012635','S6012635','S6012636','S6012637','S6012638','S6012639') AND MONTH(DT) NOT IN (1,2) AND DT<='{date_end}'
    """

    raw = pandas_fetch_all(sql, cursor)  # 累计
    raw['CHG'] = raw.groupby(['TRADE_CODE'])['CLOSE'].pct_change(10)
    data = raw[['DT', 'TRADE_CODE', 'CHG']]
    # data['DT']=pd.to_datetime(data['DT'])
    data = data.set_index(['DT', 'TRADE_CODE'])  # 两个index
    data = data.unstack(level=['DT']).T
    data[data > 1] = 1
    data = data * 100
    data = data.reset_index(drop=False)

    sql_ = f"""
    SELECT TRADE_CODE,DT,CLOSE FROM edb.EDBDATA WHERE TRADE_CODE IN ('S0027801','S0243312','S0070841','S0027817','S0070840','S0070843','S0070850','S0070851','S0070863','S0070862','S0070864','S0071470','S0071497','S0071532','S0027872','S0071515','S0071459') AND MONTH(DT) NOT IN (1,2) AND DT<='{date_end}'
    """
    raw_ = pandas_fetch_all(sql_, cursor)  # 累计
    data_ = raw_[['DT', 'TRADE_CODE', 'CLOSE']]
    # data['DT']=pd.to_datetime(data['DT'])
    data_ = data_.set_index(['DT', 'TRADE_CODE'])  # 两个index
    data_ = data_.unstack(level=['DT']).T
    data_ = data_.reset_index(drop=False)

    res = pd.merge(data_, data, on='DT', how='left')
    res = res.drop(columns=['level_0_x', 'level_0_y'])
    res.sort_values('DT', inplace=True)
    res = res.set_index('DT')
    final = res.mean(axis=1)
    final = final.reset_index()
    final.columns = ['DT', 'CLOSE']
    final=处理异常值(final)
    final1=final.copy()
    # final['CLOSE'] = final['CLOSE'].rolling(3).mean()
    final = final.set_index('DT')
    final1 = final1.set_index('DT')
    date_range = pd.date_range(start=final.index.min(), end=final.index.max())
    final = final.reindex(date_range)
    final1 = final1.reindex(date_range)
    final['CLOSE'] = final['CLOSE'].interpolate(method='linear')
    final1['CLOSE'] = final1['CLOSE'].interpolate(method='linear')
    final.ffill(inplace=True)
    final1.ffill(inplace=True)
    final.reset_index(inplace=True)
    final1.reset_index(inplace=True)
    final.rename(columns={'index': 'DT'}, inplace=True)
    final1.rename(columns={'index': 'DT'}, inplace=True)
    final.dropna(inplace=True)
    final1.dropna(inplace=True)
    df=final[['DT','CLOSE']]
    df1=final1[['DT','CLOSE']]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='自动化设备'
    # 工业增加值 当月同比
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1 = 月同比12个月移动平均(trade_code,date_end)
    df=df[180:]
    df1=df1[180:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='通用设备'
    # 工业增加值 当月同比
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1 = 月同比12个月移动平均(trade_code,date_end)
    df=df[180:]
    df1=df1[180:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='装修建材'
    # 房屋新开工面积 累计同比
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1 = 月同比12个月移动平均(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='电池'
    # 新能源汽车销量 当月值
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1 = 转12月移动平均年同比(trade_code,date_end)
    df=df[1095:]
    df1=df1[1095:]
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)

    hy='基础建设'
    # 基础设施建设投资 累计同比
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    df,df1 = 月同比12个月移动平均(trade_code,date_end)
    df=pro_df(df,df1,hy)
    final_hf = pd.concat([final_hf, df], ignore_index=True)


    final_hf.columns = ['DT', '行业', 'CLOSE', 'level']
    print(final_hf.head(5))

    final_hf.to_sql('行业指标', conns1, if_exists='replace', index=False)

    sql="""
    ALTER TABLE 行业指标
    MODIFY COLUMN DT DATE,
    MODIFY COLUMN 行业 VARCHAR(100),
    MODIFY COLUMN level VARCHAR(5),
    ADD PRIMARY KEY (DT, 行业, level);
    """   
    conns1.execute(text(sql))

date_end=time.strftime('%Y-%m-%d',time.localtime(time.time()-86400*1))   
update_all_ind(date_end,basic_p)

import pandas as pd
from sqlalchemy import create_engine


# 从MySQL数据库中读取数据
industry_indicator = pd.read_sql('SELECT * FROM 行业指标', cursor1)
industry_tracking_info = pd.read_sql('SELECT * FROM 产业跟踪指标信息 where level is not null', cursor1)
industry_tracking_info['level']=industry_tracking_info['level'].astype(str)
industry_indicator['level']=industry_indicator['level'].astype(str)
# 根据行业和日期，获取每个行业在最优级别的对应指标值
df = pd.merge(industry_indicator, industry_tracking_info, on='行业', how='left',suffixes=('_x', '_y'))

df = df[(df['level_x']) == (df['level_y'])]

# 确保数据按照行业和日期排序
df = df.sort_values(['行业', 'DT'])
df = df.groupby(['行业', 'DT']).agg({'名称': ','.join, '周期天数': 'first', '趋势天数': 'first', 'CLOSE': 'first'}).reset_index()

# 计算在过去周期天数中的最优级别指标值中的百分位排序（从低到高排）
def calculate_quantile(group):
    period_days = int(group['周期天数'].iloc[0])
    group['分位点'] = group['CLOSE'].rolling(window=period_days,min_periods=100).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])*100
    return group
df = df.reset_index(drop=True)
df = df.groupby('行业').apply(calculate_quantile)

# 计算这一指标在最近趋势判断天数范围内的变化方向
def calculate_trend(group):
    trend_days = int(group['趋势天数'].iloc[0])
    if len(group) >= trend_days:
        group['趋势'] = group['CLOSE'].diff(periods=trend_days)
    else:
        group['趋势'] = group['CLOSE'].diff(periods=len(group))
    group['趋势'] = group['趋势'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return group
df = df.reset_index(drop=True)
df = df.groupby('行业').apply(calculate_trend)
df['指标名称']=df['名称']
# 将结果插入到"行业景气度跟踪表"中
df[['行业', '指标名称', 'DT', '分位点', '趋势']].to_sql('行业景气度跟踪', con=cursor1, if_exists='replace', index=False)
sql="""
ALTER TABLE 行业景气度跟踪
MODIFY COLUMN DT DATE,
MODIFY COLUMN 行业 VARCHAR(100),
MODIFY COLUMN 指标名称 VARCHAR(100),
ADD PRIMARY KEY (DT, 行业);
"""
conns1.execute(text(sql))

from datetime import datetime, date, timedelta, time
import numpy as np
import pandas as pd

df = pd.read_sql(f"""SELECT distinct 行业
FROM yq.行业景气度跟踪""", _cursor)
target_term = '2'
for hy in df['行业']:

    sql=f"""
        select *
        from yq.产业跟踪指标信息
        where 行业= '{hy}'"""
    basic_p=pd.read_sql(sql,_cursor) 
    window_size=int(basic_p[basic_p['行业']==hy]['周期天数'].iloc[0])

    def calculate_x(df):
        df['x'] = np.arcsin(2 * df['分位点'] / 100 - 1)
        df['x'] = df.apply(lambda x: np.pi - x['x'] if x['趋势'] == -1 else x['x'], axis=1)
        df['x'] = df.apply(lambda x: np.pi * 2 + x['x'] if x['x'] < 0 else x['x'], axis=1)
        return df

    df = pd.read_sql(f"""SELECT *
    FROM yq.行业景气度跟踪
    where 行业= '{hy}'
    order by dt,分位点""", _cursor)

    # df1 = df1.groupby('DT').apply(calculate_x) 
    if hy=='证券':
        hy='证券公司'
    elif hy=='国有大型银行':
        hy='银行'

    bd=min(df['DT'])

    if hy in ('证券公司','保险','银行','其他'):
        trade_dates = pd.read_sql(f"""
        SELECT Distinct dt AS "DT" 
        FROM hzcurve_credit A 
        WHERE A.target_term=2 and A.dt >= '{bd}'
    """, _cursor_pg)
    else:
        trade_dates = pd.read_sql(f"""
        SELECT Distinct dt AS "DT" 
        FROM hzcurve_credit A
        WHERE A.target_term=2 and A.dt >= '{bd}'
        and A.trade_code in (select trade_code from 债券分类 B
        where B.大类 ='产业' and replace(split_part(B.子类,'--',2),'Ⅱ', '') ='{hy}')
        """, _cursor_pg)
    bd1=min(trade_dates['DT'])
    ed1=max(trade_dates['DT'])
    trade_dates['DT'] = pd.to_datetime(trade_dates['DT'])

    trade_dates = trade_dates['DT'].dt.strftime('%Y-%m-%d').tolist()
    unique_dates = "','".join(x for x in trade_dates)
    if target_term=='0.49999999799999995':
        classify3='中债国开债到期收益率:6月'
    else:
        classify3='中债国开债到期收益率:'+str(target_term)+'年'

    if hy in ('证券公司','保险','银行','其他'):
        sql=f"""
        select 
        distinct A.trade_code
        FROM hzcurve_credit A
        inner join 债券分类 B
        on A.trade_code = B.trade_code     
        where 
        A.dt='{ed1}'
        and A.target_term='{target_term}'
        and B.大类 ='金融'
        and B.子类 ='{hy}'
        """ 
    else:
        sql=f"""
        select 
        distinct A.trade_code
        FROM hzcurve_credit A
        inner join 债券分类 B
        on A.trade_code = B.trade_code     
        where 
        A.dt='{ed1}'
        and A.target_term='{target_term}'
        and B.大类 ='产业'
        and replace(split_part(B.子类,'--',2),'Ⅱ', '') ='{hy}'
        """
    df1=pd.read_sql(sql,_cursor_pg)
    count=len(df1)
    if hy in ('证券公司','保险','银行','其他'):
        sql=f"""
        select 
        distinct B.trade_code
        FROM 债券分类 B  
        where 
        B.大类 ='金融'
        and B.子类 ='{hy}'
        """ 
    else:
        sql=f"""
        select 
        distinct B.trade_code
        FROM 债券分类 B
        where 
        B.大类 ='产业'
        and replace(split_part(B.子类,'--',2),'Ⅱ', '') ='{hy}'
        """
    df1=pd.read_sql(sql,_cursor_pg)
    trade_codes=df1['trade_code'].tolist()
    trade_codes="','".join(x for x in trade_codes)

    def fill_na(df):
        gap_days = 180
        df['balance'] = df['balance'].bfill(limit=gap_days).ffill(limit=gap_days)
        df['stdyield'] = df['stdyield'].bfill(limit=gap_days).ffill(limit=gap_days)
        return df

    if count<100:
        query=f"""
                SELECT
                    trade_code,
                    time_bucket_gapfill ( '1 day', dt, '{bd1}', '{ed1}' ) AS 日期1,
                    interpolate(max(stdyield)) AS stdyield,
                    interpolate(max(balance)) AS balance
                FROM hzcurve_credit
                WHERE
                    dt >= '{bd1}'
                    and trade_code in ('{trade_codes}')
                    AND target_term='{target_term}'
                    and balance>0
                    and stdyield>0
                group by trade_code, 日期1
                order by 日期1;"""
        result=pd.read_sql(query,_cursor_pg)
        result.rename(columns={'日期1': 'dt'}, inplace=True)
        result = result.groupby('trade_code').apply(fill_na)
        result['weighted_yield'] = result['balance'] * result['stdyield']
        weighted_yield_df = result.groupby(['dt'])['weighted_yield'].sum() / result.groupby(['dt'])['balance'].sum()
        weighted_yield_df = weighted_yield_df.reset_index()
        weighted_yield_df.columns = ['日期', '收益率']
        weighted_yield_df.ffill(inplace=True)

        query_final1=f"""
            SELECT 
                CASE WHEN sum(A.balance)>0 THEN sum(A.balance*A.stdyield) / sum(A.balance)
                    ELSE NULL END AS 收益率
            FROM 
                hzcurve_credit A
            WHERE 
                A.dt ='{ed1}'
                and A.trade_code in ('{trade_codes}')
                AND A.target_term='{target_term}'
                and A.balance>0
                and A.stdyield>0
        """
        result0 = pd.read_sql(query_final1, _cursor_pg)
        if result0.empty or result.empty:
            result1=pd.DataFrame()
        else:
            yiled0=result0['收益率'].iloc[-1]
            yiled=weighted_yield_df['收益率'].iloc[-1]
            weighted_yield_df['收益率']=weighted_yield_df['收益率']*yiled0/yiled
            result1=weighted_yield_df
    else:
        query=f"""
        SELECT 
            A.dt as 日期,
            CASE WHEN sum(A.balance)>0 THEN sum(A.balance*A.stdyield) / sum(A.balance)
                ELSE NULL END AS 收益率
        FROM 
            hzcurve_credit A
        WHERE 
            A.dt >= '{bd1}'
            and trade_code in ('{trade_codes}')
            AND A.target_term='{target_term}'
            and A.balance>0
            and A.stdyield>0
        group by A.dt
        """
        result1 = pd.read_sql(query, _cursor_pg)

    result1['日期'] = pd.to_datetime(result1['日期'])
    result1['日期'] = result1['日期'].dt.strftime('%Y-%m-%d')

    base_data=pd.read_sql(f"""SELECT dt as 日期, trade_code, close AS BASE_CLOSE
                    FROM `bond`.`marketinfo_curve` 
                    WHERE DT >='{bd1}'
                    AND trade_code IN (SELECT trade_code FROM `bond`.`basicinfo_curve` WHERE `sec_name` = '{classify3}') order by 日期 """,_cursor)
    base_data['日期'] = pd.to_datetime(base_data['日期'])
    base_data['日期'] = base_data['日期'].dt.strftime('%Y-%m-%d')

    result1=result1.merge(base_data[['日期','BASE_CLOSE']],on=['日期'],how='inner')
    
    result1['信用利差'] = round((result1['收益率']-result1['BASE_CLOSE'])*100,2)
    result1=result1[['日期','信用利差']]
    result1['日期'] = pd.to_datetime(result1['日期'])
    result1.set_index('日期', inplace=True)
    date_range = pd.date_range(start=result1.index.min(), end=result1.index.max())
    result1 = result1.reindex(date_range)
    result1['信用利差'] = result1['信用利差'].interpolate(method='linear')
    result1.ffill(inplace=True)
    result1.reset_index(inplace=True)
    result1.rename(columns={'index': '日期'}, inplace=True)

    result1['信用利差分位点'] = ((result1['日期'].apply(lambda x: result1[(x - pd.Timedelta(days=window_size) <= result1['日期']) & (result1['日期'] <= x)]['信用利差'].rank(pct=True).iloc[-1]))*100).round(2)
    result1.dropna(how='any',inplace=True)
    result1=result1.iloc[400:]
    df['DT'] = pd.to_datetime(df['DT'])
    df.set_index('DT', inplace=True)
    date_range = pd.date_range(start=df.index.min(), end=df.index.max())
    df = df.reindex(date_range)
    df['行业景气度-高频指标分位点'] = df['分位点'].interpolate(method='linear')
    df.ffill(inplace=True)
    df.reset_index(inplace=True)
    df.rename(columns={'index': '日期'}, inplace=True)
    # df['高频指标分位点'] = ((df['日期'].apply(lambda x: df[(x - pd.Timedelta(days=window_size) <= df['日期']) & (df['日期'] <= x + pd.Timedelta(days=window_size))]['高频指标'].rank(pct=True).iloc[-1]))*100).round(2)

    df.dropna(how='any',inplace=True)
    result1=result1.merge(df[['日期','行业景气度-高频指标分位点']],on=['日期'],how='left')
    if result1.empty:
        continue
    result1.ffill(inplace=True)
    result1['信用风险暴露程度']=result1['信用利差分位点']+result1['行业景气度-高频指标分位点']
    result1['信用风险暴露程度分位点'] = ((result1['日期'].apply(lambda x: result1[(x - pd.Timedelta(days=window_size) <= result1['日期']) & (result1['日期'] <= x)]['信用风险暴露程度'].rank(pct=True).iloc[-1]))*100).round(2)
    # result1['信用利差分位点']=result1['信用利差分位点'].rolling(window=90, min_periods=1).mean()
    # result1['信用风险暴露程度分位点']=result1['信用风险暴露程度分位点'].rolling(window=90, min_periods=1).mean()
    result1['行业']=hy
    result_df = pd.DataFrame(result1.iloc[-1]).transpose()
    try:
        result_df.to_sql('行业信用风险指数', conns1, if_exists='append', index=False)
    except:
        continue

sql_engine1.commit()
    






