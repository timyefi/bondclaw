"""网站发现模块"""
import asyncio
import re
import time
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup

from core.managers.config_manager import ConfigManager
from core.managers.monitor_manager import MonitorManager
from core.managers.browser_manager import BrowserManager
from models.base.enums import SiteType, SiteStatus, PageType, CrawlStatus, Province
from utils.log_manager import log_manager
from utils.helpers import normalize_url, is_valid_url, get_domain

from .website_manager import WebsiteManager
from .page_manager import PageManager

# 获取发现器日志器
logger = log_manager.get_logger('discovery')

class SiteDiscovery:
    """网站发现器"""
    
    def __init__(
        self,
        db_manager,
        config_manager: Optional[ConfigManager] = None,
        monitor_manager: Optional[MonitorManager] = None,
        browser_manager: Optional[BrowserManager] = None
    ):
        """初始化网站发现器
        
        Args:
            db_manager: 数据库管理器
            config_manager: 配置管理器
            monitor_manager: 监控管理器
            browser_manager: 浏览器管理器
        """
        # 设置数据库管理器
        self.db_manager = db_manager
        
        # 设置配置管理器
        self.config_manager = config_manager or ConfigManager()
        
        # 设置监控管理器
        self.monitor_manager = monitor_manager or MonitorManager()
        
        # 设置浏览器管理器
        self.browser_manager = browser_manager or BrowserManager(
            config_manager=self.config_manager,
            monitor_manager=self.monitor_manager
        )
        
        # 初始化网站管理器
        self.website_manager = WebsiteManager(db_manager=db_manager)
        
        # 初始化页面管理器
        self.page_manager = PageManager(db_manager=db_manager)
        
        # 获取配置
        crawler_config = self.config_manager.get_config('crawler')
        self.browser_config = crawler_config.get('browser', {})
        self.page_load_config = crawler_config.get('page_load', {})
        self.concurrency_config = crawler_config.get('concurrency', {})
        self.proxy_config = crawler_config.get('proxy', {})
        
        # 初始化状态
        self._discovered_urls = set()
        self._processed_urls = set()
        self._error_urls = set()
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()
        
    async def initialize(self):
        """初始化网站发现器"""
        try:
            # 初始化浏览器管理器
            await self.browser_manager.initialize()
            
            # 初始化网站管理器
            if self.website_manager:
                await self.website_manager.initialize()
            
            # 初始化页面管理器
            if self.page_manager:
                await self.page_manager.initialize()
            
            logger.info("网站发现器初始化完成")
            
        except Exception as e:
            logger.error(f"初始化网站发现器失败: {str(e)}")
            # 确保资源被清理
            await self.cleanup()
            raise
            
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理浏览器资源
            if self.browser_manager:
                await self.browser_manager.cleanup()
            
            # 记录统计信息
            self.monitor_manager.record_metric('discovered_urls', len(self._discovered_urls))
            self.monitor_manager.record_metric('processed_urls', len(self._processed_urls))
            self.monitor_manager.record_metric('error_urls', len(self._error_urls))
            
            logger.info("网站发现器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理网站发现器资源失败: {str(e)}")
            
    async def discover_all_sites_async(self):
        """发现所有网站"""
        try:
            with self.monitor_manager.track_operation('discover_sites'):
            # 获取所有活跃特征
            features = await self.website_manager.get_active_features()
            if not features:
                logger.warning("未找到活跃的网站特征")
                return
                
            # 获取所有省份
            provinces = Province.get_all_provinces()
            if not provinces:
                logger.warning("未找到省份信息")
                return
                
            # 获取并发限制
            max_concurrent = self.concurrency_config.get('max_concurrent_sites', 3)
            
            # 创建信号量
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # 并发发现每个省份的网站
            async def process_province(province):
                async with semaphore:
                    try:
                        await self.discover_province_sites(
                            province=province,
                            features=features
                        )
                    except Exception as e:
                        logger.error(f"处理省份 {province} 失败: {str(e)}")
                        
            # 创建任务
            tasks = [process_province(province) for province in provinces]
            
            # 等待所有任务完成
            await asyncio.gather(*tasks)
            
            logger.info(f"网站发现完成, 共发现 {len(self._discovered_urls)} 个网站")
            
        except Exception as e:
            logger.error(f"发现网站失败: {str(e)}")
            raise
            
    async def discover_province_sites(self, province: str, features: List[Dict[str, Any]]):
        """发现指定省份的网站
        
        Args:
            province: 省份名称
            features: 特征列表
        """
        page = None
        retry_count = 0
        max_retries = self.concurrency_config.get('max_retries', 3)
        
        try:
            # 获取省份的入口URL
            entry_url = Province.get_province_url(province)
            if not entry_url:
                logger.warning(f"未找到省份 {province} 的入口URL")
                return
                
            while retry_count < max_retries:
                try:
                    # 确保浏览器和上下文已初始化
                    if not self.browser or not self.context:
                        raise RuntimeError("浏览器或上下文未初始化")
                        
                    # 创建新页面
                    page = await self.context.new_page()
                    if not page:
                        raise RuntimeError("创建页面返回None")
                        
                    # 设置页面加载选项
                    try:
                        await self._setup_page(page)
                    except Exception as e:
                        logger.error(f"设置页面失败: {str(e)}")
                        if page:
                            await page.close()
                            page = None
                        raise
                        
                    # 访问页面
                    await self._visit_page(page, entry_url)
                    
                    # 提取链接
                    links = await self._extract_links(page)
                    
                    # 分析链接
                    await self._analyze_links(
                        links=links,
                        province=province,
                        features=features
                    )
                    
                    # 成功处理，跳出重试循环
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if page:
                        try:
                            await page.close()
                        except:
                            pass
                        page = None
                        
                    if retry_count >= max_retries:
                        logger.error(f"处理页面失败 [{entry_url}] (重试次数: {retry_count}): {str(e)}")
                        self._error_urls.add(entry_url)
                        raise
                    else:
                        logger.warning(f"处理页面失败，准备重试 [{entry_url}] (重试次数: {retry_count}): {str(e)}")
                        # 增加重试延迟
                        retry_delay = self.concurrency_config.get('retry_delay', 2)
                        await asyncio.sleep(retry_delay * retry_count)
                        
        except Exception as e:
            logger.error(f"发现省份 {province} 网站失败: {str(e)}")
            raise
            
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.error(f"关闭页面失败: {str(e)}")
                    
            logger.info(f"省份 {province} 网站发现完成")
            
    async def _setup_page(self, page: Page):
        """设置页面加载选项
        
        Args:
            page: 页面对象
            
        Raises:
            ValueError: 页面对象为None
            RuntimeError: 设置页面选项失败
        """
        if not page:
            raise ValueError("页面对象为None")
            
        try:
            # 获取代理配置
            proxy_config = self.config_manager.get_proxy_config()
            if proxy_config and proxy_config.get('enabled', False):
                await page.route('**/*', lambda route: self._handle_proxy_route(route, proxy_config))
            
            # 设置超时
            timeout = self.page_load_config.get('timeout', 30000)
            try:
                await page.set_default_timeout(timeout)
            except Exception as e:
                raise RuntimeError(f"设置页面超时失败: {str(e)}")
                
            # 设置视口大小
            viewport = self.browser_config.get('viewport', {'width': 1920, 'height': 1080})
            try:
                await page.set_viewport_size(viewport)
            except Exception as e:
                raise RuntimeError(f"设置页面视口失败: {str(e)}")
                
            # 设置请求头
            headers = self.browser_config.get('headers', {})
            if not headers:
                headers = {
                    'User-Agent': self.browser_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                }
            try:
                await page.set_extra_http_headers(headers)
            except Exception as e:
                raise RuntimeError(f"设置页面请求头失败: {str(e)}")
                
            # 启用JavaScript
            if self.page_load_config.get('javascript_enabled', True):
                try:
                    await page.set_javascript_enabled(True)
                except Exception as e:
                    raise RuntimeError(f"启用JavaScript失败: {str(e)}")
                    
            # 设置请求拦截
            if not proxy_config or not proxy_config.get('enabled', False):
                try:
                    await page.route('**/*', self._handle_route)
                except Exception as e:
                    raise RuntimeError(f"设置请求拦截失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"设置页面失败: {str(e)}")
            # 确保在失败时关闭页面
            try:
                await page.close()
            except:
                pass
            raise
            
    async def _handle_route(self, route):
        """处理请求路由
        
        Args:
            route: 请求路由对象
        """
        # 检查请求类型
        if route.request.resource_type in ['image', 'media', 'font']:
            await route.abort()
        else:
            await route.continue_()
            
    async def _handle_proxy_route(self, route, proxy_config: Dict[str, Any]):
        """处理代理请求路由
        
        Args:
            route: 请求路由对象
            proxy_config: 代理配置
        """
        try:
            # 检查是否需要使用代理
            url = route.request.url
            if self._should_use_proxy(url, proxy_config):
                # 获取代理信息
                proxy_info = await self._get_proxy(proxy_config)
                if proxy_info:
                    # 使用代理
                    await route.continue_({
                        'proxy': proxy_info
                    })
                else:
                    # 无可用代理，直接请求
                    await route.continue_()
            else:
                # 不使用代理
                await route.continue_()
        except Exception as e:
            logger.error(f"处理代理请求失败: {str(e)}")
            await route.continue_()
            
    def _should_use_proxy(self, url: str, proxy_config: Dict[str, Any]) -> bool:
        """判断是否需要使用代理
        
        Args:
            url: 请求URL
            proxy_config: 代理配置
            
        Returns:
            bool: 是否使用代理
        """
        try:
            # 获取代理策略
            strategy = proxy_config.get('strategy', {})
            
            # 检查是否在重试阈值内
            min_retry = strategy.get('min_retry_before_proxy', 2)
            if self._retry_count < min_retry:
                return False
                
            # 检查是否在智能代理规则中
            smart_proxy = strategy.get('smart_proxy', {})
            if smart_proxy.get('enabled', False):
                rules = smart_proxy.get('rules', [])
                for rule in rules:
                    if rule.get('pattern') in url:
                        return rule.get('use_proxy', True)
                        
            return True
            
        except Exception as e:
            logger.error(f"判断代理使用失败: {str(e)}")
            return False
            
    async def _get_proxy(self, proxy_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取代理信息
        
        Args:
            proxy_config: 代理配置
            
        Returns:
            Optional[Dict[str, Any]]: 代理信息
        """
        try:
            # 获取代理API配置
            api_config = proxy_config.get('api', {})
            
            # 构建请求参数
            params = {
                'orderid': api_config.get('order_no'),
                'num': proxy_config.get('settings', {}).get('count', 1),
                'protocol': proxy_config.get('settings', {}).get('proxy_type', 1),
                'method': 2,  # 返回JSON格式
                'an_ha': 1,  # 返回高匿代理
                'sep': 1     # 使用分号分隔
            }
            
            # 发送请求获取代理
            async with aiohttp.ClientSession() as session:
                async with session.get(api_config['url'], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'data' in data:
                            proxy = data['data'][0]  # 获取第一个代理
                            return {
                                'server': f"http://{proxy['ip']}:{proxy['port']}",
                                'username': proxy.get('username'),
                                'password': proxy.get('password')
                            }
            return None
            
        except Exception as e:
            logger.error(f"获取代理失败: {str(e)}")
            return None
            
    async def _visit_page(self, page: Page, url: str):
        """访问页面
        
        Args:
            page: 页面对象
            url: 页面URL
        """
        try:
            # 访问页面
            response = await page.goto(
                url=url,
                wait_until=self.page_load_config.get('wait_until', 'networkidle'),
                timeout=int(self.page_load_config.get('timeout', 30000))
            )
            
            # 等待页面加载完成
            if self.page_load_config.get('wait_for_load_state', True):
                await page.wait_for_load_state('networkidle')
                
            return response
            
        except Exception as e:
            logger.error(f"访问页面失败 [{url}]: {str(e)}")
            raise
            
    async def _extract_links(self, page: Page) -> Set[str]:
        """提取页面链接
        
        Args:
            page: 页面对象
            
        Returns:
            Set[str]: 链接集合
        """
        try:
            # 获取页面内容
            content = await page.content()
            
            # 解析HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取所有链接
            links = set()
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    # 转换为绝对URL
                    abs_url = urljoin(page.url, href)
                    if is_valid_url(abs_url):
                        links.add(normalize_url(abs_url))
                        
            return links
            
        except Exception as e:
            logger.error(f"提取链接失败: {str(e)}")
            return set()
            
    async def _analyze_links(self, links: Set[str], province: str, features: List[Dict[str, Any]]):
        """分析链接
        
        Args:
            links: 链接集合
            province: 省份名称
            features: 特征列表
        """
        try:
            for url in links:
                # 检查是否已处理
                if url in self._processed_urls:
                    continue
                    
                # 标记为已处理
                self._processed_urls.add(url)
                
                try:
                    # 获取域名
                    domain = get_domain(url)
                    
                    # 检查是否为政府网站
                    if not self._is_government_site(domain):
                        continue
                        
                    # 检查是否匹配特征
                    site_type = await self._match_site_features(url, features)
                    if not site_type:
                        continue
                        
                    # 添加到发现集合
                    self._discovered_urls.add(url)
                    
                    # 保存网站信息
                    await self._save_site(
                        url=url,
                        site_type=site_type,
                        province=province
                    )
                    
                except Exception as e:
                    logger.error(f"分析链接失败 [{url}]: {str(e)}")
                    self._error_urls.add(url)
                    
        except Exception as e:
            logger.error(f"分析链接集合失败: {str(e)}")
            
    def _is_government_site(self, domain: str) -> bool:
        """检查是否为政府网站
        
        Args:
            domain: 域名
            
        Returns:
            bool: 是否为政府网站
        """
        return domain.endswith('.gov.cn')
        
    async def _match_site_features(self, url: str, features: List[Dict[str, Any]]) -> Optional[str]:
        """匹配网站特征
        
        Args:
            url: 网站URL
            features: 特征列表
            
        Returns:
            Optional[str]: 网站类型
        """
        try:
            for feature in features:
                if re.search(feature['feature_value'], url, re.I):
                    return feature['feature_category']
            return None
        except Exception as e:
            logger.error(f"匹配特征失败 [{url}]: {str(e)}")
            return None
            
    async def _save_site(self, url: str, site_type: str, province: str):
        """保存网站信息
        
        Args:
            url: 网站URL
            site_type: 网站类型
            province: 省份名称
        """
        try:
            # 检查是否已存在
            exists = await self.db_manager.check_site_exists(url)
            if exists:
                return
                
            # 创建网站记录
            site_data = {
                'url': url,
                'type': site_type,
                'province': province,
                'status': SiteStatus.ACTIVE.value,
                'is_active': True
            }
            
            # 存到数据库
            await self.db_manager.add_site(site_data)
            
            logger.info(f"保存网站成功 [{url}]")
            
        except Exception as e:
            logger.error(f"保存网站失败 [{url}]: {str(e)}")
            raise