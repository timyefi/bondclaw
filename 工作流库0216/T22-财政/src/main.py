#!/usr/bin/env python3
"""
财政数据整合导入工作流
功能：读取Excel文件中的财政数据，进行数据清洗和转换，然后导入数据库
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from common.config.database import get_trade_database_config, DatabaseConfig
from common.config.logging import setup_logging
from common.utils.database import DatabaseManager
from config import *

# 省级行政区列表
PROVINCES = [
    '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
    '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门', '中国'
]

class FiscalDataProcessor:
    """财政数据处理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化处理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
    def parse_region_info(self, region_name: str, yy_region: Optional[str]) -> Tuple[str, str, str]:
        """
        解析地域信息，区分省、市和地区级别
        
        Args:
            region_name: 地域名称
            yy_region: YY地域信息
            
        Returns:
            Tuple[province, city, level]: 省、市、地区级别
        """
        if pd.isna(region_name) or region_name == '':
            return '', '', ''
        
        # 清理地域名称
        region_name = str(region_name).strip()
        
        # 检查是否为省级
        for province in PROVINCES:
            if region_name == province:
                return province, '', '省级'
            elif region_name.startswith(province) and len(region_name) > len(province):
                # 可能是省级的下属地区
                return province, region_name, '地市级'
        
        # 如果不是省级，则默认为地市级
        return '', region_name, '地市级'
    
    def convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        转换数据类型
        
        Args:
            df: 原始数据框
            
        Returns:
            转换后的数据框
        """
        # 定义数值列
        numeric_columns = [
            '负债率(%)', '负债率(宽口径)(%)', '债务率(%)', '债务率(宽口径)(%)',
            '城投债余额(亿)', '地方政府债余额(亿)', '地方政府债限额(亿)',
            '城投有息负债(亿)', '非标融资余额(亿)', '非标融资余额/城投有息负债(%)',
            '人民币: 各项存款余额/城投有息负债(%)', '城投有息负债: 三年复合增速(%)',
            'GDP(亿)', 'GDP增速(%)', '人均GDP(元)', '房地产投资(亿)',
            '城镇居民人均可支配收入(元)', '商品房销售面积(万平方米)',
            '商品房销售金额(亿)', '城镇居民人均消费性支出(元)',
            '农村居民人均消费性支出(元)', '工业增加量(亿)',
            '本外币: 各项存款余额(亿)', '本外币: 各项贷款余额(亿)',
            '地方政府综合财力(亿)', '财政自给率(%)', '一般公共预算收入(亿)',
            '一般公共预算支出(亿)', '税收收入(亿)', '税收收入占比(%)',
            '政府性基金收入(亿)', '政府性基金支出(亿)',
            '国有土地权出让收入(亿)', '国有土地权出让收入: 三年复合增速(%)',
            '国有土地权出让收入/一般公共预算收入(%)', '常住人口(万)'
        ]
        
        # 转换数值列
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗
        
        Args:
            df: 原始数据框
            
        Returns:
            清洗后的数据框
        """
        # 替换"--"为NaN
        df = df.replace('--', np.nan)
        df = df.replace('', np.nan)
        
        # 删除全为空的行
        df = df.dropna(how='all')
        
        return df
    
    def process_year_data(self, year: int, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理单个年份的数据
        
        Args:
            year: 年份
            df: 年份数据框
            
        Returns:
            处理后的数据框
        """
        self.logger.info(f"处理{year}年数据，共{len(df)}行")
        
        # 数据清洗
        df = self.clean_data(df)
        
        # 转换数据类型
        df = self.convert_data_types(df)
        
        # 添加年份列
        df['year'] = year
        
        # 添加dt列（每年的最后一天）
        dt_date = datetime(year, 12, 31).date()
        df['dt'] = dt_date
        
        # 解析地域信息
        region_info = df.apply(
            lambda row: self.parse_region_info(row['地域'], row.get('YY地域', None)),
            axis=1
        )
        df['province'] = region_info.apply(lambda x: x[0])
        df['city'] = region_info.apply(lambda x: x[1])
        df['region_level'] = region_info.apply(lambda x: x[2])
        
        # 重排序列
        desired_columns = [
            'dt', 'year', '地域', 'province', 'city', 'region_level', 'YY地域'
        ] + [col for col in df.columns if col not in [
            'dt', 'year', '地域', 'province', 'city', 'region_level', 'YY地域'
        ]]
        
        df = df[desired_columns]
        
        self.logger.info(f"{year}年数据处理完成，有效数据{len(df)}行")
        
        return df
    
    def create_table(self):
        """创建数据库表"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dt DATE NOT NULL COMMENT '日期（每年最后一天）',
            year INT NOT NULL COMMENT '年份',
            region_name VARCHAR(100) COMMENT '地域名称',
            province VARCHAR(50) COMMENT '省份',
            city VARCHAR(50) COMMENT '城市',
            region_level ENUM('省级', '地市级') COMMENT '地区级别',
            yy_region TEXT COMMENT 'YY地域描述',
            debt_ratio DECIMAL(10,4) COMMENT '负债率(%)',
            debt_ratio_wide DECIMAL(10,4) COMMENT '负债率(宽口径)(%)',
            debt_to_gdp_ratio DECIMAL(10,4) COMMENT '债务率(%)',
            debt_to_gdp_ratio_wide DECIMAL(10,4) COMMENT '债务率(宽口径)(%)',
            urban_investment_bond_balance DECIMAL(20,2) COMMENT '城投债余额(亿)',
            local_government_debt_balance DECIMAL(20,2) COMMENT '地方政府债余额(亿)',
            local_government_debt_limit DECIMAL(20,2) COMMENT '地方政府债限额(亿)',
            urban_investment_interest_debt DECIMAL(20,2) COMMENT '城投有息负债(亿)',
            non_standard_financing_balance DECIMAL(20,2) COMMENT '非标融资余额(亿)',
            non_standard_financing_ratio DECIMAL(10,4) COMMENT '非标融资余额/城投有息负债(%)',
            deposit_to_debt_ratio DECIMAL(10,4) COMMENT '人民币: 各项存款余额/城投有息负债(%)',
            urban_investment_debt_growth_3y DECIMAL(10,4) COMMENT '城投有息负债: 三年复合增速(%)',
            gdp DECIMAL(20,2) COMMENT 'GDP(亿)',
            gdp_growth_rate DECIMAL(10,4) COMMENT 'GDP增速(%)',
            gdp_per_capita DECIMAL(20,2) COMMENT '人均GDP(元)',
            real_estate_investment DECIMAL(20,2) COMMENT '房地产投资(亿)',
            urban_disposable_income DECIMAL(20,2) COMMENT '城镇居民人均可支配收入(元)',
            commercial_housing_area DECIMAL(20,2) COMMENT '商品房销售面积(万平方米)',
            commercial_housing_amount DECIMAL(20,2) COMMENT '商品房销售金额(亿)',
            urban_consumption_expenditure DECIMAL(20,2) COMMENT '城镇居民人均消费性支出(元)',
            rural_consumption_expenditure DECIMAL(20,2) COMMENT '农村居民人均消费性支出(元)',
            industrial_added_value DECIMAL(20,2) COMMENT '工业增加量(亿)',
            total_deposits DECIMAL(20,2) COMMENT '本外币: 各项存款余额(亿)',
            total_loans DECIMAL(20,2) COMMENT '本外币: 各项贷款余额(亿)',
            local_government_fiscal_power DECIMAL(20,2) COMMENT '地方政府综合财力(亿)',
            fiscal_self_sufficiency_ratio DECIMAL(10,4) COMMENT '财政自给率(%)',
            general_public_budget_revenue DECIMAL(20,2) COMMENT '一般公共预算收入(亿)',
            general_public_budget_expenditure DECIMAL(20,2) COMMENT '一般公共预算支出(亿)',
            tax_revenue DECIMAL(20,2) COMMENT '税收收入(亿)',
            tax_revenue_ratio DECIMAL(10,4) COMMENT '税收收入占比(%)',
            government_fund_revenue DECIMAL(20,2) COMMENT '政府性基金收入(亿)',
            government_fund_expenditure DECIMAL(20,2) COMMENT '政府性基金支出(亿)',
            state_owned_land_transfer_revenue DECIMAL(20,2) COMMENT '国有土地权出让收入(亿)',
            land_transfer_revenue_growth_3y DECIMAL(10,4) COMMENT '国有土地权出让收入: 三年复合增速(%)',
            land_transfer_to_budget_ratio DECIMAL(10,4) COMMENT '国有土地权出让收入/一般公共预算收入(%)',
            resident_population DECIMAL(20,2) COMMENT '常住人口(万)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_dt (dt),
            INDEX idx_year (year),
            INDEX idx_region (region_name),
            INDEX idx_province (province),
            INDEX idx_city (city),
            INDEX idx_region_level (region_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='中国财政数据2017-2024'
        """
        
        try:
            self.db_manager.execute_sql(create_table_sql)
            self.logger.info(f"表{TABLE_NAME}创建成功")
        except Exception as e:
            self.logger.error(f"创建表失败: {e}")
            raise
    
    def import_data(self, df: pd.DataFrame):
        """
        导入数据到数据库
        
        Args:
            df: 要导入的数据框
        """
        if df.empty:
            self.logger.warning("没有数据需要导入")
            return
        
        # 重命名列以匹配数据库字段
        column_mapping = {
            '地域': 'region_name',
            'YY地域': 'yy_region',
            '负债率(%)': 'debt_ratio',
            '负债率(宽口径)(%)': 'debt_ratio_wide',
            '债务率(%)': 'debt_to_gdp_ratio',
            '债务率(宽口径)(%)': 'debt_to_gdp_ratio_wide',
            '城投债余额(亿)': 'urban_investment_bond_balance',
            '地方政府债余额(亿)': 'local_government_debt_balance',
            '地方政府债限额(亿)': 'local_government_debt_limit',
            '城投有息负债(亿)': 'urban_investment_interest_debt',
            '非标融资余额(亿)': 'non_standard_financing_balance',
            '非标融资余额/城投有息负债(%)': 'non_standard_financing_ratio',
            '人民币: 各项存款余额/城投有息负债(%)': 'deposit_to_debt_ratio',
            '城投有息负债: 三年复合增速(%)': 'urban_investment_debt_growth_3y',
            'GDP(亿)': 'gdp',
            'GDP增速(%)': 'gdp_growth_rate',
            '人均GDP(元)': 'gdp_per_capita',
            '房地产投资(亿)': 'real_estate_investment',
            '城镇居民人均可支配收入(元)': 'urban_disposable_income',
            '商品房销售面积(万平方米)': 'commercial_housing_area',
            '商品房销售金额(亿)': 'commercial_housing_amount',
            '城镇居民人均消费性支出(元)': 'urban_consumption_expenditure',
            '农村居民人均消费性支出(元)': 'rural_consumption_expenditure',
            '工业增加量(亿)': 'industrial_added_value',
            '本外币: 各项存款余额(亿)': 'total_deposits',
            '本外币: 各项贷款余额(亿)': 'total_loans',
            '地方政府综合财力(亿)': 'local_government_fiscal_power',
            '财政自给率(%)': 'fiscal_self_sufficiency_ratio',
            '一般公共预算收入(亿)': 'general_public_budget_revenue',
            '一般公共预算支出(亿)': 'general_public_budget_expenditure',
            '税收收入(亿)': 'tax_revenue',
            '税收收入占比(%)': 'tax_revenue_ratio',
            '政府性基金收入(亿)': 'government_fund_revenue',
            '政府性基金支出(亿)': 'government_fund_expenditure',
            '国有土地权出让收入(亿)': 'state_owned_land_transfer_revenue',
            '国有土地权出让收入: 三年复合增速(%)': 'land_transfer_revenue_growth_3y',
            '国有土地权出让收入/一般公共预算收入(%)': 'land_transfer_to_budget_ratio',
            '常住人口(万)': 'resident_population'
        }
        
        # 重命名列
        df_import = df.rename(columns=column_mapping)
        
        # 只选择映射成功的列
        valid_columns = [col for col in df_import.columns if col in column_mapping.values() or col in [
            'dt', 'year', 'province', 'city', 'region_level'
        ]]
        df_import = df_import[valid_columns]
        
        # 批量导入数据
        try:
            self.db_manager.insert_dataframe(df_import, TABLE_NAME, if_exists='append', chunksize=1000)
            self.logger.info(f"数据导入完成，共导入{len(df_import)}条记录")
            
        except Exception as e:
            self.logger.error(f"数据导入失败: {e}")
            raise

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化数据库连接 - 使用本地数据库配置
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
        processor = FiscalDataProcessor(db_manager)
        
        # 创建数据库表
        processor.create_table()
        
        # 读取Excel文件
        excel_path = EXCEL_FILE_PATH
        logger.info(f"读取Excel文件: {excel_path}")
        
        # 获取所有工作表名称
        excel_file = pd.ExcelFile(excel_path)
        sheet_names = [name for name in excel_file.sheet_names if name.isdigit()]
        
        logger.info(f"发现工作表: {sheet_names}")
        
        # 处理每个年份的数据
        all_data = []
        for year_str in sheet_names:
            year = int(year_str)
            df = pd.read_excel(excel_path, sheet_name=year_str)
            processed_df = processor.process_year_data(year, df)
            all_data.append(processed_df)
        
        # 合并所有数据
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"数据合并完成，总记录数: {len(combined_df)}")
            
            # 导入数据库
            processor.import_data(combined_df)
            
            # 显示数据统计
            logger.info("数据导入统计:")
            logger.info(f"总记录数: {len(combined_df)}")
            logger.info(f"年份范围: {combined_df['year'].min()} - {combined_df['year'].max()}")
            logger.info(f"省级记录数: {len(combined_df[combined_df['region_level'] == '省级'])}")
            logger.info(f"地市级记录数: {len(combined_df[combined_df['region_level'] == '地市级'])}")
            
        else:
            logger.warning("没有找到有效的数据")
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    main()