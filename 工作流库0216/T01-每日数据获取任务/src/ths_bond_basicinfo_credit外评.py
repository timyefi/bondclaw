import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

from sqlalchemy import create_engine
import pandas as pd

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

sql_engine = create_engine(
        'mysql+pymysql://%s:%s@%s:%s/%s' % (
            'hz_work',
            'Hzinsights2015',
            'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            '3306',
            'bond',
        )
    )
conns = sql_engine.connect()


import iFinDPy as THS
from sql_conns_new import insert_update_info, insert_database
THS.THS_iFinDLogin('hzmd311','1a536a')
# THS.THS_iFinDLogin('hzmd112', '992555')

edate, sdate = [i.strftime('%Y%m%d') for i in pd.read_sql("select DT from stock.indexcloseprice where trade_code = '881001.WI' order by DT desc limit 2", conns).T.values[0]]
df1 = THS.THS_DR('p04521',f'p1=1;pgjg=1,2,3,4,5,6,7,8,9,10,11;p2=0;zqlx=640004,640005,640007,640008,640009,640010,640011,640012,640014,640018,640021;sdate={sdate};edate={edate};jyzt=0;jzsdpjzq=0;sfwy=0','p04521_f001:Y,p04521_f002:N,p04521_f009:N,p04521_f003:N,p04521_f006:Y','format:dataframe')
df2 = THS.THS_DR('p04521',f'p1=1;pgjg=1,2,3,4,5,6,7,8,9,10,11;p2=2;zqlx=640004,640005,640007,640008,640009,640010,640011,640012,640014,640018,640021;sdate={sdate};edate={edate};jyzt=0;jzsdpjzq=0;sfwy=0','p04521_f001:Y,p04521_f002:N,p04521_f009:N,p04521_f003:N,p04521_f006:Y','format:dataframe')

df1.data.columns = ['TRADE_CODE', 'rating_issuer']
df2.data.columns = ['TRADE_CODE', 'rating_bond']

insert_database(df1.data.fillna(''), 'bond.basicinfo_外评', ['TRADE_CODE'])
insert_database(df2.data.fillna(''), 'bond.basicinfo_外评', ['TRADE_CODE'])
insert_update_info(df1.data.fillna(''), 'bond.basicinfo_外评', 'THS')
insert_update_info(df2.data.fillna(''), 'bond.basicinfo_外评', 'THS')
#df.data.to_sql('dealtinfo', conns, if_exists='append', index=False)
# df.data