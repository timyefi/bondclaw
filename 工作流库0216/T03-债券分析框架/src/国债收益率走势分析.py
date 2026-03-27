import pandas as pd
import sqlalchemy
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np
from matplotlib.dates import DateFormatter, YearLocator, date2num, num2date
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据库连接
sql_engine = sqlalchemy.create_engine(
    'mysql+pymysql://%s:%s@%s:%s/%s' % (
        'hz_work',
        'Hzinsights2015',
        'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
        '3306',
        'yq',
    ), poolclass=sqlalchemy.pool.NullPool
)

# 读取10年期国债收益率数据
bd = '2014-01-01'
ed = '2024-12-08'

query = f"""
SELECT 
    A.dt,
    A.CLOSE AS 收益率
FROM bond.marketinfo_curve A
INNER JOIN bond.basicinfo_curve B
ON A.trade_code = B.TRADE_CODE
WHERE A.dt BETWEEN '{bd}' AND '{ed}'
    AND B.classify2 = '中债国债到期收益率'
    AND B.SEC_NAME LIKE '%%10年%%'
ORDER BY A.dt
"""

data = pd.read_sql(query, sql_engine)
data['dt'] = pd.to_datetime(data['dt'])

# 计算移动平均线
data['MA20'] = data['收益率'].rolling(window=20).mean()
data['MA60'] = data['收益率'].rolling(window=60).mean()

# 创建图形和按钮
fig, ax = plt.subplots(figsize=(15, 8))
plt.subplots_adjust(bottom=0.2, right=0.85)  # 为按钮和图例留出空间

# 绘制收益率曲线和移动平均线
line_raw, = ax.plot(data['dt'], data['收益率'], linewidth=1.5, label='收益率', color='gray', alpha=0.6)
line_ma20, = ax.plot(data['dt'], data['MA20'], linewidth=2, label='20日均线', color='orange')
line_ma60, = ax.plot(data['dt'], data['MA60'], linewidth=2, label='60日均线', color='blue')

# 设置标题和标签
ax.set_title('10年期国债收益率走势图 (点击标注起点和终点)', pad=20, fontsize=12)
ax.set_xlabel('日期', fontsize=10)
ax.set_ylabel('收益率(%)', fontsize=10)
ax.grid(True, linestyle='--', alpha=0.6)

# 设置x轴时间格式
ax.xaxis.set_major_locator(YearLocator())
ax.xaxis.set_major_formatter(DateFormatter('%Y'))
plt.xticks(rotation=45)

# 添加图例
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

# 存储标注点
points = []
annotations = []
current_cycle = 1

def onclick(event):
    if event.inaxes != ax:
        return
    
    global current_cycle
    # 获取最接近点击位置的数据点
    x_date = num2date(event.xdata).replace(tzinfo=None)
    idx = abs(data['dt'] - x_date).argmin()
    x = data['dt'].iloc[idx]
    y = data['收益率'].iloc[idx]
    
    # 添加标注点，使用更醒目的样式
    point = ax.plot(x, y, 'ro', markersize=10, markerfacecolor='red', markeredgecolor='white', markeredgewidth=2)[0]
    points.append((x, y, idx))  # 存储日期、收益率和索引
    
    # 添加文本标注，改进样式
    bbox_props = dict(boxstyle="round,pad=0.3", fc="yellow", ec="b", alpha=0.8)
    if len(points) % 2 == 1:
        annotation = ax.annotate(f'周期{current_cycle}起点\n{x.strftime("%Y-%m-%d")}\n{y:.2f}%', 
                               (x, y), 
                               xytext=(10, 10),
                               textcoords='offset points',
                               bbox=bbox_props,
                               fontsize=9)
    else:
        annotation = ax.annotate(f'周期{current_cycle}终点\n{x.strftime("%Y-%m-%d")}\n{y:.2f}%', 
                               (x, y), 
                               xytext=(10, -10),
                               textcoords='offset points',
                               bbox=bbox_props,
                               fontsize=9)
        current_cycle += 1
    
    annotations.append(annotation)
    plt.draw()

def clear_points(event):
    global current_cycle
    for point in points:
        point[0].remove()  # 移除点
    for annotation in annotations:
        annotation.remove()
    points.clear()
    annotations.clear()
    current_cycle = 1
    plt.draw()

def save_points(event):
    # 保存标注点信息
    marked_points = []
    for i in range(0, len(points), 2):
        if i + 1 < len(points):
            cycle_num = i // 2 + 1
            start_date, start_yield, start_idx = points[i]
            end_date, end_yield, end_idx = points[i+1]
            
            marked_points.append({
                'cycle': cycle_num,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'start_yield': round(start_yield, 4),
                'end_yield': round(end_yield, 4),
                'yield_change': round(end_yield - start_yield, 4)
            })
    
    # 将标注点信息保存到DataFrame
    if marked_points:
        df = pd.DataFrame(marked_points)
        df.to_csv('收益率下行周期标注.csv', index=False, encoding='utf-8-sig')
        print("\n已标注的周期：")
        print(df.to_string(index=False))

# 添加按钮
ax_clear = plt.axes([0.7, 0.05, 0.1, 0.075])
ax_save = plt.axes([0.81, 0.05, 0.1, 0.075])
btn_clear = Button(ax_clear, '清除标注')
btn_save = Button(ax_save, '保存标注')

# 绑定事件
fig.canvas.mpl_connect('button_press_event', onclick)
btn_clear.on_clicked(clear_points)
btn_save.on_clicked(save_points)

plt.show() 