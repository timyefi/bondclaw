import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

# 设置pandas显示选项
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.width', 180)

def calculate_rolling_correlation(data, window=60):
    """计算滚动相关性"""
    correlations = {}
    target = 'USD_CNY'
    
    # 计算每个变量与汇率的滚动相关性
    for column in data.columns:
        if column != target and column != 'date':
            rolling_corr = data[target].rolling(window=window).corr(data[column])
            correlations[column] = rolling_corr
    
    # 将结果转换为DataFrame
    rolling_corr_df = pd.DataFrame(correlations, index=data.index)
    rolling_corr_df['date'] = data['date']
    
    return rolling_corr_df

def identify_high_correlation_periods(rolling_corr_df, threshold=0.5):
    """识别高相关性时期，只保留正相关"""
    high_corr_periods = {}
    
    for column in rolling_corr_df.columns:
        if column != 'date':
            # 获取相关系数大于阈值的时期（只保留正相关）
            high_corr = rolling_corr_df[['date', column]].copy()
            high_corr['is_high'] = (high_corr[column] >= threshold)
            
            # 识别连续的高相关期
            high_corr['period_group'] = (high_corr['is_high'] != high_corr['is_high'].shift()).cumsum()
            
            periods = []
            for group in high_corr[high_corr['is_high']]['period_group'].unique():
                period_data = high_corr[high_corr['period_group'] == group]
                if len(period_data) > 0:
                    start_date = period_data['date'].iloc[0]
                    end_date = period_data['date'].iloc[-1]
                    avg_corr = period_data[column].mean()
                    periods.append({
                        'start_date': start_date,
                        'end_date': end_date,
                        'avg_correlation': avg_corr
                    })
            
            high_corr_periods[column] = periods
    
    return high_corr_periods

def create_correlation_report(data):
    """创建相关性分析报告"""
    # 计算整体相关性
    overall_corr = data.drop('date', axis=1).corr()['USD_CNY'].drop('USD_CNY')
    
    # 计算滚动相关性
    rolling_corr_df = calculate_rolling_correlation(data)
    
    # 识别高相关性时期
    high_corr_periods = identify_high_correlation_periods(rolling_corr_df)
    
    # 创建图表
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('各因子与汇率的整体相关性', '各因子与汇率的动态相关性'),
        vertical_spacing=0.2,
        row_heights=[0.3, 0.7]
    )
    
    # 添加整体相关性柱状图
    fig.add_trace(
        go.Bar(
            x=overall_corr.index,
            y=overall_corr.values,
            name='整体相关性',
            text=overall_corr.values.round(3),
            textposition='auto',
        ),
        row=1, col=1
    )
    
    # 添加动态相关性曲线
    for column in rolling_corr_df.columns:
        if column != 'date':
            fig.add_trace(
                go.Scatter(
                    x=rolling_corr_df['date'],
                    y=rolling_corr_df[column],
                    name=column,
                    mode='lines',
                ),
                row=2, col=1
            )
    
    # 更新布局
    fig.update_layout(
        title='汇率因子相关性分析',
        showlegend=True,
        height=1000,
        template='plotly_white',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05
        ),
        annotations=[
            dict(
                text="数据来源：弘则研究，WIND，同花顺",
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.1,
                showarrow=False,
                font=dict(size=10)
            )
        ]
    )
    
    # 更新x轴和y轴标签
    fig.update_xaxes(title_text="因子", row=1, col=1)
    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="相关系数", row=1, col=1)
    fig.update_yaxes(title_text="相关系数", row=2, col=1)
    
    # 创建时间序列子图
    time_series_figs = {}
    for column in data.columns:
        if column not in ['date', 'USD_CNY']:
            # 创建子图
            subfig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 添加因子数据
            subfig.add_trace(
                go.Scatter(
                    x=data['date'],
                    y=data[column],
                    name=column,
                    line=dict(color='blue')
                ),
                secondary_y=False
            )
            
            # 添加汇率数据
            subfig.add_trace(
                go.Scatter(
                    x=data['date'],
                    y=data['USD_CNY'],
                    name='USD_CNY',
                    line=dict(color='red')
                ),
                secondary_y=True
            )
            
            # 添加高相关性时期的阴影
            if column in high_corr_periods:
                for period in high_corr_periods[column]:
                    subfig.add_vrect(
                        x0=period['start_date'],
                        x1=period['end_date'],
                        fillcolor="gray",
                        opacity=0.2,
                        layer="below",
                        line_width=0,
                    )
            
            # 更新布局
            subfig.update_layout(
                title=f'{column} vs USD_CNY (阴影区域表示高相关性时期)',
                xaxis_title="日期",
                height=400,
                showlegend=True,
                annotations=[
                    dict(
                        text="数据来源：弘则研究，WIND，同花顺",
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=-0.15,
                        showarrow=False,
                        font=dict(size=10)
                    )
                ]
            )
            
            subfig.update_yaxes(title_text=column, secondary_y=False)
            subfig.update_yaxes(title_text="USD_CNY", secondary_y=True)
            
            time_series_figs[column] = subfig
    
    return fig, time_series_figs, high_corr_periods

def generate_html_report(main_fig, time_series_figs, high_corr_periods):
    """生成HTML报告"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>汇率因子相关性分析报告</title>
        <meta charset="utf-8">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
        <style>
            body { font-family: "Microsoft YaHei", Arial, sans-serif; margin: 40px; }
            .container { max-width: 1200px; margin: auto; }
            .section { margin-bottom: 40px; position: relative; }
            .plot-container { width: 100%; margin: 20px 0; position: relative; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .download-btn {
                position: absolute;
                top: 10px;
                right: 10px;
                padding: 5px 10px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                z-index: 1000;
            }
            .download-btn:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>汇率因子相关性分析报告</h1>
            
            <div class="section">
                <h2>1. 整体相关性分析</h2>
                <button class="download-btn" onclick="downloadAsImage('main-plot', 'correlation_analysis')">下载为图片</button>
                <div id="main-plot" class="plot-container"></div>
            </div>

            <div class="section">
                <h2>2. 各因子与汇率的时间序列分析</h2>
                <p>阴影区域表示相关系数大于0.5的正相关时期</p>
                """
    
    # 添加每个因子的时间序列图
    for i, (factor, fig) in enumerate(time_series_figs.items(), 1):
        html_content += f"""
                <div class="section">
                    <h3>{i}. {factor}</h3>
                    <button class="download-btn" onclick="downloadAsImage('plot-{i}', '{factor}_analysis')">下载为图片</button>
                    <div id="plot-{i}" class="plot-container"></div>
                    <button class="download-btn" onclick="downloadTableAsImage('table-{i}', '{factor}_periods')">下载为图片</button>
                    <div id="table-{i}">
                        <h4>高相关性时期：</h4>
                        <table>
                            <tr>
                                <th>开始日期</th>
                                <th>结束日期</th>
                                <th>平均相关系数</th>
                            </tr>
        """
        
        if factor in high_corr_periods:
            for period in high_corr_periods[factor]:
                html_content += f"""
                            <tr>
                                <td>{period['start_date'].strftime('%Y-%m-%d')}</td>
                                <td>{period['end_date'].strftime('%Y-%m-%d')}</td>
                                <td>{period['avg_correlation']:.3f}</td>
                            </tr>
                """
        
        html_content += """
                        </table>
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <script>
            function downloadAsImage(elementId, filename) {
                var element = document.getElementById(elementId);
                html2canvas(element).then(function(canvas) {
                    var link = document.createElement('a');
                    link.download = filename + '.png';
                    link.href = canvas.toDataURL();
                    link.click();
                });
            }
            
            function downloadTableAsImage(elementId, filename) {
                var element = document.getElementById(elementId);
                html2canvas(element).then(function(canvas) {
                    var link = document.createElement('a');
                    link.download = filename + '.png';
                    link.href = canvas.toDataURL();
                    link.click();
                });
            }
    """
    
    # 添加图表数据
    html_content += f"var mainPlot = {main_fig.to_json()};\n"
    for i, (factor, fig) in enumerate(time_series_figs.items(), 1):
        html_content += f"var plot{i} = {fig.to_json()};\n"
    
    # 添加绘图命令
    html_content += """
            Plotly.newPlot('main-plot', mainPlot.data, mainPlot.layout);
    """
    
    for i in range(1, len(time_series_figs) + 1):
        html_content += f"Plotly.newPlot('plot-{i}', plot{i}.data, plot{i}.layout);\n"
    
    html_content += """
        </script>
    </body>
    </html>
    """
    
    return html_content

if __name__ == "__main__":
    # 读取数据
    data = pd.read_parquet('processed_data.parquet')
    
    # 生成分析图表
    main_fig, time_series_figs, high_corr_periods = create_correlation_report(data)
    
    # 生成HTML报告
    html_content = generate_html_report(main_fig, time_series_figs, high_corr_periods)
    
    # 保存HTML报告
    with open('correlation_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n相关性分析报告已生成：correlation_analysis.html") 