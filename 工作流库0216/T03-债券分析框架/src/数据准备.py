import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def prepare_yield_data():
    """准备债券收益率数据"""
    # 定义实际的历史下行周期
    cycles = [
        {'cycle': 1, 'start': '2014-01-02', 'end': '2015-02-13', 'start_yield': 4.6018, 'end_yield': 3.3552, 'change': -1.2466},
        {'cycle': 2, 'start': '2015-06-11', 'end': '2016-01-11', 'start_yield': 3.6197, 'end_yield': 2.8187, 'change': -0.8010},
        {'cycle': 3, 'start': '2018-01-18', 'end': '2019-02-02', 'start_yield': 3.9797, 'end_yield': 3.0978, 'change': -0.8819},
        {'cycle': 4, 'start': '2019-11-04', 'end': '2020-04-21', 'start_yield': 3.2954, 'end_yield': 2.5791, 'change': -0.7163},
        {'cycle': 5, 'start': '2021-03-10', 'end': '2022-08-29', 'start_yield': 3.2353, 'end_yield': 2.6225, 'change': -0.6128},
        {'cycle': 6, 'start': '2023-02-22', 'end': '2024-08-20', 'start_yield': 2.9175, 'end_yield': 2.1710, 'change': -0.7465}
    ]
    
    # 生成周期标注数据
    cycle_data = []
    for cycle in cycles:
        cycle_dates = pd.date_range(cycle['start'], cycle['end'], freq='B')
        cycle_data.extend([{
            'dt': date,
            'cycle_id': cycle['cycle']
        } for date in cycle_dates])
    
    # 保存周期标注
    pd.DataFrame(cycle_data).to_csv('收益率下行周期标注.csv', index=False, encoding='utf-8-sig')
    
    # 生成数据列表
    data = []
    
    # 基础利差设置（相对于10年期国债）
    term_spreads = {
        '短期': -1.0,    # 短期利率一般低于长期
        '中长期': -0.3,
        '长期': 0.0,     # 以10年期为基准
        '超长期': 0.3    # 超长期略高于10年期
    }
    
    # 信用利差设置（相对于同期限国债）
    credit_spreads = {
        'AAA': 0.5,
        'AA+': 0.8,
        'AA': 1.2,
        'AA(2)': 1.8,
        'AA-': 2.2
    }
    
    # 为每个周期生成数据
    for cycle in cycles:
        dates = pd.date_range(cycle['start'], cycle['end'], freq='B')
        total_days = (pd.Timestamp(cycle['end']) - pd.Timestamp(cycle['start'])).days
        
        for date in dates:
            # 计算当前日期在周期内的进度
            progress = (date - pd.Timestamp(cycle['start'])).days / total_days
            
            # 计算当前基准收益率（10年期国债）
            current_yield = cycle['start_yield'] + progress * cycle['change']
            
            # 生成各期限国债收益率
            for term, spread in term_spreads.items():
                base_yield = current_yield + spread + np.random.normal(0, 0.02)
                data.append({
                    'dt': date,
                    'bond_type': '国债',
                    'term': term,
                    'rating': None,
                    'yield_rate': max(base_yield, 0.5)  # 设置最低收益率
                })
                
                # 生成金融债收益率
                for bond_type in ['二永', '存单']:
                    if term != '超长期':  # 金融债没有超长期
                        for rating, credit_spread in credit_spreads.items():
                            yield_rate = base_yield + credit_spread + np.random.normal(0, 0.03)
                            data.append({
                                'dt': date,
                                'bond_type': bond_type,
                                'term': term,
                                'rating': rating,
                                'yield_rate': max(yield_rate, 0.8)
                            })
                
                # 生成城投债收益率
                if term != '超长期':  # 城投债没有超长期
                    for rating, credit_spread in credit_spreads.items():
                        yield_rate = base_yield + credit_spread * 1.3 + np.random.normal(0, 0.04)  # 城投债信用利差更大
                        data.append({
                            'dt': date,
                            'bond_type': '城投',
                            'term': term,
                            'rating': rating,
                            'yield_rate': max(yield_rate, 1.0)
                        })
    
    # 转换为DataFrame并保存
    df = pd.DataFrame(data)
    
    # 对同一天相同品种的收益率取平均
    df = df.groupby(['dt', 'bond_type', 'term', 'rating'])['yield_rate'].mean().reset_index()
    
    # 按日期排序
    df = df.sort_values('dt')
    
    # 保存数据
    df.to_csv('债券收益率数据.csv', index=False, encoding='utf-8-sig')
    
    print("数据准备完成！")
    print(f"生成记录数：{len(df)}")
    print("\n数据预览：")
    print(df.head())
    
    # 打印各个周期的基本信息
    print("\n收益率下行周期信息：")
    for cycle in cycles:
        print(f"\n周期{cycle['cycle']}:")
        print(f"起始日期：{cycle['start']}")
        print(f"结束日期：{cycle['end']}")
        print(f"收益率变动：{cycle['change']:.4f}%")
        print(f"起始收益率：{cycle['start_yield']:.4f}%")
        print(f"结束收益率：{cycle['end_yield']:.4f}%")

if __name__ == "__main__":
    prepare_yield_data() 