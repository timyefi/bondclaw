import pandas as pd
import sqlalchemy
import random
import scipy.stats as stats
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pywt
from IPython.display import display, HTML
import plotly.graph_objects as go
import pandas as pd
import pywt
import matplotlib.font_manager as fm
import matplotlib.animation as animation

import ipywidgets as widgets
from IPython.display import display, clear_output
import pandas as pd
import sqlalchemy
import random
import scipy.stats as stats
import pywt

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

basic_p=pd.read_sql("""select * from 产业跟踪指标信息""",conns1)

def 处理异常值(df):
    Q1 = df['CLOSE'].quantile(0.25)
    Q3 = df['CLOSE'].quantile(0.75)
    # 计算 IQR
    IQR = Q3 - Q1
    # 定义异常值为小于 Q1 - 1.5 * IQR 或大于 Q3 + 1.5 * IQR 的值
    outliers_indices = df[(df['CLOSE'] < (Q1 - 1.5 * IQR)) | (df['CLOSE'] > (Q3 + 1.5 * IQR))].index
    # 对于每个异常值
    df.loc[outliers_indices, 'CLOSE'] = np.nan
    # 插值
    df['CLOSE']=df['CLOSE'].interpolate(method='linear')
    df.ffill(inplace=True)
    df.bfill(inplace=True)

    df=df[['DT','CLOSE']]
    return df
def get_min_date(trade_codes):
    dates = [
        pd.read_sql(f"select max(DT) from edb.edbdata where TRADE_CODE ='{x}' ", cursor).values.tolist()[0][0]
        for x in trade_codes]
    dates.append(pd.to_datetime(dt).date())
    min_date = min(dates)
    return min_date

def 转12月移动平均年同比(trade_code, date_end, month_counts=12):
    df = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE= '{trade_code}' and DT<='{date_end}'",
        cursor)
    df=处理异常值(df)
    if df.empty:
        df=pd.DataFrame(columns=['DT','CLOSE'])
        df1=pd.DataFrame(columns=['DT','CLOSE'])
        return df,df1
    # 获取当前trade code的当月值
    df['DT'] = pd.to_datetime(df['DT'])
    df.set_index('DT', inplace=True)
    # 将数据重采样为月度数据，取每个月的最后一个值
    df = df.resample('M').last()
    df1=df.copy()
    # df['CLOSE'] = df['CLOSE'].rolling(12,min_periods=1).mean()
    # 计算年同比增长率
    df['CLOSE'] = df['CLOSE'].pct_change(12, fill_method=None) * 100
    df1['CLOSE'] = df1['CLOSE'].pct_change(12, fill_method=None) * 100
    date_range = pd.date_range(start=df.index.min(), end=df.index.max())
    df = df.reindex(date_range)
    df1 = df1.reindex(date_range)
    df['CLOSE'] = df['CLOSE'].interpolate(method='linear')
    df1['CLOSE'] = df1['CLOSE'].interpolate(method='linear')
    df.ffill(inplace=True)
    df1.ffill(inplace=True)
    df.reset_index(inplace=True)
    df1.reset_index(inplace=True)
    df.rename(columns={'index': 'DT'}, inplace=True)
    df1.rename(columns={'index': 'DT'}, inplace=True)
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    return df,df1

def 月同比12个月移动平均(trade_code, date_end):
    indicator_x = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT <='{date_end}' order by DT desc",
        cursor).sort_values('DT')
    indicator_x=处理异常值(indicator_x)
    if indicator_x.empty:
        indicator_x=pd.DataFrame(columns=['DT','CLOSE'])
        indicator_x1=pd.DataFrame(columns=['DT','CLOSE'])
        return indicator_x,indicator_x1
    indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
    indicator_x.set_index('DT', inplace=True)
    # 将数据重采样为月度数据，取每个月的最后一个值
    indicator_x = indicator_x.resample('M').mean()
    indicator_x1=indicator_x.copy()
    # indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(12,min_periods=1).mean()
    date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
    indicator_x = indicator_x.reindex(date_range)
    indicator_x1=indicator_x1.reindex(date_range)
    indicator_x['CLOSE'] = indicator_x['CLOSE'].interpolate(method='linear')
    indicator_x1['CLOSE'] = indicator_x1['CLOSE'].interpolate(method='linear')
    indicator_x.ffill(inplace=True)
    indicator_x1.ffill(inplace=True)
    indicator_x.reset_index(inplace=True)
    indicator_x1.reset_index(inplace=True)
    indicator_x.rename(columns={'index': 'DT'}, inplace=True)
    indicator_x1.rename(columns={'index': 'DT'}, inplace=True)
    indicator_x.dropna(inplace=True)
    indicator_x1.dropna(inplace=True)
    indicator_x=indicator_x[['DT','CLOSE']]
    indicator_x1=indicator_x1[['DT','CLOSE']]
    return indicator_x,indicator_x1

def 百分制月环比转12月移动平均年同比(trade_code, date_end):
    indicator_x = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT <='{date_end}' order by DT desc",
        cursor).sort_values('DT')
    indicator_x=处理异常值(indicator_x)
    if indicator_x.empty:
        indicator_x=pd.DataFrame(columns=['DT','CLOSE'])
        indicator_x1=pd.DataFrame(columns=['DT','CLOSE'])
        return indicator_x,indicator_x1
    indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
    indicator_x.set_index('DT', inplace=True)
    # 将数据重采样为月度数据，取每个月的最后一个值
    indicator_x = indicator_x.resample('M').mean()
    indicator_x1=indicator_x.copy()
    # indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(12,min_periods=1).mean()
    indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(window=12).apply(lambda x: np.prod(x/100) - 1)*100
    indicator_x1['CLOSE']=indicator_x1['CLOSE'].rolling(window=12).apply(lambda x: np.prod(x/100) - 1)*100
    date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
    indicator_x = indicator_x.reindex(date_range)
    indicator_x1=indicator_x1.reindex(date_range)
    indicator_x['CLOSE'] = indicator_x['CLOSE'].interpolate(method='linear')
    indicator_x1['CLOSE'] = indicator_x1['CLOSE'].interpolate(method='linear')
    indicator_x.ffill(inplace=True)
    indicator_x1.ffill(inplace=True)
    indicator_x.reset_index(inplace=True)
    indicator_x1.reset_index(inplace=True)
    indicator_x.rename(columns={'index': 'DT'}, inplace=True)
    indicator_x1.rename(columns={'index': 'DT'}, inplace=True)
    indicator_x.dropna(inplace=True)
    indicator_x1.dropna(inplace=True)
    indicator_x=indicator_x[['DT','CLOSE']]
    indicator_x1=indicator_x1[['DT','CLOSE']]
    return indicator_x,indicator_x1

def get_value_cycle(df,period_cycle,period_trend,level):
    df['DT'] = pd.to_datetime(df['DT'])
    values = df['CLOSE'].values
    wavelet = pywt.Wavelet('db2')
    coeffs = pywt.wavedec(values, wavelet)
    level=int(level)
    period_cycle=int(period_cycle)
    period_trend=int(period_trend)
    recon = pywt.waverec(coeffs[:level+1] + [np.zeros_like(c) for c in coeffs[level+1:]], wavelet)
    if len(recon) < abs(period_cycle):
        recent_cycle = recon
    else:
        recent_cycle = recon[-period_cycle:]
    
    # period_cycle1=int(period_cycle/2)
    # #取最新一个周期两个分段
    # recent_cycle1 = recon[-period_cycle:-period_cycle1]
    # max_value1=max(recent_cycle1)
    # min_value1=min(recent_cycle1)
    # latest_value1 = recent_cycle1[-1]

    # recent_cycle2 = recon[-period_cycle1:]
    # max_value2=max(recent_cycle2)
    # min_value2=min(recent_cycle2)
    # latest_value2 = recent_cycle2[-1]

    # max_value=max(recent_cycle)
    # min_value=min(recent_cycle)
    latest_value = recon[-1]  # 获取最新的值
    # percentile=(latest_value-min_value)/(max_value-min_value)*100
    percentile = stats.percentileofscore(recent_cycle, latest_value)  # 计算最新值在最近周期内的百分位

    if len(recon) < abs(period_trend):
        trend_value = recon[-len(recon) + 1]
    else:
        trend_value = recon[-period_trend]  # 获取最近的趋势数据
    trend_diff = latest_value-trend_value  # 计算趋势数据的差分
    trend = 0
    if trend_diff > 0:
        trend = 1  # 向上
    elif trend_diff < 0:
        trend = -1  # 向下

    # data = recent_cycle2
    # slope = (data[-1] - data[0]) / (len(data) - 1)
    # intercept = data[0]

    # # 计算直线上每一点的y值
    # line_y = [slope * t + intercept for t in range(len(data))]

    # # 计算直线上的y值和数据的y值的差
    # diff = [d - l for d, l in zip(data, line_y)]

    # # 判断大部分的点是否在直线之下
    # if sum(d < 0 for d in diff) / len(diff) > 0.5:
    
    return percentile,trend

def 高频价格转12月移动平均月均价年同比(trade_code, date_end):
    indicator_x = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT<= '{date_end}' order by DT",
        cursor)
    if indicator_x.empty:
        df=pd.DataFrame(columns=['DT','CLOSE'])
        df1=pd.DataFrame(columns=['DT','CLOSE'])
        return df,df1
    indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
    indicator_x.set_index('DT', inplace=True)
    date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
    # 将数据重采样为月度数据，取每个月的最后一个值
    indicator_x = indicator_x.resample('M').mean()
    indicator_x1=indicator_x.copy()
    # indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(12,min_periods=1).mean()
    indicator_x['CLOSE'] = indicator_x['CLOSE'].pct_change(12, fill_method=None)*100
    indicator_x1['CLOSE'] = indicator_x1['CLOSE'].pct_change(12, fill_method=None)*100
    df=indicator_x
    df1=indicator_x1
    df = df.reindex(date_range)
    df1 = df1.reindex(date_range)
    
    df['CLOSE'] = df['CLOSE'].interpolate(method='linear')
    df1['CLOSE'] = df1['CLOSE'].interpolate(method='linear')
    df.ffill(inplace=True)
    df1.ffill(inplace=True)
    df.reset_index(inplace=True)
    df1.reset_index(inplace=True)
    df.rename(columns={'index': 'DT'}, inplace=True)
    df1.rename(columns={'index': 'DT'}, inplace=True)
    
    df=处理异常值(df)
    df1=处理异常值(df1)
    df=df[['DT','CLOSE']]
    df1=df1[['DT','CLOSE']]
    df.dropna(inplace=True)
    df1.dropna(inplace=True)
    return df,df1

def mom_trend(trade_code, date_end):
    # 白酒价格月环比数为100
    indicator_x = pd.read_sql(
        f"select DT, CLOSE/100-1 as CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT <='{date_end}' order by DT desc",
        cursor).sort_values('DT')
    indicator_x=处理异常值(indicator_x)
    if indicator_x.empty:
        indicator_x=pd.DataFrame(columns=['DT','CLOSE'])
        indicator_x1=pd.DataFrame(columns=['DT','CLOSE'])
        return indicator_x,indicator_x1
    indicator_x1=indicator_x.copy()
    # indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(3).mean()
    indicator_x=indicator_x[['DT','CLOSE']]
    indicator_x1=indicator_x1[['DT','CLOSE']]
    return indicator_x,indicator_x1

def 周度价格转12月移动平均年同比(trade_code, date_end):
    indicator_x = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT<= '{date_end}' order by DT desc",
        cursor).sort_values('DT')
    if indicator_x.empty:
        indicator_x=pd.DataFrame(columns=['DT','CLOSE'])
        indicator_x1=pd.DataFrame(columns=['DT','CLOSE'])
        return indicator_x,indicator_x1
    indicator_x=indicator_x.sort_values('DT')
    indicator_x['DT'] = pd.to_datetime(indicator_x['DT'])
    indicator_x.set_index('DT', inplace=True)
    indicator_x = indicator_x.resample('M').mean()
    indicator_x['CLOSE'] = indicator_x['CLOSE'].rolling(window=12).apply(lambda x: np.prod(x/100) - 1)*100
    date_range = pd.date_range(start=indicator_x.index.min(), end=indicator_x.index.max())
    indicator_x = indicator_x.reindex(date_range)
    indicator_x['CLOSE'] = indicator_x['CLOSE'].interpolate(method='linear')
    indicator_x.ffill(inplace=True)
    indicator_x.reset_index(inplace=True)
    indicator_x=处理异常值(indicator_x)
    indicator_x.rename(columns={'index': 'DT'}, inplace=True)
    indicator_x.dropna(inplace=True)
    indicator_x=indicator_x[['DT','CLOSE']]
    return indicator_x,indicator_x

def day_value_trend(trade_code, date_end, both_daily=0):
    this_month = pd.read_sql(f"select max(DT) from edb.edbdata where TRADE_CODE ='{trade_code}' and DT <='{date_end}'",
                        cursor)
    if this_month.empty:
        return pd.DataFrame(columns=['DT','CLOSE'])
    this_month = this_month.values.tolist()[0][0]
    if this_month.month > 3:
        last_month_start = datetime.date(this_month.year, this_month.month - 3, 1)
    else:
        last_month_start = datetime.date(this_month.year-1, this_month.month - 3+12, 1)
    if this_month.month == 12 and both_daily == 0:
        this_month_start = datetime.date(this_month.year+1, 1, 1)
    else:
        this_month_start = datetime.date(this_month.year, this_month.month + 1 - both_daily, 1)
    indicator_x = pd.read_sql(
        f"select DT, CLOSE from edb.edbdata where TRADE_CODE ='{trade_code}' and DT< '{this_month_start}'",
        cursor)
    indicator_x=处理异常值(indicator_x)
    indicator_x['month'] = indicator_x['DT'].apply(lambda x: x.month)
    indicator_x = indicator_x.groupby('month').last().sort_values('DT', ascending=False).reset_index(
        drop=True).sort_values('DT')
    indicator_x['CLOSE'] = indicator_x['CLOSE'].pct_change(1, fill_method=None)
    indicator_x=indicator_x[['DT','CLOSE']]
    return indicator_x

def cal_zb1(hy):
    period_cycle=basic_p[basic_p['行业']==hy]['周期天数'].iloc[0]
    period_trend=basic_p[basic_p['行业']==hy]['趋势天数'].iloc[0]
    level=basic_p[basic_p['行业']==hy]['level'].iloc[0]
    trade_code=basic_p[basic_p['行业']==hy]['trade_code'].iloc[0]
    name=basic_p[basic_p['行业']==hy]['名称'].iloc[0]
    date_end = get_min_date([trade_code])
    df = pd.read_sql(
    f"select DT, CLOSE from edb.edbdata where TRADE_CODE ={trade_code} and DT <='{date_end}' order by DT ASC",
    cursor)
    if df.empty:
        return pd.DataFrame(columns=['行业','指标名称','DT', '分位点', '趋势'])
    else:
        df=df.sort_values('DT')
        # 铁路运输业固定资产投资完成额 累计同比
        percentile,trend=get_value_cycle(df,period_cycle,period_trend,level)
        re = pd.DataFrame(columns=['行业','指标名称','DT', '分位点', '趋势'])
        re.loc[0] = [hy,name, df['DT'][-1], percentile,trend]
        return re
def cal_zb2(hy,df):
    period_cycle=basic_p[basic_p['行业']==hy]['周期天数'].iloc[0]
    period_trend=basic_p[basic_p['行业']==hy]['趋势天数'].iloc[0]
    level=basic_p[basic_p['行业']==hy]['level'].iloc[0]
    name=",".join(basic_p[basic_p['行业']==hy]['名称'])
    if df.empty:
        return pd.DataFrame(columns=['行业','指标名称','DT', '分位点', '趋势'])
    else:
        # 铁路运输业固定资产投资完成额 累计同比
        if len(df) < abs(period_cycle):
            return pd.DataFrame(columns=['行业','指标名称','DT', '分位点', '趋势'])
        percentile,trend=get_value_cycle(df,period_cycle,period_trend,level)
        dt1=df['DT'].iloc[-1]
        re = pd.DataFrame(columns=['行业','指标名称','DT', '分位点', '趋势'])
        re.loc[0] = [hy,name, dt1, percentile,trend]
        return re