#!/usr/bin/env python3
"""
2025年上半年GDP数据导入脚本
功能：将2025年上半年各省GDP和GDP增速数据导入数据库
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, date
from typing import Dict, List
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from common.config.database import get_trade_database_config, DatabaseConfig
from common.config.logging import setup_logging
from common.utils.database import DatabaseManager

# 2025年上半年GDP数据
GDP_DATA_2025_H1 = [
    {'province': '广东', 'gdp': 68725.4, 'gdp_growth_rate': 4.2},
    {'province': '江苏', 'gdp': 66967.8, 'gdp_growth_rate': 5.7},
    {'province': '山东', 'gdp': 50046.0, 'gdp_growth_rate': 5.6},
    {'province': '浙江', 'gdp': 45004.0, 'gdp_growth_rate': 5.8},
    {'province': '四川', 'gdp': 31918.2, 'gdp_growth_rate': 5.6},
    {'province': '河南', 'gdp': 31683.8, 'gdp_growth_rate': 5.7},
    {'province': '湖北', 'gdp': 29642.61, 'gdp_growth_rate': 6.2},
    {'province': '福建', 'gdp': 27996.57, 'gdp_growth_rate': 5.7},
    {'province': '上海', 'gdp': 26222.15, 'gdp_growth_rate': 5.1},
    {'province': '湖南', 'gdp': 26166.5, 'gdp_growth_rate': 5.6},
    {'province': '安徽', 'gdp': 25723.0, 'gdp_growth_rate': 5.6},
    {'province': '北京', 'gdp': 25029.2, 'gdp_growth_rate': 5.5},
    {'province': '河北', 'gdp': 22965.9, 'gdp_growth_rate': 5.4},
    {'province': '陕西', 'gdp': 16828.01, 'gdp_growth_rate': 5.5},
    {'province': '江西', 'gdp': 16719.6, 'gdp_growth_rate': 5.6},
    {'province': '重庆', 'gdp': 15929.58, 'gdp_growth_rate': 5.0},
    {'province': '辽宁', 'gdp': 15707.9, 'gdp_growth_rate': 4.7},
    {'province': '云南', 'gdp': 15537.44, 'gdp_growth_rate': 4.4},
    {'province': '广西', 'gdp': 13850.95, 'gdp_growth_rate': 5.5},
    {'province': '内蒙古', 'gdp': 12077.6, 'gdp_growth_rate': 5.4},
    {'province': '山西', 'gdp': 11436.7, 'gdp_growth_rate': 3.8},
    {'province': '贵州', 'gdp': 11442.2, 'gdp_growth_rate': 5.3},
    {'province': '新疆', 'gdp': 10646.48, 'gdp_growth_rate': 5.7},
    {'province': '天津', 'gdp': 7067.6, 'gdp_growth_rate': 5.3},
    {'province': '黑龙江', 'gdp': 7066.7, 'gdp_growth_rate': 4.7},
    {'province': '吉林', 'gdp': 6422.8, 'gdp_growth_rate': 5.6},
    {'province': '甘肃', 'gdp': 6288.8, 'gdp_growth_rate': 5.7},
    {'province': '海南', 'gdp': 3701.85, 'gdp_growth_rate': 4.2},
    {'province': '宁夏', 'gdp': 2609.6, 'gdp_growth_rate': 5.8},
    {'province': '青海', 'gdp': 1875.99, 'gdp_growth_rate': 4.0},
    {'province': '西藏', 'gdp': 1382.76, 'gdp_growth_rate': 7.2}
]

class GDPDataImporter:
    """2025年GDP数据导入器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化导入器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.table_name = 'china_fiscal_data_2017_2024'
        
    def prepare_2025_h1_data(self) -> pd.DataFrame:
        """
        准备2025年上半年数据
        
        Returns:
            准备好的数据框
        """
        self.logger.info("准备2025年上半年GDP数据")
        
        # 转换为DataFrame
        df = pd.DataFrame(GDP_DATA_2025_H1)
        
        # 添加其他必要字段
        df['dt'] = date(2025, 6, 30)
        df['year'] = '2025H1'
        df['region_name'] = df['province']
        df['city'] = ''
        df['region_level'] = '省级'
        df['yy_region'] = None
        
        # 重命名列以匹配数据库字段
        df = df.rename(columns={
            'gdp': 'gdp',
            'gdp_growth_rate': 'gdp_growth_rate'
        })
        
        # 添加所有其他字段为NULL
        other_columns = [
            'debt_ratio', 'debt_ratio_wide', 'debt_to_gdp_ratio', 'debt_to_gdp_ratio_wide',
            'urban_investment_bond_balance', 'local_government_debt_balance', 'local_government_debt_limit',
            'urban_investment_interest_debt', 'non_standard_financing_balance', 'non_standard_financing_ratio',
            'deposit_to_debt_ratio', 'urban_investment_debt_growth_3y', 'gdp_per_capita',
            'real_estate_investment', 'urban_disposable_income', 'commercial_housing_area',
            'commercial_housing_amount', 'urban_consumption_expenditure', 'rural_consumption_expenditure',
            'industrial_added_value', 'total_deposits', 'total_loans',
            'local_government_fiscal_power', 'fiscal_self_sufficiency_ratio',
            'general_public_budget_revenue', 'general_public_budget_expenditure', 'tax_revenue',
            'tax_revenue_ratio', 'government_fund_revenue', 'government_fund_expenditure',
            'state_owned_land_transfer_revenue', 'land_transfer_revenue_growth_3y',
            'land_transfer_to_budget_ratio', 'resident_population'
        ]
        
        for col in other_columns:
            df[col] = None
            
        # 重排序列以匹配数据库表结构
        desired_columns = [
            'dt', 'year', 'region_name', 'province', 'city', 'region_level', 'yy_region',
            'debt_ratio', 'debt_ratio_wide', 'debt_to_gdp_ratio', 'debt_to_gdp_ratio_wide',
            'urban_investment_bond_balance', 'local_government_debt_balance', 'local_government_debt_limit',
            'urban_investment_interest_debt', 'non_standard_financing_balance', 'non_standard_financing_ratio',
            'deposit_to_debt_ratio', 'urban_investment_debt_growth_3y', 'gdp', 'gdp_growth_rate', 'gdp_per_capita',
            'real_estate_investment', 'urban_disposable_income', 'commercial_housing_area',
            'commercial_housing_amount', 'urban_consumption_expenditure', 'rural_consumption_expenditure',
            'industrial_added_value', 'total_deposits', 'total_loans',
            'local_government_fiscal_power', 'fiscal_self_sufficiency_ratio',
            'general_public_budget_revenue', 'general_public_budget_expenditure', 'tax_revenue',
            'tax_revenue_ratio', 'government_fund_revenue', 'government_fund_expenditure',
            'state_owned_land_transfer_revenue', 'land_transfer_revenue_growth_3y',
            'land_transfer_to_budget_ratio', 'resident_population'
        ]
        
        df = df[desired_columns]
        
        self.logger.info(f"2025年上半年数据准备完成，共{len(df)}条记录")
        return df
        
    def check_existing_data(self) -> bool:
        """
        检查是否已存在2025年数据
        
        Returns:
            是否存在2025年数据
        """
        query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE year = 2025"
        result = self.db_manager.execute_query(query)
        if result and len(result) > 0:
            return result.iloc[0]['count'] > 0
        return False
        
    def import_data(self, df: pd.DataFrame):
        """
        导入数据到数据库
        
        Args:
            df: 要导入的数据框
        """
        if df.empty:
            self.logger.warning("没有数据需要导入")
            return
            
        # 检查是否已存在2025年数据
        if self.check_existing_data():
            self.logger.warning("已存在2025年数据，删除现有数据...")
            delete_query = f"DELETE FROM {self.table_name} WHERE year = 2025"
            self.db_manager.execute_sql(delete_query)
            
        # 批量导入数据
        try:
            self.db_manager.insert_dataframe(df, self.table_name, if_exists='append', chunksize=1000)
            self.logger.info(f"数据导入完成，共导入{len(df)}条记录")
            
        except Exception as e:
            self.logger.error(f"数据导入失败: {e}")
            raise
            
    def verify_import(self):
        """
        验证导入结果
        """
        query = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT province) as unique_provinces,
            SUM(gdp) as total_gdp,
            AVG(gdp_growth_rate) as avg_growth_rate
        FROM {self.table_name} 
        WHERE year = 2025
        """
        
        result = self.db_manager.execute_query(query)
        
        if result:
            stats = result[0]
            self.logger.info("数据导入验证结果:")
            self.logger.info(f"总记录数: {stats['total_records']}")
            self.logger.info(f"唯一省份数: {stats['unique_provinces']}")
            self.logger.info(f"GDP总量: {stats['total_gdp']:.2f}亿元")
            self.logger.info(f"平均增速: {stats['avg_growth_rate']:.2f}%")
            
        # 显示具体数据
        query2 = f"""
        SELECT province, gdp, gdp_growth_rate
        FROM {self.table_name}
        WHERE year = 2025
        ORDER BY gdp DESC
        LIMIT 10
        """
        
        top_provinces = self.db_manager.execute_query(query2)
        
        self.logger.info("GDP前10名省份:")
        for i, row in enumerate(top_provinces, 1):
            self.logger.info(f"{i}. {row['province']}: {row['gdp']:.2f}亿元, 增速{row['gdp_growth_rate']}%")

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化数据库连接
        db_config = DatabaseConfig(
            user='hz_work',
            password='Hzinsights2015',
            host='rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            port='3306',
            database='bond',
            charset='utf8mb4'
        )
        db_manager = DatabaseManager(db_config)
        
        # 测试数据库连接
        if not db_manager.test_connection():
            logger.error("数据库连接失败，请检查数据库配置和网络连接")
            return
            
        importer = GDPDataImporter(db_manager)
        
        # 准备数据
        df = importer.prepare_2025_h1_data()
        
        # 导入数据
        importer.import_data(df)
        
        # 验证导入结果
        importer.verify_import()
        
        logger.info("2025年上半年GDP数据导入完成！")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    main()