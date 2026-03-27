# -*- coding: utf-8 -*-
"""
金融资负表数据清理脚本（最终版）
功能：清理重复数据，确保每个指标在每个月末只保留一条记录
"""

import pandas as pd
import sqlalchemy
from sqlalchemy import text
from datetime import datetime
import pymysql

def clean_financial_data_final():
    """执行金融资负表数据清理"""
    # 创建数据库连接
    sql_engine = sqlalchemy.create_engine(
        'mysql+pymysql://hz_work:Hzinsights2015@rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com:3306/yq'
    )
    
    print("金融资负表数据清理开始...")
    
    try:
        with sql_engine.begin() as connection:
            # 1. 统计清理前的数据情况
            print("1. 统计清理前数据情况...")
            total_query = 'SELECT COUNT(*) as total FROM 金融资负'
            total_before = pd.read_sql(text(total_query), connection).iloc[0]['total']
            
            duplicate_months_query = '''
            SELECT COUNT(*) as duplicate_months
            FROM (
                SELECT YEAR(dt) as year, MONTH(dt) as month
                FROM 金融资负
                GROUP BY YEAR(dt), MONTH(dt)
                HAVING COUNT(*) > 1
            ) t
            '''
            duplicate_months = pd.read_sql(text(duplicate_months_query), connection).iloc[0]['duplicate_months']
            
            delete_count_query = '''
            SELECT SUM(cnt - 1) as delete_count
            FROM (
                SELECT YEAR(dt) as year, MONTH(dt) as month, COUNT(*) as cnt
                FROM 金融资负
                GROUP BY YEAR(dt), MONTH(dt)
                HAVING COUNT(*) > 1
            ) t
            '''
            delete_count_result = pd.read_sql(text(delete_count_query), connection)
            delete_count = int(delete_count_result.iloc[0]['delete_count']) if delete_count_result.iloc[0]['delete_count'] else 0
            
            print(f"   总记录数: {total_before}")
            print(f"   存在重复的月份: {duplicate_months}")
            print(f"   需要删除的记录数: {delete_count}")
            
            if delete_count == 0:
                print("   没有需要清理的重复数据")
                return True
            
            # 2. 显示重复数据示例
            print("2. 重复数据示例...")
            sample_query = '''
            SELECT 
                YEAR(dt) as year,
                MONTH(dt) as month,
                MAX(dt) as last_day,
                COUNT(*) as record_count
            FROM 金融资负
            GROUP BY YEAR(dt), MONTH(dt)
            HAVING COUNT(*) > 1
            ORDER BY year DESC, month DESC
            LIMIT 3
            '''
            df_sample = pd.read_sql(text(sample_query), connection)
            for _, row in df_sample.iterrows():
                detail_query = '''
                SELECT dt
                FROM 金融资负
                WHERE YEAR(dt) = :year AND MONTH(dt) = :month
                ORDER BY dt
                '''
                df_detail = pd.read_sql(text(detail_query), connection,
                                      params={'year': row['year'], 'month': row['month']})
                dates = df_detail['dt'].tolist()
                print(f"   {row['year']}年{row['month']}月: {len(dates)}条记录 ({dates[0]} 到 {dates[-1]})")
            
            # 3. 确认执行清理
            print("3. 确认清理操作...")
            print(f"   将删除 {delete_count} 条重复记录，只保留每月最后一天的数据")
            confirm = input("   确认执行清理？(输入 'YES' 确认): ")
            if confirm != 'YES':
                print("   操作已取消")
                return False
            
            # 4. 执行清理操作
            print("4. 执行清理操作...")
            
            # 创建临时表存储每月应该保留的日期
            connection.execute(text('DROP TEMPORARY TABLE IF EXISTS temp_keep_dates'))
            create_temp_table = '''
            CREATE TEMPORARY TABLE temp_keep_dates AS (
                SELECT MAX(dt) as keep_dt
                FROM 金融资负
                GROUP BY YEAR(dt), MONTH(dt)
            )
            '''
            connection.execute(text(create_temp_table))
            
            # 删除不应该保留的记录
            delete_query = '''
            DELETE FROM 金融资负
            WHERE dt NOT IN (SELECT keep_dt FROM temp_keep_dates)
            '''
            result = connection.execute(text(delete_query))
            deleted_rows = result.rowcount
            
            # 清理临时表
            connection.execute(text('DROP TEMPORARY TABLE IF EXISTS temp_keep_dates'))
            
            print(f"   成功删除 {deleted_rows} 条重复记录")
            
            # 5. 验证清理结果
            print("5. 验证清理结果...")
            total_after_query = 'SELECT COUNT(*) as total FROM 金融资负'
            total_after = pd.read_sql(text(total_after_query), connection).iloc[0]['total']
            
            verify_query = '''
            SELECT COUNT(*) as remaining_duplicates
            FROM (
                SELECT YEAR(dt) as year, MONTH(dt) as month
                FROM 金融资负
                GROUP BY YEAR(dt), MONTH(dt)
                HAVING COUNT(*) > 1
            ) t
            '''
            remaining_duplicates = pd.read_sql(text(verify_query), connection).iloc[0]['remaining_duplicates']
            
            print(f"   清理后总记录数: {total_after}")
            print(f"   剩余重复月份: {remaining_duplicates}")
            
            if remaining_duplicates == 0:
                print("   ✓ 清理完成！所有月份都只有唯一记录。")
                return True
            else:
                print(f"   ⚠ 仍有 {remaining_duplicates} 个月份存在重复记录")
                return False
            
    except Exception as e:
        print(f"清理过程中出错: {e}")
        return False

def main():
    print("=" * 60)
    print("金融资负表数据清理工具（最终版）")
    print("=" * 60)
    print("功能：清理重复数据，确保每个指标在每个月末只保留一条记录")
    print("策略：删除重复月份中非最后一天的记录，只保留每月最后一天的数据")
    print()
    
    success = clean_financial_data_final()
    
    if success:
        print("\n" + "=" * 60)
        print("数据清理成功完成！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("数据清理未完成，请检查日志。")
        print("=" * 60)

if __name__ == "__main__":
    main()