"""页面管理模块"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any, Optional, Tuple
import re
from urllib.parse import urljoin, urlparse
import jieba
import jieba.analyse
from collections import Counter
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import joblib

from bs4 import BeautifulSoup
from playwright.async_api import Page

from models.base.enums import (
    PageType,
    CrawlStatus,
    FeatureType,
    SectionElementType,
    AnalysisType
)
from utils.log_manager import log_manager
from utils.helpers import normalize_url, get_domain
from configs.settings import settings
from services.config.config_manager import ConfigManager

# 获取页面管理器日志器
logger = log_manager.get_logger('page')

# 页面类型特征定义
PAGE_TYPE_FEATURES = {
    PageType.GOV_INFO.value: {
        'title_keywords': [
            '关于', '通知', '意见', '办���', '规定', '条例', '实施', '细则',
            '规划', '方案', '决定', '命令', '公告', '政府信息', '文件'
        ],
        'content_keywords': [
            '各省', '各市', '各县', '各部门', '文号', '特此', '请遵照执行',
            '施行', '执行', '实施', '规定', '要求', '职责', '职权'
        ],
        'url_patterns': [
            r'/zwgk/',
            r'/xxgk/',
            r'/govinfo/',
            r'/zfxxgk/',
            r'/gk/',
            r'/gov-info/'
        ],
        'structure_features': {
            'heading_patterns': [
                r'^第[一二三四五六七八九十]章\s+.+',
                r'^第[一二三四五六七八九十]条\s+.+',
                r'^\d+\.\s+.+',
                r'^[一二三四五六七八九十]、\s+.+'
            ],
            'section_patterns': [
                r'总\s*则',
                r'附\s*则',
                r'第[一二三四五六七八九十]部分',
                r'第[一二三四五六七八九十]节'
            ],
            'format_patterns': [
                r'文号[:：]\s*[\w\d\-]+',
                r'印发日期[:：]\s*\d{4}年\d{1,2}月\d{1,2}日',
                r'实施日期[:：]\s*\d{4}年\d{1,2}月\d{1,2}日'
            ]
        },
        'semantic_features': {
            'document_type': [
                '规定', '办法', '条例', '规则', '细则',
                '通知', '意见', '决定', '命令', '公告'
            ],
            'authority_terms': [
                '根据', '依据', '按照', '遵照', '执行',
                '决定', '规定', '要求', '命令', '批准'
            ],
            'responsibility_terms': [
                '职责', '责任', '权限', '义务', '职权',
                '管理', '监督', '检查', '处罚', '奖励'
            ],
            'implementation_terms': [
                '实施', '执行', '施行', '生效', '废止',
                '试行', '暂行', '修订', '补充', '废除'
            ]
        },
        'temporal_features': {
            'date_patterns': [
                r'\d{4}年\d{1,2}月\d{1,2}日',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'\d{4}/\d{1,2}/\d{1,2}'
            ],
            'period_terms': [
                '即日起', '施行之日起', '公��之日起',
                '有效期', '试行期', '过渡期'
            ],
            'deadline_terms': [
                '截止日期', '截止时间', '期限', '时限',
                '有效期限', '执行期限', '实施期限'
            ]
        },
        'format_features': {
            'document_structure': {
                'header_patterns': [
                    r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼].*?[〔\[（(].*?[）)\]〕]',  # 文件头
                    r'^.*?[省市区县]人民政府',  # 政府机关
                    r'^.*?[厅局处院委办]'  # 部门机关
                ],
                'footer_patterns': [
                    r'抄送[:：].*',  # 抄送
                    r'主题词[:：].*',  # 主题词
                    r'(?:联系|咨询)(?:电话|方式)[:：].*',  # 联系方式
                    r'.*(?:印发|印送|存档)' # 印发说明
                ],
                'layout_patterns': [
                    r'^\s*目\s*录\s*$',  # 目录
                    r'^\s*附\s*件\s*\d*\s*[:：]',  # 附件标记
                    r'^\s*附\s*表\s*\d*\s*[:：]',  # 附表标记
                    r'^\s*附\s*录\s*\d*\s*[:：]'  # 附录标记
                ]
            },
            'text_format': {
                'indent_patterns': [
                    r'^\s{2,}[\u4e00-\u9fa5]',  # 缩进
                    r'^\s*[一二三四五六七八九十]、',  # 中文序号
                    r'^\s*\d+[、.]',  # 数字序号
                    r'^\s*[（(]\d+[)）]'  # 括号序号
                ],
                'list_patterns': [
                    r'^\s*[①②③④⑤⑥⑦⑧⑨⑩]',  # 圆圈数字
                    r'^\s*[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]',  # 括号数字
                    r'^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]',  # 罗马数字
                    r'^\s*[A-Za-z][.、)]'  # 字母序号
                ],
                'emphasis_patterns': [
                    r'【.*?】',  # 方括号强调
                    r'［.*?］',  # 全角方括号强调
                    r'「.*?」',  # 书名号强调
                    r'『.*?』'  # 书名号强调
                ]
            },
            'table_format': {
                'table_patterns': [
                    r'<table.*?>.*?</table>',  # HTML表格
                    r'\|\s*[\u4e00-\u9fa5]+.*\|',  # Markdown表格
                    r'┌.*┐[\s\S]*?└.*┘',  # ASCII表格
                    r'^\s*[\u4e00-\u9fa5]+表\s*\d*\s*[:：]'  # 表格标题
                ]
            }
        },
        'citation_features': {
            'legal_citation': {
                'law_patterns': [
                    r'《.*?(?:法|条例|规定|办法|规则)》',  # 法律法规
                    r'(?:国发|国办发|发改|财建|财金|财税)\[\d{4}\]\d+号',  # 文号引用
                    r'(?:根据|依据|按照).*?(?:规定|要求|精神)',  # 依据引用
                    r'(?:《|〈).*?(?:》|〉)'  # 文件引用
                ],
                'quote_patterns': [
                    r'".*?"',  # 引号引用
                    r'".*?"',  # 全角引号引用
                    r'「.*?」',  # 书名号引用
                    r'『.*?』'  # 书名号引用
                ]
            },
            'document_citation': {
                'doc_patterns': [
                    r'(?:国务院|.*?部|.*?局|.*?厅|.*?委员会).*?[〔\[（(].*?[）)\]〕]',  # 机关文件
                    r'(?:发文|来文|原文)(?:文号|编号)[:：].*?号',  # 文号引用
                    r'(?:见|参见|详见).*?(?:文|通知|公告)',  # 参见引用
                    r'(?:附件|附表|附录)\d*[:：]'  # 附件引用
                ]
            },
            'reference_citation': {
                'ref_patterns': [
                    r'注[:：].*',  # 注释引��
                    r'备注[:：].*',  # 备注引用
                    r'说明[:：].*',  # 说明引用
                    r'(?:相关|参考)(?:文件|资料)[:：].*'  # 参考引用
                ]
            }
        },
        'attachment_features': {
            'file_attachments': {
                'doc_patterns': [
                    r'href=[\'"].*?\.(?:doc|docx)[\'"]',  # Word文档
                    r'href=[\'"].*?\.(?:xls|xlsx)[\'"]',  # Excel文档
                    r'href=[\'"].*?\.pdf[\'"]',  # PDF文档
                    r'href=[\'"].*?\.(?:zip|rar|7z)[\'"]'  # 压缩包
                ],
                'link_patterns': [
                    r'(?:附件下载|文件下载|下载附件).*?href=[\'"].*?[\'"]',  # 下载链接
                    r'(?:点击下载|查看原文).*?href=[\'"].*?[\'"]',  # 查看链接
                    r'(?:全文下载|原文下载).*?href=[\'"].*?[\'"]',  # 全文链接
                    r'(?:相关下载|资料下载).*?href=[\'"].*?[\'"]'  # 资料链接
                ]
            },
            'attachment_description': {
                'title_patterns': [
                    r'附件\d*[:：].*?(?:\n|$)',  # 附件标题
                    r'附表\d*[:：].*?(?:\n|$)',  # 附表标题
                    r'附���\d*[:：].*?(?:\n|$)',  # 附录标题
                    r'(?:相关|参考)(?:资料|文件)[:：].*?(?:\n|$)'  # 相关资料
                ],
                'size_patterns': [
                    r'\(\d+(?:KB|MB|GB)\)',  # 文件大小
                    r'（\d+(?:KB|MB|GB)）',  # 全角文件大小
                    r'\[\d+(?:KB|MB|GB)\]',  # 方括号文件大小
                    r'【\d+(?:KB|MB|GB)】'  # 方括号文件大小
                ]
            },
            'attachment_metadata': {
                'type_patterns': [
                    r'文件格式[:：].*?(?:\n|$)',  # 文件格式
                    r'文件类型[:：].*?(?:\n|$)',  # 文件类型
                    r'格式要求[:：].*?(?:\n|$)',  # 格式要求
                    r'支持格式[:：].*?(?:\n|$)'  # 支持格式
                ],
                'count_patterns': [
                    r'共\d+个附件',  # 附件数量
                    r'附件\(\d+\)',  # 括号数量
                    r'附件（\d+）',  # 全角括号数量
                    r'附件数量[:：]\d+'  # 数量说明
                ]
            }
        },
        'weights': {
            'title': 0.15,
            'content': 0.15,
            'url': 0.10,
            'structure': 0.15,
            'semantic': 0.15,
            'temporal': 0.10,
            'format': 0.10,
            'citation': 0.05,
            'attachment': 0.05
        }
    },
    PageType.NOTICE.value: {
        'title_keywords': [
            '公告', '通告', '通知', '提示', '启事', '公示', '声明',
            '招标', '中标', '采购', '拍卖', '挂牌'
        ],
        'content_keywords': [
            '现将', '特此公告', '公示期', '异议', '联系电话',
            '咨询', '联系人', '办公室', '特此通知'
        ],
        'url_patterns': [
            r'/notice/',
            r'/gonggao/',
            r'/tzgg/',
            r'/gsgg/'
        ],
        'structure_features': {
            'heading_patterns': [
                r'^公告内容[：:]',
                r'^公示事项[：:]',
                r'^[一二三四五六七八九十]、',
                r'^\d+[、.]'
            ],
            'section_patterns': [
                r'公告内容',
                r'公示事项',
                r'联系方式',
                r'注意事项'
            ],
            'format_patterns': [
                r'公告编号[:：]\s*[\w\d\-]+',
                r'公示期[:：]\s*\d+天',
                r'联系电话[:：]\s*\d{3,4}[-－]\d{7,8}'
            ]
        },
        'semantic_features': {
            'document_type': [
                '公告', '通告', '通知', '公示', '启事',
                '声明', '说明', '提示', '告知'
            ],
            'action_terms': [
                '发布', '公布', '宣布', '通知', '告知',
                '提示', '说明', '声明', '理清'
            ],
            'scope_terms': [
                '全体', '相关', '有关', '所有', '各位',
                '广大', '社会', '公众', '市民'
            ],
            'response_terms': [
                '反馈', '意见', '建议', '异议', '投诉',
                '咨询', '联系', '回复', '答复'
            ]
        },
        'temporal_features': {
            'date_patterns': [
                r'\d{4}年\d{1,2}月\d{1,2}日',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'\d{4}/\d{1,2}/\d{1,2}'
            ],
            'period_terms': [
                '公示期', '公示期', '有效期', '截止日期',
                '公告期限', '公示时间', '受理时间'
            ],
            'schedule_terms': [
                '工作日', '上午', '下午', '时间段',
                '工作时间', '办公时间', '受理时间'
            ]
        },
        'weights': {
            'title': 0.25,
            'content': 0.20,
            'url': 0.10,
            'structure': 0.15,
            'semantic': 0.20,
            'temporal': 0.10
        }
    },
    PageType.NEWS.value: {
        'title_keywords': [
            '新闻', '动态', '资讯', '快讯', '播报', '要闻', '聚焦',
            '专题', '报道', '条', '发布'
        ],
        'content_keywords': [
            '记者', '报道', '采访', '表示', '介绍', '新闻', '发布会',
            '举行', '召开', '活动', '会议'
        ],
        'url_patterns': [
            r'/news/',
            r'/xinwen/',
            r'/dongtai/',
            r'/zixun/'
        ],
        'weights': {
            'title': 0.4,
            'content': 0.3,
            'url': 0.2,
            'context': 0.1
        }
    },
    PageType.GUIDE.value: {
        'title_keywords': [
            '指南', '指引', '流程', '手册', '攻略', '须知', '说明',
            '办事', '服务', '咨询', '问答', '解答'
        ],
        'content_keywords': [
            '步骤', '流程', '材料', '清单', '注意事项', '办理', '申请',
            '咨询', '电话', '窗口', '时间', '地点'
        ],
        'url_patterns': [
            r'/guide/',
            r'/service/',
            r'/bszn/',
            r'/fwzn/'
        ],
        'weights': {
            'title': 0.4,
            'content': 0.3,
            'url': 0.2,
            'context': 0.1
        }
    }
}

# URL模式映射
url_patterns = {
    PageType.GOV_INFO.value: {
        "patterns": [
            r'/zwgk/',          # 政务公开
            r'/xxgk/',          # 信息公开
            r'/govinfo/',       # 政府信息
            r'/zfxxgk/',        # 政府信息公开
            r'/gk/',            # 公开
            r'/gov-info/'       # 政府信息(英文)
        ],
        "weight": 1.0
    },
    # ... 其他页面类型的模式
}

class PageManager:
    """页面管理器"""
    
    def __init__(self, db_manager=None):
        """初始化页面管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        self.config_manager = ConfigManager()
        
        # 从配置管理器获取配置
        page_config = self.config_manager.get('page_manager', {})
        feature_config = self.config_manager.get('features', {})
        
        # 特征使用统计
        self.feature_usage_stats = {}
        self.last_training_time = None
        
        # 从配置获取参数
        self.min_training_samples = feature_config.get('min_training_samples', 100)
        self.min_feature_importance = feature_config.get('min_importance', 0.01)
        self.feature_expiry_days = feature_config.get('expiry_days', 30)
        
        self.playwright = None
        self.browser = None
        self.context = None
        
        # 初始化缓存
        self._page_cache = {}
        self._feature_cache = {}
        self._last_cache_cleanup = datetime.now()
        
        # 设置缓存清理间隔
        self._cache_cleanup_interval = timedelta(minutes=30)
        
        # 设置重试参数
        self._max_retries = settings.CRAWLER_CONFIG.get('max_retry_count', 3)
        self._retry_delay = settings.CRAWLER_CONFIG.get('retry_delay', 1)
        
        # 设置并发限制
        self._max_concurrent_pages = settings.CRAWLER_CONFIG.get('max_concurrent_pages', 5)
        self._page_semaphore = asyncio.Semaphore(self._max_concurrent_pages)
        
        # 初始化jieba分词
        for page_type, features in PAGE_TYPE_FEATURES.items():
            for keyword in features['title_keywords'] + features['content_keywords']:
                jieba.add_word(keyword)
                
        # 机器学习相关
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            analyzer='char_wb'
        )
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.label_encoder = LabelEncoder()
        self.feature_importance = {}
        self.feature_usage_stats = {}
        self.last_training_time = None
        self.min_training_samples = 100
        self.min_feature_importance = 0.01
        self.feature_expiry_days = 30
        
    async def initialize(self):
        """初始化管理器"""
        try:
            # 加载特征使用统计
            await self._load_feature_stats()
            
            logger.info("页面管理器初始化完成")
            
        except Exception as e:
            logger.error(f"页面管理器初始化失败: {str(e)}")
            raise
            
    async def _load_feature_stats(self):
        """加载特征使用统计"""
        if not self.db_manager:
            return
            
        try:
            # 从数据库加载统计数据
            stats = await self.db_manager.fetch_all(
                "SELECT * FROM feature_stats"
            )
            
            for stat in stats:
                self.feature_usage_stats[stat['feature_id']] = {
                    'hit_count': stat['hit_count'],
                    'miss_count': stat['miss_count'],
                    'last_used': stat['last_used'],
                    'importance': stat['importance']
                }
                
        except Exception as e:
            logger.error(f"加载特征统计失败: {str(e)}")
            
    async def _load_features(self):
        """加载特征"""
        try:
            # 获取所有活跃特征
            features = await self.db_manager.get_active_page_features()
            
            # 按类型分组
            self._feature_cache = {}
            for feature in features:
                feature_type = feature['feature_type']
                if feature_type not in self._feature_cache:
                    self._feature_cache[feature_type] = []
                self._feature_cache[feature_type].append(feature)
                
            logger.info("特征加载完成")
            
        except Exception as e:
            logger.error(f"加载特征失败: {str(e)}")
            
    async def _load_sections(self):
        """加载区块定义"""
        try:
            # 获取所有活跃区块定义
            sections = await self.db_manager.get_active_page_sections()
            
            # 按类型分组
            self._section_cache = {}
            for section in sections:
                section_type = section['section_type']
                if section_type not in self._section_cache:
                    self._section_cache[section_type] = []
                self._section_cache[section_type].append(section)
                
            logger.info("区块定义加载完成")
            
        except Exception as e:
            logger.error(f"加载区块定义失败: {str(e)}")
            
    async def add_content_page(self, site_id: int, url: str, page_type: str = None) -> Optional[int]:
        """添加内容页面
        
        Args:
            site_id: 网站ID
            url: 页面URL
            page_type: 页面类型
            
        Returns:
            Optional[int]: 页面ID
        """
        try:
            # 规范化URL
            url = normalize_url(url)
            
            # 检查是否已存在
            existing = await self.db_manager.get_content_page_by_url(url)
            if existing:
                return existing['id']
                
            # 准备页面数据
            page_data = {
                'site_id': site_id,
                'url': url,
                'page_type': page_type or PageType.UNKNOWN.value,
                'status': 'pending',
                'crawl_status': CrawlStatus.PENDING.value,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 保存到数据库
            page_id = await self.db_manager.add_content_page(page_data)
            
            return page_id
            
        except Exception as e:
            logger.error(f"添加内容页面失败 [{url}]: {str(e)}")
            return None
            
    async def get_next_pages(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """获取下一批待处理的页面
        
        Args:
            batch_size: 批次大小
            
        Returns:
            List[Dict[str, Any]]: 页面列表
        """
        try:
            sql = """
                SELECT * FROM content_pages 
                WHERE status = 'pending' 
                AND is_active = 1
                LIMIT %s
            """
            
            return await self.db_manager.fetch_all(sql, (batch_size,))
            
        except Exception as e:
            logger.error(f"获取待处理页面失败: {str(e)}")
            return []
            
    async def process_page(self, page_id: int, content: str) -> bool:
        """处理页面内容
        
        Args:
            page_id: 页面ID
            content: 页内容
            
        Returns:
            bool: 是否成功
        """
        try:
            # 更新状态为处理中
            await self._update_page_status(
                page_id,
                CrawlStatus.RUNNING
            )
            
            # 解析页面
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取标题
            title = await self._extract_title(soup)
            
            # 提取页面类型
            page_type = await self._detect_page_type(soup, title)
            
            # 提取区块内容
            sections = await self._extract_sections(soup)
            
            # 分析页面
            analysis = await self._analyze_page(soup)
            
            # 保存结果
            success = await self._save_page_result(
                page_id=page_id,
                title=title,
                page_type=page_type,
                sections=sections,
                analysis=analysis
            )
            
            # 更新状态
            status = CrawlStatus.SUCCESS if success else CrawlStatus.FAILED
            await self._update_page_status(page_id, status)
            
            return success
            
        except Exception as e:
            logger.error(f"处理页面失败 [page_id={page_id}]: {str(e)}")
            await self._update_page_status(
                page_id,
                CrawlStatus.FAILED,
                str(e)
            )
            return False
            
    async def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Optional[str]: 标题
        """
        try:
            # 获取标题特征
            title_features = self._feature_cache.get(FeatureType.TITLE.value, [])
            
            # 按置信度排序
            title_features.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 尝试每个特征
            for feature in title_features:
                try:
                    # 使用选择器提取
                    elements = soup.select(feature['feature_value'])
                    if elements:
                        title = elements[0].get_text(strip=True)
                        if title:
                            # 更新特征统计
                            await self._update_feature_stats(
                                feature['id'],
                                True
                            )
                            return title
                except:
                    continue
                    
            # 使用默认选择器
            for selector in ['h1', 'title']:
                elements = soup.select(selector)
                if elements:
                    title = elements[0].get_text(strip=True)
                    if title:
                        return title
                        
            return None
            
        except Exception as e:
            logger.error(f"提取标题失败: {str(e)}")
            return None
            
    async def _detect_page_type(self, soup: BeautifulSoup, title: str = None) -> str:
        """检测页面类型"""
        try:
            # 提取文本特征
            content = soup.get_text()
            url = soup.get('url', '')
            
            # 使用机器学习模型预测
            if self.classifier is not None and len(self.feature_importance) > 0:
                prediction = await self._predict_page_type(title, content, url)
                if prediction and prediction != PageType.UNKNOWN.value:
                    return prediction
                    
            # 如果机器学习预测失败,使用规则based方法
            return await self._rule_based_detection(title, content, url)
            
        except Exception as e:
            logger.error(f"检测页面类型失败: {str(e)}")
            return PageType.UNKNOWN.value
            
    async def _predict_page_type(self, title: str, content: str, url: str) -> Optional[str]:
        """使用机器学习模型预测页面类型"""
        try:
            # 合并文本特征
            text = f"{title}\n{content}\n{url}"
            
            # 转换特征
            X = self.vectorizer.transform([text])
            
            # 预测
            prediction = self.classifier.predict(X)
            
            # 解码预测结果
            page_type = self.label_encoder.inverse_transform(prediction)[0]
            
            # 获取预测概率
            proba = self.classifier.predict_proba(X)[0]
            max_proba = max(proba)
            
            # 只有当预测概率超过阈值时才返回预测结果
            if max_proba >= settings.CONTENT_CONFIG['ml_confidence_threshold']:
                return page_type
                
            return None
            
        except Exception as e:
            logger.error(f"预测页面类型失败: {str(e)}")
            return None
            
    async def learn_from_success(self, page_id: int, success_data: Dict[str, Any]):
        """从成功案例学习"""
        try:
            # 获取页面类型
            page_type = success_data.get('page_type')
            if not page_type or page_type not in PAGE_TYPE_FEATURES:
                return
                
            features = PAGE_TYPE_FEATURES[page_type]
            title = success_data.get('title', '')
            content = success_data.get('content', '')
            
            if not content:
                return
                
            # 提取新的结构特征
            self._learn_structure_features(content, features['structure_features'])
            
            # 提取新的语义特征
            self._learn_semantic_features(title, content, features['semantic_features'])
            
            # 提取新的时间特征
            self._learn_temporal_features(content, features['temporal_features'])
            
            # 学习新的格式特征
            self._learn_format_features(content, features['format_features'])
            
            # 学习新的引用特征
            self._learn_citation_features(content, features['citation_features'])
            
            # 学习新的附件特征
            self._learn_attachment_features(content, features['attachment_features'])
            
            # 更新权重
            self._update_weights(page_type, success_data)
            
            # 更新特征统计
            await self._update_feature_stats(page_id, success_data, True)
            
            # 收集训练数据
            await self._collect_training_data(success_data)
            
            # 定期重新训练模型
            await self._retrain_model_if_needed()
            
            logger.info(f"从成功案例学习完成 [page_id={page_id}]")
            
        except Exception as e:
            logger.error(f"学习失败 [page_id={page_id}]: {str(e)}")
            
    def _learn_structure_features(
        self,
        content: str,
        features: Dict[str, List[str]]
    ):
        """学习结构特征"""
        try:
            # 提取段落标题
            headings = re.findall(r'^\s*(.+?)\s*(?:：|:|\n)', content, re.M)
            for heading in headings:
                if len(heading) > 2 and heading not in features['heading_patterns']:
                    pattern = re.escape(heading).replace(r'\ ', r'\s*')
                    features['heading_patterns'].append(f'^{pattern}')
                    
            # 提取章节标记
            sections = re.findall(r'^\s*第[一二三四五六七八九十]\s*([节章节])\s*(.+?)\s*$', content, re.M)
            for _, section in sections:
                if section not in features['section_patterns']:
                    features['section_patterns'].append(section)
                    
        except Exception as e:
            logger.error(f"学习结构特征失败: {str(e)}")
            
    def _learn_semantic_features(
        self,
        title: str,
        content: str,
        features: Dict[str, List[str]]
    ):
        """学习语义特征"""
        try:
            # 合并标题和内容
            text = f"{title}\n{content}" if title else content
            
            # 提取关键词
            keywords = jieba.analyse.extract_tags(
                text,
                topK=20,
                withWeight=True
            )
            
            # 按词性分类新关键词
            for keyword, weight in keywords:
                if weight > 0.5:
                    word_type = self._classify_word_type(keyword)
                    if word_type in features:
                        if keyword not in features[word_type]:
                            features[word_type].append(keyword)
                            
        except Exception as e:
            logger.error(f"学习语义特征失败: {str(e)}")
            
    def _learn_temporal_features(
        self,
        content: str,
        features: Dict[str, List[str]]
    ):
        """学习时间特征"""
        try:
            # 提取时间表达式
            time_exprs = re.findall(r'[自从即日]\s*[起至到]\s*\d+\s*[年月日]', content)
            for expr in time_exprs:
                if expr not in features['period_terms']:
                    features['period_terms'].append(expr)
                    
            # 提取截止时间表达式
            deadline_exprs = re.findall(r'截[止至到]\s*\d+\s*[年月日]', content)
            for expr in deadline_exprs:
                if expr not in features['deadline_terms']:
                    features['deadline_terms'].append(expr)
                    
        except Exception as e:
            logger.error(f"学习时间特征失败: {str(e)}")
            
    def _classify_word_type(self, word: str) -> Optional[str]:
        """分类词语类型"""
        try:
            # 使用词性标注
            import jieba.posseg as pseg
            words = pseg.cut(word)
            for w, flag in words:
                if flag.startswith('v'):  # 动词
                    return 'action_terms'
                elif flag.startswith('n'):  # 名词
                    return 'document_type'
                elif flag.startswith('t'):  # 时间词
                    return 'temporal_terms'
            return None
            
        except Exception as e:
            logger.error(f"分类词语类型失败: {str(e)}")
            return None
            
    async def learn_from_failure(self, page_id: int, error_data: Dict[str, Any]):
        """从失败案例学习
        
        Args:
            page_id: 页面ID
            error_data: 错误数据
        """
        try:
            # 降低失败特征的置信度
            await self._decrease_feature_confidence(page_id, error_data)
            
            # 降低失败区块的置信度
            await self._decrease_section_confidence(page_id, error_data)
            
            # 记录失败模式
            await self._record_failure_pattern(page_id, error_data)
            
        except Exception as e:
            logger.error(f"失败学习失败 [page_id={page_id}]: {str(e)}")
            
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理缓存
            self._feature_cache.clear()
            self._section_cache.clear()
            self._analysis_cache.clear()
            
            logger.info("页面管理器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理页面管理器资源失败: {str(e)}")
            
    def _calculate_format_score(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ) -> float:
        """计算文档格式得分"""
        try:
            score = 0.0
            
            if not content:
                return score
                
            # 文档结构得分
            structure_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['document_structure']
            )
            score += structure_score * 0.4
            
            # 文本格式得分
            text_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['text_format']
            )
            score += text_score * 0.4
            
            # 表格格式得分
            table_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['table_format']
            )
            score += table_score * 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"计算文档格式得分失败: {str(e)}")
            return 0.0
            
    def _calculate_citation_score(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ) -> float:
        """计算引用得分"""
        try:
            score = 0.0
            
            if not content:
                return score
                
            # 法律引用得分
            legal_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['legal_citation']
            )
            score += legal_score * 0.4
            
            # 文档引用得分
            doc_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['document_citation']
            )
            score += doc_score * 0.4
            
            # 参考引用得分
            ref_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['reference_citation']
            )
            score += ref_score * 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"计算引用得分失败: {str(e)}")
            return 0.0
            
    def _calculate_attachment_score(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ) -> float:
        """计算附件得分"""
        try:
            score = 0.0
            
            if not content:
                return score
                
            # 文件附件得分
            file_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['file_attachments']
            )
            score += file_score * 0.4
            
            # 附件描述得分
            desc_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['attachment_description']
            )
            score += desc_score * 0.4
            
            # 附件元数据得分
            meta_score = self._calculate_pattern_group_score(
                content=content,
                patterns=features['attachment_metadata']
            )
            score += meta_score * 0.2
            
            return score
            
        except Exception as e:
            logger.error(f"计算附件得分失败: {str(e)}")
            return 0.0
            
    def _calculate_pattern_group_score(
        self,
        content: str,
        patterns: Dict[str, List[str]]
    ) -> float:
        """计算模式组得分"""
        try:
            score = 0.0
            total_patterns = 0
            total_matches = 0
            
            for pattern_list in patterns.values():
                total_patterns += len(pattern_list)
                for pattern in pattern_list:
                    matches = len(re.findall(pattern, content, re.M))
                    total_matches += min(matches, 3)  # 限制单个模式的最大匹配数
                    
            if total_patterns > 0:
                score = total_matches / (total_patterns * 3)  # 归一化得分
                
            return min(score, 1.0)  # 限制最大得分为1.0
            
        except Exception as e:
            logger.error(f"计算模式组得分失败: {str(e)}")
            return 0.0
            
    def _learn_format_features(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ):
        """学习格式特征"""
        try:
            # 提取文档结构
            headers = re.findall(r'^\s*(.+?)\s*(?:：|:|\n)', content, re.M)
            for header in headers:
                if len(header) > 2:
                    pattern = re.escape(header).replace(r'\ ', r'\s*')
                    if pattern not in features['document_structure']['header_patterns']:
                        features['document_structure']['header_patterns'].append(pattern)
                        
            # 提取文本格式
            indents = re.findall(r'^\s{2,}(.+?)(?:\n|$)', content, re.M)
            for indent in indents:
                if len(indent) > 2:
                    pattern = re.escape(indent).replace(r'\ ', r'\s*')
                    if pattern not in features['text_format']['indent_patterns']:
                        features['text_format']['indent_patterns'].append(pattern)
                        
        except Exception as e:
            logger.error(f"学习格式特征失败: {str(e)}")
            
    def _learn_citation_features(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ):
        """学习引用特征"""
        try:
            # 提取法律引用
            laws = re.findall(r'《(.+?)》', content)
            for law in laws:
                if '法' in law or '条例' in law or '规定' in law:
                    pattern = f'《{re.escape(law)}》'
                    if pattern not in features['legal_citation']['law_patterns']:
                        features['legal_citation']['law_patterns'].append(pattern)
                        
            # 提取文档引用
            docs = re.findall(r'(?:根据|依据|按照)(.+?)(?:规定|要求|精神)', content)
            for doc in docs:
                if len(doc) > 2:
                    pattern = re.escape(doc).replace(r'\ ', r'\s*')
                    if pattern not in features['document_citation']['doc_patterns']:
                        features['document_citation']['doc_patterns'].append(pattern)
                        
        except Exception as e:
            logger.error(f"学习引用特征失败: {str(e)}")
            
    def _learn_attachment_features(
        self,
        content: str,
        features: Dict[str, Dict[str, List[str]]]
    ):
        """学习附件特征"""
        try:
            # 提取附件标题
            titles = re.findall(r'附件\d*[:：](.+?)(?:\n|$)', content)
            for title in titles:
                if len(title) > 2:
                    pattern = re.escape(title).replace(r'\ ', r'\s*')
                    if pattern not in features['attachment_description']['title_patterns']:
                        features['attachment_description']['title_patterns'].append(pattern)
                        
            # 提取文件类型
            types = re.findall(r'文件(?:格式|类型)[:：](.+?)(?:\n|$)', content)
            for type_ in types:
                if len(type_) > 2:
                    pattern = re.escape(type_).replace(r'\ ', r'\s*')
                    if pattern not in features['attachment_metadata']['type_patterns']:
                        features['attachment_metadata']['type_patterns'].append(pattern)
                        
        except Exception as e:
            logger.error(f"学习附件特征失败: {str(e)}")
            
    async def _load_ml_model(self):
        """加载机器学习模型"""
        try:
            model_path = os.path.join(settings.BASE_DIR, 'models', 'page_classifier.joblib')
            if os.path.exists(model_path):
                model_data = joblib.load(model_path)
                self.vectorizer = model_data['vectorizer']
                self.classifier = model_data['classifier']
                self.label_encoder = model_data['label_encoder']
                self.feature_importance = model_data['feature_importance']
                self.last_training_time = model_data['last_training_time']
                logger.info("机器学习模型加载成功")
            else:
                logger.info("未找到现有模型,将创建新模型")
                
        except Exception as e:
            logger.error(f"加载机器学习模型失败: {str(e)}")
            
    async def _initialize_feature_stats(self):
        """初始化特征统计"""
        try:
            # 从数据库加载特征使用统计
            stats = await self.db_manager.get_feature_stats()
            for stat in stats:
                self.feature_usage_stats[stat['feature_id']] = {
                    'hit_count': stat['hit_count'],
                    'miss_count': stat['miss_count'],
                    'last_used': stat['last_used'],
                    'importance': stat['importance']
                }
                
            # 清理过期特征
            await self._cleanup_expired_features()
            
        except Exception as e:
            logger.error(f"初始化特征统计失败: {str(e)}")
            
    async def _cleanup_expired_features(self):
        """清理过期特征"""
        try:
            now = datetime.now()
            expired_features = []
            
            # 检查每个特征
            for feature_id, stats in self.feature_usage_stats.items():
                # 如果特征从未使用过
                if stats['last_used'] is None:
                    expired_features.append(feature_id)
                    continue
                    
                # 如果特征长期未使用
                if (now - stats['last_used']).days > self.feature_expiry_days:
                    expired_features.append(feature_id)
                    continue
                    
                # 如果特征重要性过低且使用频率低
                if (stats['importance'] < self.min_feature_importance and
                    stats['hit_count'] / (stats['hit_count'] + stats['miss_count'] + 1) < 0.1):
                    expired_features.append(feature_id)
                    continue
                    
            # 删除过期特征
            for feature_id in expired_features:
                await self.db_manager.delete_feature(feature_id)
                del self.feature_usage_stats[feature_id]
                
            if expired_features:
                logger.info(f"清理了 {len(expired_features)} 个过期特征")
                
        except Exception as e:
            logger.error(f"清理过期特征失败: {str(e)}")
            
    def _get_feature_name(self, feature_id: int) -> str:
        """获取特征名称"""
        try:
            # 实现特征ID到特征名称的映射
            # 这里需要根据实际情况实现
            return f"feature_{feature_id}"
            
        except Exception as e:
            logger.error(f"获取特征名称失败: {str(e)}")
            return ""
            
    def _get_used_features(self, data: Dict[str, Any]) -> List[int]:
        """获取使用的特征ID列表"""
        try:
            # 实现从数据中提取使用的特征ID
            # 这里需要根据实际情况实现
            return []
            
        except Exception as e:
            logger.error(f"获取使用的特征失败: {str(e)}")
            return []
            
    async def get_page_content(self, page: Dict[str, Any]) -> Optional[str]:
        """获取页面内容
        
        Args:
            page: 页面数据
            
        Returns:
            Optional[str]: 页面内容
        """
        browser_page = None
        try:
            # 创建新页面
            browser_page = await self.context.new_page()
            
            # 设置页面选项
            await browser_page.set_default_timeout(settings.PAGE_LOAD_CONFIG['timeout'])
            await browser_page.set_viewport_size({
                'width': 1920,
                'height': 1080
            })
            
            # 访问页面
            await browser_page.goto(
                url=page['url'],
                wait_until=settings.PAGE_LOAD_CONFIG['wait_until'],
                timeout=settings.PAGE_LOAD_CONFIG['timeout']
            )
            
            # 等待页面加载
            if settings.PAGE_LOAD_CONFIG['wait_for_load_state']:
                await browser_page.wait_for_load_state('networkidle')
                
            # 获取页面内容
            content = await browser_page.content()
            return content
            
        except Exception as e:
            logger.error(f"获取页面内容失败 [url={page['url']}]: {str(e)}")
            return None
            
        finally:
            if browser_page:
                await browser_page.close()
                
    async def analyze_page(self, page_id: int, content: str) -> bool:
        """分析页面内容
        
        Args:
            page_id: 页面ID
            content: 页面内容
            
        Returns:
            bool: 是否分析成功
        """
        try:
            if not content:
                return False
                
            # 解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取文本
            text = soup.get_text(strip=True)
            if not text:
                return False
                
            # 分析页面类型
            page_type = self._analyze_page_type(text)
            
            # 提取页面特征
            features = self._extract_page_features(soup, text)
            
            # 保存分析结果
            await self.db_manager.save_page_analysis(
                page_id=page_id,
                page_type=page_type,
                features=features
            )
            
            return True
            
        except Exception as e:
            logger.error(f"分析页面失败 [id={page_id}]: {str(e)}")
            return False
            
    async def update_page_status(self, page_id: int, status: str, error_message: Optional[str] = None):
        """更新页面状态
        
        Args:
            page_id: 页面ID
            status: 状态
            error_message: 错误信息
        """
        try:
            if not self.db_manager:
                return
                
            await self.db_manager.update_page_status(
                page_id=page_id,
                status=status,
                error_message=error_message
            )
            
        except Exception as e:
            logger.error(f"更新页面状态失败 [id={page_id}]: {str(e)}")
            
    def _analyze_page_type(self, text: str) -> str:
        """分析页面类型
        
        Args:
            text: 页面文本
            
        Returns:
            str: 页面类型
        """
        # 使用预定义的特征进行分析
        max_score = 0
        page_type = PageType.UNKNOWN.value
        
        for type_value, features in PAGE_TYPE_FEATURES.items():
            score = self._calculate_type_score(text, features)
            if score > max_score:
                max_score = score
                page_type = type_value
                
        return page_type
        
    def _calculate_type_score(self, text: str, features: Dict) -> float:
        """计算类型得分
        
        Args:
            text: 页面文本
            features: 特征定义
            
        Returns:
            float: 得分
        """
        score = 0.0
        weights = features.get('weights', {})
        
        # 计算各项特征得分
        if 'title_keywords' in features:
            title_score = sum(1 for kw in features['title_keywords'] if kw in text)
            score += title_score * weights.get('title', 0.15)
            
        if 'content_keywords' in features:
            content_score = sum(1 for kw in features['content_keywords'] if kw in text)
            score += content_score * weights.get('content', 0.15)
            
        # 其他征分析...
        
        return score
        
    def _extract_page_features(self, soup: BeautifulSoup, text: str) -> Dict[str, Any]:
        """提取页面特征
        
        Args:
            soup: BeautifulSoup对象
            text: 页面文本
            
        Returns:
            Dict[str, Any]: 特征字典
        """
        features = {
            'text_length': len(text),
            'has_title': bool(soup.find('title')),
            'links_count': len(soup.find_all('a')),
            'images_count': len(soup.find_all('img')),
            'tables_count': len(soup.find_all('table')),
            'forms_count': len(soup.find_all('form')),
            'keywords': self._extract_keywords(text)
        }
        
        return features
        
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词
        
        Args:
            text: 文本
            top_k: 关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        try:
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(text, topK=top_k)
            return keywords
        except Exception as e:
            logger.error(f"提取关键词失败: {str(e)}")
            return []
        
    # ... 其他方法保持不变 ... 