import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 设置页面配置
st.set_page_config(
    page_title="市场分析表",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式
st.markdown("""
    <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .title {
            text-align: center;
            color: #1f77b4;
            padding: 20px;
        }
        .source {
            text-align: right;
            color: #666;
            font-size: 0.8em;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# 创建数据
data = {
    '情景': [
        '情景一',
        '情景二',
        '情景三',
        '情景四',
        '情景五'
    ],
    '资金面': [
        '资金转松',
        '资金继续收紧',
        '资金保持紧平衡',
        '资金保持紧平衡',
        '资金保持紧平衡'
    ],
    '资金面发生概率': [
        '30%',
        '20%',
        '50%',
        '50%',
        '50%'
    ],
    '利率走势': [
        '短端修复、长端小下',
        '长短端同时调整',
        '长短端同时震荡',
        '长端调整、短端震荡',
        '长端震荡，短端继续调整'
    ],
    '利率走势条件概率': [
        '100%',
        '100%',
        '50%',
        '30%',
        '20%'
    ],
    '最终概率': [
        '30%',
        '20%',
        '25%',
        '15%',
        '10%'
    ],
    '配置建议': [
        '短端高流动性占优',
        '短端高流动性占优',
        '长端高票息占优',
        '短端高流动性占优',
        '长端高票息占优'
    ]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 页面标题
st.markdown("<h1 class='title'>当前债市情景概率表</h1>", unsafe_allow_html=True)

# 创建Plotly表格
fig = go.Figure(data=[go.Table(
    header=dict(
        values=list(df.columns),
        fill_color='#1f77b4',
        align='center',
        font=dict(color='white', size=14),
        height=40
    ),
    cells=dict(
        values=[df[col] for col in df.columns],
        fill_color='white',
        align='center',
        font=dict(color='rgb(50, 50, 50)', size=12),
        height=35
    )
)])

# 设置表格布局
fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=300,
    width=None
)

# 显示表格
st.plotly_chart(fig, use_container_width=True)

# 添加数据来源
st.markdown("<p class='source'>数据来源：弘则研究</p>", unsafe_allow_html=True)

# 添加概率分布饼图
st.markdown("<h2 style='text-align: center; color: #1f77b4; margin-top: 40px;'>配置建议分布</h2>", unsafe_allow_html=True)

# 统计配置建议分布
config_counts = df['配置建议'].value_counts()
config_percentages = (config_counts / len(df) * 100).round(1)

# 创建饼图
fig_pie = go.Figure(data=[go.Pie(
    labels=config_counts.index,
    values=config_percentages,
    hole=.3,
    marker_colors=['#1f77b4', '#ff7f0e'],
    textinfo='label+percent',
    hovertemplate="建议: %{label}<br>占比: %{percent}<extra></extra>"
)])

fig_pie.update_layout(
    height=400,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig_pie, use_container_width=True) 