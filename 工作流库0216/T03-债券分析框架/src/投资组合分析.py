import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from itertools import permutations, product
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.font_manager import findfont, FontProperties
import subprocess
import sys
import os
import glob

# 清理输出文件夹
def clean_output_files():
    """清理分析结果文件，但保留原始数据文件"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\n清理目录: {current_dir}")
    
    # 需要保护的原始数据文件
    protected_files = ['收益率下行周期标注.csv', '债券收益率数据.csv']
    
    # 删除分析结果图片
    for f in glob.glob(os.path.join(current_dir, "*.png")):
        try:
            os.remove(f)
            print(f"已删除: {os.path.basename(f)}")
        except Exception as e:
            print(f"删除{os.path.basename(f)}时出错: {e}")
    
    # 删除分析���果CSV文件（但保留原始数据文件）
    for f in glob.glob(os.path.join(current_dir, "*.csv")):
        if os.path.basename(f) not in protected_files:
            try:
                os.remove(f)
                print(f"已删除: {os.path.basename(f)}")
            except Exception as e:
                print(f"删除{os.path.basename(f)}时出错: {e}")
    
    print("清理完成\n")

# 检查并安装必要的包
def check_and_install_packages():
    required_packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn'
    }
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            print(f"{package} 安装完成")

# 在程序开始时检查并安装包
check_and_install_packages()

# 设置中文字体
def setup_chinese_font():
    try:
        font = FontProperties(fname=r"C:\Windows\Fonts\msyh.ttc")  # Microsoft YaHei
        return font
    except:
        try:
            font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")  # SimHei
            return font
        except:
            print("警告: 无法加载中文字体，图表中的中文可能无法正常显示")
            return None

chinese_font = setup_chinese_font()
plt.rcParams['axes.unicode_minus'] = False

# 读取债券收益率数据
data = pd.read_csv(r'D:\389717562\WPS云盘\WPS\代码库\模版\不同曲线投资顺序分析\债券收益率数据.csv')
data['dt'] = pd.to_datetime(data['dt'])
cycles_df = pd.read_csv(r'D:\389717562\WPS云盘\WPS\代码库\模版\不同曲线投资顺序分析\收益率下行周期标注.csv')

class Strategy:
    def __init__(self, bond_type, term, credit_level=None):
        self.bond_type = bond_type
        self.term = term
        self.credit_level = credit_level
    
    def __str__(self):
        if self.credit_level:
            return f"{self.bond_type}_{self.term}_{self.credit_level}资质"
        return f"{self.bond_type}_{self.term}"

class PortfolioStrategy:
    def __init__(self, initial_amount=1_000_000_000):
        self.initial_amount = initial_amount
        
        # 债券类型映射
        self.TYPE_MAPPING = {
            '利率债': ['国债'],
            '金融债': ['二永'],
            '信用债': ['城投']
        }
        
        # 评级映射
        self.RATING_MAPPING = {
            '高资质': ['AAA', 'AA+'],
            '中资质': ['AA'],
            '弱资质': ['AA(2)', 'AA-']
        }
    
    def generate_dimension_strategies(self):
        """生成三个维度��略组合"""
        
        # 1. 品种维度策略（固定久期为中长期，资质为高资质）
        type_strategies = [
            # 利率债优先
            [
                ('利率债', '中长期', None),
                ('金融债', '中长期', '高资质'),
                ('信用债', '中长期', '高资质')
            ],
            [
                ('利率债', '中长期', None),
                ('信用债', '中长期', '高资质'),
                ('金融债', '中长期', '高资质')
            ],
            # 金融债优先
            [
                ('金融债', '中长期', '高资质'),
                ('信用债', '中长期', '高资质'),
                ('利率债', '中长期', None)
            ],
            [
                ('金融债', '中长期', '高资质'),
                ('利率债', '中长期', None),
                ('信用债', '中长期', '高资质')    
            ],
            # 信用债优先
            [
                ('信用债', '中长期', '高资质'),
                ('金融债', '中长期', '高资质'),
                ('利率债', '中长期', None)
            ],
            [
                ('信用债', '中长期', '高资质'),
                ('利率债', '中长期', None),
                ('金融债', '中长期', '高资质') 
            ]
        ]
        
        # 2. 久期维度策略（固定品种为利率债，资质为高资质）
        term_strategies = [
            # 长久期优先
            [
                ('利率债', '超长期', None),
                ('信用债', '长期', '中资质'),
                ('信用债', '中长期', '中资质'),
                ('信用债', '短期', '中资质')
            ],
            # 短久期优先
            [
                ('信用债', '短期', '中资质'),
                ('信用债', '中长期', '中资质'),
                ('信用债', '长期', '中资质'),
                ('利率债', '超长期', None)
            ]
        ]
        
        # 3. 资质维度策略（固定品种为信用债，久期为长期）
        credit_strategies = [
            # 高资质优先
            [
                ('信用债', '中长期', '高资质'),
                ('信用债', '中长期', '中资质'),
                ('信用债', '中长期', '弱资质')
            ],
            # 弱资质优先
            [
                ('信用债', '中长期', '弱资质'),
                ('信用债', '中长期', '中资质'),
                ('信用债', '中长期', '高资质')
            ]
        ]
        
        return {
            '品种维度': type_strategies,
            '久期维度': term_strategies,
            '资质维度': credit_strategies
        }
    
    def get_period_return(self, start_date, end_date, strategy):
        """计算特定策略在特定时期的收益"""
        # ��建数据筛选条件
        conditions = [
            (data['dt'] >= start_date),
            (data['dt'] <= end_date),
            (data['term'] == strategy.term)
        ]
        
        # 根据类型筛选
        if strategy.bond_type == '利率债':
            conditions.append(data['bond_type'].isin(self.TYPE_MAPPING['利率债']))
        elif strategy.bond_type == '金融债':
            conditions.append(data['bond_type'].isin(self.TYPE_MAPPING['金融债']))
        else:  # 信用债
            conditions.append(data['bond_type'].isin(self.TYPE_MAPPING['信用债']))
        
        # 根据资质等级筛选评级
        if strategy.credit_level:
            conditions.append(data['rating'].isin(self.RATING_MAPPING[strategy.credit_level]))
        
        # 应用筛选条件
        period_data = data[np.all(conditions, axis=0)]
        
        if period_data.empty:
            return 0
        
        start_yield = period_data.iloc[0]['yield_rate'] / 100
        end_yield = period_data.iloc[-1]['yield_rate'] / 100
        duration = self.get_duration(strategy.term)
        period_days = (end_date - start_date).days
        
        return self.calculate_bond_return(start_yield, end_yield, duration, period_days)


    def split_period(self, start_date, end_date, n_splits):
        """
        将时间段等分为n个子期间
        
        Parameters:
        -----------
        start_date : datetime
            起始日期
        end_date : datetime
            结束日期
        n_splits : int
            需要分割的份数
            
        Returns:
        --------
        list of tuples
            每个元组包含子期间的(起始日期, 结束日期)
        """
        # 确保输入的是datetime类型
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
        
        # 计算总天数
        total_days = (end_date - start_date).days
        # 计算每个子期间的天数
        days_per_split = total_days // n_splits
        
        # 生成子期间
        periods = []
        for i in range(n_splits):
            if i == n_splits - 1:
                # 最后一个子期间直接使用结束日期，避免舍入误差
                period_end = end_date
            else:
                period_end = start_date + pd.Timedelta(days=(i + 1) * days_per_split)
            
            period_start = start_date + pd.Timedelta(days=i * days_per_split)
            periods.append((period_start, period_end))
            
            # 调试信息
            print(f"子期间 {i+1}: {period_start.date()} 至 {period_end.date()} "
                  f"({(period_end - period_start).days}天)")
        
        return periods

    def analyze_dimension_performance(self, dimension_strategies, cycle_id):
        """分析某个维度策略的表现"""
        results = []
        cycle_info = cycles_df[cycles_df['cycle'] == cycle_id].iloc[0]
        start_date = pd.to_datetime(cycle_info['start_date'])
        end_date = pd.to_datetime(cycle_info['end_date'])
        
        print(f"\n{'='*80}")
        print(f"分析周期 {cycle_id}: {start_date.date()} 至 {end_date.date()}")
        print(f"收益率环境: {cycle_info['start_yield']:.2f}% → {cycle_info['end_yield']:.2f}% (变动 {cycle_info['yield_change']:+.2f}%)")
        print(f"{'='*80}")
        
        for strategy_sequence in dimension_strategies:
            print(f"\n{'-'*60}")
            print(f"执行策略序列: {' → '.join(str(Strategy(*s)) for s in strategy_sequence)}")
            print(f"{'-'*60}")
            
            portfolio_value = self.initial_amount
            returns_sequence = []
            
            # 将周期分成子期间
            sub_periods = self.split_period(start_date, end_date, len(strategy_sequence))
            
            for i, ((period_start, period_end), (bond_type, term, credit_level)) in enumerate(
                zip(sub_periods, strategy_sequence)
            ):
                strategy = Strategy(bond_type, term, credit_level)
                print(f"\n执行第 {i+1} 阶段策略:")
                print(f"时间: {period_start.date()} → {period_end.date()}")
                print(f"策略: {strategy}")
                
                # 获取期初和期末的收益率
                start_yields = self.get_period_yields(strategy, period_start, period_end)
                end_yields = self.get_period_yields(strategy, period_start, period_end)
                
                print(f"\n策略 {i+1} 数据统计:")
                print("期初收益率:")
                if not start_yields.empty:
                    print(f"{start_yields.iloc[0]:.4f}%")
                else:
                    print("未找到符合条件的债券")
                
                print("\n期末收益率:")
                if not end_yields.empty:
                    print(f"{end_yields.iloc[-1]:.4f}%")
                else:
                    print("未找到符合条件的债券")
                
                if not start_yields.empty and not end_yields.empty:
                    start_yield = start_yields.iloc[0] / 100
                    end_yield = end_yields.iloc[-1] / 100
                    duration = self.get_duration(strategy.term)
                    sub_period_days = (period_end - period_start).days
                    
                    print("\n收益率计算详细过程:")
                    print(f"期初收益率: {start_yield:.4%}")
                    print(f"期末收益率: {end_yield:.4%}")
                    print(f"收益率变动: {end_yield - start_yield:.4%}")
                    print(f"修正久期: {duration:.1f}年")
                    print(f"持有天数: {sub_period_days}天")
                    
                    # 计算该策略在子期间的收益
                    period_return = self.calculate_bond_return(
                        start_yield,
                        end_yield,
                        duration,
                        sub_period_days
                    )
                    
                    # 更新组合价值
                    old_value = portfolio_value
                    portfolio_value *= (1 + period_return)
                    value_change = portfolio_value - old_value
                    
                    print(f"\n本期收益计算:")
                    print(f"期初组合价值: {old_value:,.2f}元")
                    print(f"收益率: {period_return:.4%}")
                    print(f"价值变动: {value_change:,.2f}元")
                    print(f"期末组合价值: {portfolio_value:,.2f}元")
                    
                    returns_sequence.append(period_return)
                else:
                    returns_sequence.append(0)
                    print(f"\n警告：未找到符合条件的债券数据")
                    print("期初数据筛选条件:")
                    print(f"- 期限: {strategy.term}")
                    print(f"- 债券类型: {self.TYPE_MAPPING[strategy.bond_type]}")
                    if strategy.bond_type != '利率债':
                        print(f"- 评级: {self.RATING_MAPPING[strategy.credit_level.replace('资质资质', '资质')]}")
            
            # 计算整体收益率
            total_return = (portfolio_value - self.initial_amount) / self.initial_amount
            annual_return = total_return * (365 / (end_date - start_date).days)
            
            print(f"\n策略序列总结:")
            print(f"总收益率: {total_return:.4%}")
            print(f"年化收益率: {annual_return:.4%}")
            print(f"各阶段收益率: {[f'{r:.4%}' for r in returns_sequence]}")
            
            results.append({
                'cycle_id': cycle_id,
                'strategy_sequence': ' → '.join(str(Strategy(*s)) for s in strategy_sequence),
                'total_return': total_return,
                'annual_return': annual_return,
                'returns_sequence': returns_sequence
            })
        
        return results

    def get_duration(self, term):
        """根据期限获取估算的修正久期"""
        duration_map = {
            '短期': 0.5,      # 0-1年，假设平均久期0.5年
            '中短期': 2.0,    # 1-3年，假设平均久期2年
            '中长期': 4.0,    # 3-5年，假设平均久期4年
            '长期': 7.0,      # 5年以上，假设平均久期7年
            '超长期': 15.0    # 20年以上，假设平均久期15年
        }
        return duration_map[term]
    
    def calculate_bond_return(self, start_yield, end_yield, duration, period_days):
        """计算债券在持有期间的总收益率"""
        print("\n收益率计算详细过程:")
        print(f"期初收益率: {start_yield:.4%}")
        print(f"期末收益率: {end_yield:.4%}")
        print(f"修正久期: {duration:.1f}年")
        print(f"持有天数: {period_days}天")
        
        # 1. 票息收益（使用期初收益率作为票息率）
        coupon_return = start_yield * (period_days / 365)
        print(f"票息收益计算: {start_yield:.4%} × ({period_days} / 365) = {coupon_return:.4%}")
        
        # 2. 资本利得/损失（近似计算）
        # 收益率下降，债券价格上升，资本利得为正
        yield_change = end_yield - start_yield
        price_return = -duration * yield_change * (period_days / 365)
        print(f"收益率变动: {yield_change:.4%}")
        print(f"价格收益计算: -{duration} × {yield_change:.4%} × ({period_days} / 365) = {price_return:.4%}")
        
        # 3. 总收益
        total_return = coupon_return + price_return
        print(f"总收益 = 票息收益 + 价格收益 = {coupon_return:.4%} + {price_return:.4%} = {total_return:.4%}")
        
        return total_return

    def get_yield_curve_mapping(self):
        """定义每种策略对应的具体收益率曲线"""
        return {
            # 利率债曲线 - 直接使用国债
            ('利率债', '短期'): {'bond_type': ['国债'], 'term': '短期'},
            ('利率债', '中短期'): {'bond_type': ['国债'], 'term': '中短期'},
            ('利率债', '中长期'): {'bond_type': ['国债'], 'term': '中长期'},
            ('利率债', '长期'): {'bond_type': ['国债'], 'term': '长期'},
            ('利率债', '超长期'): {'bond_type': ['国债'], 'term': '超长期'},
            
            # 金融债曲线 - 需要特殊处理二永和存单
            ('金融债', '短期', '高资质'): {
                'bond_type': ['二永'],  # 短期主要看存单
                'term': '短期',
                'rating': ['AAA', 'AA+']
            },
            ('金融债', '中短期', '高资质'): {
                'bond_type': ['二永'],  # 中短期以上主要看二永
                'term': '中短期',
                'rating': ['AAA', 'AA+']
            },
            ('金融债', '中长期', '高资质'): {
                'bond_type': ['二永'],
                'term': '中长期',
                'rating': ['AAA', 'AA+']
            },
            ('金融债', '长期', '高资质'): {
                'bond_type': ['二永'],
                'term': '长期',
                'rating': ['AAA', 'AA+']
            },
            
            # 信用债曲线 - 城投债
            ('信用债', '短期', '高资质'): {
                'bond_type': ['城投'],
                'term': '短期',
                'rating': ['AAA', 'AA+']
            },
            ('信用债', '中短期', '高资质'): {
                'bond_type': ['城投'],
                'term': '中短期',
                'rating': ['AAA', 'AA+']
            },
            ('信用债', '中长期', '高资质'): {
                'bond_type': ['城投'],
                'term': '中长期',
                'rating': ['AAA', 'AA+']
            },
            ('信用债', '长期', '高资质'): {
                'bond_type': ['城投'],
                'term': '长期',
                'rating': ['AAA', 'AA+']
            },
            
            # 中资质
            ('信用债', '短期', '中资质'): {
                'bond_type': ['城投'],
                'term': '短期',
                'rating': ['AA']
            },
            ('信用债', '中短期', '中资质'): {
                'bond_type': ['城投'],
                'term': '中短期',
                'rating': ['AA']
            },
            ('信用债', '中长期', '中资质'): {
                'bond_type': ['城投'],
                'term': '中长期',
                'rating': ['AA']
            },
            ('信用债', '长期', '中资质'): {
                'bond_type': ['城投'],
                'term': '长期',
                'rating': ['AA']
            },

            
            # 弱资质
            ('信用债', '短期', '弱资质'): {
                'bond_type': ['城投'],
                'term': '短期',
                'rating': ['AA-']
            },
            ('信用债', '中短期', '弱资质'): {
                'bond_type': ['城投'],
                'term': '中短期',
                'rating': ['AA-']
            },
            ('信用债', '中长期', '弱资质'): {
                'bond_type': ['城投'],
                'term': '中长期',
                'rating': ['AA-']
            },
            ('信用债', '长期', '弱资质'): {
                'bond_type': ['城投'],
                'term': '长期',
                'rating': ['AA-']
            },
        }

    def get_period_yields(self, strategy, start_date, end_date):
        """获取特定策略在特定时期的收益率序列"""
        # 获取该策略对应的具体收益率曲线
        curve_mapping = self.get_yield_curve_mapping()
        strategy_key = (strategy.bond_type, strategy.term) if strategy.bond_type == '利率债' else (
            strategy.bond_type, strategy.term, strategy.credit_level)
        
        if strategy_key not in curve_mapping:
            raise ValueError(f"未找到策略 {strategy_key} 对应的收益率曲线")
        
        curve_params = curve_mapping[strategy_key]
        
        # 获取该时期内的所有交易日数据
        period_data = data[
            (data['dt'] >= start_date) & 
            (data['dt'] <= end_date)
        ].copy()
        
        # 根据具体曲线参数筛选数据
        mask = (
            period_data['bond_type'].isin(curve_params['bond_type']) & 
            (period_data['term'] == curve_params['term'])
        )
        
        if 'rating' in curve_params:
            mask &= period_data['rating'].isin(curve_params['rating'])
        
        filtered_data = period_data[mask].sort_values('dt')
        
        if filtered_data.empty:
            print(f"警告: 策略 {strategy_key} 在 {start_date} 至 {end_date} 期间没有收益率数据")
            return pd.Series()
        
        # 对于金融债特殊处理
        if strategy.bond_type == '金融债':
            # 按日期和债券类型分组计算平均收益率
            daily_yields = filtered_data.groupby(['dt', 'bond_type'])['yield_rate'].mean().reset_index()
            # 再按日期计算不同债券类���的平均值
            daily_yields = daily_yields.groupby('dt')['yield_rate'].mean()
        else:
            # 其他债券直接按日期计算平均值
            daily_yields = filtered_data.groupby('dt')['yield_rate'].mean()
        
        # 输出调试信息
        print(f"\n策略 {strategy_key} 收益率数据:")
        print(f"使用曲线参数: {curve_params}")
        print(f"数据点数: {len(daily_yields)}")
        if not daily_yields.empty:
            print(f"期初收益率: {daily_yields.iloc[0]:.4f}%")
            print(f"期末收益率: {daily_yields.iloc[-1]:.4f}%")
            print(f"收益率变动: {daily_yields.iloc[-1] - daily_yields.iloc[0]:.4f}%")
            if strategy.bond_type == '金融债':
                print("\n使用的债券类型及其数量:")
                type_counts = filtered_data['bond_type'].value_counts()
                print(type_counts)
        
        return daily_yields


class PortfolioVisualizer:
    def __init__(self):
        self.colors = ['#2878B5', '#9AC9DB', '#C82423', '#F8AC8C', '#1B9E77', '#D95F02']
        self.fig_size = (12, 8)
        self.title_size = 14
        self.label_size = 12
        self.tick_size = 10
        self.chinese_font = chinese_font
        
        # 设置全局样式
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = self.fig_size
        plt.rcParams['axes.titlesize'] = self.title_size
        plt.rcParams['axes.labelsize'] = self.label_size
        plt.rcParams['xtick.labelsize'] = self.tick_size
        plt.rcParams['ytick.labelsize'] = self.tick_size
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['grid.linestyle'] = '--'
    
    def plot_market_cycle_analysis(self, df, dimension):
        """绘制不同策略的收益率对比"""
        # 按周期分组计算每个策略的年化收益率
        cycle_performance = df.pivot_table(
            index='cycle_id', 
            columns='strategy_sequence', 
            values='annual_return',
            aggfunc='mean'
        )
        
        # 创建图表
        plt.figure(figsize=(15, 8))
        
        # 设置柱状图的位置
        n_strategies = len(cycle_performance.columns)
        n_cycles = len(cycle_performance.index)
        width = 0.8 / n_strategies
        
        # 绘制柱状图
        for i, strategy in enumerate(cycle_performance.columns):
            x = np.arange(n_cycles) + i * width - (n_strategies-1) * width/2
            plt.bar(x, cycle_performance[strategy], width, 
                   label=strategy.replace(' → ', '\n→\n'),
                   color=self.colors[i % len(self.colors)])
        
        # 设置图表标签
        if chinese_font is not None:
            plt.title(f'历史不同行情时期{dimension}年化收益率对比', fontproperties=chinese_font, fontsize=14, pad=20)
            plt.xlabel('观察期', fontproperties=chinese_font, fontsize=12)
            plt.ylabel('年化收益率', fontproperties=chinese_font, fontsize=12)
        else:
            plt.title('Strategy Returns Comparison', fontsize=14, pad=20)
            plt.xlabel('Period', fontsize=12)
            plt.ylabel('Annual Return', fontsize=12)
        
        # 设置x轴刻度
        cycle_labels = [f'周期{i}\n{cycles_df[cycles_df["cycle"]==i]["start_date"].iloc[0][:7]}' 
                       for i in cycle_performance.index]
        plt.xticks(np.arange(n_cycles), cycle_labels, fontproperties=chinese_font if chinese_font is not None else None)
        
        # 设置y轴为百分比格式
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        
        # 添加网格线
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # 添加图例
        if chinese_font is not None:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                      prop=chinese_font, fontsize=10, frameon=True)
        else:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
                      fontsize=10, frameon=True)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(f'{dimension}策略收益率对比.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 生成详细的分析文本
        with open(f'{dimension}策略分析报告.txt', 'w', encoding='utf-8') as f:
            f.write(f"{dimension}策略分析报告\n")
            f.write("="*50 + "\n\n")
            
            # 1. 各周期最优策略
            f.write("各周期最优策略:\n")
            f.write("-"*30 + "\n")
            for cycle_id in cycle_performance.index:
                period_returns = cycle_performance.loc[cycle_id]
                best_strategy = period_returns.idxmax()
                best_return = period_returns.max()
                cycle_row = cycles_df[cycles_df['cycle'] == cycle_id].iloc[0]
                
                f.write(f"\n周期 {cycle_id} ({cycle_row['start_date']} 至 {cycle_row['end_date']})\n")
                f.write(f"收益率变动: {cycle_row['start_yield']:.2f}% → {cycle_row['end_yield']:.2f}% (变动 {cycle_row['yield_change']:+.2f}%)\n")
                f.write(f"最优策略: {best_strategy}\n")
                f.write(f"年化收益率: {best_return:.2%}\n")
                
                # 添加该周期所有策略的排名
                f.write("策略排名:\n")
                for rank, (strat, ret) in enumerate(period_returns.sort_values(ascending=False).items(), 1):
                    f.write(f"  {rank}. {strat}: {ret:.2%}\n")
                f.write("\n")
            
            # 2. 策略整体统计
            f.write("\n策略整体统计:\n")
            f.write("-"*30 + "\n")
            stats = {
                '平均年化收益率': cycle_performance.mean(),
                '收益率标准差': cycle_performance.std(),
                '最高收益率': cycle_performance.max(),
                '最低收益率': cycle_performance.min(),
                '胜率': (cycle_performance == cycle_performance.max(axis=1).values.reshape(-1, 1)).mean()
            }
            
            stats_df = pd.DataFrame(stats)
            f.write("\n" + stats_df.to_string(float_format=lambda x: '{:.2%}'.format(x)))
            
            # 3. 策略稳定性排名
            f.write("\n\n策略稳定性排名 (按标准差从到高):\n")
            f.write("-"*30 + "\n")
            stability_ranking = stats_df['收益率标准差'].sort_values()
            for rank, (strategy, std) in enumerate(stability_ranking.items(), 1):
                mean_return = stats_df.loc[strategy, '平均年化收益率']
                f.write(f"{rank}. {strategy}\n")
                f.write(f"   平均收益率: {mean_return:.2%}\n")
                f.write(f"   波动率: {std:.2%}\n")
        
        # 保存策略统计结果
        stats_df.to_csv(f'{dimension}策略统计.csv', encoding='utf-8-sig', float_format='%.4f')
    
    def plot_strategy_comparison(self, df, dimension):
        """绘制策略对比图"""
        plt.figure(figsize=self.fig_size)
        
        # 计算每个策略的平均表现
        strategy_means = df.groupby('strategy_sequence')['annual_return'].mean().sort_values(ascending=True)
        
        # 创建柱状图
        bars = plt.barh(range(len(strategy_means)), strategy_means.values, 
                       color=self.colors[:len(strategy_means)])
        
        # 设置y轴标签
        plt.yticks(range(len(strategy_means)), strategy_means.index, 
                  fontproperties=self.chinese_font)
        
        # 添加数值标签
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width, i, f'{width:.2%}', 
                    va='center', fontsize=self.tick_size,
                    fontproperties=self.chinese_font)
        
        plt.title(f'{dimension}策略年化收益率对比', fontproperties=self.chinese_font)
        plt.xlabel('年化收益率', fontproperties=self.chinese_font)
        plt.ylabel('策略顺序', fontproperties=self.chinese_font)
        
        plt.tight_layout()
        plt.savefig(f'{dimension}策略对比.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_strategy_stability(self, df, dimension):
        """绘制策略稳定性分析图"""
        fig = plt.figure(figsize=(15, 6))
        gs = gridspec.GridSpec(1, 2, width_ratios=[2, 1])
        
        # 1. 箱线图
        ax1 = plt.subplot(gs[0])
        bp = ax1.boxplot([group['annual_return'].values for name, group in df.groupby('strategy_sequence')],
                        labels=df['strategy_sequence'].unique(),
                        patch_artist=True)
        
        # 设置箱线图颜色
        for i, box in enumerate(bp['boxes']):
            box.set(facecolor=self.colors[i % len(self.colors)])
        
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45, ha='right',
                           fontproperties=self.chinese_font)
        ax1.set_title('策略收益率分布', fontproperties=self.chinese_font)
        ax1.set_xlabel('策���顺序', fontproperties=self.chinese_font)
        ax1.set_ylabel('年化收益率', fontproperties=self.chinese_font)
        
        # 2. 密度图
        ax2 = plt.subplot(gs[1])
        for i, (name, group) in enumerate(df.groupby('strategy_sequence')):
            sns.kdeplot(data=group['annual_return'], ax=ax2, label=name,
                       color=self.colors[i % len(self.colors)])
        
        ax2.set_title('策略收益率密度分布', fontproperties=self.chinese_font)
        ax2.set_xlabel('年化收益率', fontproperties=self.chinese_font)
        ax2.set_ylabel('密度', fontproperties=self.chinese_font)
        ax2.legend(prop=self.chinese_font, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.savefig(f'{dimension}策略稳定性分析.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_cumulative_returns(self, df, dimension):
        """绘制累计收益曲线"""
        plt.figure(figsize=self.fig_size)
        
        for i, strategy in enumerate(df['strategy_sequence'].unique()):
            strategy_data = df[df['strategy_sequence'] == strategy]
            cumulative_returns = (1 + strategy_data['annual_return']).cumprod()
            
            plt.plot(range(len(cumulative_returns)), cumulative_returns,
                    label=strategy, linewidth=2, color=self.colors[i % len(self.colors)])
        
        plt.title(f'{dimension}策略累计收益对比', fontproperties=self.chinese_font)
        plt.xlabel('观察期数', fontproperties=self.chinese_font)
        plt.ylabel('累计收益倍数', fontproperties=self.chinese_font)
        plt.legend(prop=self.chinese_font, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(f'{dimension}累计收益.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    # 清理已有的输出文件
    print("\n清理已有输出文件...")
    clean_output_files()
    
    strategy = PortfolioStrategy()
    visualizer = PortfolioVisualizer()
    dimension_strategies = strategy.generate_dimension_strategies()
    
    # 存储所有维度的分析结果
    all_results = {dimension: [] for dimension in dimension_strategies.keys()}
    
    # 对每个维度进行分析
    for dimension, strategies in dimension_strategies.items():
        print(f"\n分析{dimension}策略:")
        print(f"策略组合数量: {len(strategies)}")
        
        # 对每个周期进行分析
        for cycle_id in data['cycle_id'].unique():
            results = strategy.analyze_dimension_performance(strategies, cycle_id)
            all_results[dimension].extend(results)
        
        # 转换为DataFrame
        df = pd.DataFrame(all_results[dimension])
        
        # 生成可视化图表
        visualizer.plot_strategy_comparison(df, dimension)
        visualizer.plot_strategy_stability(df, dimension)
        visualizer.plot_market_cycle_analysis(df, dimension)
        visualizer.plot_cumulative_returns(df, dimension)
        
        # 保存详细结果
        df.to_csv(f'{dimension}分析结果.csv', index=False, encoding='utf-8-sig')
        
        # 计算并保存统计信息
        strategy_performance = df.groupby('strategy_sequence').agg({
            'annual_return': ['mean', 'std', 'min', 'max'],
            'total_return': ['mean', 'std', 'min', 'max']
        }).round(4)
        
        strategy_performance.columns = [
            '年化收益率均值', '年化收益率标准差', '年化收益率最小值', '年化收益率最大值',
            '总收益率均值', '总收益率标准差', '总收益率最小值', '总收益率最大值'
        ]
        strategy_performance.to_csv(f'{dimension}策略统计.csv', encoding='utf-8-sig')
        
        # 打印关键统计信息
        print(f"\n{dimension}策略表现统计:")
        print("\n最优策略组合:")
        best_strategy = df.groupby('strategy_sequence')['annual_return'].mean().idxmax()
        best_stats = strategy_performance.loc[best_strategy]
        print(f"策略序: {best_strategy}")
        print(f"平均年化收益率: {best_stats['年化收益率均值']:.2%}")
        print(f"收益率波动率: {best_stats['年化收益率标准差']:.2%}")
        print(f"最大年化收益率: {best_stats['年化收益率最大值']:.2%}")
        print(f"最小年化收益率: {best_stats['年化收益率最小值']:.2%}")
    
    print("\n分析完成，结果已保存到相应的CSV文件和图表中")

if __name__ == "__main__":
    main() 