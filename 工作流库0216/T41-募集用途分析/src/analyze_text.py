import sqlite3
import jieba
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

warnings.filterwarnings('ignore')

# 定义关键词字典
KEYWORDS_DICT = {
    '债务管理': ['偿还', '债务', '贷款', '融资', '借款', '还款'],
    '资金用途': ['补充流动资金', '项目建设', '基础设施', '投资', '建设'],
    '转型相关': ['转型', '改革', '创新', '升级', '发展'],
    '政府关系': ['政府', '财政', '补贴', '划拨', '注入'],
    '业务发展': ['主营业务', '收入', '营收', '利润', '效益'],
    '产业投资': ['产业', '园区', '制造', '科技', '研发'],
    '市场竞争': ['市场', '竞争', '优势', '品牌', '客户'],
    '创新发展': ['创新', '技术', '研发', '专利', '知识产权'],
    '公司治理': ['治理', '管理', '制度', '规范', '风控'],
    '财务状况': ['资产', '负债', '收入', '利润', '现金流'],
    '转型效果': ['成果', '效果', '业绩', '增长', '提升'],
    '市场化指标': ['市场化', '商业化', '效率', '竞争力'],
    '企业文化': ['文化', '人才', '团队', '价值观'],
    '社会责任': ['责任', '环保', '可持续', '公益']
}

def analyze_text(text):
    """分析单个文本"""
    if not isinstance(text, str) or not text.strip():
        return {}
    
    # 分词
    words = jieba.lcut(text)
    
    # 统计关键词
    keyword_counts = {}
    for category, keywords in KEYWORDS_DICT.items():
        category_counts = {}
        for keyword in keywords:
            count = sum(1 for w in words if w == keyword)
            if count > 0:
                category_counts[keyword] = count
        if category_counts:
            keyword_counts[category] = category_counts
    
    return keyword_counts

def analyze_texts(texts):
    """分析多个文本"""
    all_counts = {category: {word: 0 for word in words} 
                 for category, words in KEYWORDS_DICT.items()}
    
    total_words = 0
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            continue
        
        # 分词
        words = jieba.lcut(text)
        total_words += len(words)
        
        # 统计关键词
        for category, keywords in KEYWORDS_DICT.items():
            for keyword in keywords:
                count = sum(1 for w in words if w == keyword)
                if count > 0:
                    all_counts[category][keyword] += count
    
    # 计算并打印统计结果
    print("\n关键词频率分析结果:")
    for category, counts in all_counts.items():
        category_total = sum(counts.values())
        if category_total > 0:
            print(f"\n{category}:")
            for word, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    percentage = count / total_words * 100
                    print(f"- {word}: {count}次 ({percentage:.2f}%)")
    
    return all_counts

def cluster_texts(texts, n_clusters=3):
    """对文本进行聚类分析"""
    if not texts or len(texts) < n_clusters:
        print("文本数量不足以进行聚类分析")
        return None, None
    
    # 文本预处理
    processed_texts = []
    for text in texts:
        if isinstance(text, str) and text.strip():
            words = jieba.lcut(text)
            processed_texts.append(' '.join(words))
    
    if not processed_texts:
        print("没有有效的文本进行聚类")
        return None, None
    
    # 向量化
    vectorizer = TfidfVectorizer(max_features=1000)
    try:
        X = vectorizer.fit_transform(processed_texts)
        print(f"向量化完成，维度: {X.shape}")
    except Exception as e:
        print(f"向量化失败: {e}")
        return None, None
    
    # 聚类
    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(X)
        print(f"聚类完成，共{n_clusters}个簇")
    except Exception as e:
        print(f"聚类失败: {e}")
        return None, None
    
    # 分析簇的特征词
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

def plot_keyword_comparison(counts1, counts2, label1="组1", label2="组2"):
    """绘制关键词对比图"""
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 对每个类别生成对比图
    for category in counts1.keys():
        plt.figure(figsize=(12, 6))
        
        # 获取所有关键词
        keywords = list(set(counts1[category].keys()) | set(counts2[category].keys()))
        
        # 准备数据
        values1 = [counts1[category].get(k, 0) for k in keywords]
        values2 = [counts2[category].get(k, 0) for k in keywords]
        
        # 设置条形图
        x = np.arange(len(keywords))
        width = 0.35
        
        plt.bar(x - width/2, values1, width, label=label1)
        plt.bar(x + width/2, values2, width, label=label2)
        
        plt.xlabel('关键词')
        plt.ylabel('出现次数')
        plt.title(f'{category}关键词对比')
        plt.xticks(x, keywords, rotation=45)
        plt.legend()
        
        # 保存图片
        plt.tight_layout()
        plt.savefig(f'output/{category}_comparison.png')
        plt.close()

def save_results(results, filename=None):
    """保存分析结果"""
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 生成文件名
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'analysis_results_{timestamp}.json'
    
    # 保存结果
    output_path = os.path.join('output', filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到: {output_path}")

def main():
    """主函数"""
    print("开始文本分析...")
    
    # 连接数据库
    try:
        conn = sqlite3.connect('bond_data.db')
        print("成功连接到数据库")
    except Exception as e:
        print(f"连接数据库失败: {e}")
        return
    
    try:
        # 获取数据
        cursor = conn.cursor()
        
        # 获取转型城投数据
        cursor.execute("SELECT 原文 FROM 转型城投")
        transform_texts = [row[0] for row in cursor.fetchall() if row[0]]
        print(f"\n获取到转型城投文本 {len(transform_texts)} 条")
        
        # 获取普通城投数据
        cursor.execute("SELECT 原文 FROM 普通城投")
        normal_texts = [row[0] for row in cursor.fetchall() if row[0]]
        print(f"获取到普通城投文本 {len(normal_texts)} 条")
        
        # 分析转型城投文本
        print("\n=== 分析转型城投文本 ===")
        transform_counts = analyze_texts(transform_texts)
        transform_clusters, transform_keywords = cluster_texts(transform_texts)
        
        # 分析普通城投文本
        print("\n=== 分析普通城投文本 ===")
        normal_counts = analyze_texts(normal_texts)
        normal_clusters, normal_keywords = cluster_texts(normal_texts)
        
        # 生成对比图
        plot_keyword_comparison(transform_counts, normal_counts, "转型城投", "普通城投")
        
        # 保存结果
        save_results({
            'transform': {
                'counts': transform_counts,
                'clusters': transform_keywords
            },
            'normal': {
                'counts': normal_counts,
                'clusters': normal_keywords
            }
        })
        
    except Exception as e:
        print(f"分析过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n分析完成")

if __name__ == "__main__":
    main() 