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

# 删除 basicinfo_finance 表中迁移走的数据
delete_query = f"""
    DELETE FROM basicinfo_finance 
    WHERE TRADE_CODE IN (SELECT TRADE_CODE from basicinfo_rate)
"""
conn.execute(delete_query)
conn.close()