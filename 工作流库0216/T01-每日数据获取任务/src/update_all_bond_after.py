import datetime
import os
import warnings
import numpy as np
import pandas as pd
import pymysql

from sqlalchemy import create_engine
import pandas as pd

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


query_tables = """
SELECT DISTINCT TABLE_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA IN ('bond', 'company');
"""

tables_df = pd.read_sql(query_tables, conn)

like_clauses = [f"python_code LIKE '%%{table_name}%%'" for table_name in tables_df['TABLE_NAME']]
conditions = " OR ".join(like_clauses)
final_query = f"SELECT id, title FROM vmp.chart_info WHERE {conditions};"
final = pd.read_sql(final_query, conn)
final['id'].to_list()


import json 
import redis

# 创建 Redis 连接对象
def create_redis_client(host='47.102.110.133', port=6379, db=0, password="hzinsights",):
    return redis.Redis(host=host, port=port, db=db, password=password)

# 执行 Redis 命令
def execute_command(command, *args, **options):
    client = create_redis_client()
    try:
        response = client.execute_command(command, *args, **options)
        return response
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return None

collections = []
data = json.loads(execute_command("GET", "vmp_server_FiContent_data"))
for section_key, section_value in data.items():
    if isinstance(section_value, dict):
        for subsection_key, subsection_value in section_value.items():
            if isinstance(subsection_value, dict):
                for inner_key, inner_value in subsection_value.items():
                    if 'Collections' in inner_key:
                        collections.extend(inner_value)

# 去除重复元素并排序
collections_list = sorted(set(collections))

import requests

def send_request(chart_ids, collections_list):
    url_preheat = "https://file2html.internal.hzinsights.com/api/tasks/preheat"
    # url_cleanCache = "https://file2html.internal.hzinsights.com/api/tasks/cleanCache"
    headers = {'Content-Type': 'application/json'}
    data = {
        "charts": chart_ids,
        # "articles": [10507],
        "collections": collections_list
    }
    
    # 发送预热的请求
    response_preheat = requests.post(url_preheat, json=data, headers=headers)
    print("预热响应状态码:", response_preheat.status_code)
    print("预热响应内容:", response_preheat.text)
    
    # 发送清除缓存的请求
    # response_cleanCache = requests.post(url_cleanCache, json=data, headers=headers)
    # print("清除缓存响应状态码:", response_cleanCache.status_code)
    # print("清除缓存响应内容:", response_cleanCache.text)

if __name__ == "__main__":
    send_request(final['id'].to_list(), collections_list)
