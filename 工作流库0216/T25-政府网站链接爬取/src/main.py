"""主程序入口

提供程序启动和初始化功能
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

from services.config.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.website_manager import WebsiteManager
from core.site_discovery import SiteDiscovery
from core.site_analyzer import SiteAnalyzer
from core.page_manager import PageManager
from utils.logging import log_manager

# 初始化日志
logger = log_manager.get_logger('main')

def init_config():
    """初始化配置"""
    # 确保配置目录存在
    config_dir = Path('config')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 确保配置文件存在
    config_path = config_dir / 'config.json'
    if not config_path.exists():
        logger.warning("配置文件不存在，使用默认设置")
        
    return ConfigManager(str(config_path))

async def initialize_services():
    """初始化各个服务组件"""
    try:
        # 初始化配置管理器
        config_manager = init_config()
        logger.info("配置管理器初始化完成")
        
        # 初始化数据库管理器
        db_config = config_manager.get('database', {})
        db_manager = DatabaseManager(db_config)
        await db_manager.initialize()
        logger.info("数据库管理器初始化完成")
        
        # 初始化网站管理器
        website_config = config_manager.get('website', {})
        website_manager = WebsiteManager(db_manager, website_config)
        await website_manager.initialize()
        logger.info("网站管理器初始化完成")
        
        # 初始化站点发现服务
        discovery_config = config_manager.get('discovery', {})
        site_discovery = SiteDiscovery(db_manager, discovery_config)
        await site_discovery.initialize()
        logger.info("站点发现服务初始化完成")
        
        # 初始化站点分析器
        analyzer_config = config_manager.get('analyzer', {})
        site_analyzer = SiteAnalyzer(db_manager, analyzer_config)
        await site_analyzer.initialize()
        logger.info("站点分析器初始化完成")
        
        # 初始化页面管理器
        page_config = config_manager.get('page', {})
        page_manager = PageManager(db_manager, page_config)
        await page_manager.initialize()
        logger.info("页面管理器初始化完成")
        
        return {
            'config_manager': config_manager,
            'db_manager': db_manager,
            'website_manager': website_manager,
            'site_discovery': site_discovery,
            'site_analyzer': site_analyzer,
            'page_manager': page_manager
        }
        
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        raise

async def cleanup_services(services):
    """清理各个服务组件"""
    try:
        for name, service in services.items():
            if hasattr(service, 'cleanup'):
                await service.cleanup()
                logger.info(f"{name} 清理完成")
    except Exception as e:
        logger.error(f"服务清理失败: {str(e)}")

async def main():
    """主程序入口"""
    services = None
    try:
        # 初始化所有服务
        services = await initialize_services()
        
        # 启动核心服务
        website_manager = services['website_manager']
        site_discovery = services['site_discovery']
        
        await website_manager.start()
        await site_discovery.start()
        
        logger.info("系统启动完成")
        
        # 等待退出信号
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        
    except Exception as e:
        logger.error(f"系统运行异常: {str(e)}")
        sys.exit(1)
    finally:
        # 清理资源
        if services:
            await cleanup_services(services)

if __name__ == "__main__":
    try:
        # 设置项目根目录
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # 运行主程序
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("程序退出")
    except Exception as e:
        logger.error(f"程序异常退出: {str(e)}")
        sys.exit(1) 