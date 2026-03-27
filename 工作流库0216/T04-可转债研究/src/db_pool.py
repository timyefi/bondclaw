import os
import yaml
import time
import queue
import pymysql
import threading
from typing import Dict, Optional

class DatabaseConnectionPool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
            return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.config = self._load_config()
            self.pool_config = self.config.get('pool', {})
            self.connections = queue.Queue(maxsize=self.pool_config.get('max_connections', 10))
            self.active_connections = 0
            self.initialized = True
            self._fill_pool()
    
    def _load_config(self) -> Dict:
        """加载数据库配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'database.yml')
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _create_connection(self, use_backup: bool = False) -> pymysql.Connection:
        """创建新的数据库连接"""
        db_config = self.config['backup' if use_backup else 'primary'].copy()
        if 'cursorclass' in db_config:
            db_config['cursorclass'] = getattr(pymysql.cursors, db_config['cursorclass'])
        
        retry_count = self.pool_config.get('retry_count', 3)
        retry_delay = self.pool_config.get('retry_delay', 1)
        
        for attempt in range(retry_count):
            try:
                return pymysql.connect(**db_config)
            except Exception as e:
                if attempt == retry_count - 1:
                    if not use_backup:
                        print(f"主数据库连接失败，尝试连接备用数据库: {str(e)}")
                        return self._create_connection(use_backup=True)
                    raise
                time.sleep(retry_delay)
    
    def _fill_pool(self):
        """填充连接池到最小连接数"""
        min_connections = self.pool_config.get('min_connections', 2)
        while self.active_connections < min_connections:
            try:
                conn = self._create_connection()
                self.connections.put(conn)
                self.active_connections += 1
            except Exception as e:
                print(f"填充连接池失败: {str(e)}")
                break
    
    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        try:
            # 尝试从池中获取连接
            conn = self.connections.get_nowait()
            
            # 验证连接是否有效
            try:
                conn.ping(reconnect=True)
                return conn
            except:
                self.active_connections -= 1
                conn = self._create_connection()
                self.active_connections += 1
                return conn
                
        except queue.Empty:
            # 如果池为空且未达到最大连接数，创建新连接
            if self.active_connections < self.pool_config.get('max_connections', 10):
                conn = self._create_connection()
                self.active_connections += 1
                return conn
            else:
                # 等待可用连接
                return self.connections.get()
    
    def return_connection(self, conn: pymysql.Connection):
        """归还数据库连接到连接池"""
        try:
            # 验证连接是否有效
            conn.ping(reconnect=False)
            self.connections.put(conn)
        except:
            # 连接无效，关闭并创建新连接
            try:
                conn.close()
            except:
                pass
            self.active_connections -= 1
            self._fill_pool()
    
    def close_all(self):
        """关闭所有连接"""
        while not self.connections.empty():
            conn = self.connections.get_nowait()
            try:
                conn.close()
            except:
                pass
        self.active_connections = 0

class DatabaseConnection:
    """数据库连接上下文管理器"""
    def __init__(self):
        self.pool = DatabaseConnectionPool()
        self.conn = None
    
    def __enter__(self) -> pymysql.Connection:
        self.conn = self.pool.get_connection()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.return_connection(self.conn)

# 使用示例
if __name__ == "__main__":
    # 测试连接池
    with DatabaseConnection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM target_code")
            result = cursor.fetchone()
            print(f"target_code表中有 {result['count']} 条记录") 