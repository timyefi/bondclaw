# -*- coding: utf-8 -*-
"""
债券框架 - 可视化模块
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config

# 设置中文字体
plt.rcParams['font.sans-serif'] = [config.CHART_FONT_FAMILY]
plt.rcParams['axes.unicode_minus'] = False


def create_dynamic_html(analysis_df, roll_df, filename='analysis_dashboard.html'):
    """生成动态交互式分析报告"""
    fig = make_subplots(
        rows=3, cols=1,
        specs=[[{"type": "scatter"}],
               [{"type": "scatter"}],
               [{"type": "scatter"}]],
        subplot_titles=("资金利率与收益率走势", "滚动回归系数", "预期缺口变化"),
        vertical_spacing=0.1
    )

    # 资金利率与收益率双轴图
    fig.add_trace(
        go.Scatter(x=analysis_df.dt, y=analysis_df.fund_rate, name="资金利率"),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=analysis_df.dt, y=analysis_df.yield_rate,
                   name="债券收益率", yaxis="y2"),
        row=1, col=1
    )

    # 滚动回归系数
    fig.add_trace(
        go.Scatter(x=roll_df.dt, y=roll_df.fund_beta, name="资金利率系数"),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=roll_df.dt, y=roll_df.gap_beta, name="预期缺口系数"),
        row=2, col=1
    )

    # 预期缺口变化
    fig.add_trace(
        go.Scatter(x=analysis_df.dt, y=analysis_df['预期缺口'],
                   name="20日预期缺口", mode='lines+markers'),
        row=3, col=1
    )

    # 布局调整
    fig.update_layout(
        height=1200,
        title_text="债券定价动态分析看板",
        hovermode="x unified",
        yaxis2=dict(
            title="债券收益率",
            overlaying="y",
            side="right"
        )
    )

    # 添加分析注释
    annotations = [
        dict(xref='paper', yref='paper', x=0.5, y=1.15,
             xanchor='center', yanchor='top',
             text='分析结论：<br>1. 资金利率系数长期均值为{:.2f}<br>2. 预期缺口最大波动区间[{:.2f}, {:.2f}]'.format(
                 roll_df.fund_beta.mean(),
                 analysis_df['预期缺口'].quantile(0.05),
                 analysis_df['预期缺口'].quantile(0.95)
             ),
             showarrow=False)
    ]
    fig.update_layout(annotations=annotations)

    fig.write_html(filename)


def plot_comparison(individual_results, group_results):
    """绘制对比分析图，每个期限单独绘图"""
    terms = individual_results['期限'].unique()
    for term in terms:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=config.CHART_FIGSIZE)

        term_individual_results = individual_results[
            individual_results['期限'] == term
        ]
        term_group_results = group_results[group_results['期限'] == term]

        # 单因子解释度对比
        top_individual = term_individual_results.sort_values(
            'R方', ascending=False
        ).head(20)
        sns.barplot(x='R方', y='因子名称', data=top_individual, ax=ax1)
        ax1.set_title(f'对{term}期国债收益率的单因子解释度Top20')

        # 整体指标解释度对比
        sns.barplot(x='r2', y='group_type', data=term_group_results, ax=ax2)
        ax2.set_title(f'对{term}期国债收益率的整体指标解释度对比')

        plt.tight_layout()
        plt.savefig(config.OUTPUT_DIR / f'解释度对比分析_{term}.png')
        plt.close()


def plot_dynamic_comparison(dynamic_group_results):
    """绘制动态整体指标解释度对比图"""
    terms = dynamic_group_results['期限'].unique()
    group_types = dynamic_group_results['group_type'].unique()

    for term in terms:
        fig, axes = plt.subplots(
            len(group_types), 1,
            figsize=(14, 7 * len(group_types)),
            sharex=True
        )
        axes = axes.flatten()

        term_dynamic_results = dynamic_group_results[
            dynamic_group_results['期限'] == term
        ]

        for i, g_type in enumerate(group_types):
            ax = axes[i]
            group_data = term_dynamic_results[
                term_dynamic_results['group_type'] == g_type
            ]
            sns.lineplot(x='date', y='r2', data=group_data, ax=ax, label=g_type)
            ax.set_title(f'{term}期国债收益率 - {g_type}指标动态解释度')
            ax.set_ylabel('R方')
            ax.legend()

        plt.xlabel('日期')
        plt.tight_layout()
        plt.savefig(config.OUTPUT_DIR / f'动态整体指标解释度_{term}.png')
        plt.close()


def visualize_results(df, roll_result, reg_results, yield_code):
    """增强可视化：添加政策预期分析"""
    name1 = config.TERM_NAME_MAP.get(yield_code, yield_code)

    plt.figure(figsize=config.CHART_FIGSIZE)
    df['最优平移值'] = -df['最优平移值']

    # 主图：资金利率与收益率
    ax1 = plt.subplot(311)
    ax1.plot(df['dt'], df['fund_rate'], label='资金利率', color='tab:blue')
    ax1.plot(df['dt'], df['yield_rate'], label='债券收益率', color='tab:orange')
    ax1.set_title(f'{name1}利率走势与市场预期', fontsize=14)
    ax1.legend(loc='upper left')

    # 次图：最优平移值（政策预期）
    ax2 = ax1.twinx()
    ax2.plot(df['dt'], df['最优平移值'],
             label=f'{name1}市场隐含政策预期',
             color='green', linestyle='--', alpha=0.7)
    ax2.axhline(0, color='grey', linestyle=':')
    ax2.set_ylabel('平移值(%)', fontsize=10)
    ax2.legend(loc='upper right')

    # 中图：预期缺口分解
    ax3 = plt.subplot(312)
    ax3.fill_between(df['dt'], df['fund_rate'], df['预期缺口'],
                     where=(df['预期缺口'] > df['fund_rate']),
                     facecolor='green', alpha=0.3, label='宽松预期区域')
    ax3.fill_between(df['dt'], df['fund_rate'], df['预期缺口'],
                     where=(df['预期缺口'] <= df['fund_rate']),
                     facecolor='red', alpha=0.3, label='紧缩预期区域')
    ax3.plot(df['dt'], df['fund_rate'], label='实际资金利率', color='navy')
    ax3.plot(df['dt'], df['预期缺口'], label='均衡利率水平',
             color='purple', linestyle='--')
    ax3.set_title(f'资金利率与{name1}均衡水平缺口分析', fontsize=14)
    ax3.legend()

    # 下图：滚动平移值分析
    ax4 = plt.subplot(313)
    monthly_shift = df.set_index('dt')['最优平移值'].resample('M').mean()
    ax4.bar(monthly_shift.index, monthly_shift.values,
            width=15, color=np.where(monthly_shift > 0, 'tomato', 'limegreen'))
    ax4.set_title('月度政策预期变化（正值=加息预期，负值=降息预期）', fontsize=14)
    ax4.axhline(0, color='black', linewidth=0.8)

    # 添加数据来源说明
    fig = plt.gcf()
    fig.text(0.1, 0.05, 'Source: WIND, 同花顺, Bloomberg',
             fontsize=8, color='gray', alpha=0.8)

    plt.tight_layout()
    plt.savefig(config.OUTPUT_DIR / f'{yield_code}policy_expectation_analysis.png')
    plt.close()


def plot_pgim_fund_data():
    """PGIM海外债基数据可视化"""
    years = list(range(1991, 2025))

    a_values = [
        4.69, 8.74, -13.91, 4.36, 4.56, 8.97, 1.09, 7.92, 0.48, 4.60,
        14.55, -5.22, 12.57, 9.51, 4.14, 23.04, -15.27, -0.11, 6.30, 6.53,
        5.90, 6.58, 6.51, 4.80, 3.79, -2.97, 5.41, 10.49, 3.55, 16.88,
        -3.02, 11.40, 8.81, 12.40
    ]

    c_values = [
        3.83, 7.89, -14.59, 3.55, 3.77, 8.16, 0.33, 7.14, -0.25, 3.83,
        13.70, -5.93, 11.74, 8.60, 3.55, 22.46, -15.66, -0.50, 5.80, 6.00,
        5.28, 6.12, 5.88, 4.39, 3.27, -3.46, 4.74, 9.78, 2.97, 16.03,
        None, None, None, None
    ]

    r6_values = [
        5.01, 9.10, -13.65, 4.69, 4.87, 9.24, 1.56, None, None, None,
        None, None, None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None, None, None,
        None, None, None, None
    ]

    z_values = [
        4.92, 8.88, -13.64, 4.60, 4.80, 9.11, 1.42, 8.13, 0.77, 4.87,
        14.85, -4.99, 12.86, 9.69, 4.53, 23.27, -15.04, 0.24, 6.56, 6.79,
        6.16, 6.89, 6.77, 5.06, 4.04, -2.74, 5.52, 10.60, None, None,
        None, None, None, None
    ]

    df = pd.DataFrame({
        'Year': years,
        'A': a_values,
        'C': c_values,
        'R6': r6_values,
        'Z': z_values
    })

    df = df.iloc[::-1].reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Year'], y=df['A'],
        mode='lines+markers', name='A份额',
        line=dict(width=2), marker=dict(size=8, symbol='circle')
    ))

    fig.add_trace(go.Scatter(
        x=df['Year'], y=df['C'],
        mode='lines+markers', name='C份额',
        line=dict(width=2), marker=dict(size=8, symbol='square')
    ))

    fig.add_trace(go.Scatter(
        x=df['Year'], y=df['R6'],
        mode='lines+markers', name='R6份额',
        line=dict(width=2), marker=dict(size=8, symbol='triangle-up')
    ))

    fig.add_trace(go.Scatter(
        x=df['Year'], y=df['Z'],
        mode='lines+markers', name='Z份额',
        line=dict(width=2), marker=dict(size=8, symbol='diamond')
    ))

    fig.add_shape(
        type="line",
        x0=df['Year'].min(), y0=0,
        x1=df['Year'].max(), y1=0,
        line=dict(color="black", width=1, dash="solid"),
    )

    max_idx = df['A'].idxmax()
    min_idx = df['A'].idxmin()
    max_year = df.iloc[max_idx]['Year']
    min_year = df.iloc[min_idx]['Year']
    max_value = df.iloc[max_idx]['A']
    min_value = df.iloc[min_idx]['A']

    fig.add_annotation(
        x=max_year, y=max_value,
        text=f"{max_value:.1f}%",
        showarrow=True, arrowhead=2,
        arrowsize=1, arrowwidth=2,
        ax=20, ay=-30
    )

    fig.add_annotation(
        x=min_year, y=min_value,
        text=f"{min_value:.1f}%",
        showarrow=True, arrowhead=2,
        arrowsize=1, arrowwidth=2,
        ax=20, ay=30
    )

    fig.update_layout(
        title={
            'text': 'PGIM Muni High Income Fund年度表现 (1991-2024)',
            'y': 0.95, 'x': 0.5,
            'xanchor': 'center', 'yanchor': 'top',
            'font': dict(size=20, color='black')
        },
        xaxis_title='年份',
        yaxis_title='收益率 (%)',
        legend=dict(
            x=0.02, y=0.98,
            bgcolor='rgba(255, 255, 255, 0.5)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1
        ),
        font=dict(family="Arial, sans-serif", size=12, color="black"),
        hovermode="x unified",
        width=900, height=600,
        template='plotly_white',
        annotations=[
            dict(
                text="数据来源: PGIM, 弘则研究整理",
                x=0.02, y=-0.15,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=10, color="gray"),
                align="left"
            )
        ]
    )

    fig.update_xaxes(
        tickmode='array',
        tickvals=df['Year'][::5].tolist() +
                 ([df['Year'].iloc[-1]]
                  if df['Year'].iloc[-1] not in df['Year'][::5].tolist()
                  else []),
        tickangle=45,
        gridcolor='lightgray',
        zeroline=False
    )

    fig.update_yaxes(
        gridcolor='lightgray',
        zeroline=False,
        tickformat='.0f',
        ticksuffix='%'
    )

    # 保存文件
    fig.write_html(str(config.OUTPUT_DIR / 'pgim_data_plot.html'))
    fig.write_image(str(config.OUTPUT_DIR / 'pgim_data_plot.png'), scale=3)
    fig.write_image(str(config.OUTPUT_DIR / 'pgim_data_plot.pdf'))

    return fig
