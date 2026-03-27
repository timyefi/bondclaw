import numpy as np
import jieba
import pymysql
import re
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.cluster import KMeans
import warnings
from collections import Counter
import pandas as pd
from datetime import datetime
from visualize_analysis import (plot_keyword_heatmap, plot_wordcloud, plot_radar_chart,
                              plot_usage_pie, plot_usage_boxplot, plot_monthly_trend,
                              plot_cumulative_amount, plot_cluster_scatter, plot_keyword_comparison)
from config import KEYWORDS_DICT
warnings.filterwarnings('ignore')

def connect_db():
    print("正在连接数据库...")
    try:
        conn = pymysql.connect(
            host='rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
            user='hz_work',
            password='Hzinsights2015',
            database='yq',
            port=3306,
            charset='utf8'
        )
        print("数据库连接成功")
        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        raise

def get_text_samples():
    print("连接数据库...")
    conn = connect_db()
    cursor = conn.cursor()
    
    # 获取近1年样本
    print("执行转型城投查询(近1年)...")
    cursor.execute("""
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 城投募集资金用途 
                   WHERE 发行人 in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2023-10-26'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                   union
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 产业债募集资金用途
                   WHERE 发行人 in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2023-10-26'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                   """)
    transform_samples_1y = cursor.fetchall()
    print(f"获取到转型城投样本(近1年): {len(transform_samples_1y)}条")
    
    print("执行普通城投查询(近1年)...")
    cursor.execute("""
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 城投募集资金用途 
                   WHERE 发行人 not in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2023-10-26'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
                   """)
    normal_samples_1y = cursor.fetchall()
    print(f"获取到普通城投样本(近1年): {len(normal_samples_1y)}条")
    
    # 获取近3个月样本
    print("\n执行转型城投查询(近3个月)...")
    cursor.execute("""
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 城投募集资金用途 
                   WHERE 发行人 in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        where 披露日期>='2024-10-1'
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2024-10-1'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                   union
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 产业债募集资金用途
                   WHERE 发行人 in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        where 披露日期>='2024-10-1'
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2024-10-1'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                   """)
    transform_samples_3m = cursor.fetchall()
    print(f"获取到转型城投样本(近3个月): {len(transform_samples_3m)}条")
    
    print("执行普通城投查询(近3个月)...")
    cursor.execute("""
                   SELECT `原文`, `发行人`, `公告日期`, `发行规模(亿)`, `借新还旧(亿)`, 
                          `偿还有息债务(亿)`, `补充流动资金(亿)`, `项目建设(亿)`, `其他(亿)`
                   FROM 城投募集资金用途 
                   WHERE 发行人 not in (
                        select distinct 公司名称 
                        from yq.城投平台市场化经营主体
                        where 披露日期>='2024-10-1'
                        union
                        select distinct 公司名称 
                        from yq.城投平台退出
                        where 披露日期>='2024-10-1'
                   )
                   AND 公告日期 >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                   """)
    normal_samples_3m = cursor.fetchall()
    print(f"获取到普通城投样本(近3个月): {len(normal_samples_3m)}条")
    
    cursor.close()
    conn.close()
    print("数据库连接已关闭")
    
    return (transform_samples_1y, normal_samples_1y), (transform_samples_3m, normal_samples_3m)

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    
    # 移除多余空白字符
    text = ' '.join(text.split())
    
    # 移除特殊字符，保留中文、英文、数字
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
    
    # 移除独立数字，但保留带单位的数字
    text = re.sub(r'\b\d+\b(?!\s*[亿万元])', '', text)
    
    # 移除过短的文本
    if len(text.strip()) < 10:
        return ""
        
    return text.strip()

def analyze_keywords(texts, keywords_dict):
    total_words = 0
    keyword_counts = {category: {word: 0 for word in words} 
                     for category, words in keywords_dict.items()}
    
    for text in texts:
        if not isinstance(text, str):
            continue
            
        text_content = str(text)
        if not text_content:
            continue
            
        # 分词并统计总词数
        words = jieba.lcut(text_content)
        total_words += len(words)
        
        # 对每个类别的每个关键词进行计数
        for category, keywords in keywords_dict.items():
            for word in keywords:
                count = sum(1 for w in words if w == word)  # 使用精确匹配
                if count > 0:
                    keyword_counts[category][word] += count
    
    # 打印分析结果
    print("\n关键词频率分析结果:")
    for category, counts in keyword_counts.items():
        category_total = sum(counts.values())
        if category_total > 0:
            print(f"\n{category}:")
            for word, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    percentage = count / total_words * 100
                    print(f"- {word}: {count}次 ({percentage:.2f}%)")
    
    return keyword_counts

def perform_clustering(texts, n_clusters=5):
    """对文本进行聚类分析"""
    if not texts:
        print("输入文本列表为空")
        return None, None
    
    # 文本预处理
    processed_texts = []
    for text in texts:
        try:
            # 确保文本是字符串类型
            if not isinstance(text, str):
                text = str(text) if text is not None else ""
            
            # 清理和分词
            text = text.strip()
            if not text:  # 跳过空文本
                continue
                
            # 使用jieba分词
            words = jieba.lcut(text)
            if not words:  # 跳过分词结果为空的情况
                continue
                
            # 过滤空词并拼接
            words = [w.strip() for w in words if w.strip() and len(w.strip()) > 1]
            if not words:  # 跳过过滤后为空的情况
                continue
                
            processed_text = " ".join(words)
            if processed_text.strip():  # 最后确认处理后的文本非空
                processed_texts.append(processed_text)
                
        except Exception as e:
            print(f"处理文本时出错: {str(e)}")
            continue
    
    # 检查处理后的文本
    if not processed_texts:
        print("预处理后没有有效的文本数据")
        return None, None
    
    print(f"有效文本数量: {len(processed_texts)}")
    
    try:
        # 向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.95,
            token_pattern=r"(?u)\b\w+\b"  # 匹配任何单词字符
        )
        X = vectorizer.fit_transform(processed_texts)
        print(f"向量化后的文本维度: {X.shape}")
        
        # 调整聚类数
        n_clusters = min(n_clusters, len(processed_texts))
        if n_clusters < 2:
            print("样本数量太少，无法进行聚类分析")
            return None, None
        
        # 聚类 - 移除 n_jobs 参数
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
            max_iter=300,
            algorithm='elkan'  # 使用 elkan 算法，通常比 lloyd 更快
        )
        clusters = kmeans.fit_predict(X)
        print(f"聚类完成，共{n_clusters}个簇")
        
        # 分析关键词
        feature_names = vectorizer.get_feature_names_out()
        cluster_keywords = {}
        
        for i in range(n_clusters):
            cluster_docs = X[clusters == i]
            if cluster_docs.shape[0] == 0:
                continue
            
            centroid = cluster_docs.mean(axis=0).A1
            sorted_indices = centroid.argsort()[::-1][:10]
            keywords = [feature_names[j] for j in sorted_indices]
            cluster_keywords[i] = keywords
            
            print(f"\n簇 {i} (包含{cluster_docs.shape[0]}个文档)的关键词:")
            print(", ".join(keywords))
        
        return clusters, cluster_keywords
        
    except Exception as e:
        print(f"聚类过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def analyze_time_patterns(samples, sample_type=""):
    print(f"\n{sample_type}时间分析:")
    
    # 转换为DataFrame
    df = pd.DataFrame(samples, columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)', 
                                      '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
    
    # 转换公告日期为datetime
    df['公告日期'] = pd.to_datetime(df['公告日期'])
    
    # 按月份统计发行数量
    monthly_counts = df.groupby(df['公告日期'].dt.to_period('M')).size()
    print("\n月度发行数量:")
    for month, count in monthly_counts.items():
        print(f"{month}: {count}笔")
    
    # 按月份统计发行规模
    df['发行规模(亿)'] = pd.to_numeric(df['发行规模(亿)'], errors='coerce')
    monthly_amounts = df.groupby(df['公告日期'].dt.to_period('M'))['发行规模(亿)'].sum()
    print("\n月度发行规模(亿元):")
    for month, amount in monthly_amounts.items():
        print(f"{month}: {amount:.2f}亿")
    
    # 生成趋势图
    plot_monthly_trend(df, sample_type)
    plot_cumulative_amount(df, sample_type)

def save_analysis_results(results):
    """保存分析结果到文件"""
    import json
    import os
    from datetime import datetime
    
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 将结果转换为可序列化的格式
    serializable_results = {}
    for sample_type, data in results.items():
        serializable_results[sample_type] = {
            'keyword_counts': {
                category: {word: count for word, count in counts.items()}
                for category, counts in data['keyword_counts'].items()
            },
            'cluster_keywords': data['cluster_keywords'] if data['cluster_keywords'] else {}
        }
    
    # 保存为JSON文件
    output_file = f'output/analysis_results_{timestamp}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到: {output_file}")

def main():
    print("开始执行分析...")
    
    # 获取样本数据
    print("正在获取样本数据...")
    (transform_samples_1y, normal_samples_1y), (transform_samples_3m, normal_samples_3m) = get_text_samples()
    
    # 创建向量化器
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.95,
        token_pattern=r"(?u)\b\w+\b"
    )

    # 分析转型城投样本(近1年)
    print("\n=== 转型城投样本分析(近1年) ===")
    if transform_samples_1y:
        # 提取文本和转换为DataFrame
        transform_texts = [sample[0] for sample in transform_samples_1y if sample[0]]
        transform_df = pd.DataFrame(transform_samples_1y, 
                                  columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)', 
                                         '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
        
        # 关键词分析
        transform_keyword_counts = analyze_keywords(transform_texts, KEYWORDS_DICT)
        
        # 聚类分析
        transform_clusters, transform_keywords = perform_clustering(transform_texts)
        
        # 时间分析
        analyze_time_patterns(transform_samples_1y, "transform_1y")
        
        # 生成可视化
        plot_wordcloud(transform_texts, "转型城投(近1年)")
        plot_keyword_heatmap(transform_keyword_counts, "转型城投(近1年)")
        plot_radar_chart(transform_keyword_counts, "转型城投(近1年)")
        plot_usage_pie(transform_df, "转型城投(近1年)")
        plot_usage_boxplot(transform_df, "转型城投(近1年)")
        if transform_clusters is not None:
            # 向量化文本用于聚类可视化
            transform_vectors = vectorizer.fit_transform(transform_texts)
            plot_cluster_scatter(transform_vectors, transform_clusters, "转型城投(近1年)")
    else:
        print("未获取到转型城投样本数据")

    # 分析普通城投样本(近1年)
    print("\n=== 普通城投样本分析(近1年) ===")
    if normal_samples_1y:
        # 提取文本和转换为DataFrame
        normal_texts = [sample[0] for sample in normal_samples_1y if sample[0]]
        normal_df = pd.DataFrame(normal_samples_1y,
                               columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)',
                                      '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
        
        # 关键词分析
        normal_keyword_counts = analyze_keywords(normal_texts, KEYWORDS_DICT)
        
        # 聚类分析
        normal_clusters, normal_keywords = perform_clustering(normal_texts)
        
        # 时间分析
        analyze_time_patterns(normal_samples_1y, "normal_1y")
        
        # 生成可视化
        plot_wordcloud(normal_texts, "普通城投(近1年)")
        plot_keyword_heatmap(normal_keyword_counts, "普通城投(近1年)")
        plot_radar_chart(normal_keyword_counts, "普通城投(近1年)")
        plot_usage_pie(normal_df, "普通城投(近1年)")
        plot_usage_boxplot(normal_df, "普通城投(近1年)")
        if normal_clusters is not None:
            # 向量化文本用于聚类可视化
            normal_vectors = vectorizer.fit_transform(normal_texts)
            plot_cluster_scatter(normal_vectors, normal_clusters, "普通城投(近1年)")
    else:
        print("未获取到普通城投样本数据")

    # 生成对比可视化(近1年)
    if transform_samples_1y and normal_samples_1y:
        plot_keyword_comparison(transform_keyword_counts, normal_keyword_counts, 
                              "转型城投(近1年)", "普通城投(近1年)",'近1年')
        print("\n已生成关键词对比图表(近1年)")

    # 分析转型城投样本(近3个月)
    print("\n=== 转型城投样本分析(近3个月) ===")
    if transform_samples_3m:
        # 提取文本和转换为DataFrame
        transform_texts = [sample[0] for sample in transform_samples_3m if sample[0]]
        transform_df = pd.DataFrame(transform_samples_3m, 
                                  columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)', 
                                         '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
        
        # 关键词分析
        transform_keyword_counts = analyze_keywords(transform_texts, KEYWORDS_DICT)
        
        # 聚类分析
        transform_clusters, transform_keywords = perform_clustering(transform_texts)
        
        # 时间分析
        analyze_time_patterns(transform_samples_3m, "transform_3m")
        
        # 生成可视化
        plot_wordcloud(transform_texts, "转型城投(近3个月)")
        plot_keyword_heatmap(transform_keyword_counts, "转型城投(近3个月)")
        plot_radar_chart(transform_keyword_counts, "转型城投(近3个月)")
        plot_usage_pie(transform_df, "转型城投(近3个月)")
        plot_usage_boxplot(transform_df, "转型城投(近3个月)")
        if transform_clusters is not None:
            # 向量化文本用于聚类可视化
            transform_vectors = vectorizer.fit_transform(transform_texts)
            plot_cluster_scatter(transform_vectors, transform_clusters, "转型城投(近3个月)")
    else:
        print("未获取到转型城投样本数据")

    # 分析普通城投样本(近3个月)
    print("\n=== 普通城投样本分析(近3个月) ===")
    if normal_samples_3m:
        # 提取文本和转换为DataFrame
        normal_texts = [sample[0] for sample in normal_samples_3m if sample[0]]
        normal_df = pd.DataFrame(normal_samples_3m,
                               columns=['原文', '发行人', '公告日期', '发行规模(亿)', '借新还旧(亿)',
                                      '偿还有息债务(亿)', '补充流动资金(亿)', '项目建设(亿)', '其他(亿)'])
        
        # 关键词分析
        normal_keyword_counts = analyze_keywords(normal_texts, KEYWORDS_DICT)
        
        # 聚类分析
        normal_clusters, normal_keywords = perform_clustering(normal_texts)
        
        # 时间分析
        analyze_time_patterns(normal_samples_3m, "normal_3m")
        
        # 生成可视化
        plot_wordcloud(normal_texts, "普通城投(近3个月)")
        plot_keyword_heatmap(normal_keyword_counts, "普通城投(近3个月)")
        plot_radar_chart(normal_keyword_counts, "普通城投(近3个月)")
        plot_usage_pie(normal_df, "普通城投(近3个月)")
        plot_usage_boxplot(normal_df, "普通城投(近3个月)")
        if normal_clusters is not None:
            # 向量化文本用于聚类可视化
            normal_vectors = vectorizer.fit_transform(normal_texts)
            plot_cluster_scatter(normal_vectors, normal_clusters, "普通城投(近3个月)")
    else:
        print("未获取到普通城投样本数据")

    # 生成对比可视化(近3个月)
    if transform_samples_3m and normal_samples_3m:
        plot_keyword_comparison(transform_keyword_counts, normal_keyword_counts,
                              "转型城投(近3个月)", "普通城投(近3个月)",'近3个月')
        print("\n已生成关键词对比图表(近3个月)")

    # 保存分析结果
    save_analysis_results({
        'transform_1y': {
            'keyword_counts': transform_keyword_counts if transform_samples_1y else {},
            'cluster_keywords': transform_keywords if transform_samples_1y else {}
        },
        'normal_1y': {
            'keyword_counts': normal_keyword_counts if normal_samples_1y else {},
            'cluster_keywords': normal_keywords if normal_samples_1y else {}
        },
        'transform_3m': {
            'keyword_counts': transform_keyword_counts if transform_samples_3m else {},
            'cluster_keywords': transform_keywords if transform_samples_3m else {}
        },
        'normal_3m': {
            'keyword_counts': normal_keyword_counts if normal_samples_3m else {},
            'cluster_keywords': normal_keywords if normal_samples_3m else {}
        }
    })

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"执行过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc() 