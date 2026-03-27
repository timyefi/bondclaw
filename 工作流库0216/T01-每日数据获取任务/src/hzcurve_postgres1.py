# import warnings
# import numpy as np
# import pandas as pd
# import pymysql
# from sqlalchemy import create_engine

# warnings.filterwarnings('ignore')

# import datetime

# sql_config = {

# }

# sql_engine = create_engine(
#         'mysql+pymysql://%s:%s@%s:%s/%s' % (
#             'hz_work',
#             'Hzinsights2015',
#             'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
#             '3306',
#             'bond',
#         )
#     )
# conn = sql_engine.connect()

# conns = pymysql.connect(**sql_config)
# conns.autocommit(1)
# SQL = conns.cursor()

# import psycopg2
# from psycopg2.extras import execute_values
# postgres_config = {

# }
# postgres_conn = psycopg2.connect(**postgres_config)
# postgres_cursor = postgres_conn.cursor()

# mysql_conn = conn

from multiprocessing import Pool
from sqlalchemy.pool import QueuePool
import logging
import warnings
import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from psycopg2.extras import execute_values
import psycopg2

warnings.filterwarnings('ignore')


def create_mysql_connection():
    """创建MySQL连接"""
    sql_config = {
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': 3306,
        'user': 'hz_work',
        'passwd': 'Hzinsights2015',
        'db': 'stock',
        'charset': 'utf8',
        'cursorclass': pymysql.cursors.DictCursor
    }
    return pymysql.connect(**sql_config)


def create_postgres_connection():
    """创建PostgreSQL连接"""
    postgres_config = {
        'host': '139.224.201.106',
        'user': 'postgres',
        'password': 'hzinsights2015',
        'dbname': 'tsdb',
        'port': '18032'
    }
    return psycopg2.connect(**postgres_config)


# 定义表名映射关系
suffix_to_target_term_value = {
    "05": 0.49999999799999995,
    "175": 1.75,
    "025": 0.25,
    "075": 0.75,
    "0083": 0.083,
}


def get_date_range_and_count(mysql_conn, table_name):
    """获取数据的日期范围和总记录数"""
    query = f"""
        SELECT 
            MIN(DT) as min_date, 
            MAX(DT) as max_date, 
            CAST(COUNT(*) AS SIGNED) as total_count 
        FROM {table_name}
        where DT >= '2024-01-01' and DT <= '2024-10-01'
    """
    try:
        cursor = mysql_conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        return {
            'min_date': result['min_date'],
            'max_date': result['max_date'],
            'total_count': int(result['total_count'])
        }
    except Exception as e:
        print(f"Error querying {table_name}: {str(e)}")
        raise
    finally:
        cursor.close()


def split_date_ranges(start_date, end_date, num_splits):
    """将时间范围均匀分割成指定数量的区间"""
    date_range = pd.date_range(start_date, end_date, periods=num_splits + 1)
    return [(date_range[i].strftime('%Y-%m-%d'),
             date_range[i + 1].strftime('%Y-%m-%d'))
            for i in range(len(date_range) - 1)]


def auto_split_date_ranges(mysql_conn, table_names, desired_chunks=3):
    """自动计算合适的时间区间分割"""
    all_min_dates = []
    all_max_dates = []
    total_records = 0

    for table_name in table_names[:1]:
        stats = get_date_range_and_count(mysql_conn, table_name)
        all_min_dates.append(pd.to_datetime(stats['min_date']))
        all_max_dates.append(pd.to_datetime(stats['max_date']))
        total_records += stats['total_count']

    start_date = min(all_min_dates)
    end_date = max(all_max_dates)

    print(f"Total date range: {start_date} to {end_date}")
    print(f"Total records: {total_records}")

    return split_date_ranges(start_date, end_date, desired_chunks)

def check_completion_for_range(mysql_conn, pg_keys_by_term, table_names, start_date, end_date):
    """检查特定时间范围内的完成情况"""
    suffix_to_target_term_value = {
        "05": 0.49999999799999995,
        "175": 1.75,
        "025": 0.25,
        "075": 0.75,
        "0083": 0.083,
    }
    
    results = []
    for table_name in table_names:
        suffix = table_name.split('_')[-1]
        target_term_value = suffix_to_target_term_value.get(
            suffix, float(suffix) if suffix.isdigit() else suffix)
        
        mysql_cursor = mysql_conn.cursor()
        mysql_query = f"""
            SELECT DT, TRADE_CODE
            FROM {table_name} 
            WHERE DT >= '{start_date}' 
            AND DT < '{end_date}'
        """
        mysql_cursor.execute(mysql_query)
        mysql_keys = set((row['DT'].strftime('%Y-%m-%d'), row['TRADE_CODE']) 
                       for row in mysql_cursor.fetchall())
        
        pg_keys = set((dt, code) for dt, code in pg_keys_by_term.get(target_term_value, set())
                     if start_date <= dt < end_date)
        
        missing_keys = mysql_keys - pg_keys
        total_keys = len(mysql_keys)
        missing_count = len(missing_keys)
        completion_rate = ((total_keys - missing_count) / total_keys * 100) if total_keys > 0 else 0
        
        print(f"\n{table_name} (term={target_term_value}):")
        print(f"Total records in MySQL for this range: {total_keys}")
        print(f"Missing records: {missing_count}")
        print(f"Completion rate: {completion_rate:.2f}%")
        
        results.append({
            'table_name': table_name,
            'missing_keys': missing_keys,
            'completion_rate': completion_rate,
            'target_term': target_term_value
        })
        
        mysql_cursor.close()
    
    return results


# 定义表名列表
table_names1 = [
    'bond.hzcurve_credit_0083', 'bond.hzcurve_credit_025',
    'bond.hzcurve_credit_05', 'bond.hzcurve_credit_075',
    'bond.hzcurve_credit_1', 'bond.hzcurve_credit_175',
    'bond.hzcurve_credit_2', 'bond.hzcurve_credit_3', 'bond.hzcurve_credit_4',
    'bond.hzcurve_credit_5', 'bond.hzcurve_credit_7', 'bond.hzcurve_credit_10',
    'bond.hzcurve_credit_15', 'bond.hzcurve_credit_20',
    'bond.hzcurve_credit_30'
]
table_names1 = []
table_names2 = [
    'bond.hzcurve_abs_0083', 'bond.hzcurve_abs_025', 'bond.hzcurve_abs_05',
    'bond.hzcurve_abs_075', 'bond.hzcurve_abs_1', 'bond.hzcurve_abs_175',
    'bond.hzcurve_abs_2', 'bond.hzcurve_abs_3', 'bond.hzcurve_abs_4',
    'bond.hzcurve_abs_5', 'bond.hzcurve_abs_7', 'bond.hzcurve_abs_10',
    'bond.hzcurve_abs_15', 'bond.hzcurve_abs_20', 'bond.hzcurve_abs_30'
]

table_names3 = [
    'bond.hzcurve_finance_0083', 'bond.hzcurve_finance_025',
    'bond.hzcurve_finance_05', 'bond.hzcurve_finance_075',
    'bond.hzcurve_finance_1', 'bond.hzcurve_finance_175',
    'bond.hzcurve_finance_2', 'bond.hzcurve_finance_3',
    'bond.hzcurve_finance_4', 'bond.hzcurve_finance_5',
    'bond.hzcurve_finance_7', 'bond.hzcurve_finance_10',
    'bond.hzcurve_finance_15', 'bond.hzcurve_finance_20',
    'bond.hzcurve_finance_30'
]

def get_all_pg_keys(postgres_conn, start_date, end_date):
    """获取指定日期范围内的PG主键"""
    pg_cursor = postgres_conn.cursor()
    try:
        pg_query = """
            SELECT dt, trade_code, target_term
            FROM public.hzcurve_credit
            WHERE dt >= %s AND dt < %s
        """
        pg_cursor.execute(pg_query, (start_date, end_date))
        
        pg_keys_by_term = {}
        for row in pg_cursor.fetchall():
            dt, trade_code, term = row
            dt_str = dt.strftime('%Y-%m-%d')
            if term not in pg_keys_by_term:
                pg_keys_by_term[term] = set()
            pg_keys_by_term[term].add((dt_str, trade_code))
        
        print(f"Loaded PG keys for range {start_date} to {end_date}, total terms: {len(pg_keys_by_term)}")
        return pg_keys_by_term
    finally:
        pg_cursor.close()

def process_date_range_batch(params):
    start_date, end_date, table_names, target_table, batch_size = params
    
    try:
        mysql_conn = create_mysql_connection()
        postgres_conn = create_postgres_connection()
        
        print(f"\nProcessing range {start_date} to {end_date}")
        
        # 只获取当前时间范围的PG键
        pg_keys = get_all_pg_keys(postgres_conn, start_date, end_date)
        
        results = check_completion_for_range(
            mysql_conn, 
            pg_keys, 
            table_names, 
            start_date, 
            end_date
        )
        
        # 处理未完成的表
        for status in results:
            if status['completion_rate'] < 99.9:
                table_name = status['table_name']
                missing_keys = status['missing_keys']
                
                if missing_keys:
                    # 将missing_keys分批处理
                    missing_keys_list = list(missing_keys)
                    for i in range(0, len(missing_keys_list), batch_size):
                        batch_keys = missing_keys_list[i:i + batch_size]
                        missing_dates = "','".join(key[0] for key in batch_keys)
                        missing_codes = "','".join(key[1] for key in batch_keys)
                        
                        query = f"""
                            SELECT 
                                DT, 
                                TRADE_CODE, 
                                balance, 
                                imrating_calc, 
                                stdyield
                            FROM {table_name} 
                            WHERE (DT, TRADE_CODE) IN (
                                SELECT DT, TRADE_CODE 
                                FROM {table_name}
                                WHERE DT IN ('{missing_dates}')
                                AND TRADE_CODE IN ('{missing_codes}')
                            )
                        """
                        
                        cursor = mysql_conn.cursor()
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        cursor.close()
                        
                        processed_data = []
                        for row in rows:
                            dt = row['DT'].strftime('%Y-%m-%d') if hasattr(row['DT'], 'strftime') else row['DT']
                            processed_data.append([
                                dt,
                                row['TRADE_CODE'],
                                row['balance'],
                                row['imrating_calc'],
                                status['target_term'],
                                row['stdyield']
                            ])
                        
                        if processed_data:
                            insert_query = f'''
                                INSERT INTO public.{target_table} 
                                (dt, trade_code, balance, imrating_calc, target_term, stdyield)
                                VALUES %s 
                                ON CONFLICT (dt, trade_code, target_term) DO NOTHING
                            '''
                            
                            pg_cursor = postgres_conn.cursor()
                            try:
                                execute_values(pg_cursor, insert_query, processed_data)
                                postgres_conn.commit()
                                print(f"Processed {len(processed_data)} records for {table_name}")
                            finally:
                                pg_cursor.close()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()


from tqdm import tqdm
from multiprocessing import Pool, Manager

def process_with_progress(params):
    """包装处理函数，用于更新进度条"""
    try:
        process_date_range_batch(params)
        return True
    except Exception as e:
        print(f"Error processing range {params[0]} to {params[1]}: {str(e)}")
        return False

if __name__ == '__main__':
    # 获取日期范围
    mysql_conn = create_mysql_connection()
    date_ranges = auto_split_date_ranges(
        mysql_conn, 
        table_names1+table_names2+table_names3,
        desired_chunks=50
    )
    mysql_conn.close()
    
    # 准备参数
    params = [(start, end, table_names1+table_names2+table_names3, 
               'hzcurve_credit', 100000) 
              for start, end in date_ranges]
    
    total_chunks = len(params)
    print(f"Total chunks to process: {total_chunks}")
    
    # 使用进程池处理，带进度条
    with Pool(processes=min(total_chunks, 50)) as pool:
        try:
            # 使用tqdm显示进度
            results = list(tqdm(
                pool.imap_unordered(process_with_progress, params),
                total=total_chunks,
                desc="Processing chunks",
                unit="chunk"
            ))
            
            # 统计处理结果
            successful = sum(1 for x in results if x)
            failed = sum(1 for x in results if not x)
            
            print("\nProcessing completed:")
            print(f"Successfully processed: {successful} chunks")
            print(f"Failed: {failed} chunks")
            
        except Exception as e:
            print(f"Error in main process: {str(e)}")
            raise