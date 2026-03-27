#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据插入结果
"""

import pandas as pd
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from common.utils.database import DatabaseManager
from common.config.database import get_predefined_database_config

def verify_results():
    """验证数据插入结果"""
    # 使用yq数据库配置
    config = get_predefined_database_config('yq')
    db_manager = DatabaseManager(config)
    
    try:
        # 查询表中数据总数
        df = db_manager.execute_query('SELECT COUNT(*) as count FROM `全球实物资产比金融资产`', None)
        print(f'表中数据总数: {df["count"].iloc[0]}')
        
        # 查询最新5条数据
        df = db_manager.execute_query('SELECT dt, close FROM `全球实物资产比金融资产` ORDER BY dt DESC LIMIT 5', None)
        print('最新5条数据:')
        print(df)
        
        # 查询最早的5条数据
        df = db_manager.execute_query('SELECT dt, close FROM `全球实物资产比金融资产` ORDER BY dt ASC LIMIT 5', None)
        print('最早5条数据:')
        print(df)
        
    except Exception as e:
        print(f"验证失败: {e}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    verify_results()