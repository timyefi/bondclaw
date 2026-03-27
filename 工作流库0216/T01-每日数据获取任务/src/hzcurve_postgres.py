import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine

warnings.filterwarnings('ignore')

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
            'bond',
        )
    )
conn = sql_engine.connect()

conns = pymysql.connect(**sql_config)
conns.autocommit(1)
SQL = conns.cursor()

import psycopg2
from psycopg2.extras import execute_values
postgres_config = {
    'host': '139.224.201.106',
    'user': 'postgres',
    'password': 'hzinsights2015',
    'dbname': 'tsdb',
    'port': '18032'
}
postgres_conn = psycopg2.connect(**postgres_config)
postgres_cursor = postgres_conn.cursor()


mysql_conn = conn


def get_unique_dates(mysql_conn, table_name):
    query = f"SELECT DISTINCT DT FROM {table_name} order by dt desc limit 3"
    df = pd.read_sql(query, mysql_conn)
    return df['DT'].sort_values().tolist()

def migrate_data_to_postgres(mysql_conn, engine, table_names, target_table):
    # 从第一个表名中提取目标 PostgreSQL 表名
    target_pg_table = table_names[0].split('.')[1].split('_')[0] + '_' + table_names[0].split('.')[1].split('_')[1]
    suffix_to_target_term_value = {
        "05": 0.5,
        "175": 1.75,
        "0083":0.083,
        "025":0.25,
        "075":0.75
    }

    for table_name in table_names:
        unique_dates = get_unique_dates(mysql_conn, table_name)
        suffix = table_name.split('_')[-1]
        target_term_value = suffix_to_target_term_value.get(suffix, int(suffix))

        # query = f"SELECT * FROM {table_name} "
        # df = pd.read_sql(query, mysql_conn)

        # if not df.empty:
        #     df['target_term'] = target_term_value

        #     # 准备批量插入的数据
        #     data = df[['DT', 'TRADE_CODE', 'balance', 'imrating_calc', 'target_term', 'stdyield']].values.tolist()

        #     # 构建 INSERT 语句
        #     insert_query = '''
        #         INSERT INTO public.hzcurve_credit (dt, trade_code, balance, imrating_calc, target_term, stdyield)
        #         VALUES %s
        #     '''
        #     # 执行批量插入
        #     execute_values(engine, insert_query, data)

        for date in unique_dates:
            # 读取特定日期的数据
            query = f"SELECT * FROM {table_name} WHERE DT = '{date}'"
            df = pd.read_sql(query, mysql_conn)

            print(date, target_term_value, target_pg_table)


            if not df.empty:
                df['target_term'] = target_term_value

                # 准备批量插入的数据
                data = df[['DT', 'TRADE_CODE', 'balance', 'imrating_calc', 'target_term', 'stdyield']].values.tolist()

                # 构建 INSERT 语句
                insert_query = '''
                    INSERT INTO public.target_table1111 (dt, trade_code, balance, imrating_calc, target_term, stdyield) 
                    VALUES %s ON CONFLICT (dt, trade_code, target_term) DO NOTHING
                '''.replace('target_table1111', target_table)
                # 执行批量插入
                execute_values(engine, insert_query, data)

        postgres_conn.commit()

#             if not df.empty:
#                 df['target_term'] = target_term_value

#                 # 将 DataFrame 写入指定的 PostgreSQL 表
#                 df.to_sql(target_pg_table, engine, if_exists='append', index=False)

# 待迁移的表名列表
table_names1 = ['bond.hzcurve_credit_0083','bond.hzcurve_credit_025','bond.hzcurve_credit_05',  'bond.hzcurve_credit_075','bond.hzcurve_credit_1', 'bond.hzcurve_credit_175','bond.hzcurve_credit_2','bond.hzcurve_credit_3','bond.hzcurve_credit_4','bond.hzcurve_credit_5','bond.hzcurve_credit_7','bond.hzcurve_credit_10', 'bond.hzcurve_credit_15', 'bond.hzcurve_credit_20', 'bond.hzcurve_credit_30']
table_names2 = ['bond.hzcurve_abs_0083','bond.hzcurve_abs_025', 'bond.hzcurve_abs_05', 'bond.hzcurve_abs_075', 'bond.hzcurve_abs_1', 'bond.hzcurve_abs_175','bond.hzcurve_abs_2','bond.hzcurve_abs_3','bond.hzcurve_abs_4','bond.hzcurve_abs_5','bond.hzcurve_abs_7','bond.hzcurve_abs_10', 'bond.hzcurve_abs_15', 'bond.hzcurve_abs_20', 'bond.hzcurve_abs_30']
table_names3 = ['bond.hzcurve_finance_0083','bond.hzcurve_finance_025','bond.hzcurve_finance_05','bond.hzcurve_finance_075','bond.hzcurve_finance_1', 'bond.hzcurve_finance_175','bond.hzcurve_finance_2','bond.hzcurve_finance_3','bond.hzcurve_finance_4','bond.hzcurve_finance_5', 'bond.hzcurve_finance_7','bond.hzcurve_finance_10', 'bond.hzcurve_finance_15', 'bond.hzcurve_finance_20', 'bond.hzcurve_finance_30']
# table_names = ['bond.hzcurve_credit_05']

# 执行数据迁移
migrate_data_to_postgres(mysql_conn, postgres_cursor, table_names1+table_names2+table_names3, 'hzcurve_credit')