import pymysql
import pandas as pd

# 数据库连接
print("连接数据库...")
conn = pymysql.connect(
    host='rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    user='hz_work',
    password='Hzinsights2015',
    database='yq',
    port=3306
)

try:
    # 获取转型城投清单
    print("\n获取转型城投清单...")
    query = """
    select distinct 公司名称 
    from yq.城投平台市场化经营主体
    union
    select distinct 公司名称 
    from yq.城投平台退出
    where 披露日期>='2023-10-26'
    """
    print(f"\n执行查询: {query}")
    df = pd.read_sql(query, conn)
    print(f"\n获取到 {len(df)} 家转型城投")
    
    if len(df) > 0:
        print("\n样例公司:")
        print(df.head())
    
except Exception as e:
    print(f"出错: {e}")
finally:
    conn.close() 