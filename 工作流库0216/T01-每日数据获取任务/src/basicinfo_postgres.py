import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

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


# 清空 PostgreSQL 表
def clear_postgres_table(table_name, postgres_conn):
    try:
        cursor = postgres_conn.cursor()
        cursor.execute(f"DELETE FROM {table_name}")
        postgres_conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error clearing PostgreSQL table: {e}")


# 数据迁移函数
def migrate_data(mysql_table, postgres_table, mysql_engine=conn, postgres_conn=postgres_conn):
# def migrate_data(mysql_table, postgres_table, mysql_engine, postgres_conn):
    try:
        # 从 MySQL 读取数据
        df = pd.read_sql(f"SELECT * FROM {mysql_table}", mysql_engine)

        # 清空 PostgreSQL 表
        clear_postgres_table(postgres_table, postgres_conn)

        # 将 DataFrame 转换为元组列表
        data_tuples = list(df.itertuples(index=False, name=None))

        # 构建 SQL 插入语句
        # 注意: 字段名需要与 PostgreSQL 表字段名匹配
        columns = ', '.join(df.columns)
        insert_query = f'INSERT INTO {postgres_table} ({columns}) VALUES %s'

        # 使用 psycopg2 进行批量插入
        cursor = postgres_conn.cursor()
        execute_values(cursor, insert_query, data_tuples)
        postgres_conn.commit()
        cursor.close()

        print(f"Data migrated successfully from {mysql_table} to {postgres_table}")

    except (psycopg2.Error, pd.io.sql.DatabaseError) as e:
        print(f"Error in data migration: {e}")


# 执行数据迁移
for i in ['bond.basicinfo_abs',
'bond.basicinfo_credit',
'bond.basicinfo_finance',
'bond.basicinfo_xzqh_ct',
'bond.basicinfo_industrytype1']:
    # print()
    migrate_data(i, i.split('.')[1])