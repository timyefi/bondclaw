import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.utils.database import DatabaseManager
from common.config.database import get_bond_database_config
import pandas as pd

def get_target_data():
    """严格按照需求文档中的第二段代码获取目标格式数据"""
    db_manager_bond = DatabaseManager(get_bond_database_config())

    try:
        dt = pd.to_datetime('today').strftime("%Y-%m-%d")
        
        trade_dates_query = f"""SELECT MAX(DT) AS DT FROM `stock`.`temp_5843` WHERE DT <= '{dt}'"""
        trade_dates = db_manager_bond.execute_query(trade_dates_query).values[0][0]
        
        trade_dates1_query = f"""SELECT MAX(DT) AS DT FROM `stock`.`temp_5857` WHERE DT <= '{dt}'"""
        trade_dates1 = db_manager_bond.execute_query(trade_dates1_query).values[0][0]
        
        if trade_dates <= trade_dates1:
            ed = trade_dates.strftime("%Y-%m-%d")
        else:
            ed = trade_dates1.strftime("%Y-%m-%d")

        print(f"--- 获取到的目标数据日期为: {ed} ---")

        # --- 获取省级数据 (raw1) ---
        raw1_query = f"""SELECT * FROM `stock`.`temp_5843` WHERE DT = '{ed}'"""
        raw1 = db_manager_bond.execute_query(raw1_query)
        raw1 = raw1.groupby(['PROVINCE','DT']).agg({'CLOSE':'mean'}).reset_index(drop=False)
        raw1.columns=['name','dt','value']
        raw1['name']=raw1['name'].apply(lambda x : str(x)[0:2])
        raw1.loc[raw1['name'] == '内蒙', 'name'] = '内蒙古'
        raw1.loc[raw1['name'] == '黑龙', 'name'] = '黑龙江'
        raw1['value']=raw1['value'].apply(lambda x: round(x*100,0))
        
        print("--- 目标格式(省级) ---")
        print(raw1)

        # --- 获取市级数据 (raw2) ---
        raw2_query = f"""SELECT * FROM `stock`.`temp_5857` WHERE DT = '{ed}'"""
        raw2 = db_manager_bond.execute_query(raw2_query)
        raw2 = raw2.groupby(['PROVINCE','DT','CITY']).agg({'CLOSE':'mean'}).reset_index(drop=False)
        raw2['PROVINCE']=raw2['PROVINCE'].apply(lambda x : str(x)[0:2])
        raw2.loc[raw2['PROVINCE'] == '内蒙', 'PROVINCE'] = '内蒙古'
        raw2.loc[raw2['PROVINCE'] == '黑龙', 'PROVINCE'] = '黑龙江'
        raw2['CITY']=raw2['CITY'].apply(lambda x:str(x)[0:2])
        raw2['CLOSE']=raw2['CLOSE'].apply(lambda x:round(x*100,0))

        print("\n--- 目标格式(市级) ---")
        print(raw2)

    except Exception as e:
        print(f"执行目标数据查询时出错: {e}")

if __name__ == '__main__':
    get_target_data()
