"""内容分析模块"""
import re
from typing import List, Dict, Any, Tuple
import jieba
import jieba.analyse
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim import corpora, models
import numpy as np
from datetime import datetime
from utils.log_manager import log_manager

logger = log_manager.get_logger('content_analyzer')

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self):
        """初始化"""
        # 加载停用词
        self.stopwords = self._load_stopwords()
        
        # 初始化分词器
        jieba.initialize()
        
        # 初始化TF-IDF分析器
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3)
        )
        
        # 初始化主题模型
        self.lda_model = None
        self.dictionary = None
        
    def _load_stopwords(self) -> set:
        """加载停用词"""
        try:
            stopwords = set()
            # 添加常用停用词
            common_stopwords = {'的', '了', '和', '是', '就', '都', '也', '及', '与', '这', '有', '之', '在'}
            stopwords.update(common_stopwords)
            return stopwords
        except Exception as e:
            logger.error(f"加载停用词失败: {str(e)}")
            return set()
            
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """分析文本内容
        
        Args:
            text: 待分析文本
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # 基础文本统计
            basic_stats = self._get_basic_stats(text)
            
            # 关键词提取
            keywords = self._extract_keywords(text)
            
            # 命名实体识别
            entities = self._extract_entities(text)
            
            # 情感分析
            sentiment = self._analyze_sentiment(text)
            
            # 主题分析
            topics = self._analyze_topics(text)
            
            # 时间信息提取
            time_info = self._extract_time_info(text)
            
            # 数值信息提取
            numerical_info = self._extract_numerical_info(text)
            
            return {
                'basic_stats': basic_stats,
                'keywords': keywords,
                'entities': entities,
                'sentiment': sentiment,
                'topics': topics,
                'time_info': time_info,
                'numerical_info': numerical_info,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分析文本失败: {str(e)}")
            return {}
            
    def _get_basic_stats(self, text: str) -> Dict[str, Any]:
        """获取基础文本统计
        
        Args:
            text: 文本
            
        Returns:
            Dict[str, Any]: 统计结果
        """
        try:
            # 分词
            words = [w for w in jieba.cut(text) if w not in self.stopwords]
            
            # 统计词频
            word_freq = Counter(words)
            
            return {
                'char_count': len(text),
                'word_count': len(words),
                'unique_word_count': len(set(words)),
                'top_words': dict(word_freq.most_common(20))
            }
            
        except Exception as e:
            logger.error(f"获取基础统计失败: {str(e)}")
            return {}
            
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """提取关键词
        
        Args:
            text: 文本
            top_k: 返回关键词数量
            
        Returns:
            List[Tuple[str, float]]: 关键词及其权重
        """
        try:
            # 使用TextRank算法提取关键词
            textrank_keywords = jieba.analyse.textrank(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('ns', 'n', 'vn', 'v')
            )
            
            # 使用TF-IDF算法提取关键词
            tfidf_keywords = jieba.analyse.extract_tags(
                text,
                topK=top_k,
                withWeight=True,
                allowPOS=('ns', 'n', 'vn', 'v')
            )
            
            # 合并结果
            keywords = {}
            for word, weight in textrank_keywords:
                keywords[word] = weight
            for word, weight in tfidf_keywords:
                if word in keywords:
                    keywords[word] = (keywords[word] + weight) / 2
                else:
                    keywords[word] = weight
                    
            # 排序
            return sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:top_k]
            
        except Exception as e:
            logger.error(f"提取关键词失败: {str(e)}")
            return []
            
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取命名实体
        
        Args:
            text: 文本
            
        Returns:
            Dict[str, List[str]]: 实体分类结果
        """
        try:
            entities = {
                'location': [],    # 地点
                'organization': [], # 组织机构
                'person': [],      # 人名
                'time': [],        # 时间
                'number': []       # 数字
            }
            
            # 使用正则表达式提取
            # 地点
            locations = re.findall(r'[省市区县乡镇村]', text)
            entities['location'].extend(locations)
            
            # 组织机构
            orgs = re.findall(r'[局厅处委办署]', text)
            entities['organization'].extend(orgs)
            
            # 时间
            times = re.findall(r'\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}', text)
            entities['time'].extend(times)
            
            # 数字
            numbers = re.findall(r'\d+\.?\d*[万亿元]', text)
            entities['number'].extend(numbers)
            
            return entities
            
        except Exception as e:
            logger.error(f"提取命名实体失败: {str(e)}")
            return {}
            
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """情感分析
        
        Args:
            text: 文本
            
        Returns:
            Dict[str, float]: 情感分析结果
        """
        try:
            # 简单规则基础的情感分析
            positive_words = {'支持', '鼓励', '促进', '优化', '提高', '加强', '创新'}
            negative_words = {'限制', '禁止', '暂停', '取消', '停止', '降低', '减少'}
            
            words = set(jieba.cut(text))
            
            positive_count = len(words & positive_words)
            negative_count = len(words & negative_words)
            total_count = len(words)
            
            if total_count == 0:
                return {'positive': 0, 'negative': 0, 'neutral': 1}
                
            positive_score = positive_count / total_count
            negative_score = negative_count / total_count
            neutral_score = 1 - positive_score - negative_score
            
            return {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            }
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return {}
            
    def _analyze_topics(self, text: str, num_topics: int = 5) -> List[Tuple[int, List[Tuple[str, float]]]]:
        """主题分析
        
        Args:
            text: 文本
            num_topics: 主题数量
            
        Returns:
            List[Tuple[int, List[Tuple[str, float]]]]: 主题及其关键词
        """
        try:
            # 分词
            words = [w for w in jieba.cut(text) if w not in self.stopwords]
            
            # 创建字典
            if not self.dictionary:
                self.dictionary = corpora.Dictionary([words])
            else:
                self.dictionary.add_documents([words])
                
            # 创建语料库
            corpus = [self.dictionary.doc2bow(words)]
            
            # 训练LDA模型
            if not self.lda_model:
                self.lda_model = models.LdaModel(
                    corpus,
                    num_topics=num_topics,
                    id2word=self.dictionary
                )
            
            # 获取主题
            topics = []
            for topic_id in range(num_topics):
                topic_words = self.lda_model.show_topic(topic_id)
                topics.append((topic_id, topic_words))
                
            return topics
            
        except Exception as e:
            logger.error(f"主题分析失败: {str(e)}")
            return []
            
    def _extract_time_info(self, text: str) -> List[Dict[str, Any]]:
        """提取时间信息
        
        Args:
            text: 文本
            
        Returns:
            List[Dict[str, Any]]: 时间信息列表
        """
        try:
            time_patterns = [
                (r'\d{4}年\d{1,2}月\d{1,2}日', 'date'),
                (r'\d{4}年\d{1,2}月', 'month'),
                (r'\d{4}年', 'year'),
                (r'\d{1,2}月\d{1,2}日', 'month_day'),
                (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'date'),
                (r'(\d{4})/(\d{1,2})/(\d{1,2})', 'date')
            ]
            
            time_info = []
            for pattern, time_type in time_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    time_info.append({
                        'text': match.group(),
                        'type': time_type,
                        'start': match.start(),
                        'end': match.end()
                    })
                    
            return sorted(time_info, key=lambda x: x['start'])
            
        except Exception as e:
            logger.error(f"提取时间信息失败: {str(e)}")
            return []
            
    def _extract_numerical_info(self, text: str) -> List[Dict[str, Any]]:
        """提取数值信息
        
        Args:
            text: 文本
            
        Returns:
            List[Dict[str, Any]]: 数值信息列表
        """
        try:
            number_patterns = [
                (r'\d+\.?\d*[万亿元]', 'money'),
                (r'\d+\.?\d*[%％]', 'percentage'),
                (r'\d+\.?\d*[平方]?[米千克吨]', 'measurement')
            ]
            
            numerical_info = []
            for pattern, num_type in number_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    numerical_info.append({
                        'text': match.group(),
                        'type': num_type,
                        'start': match.start(),
                        'end': match.end()
                    })
                    
            return sorted(numerical_info, key=lambda x: x['start'])
            
        except Exception as e:
            logger.error(f"提取数值信息失败: {str(e)}")
            return []
            
    def update_models(self, texts: List[str]):
        """更新模型
        
        Args:
            texts: 文本列表
        """
        try:
            # 更新TF-IDF模型
            self.tfidf.fit(texts)
            
            # 更新主题模型
            words_list = [
                [w for w in jieba.cut(text) if w not in self.stopwords]
                for text in texts
            ]
            
            self.dictionary = corpora.Dictionary(words_list)
            corpus = [self.dictionary.doc2bow(words) for words in words_list]
            
            self.lda_model = models.LdaModel(
                corpus,
                num_topics=5,
                id2word=self.dictionary
            )
            
            logger.info("模型更新成功")
            
        except Exception as e:
            logger.error(f"更新模型失败: {str(e)}")
            
    def export_analysis(self, analysis_results: List[Dict[str, Any]], 
                       format: str = 'json') -> str:
        """导出分析结果
        
        Args:
            analysis_results: 分析结果列表
            format: 导出格式 (json/csv)
            
        Returns:
            str: 导出文件路径
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format == 'json':
                import json
                filename = f'analysis_results_{timestamp}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(analysis_results, f, ensure_ascii=False, indent=2)
                    
            elif format == 'csv':
                import csv
                filename = f'analysis_results_{timestamp}.csv'
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=analysis_results[0].keys())
                    writer.writeheader()
                    writer.writerows(analysis_results)
                    
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
            return filename
            
        except Exception as e:
            logger.error(f"导出分析结果失败: {str(e)}")
            return '' 