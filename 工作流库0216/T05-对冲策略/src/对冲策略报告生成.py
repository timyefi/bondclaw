#同花顺理财
import pandas as pd
import json
import chardet
from time import sleep
import time
import requests
import pandas as pd
import random
import pymysql
import json
import sys
import sqlalchemy
from datetime import datetime,date, timedelta
from bs4 import BeautifulSoup
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')
from WindPy import w
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import webbrowser
import os
from jinja2 import Template

w.start()
class MarketAnalyzer:
    def __init__(self,trade_code1,trade_code2,name1,name2):
        print("初始化MarketAnalyzer...")
        self.setup_database()
        self.trade_code1 = trade_code1
        self.trade_code2 = trade_code2
        self.name1 = name1
        self.name2 = name2
    def setup_database(self):
        try:
            print("创建数据库连接...")
            self.sql_engine = sqlalchemy.create_engine(
                'mysql+pymysql://%s:%s@%s:%s/%s' % (
                    'hz_work',
                    'Hzinsights2015',
                    'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                    '3306',
                    'yq',
                ), poolclass=sqlalchemy.pool.NullPool
            )
            self.cursor = self.sql_engine.connect()
            print("数据库连接创建成功")
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise

    def setup_display(self):
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

    def get_data(self,trade_code1,trade_code2):
        """获取历史数据"""
        try:
            print("获取历史数据...")
            
            # 获取可转债上市以来的所有数据
            xiaomi_sql = f"""
            SELECT dt, open, high, low, close, volume, vwap
            FROM marketinfo_fund 
            WHERE trade_code = '{self.trade_code1}'
            AND dt >= '2023-01-14'
            ORDER BY dt
            """
            
            print(f"获取{self.name1}数据...")
            xiaomi_df = pd.read_sql(xiaomi_sql, self.sql_engine)
            print(f"获取到{self.name1}数据 {len(xiaomi_df)} 条")
            print(f"{self.name1}数据日期范围: {xiaomi_df['dt'].min()} 至 {xiaomi_df['dt'].max()}")
            
            # 获取对应时间段的30ETF数据
            etf_sql = f"""
            SELECT dt, open, high, low, close, volume, vwap
            FROM marketinfo_fund 
            WHERE trade_code = '{self.trade_code2}'
            AND dt >= '2023-01-14'
            ORDER BY dt
            """
            
            print(f"获取{self.name2}数据...")
            etf_df = pd.read_sql(etf_sql, self.sql_engine)
            print(f"获取到{self.name2}数据 {len(etf_df)} 条")
            print(f"{self.name2}数据日期范围: {etf_df['dt'].min()} 至 {etf_df['dt'].max()}")
            
            # 合并数据并处理缺失值
            print("\n合并数据前行数:")
            print(f"{self.name1}: {len(xiaomi_df)}")
            print(f"{self.name2}: {len(etf_df)}")
            
            self.df = pd.merge(xiaomi_df, etf_df, on='dt', how='inner',suffixes=('_xiaomi', ''))
            print(f"合并后行数: {len(self.df)}")
            
            self.df['dt'] = pd.to_datetime(self.df['dt'])
            self.df = self.df.set_index('dt')
            
            # 计算收益率
            self.df['return_xiaomi'] = self.df['close_xiaomi'].pct_change()
            self.df['return_etf'] = self.df['close'].pct_change()
            
            print("\n计算收益率后行数:", len(self.df))
            print("\n最后一天的数据:")
            print(self.df.tail(1))
            
            # 处理异常值，但保留最后一天的数据
            last_day_data = self.df.iloc[[-1]]
            self.df = self.df.iloc[:-1]  # 暂时移除最后一天
            
            # 处理异常值
            mask = (abs(self.df['return_xiaomi']) < 0.2) & (abs(self.df['return_etf']) < 0.2)
            removed_dates = self.df[~mask].index
            if len(removed_dates) > 0:
                print("\n被移除的异常日期:")
                for date in removed_dates:
                    print(f"{date.strftime('%Y-%m-%d')}: {self.name1}收益率={self.df.loc[date, 'return_xiaomi']:.2%}, {self.name2}收益率={self.df.loc[date, 'return_etf']:.2%}")
            
            self.df = self.df[mask]
            
            # 添加回最后一天的数据
            self.df = pd.concat([self.df, last_day_data])
            
            print("\n处理异常值后的最后几条数据:")
            print(self.df.tail())
            
            print(f"\n最终可用数据条数: {len(self.df)}")
            print(f"数据日期范围: {self.df.index[0].strftime('%Y-%m-%d')} 至 {self.df.index[-1].strftime('%Y-%m-%d')}")
            
            return True
            
        except Exception as e:
            print(f"获取数据失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    def analyze_market_conditions(self):
        """分析当前市场环境"""
        try:
            latest = self.df.iloc[-1]
            recent = self.df.iloc[-20:]
            
            # 1. 波动率环境
            vol_regime = {
                f'{self.name1}波动率': self.df['return_xiaomi'].std() * np.sqrt(252),
                f'{self.name2}波动率': self.df['return_etf'].std() * np.sqrt(252),
                '波动率比值': (self.df['return_xiaomi'].std() / self.df['return_etf'].std()),
                '波动率百分位': {
                    f'{self.name1}': stats.percentileofscore(self.df['return_xiaomi'].rolling(20).std(), self.df['return_xiaomi'].std()),
                    f'{self.name2}': stats.percentileofscore(self.df['return_etf'].rolling(20).std(), self.df['return_etf'].std())
                }
            }
            
            # 2. 相关性环境
            correlation = self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf'])
            corr_regime = {
                '当前相关性': correlation.iloc[-1],
                '相关性稳定性': correlation.std(),
                '相关性趋势': correlation.iloc[-1] - correlation.iloc[-20]
            }
            
            # 3. 趋势环境
            def calculate_rsi(returns, periods=14):
                delta = returns
                gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))
            
            trend_regime = {
                f'{self.name1}RSI': calculate_rsi(self.df['return_xiaomi']).iloc[-1],
                f'{self.name2} RSI': calculate_rsi(self.df['return_etf']).iloc[-1],
                f'{self.name1}动能': self.df['return_xiaomi'].mean() / self.df['return_xiaomi'].std(),
                f'{self.name2}动能': self.df['return_etf'].mean() / self.df['return_etf'].std()
            }
            
            return {
                '波动率环境': vol_regime,
                '相关性环境': corr_regime,
                '趋势环境': trend_regime
            }
            
        except Exception as e:
            print(f"分析市场环境失败: {str(e)}")
            return None

    def get_historical_scenarios(self):
        """识别历史上的类似场景"""
        try:
            current = self.df.iloc[-1]
            
            # 计算滚动波动率
            rolling_vol_xiaomi = self.df['return_xiaomi'].rolling(20).std() * np.sqrt(252)
            rolling_vol_etf = self.df['return_etf'].rolling(20).std() * np.sqrt(252)
            rolling_correlation = self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf'])
            
            # 定义相似性条件
            current_vol_xiaomi = rolling_vol_xiaomi.iloc[-1]
            current_vol_etf = rolling_vol_etf.iloc[-1]
            current_corr = rolling_correlation.iloc[-1]
            
            vol_similar = (
                (rolling_vol_xiaomi > current_vol_xiaomi * 0.8) &
                (rolling_vol_xiaomi < current_vol_xiaomi * 1.2) &
                (rolling_vol_etf > current_vol_etf * 0.8) &
                (rolling_vol_etf < current_vol_etf * 1.2)
            )
            
            corr_similar = (
                (rolling_correlation > current_corr - 0.2) &
                (rolling_correlation < current_corr + 0.2)
            )
            
            # 找到类似场景
            similar_days = self.df[vol_similar & corr_similar]
            
            # 分析这些场景下的表现
            scenarios = []
            for i in range(len(similar_days) - 20):
                scenario_start = similar_days.index[i]
                forward_20d = self.df.loc[scenario_start:].head(20)
                
                if len(forward_20d) == 20:
                    scenario = {
                        '日期': scenario_start,
                        f'{self.name1}20日收益': (forward_20d['close_xiaomi'].iloc[-1] / forward_20d['close_xiaomi'].iloc[0] - 1),
                        f'{self.name2}20日收益': (forward_20d['close'].iloc[-1] / forward_20d['close'].iloc[0] - 1),
                        '相关性': rolling_correlation.loc[scenario_start:scenario_start + timedelta(days=20)].mean(),
                        '波动率比值': (rolling_vol_xiaomi.loc[scenario_start:scenario_start + timedelta(days=20)] / 
                                  rolling_vol_etf.loc[scenario_start:scenario_start + timedelta(days=20)]).mean()
                    }
                    scenarios.append(scenario)
            
            return pd.DataFrame(scenarios)
            
        except Exception as e:
            print(f"分析历史场景失败: {str(e)}")
            import traceback
            print("详细错误信息:")
            print(traceback.format_exc())
            return pd.DataFrame()  # 返回空DataFrame而不是None

    def calculate_optimal_weights(self):
        """计算最优配置权重"""
        # 计算风险平价权重
        vol_xiaomi = self.df['return_xiaomi'].rolling(20).std()
        vol_etf = self.df['return_etf'].rolling(20).std()
        w_rp_xiaomi = 1/vol_xiaomi / (1/vol_xiaomi + 1/vol_etf)
        w_rp_etf = 1 - w_rp_xiaomi
        
        # 计算动态调整权重
        corr = self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf'])
        momentum_xiaomi = self.df['return_xiaomi'].rolling(60).mean()
        momentum_etf = self.df['return_etf'].rolling(60).mean()
        
        # 基础权重
        base_weight = 0.6
        
        # 相关性调整
        corr_adj = -0.2 * corr
        
        # 动量调整
        mom_adj = 0.1 * (momentum_xiaomi > momentum_etf).astype(float)
        
        # 波动率调整
        vol_adj = -0.1 * (vol_xiaomi > vol_etf).astype(float)
        
        # 最终动态权重
        w_dyn_xiaomi = (base_weight + corr_adj + mom_adj + vol_adj).clip(0.3, 0.8)
        w_dyn_etf = 1 - w_dyn_xiaomi
        
        return {
            '风险平价': {
                f'{self.name1}权重': w_rp_xiaomi.iloc[-1],
                f'{self.name2}权重': w_rp_etf.iloc[-1],
                '计算依据': f'基于20日波动率（{self.name1}: {vol_xiaomi.iloc[-1]:.2%}, {self.name2}: {vol_etf.iloc[-1]:.2%}）'
            },
            '动态调整': {
                f'{self.name1}权重': w_dyn_xiaomi.iloc[-1],
                f'{self.name2}权重': w_dyn_etf.iloc[-1],
                '计算依据': f'相关性:{corr.iloc[-1]:.2f}, 动量比:{(momentum_xiaomi/momentum_etf).iloc[-1]:.2f}'
            }
        }
    
    def generate_allocation_advice(self, xiaomi_shares, etf_shares, cash):
        """生成具体的配置建议"""
        # 获取最新价格
        xiaomi_price = self.df['close_xiaomi'].iloc[-1]
        etf_price = self.df['close'].iloc[-1]
        
        # 计算当前持仓市值
        xiaomi_value = xiaomi_shares * xiaomi_price
        etf_value = etf_shares * etf_price
        total_value = xiaomi_value + etf_value + cash
        
        # 获取最优权重
        weights = self.calculate_optimal_weights()
        
        # 生成建议
        advice = []
        for strategy, w in weights.items():
            target_xiaomi = total_value * w[f'{self.name1}权重']
            target_etf = total_value * w[f'{self.name2}权重']
            
            xiaomi_diff = target_xiaomi - xiaomi_value
            etf_diff = target_etf - etf_value
            
            # 构建目标配置字典
            target_config = {
                f'{self.name1}目标持仓': f"{int(target_xiaomi / xiaomi_price)}股",
                f'{self.name2}目标持仓': f"{int(target_etf / etf_price)}份",
                f'{self.name1}目标占比': f"{w[f'{self.name1}权重']:.1%}",
                f'{self.name2}目标占比': f"{w[f'{self.name2}权重']:.1%}",
                '模拟情景': []
            }
            
            # 添加具体操作建议
            if abs(xiaomi_diff) > total_value * 0.05:  # 差异超过5%才建议调整
                action = "增配" if xiaomi_diff > 0 else "减配"
                shares = abs(int(xiaomi_diff / xiaomi_price))
                target_config['模拟情景'].append(
                    f"{action}{self.name1} {shares}股 (约{abs(xiaomi_diff):,.0f}元)"
                )
            
            if abs(etf_diff) > total_value * 0.05:
                action = "增配" if etf_diff > 0 else "减配"
                shares = abs(int(etf_diff / etf_price))
                target_config['模拟情景'].append(
                    f"{action}{self.name2} {shares}份 (约{abs(etf_diff):,.0f}元)"
                )
            
            advice.append({
                '策略': strategy,
                '目标配置': target_config,
                '计算依据': w['计算依据']
            })
        
        return advice

    def _plot_strategy_nav_comparison(self, ax):
        """绘制不同策略的历史净值对比"""
        # 计算不同策略的净值
        nav_df = pd.DataFrame(index=self.df.index)
        summary_stats = []
        
        # 定义策略列表
        strategies = {
            f'{self.name1}': (1.0, 0.0),
            f'{self.name2}': (0.0, 1.0),
            '固定配置(70/30)': (0.7, 0.3),
            '固定配置(50/50)': (0.5, 0.5),
            '风险平价': None,
            '动态调整': 'dynamic'  # 改为字符串'dynamic'以匹配calculate_strategy_nav的参数要求
        }
        
        for name, weights in strategies.items():
            # 使用统一的calculate_strategy_nav函数计算净值
            nav = self.calculate_strategy_nav(weights)
            nav_df[name] = nav
            
            # 计算策略指标
            annual_return = (nav.iloc[-1] ** (252/len(nav)) - 1)
            annual_vol = nav.pct_change().std() * np.sqrt(252)
            sharpe = (annual_return - 0.02) / annual_vol
            max_drawdown = (nav / nav.expanding().max() - 1).min()
            win_rate = (nav.pct_change() > 0).mean()
            
            summary_stats.append({
                '策略': name,
                '年化收益': annual_return,
                '夏普比率': sharpe,
                '最大回撤': max_drawdown,
                '胜率': win_rate
            })
            
            # 绘制净值曲线
            ax.plot(nav.index, nav.values, label=name, alpha=0.7, linewidth=2)
        
        # 添加重要时间点标注
        important_dates = [
            ('2020-01-23', '疫情爆发'),
            ('2021-07-01', '监管收紧'),
            ('2022-03-15', '市场底部'),
            ('2023-01-01', '复苏开始')
        ]
        
        for date, event in important_dates:
            if date in nav_df.index:
                ax.axvline(x=pd.to_datetime(date), color='gray', linestyle='--', alpha=0.3)
                ax.text(pd.to_datetime(date), ax.get_ylim()[1], event, 
                       rotation=90, verticalalignment='bottom')
        
        # 添加策略表现总结
        summary_df = pd.DataFrame(summary_stats)
        table_data = []
        for _, row in summary_df.iterrows():
            table_data.append([
                row['策略'],
                f"{row['年化收益']:.1%}",
                f"{row['夏普比率']:.2f}",
                f"{row['最大回撤']:.1%}",
                f"{row['胜率']:.1%}"
            ])
        
        table = ax.table(cellText=table_data,
                        colLabels=['策略', '年化收益', '夏普比率', '最大回撤', '胜率'],
                        loc='bottom',
                        bbox=[0, -0.3, 1, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        
        ax.set_title('策略净值对比 (2023-至今)')
        ax.grid(True)
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        # 调整策略说明位置和样式
        strategy_desc = """
策略说明：
        """
        # 将说明放在图表下方，避免与曲线重叠
        ax.text(0.02, -0.25, strategy_desc, transform=ax.transAxes,
                va='top', bbox=dict(facecolor='white', alpha=0.9, pad=1.0),
                fontproperties='SimHei', fontsize=10)
        
    def _plot_market_environment(self, ax):
        """绘制市场环境分析"""
        # 计算关键指标
        periods = [20, 60, 120]
        indicators = {}
        
        for period in periods:
            vol_xiaomi = self.df['return_xiaomi'].rolling(period).std() * np.sqrt(252)
            vol_etf = self.df['return_etf'].rolling(period).std() * np.sqrt(252)
            correlation = self.df['return_xiaomi'].rolling(period).corr(self.df['return_etf'])
            
            indicators[f'{period}日'] = {
                f'{self.name1}波动率': vol_xiaomi.iloc[-1],
                f'{self.name2}波动率': vol_etf.iloc[-1],
                '相关性': correlation.iloc[-1]
            }
        
        # 创建热力图数据
        data = np.array([[indicators[p][i] for p in indicators.keys()] 
                        for i in [f'{self.name1}波动率', f'{self.name2}波动率', '相关性']])
        
        # 绘制热力图
        im = ax.imshow(data, cmap='RdYlGn_r')
        
        # 添加数值标签
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                text = f'{data[i, j]:.2f}'
                ax.text(j, i, text, ha='center', va='center')
        
        # 设置坐标轴
        ax.set_xticks(np.arange(len(periods)))
        ax.set_yticks(np.arange(3))
        ax.set_xticklabels([f'{p}日' for p in periods])
        ax.set_yticklabels([f'{self.name1}波动率', f'{self.name2}波动率', '相关性'])
        
        # 添加市场环境结论
        current_vol_ratio = data[0, 0] / data[1, 0]
        current_corr = data[2, 0]
        
        conclusion = []
        if current_vol_ratio > 2:
            conclusion.append('波动率差异大\n建议增加对冲')
        if current_corr < -0.3:
            conclusion.append('相关性强\n对冲效果好')
        
        if conclusion:
            ax.text(1, -0.5, '\n'.join(conclusion), 
                   ha='center', va='top', bbox=dict(facecolor='white', alpha=0.8))
        
        ax.set_title('市场环境热力图')
        
#         # 调整市场环境说明位置和样式
#         market_desc = """
# 市场环境指标说明：
#         """
#         # 将说明放在热力图右侧
#         ax.text(1.4, 0.5, market_desc, transform=ax.transAxes,
#                 va='center', bbox=dict(facecolor='white', alpha=0.9, pad=1.0),
#                 fontproperties='SimHei', fontsize=10)

    def _plot_position_analysis(self, ax, current_xiaomi_shares, current_etf_shares):
        """绘制持仓分析"""
        # 计算当前和目标持仓
        current_xiaomi = self.df['close_xiaomi'].iloc[-1]
        current_etf = self.df['close'].iloc[-1]
        
        # 计算目标权重
        vol_xiaomi = self.df['return_xiaomi'].std() * np.sqrt(252)
        vol_etf = self.df['return_etf'].std() * np.sqrt(252)
        correlation = self.df['return_xiaomi'].corr(self.df['return_etf'])
        
        hedge_ratio = vol_xiaomi / vol_etf
        correlation_adj = 1 + (correlation * 0.2)
        final_ratio = hedge_ratio * correlation_adj
        
        target_xiaomi = 1 / (1 + final_ratio)
        target_etf = 1 - target_xiaomi
        
        # 绘制双饼图
        size = 0.3
        vals = np.array([[target_xiaomi, target_etf], 
                        [current_xiaomi/(current_xiaomi + current_etf), 
                         current_etf/(current_xiaomi + current_etf)]])
        
        cmap = plt.get_cmap("tab20c")
        outer_colors = cmap(np.array([1, 2]))
        inner_colors = cmap(np.array([3, 4]))
        
        ax.pie(vals.flatten(), radius=1, colors=np.concatenate([outer_colors, inner_colors]),
               wedgeprops=dict(width=size, edgecolor='w'),
               labels=[f'目标{self.name1}', f'目标{self.name2}', f'当前{self.name1}', f'当前{self.name2}'])
        
        ax.set_title('持仓对比')
        
    def _plot_strategy_signals(self, ax):
        """绘制策略信号"""
        # 计算策略信号
        signals = {
            '趋势信号': {
                '值': self.df['close_xiaomi'].pct_change(20).iloc[-1],
                '说明': '20日收益率，>0表示上升趋势，<0表示下降趋势'
            },
            '波动信号': {
                '值': (self.df['return_xiaomi'].std() - self.df['return_etf'].std()) * np.sqrt(252),
                '说明': '年化波动率差异，>0表示可转债波动性更大，需增加对冲'
            },
            '相关信号': {
                '值': self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf']).iloc[-1],
                '说明': '20日相关系数，<0表示负相关，对冲效果好'
            },
            '动量信号': {
                '值': (self.df['close_xiaomi'].pct_change(60) - self.df['close'].pct_change(60)).iloc[-1],
                '说明': '60日动量差异，>0表示可转债相对强势'
            }
        }
        
        # 绘制信号条形图
        y_pos = np.arange(len(signals))
        signal_values = [s['值'] for s in signals.values()]
        
        bars = ax.barh(y_pos, signal_values, align='center')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(signals.keys())
        
        # 为正负值设置不同颜色
        for bar, val in zip(bars, signal_values):
            if val > 0:
                bar.set_color('red')
            else:
                bar.set_color('green')
        
        # 添加数值标签
        for i, v in enumerate(signal_values):
            ax.text(v + np.sign(v) * 0.01, i, f'{v:.2f}',
                    va='center', ha='left' if v > 0 else 'right')
        
        # # 添加信号说明
        # signal_desc = "信号说明：\n"
        # # for name, info in signals.items():
        # #     signal_desc += f"{name}：{info['说明']}\n"
        
        # # 将说明放在图表右侧
        # ax.text(1.4, 0.5, signal_desc, transform=ax.transAxes,
        #         va='center', bbox=dict(facecolor='white', alpha=0.9, pad=1.0),
        #         fontproperties='SimHei', fontsize=10)
        
        ax.set_title('策略信号强度')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3)

    def plot_market_dashboard(self, xiaomi_shares, etf_shares, cash):
        """绘制完整的市场分析仪表盘"""
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建更大的图表以适应所有内容
            fig = plt.figure(figsize=(24, 22))
            
            # 调整网格布局例，增加间距
            gs = plt.GridSpec(4, 3, height_ratios=[2, 0.5, 1.5, 1], 
                             hspace=0.5, wspace=0.4)
            
            # 绘制各个子图
            ax_nav = fig.add_subplot(gs[0, :])
            self._plot_strategy_nav_comparison(ax_nav)
            
            # 在值图和其他图之间添加空白区域
            fig.add_subplot(gs[1, :]).set_visible(False)
            
            ax_market = fig.add_subplot(gs[2, 0])
            self._plot_market_environment(ax_market)
            
            ax_position = fig.add_subplot(gs[2, 1])
            self._plot_position_analysis(ax_position, xiaomi_shares, etf_shares)
            
            ax_signal = fig.add_subplot(gs[2, 2])
            self._plot_strategy_signals(ax_signal)
            
            # 添加配置建议（使用表格形式展示）
            ax_advice = fig.add_subplot(gs[3, :])
            ax_advice.axis('off')
            
            advice = self.generate_allocation_advice(xiaomi_shares, etf_shares, cash)
            
            # 创建表格数据
            table_data = []
            headers = ['策略类型', '计算依据', '目标配置', '建议操作']
            
            for strat in advice:
                # 构建目标配置文本
                target_config_text = (
                    f"{self.name1}: {strat['目标配置'][self.name1 + '目标持仓']} "
                    f"({strat['目标配置'][self.name1 + '目标占比']})<br>"
                    f"{self.name2}: {strat['目标配置'][self.name2 + '目标持仓']} "
                    f"({strat['目标配置'][self.name2 + '目标占比']})"
                )
                
                # 构建建议操作文本
                advice_text = (
                    '\n'.join(strat['目标配置']['建议操作'])
                    if strat['目标配置']['建议操作']
                    else "当前配置合理，无需调整"
                )
                
                # 添加行数据
                row = [
                    strat['策略'],
                    strat['计算依据'],
                    target_config_text,
                    advice_text
                ]
                table_data.append(row)
            
            # 创建表格
            table = ax_advice.table(
                cellText=table_data,
                colLabels=headers,
                loc='center',
                cellLoc='center',
                colWidths=[0.15, 0.3, 0.25, 0.3]
            )
            
            # 设置表格样式
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 2)
            
            # 设置表格标题
            ax_advice.text(0.5, 1.05, '策略配置建议',
                          ha='center', va='bottom',
                          fontsize=12, fontweight='bold',
                          transform=ax_advice.transAxes)
            
            # 调整整体布局
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(f"绘制分析图表失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def calculate_strategy_nav(self, weights):
        """计算策略净值"""
        try:
            if weights is None:
                print("\n计算风险平价策略权重...")
                # 计算风险平价权重
                vol_xiaomi = self.df['return_xiaomi'].rolling(20).std()
                vol_etf = self.df['return_etf'].rolling(20).std()
                w_xiaomi = 1/vol_xiaomi / (1/vol_xiaomi + 1/vol_etf)
                w_xiaomi = w_xiaomi.fillna(0.5)
                
                # 使用前一日权重计算当日收益
                w_xiaomi_aligned = w_xiaomi.shift(1)
                w_xiaomi_aligned.iloc[0] = 0.5  # 第一天使用0.5作为默认权重
                w_xiaomi_aligned.iloc[-1] = w_xiaomi.iloc[-2]  # 最后一天使用前一天的权重
                
                # 计算每日收益率
                returns = pd.Series(index=self.df.index)
                for i in range(len(self.df)):
                    if i == 0:
                        returns.iloc[i] = (self.df['return_xiaomi'].iloc[i] * 0.5 + 
                                         self.df['return_etf'].iloc[i] * 0.5)
                    else:
                        returns.iloc[i] = (self.df['return_xiaomi'].iloc[i] * w_xiaomi_aligned.iloc[i] + 
                                         self.df['return_etf'].iloc[i] * (1 - w_xiaomi_aligned.iloc[i]))
                
            elif isinstance(weights, str) and weights == 'dynamic':
                print("\n计算动态调整策略权重...")
                # 基础权重
                base_weight = 0.6
                
                # 相关性调整
                corr = self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf'])
                corr_adj = -0.2 * corr
                
                # 动量调整
                momentum_xiaomi = self.df['return_xiaomi'].rolling(60).mean()
                momentum_etf = self.df['return_etf'].rolling(60).mean()
                mom_adj = 0.1 * (momentum_xiaomi > momentum_etf).astype(float)
                
                # 波动率调整
                vol_xiaomi = self.df['return_xiaomi'].rolling(20).std()
                vol_etf = self.df['return_etf'].rolling(20).std()
                vol_adj = -0.1 * (vol_xiaomi > vol_etf).astype(float)
                
                # 最终动态权重
                w_xiaomi = (base_weight + corr_adj + mom_adj + vol_adj).clip(0.3, 0.8)
                w_xiaomi = w_xiaomi.fillna(0.5)
                
                # 使用前一日权重计算当日收益
                w_xiaomi_aligned = w_xiaomi.shift(1)
                w_xiaomi_aligned.iloc[0] = 0.5  # 第一天使用0.5作为默认权重
                w_xiaomi_aligned.iloc[-1] = w_xiaomi.iloc[-2]  # 最后一天使用前一天的权重
                
                # 计算每日收益率
                returns = pd.Series(index=self.df.index)
                for i in range(len(self.df)):
                    if i == 0:
                        returns.iloc[i] = (self.df['return_xiaomi'].iloc[i] * 0.5 + 
                                         self.df['return_etf'].iloc[i] * 0.5)
                    else:
                        returns.iloc[i] = (self.df['return_xiaomi'].iloc[i] * w_xiaomi_aligned.iloc[i] + 
                                         self.df['return_etf'].iloc[i] * (1 - w_xiaomi_aligned.iloc[i]))
                
            elif isinstance(weights, tuple) and len(weights) == 2:
                # 使用固定权重计算收益
                w_xiaomi, w_etf = weights
                returns = self.df['return_xiaomi'] * w_xiaomi + self.df['return_etf'] * w_etf
            else:
                raise ValueError("无效的权重参数")
            
            # 计算净值
            nav = (1 + returns).cumprod()
            
            return nav
            
        except Exception as e:
            print(f"计算策略净值失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return pd.Series(index=self.df.index)
    
    def calculate_market_indicators(self, periods):
        """计算市场环境指标"""
        try:
            indicators = {}
            
            # 计算动率
            indicators['波动率'] = {}
            for period in periods:
                vol_xiaomi = self.df['return_xiaomi'].rolling(period).std() * np.sqrt(252)
                vol_etf = self.df['return_etf'].rolling(period).std() * np.sqrt(252)
                indicators['波动率'][f'{period}日'] = vol_xiaomi.iloc[-1]
            
            # 计算关性
            indicators['相关性'] = {}
            for period in periods:
                corr = self.df['return_xiaomi'].rolling(period).corr(self.df['return_etf'])
                indicators['相关性'][f'{period}日'] = corr.iloc[-1]
            
            # 计算趋势
            indicators['趋势'] = {}
            for period in periods:
                trend_xiaomi = self.df['close_xiaomi'].pct_change(period)
                trend_etf = self.df['close'].pct_change(period)
                indicators['趋势'][f'{period}日'] = trend_xiaomi.iloc[-1] - trend_etf.iloc[-1]
            
            return indicators
            
        except Exception as e:
            print(f"计算市场指标失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}
    
    def calculate_strategy_signals(self):
        """计算策略信号"""
        try:
            signals = {
                '趋势信号': {
                    '值': self.df['close_xiaomi'].pct_change(20).iloc[-1],
                    '说明': '20日收益率，>0表示上升趋势，<0表示下降趋势'
                },
                '波动信号': {
                    '值': (self.df['return_xiaomi'].std() - self.df['return_etf'].std()) * np.sqrt(252),
                    '说明': '年化波动率差异，>0表示可转债波动性更大，需增加对冲'
                },
                '相关信号': {
                    '值': self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf']).iloc[-1],
                    '说明': '20日相关系数，<0表示负相关，对冲效果好'
                },
                '动量信号': {
                    '值': (self.df['close_xiaomi'].pct_change(60) - self.df['close'].pct_change(60)).iloc[-1],
                    '说明': '60日动量差异，>0表示可转债相对强势'
                }
            }
            
            return signals
            
        except Exception as e:
            print(f"计算策略信号失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}
    
    def calculate_dynamic_weights(self):
        """计算动态调整权重"""
        try:
            # 基础权重
            base_weight = 0.6
            
            # 相关性调整
            corr = self.df['return_xiaomi'].rolling(20).corr(self.df['return_etf'])
            corr_adj = -0.2 * corr
            
            # 动量调整
            momentum_xiaomi = self.df['return_xiaomi'].rolling(60).mean()
            momentum_etf = self.df['return_etf'].rolling(60).mean()
            mom_adj = 0.1 * (momentum_xiaomi > momentum_etf).astype(float)
            
            # 波动率调整
            vol_xiaomi = self.df['return_xiaomi'].rolling(20).std()
            vol_etf = self.df['return_etf'].rolling(20).std()
            vol_adj = -0.1 * (vol_xiaomi > vol_etf).astype(float)
            
            # 最终动态权重
            w_xiaomi = (base_weight + corr_adj + mom_adj + vol_adj).clip(0.3, 0.8)
            self.df['dynamic_weight'] = w_xiaomi
            
            return w_xiaomi
            
        except Exception as e:
            print(f"计算动态权重失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return pd.Series(0.5, index=self.df.index)

    def calculate_strategy_metrics(self):
        """计算各个策略的表现指标"""
        print("\n开始计算策略指标...")
        strategies = {
            f'{self.name1}': (1.0, 0.0),
            f'{self.name2}': (0.0, 1.0),
            '固定配置(70/30)': (0.7, 0.3),
            '固定配置(50/50)': (0.5, 0.5),
            '风险平价': None,
            '动态调整': 'dynamic'
        }
        
        metrics = {}
        risk_free_rate = 0.02  # 假设无风险利率为2%
        
        for name, weights in strategies.items():
            print(f"\n计算{name}策略的指标...")
            # 计算策略收益率序列
            nav = self.calculate_strategy_nav(weights)
            returns = nav.pct_change().dropna()
            
            # 计算各项指标
            annual_return = (nav.iloc[-1] ** (252/len(nav)) - 1)
            annual_vol = returns.std() * np.sqrt(252)
            sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol != 0 else 0
            max_drawdown = (nav / nav.expanding().max() - 1).min()
            win_rate = (returns > 0).mean()
            
            print(f"{name}策略指标:")
            print(f"年化收益率: {annual_return:.2%}")
            print(f"年化波动率: {annual_vol:.2%}")
            print(f"夏普比率: {sharpe:.2f}")
            print(f"最大回撤: {max_drawdown:.2%}")
            print(f"胜率: {win_rate:.2%}")
            
            # 计算最大回撤持续期
            drawdown = nav / nav.expanding().max() - 1
            drawdown_periods = []
            current_period = 0
            for dd in drawdown:
                if dd < 0:
                    current_period += 1
                else:
                    if current_period > 0:
                        drawdown_periods.append(current_period)
                    current_period = 0
            if current_period > 0:
                drawdown_periods.append(current_period)
            max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
            
            # 计算信息比率
            if name not in [self.name1, self.name2]:
                benchmark_returns = self.df['return_xiaomi']  # 使用可转债作为基准
                tracking_error = (returns - benchmark_returns).std() * np.sqrt(252)
                information_ratio = (annual_return - benchmark_returns.mean() * 252) / tracking_error if tracking_error != 0 else 0
            else:
                information_ratio = None
            
            metrics[name] = {
                '年化收益率': annual_return,
                '年化波动率': annual_vol,
                '夏普比率': sharpe,
                '最大回撤': max_drawdown,
                '最大回撤持续期': f"{max_drawdown_duration}天",
                '胜率': win_rate,
                '信息比率': information_ratio
            }
        
        return metrics

class DataManager:
    def __init__(self,trade_codes):
        print("初始化DataManager...")
        self.setup_database()
        self.table_name = 'marketinfo_fund'
        self.allowed_trade_codes =trade_codes
        self.update_data()
        
    def setup_database(self):
        try:
            print("创建数据库连接...")
            self.sql_engine = sqlalchemy.create_engine(
                'mysql+pymysql://%s:%s@%s:%s/%s' % (
                    'hz_work',
                    'Hzinsights2015',
                    'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
                    '3306',
                    'yq',
                ), poolclass=sqlalchemy.pool.NullPool
            )
            self.cursor = self.sql_engine.connect()
            print("数据库连接创建成功")
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise

    def get_latest_data_date(self,trade_code):
        """获取数据库中最新的数据日期"""
        try:
            query = f"""
            SELECT MAX(dt) as latest_date 
            FROM {self.table_name} 
                    WHERE trade_code = '{trade_code}'
                """
            with self.sql_engine.begin() as conn:
                result = conn.execute(sqlalchemy.text(query)).fetchone()
                if result and result[0]:
                    return result[0]
        except Exception as e:
            print(f"获取最新数据日期失败: {str(e)}")
            return None

    def update_data(self):
        """更新数据"""
        for trade_code in self.allowed_trade_codes:
            try:
                # 获取新数据日期
                latest_date = self.get_latest_data_date(trade_code)
                if latest_date:
                    start_date = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')
                else:
                    start_date = "2020-01-01"
                
                end_date = datetime.now().strftime('%Y-%m-%d')
                
                if start_date > end_date:
                    print("数据已是最新")
                    return True
                    
                print(f"更新数据期间: {start_date} 到 {end_date}")
            
                # 获取Wind数据
                w.start()
                print("正在从Wind获取数据...")
                wsd_data = w.wsd(f"{trade_code}", "open,high,low,close,volume,vwap", 
                            start_date, end_date, "")
                
                if wsd_data.ErrorCode != 0:
                    print(f"获取Wind数据失败，错误码: {wsd_data.ErrorCode}")
                    return False
                
                if not wsd_data.Data or not wsd_data.Times:
                    print("未获取到新数据")
                    return True
                
                # 转换为DataFrame
                df = pd.DataFrame()
                for field, data in zip(wsd_data.Fields, wsd_data.Data):
                    df[field] = data
                df.index = wsd_data.Times
                
                if df.empty:
                    print("未获取到数据")
                    return True
                
                # 添加trade_code列和日期列
                df['trade_code'] = trade_code
                df['dt'] = df.index
                
                # 重命名列以匹配数据库
                df = df.rename(columns={
                    'OPEN': 'open',
                    'HIGH': 'high',
                    'LOW': 'low',
                    'CLOSE': 'close',
                    'VOLUME': 'volume',
                    'VWAP': 'vwap'
                })
                
                # 数据验证
                df = df.dropna()  # 删除空值
                
                # 验证数值范围
                for col in ['open', 'high', 'low', 'close', 'vwap']:
                    invalid_mask = df[col] <= 0
                    if invalid_mask.any():
                        print(f"警告：{col}列存在{invalid_mask.sum()}个异常值，已过滤")
                        df = df[~invalid_mask]
                
                if df.empty:
                    print("数据验证后无有效数据")
                    return True
                
                # 写入数据库
                print(f"正在写入{len(df)}条数据...")
                df.to_sql(self.table_name, self.sql_engine, if_exists='append', index=False,
                        dtype={
                            'trade_code': sqlalchemy.String(20),
                            'dt': sqlalchemy.Date,
                            'open': sqlalchemy.DECIMAL(20,4),
                            'high': sqlalchemy.DECIMAL(20,4),
                            'low': sqlalchemy.DECIMAL(20,4),
                            'close': sqlalchemy.DECIMAL(20,4),
                            'volume': sqlalchemy.DECIMAL(20,4),
                            'vwap': sqlalchemy.DECIMAL(20,4)
                        })
                
                print("数据更新完成")
                return True
                
            except Exception as e:
                print(f"更新数据失败: {str(e)}")
                import traceback
                print("详细错误信息:")
                print(traceback.format_exc())
                return False
            finally:
                try:
                    w.close()
                except:
                    pass

class ReportGenerator:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.name1=self.analyzer.name1
        self.name2=self.analyzer.name2
        self.report_dir = "reports"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
    
    def create_nav_figure(self):
        """创建策略净值对比图"""
        try:
            # 创建单个图表，不再需要子图
            fig = go.Figure()
            
            # 添加净值曲线
            strategies = {
                f'{self.name1}': (1.0, 0.0),
                f'{self.name2}': (0.0, 1.0),
                '固定配置(70/30)': (0.7, 0.3),
                '固定配置(50/50)': (0.5, 0.5),
                '风险平价': None,
                '动态调整': 'dynamic'
            }
            
            # 记录所有策略的最后日期
            last_dates = []
            
            for name, weights in strategies.items():
                nav = self.analyzer.calculate_strategy_nav(weights)
                
                # 检查净值数据
                if nav is None or len(nav) == 0:
                    print(f"警告：{name}策略的净值计算结果为空")
                    continue
                
                # 记录最后日期
                last_dates.append(nav.index[-1])
                
                # 打印每个策略的数据范围
                print(f"\n{name}策略:")
                print(f"数据范围: {nav.index[0]} 至 {nav.index[-1]}")
                print(f"数据点数: {len(nav)}")
                print(f"最后三个净值: {nav.tail(3).values}")
                
                fig.add_trace(
                    go.Scatter(
                        x=nav.index,
                        y=nav.values,
                        name=name,
                        hovertemplate='%{x|%Y-%m-%d}<br>净值: %{y:.2f}<extra></extra>'
                    )
                )
            
            # 检查所有策略的最后日期是否一致
            if last_dates:
                last_date = max(last_dates)
                if not all(d == last_date for d in last_dates):
                    print("\n警告：不同策略的最后日期不一致:")
                    for name, date in zip(strategies.keys(), last_dates):
                        print(f"{name}: {date}")
            
            # 更新布局
            fig.update_layout(
                title='策略净值对比 (2023年1月14日至今)',
                height=500,  # 小图表高度
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.05
                ),
                margin=dict(r=100, t=50, b=50),
                hovermode='x unified',
                xaxis_title="日期",
                yaxis_title="净值"
            )
            
            return fig
            
        except Exception as e:
            print(f"创建净值对比图失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return go.Figure()
    
    def create_market_env_figure(self):
        """创建市场环境分析图"""
        try:
            # 创建单个图表
            fig = go.Figure()
            
            # 计算指标
            periods = [20, 60, 120]
            indicators = self.analyzer.calculate_market_indicators(periods)
            
            # 准备热力图数据
            z_data = []
            y_labels = []
            text_data = []
            
            for indicator, period_data in indicators.items():
                y_labels.append(indicator)
                row_data = []
                text_row = []
                for period in periods:
                    value = period_data.get(f'{period}日', 0)
                    row_data.append(value)
                    text_row.append(f'{value:.1%}')
                z_data.append(row_data)
                text_data.append(text_row)
            
            # 添加热力图
            fig.add_trace(
                go.Heatmap(
                    z=z_data,
                    x=[f'{p}日' for p in periods],
                    y=y_labels,
                    text=text_data,
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    colorscale='RdYlGn'
                )
            )
            
            # 更新布局
            fig.update_layout(
                title='市场环境热力图',
                height=400,  # 减小图表高度
                margin=dict(r=50, t=50, b=50),
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            print(f"创建市场环境图失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return go.Figure()
    
    def create_signals_figure(self):
        """创建策略信号图"""
        try:
            # 创建单个图表
            fig = go.Figure()
            
            # 获取信号数据
            signals = self.analyzer.calculate_strategy_signals()
            
            # 准备数据
            names = list(signals.keys())
            values = [s['值'] for s in signals.values()]
            colors = ['red' if v > 0 else 'green' for v in values]
            
            # 添加信号条形图
            fig.add_trace(
                go.Bar(
                    y=names,
                    x=values,
                    orientation='h',
                    marker_color=colors,
                    text=[f'{v:.2%}' for v in values],
                    textposition='outside',
                    hovertemplate='%{y}: %{x:.2%}<extra></extra>'
                )
            )
            
            # 添加零线
            fig.add_shape(
                type='line',
                x0=0, x1=0,
                y0=-0.5, y1=len(names)-0.5,
                line=dict(color='black', width=1)
            )
            
            # 更新布局
            fig.update_layout(
                title='策略信号强度',
                height=400,  # 减小图表高度
                showlegend=False,
                margin=dict(r=50, t=50, b=50)
            )
            
            return fig
            
        except Exception as e:
            print(f"创建信号图失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return go.Figure()
    
    def generate_html_report(self, xiaomi_shares, etf_shares, cash):
        """生成HTML报告"""
        # 获取最新价格
        xiaomi_price = self.analyzer.df['close_xiaomi'].iloc[-1]
        etf_price = self.analyzer.df['close'].iloc[-1]
        
        # 计算当前持仓市值和占比
        xiaomi_value = xiaomi_shares * xiaomi_price
        etf_value = etf_shares * etf_price
        total_value = xiaomi_value + etf_value + cash
        
        xiaomi_ratio = xiaomi_value / total_value
        etf_ratio = etf_value / total_value
        cash_ratio = cash / total_value
        
        # 生成图表
        nav_fig = self.create_nav_figure()
        market_fig = self.create_market_env_figure()
        signals_fig = self.create_signals_figure()
        
        # 获取配置建议
        advice = self.analyzer.generate_allocation_advice(xiaomi_shares, etf_shares, cash)
        
        # 获取策略指标
        strategy_metrics = self.analyzer.calculate_strategy_metrics()
        
        # 读取HTML模板
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>策略分析报告</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .section { margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
        th { background-color: #f5f5f5; }
        .header { 
            background-color: #f8f9fa;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
        }
        .advice-table tr:nth-child(even) { background-color: #f9f9f9; }
        .timestamp { color: #666; font-size: 0.9em; }
        .current-holdings {
            background-color: #e8f4f8;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .holdings-info {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
        }
        .holding-item {
            flex: 1;
            text-align: center;
            padding: 10px;
        }
        .description-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .description-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .description-card h4 {
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid #3498db;
        }
        .description-card ul {
            margin: 0;
            padding-left: 20px;
        }
        .description-card li {
            margin-bottom: 8px;
            line-height: 1.4;
        }
        .highlight {
            color: #e74c3c;
            font-weight: bold;
        }
        .usage-tips {
            margin-top: 15px;
            padding: 10px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 0 4px 4px 0;
        }
        .usage-tips h5 {
            margin: 0 0 8px 0;
            color: #856404;
        }
        .usage-tips ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .metrics-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .metrics-card h4 {
            color: #2c3e50;
            margin: 0 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }
        
        .metrics-content {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }
        
        .metric-item {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
        }
        
        .metric-value {
            font-size: 1.1em;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .metric-value.positive {
            color: #27ae60;
        }
        
        .metric-value.negative {
            color: #e74c3c;
        }
        
        .metrics-explanation {
            background-color: #f8f9fa;
            padding: 20px;
            margin-top: 20px;
            border-radius: 8px;
        }
        
        .metrics-explanation h4 {
            color: #2c3e50;
            margin: 0 0 15px 0;
        }
        
        .metrics-explanation ul {
            margin: 0;
            padding-left: 20px;
        }
        
        .metrics-explanation li {
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .advice-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .advice-table th {
            background-color: #3498db;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 500;
        }
        
        .advice-table td {
            padding: 15px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }
        
        .advice-table tr:last-child td {
            border-bottom: none;
        }
        
        .advice-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .advice-table tr:hover {
            background-color: #f1f4f6;
        }
        
        .advice-operation {
            color: #e74c3c;
            font-weight: 500;
        }
        
        .advice-operation.no-action {
            color: #27ae60;
        }
        
        .advice-basis {
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ name1 }}与{{ name2 }}对冲策略分析报告</h1>
            <p class="timestamp">生成时间：{{ timestamp }}</p>
        </div>

        <div class="current-holdings">
            <h3>当前持仓状况</h3>
            <div class="holdings-info">
                <div class="holding-item">
                    <h4>{{ name1 }}</h4>
                    <p>{{ xiaomi_shares }}股</p>
                    <p>{{ "{:,.0f}".format(xiaomi_value) }}元 ({{ "{:.1%}".format(xiaomi_ratio) }})</p>
                </div>
                <div class="holding-item">
                    <h4>{{ name2 }}</h4>
                    <p>{{ etf_shares }}份</p>
                    <p>{{ "{:,.0f}".format(etf_value) }}元 ({{ "{:.1%}".format(etf_ratio) }})</p>
                </div>
                <div class="holding-item">
                    <h4>可用现金</h4>
                    <p>{{ "{:,.0f}".format(cash) }}元</p>
                    <p>({{ "{:.1%}".format(cash_ratio) }})</p>
                </div>
                <div class="holding-item">
                    <h4>总资产</h4>
                    <p>{{ "{:,.0f}".format(total_value) }}元</p>
                    <p>(100%)</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>策略净值对比</h2>
            {{ nav_chart }}
            
            <div class="description-grid">
                <div class="description-card">
                    <h4>风险平价策略</h4>
                    <ul>
                        <li>基于各资产的<span class="highlight">波动率</span>动态调整权重</li>
                        <li>当某个资产波动率升高时，自动降低其权重</li>
                        <li>目标：通过动态调整实现风险贡献的平衡</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>动态调整策略</h4>
                    <ul>
                        <li>综合考虑<span class="highlight">相关性</span>、<span class="highlight">动量</span>和<span class="highlight">波动率</span></li>
                        <li>在基准权重(60/40)基础上动态调整</li>
                        <li>调整范围：30%-80%之间</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>固定配置策略</h4>
                    <ul>
                        <li>维持固定的资产配置比例</li>
                        <li>定期进行再平衡以保持目标权重</li>
                        <li>提供70/30和50/50两种固定配置方案</li>
                    </ul>
                </div>
            </div>
            
            <div class="usage-tips">
                <h5>使用说明</h5>
                <ul>
                    <li>双击图例可以单独显示某个策略</li>
                    <li>点击并拖动可以放大某个时间段</li>
                    <li>双击图表可以还原到原始视图</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>市场环境分析</h2>
            {{ market_chart }}
            
            <div class="description-grid">
                <div class="description-card">
                    <h4>波动率环境</h4>
                    <ul>
                        <li><span class="highlight">高波动(>20%)</span>：市场剧烈波动，风险较大</li>
                        <li><span class="highlight">中等波动(10%-20%)</span>：市场波动正常</li>
                        <li><span class="highlight">低波动(<10%)</span>：市场平稳，风险较小</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>相关性环境</h4>
                    <ul>
                        <li><span class="highlight">高度正相关(>0.5)</span>：同向波动，对冲效果差</li>
                        <li><span class="highlight">弱相关(-0.3~0.3)</span>：相对独立</li>
                        <li><span class="highlight">显著负相关(<-0.3)</span>：反向波动，对冲效果好</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>趋势环境</h4>
                    <ul>
                        <li><span class="highlight">上升趋势</span>：价格持续上涨，动能强劲</li>
                        <li><span class="highlight">盘整趋势</span>：价格区间波动</li>
                        <li><span class="highlight">下降趋势</span>：价格持续下跌，需谨慎</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>策略信号</h2>
            {{ signals_chart }}
            
            <div class="description-grid">
                <div class="description-card">
                    <h4>趋势信号</h4>
                    <ul>
                        <li>基于<span class="highlight">20日收益率</span>计算</li>
                        <li>正值：上升趋势，建议增持{{ name1 }}</li>
                        <li>负值：下降趋势，建议减持{{ name1 }}</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>波动信号</h4>
                    <ul>
                        <li>基于<span class="highlight">年化波动率差异</span></li>
                        <li>正值：{{ name1 }}波动较大，建议增加对冲</li>
                        <li>负值：{{ name2 }}波动较大，建议减少对冲</li>
                    </ul>
                </div>
                <div class="description-card">
                    <h4>相关性信号</h4>
                    <ul>
                        <li>基于<span class="highlight">20日滚动相关系数</span></li>
                        <li>正值：正相关，对冲效果较差</li>
                        <li>负值：负相关，对冲效果较好</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>策略表现指标</h2>
            <div class="metrics-grid">
                {% for strategy, metrics in strategy_metrics.items() %}
                <div class="metrics-card">
                    <h4>{{ strategy }}</h4>
                    <div class="metrics-content">
                        <div class="metric-item">
                            <span class="metric-label">年化收益率</span>
                            <span class="metric-value {% if metrics['年化收益率'] > 0 %}positive{% else %}negative{% endif %}">
                                {{ "{:.2%}".format(metrics['年化收益率']) }}
                            </span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">年化波动率</span>
                            <span class="metric-value">{{ "{:.2%}".format(metrics['年化波动率']) }}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">夏普比率</span>
                            <span class="metric-value {% if metrics['夏普比率'] > 1 %}positive{% elif metrics['夏普比率'] < 0 %}negative{% endif %}">
                                {{ "{:.2f}".format(metrics['夏普比率']) }}
                            </span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">最大回撤</span>
                            <span class="metric-value negative">{{ "{:.2%}".format(metrics['最大回撤']) }}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">最大回撤持续期</span>
                            <span class="metric-value">{{ metrics['最大回撤持续期'] }}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">胜率</span>
                            <span class="metric-value">{{ "{:.2%}".format(metrics['胜率']) }}</span>
                        </div>
                        {% if metrics['信息比率'] is not none %}
                        <div class="metric-item">
                            <span class="metric-label">信息比率</span>
                            <span class="metric-value {% if metrics['信息比率'] > 0 %}positive{% else %}negative{% endif %}">
                                {{ "{:.2f}".format(metrics['信息比率']) }}
                            </span>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <div class="metrics-explanation">
                <h4>指标说明</h4>
                <ul>
                    <li><span class="highlight">年化收益率</span>：策略年化后的收益表现</li>
                    <li><span class="highlight">年化波动率</span>：策略收益率的年化标准差，反映风险水平</li>
                    <li><span class="highlight">夏普比率</span>：超额收益与波动率之比，大于1表现优秀，小于0表现不佳</li>
                    <li><span class="highlight">最大回撤</span>：策略遭遇的最大损失幅度</li>
                    <li><span class="highlight">最大回撤持续期</span>：最大回撤的持续天数</li>
                    <li><span class="highlight">胜率</span>：策略日收益为正的概率</li>
                    <li><span class="highlight">信息比率</span>：相对基准的超额收益与跟踪误差之比，衡量超额收益的稳定性</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>配置思路</h2>
            <table class="advice-table">
                <tr>
                    <th>策略类型</th>
                    <th>目标配置</th>
                    <th>建议操作</th>
                    <th>计算依据</th>
                </tr>
                {% for strat in advice %}
                <tr>
                    <td>{{ strat['策略'] }}</td>
                    <td>
                        {{ name1 }}: {{ strat['目标配置'][name1 + '目标持仓'] }} ({{ strat['目标配置'][name1 + '目标占比'] }})<br>
                        {{ name2 }}: {{ strat['目标配置'][name2 + '目标持仓'] }} ({{ strat['目标配置'][name2 + '目标占比'] }})
                    </td>
                    <td>
                        {% if strat['目标配置']['模拟情景'] %}
                            {% for op in strat['目标配置']['模拟情景'] %}
                                {{ op }}<br>
                            {% endfor %}
                        {% else %}
                            当前配置合理，无需调整
                        {% endif %}
                    </td>
                    <td>{{ strat['计算依据'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
        """
        
        # 渲染模板
        template = Template(template_str)
        html_content = template.render(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            xiaomi_shares=f"{xiaomi_shares:,.0f}",
            etf_shares=f"{etf_shares:,.0f}",
            cash=cash,
            xiaomi_value=xiaomi_value,
            etf_value=etf_value,
            total_value=total_value,
            xiaomi_ratio=xiaomi_ratio,
            etf_ratio=etf_ratio,
            cash_ratio=cash_ratio,
            nav_chart=nav_fig.to_html(full_html=False),
            market_chart=market_fig.to_html(full_html=False),
            signals_chart=signals_fig.to_html(full_html=False),
            advice=advice,
            name1=self.name1,
            name2=self.name2,
            strategy_metrics=strategy_metrics
        )
        
        # 保存HTML文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(self.report_dir, f'strategy_report_{timestamp}.html')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path

def get_user_input(name1,name2):
    """获取用户输入的持仓信息"""
    while True:
        try:
            print("\n=== 请输入当前持仓信息 ===")
            xiaomi_shares = float(input(f"{name1}持仓数量: "))
            etf_shares = float(input(f"{name2}持仓份额: "))
            cash = float(input("可用现金金额（元）: "))
            
            if xiaomi_shares < 0 or etf_shares < 0 or cash < 0:
                print("输入值不能为负数，请重新输入")
                continue
                
            return xiaomi_shares, etf_shares, cash
            
        except ValueError:
            print("输入无效，请输入数字")

def main():
    try:
        # 1. 获取用户输入
        trade_code1 ='511220.SH'
        trade_code2 = '518880.SH'
        name1 = '城投ETF'
        name2 = '黄金ETF'
        xiaomi_shares, etf_shares, cash = get_user_input(name1,name2)
        
        # 2. 初始化分析器
        print("\n=== 开始策略分析 ===")
        
        analyzer = MarketAnalyzer(trade_code1,trade_code2,name1,name2)
        DataManager1 = DataManager(['518880.SH','511380.SH','511220.SH','511090.OF'])

        # 3. 获取数据
        if not analyzer.get_data(trade_code1,trade_code2):
            print("获取数据失败")
            return
        
        # 4. 生成报告
        report_generator = ReportGenerator(analyzer)
        report_path = report_generator.generate_html_report(xiaomi_shares, etf_shares, cash)
        
        print(f"\n报告已生成: {report_path}")
        
        # 5. 自动打开报告
        webbrowser.open('file://' + os.path.abspath(report_path))
        
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        try:
            analyzer.cursor.close()
        except:
            pass

if __name__ == "__main__":
    main()
