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


# 获取两个表的列名
finance_columns = pd.read_sql("SHOW COLUMNS FROM basicinfo_finance", conn)
rate_columns = pd.read_sql("SHOW COLUMNS FROM basicinfo_rate", conn)

# 找出两个表共有的列
common_columns = set(finance_columns['Field']).intersection(set(rate_columns['Field']))

# 构建查询语句
select_query = f"""
    SELECT {', '.join(common_columns)} FROM basicinfo_finance 
    WHERE ths_ths_bond_third_type_bond IN ('中国农业发展银行', '中国进出口银行', '国家开发银行') or trade_code like '%%xxxxxxxx%%'
"""

# 从 basicinfo_finance 表中读取数据
data = pd.read_sql(select_query, conn)

# 将数据迁移到 basicinfo_rate 表
# data.to_sql('basicinfo_rate', conn, if_exists='append', index=False)
insert_database(data, 'bond.basicinfo_rate', [])

# 删除 basicinfo_finance 表中迁移走的数据
delete_query = f"""
    DELETE FROM basicinfo_finance 
    WHERE ths_ths_bond_third_type_bond IN ('中国农业发展银行', '中国进出口银行', '国家开发银行') or trade_code like '%%xxxxxxxx%%'
"""
conn.execute(delete_query)
conn.close()