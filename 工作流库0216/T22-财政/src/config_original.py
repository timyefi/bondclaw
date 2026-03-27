"""
财政数据整合导入配置文件
"""

# 数据库表名
TABLE_NAME = 'china_fiscal_data_2017_2024'

# Excel文件路径
EXCEL_FILE_PATH = '/data/项目/快速处理/2025/财政/17-24chinafiscaldata.xlsx'

# 数据库配置
DATABASE_CONFIG = {
    'host': 'rm-uf6c8yi6zdq6ea7p1qo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'hz_work',
    'password': 'Hzinsights2015',
    'database': 'bond',
    'charset': 'utf8mb4',
    'pool_recycle': 3600,
    'pool_size': 10,
    'max_overflow': 20
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': {
        'file': {
            'filename': 'fiscal_data_import.log',
            'max_bytes': 10485760,  # 10MB
            'backup_count': 5
        }
    }
}

# 数据处理配置
PROCESSING_CONFIG = {
    'batch_size': 1000,  # 批量插入大小
    'null_values': ['--', '', 'NaN', 'nan', 'NULL'],  # 空值定义
    'date_format': '%Y-%m-%d',  # 日期格式
    'encoding': 'utf-8'  # 文件编码
}

# 省级行政区列表（用于地域级别判断）
PROVINCES = [
    '北京', '天津', '上海', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南',
    '广东', '海南', '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门', '中国'
]

# 数据质量检查配置
QUALITY_CHECKS = {
    'required_columns': [
        '地域', 'YY地域', '负债率(%)', '负债率(宽口径)(%)', '债务率(%)',
        '债务率(宽口径)(%)', '城投债余额(亿)', '地方政府债余额(亿)',
        '地方政府债限额(亿)', '城投有息负债(亿)', '非标融资余额(亿)',
        '非标融资余额/城投有息负债(%)', '人民币: 各项存款余额/城投有息负债(%)',
        '城投有息负债: 三年复合增速(%)', 'GDP(亿)', 'GDP增速(%)', '人均GDP(元)',
        '房地产投资(亿)', '城镇居民人均可支配收入(元)',
        '商品房销售面积(万平方米)', '商品房销售金额(亿)',
        '城镇居民人均消费性支出(元)', '农村居民人均消费性支出(元)',
        '工业增加量(亿)', '本外币: 各项存款余额(亿)',
        '本外币: 各项贷款余额(亿)', '地方政府综合财力(亿)',
        '财政自给率(%)', '一般公共预算收入(亿)', '一般公共预算支出(亿)',
        '税收收入(亿)', '税收收入占比(%)', '政府性基金收入(亿)',
        '政府性基金支出(亿)', '国有土地权出让收入(亿)',
        '国有土地权出让收入: 三年复合增速(%)',
        '国有土地权出让收入/一般公共预算收入(%)', '常住人口(万)'
    ],
    'year_range': (2017, 2024),  # 年份范围
    'max_null_percentage': 50,  # 最大空值百分比
    'min_records_per_year': 100  # 每年最小记录数
}

# 错误处理配置
ERROR_HANDLING = {
    'continue_on_error': True,  # 遇到错误是否继续
    'max_retries': 3,  # 最大重试次数
    'retry_delay': 1,  # 重试延迟（秒）
    'log_errors': True,  # 是否记录错误
    'error_log_file': 'fiscal_data_import_errors.log'  # 错误日志文件
}