import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import jieba
from sklearn.preprocessing import MinMaxScaler
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import warnings
import os
from config import KEYWORDS_DICT
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 确保输出目录存在
def ensure_output_dir():
    if not os.path.exists('output'):
        os.makedirs('output')
        print("创建输出目录: output/")

def add_data_source(fig):
    """添加数据来源说明"""
    fig.text(0.99, 0.01, '数据来源：弘则研究，企业发行人募集说明书', 
             ha='right', va='bottom', fontsize=8, style='italic')

def plot_keyword_heatmap(keyword_counts, sample_type=""):
    """绘制关键词热力图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(15, 10))
    
    # 准备数据
    categories = list(keyword_counts.keys())
    keywords = []
    frequencies = []
    cats = []
    
    for category in categories:
        for keyword, count in keyword_counts[category].items():
            keywords.append(keyword)
            frequencies.append(count)
            cats.append(category)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'Category': cats,
        'Keyword': keywords,
        'Frequency': frequencies
    })
    
    # 转换为透视表
    pivot_table = df.pivot(index='Category', columns='Keyword', values='Frequency')
    
    # 绘制热力图
    sns.heatmap(pivot_table, cmap='YlOrRd', annot=True, fmt='.0f')
    plt.title(f'{sample_type}关键词频率热力图')
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_keyword_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_wordcloud(texts, sample_type=""):
    """生成词云图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(15, 10))
    
    # 合并所有文本
    text = ' '.join([str(t) for t in texts if isinstance(t, str)])
    
    # 定义停用词列表
    stopwords = {'募集', '资金', '全部', '用于', '本期', '债券', '发行', '费用', '亿元', 
                '募集', '本期', '本金', '发', '本', '的', '了', '和', '与', '及', '将'}
    
    # 获取所有关键词
    all_keywords = set()
    for keywords in KEYWORDS_DICT.values():
        all_keywords.update(keywords)
    
    # 分词并只保留关键词列表中的词
    words = jieba.lcut(text)
    keyword_freq = {}
    for word in words:
        if word in all_keywords and word not in stopwords:
            keyword_freq[word] = keyword_freq.get(word, 0) + 1
    
    if not keyword_freq:
        print("没有找到关键词,无法生成词云图")
        return
    
    # 生成词云
    wordcloud = WordCloud(
        width=1200, height=800,
        background_color='white',
        font_path='C:/Windows/Fonts/simhei.ttf',  # 使用Windows系统自带的黑体字体
        min_font_size=10,
        max_font_size=100,
        max_words=100,
        collocations=False  # 避免词语重复
    ).generate_from_frequencies(keyword_freq)
    
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'{sample_type}关键词词云图')
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_wordcloud.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_radar_chart(keyword_counts, sample_type=""):
    """绘制雷达图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(10, 10))
    
    # 准备数据
    categories = list(keyword_counts.keys())
    values = [sum(keyword_counts[cat].values()) for cat in categories]
    
    # 计算角度
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
    
    # 闭合图形
    values = np.concatenate((values, [values[0]]))
    angles = np.concatenate((angles, [angles[0]]))
    
    # 绘制雷达图
    ax = plt.subplot(111, projection='polar')
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    plt.title(f'{sample_type}维度分布雷达图')
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_radar_chart.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_usage_pie(df, sample_type=""):
    """绘制资金用途饼图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(12, 8))
    
    # 准备数据
    usage_cols = ['借新还旧(亿)', '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)']
    values = [df[col].astype(float).sum() for col in usage_cols]
    total = sum(values)
    percentages = [v/total*100 for v in values]
    
    # 绘制饼图
    plt.pie(percentages, labels=usage_cols, autopct='%1.1f%%')
    plt.title(f'{sample_type}资金用途分布')
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_usage_pie.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_usage_boxplot(df, sample_type=""):
    """绘制资金用途箱线图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(15, 8))
    
    # 准备数据
    usage_cols = ['借新还旧(亿)', '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)']
    
    # 数据预处理和清洗
    data = []
    for col in usage_cols:
        # 转换为数值型,非数值替换为NaN
        series = pd.to_numeric(df[col], errors='coerce')
        # 移除异常值(可选)
        # q1 = series.quantile(0.25)
        # q3 = series.quantile(0.75)
        # iqr = q3 - q1
        # series = series[(series >= q1 - 1.5*iqr) & (series <= q3 + 1.5*iqr)]
        data.append(series)
    
    # 打印数据统计信息用于调试
    for col, series in zip(usage_cols, data):
        print(f"\n{col} 统计信息:")
        print(f"数据点数量: {len(series.dropna())}")
        print(f"平均值: {series.mean():.2f}")
        print(f"中位数: {series.median():.2f}")
        print(f"最大值: {series.max():.2f}")
        print(f"最小值: {series.min():.2f}")
    
    # 绘制箱线图
    plt.boxplot(data, labels=usage_cols, showfliers=True)
    plt.xticks(rotation=45)
    plt.title(f'{sample_type}资金用途金额分布')
    plt.ylabel('金额(亿元)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_usage_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_monthly_trend(df, sample_type=""):
    """绘制月度趋势图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(15, 8))
    
    # 转换日期
    df['公告日期'] = pd.to_datetime(df['公告日期'])
    monthly_data = df.groupby(df['公告日期'].dt.to_period('M'))['发行规模(亿)'].sum()
    
    # 绘制趋势线
    plt.plot(range(len(monthly_data)), monthly_data.values)
    plt.xticks(range(len(monthly_data))[::6], monthly_data.index[::6], rotation=45)
    plt.title(f'{sample_type}月度发行规模趋势')
    plt.ylabel('发行规模(亿元)')
    plt.grid(True)
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_monthly_trend.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_cumulative_amount(df, sample_type=""):
    """绘制累计发行规模图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(15, 8))
    
    # 准备数据
    df['公告日期'] = pd.to_datetime(df['公告日期'])
    df = df.sort_values('公告日期')
    df['累计规模'] = df['发行规模(亿)'].astype(float).cumsum()
    
    # 绘制面积图
    plt.fill_between(range(len(df)), df['累计规模'])
    plt.title(f'{sample_type}累计发行规模')
    plt.ylabel('累计规模(亿元)')
    plt.grid(True)
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_cumulative_amount.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_cluster_scatter(tfidf_matrix, clusters, sample_type=""):
    """绘制聚类散点图"""
    ensure_output_dir()
    fig = plt.figure(figsize=(12, 8))
    
    # 降维处理
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    coords = pca.fit_transform(tfidf_matrix.toarray())
    
    # 绘制散点图
    plt.scatter(coords[:, 0], coords[:, 1], c=clusters)
    plt.title(f'{sample_type}文本聚类结果')
    plt.xlabel('第一主成分')
    plt.ylabel('第二主成分')
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/{sample_type}_cluster_scatter.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_all_plots(transform_samples, normal_samples):
    """生成所有可视化图表"""
    import os
    
    # 创建输出目录
    if not os.path.exists('output'):
        os.makedirs('output')
    
    # 转换为DataFrame
    transform_df = pd.DataFrame(transform_samples, 
                              columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)', 
                                     '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
    normal_df = pd.DataFrame(normal_samples,
                           columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)',
                                  '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
    
    # 生成转型城投图表
    print("正在生成转型城投图表...")
    plot_usage_pie(transform_df, "转型城投")
    plot_usage_boxplot(transform_df, "转型城投")
    plot_monthly_trend(transform_df, "转型城投")
    plot_cumulative_amount(transform_df, "转型城投")
    
    # 生成普通城投图表
    print("正在生成普通城投图表...")
    plot_usage_pie(normal_df, "普通城投")
    plot_usage_boxplot(normal_df, "普通城投")
    plot_monthly_trend(normal_df, "普通城投")
    plot_cumulative_amount(normal_df, "普通城投")
    
    print("图表生成完成，已保存到output目录") 

def plot_keyword_comparison(keyword_counts1, keyword_counts2, sample_type1="转型城投", sample_type2="普通城投",time_period=""):
    """绘制关键词对比图"""
    ensure_output_dir()
    
    # 计算每个样本的总词频
    def get_total_freq(keyword_counts):
        total = 0
        for category in keyword_counts.values():
            total += sum(category.values())
        return total
    
    total_freq1 = get_total_freq(keyword_counts1)
    total_freq2 = get_total_freq(keyword_counts2)
    
    # 对每个类别生成对比图
    for category in keyword_counts1.keys():
        fig = plt.figure(figsize=(15, 8))
        
        # 获取该类别下的所有关键词
        keywords = list(set(keyword_counts1[category].keys()) | set(keyword_counts2[category].keys()))
        
        # 计算频率占比
        values1 = [(keyword_counts1[category].get(k, 0) / total_freq1 * 100) for k in keywords]
        values2 = [(keyword_counts2[category].get(k, 0) / total_freq2 * 100) for k in keywords]
        
        # 设置条形图
        x = np.arange(len(keywords))
        width = 0.35
        
        plt.bar(x - width/2, values1, width, label=sample_type1)
        plt.bar(x + width/2, values2, width, label=sample_type2)
        
        plt.xlabel('关键词')
        plt.ylabel('频率占比(%)')
        plt.title(f'{category}关键词频率对比')
        plt.xticks(x, keywords, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 在柱状图上添加数值标签
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                plt.text(rect.get_x() + rect.get_width()/2., height,
                        f'{height:.2f}%',
                        ha='center', va='bottom')
        
        # 获取图形中的柱状图对象
        bars = plt.gca().patches
        autolabel(bars[:len(keywords)])  # 第一组柱状图
        autolabel(bars[len(keywords):])  # 第二组柱状图
        
        # 调整布局避免标签被截断
        plt.tight_layout()
        
        # 添加数据来源
        add_data_source(fig)
        
        plt.savefig(f'output/{category}_comparison_{time_period}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # 额外生成产业转型相关词频对比图
    fig = plt.figure(figsize=(15, 8))
    
    # 合并产业投资和转型相关的关键词
    transform_keywords = list(set(keyword_counts1['产业投资'].keys()) | set(keyword_counts2['产业投资'].keys()) |
                            set(keyword_counts1['转型相关'].keys()) | set(keyword_counts2['转型相关'].keys()))
    
    # 计算频率占比
    values1 = []
    values2 = []
    for k in transform_keywords:
        # 计算每个关键词在两个类别中的总频率
        freq1 = (keyword_counts1['产业投资'].get(k, 0) + keyword_counts1['转型相关'].get(k, 0)) / total_freq1 * 100
        freq2 = (keyword_counts2['产业投资'].get(k, 0) + keyword_counts2['转型相关'].get(k, 0)) / total_freq2 * 100
        values1.append(freq1)
        values2.append(freq2)
    
    # 设置条形图
    x = np.arange(len(transform_keywords))
    width = 0.35
    
    plt.bar(x - width/2, values1, width, label=sample_type1)
    plt.bar(x + width/2, values2, width, label=sample_type2)
    
    plt.xlabel('关键词')
    plt.ylabel('频率占比(%)')
    plt.title('产业转型相关关键词频率对比')
    plt.xticks(x, transform_keywords, rotation=45, ha='right')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 在柱状图上添加数值标签
    bars = plt.gca().patches
    autolabel(bars[:len(transform_keywords)])  # 第一组柱状图
    autolabel(bars[len(transform_keywords):])  # 第二组柱状图
    
    # 调整布局避免标签被截断
    plt.tight_layout()
    
    # 添加数据来源
    add_data_source(fig)
    
    plt.savefig(f'output/产业转型相关_comparison_{time_period}.png', dpi=300, bbox_inches='tight')
    plt.close() 