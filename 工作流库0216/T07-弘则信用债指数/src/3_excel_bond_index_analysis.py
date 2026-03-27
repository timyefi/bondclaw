import pandas as pd
import numpy as np
import sqlalchemy
import psycopg2
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import warnings
warnings.filterwarnings('ignore')

class BondExcelSystem:
    def __init__(self):
        # MySQL数据库连接 (bond数据库)
        self.sql_engine = sqlalchemy.create_engine(
            'mysql+pymysql://%s:%s@%s:%s/%s' % (
                'hz_work',
                'Hzinsights2015',
                'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                '3306',
                'bond',
            ), poolclass=sqlalchemy.pool.NullPool
        )
        
        # PostgreSQL数据库连接 (tsdb数据库)
        self.pg_conn = psycopg2.connect(
            host="139.224.107.113",
            port=18032,
            user="postgres",
            password="hzinsights2015",
            database="tsdb"
        )
        
    def export_data_to_excel(self, start_date='2025-01-01', end_date='2025-06-15', excel_file='bond_data.xlsx'):
        """导出数据到Excel文件"""
        print(f"Exporting data from {start_date} to {end_date} to {excel_file}...")
        
        # 创建Excel写入器
        writer = pd.ExcelWriter(excel_file, engine='openpyxl')
        
        try:
            # 1. 导出收益率数据
            print("Exporting yield data...")
            yield_query = f"""
            SELECT dt, trade_code, stdyield, balance, imrating_calc, target_term
            FROM hzcurve_credit
            WHERE dt >= '{start_date}' AND dt <= '{end_date}'
            AND target_term = 3
            AND stdyield IS NOT NULL
            ORDER BY dt, stdyield DESC
            """
            yield_data = pd.read_sql(yield_query, self.pg_conn)
            yield_data.to_excel(writer, sheet_name='yield_data', index=False)
            
            # 2. 导出信用债基础信息
            print("Exporting credit bond basic info...")
            credit_basic_query = """
            SELECT trade_code, ths_bond_short_name_bond, ths_ths_bond_third_type_bond,
                   ths_conceptualsector_bond_type_bond, ths_listed_date_bond, ths_delist_date_bond,
                   ths_nominal_interest_current_bond, ths_bond_maturity_theory_bond,
                   ths_interest_begin_date_bond, ths_maturity_date_bond, ths_issue_method_bond,
                   ths_ipo_actual_issue_total_amt_bond, ths_issuer_name_cn_bond,
                   ths_actual_controller_name_bond, ths_org_type_bond, ths_is_lc_bond,
                   ths_issuer_respond_district_bond_province, ths_issuer_respond_district_bond_city,
                   ths_is_perpetual_bond, ths_is_subordinated_debt_bond, ths_grnt_bond,
                   ths_urban_platform_area_bond, ths_city_bond_administrative_level_yy_bond,
                   ths_is_city_invest_debt_yy_bond, ths_is_city_invest_debt_ifind_bond,
                   ths_object_the_sw_bond, ths_is_issuing_failure_bond
            FROM basicinfo_credit
            WHERE ths_is_issuing_failure_bond != '是'
            """
            credit_basic = pd.read_sql(credit_basic_query, self.pg_conn)
            credit_basic.to_excel(writer, sheet_name='credit_basic_info', index=False)
            
            # 3. 导出金融债基础信息
            print("Exporting finance bond basic info...")
            finance_basic_query = """
            SELECT trade_code, ths_bond_short_name_bond, ths_ths_bond_third_type_bond,
                   ths_conceptualsector_bond_type_bond, ths_listed_date_bond, ths_delist_date_bond,
                   ths_nominal_interest_current_bond, ths_bond_maturity_theory_bond,
                   ths_interest_begin_date_bond, ths_maturity_date_bond, ths_issue_method_bond,
                   ths_ipo_actual_issue_total_amt_bond, ths_issuer_name_cn_bond,
                   ths_actual_controller_name_bond, ths_org_type_bond, ths_is_lc_bond,
                   ths_is_perpetual_bond, ths_is_subordinated_debt_bond,
                   ths_is_issuing_failure_bond, ths_nominal_interest_at_issuing_bond
            FROM basicinfo_finance
            WHERE ths_is_issuing_failure_bond != '是'
            """
            finance_basic = pd.read_sql(finance_basic_query, self.pg_conn)
            finance_basic.to_excel(writer, sheet_name='finance_basic_info', index=False)
            
            # 4. 导出信用债市场信息
            print("Exporting credit bond market info...")
            
            # 获取相关债券代码
            credit_codes = credit_basic['trade_code'].tolist()
            if credit_codes:
                # 分批查询以避免SQL语句过长
                batch_size = 100
                all_credit_market_data = []
                
                for i in range(0, len(credit_codes), batch_size):
                    batch_codes = credit_codes[i:i+batch_size]
                    code_placeholders = ','.join(['%s'] * len(batch_codes))
                    
                    credit_market_query = f"""
                    SELECT DT, TRADE_CODE, ths_remain_duration_y_bond, ths_bond_balance_bond,
                           ths_specified_date_subject_rating_bond, ths_specified_date_bond_rating_bond,
                           ths_evaluate_yeild_cfets_bond, ths_evaluate_yield_shch_bond,
                           ths_evaluate_yield_yy_bond, ths_yy_default_ratio_bond,
                           ths_evaluate_yield_cb_bond, ths_repay_years_cb_bond,
                           ths_cb_market_implicit_rating_bond, ths_evaluate_yield_cb_bond_exercise,
                           ths_repay_years_cb_bond_exercise, ths_subject_latest_rating_yy_bond,
                           ths_evaluate_interest_durcb_bond_exercise, ths_evaluate_spread_durcb_bond_exercise,
                           ths_evaluate_modified_dur_cb_bond_exercise, ths_evaluate_convexity_cb_bond,
                           ths_evaluate_net_price_cb_bond, ths_valuate_full_price_cb_bond
                    FROM marketinfo_credit
                    WHERE TRADE_CODE IN ({code_placeholders})
                    AND DT >= %s AND DT <= %s
                    AND ths_bond_balance_bond IS NOT NULL
                    AND ths_valuate_full_price_cb_bond IS NOT NULL
                    AND ths_evaluate_net_price_cb_bond IS NOT NULL
                    """
                    
                    params = list(batch_codes) + [start_date, end_date]
                    batch_data = pd.read_sql(credit_market_query, self.sql_engine, params=params)
                    all_credit_market_data.append(batch_data)
                
                if all_credit_market_data:
                    credit_market = pd.concat(all_credit_market_data, ignore_index=True)
                    credit_market.to_excel(writer, sheet_name='credit_market_info', index=False)
            
            # 5. 导出金融债市场信息
            print("Exporting finance bond market info...")
            
            # 获取相关债券代码
            finance_codes = finance_basic['trade_code'].tolist()
            if finance_codes:
                # 分批查询以避免SQL语句过长
                all_finance_market_data = []
                
                for i in range(0, len(finance_codes), batch_size):
                    batch_codes = finance_codes[i:i+batch_size]
                    code_placeholders = ','.join(['%s'] * len(batch_codes))
                    
                    finance_market_query = f"""
                    SELECT DT, TRADE_CODE, ths_remain_duration_y_bond, ths_bond_balance_bond,
                           ths_specified_date_subject_rating_bond, ths_specified_date_bond_rating_bond,
                           ths_evaluate_yeild_cfets_bond, ths_evaluate_yield_shch_bond,
                           ths_repay_years_cb_bond, ths_cb_market_implicit_rating_bond,
                           ths_evaluate_yield_cb_bond_exercise, ths_repay_years_cb_bond_exercise,
                           ths_evaluate_interest_durcb_bond_exercise, ths_evaluate_spread_durcb_bond_exercise,
                           ths_evaluate_modified_dur_cb_bond_exercise, ths_evaluate_convexity_cb_bond,
                           ths_evaluate_net_price_cb_bond, ths_valuate_full_price_cb_bond
                    FROM marketinfo_finance
                    WHERE TRADE_CODE IN ({code_placeholders})
                    AND DT >= %s AND DT <= %s
                    AND ths_bond_balance_bond IS NOT NULL
                    AND ths_valuate_full_price_cb_bond IS NOT NULL
                    AND ths_evaluate_net_price_cb_bond IS NOT NULL
                    """
                    
                    params = list(batch_codes) + [start_date, end_date]
                    batch_data = pd.read_sql(finance_market_query, self.sql_engine, params=params)
                    all_finance_market_data.append(batch_data)
                
                if all_finance_market_data:
                    finance_market = pd.concat(all_finance_market_data, ignore_index=True)
                    finance_market.to_excel(writer, sheet_name='finance_market_info', index=False)
            
            # 6. 创建数据字典
            print("Creating data dictionary...")
            data_dict = pd.DataFrame({
                'Table': ['yield_data', 'credit_basic_info', 'finance_basic_info', 'credit_market_info', 'finance_market_info'],
                'Description': [
                    'Yield curve data from hzcurve_credit table',
                    'Basic information for credit bonds',
                    'Basic information for finance bonds',
                    'Market information for credit bonds',
                    'Market information for finance bonds'
                ],
                'Source': ['tsdb.hzcurve_credit', 'tsdb.basicinfo_credit', 'tsdb.basicinfo_finance', 
                          'bond.marketinfo_credit', 'bond.marketinfo_finance']
            })
            data_dict.to_excel(writer, sheet_name='data_dictionary', index=False)
            
            writer.close()
            print(f"Data exported successfully to {excel_file}")
            
        except Exception as e:
            print(f"Error exporting data: {str(e)}")
            writer.close()
            raise
    
    def load_data_from_excel(self, excel_file='bond_data.xlsx'):
        """从Excel文件加载数据"""
        print(f"Loading data from {excel_file}...")
        
        try:
            # 读取各个工作表
            yield_data = pd.read_excel(excel_file, sheet_name='yield_data')
            credit_basic = pd.read_excel(excel_file, sheet_name='credit_basic_info')
            finance_basic = pd.read_excel(excel_file, sheet_name='finance_basic_info')
            credit_market = pd.read_excel(excel_file, sheet_name='credit_market_info')
            finance_market = pd.read_excel(excel_file, sheet_name='finance_market_info')
            
            print(f"Loaded data:")
            print(f"  Yield data: {len(yield_data)} records")
            print(f"  Credit basic: {len(credit_basic)} records")
            print(f"  Finance basic: {len(finance_basic)} records")
            print(f"  Credit market: {len(credit_market)} records")
            print(f"  Finance market: {len(finance_market)} records")
            
            return {
                'yield_data': yield_data,
                'credit_basic': credit_basic,
                'finance_basic': finance_basic,
                'credit_market': credit_market,
                'finance_market': finance_market
            }
            
        except Exception as e:
            print(f"Error loading data from Excel: {str(e)}")
            raise
    
    def process_excel_data(self, data_dict):
        """处理Excel数据并计算指数"""
        print("Processing Excel data...")
        
        yield_data = data_dict['yield_data']
        credit_basic = data_dict['credit_basic']
        finance_basic = data_dict['finance_basic']
        credit_market = data_dict['credit_market']
        finance_market = data_dict['finance_market']
        
        # 获取债券分类
        credit_bonds = credit_basic['trade_code'].tolist()
        finance_bonds = finance_basic['trade_code'].tolist()
        
        # 标记债券类型
        yield_data['bond_type'] = 'unknown'
        yield_data.loc[yield_data['trade_code'].isin(credit_bonds), 'bond_type'] = 'credit'
        yield_data.loc[yield_data['trade_code'].isin(finance_bonds), 'bond_type'] = 'finance'
        
        # 移除未分类的债券
        yield_data = yield_data[yield_data['bond_type'] != 'unknown']
        
        return self.create_percentile_groups_from_data(yield_data, credit_market, finance_market)
    
    def create_percentile_groups_from_data(self, yield_data, credit_market, finance_market):
        """从数据创建分位数分组"""
        print("Creating percentile groups from data...")
        
        all_indices = []
        
        for date in yield_data['dt'].unique():
            daily_yield = yield_data[yield_data['dt'] == date]
            
            for bond_type in ['credit', 'finance']:
                # 选择对应的市场数据
                market_data = credit_market if bond_type == 'credit' else finance_market
                daily_market = market_data[market_data['DT'] == date]
                
                # 获取当日的债券数据
                type_data = daily_yield[daily_yield['bond_type'] == bond_type].copy()
                
                if len(type_data) == 0:
                    continue
                
                # 按收益率降序排列
                type_data = type_data.sort_values('stdyield', ascending=True)
                
                # 计算分位数
                n_bonds = len(type_data)
                
                for i in range(10):
                    start_pct = i * 10
                    end_pct = (i + 1) * 10
                    
                    start_idx = int(n_bonds * start_pct / 100)
                    end_idx = int(n_bonds * end_pct / 100)
                    
                    if start_idx >= n_bonds:
                        continue
                    if end_idx > n_bonds:
                        end_idx = n_bonds
                    
                    group_data = type_data.iloc[start_idx:end_idx]
                    
                    if len(group_data) == 0:
                        continue
                    
                    # 合并价格数据
                    group_codes = group_data['trade_code'].tolist()
                    group_market = daily_market[daily_market['TRADE_CODE'].isin(group_codes)]
                    
                    if group_market.empty:
                        continue
                    
                    # 计算加权平均
                    total_balance = group_market['ths_bond_balance_bond'].sum()
                    if total_balance == 0:
                        continue
                    
                    weights = group_market['ths_bond_balance_bond'] / total_balance
                    
                    full_price_index = (group_market['ths_valuate_full_price_cb_bond'] * weights).sum()
                    net_price_index = (group_market['ths_evaluate_net_price_cb_bond'] * weights).sum()
                    
                    all_indices.append({
                        'dt': date,
                        'index_code': f"{bond_type.title()}_{start_pct}-{end_pct}_Full",
                        'index_value': full_price_index,
                        'index_type': 'full_price'
                    })
                    
                    all_indices.append({
                        'dt': date,
                        'index_code': f"{bond_type.title()}_{start_pct}-{end_pct}_Net",
                        'index_value': net_price_index,
                        'index_type': 'net_price'
                    })
        
        return pd.DataFrame(all_indices)
    
    def create_interactive_chart_from_excel(self, indices_data, output_file='bond_indices_excel_dashboard.html'):
        """从Excel数据创建交互式图表"""
        print("Creating interactive chart from Excel data...")
        
        # 转换日期格式
        indices_data['dt'] = pd.to_datetime(indices_data['dt'])
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Credit Bond Indices - Full Price', 'Credit Bond Indices - Net Price',
                          'Finance Bond Indices - Full Price', 'Finance Bond Indices - Net Price'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 定义颜色
        colors = px.colors.qualitative.Set3
        
        # 绘制信用债全价指数
        credit_full = indices_data[
            (indices_data['index_code'].str.contains('Credit')) & 
            (indices_data['index_type'] == 'full_price')
        ]
        
        for i, index_code in enumerate(credit_full['index_code'].unique()):
            data = credit_full[credit_full['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines+markers',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # 绘制信用债净价指数
        credit_net = indices_data[
            (indices_data['index_code'].str.contains('Credit')) & 
            (indices_data['index_type'] == 'net_price')
        ]
        
        for i, index_code in enumerate(credit_net['index_code'].unique()):
            data = credit_net[credit_net['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines+markers',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # 绘制金融债全价指数
        finance_full = indices_data[
            (indices_data['index_code'].str.contains('Finance')) & 
            (indices_data['index_type'] == 'full_price')
        ]
        
        for i, index_code in enumerate(finance_full['index_code'].unique()):
            data = finance_full[finance_full['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines+markers',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 绘制金融债净价指数
        finance_net = indices_data[
            (indices_data['index_code'].str.contains('Finance')) & 
            (indices_data['index_type'] == 'net_price')
        ]
        
        for i, index_code in enumerate(finance_net['index_code'].unique()):
            data = finance_net[finance_net['index_code'] == index_code]
            fig.add_trace(
                go.Scatter(
                    x=data['dt'], 
                    y=data['index_value'],
                    mode='lines+markers',
                    name=index_code,
                    line=dict(color=colors[i % len(colors)]),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Value: %{y:.4f}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text="Bond Indices Dashboard (Excel Data)",
            title_x=0.5,
            height=800,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified'
        )
        
        # 添加范围选择器
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=7, label="7d", step="day", stepmode="backward"),
                            dict(count=30, label="30d", step="day", stepmode="backward"),
                            dict(count=90, label="90d", step="day", stepmode="backward"),
                            dict(step="all")
                        ])
                    ),
                    type="date",
                    row=i, col=j
                )
        
        # 保存HTML文件
        pyo.plot(fig, filename=output_file, auto_open=False)
        print(f"Interactive chart saved as {output_file}")
        
        return fig
    
    def run_excel_analysis(self, excel_file='bond_data.xlsx', output_file='bond_indices_excel_dashboard.html'):
        """运行基于Excel的分析"""
        print("Starting Excel-based bond index analysis...")
        
        try:
            # 从Excel加载数据
            data_dict = self.load_data_from_excel(excel_file)
            
            # 处理数据并计算指数
            indices_data = self.process_excel_data(data_dict)
            print(f"Calculated {len(indices_data)} index points")
            
            if indices_data.empty:
                print("No indices calculated")
                return None, None
            
            # 创建交互式图表
            fig = self.create_interactive_chart_from_excel(indices_data, output_file)
            
            print("Excel analysis completed successfully!")
            
            return indices_data, data_dict
            
        except Exception as e:
            print(f"Error in Excel analysis: {str(e)}")
            raise
        
        finally:
            # 关闭数据库连接
            if hasattr(self, 'pg_conn'):
                self.pg_conn.close()

# 主程序
if __name__ == "__main__":
    import sys
    
    # 创建Excel分析系统
    excel_system = BondExcelSystem()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == 'export':
            # 导出数据模式
            start_date = sys.argv[2] if len(sys.argv) > 2 else '2025-01-01'
            end_date = sys.argv[3] if len(sys.argv) > 3 else '2025-06-15'
            excel_file = sys.argv[4] if len(sys.argv) > 4 else 'bond_data.xlsx'
            
            excel_system.export_data_to_excel(start_date, end_date, excel_file)
            
        elif mode == 'analyze':
            # 分析模式
            excel_file = sys.argv[2] if len(sys.argv) > 2 else 'bond_data.xlsx'
            output_file = sys.argv[3] if len(sys.argv) > 3 else 'bond_indices_excel_dashboard.html'
            
            indices_data, data_dict = excel_system.run_excel_analysis(excel_file, output_file)
            
            if indices_data is not None:
                print("\nIndex Summary:")
                print(f"Date range: {indices_data['dt'].min()} to {indices_data['dt'].max()}")
                print(f"Number of indices: {len(indices_data['index_code'].unique())}")
                print("\nIndex codes:")
                for code in sorted(indices_data['index_code'].unique()):
                    print(f"  {code}")
                
                # 保存数据到CSV
                indices_data.to_csv('bond_indices_excel_data.csv', index=False)
                print("\nData saved to bond_indices_excel_data.csv")
        else:
            print("Unknown mode. Use 'export' or 'analyze'")
    else:
        # 默认：先导出数据，再分析
        print("Running full process: export + analyze...")
        
        # 导出数据
        excel_system.export_data_to_excel()
        
        # 分析数据
        indices_data, data_dict = excel_system.run_excel_analysis()
        
        if indices_data is not None:
            print("\nIndex Summary:")
            print(f"Date range: {indices_data['dt'].min()} to {indices_data['dt'].max()}")
            print(f"Number of indices: {len(indices_data['index_code'].unique())}")
            
    print("\nUsage examples:")
    print("  python bond_excel_system.py export                           # Export data for default date range")
    print("  python bond_excel_system.py export 2025-01-01 2025-06-15    # Export data for specific date range")
    print("  python bond_excel_system.py analyze bond_data.xlsx          # Analyze existing Excel file")
    print("  python bond_excel_system.py                                 # Full process: export + analyze") 