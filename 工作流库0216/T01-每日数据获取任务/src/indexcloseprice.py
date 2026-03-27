import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

warnings.filterwarnings('ignore')
from dateutil.relativedelta import relativedelta

sql_config = {
    'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'hz_work',
    'passwd': 'Hzinsights2015',
    'db': 'bond',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

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
    if mode == 'UPDATE':
        col = raw.columns.tolist()
        col2 = col.copy()
        if len(key_list) > 0:
            for key in key_list:
                col2.remove(key)

        update_str = ','.join(f'`{x}` = VALUES(`{x}`)' for x in col2)
        SQL.executemany(
            f"INSERT INTO {db} (`{'`,`'.join(x for x in col)}`) VALUES (%s{', %s' * (len(raw.columns) - 1)}) ON DUPLICATE KEY UPDATE {update_str}",
            values)

    elif mode == 'REPLACE':
        SQL.executemany(
            f"REPLACE INTO {db} VALUES (%s{', %s' * (len(final_table.columns) - 1)})", values)

    else:
        raise Exception('SELECT MODE IN (UPDATE, REPLACE)')


# from sql_conns import *

####iFIND日频期货更新####
#conns = conn

# sql = f"""SELECT TRADE_CODE FROM EDB.EDBINFO_THS WHERE REMARK ='THS_T'"""  ###T是交易数据
# raw = pd.read_sql(sql, conns)
# ths_list = list(raw['TRADE_CODE'].values)

bgn_date_d = '1900-01-01'
import iFinDPy as THS

THS.THS_iFinDLogin('hznd002', '160401')
# THS.THS_iFinDLogin('hzmd112', '992555')
# THS.THS_iFinDLogin('wanfj002', '666888')
_df = pd.read_sql("""SELECT 
    ic.trade_code,
    COALESCE(MAX(icp.dt), '1900-01-01') AS dt
FROM 
    indexcode ic
LEFT JOIN 
    bond.indexcloseprice icp ON ic.trade_code = icp.trade_code
GROUP BY 
    ic.trade_code""", conns)

for i, row in _df[:].iterrows():
    #     temp = THS.THS_HistoryQuotes (i, 'close', 'Interval:D,CPS:1,baseDate:1900-01-01,Currency:YSHB,fill:Previous',
    #                                   bgn_date_d, end_date_d, True)
    #     data = THS.THS_Trans2DataFrame (temp)
    # data = THS.THS_EDB(row['trade_code'], '', row['dt'].strftime('%F'), end_date_d)
    data = THS.THS_DS(row['trade_code'],'ths_close_price_index','','block:history', row['dt'], datetime.datetime.today().strftime('%F'))
    print(11111, data)
    if not data.data.empty:
        df = pd.DataFrame()
        df = data.data[['thscode', 'time', 'ths_close_price_index']].rename(columns={'thscode': 'TRADE_CODE', 'time': 'DT', 'ths_close_price_index': 'CLOSE'})
        insert_database(df.fillna(''), 'bond.indexcloseprice', ['DT', 'TRADE_CODE'])