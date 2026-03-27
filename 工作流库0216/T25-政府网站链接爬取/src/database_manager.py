"""数据库管理器模块"""
import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Type, Set
from datetime import datetime
import json

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
import aiomysql

from services.config.config_manager import ConfigManager
from models import (
    GovernmentSite, SiteFeature, ContentPage,
    PageSection, PageAnalysis, FeatureStats,
    TrainingData, ModelPerformance, PageFeature,
    SiteSection, Dictionary, CrawlLog, BaseModel
)
from utils.log_manager import log_manager

# 获取日志器
logger = log_manager.get_logger('database_manager')

def _get_model_dependencies(model_class: BaseModel) -> Set[str]:
    """获取模型的依赖表名"""
    dependencies = set()
    table_name = model_class.__tablename__
    for column in model_class.__table__.columns:
        for fk in column.foreign_keys:
            # 忽略自引用
            if fk.column.table.name != table_name:
                dependencies.add(fk.column.table.name)
    return dependencies

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.pool = None
        self.engine = None
        self._session_factory = None
        self.config_manager = ConfigManager()
        
    async def initialize(self):
        """初始化数据库连接"""
        try:
            # 从配置管理器获取数据库配置
            db_config = self.config_manager.get('database', {})
            
            # 创建数据库连接池
            self.pool = await aiomysql.create_pool(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3306),
                user=db_config.get('username'),
                password=db_config.get('password'),
                db=db_config.get('database'),
                charset=db_config.get('charset', 'utf8mb4'),
                autocommit=True
            )
            logger.info("数据库连接池创建成功")
            
            # 创建异步引擎
            database_url = (
                f"mysql+aiomysql://{db_config.get('username')}:{db_config.get('password')}@"
                f"{db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}"
            )
            self.engine = create_async_engine(
                database_url,
                pool_pre_ping=True,
                echo=db_config.get('echo', False)
            )
            
            # 创建会话工厂
            self._session_factory = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 检查并更新表结构
            await self._check_and_update_tables()
            
            logger.info("数据库管理器初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
            
    async def cleanup(self):
        """清理资源"""
        try:
            if self.engine:
                await self.engine.dispose()
                logger.info("数据库引擎已关闭")
                
            if self.pool:
                self.pool.close()
                await self.pool.wait_closed()
                logger.info("数据库连接池已关闭")
        except Exception as e:
            logger.error(f"清理资源时发生错误: {str(e)}")
            
    def _sort_models_by_dependencies(self, models_dict: Dict[str, BaseModel]) -> List[BaseModel]:
        """按依赖关系对模型进行排序"""
        # 构建依赖图
        dependencies = {
            table_name: _get_model_dependencies(model_class)
            for table_name, model_class in models_dict.items()
        }
        
        # 拓扑排序
        sorted_tables = []
        visited = set()
        temp_visited = set()
        
        def visit(table_name: str):
            if table_name in temp_visited:
                raise ValueError(f"检测到循环依赖: {table_name}")
            if table_name in visited:
                return
                
            temp_visited.add(table_name)
            
            # 先处理依赖
            for dep in dependencies[table_name]:
                if dep in models_dict:  # 只处理已定义的表
                    visit(dep)
                    
            temp_visited.remove(table_name)
            visited.add(table_name)
            sorted_tables.append(models_dict[table_name])
            
        # 遍历所有表
        for table_name in models_dict:
            if table_name not in visited:
                visit(table_name)
                
        return sorted_tables
        
    async def _check_and_update_tables(self):
        """检查并更新表结构"""
        try:
            # 获取所有模型类
            models_dict = {
                model.__tablename__: model
                for model in [
                    GovernmentSite,  # 基础表
                    Dictionary,       # 基础表
                    SiteFeature,     # 依赖 GovernmentSite
                    SiteSection,     # 依赖 GovernmentSite
                    ContentPage,     # 依赖 GovernmentSite
                    PageFeature,     # 依赖 ContentPage, SiteFeature
                    PageSection,     # 依赖 ContentPage
                    PageAnalysis,    # 依赖 ContentPage
                    FeatureStats,    # 依赖 SiteFeature
                    TrainingData,    # 独立表
                    ModelPerformance,# 独立表
                    CrawlLog        # 依赖 GovernmentSite
                ]
            }
            
            # 按依赖关系排序
            sorted_models = self._sort_models_by_dependencies(models_dict)
            
            # 创建或更新表
            async with self.engine.begin() as conn:
                for model in sorted_models:
                    await conn.run_sync(lambda sync_conn: model.__table__.create(sync_conn, checkfirst=True))
                    logger.info(f"表 {model.__tablename__} 创建或更新成功")
                    
        except Exception as e:
            logger.error(f"检查和更新表结构失败: {str(e)}")
            raise
            
    async def drop_all_tables(self):
        """删除所有表"""
        try:
            # 禁用外键检查
            await self.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 获取所有模型类并按依赖关系排序
            models_dict = {
                model.__tablename__: model
                for model in [
                    ModelPerformance, TrainingData, FeatureStats,
                    PageFeature, PageSection, PageAnalysis,
                    ContentPage, SiteSection, SiteFeature,
                    GovernmentSite, Dictionary, CrawlLog
                ]
            }
            
            # 按依赖关系的反序删除表
            sorted_models = self._sort_models_by_dependencies(models_dict)
            sorted_models.reverse()  # 反转顺序，先删除依赖表
            
            for model in sorted_models:
                table_name = model.__tablename__
                query = f"DROP TABLE IF EXISTS {table_name}"
                await self.execute(query)
                logger.info(f"表 {table_name} 删除成功")
                
        except Exception as e:
            logger.error(f"删除表失败: {str(e)}")
            raise
            
        finally:
            # 恢复外键检查
            await self.execute("SET FOREIGN_KEY_CHECKS = 1")
            
    async def execute(self, query: str, params: tuple = None) -> bool:
        """执行SQL语句
        
        Args:
            query: SQL语句
            params: 参数元组
            
        Returns:
            bool: 是否执行成功
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, params or ())
                    return True
                except Exception as e:
                    logger.error(f"执行SQL失败: {str(e)}")
                    return False
                    
    async def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """查询单条记录
        
        Args:
            query: SQL语句
            params: 参数元组
            
        Returns:
            Dict: 记录字典
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(query, params or ())
                    return await cur.fetchone()
                except Exception as e:
                    logger.error(f"查询单条记录失败: {str(e)}")
                    return None
                    
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """查询多条记录
        
        Args:
            query: SQL语句
            params: 参数元组
            
        Returns:
            List[Dict]: 记录字典列表
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                try:
                    await cur.execute(query, params or ())
                    return await cur.fetchall()
                except Exception as e:
                    logger.error(f"查询多条记录失败: {str(e)}")
                    return []
                    
    async def get_all_sites(self) -> List[Dict[str, Any]]:
        """获取所有网站
        
        Returns:
            List[Dict[str, Any]]: 网站列表
        """
        query = """
            SELECT * FROM government_sites 
            WHERE is_active = TRUE
            ORDER BY province, city, department
        """
        return await self.fetch_all(query)
        
    async def get_site_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """根据URL获取网站
        
        Args:
            url: 网站URL
            
        Returns:
            Optional[Dict[str, Any]]: 网站信息
        """
        query = "SELECT * FROM government_sites WHERE url = %s"
        return await self.fetch_one(query, (url,))
        
    async def add_site(self, site_data: Dict[str, Any]) -> Optional[int]:
        """添加网站
        
        Args:
            site_data: 网站数据
            
        Returns:
            Optional[int]: 网站ID
        """
        try:
            # 准备SQL
            columns = ', '.join(site_data.keys())
            placeholders = ', '.join(['%s'] * len(site_data))
            query = f"""
                INSERT INTO government_sites ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(site_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加网站失败: {str(e)}")
            return None
            
    async def update_site(self, site_id: int, site_data: Dict[str, Any]) -> bool:
        """更新网站信息
        
        Args:
            site_id: 网站ID
            site_data: 网站数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 准备SQL
            set_clause = ', '.join([f"{k} = %s" for k in site_data.keys()])
            query = f"""
                UPDATE government_sites 
                SET {set_clause}
                WHERE id = %s
            """
            
            # 执行更新
            values = tuple(site_data.values()) + (site_id,)
            return await self.execute(query, values)
            
        except Exception as e:
            logger.error(f"更新网站失败: {str(e)}")
            return False
            
    async def add_feature(self, feature_data: Dict[str, Any]) -> Optional[int]:
        """添加特征
        
        Args:
            feature_data: 特征数据
            
        Returns:
            Optional[int]: 特征ID
        """
        try:
            # 准备SQL
            columns = ', '.join(feature_data.keys())
            placeholders = ', '.join(['%s'] * len(feature_data))
            query = f"""
                INSERT INTO site_features ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(feature_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加特征失败: {str(e)}")
            return None
            
    async def get_site_features(self, site_id: int) -> List[Dict[str, Any]]:
        """获取网站特征
        
        Args:
            site_id: 网站ID
            
        Returns:
            List[Dict[str, Any]]: 特征列表
        """
        query = """
            SELECT * FROM site_features 
            WHERE site_id = %s AND is_active = TRUE
            ORDER BY feature_type, feature_category
        """
        return await self.fetch_all(query, (site_id,))
        
    async def add_content_page(self, page_data: Dict[str, Any]) -> Optional[int]:
        """添加内容页面
        
        Args:
            page_data: 页面数据
            
        Returns:
            Optional[int]: 页面ID
        """
        try:
            # 准备SQL
            columns = ', '.join(page_data.keys())
            placeholders = ', '.join(['%s'] * len(page_data))
            query = f"""
                INSERT INTO content_pages ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(page_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加内容页面失败: {str(e)}")
            return None
            
    async def get_content_page_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """根据URL获取内容页面
        
        Args:
            url: 页面URL
            
        Returns:
            Optional[Dict[str, Any]]: 页面信息
        """
        query = "SELECT * FROM content_pages WHERE url = %s"
        return await self.fetch_one(query, (url,))
        
    async def get_pending_content_pages(self, batch_size: int = 100) -> List[Dict[str, Any]]:
        """获取待处理的内容页面
        
        Args:
            batch_size: 批次大小
            
        Returns:
            List[Dict[str, Any]]: 页面列表
        """
        query = f"""
            SELECT * FROM content_pages 
            WHERE status = 'pending' 
            AND crawl_status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT {batch_size}
        """
        return await self.fetch_all(query)
        
    async def update_page_status(self, page_id: int, status: str, error_message: str = None) -> bool:
        """更新页面状态
        
        Args:
            page_id: 页面ID
            status: 新状态
            error_message: 错误信息
            
        Returns:
            bool: 是否成功
        """
        try:
            query = """
                UPDATE content_pages 
                SET 
                    status = %s,
                    error_message = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            return await self.execute(query, (status, error_message, page_id))
            
        except Exception as e:
            logger.error(f"更新页面状态失败: {str(e)}")
            return False
            
    async def add_page_feature(self, page_id: int, feature_id: int, value: str) -> Optional[int]:
        """添加页面特征
        
        Args:
            page_id: 页面ID
            feature_id: 特征ID
            value: 特征值
            
        Returns:
            Optional[int]: 页面特征ID
        """
        try:
            query = """
                INSERT INTO page_features (
                    page_id, feature_id, feature_value,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, NOW(), NOW()
                )
            """
            
            if await self.execute(query, (page_id, feature_id, value)):
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加页面特征失败: {str(e)}")
            return None
            
    async def update_feature_stats(self, feature_id: int, hit: bool = True) -> bool:
        """更新特征统计
        
        Args:
            feature_id: 特征ID
            hit: 是否命中
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查询是否存在统计记录
            exists = await self.fetch_one(
                "SELECT id FROM feature_stats WHERE feature_id = %s",
                (feature_id,)
            )
            
            if exists:
                # 更新现有记录
                query = """
                    UPDATE feature_stats 
                    SET 
                        hit_count = hit_count + %s,
                        miss_count = miss_count + %s,
                        last_update = NOW()
                    WHERE feature_id = %s
                """
                return await self.execute(query, (1 if hit else 0, 0 if hit else 1, feature_id))
            else:
                # 创建新记录
                query = """
                    INSERT INTO feature_stats (
                        feature_id, hit_count, miss_count,
                        created_at, last_update
                    ) VALUES (
                        %s, %s, %s, NOW(), NOW()
                    )
                """
                return await self.execute(query, (feature_id, 1 if hit else 0, 0 if hit else 1))
                
        except Exception as e:
            logger.error(f"更新特征统计失败: {str(e)}")
            return False
            
    async def add_dictionary_word(self, word_data: Dict[str, Any]) -> Optional[int]:
        """添加词典词条
        
        Args:
            word_data: 词条数据
            
        Returns:
            Optional[int]: 词条ID
        """
        try:
            # 准备SQL
            columns = ', '.join(word_data.keys())
            placeholders = ', '.join(['%s'] * len(word_data))
            query = f"""
                INSERT INTO dictionaries ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(word_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加词条失败: {str(e)}")
            return None
            
    async def get_dictionary_words(
        self,
        word_type: str = None,
        province: str = None,
        is_enabled: bool = True
    ) -> List[Dict[str, Any]]:
        """获取词典词条
        
        Args:
            word_type: 词条类型
            province: 省份
            is_enabled: 是否启用
            
        Returns:
            List[Dict[str, Any]]: 词条列表
        """
        try:
            # 准备SQL
            conditions = ["1=1"]
            params = []
            
            if word_type:
                conditions.append("type = %s")
                params.append(word_type)
                
            if province:
                conditions.append("province = %s")
                params.append(province)
                
            if is_enabled is not None:
                conditions.append("is_enabled = %s")
                params.append(is_enabled)
                
            query = f"""
                SELECT * FROM dictionaries 
                WHERE {' AND '.join(conditions)}
                ORDER BY type, word
            """
            
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取词条失败: {str(e)}")
            return []
            
    async def get_dictionary_word(self, word: str, word_type: str = None) -> Optional[Dict[str, Any]]:
        """获取词条
        
        Args:
            word: 词条
            word_type: 词条类型
            
        Returns:
            Optional[Dict[str, Any]]: 词条信息
        """
        try:
            # 准备SQL
            conditions = ["word = %s"]
            params = [word]
            
            if word_type:
                conditions.append("type = %s")
                params.append(word_type)
                
            query = f"""
                SELECT * FROM dictionaries 
                WHERE {' AND '.join(conditions)}
                LIMIT 1
            """
            
            return await self.fetch_one(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取词条失败: {str(e)}")
            return None
            
    async def update_dictionary_word(self, word_id: int, word_data: Dict[str, Any]) -> bool:
        """更新词条
        
        Args:
            word_id: 词条ID
            word_data: 词条数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 准备SQL
            set_clause = ', '.join([f"{k} = %s" for k in word_data.keys()])
            query = f"""
                UPDATE dictionaries 
                SET {set_clause}
                WHERE id = %s
            """
            
            # 执行更新
            values = tuple(word_data.values()) + (word_id,)
            return await self.execute(query, values)
            
        except Exception as e:
            logger.error(f"更新词条失败: {str(e)}")
            return False
            
    async def update_word_frequency(self, word: str, word_type: str, increment: int = 1) -> bool:
        """更新词条频率
        
        Args:
            word: 词条
            word_type: 词条类型
            increment: 增量
            
        Returns:
            bool: 是否成功
        """
        try:
            query = """
                UPDATE dictionaries 
                SET 
                    frequency = frequency + %s,
                    last_used = NOW()
                WHERE word = %s AND type = %s
            """
            return await self.execute(query, (increment, word, word_type))
            
        except Exception as e:
            logger.error(f"更新词条频率失败: {str(e)}")
            return False
            
    async def get_word_frequency(self, word: str, word_type: str) -> int:
        """获取词条频率
        
        Args:
            word: 词条
            word_type: 词条类型
            
        Returns:
            int: 词条频率
        """
        try:
            query = """
                SELECT frequency 
                FROM dictionaries 
                WHERE word = %s AND type = %s
            """
            result = await self.fetch_one(query, (word, word_type))
            return result['frequency'] if result else 0
            
        except Exception as e:
            logger.error(f"获取词条频率失败: {str(e)}")
            return 0
            
    async def get_high_frequency_words(
        self,
        word_type: str = None,
        province: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取高频词条
        
        Args:
            word_type: 词条类型
            province: 省份
            limit: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 词条列表
        """
        try:
            # 准备SQL
            conditions = ["is_enabled = TRUE"]
            params = []
            
            if word_type:
                conditions.append("type = %s")
                params.append(word_type)
                
            if province:
                conditions.append("province = %s")
                params.append(province)
                
            query = f"""
                SELECT * FROM dictionaries 
                WHERE {' AND '.join(conditions)}
                ORDER BY frequency DESC, last_used DESC
                LIMIT {limit}
            """
            
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取高频词条失败: {str(e)}")
            return []
        
    async def add_site_feature(self, feature_type: str, selector: str, confidence: float, description: str, site_id: int) -> Optional[int]:
        """添加网站特征
        
        Args:
            feature_type: 特征类型
            selector: 选择器
            confidence: 置信度
            description: 描述
            site_id: 网站ID
            
        Returns:
            Optional[int]: 特征ID
        """
        try:
            feature_data = {
                'feature_type': feature_type,
                'feature_value': selector,
                'confidence': confidence,
                'description': description,
                'site_id': site_id,
                'is_active': True,
                'is_verified': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 准备SQL
            columns = ', '.join(feature_data.keys())
            placeholders = ', '.join(['%s'] * len(feature_data))
            query = f"""
                INSERT INTO site_features ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(feature_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加网站特征失败: {str(e)}")
            return None
            
    async def add_page_section(self, section_type: str, selector: str, confidence: float, page_id: int) -> Optional[int]:
        """添加页面区块
        
        Args:
            section_type: 区块类型
            selector: 选择器
            confidence: 置信度
            page_id: 页面ID
            
        Returns:
            Optional[int]: 区块ID
        """
        try:
            section_data = {
                'section_type': section_type,
                'selector': selector,
                'confidence': confidence,
                'page_id': page_id,
                'is_active': True,
                'is_verified': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            # 准备SQL
            columns = ', '.join(section_data.keys())
            placeholders = ', '.join(['%s'] * len(section_data))
            query = f"""
                INSERT INTO page_sections ({columns})
                VALUES ({placeholders})
            """
            
            # 执行插入
            if await self.execute(query, tuple(section_data.values())):
                # 获取插入的ID
                result = await self.fetch_one("SELECT LAST_INSERT_ID() as id")
                return result['id'] if result else None
                
            return None
            
        except Exception as e:
            logger.error(f"添加页面区块失败: {str(e)}")
            return None

    async def create_site(self, name: str, url: str, site_type: str, description: str, status: str) -> GovernmentSite:
        """创建政府网站记录
        
        Args:
            name: 网站名称
            url: 网站URL
            site_type: 网站类型
            description: 网站描述
            status: 网站状态
            
        Returns:
            GovernmentSite: 创建的网站记录
        """
        async with self._session_factory() as session:
            try:
                # 检查是否已存在
                stmt = select(GovernmentSite).where(GovernmentSite.url == url)
                result = await session.execute(stmt)
                existing_site = result.scalar_one_or_none()
                
                if existing_site:
                    logger.info(f"网站已存在: {url}")
                    return existing_site
                
                # 创建新网站
                site = GovernmentSite(
                    title=name,
                    url=url,
                    type=site_type,
                    description=description,
                    status=status,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(site)
                await session.commit()
                await session.refresh(site)
                
                logger.info(f"创建网站成功: {name} - {url}")
                return site
                
            except Exception as e:
                await session.rollback()
                logger.error(f"创建网站失败: {str(e)}")
                raise
    
    async def create_page(self, site_id: int, url: str, title: str, status: str) -> ContentPage:
        """创建内容页面记录
        
        Args:
            site_id: 网站ID
            url: 页面URL
            title: 页面标题
            status: 页面状态
            
        Returns:
            ContentPage: 创建的页面记录
        """
        async with self._session_factory() as session:
            try:
                # 检查是否已存在
                stmt = select(ContentPage).where(ContentPage.url == url)
                result = await session.execute(stmt)
                existing_page = result.scalar_one_or_none()
                
                if existing_page:
                    logger.info(f"页面已存在: {url}")
                    return existing_page
                
                # 创建新页面
                page = ContentPage(
                    site_id=site_id,
                    url=url,
                    title=title,
                    status=status,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(page)
                await session.commit()
                await session.refresh(page)
                
                logger.info(f"创建页面成功: {title} - {url}")
                return page
                
            except Exception as e:
                await session.rollback()
                logger.error(f"创建页面失败: {str(e)}")
                raise

    async def create_site_feature(self, site_id: int, feature_type: str, selector: str, confidence: float, description: str) -> SiteFeature:
        """创建网站特征记录
        
        Args:
            site_id: 网站ID
            feature_type: 特征类型
            selector: CSS选择器
            confidence: 置信度
            description: 特征描述
            
        Returns:
            SiteFeature: 创建的特征记录
        """
        async with self._session_factory() as session:
            try:
                # 检查是否已存在
                stmt = select(SiteFeature).where(
                    SiteFeature.site_id == site_id,
                    SiteFeature.feature_type == feature_type,
                    SiteFeature.feature_value == selector
                )
                result = await session.execute(stmt)
                existing_feature = result.scalar_one_or_none()
                
                if existing_feature:
                    logger.info(f"特征已存在: {feature_type} - {selector}")
                    return existing_feature
                
                # 创建新特征
                feature = SiteFeature(
                    site_id=site_id,
                    feature_type=feature_type,
                    feature_value=selector,  # 使用 feature_value 而不是 selector
                    confidence=confidence,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(feature)
                await session.commit()
                await session.refresh(feature)
                
                logger.info(f"创建特征成功: {feature_type} - {selector}")
                return feature
                
            except Exception as e:
                await session.rollback()
                logger.error(f"创建特征失败: {str(e)}")
                raise

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()

    async def get_active_features(self, site_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取活跃特征
        
        Args:
            site_id: 网站ID，如果为None则获取所有活跃特征
            
        Returns:
            List[Dict[str, Any]]: 特征列表
        """
        try:
            # 构建基础查询
            query = """
                SELECT 
                    sf.*,
                    fs.hit_count,
                    fs.miss_count,
                    fs.last_used,
                    fs.importance
                FROM site_features sf
                LEFT JOIN feature_stats fs ON fs.feature_id = sf.id
                WHERE sf.is_active = TRUE
            """
            
            params = []
            
            # 添加网站过滤
            if site_id is not None:
                query += " AND sf.site_id = %s"
                params.append(site_id)
                
            # 添加排序
            query += " ORDER BY sf.feature_type, sf.feature_category"
            
            # 执行查询
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取活跃特征失败: {str(e)}")
            return []
            
    async def get_active_page_features(self, page_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取活跃的页面特征
        
        Args:
            page_id: 页面ID，如果为None则获取所有活跃特征
            
        Returns:
            List[Dict[str, Any]]: 特征列表
        """
        try:
            # 构建查询
            query = """
                SELECT 
                    pf.*,
                    cp.url as page_url,
                    sf.feature_type,
                    sf.feature_category
                FROM page_features pf
                LEFT JOIN content_pages cp ON pf.page_id = cp.id
                LEFT JOIN site_features sf ON pf.feature_id = sf.id
                WHERE pf.is_active = TRUE
            """
            
            params = []
            if page_id is not None:
                query += " AND pf.page_id = %s"
                params.append(page_id)
                
            query += " ORDER BY sf.feature_type, sf.feature_category"
            
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取活跃页面特征失败: {str(e)}")
            return []
            
    async def get_active_page_sections(self, page_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取活跃的页面区块
        
        Args:
            page_id: 页面ID，如果为None则获取所有活跃区块
            
        Returns:
            List[Dict[str, Any]]: 区块列表
        """
        try:
            # 构建查询
            query = """
                SELECT 
                    ps.*,
                    cp.url as page_url
                FROM page_sections ps
                LEFT JOIN content_pages cp ON ps.page_id = cp.id
                WHERE ps.is_active = TRUE
            """
            
            params = []
            if page_id is not None:
                query += " AND ps.page_id = %s"
                params.append(page_id)
                
            query += " ORDER BY ps.section_type, ps.confidence DESC"
            
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取活跃页面区块失败: {str(e)}")
            return []
            
    async def get_feature_stats(self, feature_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取特征统计信息
        
        Args:
            feature_id: 特征ID，如果为None则获取所有统计信息
            
        Returns:
            List[Dict[str, Any]]: 统计信息列表
        """
        try:
            # 构建查询
            query = """
                SELECT 
                    fs.*,
                    sf.feature_type,
                    sf.feature_category,
                    sf.feature_value
                FROM feature_stats fs
                LEFT JOIN site_features sf ON fs.feature_id = sf.id
            """
            
            params = []
            if feature_id is not None:
                query += " WHERE fs.feature_id = %s"
                params.append(feature_id)
                
            query += " ORDER BY fs.hit_count DESC"
            
            return await self.fetch_all(query, tuple(params))
            
        except Exception as e:
            logger.error(f"获取特征统计失败: {str(e)}")
            return []

    async def save_page_analysis(self, page_id: int, page_type: str, features: Dict[str, Any]) -> bool:
        """保存页面分析结果
        
        Args:
            page_id: 页面ID
            page_type: 页面类型
            features: 页面特征
            
        Returns:
            bool: 是否成功
        """
        try:
            # 更新页面类型
            await self.execute(
                "UPDATE content_pages SET page_type = %s WHERE id = %s",
                (page_type, page_id)
            )
            
            # 保存页面特征
            for feature_type, feature_value in features.items():
                feature_data = {
                    'page_id': page_id,
                    'feature_type': feature_type,
                    'feature_value': json.dumps(feature_value) if isinstance(feature_value, (dict, list)) else str(feature_value),
                    'created_at': datetime.now()
                }
                
                columns = ', '.join(feature_data.keys())
                placeholders = ', '.join(['%s'] * len(feature_data))
                query = f"""
                    INSERT INTO page_features ({columns})
                    VALUES ({placeholders})
                """
                
                await self.execute(query, tuple(feature_data.values()))
                
            return True
            
        except Exception as e:
            logger.error(f"保存页面分析结果失败 [id={page_id}]: {str(e)}")
            return False
            
    async def update_page_status(self, page_id: int, status: str, error_message: Optional[str] = None) -> bool:
        """更新页面状态
        
        Args:
            page_id: 页面ID
            status: 状态
            error_message: 错误信息
            
        Returns:
            bool: 是否成功
        """
        try:
            query = """
                UPDATE content_pages 
                SET status = %s, 
                    error_message = %s,
                    updated_at = %s
                WHERE id = %s
            """
            
            return await self.execute(
                query,
                (status, error_message, datetime.now(), page_id)
            )
            
        except Exception as e:
            logger.error(f"更新页面状态失败 [id={page_id}]: {str(e)}")
            return False
            
    async def get_pending_pages(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """获取待处理的页面
        
        Args:
            batch_size: 批次大小
            
        Returns:
            List[Dict[str, Any]]: 页面列表
        """
        try:
            query = f"""
                SELECT * FROM content_pages 
                WHERE status = 'pending'
                AND error_count < {settings.CRAWLER_CONFIG['max_retry_count']}
                ORDER BY priority DESC, created_at ASC
                LIMIT {batch_size}
            """
            
            return await self.fetch_all(query)
            
        except Exception as e:
            logger.error(f"获取待处理页面失败: {str(e)}")
            return []

