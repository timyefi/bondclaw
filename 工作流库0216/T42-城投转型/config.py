# -*- coding: utf-8 -*-
"""
城投转型项目配置文件

该配置文件使用环境变量管理敏感信息，确保安全性。
请在运行前设置相应的环境变量。
"""

import os
from pathlib import Path


class Config:
    """项目配置类"""

    def __init__(self):
        # 项目根目录
        self.base_dir = Path(__file__).parent.absolute()

        # 数据库配置 - 使用环境变量
        self.db_host = os.environ.get('DB_HOST', 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com')
        self.db_port = os.environ.get('DB_PORT', '3306')
        self.db_name = os.environ.get('DB_NAME', 'yq')
        self.db_user = os.environ.get('DB_USER', 'hz_work')
        self.db_password = os.environ.get('DB_PASSWORD', '')  # 请设置环境变量 DB_PASSWORD

        # 输出目录配置
        self.output_dir = os.path.join(self.base_dir, 'output')
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.assets_dir = os.path.join(self.base_dir, 'assets')

        # 数据表配置
        self.table_name = '城投平台市场化转型'

        # 发布主体映射
        self.publish_entity_mapping = {
            1: '官方披露',
            2: '企业披露',
            0: '其他',
            3: '其他'
        }

        # 评级等级排序
        self.rating_order = ['AAA', 'AA+', 'AA', 'AA-', 'A']

        # 变更类型说明
        self.change_type_desc = {
            '退出': '城投融资平台完全退出政府融资职能，转型为市场化运作的国有企业',
            '市场化转型': '按照市场化要求建立公司法人治理结构，按照《公司法》、《公司章程》规定开展市场化融资',
            '隐性债务清零': '隐性债务已清零，退出融资平台监管范畴'
        }

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f'mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4'

    def ensure_directories(self):
        """确保所有必要目录存在"""
        for dir_path in [self.output_dir, self.data_dir, self.assets_dir]:
            os.makedirs(dir_path, exist_ok=True)


# 创建全局配置实例
config = Config()


if __name__ == '__main__':
    # 测试配置
    print("项目配置信息:")
    print(f"  数据库主机: {config.db_host}")
    print(f"  数据库端口: {config.db_port}")
    print(f"  数据库名称: {config.db_name}")
    print(f"  数据库用户: {config.db_user}")
    print(f"  输出目录: {config.output_dir}")
    print(f"  数据目录: {config.data_dir}")

    # 检查环境变量
    if not config.db_password:
        print("\n警告: 未设置数据库密码环境变量 DB_PASSWORD")
        print("请在运行前设置: export DB_PASSWORD='your_password'")
