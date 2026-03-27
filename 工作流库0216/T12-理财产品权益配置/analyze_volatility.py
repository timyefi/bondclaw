#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def main():
    # 读取Excel文件
    excel_file = '银行理财权益测算.xlsx'
    sheet_name = '年化波动率全量'
    
    try:
        # 读取指定工作表
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"成功读取工作表 '{sheet_name}'，数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        
        # 查找年化波动率列（可能的列名变体）
        volatility_col = None
        possible_names = ['年华波动率', '年化波动率', '波动率']
        
        for col in df.columns:
            for name in possible_names:
                if name in str(col):
                    volatility_col = col
                    break
            if volatility_col:
                break
        
        if volatility_col is None:
            print("未找到年化波动率列，可用列名:")
            for i, col in enumerate(df.columns):
                print(f"{i}: {col}")
            return
        
        print(f"使用列: {volatility_col}")
        
        # 提取年化波动率数据
        volatility_data = df[volatility_col].dropna()
        print(f"有效数据点数量: {len(volatility_data)}")
        
        # 基础统计信息
        print("\n基础统计信息:")
        print(f"最小值: {volatility_data.min():.4f}")
        print(f"最大值: {volatility_data.max():.4f}")
        print(f"平均值: {volatility_data.mean():.4f}")
        print(f"中位数: {volatility_data.median():.4f}")
        print(f"标准差: {volatility_data.std():.4f}")
        
        # 确定合理的分组数量（使用Sturges规则和Scott规则的平均值）
        n = len(volatility_data)
        sturges_bins = int(np.ceil(np.log2(n) + 1))
        scott_bins = int(np.ceil((volatility_data.max() - volatility_data.min()) / 
                                (3.5 * volatility_data.std() / (n ** (1/3)))))
        optimal_bins = max(10, min(30, int((sturges_bins + scott_bins) / 2)))
        
        print(f"\n分组统计:")
        print(f"Sturges规则建议分组数: {sturges_bins}")
        print(f"Scott规则建议分组数: {scott_bins}")
        print(f"最终使用分组数: {optimal_bins}")
        
        # 创建图形
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('银行理财产品年化波动率分布分析', fontsize=20, fontweight='bold', y=0.95)
        
        # 1. 点状分布图（散点图）
        y_jitter = np.random.normal(0, 0.02, len(volatility_data))
        ax1.scatter(volatility_data, y_jitter, alpha=0.6, s=30, c='steelblue', edgecolors='white', linewidth=0.5)
        ax1.set_xlabel('年化波动率', fontsize=12, fontweight='bold')
        ax1.set_ylabel('分布密度（带抖动）', fontsize=12, fontweight='bold')
        ax1.set_title('年化波动率点状分布图', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-0.1, 0.1)
        
        # 2. 直方图
        counts, bins, patches = ax2.hist(volatility_data, bins=optimal_bins, alpha=0.7, 
                                        color='lightcoral', edgecolor='black', linewidth=0.8)
        ax2.set_xlabel('年化波动率', fontsize=12, fontweight='bold')
        ax2.set_ylabel('频数', fontsize=12, fontweight='bold')
        ax2.set_title('年化波动率频数分布直方图', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 添加统计信息到直方图
        ax2.axvline(volatility_data.mean(), color='red', linestyle='--', linewidth=2, label=f'平均值: {volatility_data.mean():.4f}')
        ax2.axvline(volatility_data.median(), color='green', linestyle='--', linewidth=2, label=f'中位数: {volatility_data.median():.4f}')
        ax2.legend()
        
        # 3. 密度分布图（核密度估计）
        ax3.hist(volatility_data, bins=optimal_bins, density=True, alpha=0.5, color='lightblue', edgecolor='black')
        volatility_data.plot.density(ax=ax3, color='darkblue', linewidth=2)
        ax3.set_xlabel('年化波动率', fontsize=12, fontweight='bold')
        ax3.set_ylabel('密度', fontsize=12, fontweight='bold')
        ax3.set_title('年化波动率密度分布图', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # 4. 箱线图
        box_plot = ax4.boxplot(volatility_data, vert=True, patch_artist=True, 
                              boxprops=dict(facecolor='lightgreen', alpha=0.7),
                              medianprops=dict(color='red', linewidth=2),
                              whiskerprops=dict(color='black', linewidth=1.5),
                              capprops=dict(color='black', linewidth=1.5))
        ax4.set_ylabel('年化波动率', fontsize=12, fontweight='bold')
        ax4.set_title('年化波动率箱线图', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.set_xticklabels(['年化波动率'])
        
        # 添加统计信息文本框
        stats_text = f"""数据统计摘要:
样本数量: {len(volatility_data)}
最小值: {volatility_data.min():.4f}
最大值: {volatility_data.max():.4f}
平均值: {volatility_data.mean():.4f}
中位数: {volatility_data.median():.4f}
标准差: {volatility_data.std():.4f}
分组数: {optimal_bins}"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=10, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.15)
        
        # 保存图片
        plt.savefig('年化波动率分布分析.png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.show()
        
        # 创建专门的点状分布图
        create_dot_plot(volatility_data, optimal_bins)
        
        # 创建圆圈分布图
        create_circle_plot(volatility_data, optimal_bins)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def create_dot_plot(data, bins):
    """创建专业的点状分布图"""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 计算分组
    hist, bin_edges = np.histogram(data, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_width = bin_edges[1] - bin_edges[0]
    
    # 为每个分组创建点状分布
    colors = plt.cm.viridis(np.linspace(0, 1, len(bin_centers)))
    
    for i, (center, count) in enumerate(zip(bin_centers, hist)):
        if count > 0:
            # 在每个分组中随机分布点
            x_points = np.random.normal(center, bin_width/6, count)
            y_points = np.random.uniform(0, 1, count)
            
            ax.scatter(x_points, y_points, alpha=0.6, s=40, c=[colors[i]], 
                      edgecolors='white', linewidth=0.5, label=f'分组 {i+1}' if i < 5 else "")
    
    ax.set_xlabel('年化波动率', fontsize=14, fontweight='bold')
    ax.set_ylabel('分布位置（标准化）', fontsize=14, fontweight='bold')
    ax.set_title('银行理财产品年化波动率点状分布图', fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    # 添加统计线
    ax.axvline(data.mean(), color='red', linestyle='--', linewidth=2, 
              label=f'平均值: {data.mean():.4f}', alpha=0.8)
    ax.axvline(data.median(), color='green', linestyle='--', linewidth=2, 
              label=f'中位数: {data.median():.4f}', alpha=0.8)
    
    # 添加分位数线
    q25, q75 = np.percentile(data, [25, 75])
    ax.axvline(q25, color='orange', linestyle=':', linewidth=1.5, 
              label=f'25%分位数: {q25:.4f}', alpha=0.8)
    ax.axvline(q75, color='orange', linestyle=':', linewidth=1.5, 
              label=f'75%分位数: {q75:.4f}', alpha=0.8)
    
    ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    
    # 美化图表
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['bottom'].set_linewidth(1.2)
    
    plt.tight_layout()
    plt.savefig('年化波动率专业点状分布图.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.show()

def create_circle_plot(data, bins):
    """创建智能圆圈分布图，使用非线性横轴和样本数量驱动的布局"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 14))
    
    # 计算分组
    hist, bin_edges = np.histogram(data, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # 过滤掉空分组
    valid_indices = hist > 0
    valid_hist = hist[valid_indices]
    valid_centers = bin_centers[valid_indices]
    valid_edges_left = bin_edges[:-1][valid_indices]
    valid_edges_right = bin_edges[1:][valid_indices]
    
    max_count = max(valid_hist)
    print(f"\n智能圆圈分布图分组信息:")
    print("分组区间\t\t样本数量\t\t累积占比(%)")
    print("-" * 60)
    
    cumulative_count = 0
    for i, (center, count, left, right) in enumerate(zip(valid_centers, valid_hist, valid_edges_left, valid_edges_right)):
        cumulative_count += count
        cumulative_pct = (cumulative_count / len(data)) * 100
        print(f"[{left:.3f}, {right:.3f})\t{count}\t\t{cumulative_pct:.2f}")
    
    # 上图：基于累积分布的非线性横轴
    # 计算累积分布来创建非线性横轴
    cumulative_samples = np.cumsum(valid_hist)
    cumulative_ratios = cumulative_samples / len(data)
    
    # 创建非线性X轴位置：基于累积样本比例
    x_positions_cumulative = cumulative_ratios * 10  # 缩放到0-10范围
    
    # 圆圈大小：平方根缩放
    sqrt_hist = np.sqrt(valid_hist)
    max_sqrt = max(sqrt_hist)
    circle_sizes = 100 + (800 - 100) * (sqrt_hist / max_sqrt)
    
    # Y轴位置：基于样本数量的对数分布
    log_hist = np.log10(valid_hist + 1)  # +1避免log(0)
    max_log = max(log_hist)
    y_positions_log = 0.2 + 0.6 * (log_hist / max_log)  # 映射到0.2-0.8范围
    
    # 颜色映射：基于样本数量
    colors = plt.cm.plasma(valid_hist / max_count)
    
    # 绘制上图
    scatter1 = ax1.scatter(x_positions_cumulative, y_positions_log, s=circle_sizes, 
                          c=valid_hist, cmap='plasma', alpha=0.7, 
                          edgecolors='white', linewidth=1.5)
    
    # 添加样本数量标签
    for i, (x, y, count, center) in enumerate(zip(x_positions_cumulative, y_positions_log, valid_hist, valid_centers)):
        if count > max_count * 0.05:  # 大圆圈显示样本数
            ax1.text(x, y, f'{count:,}', ha='center', va='center', 
                    fontsize=8, fontweight='bold', color='white')
        if count > max_count * 0.02:  # 中等圆圈显示波动率值
            ax1.text(x, y-0.08, f'{center:.2f}%', ha='center', va='center', 
                    fontsize=7, color='darkblue', fontweight='bold')
    
    ax1.set_xlabel('累积样本分布位置（非线性）', fontsize=12, fontweight='bold')
    ax1.set_ylabel('样本数量层次（对数刻度）', fontsize=12, fontweight='bold')
    ax1.set_title('智能圆圈分布图（基于累积分布的非线性布局）', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 添加颜色条
    cbar1 = plt.colorbar(scatter1, ax=ax1, shrink=0.8)
    cbar1.set_label('样本数量', fontsize=10)
    
    # 创建自定义X轴标签（显示实际波动率值）
    x_tick_positions = []
    x_tick_labels = []
    for i in range(0, len(x_positions_cumulative), max(1, len(x_positions_cumulative)//8)):
        x_tick_positions.append(x_positions_cumulative[i])
        x_tick_labels.append(f'{valid_centers[i]:.2f}%')
    
    ax1.set_xticks(x_tick_positions)
    ax1.set_xticklabels(x_tick_labels, rotation=45)
    
    # 下图：分位数驱动的布局
    # 根据波动率分位数创建X轴位置
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    percentile_values = np.percentile(data, percentiles)
    
    # 为每个有效分组找到最近的分位数位置
    x_positions_percentile = []
    for center in valid_centers:
        # 找到最接近的分位数位置
        closest_percentile_idx = np.argmin(np.abs(percentile_values - center))
        x_pos = percentiles[closest_percentile_idx] / 100 * 10  # 映射到0-10
        x_positions_percentile.append(x_pos)
    
    x_positions_percentile = np.array(x_positions_percentile)
    
    # Y轴：基于样本数量的螺旋分布
    # 样本数量越多，越靠近中心；样本数量少的，分散在外围
    theta = np.linspace(0, 4*np.pi, len(valid_hist))  # 螺旋角度
    radius_base = 1 - (valid_hist / max_count) * 0.8  # 基础半径：样本多的靠近中心
    
    # 添加一些随机扰动避免重叠
    np.random.seed(42)  # 固定随机种子保证结果可重复
    radius_jitter = radius_base + np.random.normal(0, 0.05, len(radius_base))
    radius_jitter = np.clip(radius_jitter, 0.1, 0.9)
    
    y_positions_spiral = 0.5 + radius_jitter * np.sin(theta) * 0.4
    x_positions_spiral = x_positions_percentile + radius_jitter * np.cos(theta) * 0.3
    
    # 绘制下图
    scatter2 = ax2.scatter(x_positions_spiral, y_positions_spiral, s=circle_sizes, 
                          c=valid_hist, cmap='viridis', alpha=0.7, 
                          edgecolors='white', linewidth=1.5)
    
    # 添加标签
    for i, (x, y, count, center) in enumerate(zip(x_positions_spiral, y_positions_spiral, valid_hist, valid_centers)):
        if count > max_count * 0.1:  # 只为最大的圆圈添加标签
            ax2.text(x, y, f'{count:,}', ha='center', va='center', 
                    fontsize=9, fontweight='bold', color='white')
            ax2.text(x, y-0.12, f'{center:.2f}%', ha='center', va='center', 
                    fontsize=8, color='darkred', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7))
    
    ax2.set_xlabel('波动率分位数布局（非线性）', fontsize=12, fontweight='bold')
    ax2.set_ylabel('样本密度分布（螺旋布局）', fontsize=12, fontweight='bold')
    ax2.set_title('分位数驱动的螺旋分布图', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 添加颜色条
    cbar2 = plt.colorbar(scatter2, ax=ax2, shrink=0.8)
    cbar2.set_label('样本数量', fontsize=10)
    
    # 设置X轴标签为分位数
    ax2.set_xticks([p/100*10 for p in percentiles])
    ax2.set_xticklabels([f'{p}%分位\n({v:.2f})' for p, v in zip(percentiles, percentile_values)], 
                       fontsize=8, rotation=45)
    
    # 添加关键统计线
    mean_pos = np.interp(data.mean(), percentile_values, [p/100*10 for p in percentiles])
    median_pos = np.interp(data.median(), percentile_values, [p/100*10 for p in percentiles])
    
    ax2.axvline(mean_pos, color='red', linestyle='--', linewidth=2, alpha=0.8, 
               label=f'平均值: {data.mean():.4f}')
    ax2.axvline(median_pos, color='green', linestyle='--', linewidth=2, alpha=0.8, 
               label=f'中位数: {data.median():.4f}')
    ax2.legend(loc='upper right')
    
    # 添加统计信息文本框
    stats_text = f"""智能布局统计:
总样本数: {len(data):,}
有效分组数: {len(valid_hist)}
最大分组样本数: {max_count:,}
数据分布特征:
- 50%数据集中在: {np.percentile(data, 50):.3f}%以下
- 90%数据集中在: {np.percentile(data, 90):.3f}%以下
- 99%数据集中在: {np.percentile(data, 99):.3f}%以下
非线性缩放效果:
- 上图: 累积分布驱动的X轴
- 下图: 分位数+螺旋布局"""
    
    fig.text(0.02, 0.5, stats_text, fontsize=10,
            verticalalignment='center', bbox=dict(boxstyle="round,pad=0.5", 
            facecolor="lightcyan", alpha=0.9))
    
    plt.tight_layout()
    plt.subplots_adjust(left=0.25)
    plt.savefig('年化波动率圆圈分布图.png', dpi=300, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    plt.show()

if __name__ == "__main__":
    main() 