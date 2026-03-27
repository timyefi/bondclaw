# /data/project/研究项目/可转债研究/可转债数据/main.py

import os
import sys
import traceback

# 添加正确的项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from src.bond_data_collector import THSBondDataCollector
    
    # 创建采集器实例
    collector = THSBondDataCollector()
    
    # 确保连接成功
    if not collector.login_status:
        print("同花顺登录失败，程序退出")
        sys.exit(1)

    print(collector.login_status)
        
    # 开始采集数据
    start_date = '2025-01-17'
    end_date = '2025-02-26'
    collector.collect_historical_data(start_date, end_date)
    
except Exception as e:
    print(f"Error occurred: {str(e)}")
    print(f"Traceback: {traceback.format_exc()}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"__file__: {__file__}")
finally:
    # 确保正确登出
    if 'collector' in locals() and collector.login_status:
        collector.stop_collection()