
import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

warnings.filterwarnings('ignore')
from iFinDPy import *


#用户在使用时请修改成自己的账号和密码
thsLogin = THS_iFinDLogin('hznd002', '160401')
# thsLogin = THS_iFinDLogin('nylc082', '491448')
# thsLogin = THS_iFinDLogin('hzqh173', '13b5a6')
# thsLogin = THS_iFinDLogin('wanfj002', 'wan123')
#thsLogin=('','')
if(thsLogin == 0 or thsLogin == -201):
    print('登陆成功')
else:
    print("登录失败", thsLogin)


import datetime



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
            'stock',
        )
    )
conn = sql_engine.connect()

conns = pymysql.connect(**sql_config)
conns.autocommit(1)
SQL = conns.cursor()


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
        SQL.executemany(f"INSERT INTO {db} (`{'`,`'.join(x for x in col)}`) VALUES (%s{', %s' * (len(raw.columns) - 1)}) ON DUPLICATE KEY UPDATE {update_str}", processed_values)

    elif mode == 'REPLACE':
        SQL.executemany(
            f"REPLACE INTO {db} VALUES (%s{', %s' * (len(final_table.columns) - 1)})", processed_values)

    else:
        raise Exception('SELECT MODE IN (UPDATE, REPLACE)')


def insert_update_info(_df: pd.DataFrame, table_name: str, source: str):
    pd.DataFrame([[_df.shape[0], table_name, _df.isna().sum().sum(), (_df.isna().sum() / _df.shape[0]).mean(), source.upper()]],
                 columns=['num', 'table_name', 'num_null', 'rate_null', 'source']).to_sql('dailyupdatesummary', index=False,
                                                                             if_exists='append', con=conn)


def CJ(left, right):
    return (left.assign(key = 1).merge(right.assign(key = 1), on = 'key').drop('key', axis = 1))


def get_date(ago=0):
    return (datetime.datetime.today()-datetime.timedelta(days=ago)).strftime('%F')


def wind2table(d1, col):
        # d1 = w.wsd(codelist, col, start, end)
    d = pd.DataFrame(d1.Data)
    if len(d) != 1:
        d = d.T
    try:
        d.columns = d1.Codes
        d['DT'] = d1.Times
        # if len(d.columns) == len(d1.Codes):
        #     d.columns = d1.Codes
        #     d['DT'] = d1.Times
        # else:
        #     d['TRADE_CODE'] = d1.Codes
        #     d['DT'] = d1.Times[0]
        d2 = pd.DataFrame()
        d2[col] = d.set_index('DT').stack()
        d2 = d2.reset_index(drop=False)
        if d2.empty:
            return d2
        d2.columns = ['DT', 'TRADE_CODE', col]
    except:
        print(d, (d1, col))
        return pd.DataFrame()
    return d2


def wind_dataframe(wseedata, date):
    df = pd.DataFrame(wseedata.Data)
    df = df.T
    df['Code'] = wseedata.Codes
    df['DT'] = date
    wseedata.Fields.append('Code')
    wseedata.Fields.append('DT')
    df.columns = wseedata.Fields
    return df


def get_data_wind_wsd(codelist, col, start, end, option=''):
    from WindPy import w
    w.start()
    if option:
        d1 = w.wsd(codelist, col, start, end, option)
    else:
        d1 = w.wsd(codelist, col, start, end)
    return wind2table(d1, col)
    # d = pd.DataFrame(d1.Data).T


# rsp = w.wset('sectorconstituent', f"date={end};sectorid=a001010100000000;field=wind_code")
def get_data_wind_wset(col, parameter, date):
    from WindPy import w
    w.start()
    d1 = w.wset(col, parameter)
    print(d1)
    return wind_dataframe(d1, date)


# rsp = w.wss("836395.BJ", "tax,cash_recp_sg_and_rs","unit=1;rptDate=20211231;rptType=1")
def get_data_wind_wss(code, parameter1, parameter2='', date=''):
    from WindPy import w
    w.start()
    if (parameter2 == '') and (date == ''):
        d1 = w.wss(code, parameter1)
    else:
        d1 = w.wss(code, parameter1, parameter2)
    return wind_dataframe(d1, date)


# THS_DP('finance','2022-09-16','date:Y,thscode:Y')
def get_data_ths_DP(col, date, parameter):
    from WindPy import w
    w.start()
    d1 = THS_DP(col, date, parameter)
    if d1.errorcode == 0:
        return d1.data
    else:
        print((col, date, parameter), d1.errmsg)

# THS_DS('000010.SZ','ths_margin_trading_amtb_stock','','','2022-09-15','2022-09-16')
def get_data_ths_DS(codelist, col, parameter1, parameter2, date1, date2):
    from WindPy import w
    w.start()
    d1 = THS_DS(codelist, col, parameter1, parameter2, date1, date2)
    if d1.errorcode == 0:
        return d1.data
    else:
        print((codelist, col, parameter1, parameter2, date1, date2), d1.errmsg)


def get_data_ths_BD(codelist, date, parameter):
    d1 = THS_BD(codelist, date, parameter)
    if d1.errorcode == 0:
        return d1.data
    else:
        print((codelist, date, parameter), d1.errmsg)


def get_data_ths_HQ(codelist, parameter1, parameter2, date1, date2):
    d1 = THS_HQ(codelist, parameter1, parameter2, date1, date2)
    if d1.errorcode == 0:
        return d1.data
    else:
        print((codelist, parameter1, parameter2, date1, date2), d1.errmsg)
