import pymysql
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import numpy as np
import sys
import traceback

def get_transform_companies(conn):
    """获取转型城投清单"""
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
    companies = df['公司名称'].tolist()
    print(f"\n获取到 {len(companies)} 家转型城投")
    return companies

def get_usage_data(conn, table_name, companies=None, is_sample=False, sample_size=100):
    """获取募集资金用途数据"""
    where_clause = "WHERE 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"
    if companies:
        companies_str = "','".join(companies)
        where_clause += f" AND 发行人 IN ('{companies_str}')"
    elif is_sample:
        where_clause += f" LIMIT {sample_size}"
    
    query = f"""
    SELECT 
        发行人,
        公告日期,
        `发行规模(亿)` as total_size,
        `借新还旧(亿)` as refinance,
        `偿还有息债务(亿)` as debt_repay,
        `补充流动资金(亿)` as working_capital,
        `项目建设(亿)` as project_build,
        `其他(亿)` as others,
        主体评级,
        省份,
        地级市
    FROM {table_name}
    {where_clause}
    """
    print(f"\n执行查询: {query}")
    
    df = pd.read_sql(query, conn)
    print(f"\n获取到 {len(df)} 条记录")
    
    # 转换数值列
    numeric_columns = ['total_size', 'refinance', 'debt_repay', 
                      'working_capital', 'project_build', 'others']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def main():
    """主函数"""
    try:
        # 连接数据库
        print("连接数据库...")
        conn = pymysql.connect(
            host='rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            user='hz_work',
            password='Hzinsights2015',
            database='yq',
            port=3306
        )
        
        # 获取转型城投清单
        print("\n获取转型城投清单...")
        transform_companies = get_transform_companies(conn)
        
        if transform_companies:
            # 获取各类数据
            print("\n获取转型城投(城投债)数据...")
            transform_urban = get_usage_data(conn, '城投募集资金用途', transform_companies)
            
            print("\n获取转型城投(产业债)数据...")
            transform_industry = get_usage_data(conn, '产业债募集资金用途', transform_companies)
            
            print("\n获取普通城投数据...")
            normal_urban = get_usage_data(conn, '城投募集资金用途', is_sample=True, sample_size=100)
            
            # 打印统计信息
            print("\n=== 数据统计 ===")
            print(f"转型城投(城投债)记录数: {len(transform_urban)}")
            print(f"转型城投(产业债)记录数: {len(transform_industry)}")
            print(f"普通城投记录数: {len(normal_urban)}")
            
            # 保存数据到CSV
            transform_urban.to_csv('transform_urban.csv', index=False)
            transform_industry.to_csv('transform_industry.csv', index=False)
            normal_urban.to_csv('normal_urban.csv', index=False)
            
            print("\n数据已保存到CSV文件")
            
        else:
            print("未获取到转型城投数据")
            
    except Exception as e:
        print(f"分析过程中出错: {e}")
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 