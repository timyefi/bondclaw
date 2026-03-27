#!/usr/bin/env python3
"""
财政数据整合导入测试程序
功能：读取Excel文件中的财政数据，进行数据清洗和转换，输出处理结果到CSV文件
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os

# 省级行政区列表
PROVINCES = [
    '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
    '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门', '中国'
]

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FiscalDataProcessorTest:
    """财政数据处理器（测试版本）"""
    
    def __init__(self):
        """初始化处理器"""
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

def main():
    """主函数"""
    try:
        # 初始化处理器
        processor = FiscalDataProcessorTest()
        
        # Excel文件路径
        excel_path = '/data/项目/快速处理/2025/财政/17-24chinafiscaldata.xlsx'
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
            
            # 保存处理后的数据到CSV文件
            output_file = '/data/项目/快速处理/2025/财政/财政数据整合导入/processed_fiscal_data.csv'
            combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"处理后的数据已保存到: {output_file}")
            
            # 显示数据统计
            logger.info("数据处理统计:")
            logger.info(f"总记录数: {len(combined_df)}")
            logger.info(f"年份范围: {combined_df['year'].min()} - {combined_df['year'].max()}")
            
            # 统计省级和地市级记录数
            provincial_count = len(combined_df[combined_df['region_level'] == '省级'])
            city_count = len(combined_df[combined_df['region_level'] == '地市级'])
            logger.info(f"省级记录数: {provincial_count}")
            logger.info(f"地市级记录数: {city_count}")
            
            # 显示地域解析结果样本
            logger.info("地域解析结果样本:")
            sample_data = combined_df[['地域', 'province', 'city', 'region_level']].head(10)
            for _, row in sample_data.iterrows():
                logger.info(f"  {row['地域']} -> 省: {row['province']}, 市: {row['city']}, 级别: {row['region_level']}")
            
            # 显示数据质量统计
            logger.info("数据质量统计:")
            for year in sorted(combined_df['year'].unique()):
                year_data = combined_df[combined_df['year'] == year]
                logger.info(f"  {year}年: {len(year_data)}条记录")
            
        else:
            logger.warning("没有找到有效的数据")
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise

if __name__ == "__main__":
    main()