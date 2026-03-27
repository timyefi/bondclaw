#!/usr/bin/env python3
"""
验证2025年上半年GDP数据是否成功导入到数据库表 china_fiscal_data_2017_2024 中
"""
import pandas as pd
from sqlalchemy import create_engine, text
import pymysql
import sys
import os

def get_db_connection():
    """获取数据库连接"""
    config = {
        'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        'port': 3306,
        'user': 'hz_work',
        'password': 'Hzinsights2015',
        'database': 'bond',
        'charset': 'utf8mb4'
    }
    
    connection_string = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
    engine = create_engine(connection_string, pool_recycle=3600)
    return engine

def execute_query(engine, query):
    """执行SQL查询并返回DataFrame"""
    try:
        with engine.connect() as conn:
            result = pd.read_sql(text(query), conn)
        return result
    except Exception as e:
        print(f"执行查询时出错: {e}")
        return pd.DataFrame()

def verify_gdp_data():
    """验证2025年上半年GDP数据"""
    print("开始验证2025年上半年GDP数据导入情况...")
    print("=" * 60)
    
    # 创建数据库连接
    engine = get_db_connection()
    
    # 1. 统计2025年的数据记录数
    print("1. 统计2025年的数据记录数")
    print("-" * 40)
    
    count_2025_query = """
    SELECT COUNT(*) as total_records
    FROM china_fiscal_data_2017_2024
    WHERE year = 2025
    """
    
    try:
        count_result = execute_query(engine, count_2025_query)
        if not count_result.empty:
            total_records = count_result.iloc[0]['total_records']
            print(f"2025年总记录数: {total_records}")
            
            # 按日期统计
            monthly_count_query = """
            SELECT dt, COUNT(*) as record_count
            FROM china_fiscal_data_2017_2024
            WHERE year = 2025
            GROUP BY dt
            ORDER BY dt
            """
            
            monthly_count = execute_query(engine, monthly_count_query)
            if not monthly_count.empty:
                print("2025年各日期记录数:")
                for _, row in monthly_count.iterrows():
                    print(f"  {row['dt']}: {row['record_count']}条")
            else:
                print("未找到2025年各日期数据")
        else:
            print("未找到2025年数据记录")
    except Exception as e:
        print(f"查询2025年记录数时出错: {e}")
    
    print()
    
    # 2. 显示GDP前10名的省份
    print("2. 显示2025年上半年GDP前10名的省份")
    print("-" * 40)
    
    top_gdp_query = """
    SELECT 
        province,
        SUM(CAST(gdp AS DECIMAL(20,2))) as total_gdp,
        COUNT(*) as record_count
    FROM china_fiscal_data_2017_2024
    WHERE year = 2025 AND gdp IS NOT NULL AND gdp != ''
    GROUP BY province
    ORDER BY total_gdp DESC
    LIMIT 10
    """
    
    try:
        top_gdp_result = execute_query(engine, top_gdp_query)
        if not top_gdp_result.empty:
            print("2025年上半年GDP前10名省份:")
            for i, (_, row) in enumerate(top_gdp_result.iterrows(), 1):
                print(f"  {i:2d}. {row['province']:12s} - {row['total_gdp']:>15,.2f}亿元 ({row['record_count']}条记录)")
        else:
            print("未找到2025年GDP数据")
    except Exception as e:
        print(f"查询GDP前10名时出错: {e}")
    
    print()
    
    # 3. 验证数据完整性
    print("3. 验证数据完整性")
    print("-" * 40)
    
    # 检查数据表中的年份范围
    year_range_query = """
    SELECT 
        MIN(year) as min_year,
        MAX(year) as max_year,
        COUNT(DISTINCT year) as year_count
    FROM china_fiscal_data_2017_2024
    """
    
    try:
        year_range = execute_query(engine, year_range_query)
        if not year_range.empty:
            min_year = year_range.iloc[0]['min_year']
            max_year = year_range.iloc[0]['max_year']
            year_count = year_range.iloc[0]['year_count']
            
            print(f"数据表中的年份范围: {min_year} - {max_year}")
            print(f"包含的年份数: {year_count}")
            
            # 检查2025年数据的省份覆盖情况
            province_coverage_query = """
            SELECT 
                COUNT(DISTINCT province) as province_count,
                GROUP_CONCAT(DISTINCT province ORDER BY province SEPARATOR ', ') as provinces
            FROM china_fiscal_data_2017_2024
            WHERE year = 2025
            """
            
            province_coverage = execute_query(engine, province_coverage_query)
            if not province_coverage.empty:
                province_count = province_coverage.iloc[0]['province_count']
                provinces = province_coverage.iloc[0]['provinces']
                
                print(f"2025年覆盖的省份数: {province_count}")
                print(f"包含的省份: {provinces}")
            
            # 检查关键字段的数据质量
            data_quality_query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN gdp IS NULL THEN 1 END) as gdp_missing,
                COUNT(CASE WHEN gdp_growth_rate IS NULL THEN 1 END) as gdp_growth_missing,
                COUNT(CASE WHEN general_public_budget_revenue IS NULL THEN 1 END) as fiscal_revenue_missing,
                COUNT(CASE WHEN general_public_budget_expenditure IS NULL THEN 1 END) as fiscal_expenditure_missing
            FROM china_fiscal_data_2017_2024
            WHERE year = 2025
            """
            
            data_quality = execute_query(engine, data_quality_query)
            if not data_quality.empty:
                total = data_quality.iloc[0]['total_records']
                gdp_missing = data_quality.iloc[0]['gdp_missing']
                gdp_growth_missing = data_quality.iloc[0]['gdp_growth_missing']
                fiscal_revenue_missing = data_quality.iloc[0]['fiscal_revenue_missing']
                fiscal_expenditure_missing = data_quality.iloc[0]['fiscal_expenditure_missing']
                
                print(f"2025年数据质量检查:")
                print(f"  总记录数: {total}")
                if total > 0:
                    print(f"  GDP数据缺失: {gdp_missing}条 ({gdp_missing/total*100:.1f}%)")
                    print(f"  GDP增长数据缺失: {gdp_growth_missing}条 ({gdp_growth_missing/total*100:.1f}%)")
                    print(f"  财政收入数据缺失: {fiscal_revenue_missing}条 ({fiscal_revenue_missing/total*100:.1f}%)")
                    print(f"  财政支出数据缺失: {fiscal_expenditure_missing}条 ({fiscal_expenditure_missing/total*100:.1f}%)")
        else:
            print("无法获取数据表年份范围信息")
    except Exception as e:
        print(f"验证数据完整性时出错: {e}")
    
    print()
    
    # 4. 显示2025年数据样本
    print("4. 2025年数据样本")
    print("-" * 40)
    
    sample_query = """
    SELECT 
        year,
        dt,
        province,
        gdp,
        gdp_growth_rate,
        general_public_budget_revenue,
        general_public_budget_expenditure
    FROM china_fiscal_data_2017_2024
    WHERE year = 2025
    LIMIT 5
    """
    
    try:
        sample_data = execute_query(engine, sample_query)
        if not sample_data.empty:
            print("2025年数据样本:")
            print(sample_data.to_string(index=False))
        else:
            print("未找到2025年数据样本")
    except Exception as e:
        print(f"显示数据样本时出错: {e}")
    
    print()
    print("=" * 60)
    print("验证完成！")

if __name__ == "__main__":
    verify_gdp_data()