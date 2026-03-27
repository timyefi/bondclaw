"""网站管理模块"""
from typing import Dict, List, Optional, Any, Set
import re
from datetime import datetime, timedelta
import asyncio

from models.base.enums import SectionType, Province
from utils.log_manager import log_manager
from configs.settings import settings
from utils.helpers import normalize_url, get_domain

# 获取网站管理器日志器
logger = log_manager.get_logger('website')

class WebsiteManager:
    """网站管理类"""
    
    def __init__(self, db_manager=None):
        """初始化网站管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db_manager = db_manager
        
        # 使用models中的定义
        self.section_patterns = {
            section_type: SectionType.get_patterns(section_type.value)
            for section_type in SectionType
        }
        
        # 使用models中的省份定义
        self.province_sites = Province.PROVINCIAL_SITES
        
        # 初始化特征缓存
        self._feature_cache = {
            'url_patterns': {},
            'domain_patterns': {},
            'section_patterns': {},
            'last_update': datetime.now()
        }
        
        # 初始化URL缓存
        self._url_section_cache: Dict[str, str] = {}
        self._url_province_cache: Dict[str, str] = {}
        self._last_cache_cleanup = datetime.now()
        self._cache_hits = 0
        self._cache_misses = 0
        
    async def initialize(self):
        """初始化管理器"""
        if self.db_manager:
            await self._load_features()
            
    def get_provinces(self) -> List[str]:
        """获取所有省份列表
        
        Returns:
            List[str]: 省份名称列表
        """
        return list(self.province_sites.keys())
            
    async def get_active_features(self, site_id: int = None) -> List[Dict[str, Any]]:
        """获取活跃特征
        
        Args:
            site_id: 网站ID，如果为None则获取所有活跃特征
            
        Returns:
            List[Dict[str, Any]]: 特征列表
        """
        try:
            # 如果没有数据库管理器，返回空列表
            if not self.db_manager:
                logger.warning("数据库管理器未初始化")
                return []
                
            # 获取特征
            features = await self.db_manager.get_active_features(site_id)
            
            # 如果特征为空，尝试从缓存加载
            if not features and hasattr(self, 'features'):
                logger.info("从缓存加载特征")
                features = []
                for feature_list in self.features.values():
                    features.extend(feature_list)
                    
            # 如果仍然为空，尝试重新加载特征
            if not features:
                logger.info("重新加载特征")
                await self._load_features()
                if hasattr(self, 'features'):
                    for feature_list in self.features.values():
                        features.extend(feature_list)
                        
            return features
            
        except Exception as e:
            logger.error(f"获取活跃特征失败: {str(e)}")
            return []
            
    async def _load_features(self):
        """加载特征"""
        try:
            # 获取活跃特征
            features = await self.db_manager.get_active_features()
            if not features:
                logger.warning("未找到活跃的网站特征")
                return
                
            # 按类型分组
            self.features = {}
            for feature in features:
                feature_type = feature['feature_type']
                if feature_type not in self.features:
                    self.features[feature_type] = []
                self.features[feature_type].append(feature)
                
            logger.info("特征加载完成")
            
        except Exception as e:
            logger.error(f"加载特征失败: {str(e)}")
            
    def _group_features_by_category(self, features: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """按类别分组特征
        
        Args:
            features: 特征列表
            
        Returns:
            Dict[str, List[str]]: 分组后的特征
        """
        grouped = {}
        for feature in features:
            category = feature['feature_category']
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(feature['feature_value'])
        return grouped
        
    async def _update_feature_stats(self, feature_type: str, feature_value: str, hit: bool):
        """更新特征统计
        
        Args:
            feature_type: 特征类型
            feature_value: 特征值
            hit: 是否命中
        """
        if not self.db_manager:
            return
            
        try:
            # 查找特征
            features = await self.get_active_features(feature_type)
            for feature in features:
                if feature['feature_value'] == feature_value:
                    # 更新统计
                    await self.db_manager.update_feature_stats(feature['id'], hit)
                    break
                    
        except Exception as e:
            logger.error(f"更新特征统计失败: {str(e)}")
            
    async def add_new_feature(self, feature_type: str, feature_value: str, category: str, source_url: str = None):
        """添加新特征
        
        Args:
            feature_type: 特征类型
            feature_value: 特征值
            category: 特征类别
            source_url: 来源URL
        """
        if not self.db_manager:
            return
            
        try:
            # 创建新特征
            feature_data = {
                'feature_type': feature_type,
                'feature_value': feature_value,
                'feature_category': category,
                'source_url': source_url,
                'confidence': 0.5,  # 初始置信度
                'is_active': True,
                'is_verified': False
            }
            
            # 添加到数据库
            await self.db_manager.add_feature(feature_data)
            
            # 重��加载特征
            await self._load_features()
            
        except Exception as e:
            logger.error(f"添加新特征失败: {str(e)}")
            
    def get_section_type(self, url: str) -> Optional[str]:
        """根据URL获取栏目类型
        
        Args:
            url: 网站URL
            
        Returns:
            Optional[str]: 栏目类型
        """
        # 规范化URL
        url = normalize_url(url)
        
        # 检查缓存
        if settings.CACHE_CONFIG['enabled']:
            if url in self._url_section_cache:
                self._cache_hits += 1
                return self._url_section_cache[url]
            self._cache_misses += 1
            
        # 从特征缓存中匹配
        for category, patterns in self._feature_cache['section_patterns'].items():
            for pattern in patterns:
                if re.search(pattern, url, re.I):
                    # 更新特征统计
                    asyncio.create_task(
                        self._update_feature_stats('section_pattern', pattern, True)
                    )
                    # 更新缓存
                    if settings.CACHE_CONFIG['enabled']:
                        self._url_section_cache[url] = category
                    return category
                    
        # 从默认配置中匹配
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url, re.I):
                    # 添加新特征
                    asyncio.create_task(
                        self.add_new_feature(
                            'section_pattern',
                            pattern,
                            section_type.value,
                            url
                        )
                    )
                    # 更新缓存
                    if settings.CACHE_CONFIG['enabled']:
                        self._url_section_cache[url] = section_type.value
                    return section_type.value
                    
        # 更新缓存
        if settings.CACHE_CONFIG['enabled']:
            self._url_section_cache[url] = None
            
        return None
        
    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效
        
        Args:
            url: 网站URL
            
        Returns:
            bool: URL是否有效
        """
        # 规范化URL
        url = normalize_url(url)
        
        # 检查黑名单
        for pattern in settings.DICT_CONFIG.get('url_blacklist', []):
            if re.search(pattern, url, re.I):
                return False
                
        # 检查白名单
        for pattern in settings.DICT_CONFIG.get('url_whitelist', []):
            if re.search(pattern, url, re.I):
                return True
                
        # 检查域名
        domain = get_domain(url)
        if not domain:
            return False
            
        # 检查是否为政府网站
        if not domain.endswith('.gov.cn'):
            return False
            
        return True
        
    async def get_site_info(self, url: str) -> Optional[Dict[str, Any]]:
        """获取网站信息
        
        Args:
            url: 网站URL
            
        Returns:
            Optional[Dict[str, Any]]: 网站信息
        """
        try:
            # 规范化URL
            url = normalize_url(url)
            
            # 从数据库获取
            site = await self.db_manager.get_site_by_url(url)
            if site:
                return site
                
            # 获取域名
            domain = get_domain(url)
            if not domain:
                return None
                
            # 获取省份
            province = None
            for prov, site_url in self.province_sites.items():
                if url.startswith(site_url):
                    province = prov
                    break
                    
            # 创建网站信息
            site_info = {
                'url': url,
                'domain': domain,
                'province': province,
                'type': SiteType.UNKNOWN.value,
                'status': SiteStatus.PENDING.value,
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 保存到数据库
            site_id = await self.db_manager.add_site(site_info)
            if site_id:
                site_info['id'] = site_id
                return site_info
                
            return None
            
        except Exception as e:
            logger.error(f"获取网站信息失败 [{url}]: {str(e)}")
            return None
            
    async def update_site_status(self, site_id: int, status: str, error_message: str = None) -> bool:
        """更新网站状态
        
        Args:
            site_id: 网站ID
            status: 新状态
            error_message: 错误信息
            
        Returns:
            bool: 是否成功
        """
        try:
            site_data = {
                'status': status,
                'error_message': error_message,
                'updated_at': datetime.now()
            }
            return await self.db_manager.update_site(site_id, site_data)
            
        except Exception as e:
            logger.error(f"更新网站状态失败 [id={site_id}]: {str(e)}")
            return False
        
    def get_province(self, url: str) -> Optional[str]:
        """获取URL所属省份
        
        Args:
            url: 网站URL
            
        Returns:
            Optional[str]: 省份名称
        """
        # 规范化URL
        url = normalize_url(url)
        
        # 检查缓存
        if settings.CACHE_CONFIG['enabled']:
            if url in self._url_province_cache:
                self._cache_hits += 1
                return self._url_province_cache[url]
            self._cache_misses += 1
            
        # 从特征缓存中匹配
        for province, patterns in self._feature_cache['url_patterns'].items():
            for pattern in patterns:
                if re.search(pattern, url, re.I):
                    # 更新特征统计
                    asyncio.create_task(
                        self._update_feature_stats('url_pattern', pattern, True)
                    )
                    # 更新缓存
                    if settings.CACHE_CONFIG['enabled']:
                        self._url_province_cache[url] = province
                    return province
                    
        # 从默认配置中匹配
        for province, patterns in self.province_sites.items():
            for pattern in patterns:
                if re.search(pattern, url, re.I):
                    # 添加新特征
                    asyncio.create_task(
                        self.add_new_feature(
                            'url_pattern',
                            pattern,
                            province,
                            url
                        )
                    )
                    # 更新缓存
                    if settings.CACHE_CONFIG['enabled']:
                        self._url_province_cache[url] = province
                    return province
                    
        # 更新缓存
        if settings.CACHE_CONFIG['enabled']:
            self._url_province_cache[url] = None
            
        return None
        
    def _cleanup_cache(self):
        """清理过期缓存"""
        if not settings.CACHE_CONFIG['enabled']:
            return
            
        now = datetime.now()
        
        # 清理特征缓存
        if (now - self._feature_cache['last_update']).seconds > settings.CACHE_CONFIG['expire']:
            if self.db_manager:
                asyncio.create_task(self._load_features())
                
        # 清理URL缓存
        if (now - self._last_cache_cleanup).seconds > settings.CACHE_CONFIG['expire']:
            self._url_section_cache.clear()
            self._url_province_cache.clear()
            self._last_cache_cleanup = now
            
            # 记录缓存统计
            total = self._cache_hits + self._cache_misses
            if total > 0:
                hit_rate = self._cache_hits / total * 100
                logger.info(f"缓存命中率: {hit_rate:.2f}%")
            self._cache_hits = 0
            self._cache_misses = 0