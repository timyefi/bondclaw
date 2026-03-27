"""网站分析模块"""
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional

from bs4 import BeautifulSoup
import jieba
import jieba.analyse
from playwright.async_api import Page
from sklearn.feature_extraction.text import TfidfVectorizer

from configs.settings import settings
from models.enums import DictionaryType
from utils.log_manager import log_manager
from utils.helpers import normalize_url, extract_text

from .website_manager import WebsiteManager

# 获取分析器日志器
logger = log_manager.get_logger('analyzer')

class SiteAnalyzer:
    """网站分析器"""
    
    def __init__(
        self,
        db_manager,
        browser_config: Dict = None,
        page_load_config: Dict = None,
        performance_config: Dict = None
    ):
        """初始化网站分析器
        
        Args:
            db_manager: 数据库管理器
            browser_config: 浏览器配置
            page_load_config: 页面加载配置
            performance_config: 性能配置
        """
        # 设置数据库管理器
        self.db_manager = db_manager
        
        # 初始化网站管理器
        self.website_manager = WebsiteManager(db_manager=db_manager)
        
        # 初始化配置
        self.browser_config = browser_config or settings.CRAWLER_CONFIG['playwright']
        self.page_load_config = page_load_config or settings.PAGE_LOAD_CONFIG
        self.perf_config = performance_config or settings.PERFORMANCE_CONFIG
        
        # 初始化特征缓存
        self._content_features = {
            'title_patterns': {},
            'meta_patterns': {},
            'text_patterns': {},
            'last_update': datetime.now()
        }
        
        # 初始化缓存
        self._content_cache = {}
        self._selector_cache = {}
        self._word_cache = {}
        self._stopwords = set()
        self._last_cache_cleanup = datetime.now()
        
        # 初始化组件
        self.vectorizer = None
        
    async def initialize(self):
        """初始化分析器"""
        try:
            # 加载特征
            await self._load_content_features()
            
            # 初始化jieba分词器
            jieba.initialize()
            
            # 加载停用词
            self._stopwords = await self._get_stopwords()
            
            # 初始化TF-IDF向量化器
            self.vectorizer = TfidfVectorizer(
                tokenizer=self._tokenize_text,
                stop_words=self._stopwords
            )
            
            logger.info("网站分析器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化网站分析器失败: {str(e)}")
            raise
            
    async def _load_content_features(self):
        """从数据库加载特征"""
        try:
            # 加载URL模式特征
            url_patterns = await self.website_manager.get_active_features('url_pattern')
            self._content_features['url_patterns'] = self._group_features_by_category(url_patterns)
            
            # 加载域名模式特征
            domain_patterns = await self.website_manager.get_active_features('domain_pattern')
            self._content_features['domain_patterns'] = self._group_features_by_category(domain_patterns)
            
            # 加载栏目模式特征
            section_patterns = await self.website_manager.get_active_features('section_pattern')
            self._content_features['section_patterns'] = self._group_features_by_category(section_patterns)
            
            # 更新缓存时间
            self._content_features['last_update'] = datetime.now()
            
            logger.info("内容特征加载完成")
            
        except Exception as e:
            logger.error(f"加载内容特征失败: {str(e)}")
            
    def _group_features_by_category(self, features: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """按类别分组特征"""
        grouped = {}
        for feature in features:
            category = feature['feature_category']
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(feature['feature_value'])
        return grouped
        
    async def analyze_site(self, page: Page) -> Dict[str, Any]:
        """分析网站页面"""
        try:
            # 获取页面URL
            url = page.url
            normalized_url = normalize_url(url)
            
            # 检查缓存
            if settings.CACHE_CONFIG['enabled']:
                cache_key = f"analysis_{normalized_url}"
                if cache_key in self._content_cache:
                    return self._content_cache[cache_key]
            
            # 获取页面内容
            content = await self._get_page_content(page)
            
            # 提取基本信息
            info = await self._extract_basic_info(page)
            
            # 分析页面性能
            performance = await self._analyze_performance(page)
            
            # 分析页面内容
            content_analysis = await self._analyze_content(content)
            
            # 分析页面结构
            structure = await self._analyze_structure(page)
            
            # 组合分析结果
            result = {
                'url': normalized_url,
                'title': info.get('title', ''),
                'description': info.get('description', ''),
                'keywords': info.get('keywords', []),
                'language': info.get('language', 'zh-CN'),
                'encoding': info.get('encoding', 'utf-8'),
                'content_type': info.get('content_type', 'text/html'),
                'performance': performance,
                'content_analysis': content_analysis,
                'structure': structure,
                'analyzed_at': datetime.now().isoformat()
            }
            
            # 更新缓存
            if settings.CACHE_CONFIG['enabled']:
                self._content_cache[cache_key] = result
                
            return result
            
        except Exception as e:
            logger.error(f"网站分析失败 [{url}]: {str(e)}")
            return None
            
    async def _get_page_content(self, page: Page) -> str:
        """获取页面内容"""
        try:
            # 获取HTML内容
            content = await page.content()
            
            # 解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 移除不需要的标签
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe']):
                tag.decompose()
                
            return str(soup)
            
        except Exception as e:
            logger.error(f"获取页面内容失败: {str(e)}")
            return ""
            
    async def _extract_basic_info(self, page: Page) -> Dict[str, Any]:
        """提取基本信息"""
        try:
            # 获取页面内容
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取标题
            title = soup.title.string if soup.title else ""
            
            # 提取元信息
            meta = {}
            for tag in soup.find_all('meta'):
                name = tag.get('name', '').lower()
                content = tag.get('content', '')
                if name and content:
                    meta[name] = content
                    
            # 提取关键词
            keywords = []
            if 'keywords' in meta:
                keywords = [k.strip() for k in meta['keywords'].split(',')]
                
            return {
                'title': title,
                'description': meta.get('description', ''),
                'keywords': keywords,
                'language': meta.get('language', 'zh-CN'),
                'encoding': meta.get('charset', 'utf-8'),
                'content_type': meta.get('content-type', 'text/html')
            }
            
        except Exception as e:
            logger.error(f"提取基本信息失败: {str(e)}")
            return {}
            
    async def _analyze_performance(self, page: Page) -> Dict[str, Any]:
        """分析页面性能"""
        try:
            # 获取性能指标
            metrics = await page.evaluate('''() => {
                const performance = window.performance;
                const timing = performance.timing;
                return {
                    loadTime: timing.loadEventEnd - timing.navigationStart,
                    domReadyTime: timing.domContentLoadedEventEnd - timing.navigationStart,
                    firstPaintTime: timing.responseStart - timing.navigationStart,
                    resourceCount: performance.getEntriesByType('resource').length
                }
            }''')
            
            return metrics
            
        except Exception as e:
            logger.error(f"分析页面性能失败: {str(e)}")
            return {}
            
    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """分析页面内容"""
        try:
            # 提取文本
            text = extract_text(content)
            
            # 分词
            words = self._tokenize_text(text)
            
            # 计算TF-IDF
            if self.vectorizer and words:
                try:
                    tfidf = self.vectorizer.fit_transform([' '.join(words)])
                    feature_names = self.vectorizer.get_feature_names_out()
                    scores = tfidf.toarray()[0]
                    keywords = [
                        (feature_names[i], scores[i])
                        for i in scores.argsort()[-10:][::-1]
                    ]
                except:
                    keywords = []
            else:
                keywords = []
                
            # 分析文本块
            text_blocks = []
            soup = BeautifulSoup(content, 'html.parser')
            for block in soup.find_all(['p', 'div', 'article']):
                block_text = extract_text(str(block))
                if len(block_text) > 50:  # 忽略太短的文本块
                    text_blocks.append({
                        'text': block_text,
                        'type': block.name,
                        'length': len(block_text)
                    })
                    
            return {
                'text_length': len(text),
                'word_count': len(words),
                'keywords': keywords,
                'text_blocks': text_blocks
            }
            
        except Exception as e:
            logger.error(f"分析页面内容失败: {str(e)}")
            return {}
            
    async def _analyze_structure(self, page: Page) -> Dict[str, Any]:
        """分析页面结构"""
        try:
            # 获取页面内容
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 分析链接
            links = []
            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                if href and not href.startswith(('#', 'javascript:')):
                    links.append({
                        'url': href,
                        'text': a.get_text(strip=True),
                        'title': a.get('title', '')
                    })
                    
            # 分析导航
            nav_elements = []
            for nav in soup.find_all(['nav', 'menu', 'ul']):
                items = []
                for item in nav.find_all(['li', 'a']):
                    text = item.get_text(strip=True)
                    if text:
                        items.append(text)
                if items:
                    nav_elements.append({
                        'type': nav.name,
                        'items': items
                    })
                    
            return {
                'link_count': len(links),
                'links': links[:100],  # 限制链接数量
                'navigation': nav_elements
            }
            
        except Exception as e:
            logger.error(f"分析页面结构失败: {str(e)}")
            return {}
            
    def _tokenize_text(self, text: str) -> List[str]:
        """分词"""
        try:
            # 使用jieba分词
            words = jieba.cut(text)
            
            # 过滤停用词
            words = [w for w in words if w not in self._stopwords]
            
            return words
            
        except Exception as e:
            logger.error(f"分词失败: {str(e)}")
            return []
            
    async def _get_stopwords(self) -> Set[str]:
        """获取停用词"""
        try:
            # 从数据库加载停用词
            stopwords = set()
            if self.db_manager:
                stopwords.update(
                    await self.db_manager.get_dictionary_entries(
                        dict_type=DictionaryType.STOPWORD.value,
                        is_enabled=True
                    )
                )
            return stopwords
            
        except Exception as e:
            logger.error(f"获取停用词失败: {str(e)}")
            return set()
            
    def _cleanup_cache(self):
        """清理过期缓存"""
        if not settings.CACHE_CONFIG['enabled']:
            return
            
        now = datetime.now()
        
        # 清理特征缓存
        if (now - self._content_features['last_update']).seconds > settings.CACHE_CONFIG['expire']:
            if self.db_manager:
                asyncio.create_task(self._load_content_features())
                
        # 清理内容缓存
        if (now - self._last_cache_cleanup).seconds > settings.CACHE_CONFIG['expire']:
            self._content_cache.clear()
            self._selector_cache.clear()
            self._word_cache.clear()
            self._last_cache_cleanup = now