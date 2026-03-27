import pymysql
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys

# 配置日志
logging.basicConfig(
    filename='explore.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 同时输出到控制台和文件
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def explore_table(conn, table_name):
    """探索表格的基本特征"""
    logging.info(f"\n=== 探索表 {table_name} ===")
    
    try:
        # 1. 获取表的列结构
        logging.info("\n1. 表结构:")
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        for col in columns:
            logging.info(f"- {col[0]}: {col[1]}")
        
        # 2. 获取数据量
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]
        logging.info(f"\n2. 总记录数: {total_count}")
        
        # 3. 时间分布
        logging.info("\n3. 时间分布:")
        query = f"""
        SELECT 
            DATE_FORMAT(公告日期, '%Y-%m') as month,
            COUNT(*) as count
        FROM {table_name}
        GROUP BY DATE_FORMAT(公告日期, '%Y-%m')
        ORDER BY month DESC
        LIMIT 12
        """
        df_time = pd.read_sql(query, conn)
        logging.info("\n" + str(df_time))
        
        # 4. 数值字段的统计特征
        logging.info("\n4. 数值字段统计:")
        numeric_columns = ['发行规模(亿)', '借新还旧(亿)', '偿还有息债务(亿)', 
                          '补充流动资金(亿)', '项目建设(亿)', '其他(亿)']
        
        for col in numeric_columns:
            query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT(NULLIF(`{col}`, '')) as valid_count,
                AVG(CAST(NULLIF(`{col}`, '') AS DECIMAL(10,2))) as mean,
                MIN(CAST(NULLIF(`{col}`, '') AS DECIMAL(10,2))) as min,
                MAX(CAST(NULLIF(`{col}`, '') AS DECIMAL(10,2))) as max
            FROM {table_name}
            WHERE 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            """
            df_stats = pd.read_sql(query, conn)
            logging.info(f"\n{col}统计:")
            logging.info("\n" + str(df_stats))
        
        # 5. 主体评级分布
        logging.info("\n5. 主体评级分布:")
        query = f"""
        SELECT 
            主体评级,
            COUNT(*) as count
        FROM {table_name}
        WHERE 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY 主体评级
        ORDER BY count DESC
        """
        df_rating = pd.read_sql(query, conn)
        logging.info("\n" + str(df_rating))
        
        # 6. 地区分布
        logging.info("\n6. 地区分布(Top 10):")
        query = f"""
        SELECT 
            省份,
            COUNT(*) as count
        FROM {table_name}
        WHERE 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
        GROUP BY 省份
        ORDER BY count DESC
        LIMIT 10
        """
        df_region = pd.read_sql(query, conn)
        logging.info("\n" + str(df_region))
        
    except Exception as e:
        logging.error(f"探索表 {table_name} 时出错: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

def main():
    """主函数"""
    try:
        logging.info("开始分析...")
        
        # 连接数据库
        logging.info("连接数据库...")
        conn = pymysql.connect(
            host='rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            user='hz_work',
            password='Hzinsights2015',
            database='yq',
            port=3306,
            charset='utf8'
        )
        logging.info("数据库连接成功")
        
        # 探索城投债表
        explore_table(conn, '城投募集资金用途')
        
        # 探索产业债表
        explore_table(conn, '产业债募集资金用途')
        
        # 获取转型城投清单
        logging.info("\n=== 转型城投清单统计 ===")
        query = """
        select 
            '市场化经营主体' as type,
            COUNT(distinct 公司名称) as company_count
        from yq.城投平台市场化经营主体
        union all
        select 
            '退出平台' as type,
            COUNT(distinct 公司名称) as company_count
        from yq.城投平台退出
        where 披露日期>='2023-10-26'
        """
        df_transform = pd.read_sql(query, conn)
        logging.info("\n转型城投数量统计:")
        logging.info("\n" + str(df_transform))
        
        conn.close()
        logging.info("\n分析完成")
        
    except Exception as e:
        logging.error(f"分析过程中出错: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main() 