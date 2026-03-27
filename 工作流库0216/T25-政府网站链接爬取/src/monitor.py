"""监控和报警模块"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import threading
import queue
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, DateTime, JSON, MetaData
from sqlalchemy.sql import select, insert, update
from configs.settings import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS
from utils.log_manager import log_manager

logger = log_manager.get_logger('monitor')

class Monitor:
    """监控器"""
    
    def __init__(self):
        """初始化"""
        # 数据库连接
        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URI,
            **SQLALCHEMY_ENGINE_OPTIONS
        )
        self.metadata = MetaData()
        
        # 定义监控记录表
        self.monitor_table = Table(
            'monitor_records',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('metric_name', String(255)),
            Column('metric_value', Float),
            Column('timestamp', DateTime, default=datetime.now),
            Column('status', String(50)),
            Column('details', JSON),
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
        
        # 定义报警记录表
        self.alert_table = Table(
            'alert_records',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('alert_type', String(50)),
            Column('severity', String(50)),
            Column('message', String(1000)),
            Column('timestamp', DateTime, default=datetime.now),
            Column('status', String(50)),
            Column('handled_by', String(255)),
            Column('handled_at', DateTime),
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci'
        )
        
        # 创建表
        self.metadata.create_all(self.engine)
        
        # 报警队列
        self.alert_queue = queue.Queue()
        
        # 报警处理线程
        self.alert_thread = threading.Thread(
            target=self._process_alerts,
            daemon=True
        )
        self.alert_thread.start()
        
        # 监控指标
        self.metrics = {}
        
        # 报警规则
        self.alert_rules = {}
        
        # 报警通知配置
        self.notification_config = {
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'recipients': []
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'headers': {},
                'template': ''
            }
        }
        
    def add_metric(self, name: str, func: Callable, 
                  interval: int = 60, threshold: float = None):
        """添加监控指标
        
        Args:
            name: 指标名称
            func: 指标计算函数
            interval: 采集间隔(秒)
            threshold: 阈值
        """
        self.metrics[name] = {
            'func': func,
            'interval': interval,
            'threshold': threshold,
            'last_check': None,
            'last_value': None
        }
        
    def add_alert_rule(self, name: str, condition: Callable,
                      severity: str = 'warning',
                      message_template: str = None):
        """添加报警规则
        
        Args:
            name: 规则名称
            condition: 触发条件函���
            severity: 严重程度
            message_template: 消息模板
        """
        self.alert_rules[name] = {
            'condition': condition,
            'severity': severity,
            'message_template': message_template,
            'last_trigger': None
        }
        
    def configure_notification(self, method: str, config: Dict[str, Any]):
        """配置通知方式
        
        Args:
            method: 通知方式
            config: 配置信息
        """
        if method in self.notification_config:
            self.notification_config[method].update(config)
        
    def check_metrics(self):
        """检查所有监控指标"""
        try:
            current_time = datetime.now()
            
            for name, metric in self.metrics.items():
                # 检查是否需要采集
                if (metric['last_check'] is None or
                    (current_time - metric['last_check']).total_seconds() >= metric['interval']):
                    
                    # 采集指标
                    try:
                        value = metric['func']()
                        metric['last_value'] = value
                        metric['last_check'] = current_time
                        
                        # 记录到数据库
                        status = 'normal'
                        if metric['threshold'] is not None:
                            if value > metric['threshold']:
                                status = 'exceeded'
                                
                        with self.engine.connect() as conn:
                            conn.execute(
                                self.monitor_table.insert().values(
                                    metric_name=name,
                                    metric_value=value,
                                    timestamp=current_time,
                                    status=status,
                                    details={'threshold': metric['threshold']}
                                )
                            )
                            conn.commit()
                            
                        # 检查报警规则
                        self._check_alert_rules(name, value)
                        
                    except Exception as e:
                        logger.error(f"采集指标 {name} 失败: {str(e)}")
                        
        except Exception as e:
            logger.error(f"检查监控指标失败: {str(e)}")
            
    def _check_alert_rules(self, metric_name: str, value: float):
        """检查报警规则
        
        Args:
            metric_name: 指标名称
            value: 指标值
        """
        try:
            current_time = datetime.now()
            
            for name, rule in self.alert_rules.items():
                try:
                    # 检查是否触发
                    if rule['condition'](metric_name, value):
                        # 检查冷却时间
                        if (rule['last_trigger'] is None or
                            (current_time - rule['last_trigger']).total_seconds() >= 300):
                            
                            # 生成报警消息
                            message = rule['message_template'].format(
                                metric_name=metric_name,
                                value=value,
                                threshold=self.metrics[metric_name]['threshold']
                            ) if rule['message_template'] else \
                               f"指标 {metric_name} 当前值 {value} 超过阈值 {self.metrics[metric_name]['threshold']}"
                            
                            # 创建报警记录
                            with self.engine.connect() as conn:
                                conn.execute(
                                    self.alert_table.insert().values(
                                        alert_type=name,
                                        severity=rule['severity'],
                                        message=message,
                                        timestamp=current_time,
                                        status='new'
                                    )
                                )
                                conn.commit()
                                
                            # 发送报警
                            self.alert_queue.put({
                                'type': name,
                                'severity': rule['severity'],
                                'message': message,
                                'timestamp': current_time
                            })
                            
                            rule['last_trigger'] = current_time
                            
                except Exception as e:
                    logger.error(f"检查报警规则 {name} 失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"检查报警规则失败: {str(e)}")
            
    def _process_alerts(self):
        """处理报警队列"""
        while True:
            try:
                # 获取报警信息
                alert = self.alert_queue.get()
                
                # 发送邮件通知
                if self.notification_config['email']['enabled']:
                    self._send_email_alert(alert)
                    
                # 发送Webhook通知
                if self.notification_config['webhook']['enabled']:
                    self._send_webhook_alert(alert)
                    
            except Exception as e:
                logger.error(f"处理报警失败: {str(e)}")
                
            finally:
                self.alert_queue.task_done()
                
    def _send_email_alert(self, alert: Dict[str, Any]):
        """发送邮件报警
        
        Args:
            alert: 报警信息
        """
        try:
            config = self.notification_config['email']
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = config['username']
            msg['To'] = ', '.join(config['recipients'])
            msg['Subject'] = f"[{alert['severity'].upper()}] {alert['type']}"
            
            body = f"""
            报警类型: {alert['type']}
            严重程度: {alert['severity']}
            报警时间: {alert['timestamp']}
            报警内容: {alert['message']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['username'], config['password'])
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"发送邮件报警失败: {str(e)}")
            
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """发送Webhook报警
        
        Args:
            alert: 报警信息
        """
        try:
            config = self.notification_config['webhook']
            
            # 准备请求数据
            if config['template']:
                data = config['template'].format(**alert)
            else:
                data = json.dumps(alert)
                
            # 发送请求
            response = requests.post(
                config['url'],
                headers=config['headers'],
                data=data,
                timeout=5
            )
            
            if response.status_code != 200:
                raise Exception(f"Webhook返回状态码: {response.status_code}")
                
        except Exception as e:
            logger.error(f"发送Webhook报警失败: {str(e)}")
            
    def get_metrics(self, start_time: datetime = None,
                   end_time: datetime = None) -> List[Dict[str, Any]]:
        """获取监控指标数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict[str, Any]]: 指标数据列表
        """
        try:
            query = select(self.monitor_table)
            
            if start_time:
                query = query.where(self.monitor_table.c.timestamp >= start_time)
            if end_time:
                query = query.where(self.monitor_table.c.timestamp <= end_time)
                
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [dict(row) for row in result]
                
        except Exception as e:
            logger.error(f"获取监控指标数据失败: {str(e)}")
            return []
            
    def get_alerts(self, start_time: datetime = None,
                  end_time: datetime = None,
                  status: str = None) -> List[Dict[str, Any]]:
        """获取报警记录
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            status: 状态
            
        Returns:
            List[Dict[str, Any]]: 报警记录列表
        """
        try:
            query = select(self.alert_table)
            
            if start_time:
                query = query.where(self.alert_table.c.timestamp >= start_time)
            if end_time:
                query = query.where(self.alert_table.c.timestamp <= end_time)
            if status:
                query = query.where(self.alert_table.c.status == status)
                
            with self.engine.connect() as conn:
                result = conn.execute(query)
                return [dict(row) for row in result]
                
        except Exception as e:
            logger.error(f"获取报警记录失败: {str(e)}")
            return []
            
    def handle_alert(self, alert_id: int, handler: str):
        """处理报警
        
        Args:
            alert_id: 报警ID
            handler: 处理人
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    self.alert_table.update().where(
                        self.alert_table.c.id == alert_id
                    ).values(
                        status='handled',
                        handled_by=handler,
                        handled_at=datetime.now()
                    )
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"处理报警失败: {str(e)}")
            
    def export_metrics(self, start_time: datetime = None,
                      end_time: datetime = None,
                      format: str = 'json') -> str:
        """导出监控指标数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            format: 导出格式
            
        Returns:
            str: 导出文件路径
        """
        try:
            # 获取数据
            metrics = self.get_metrics(start_time, end_time)
            
            if not metrics:
                return ''
                
            # 导出文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format == 'json':
                filename = f'metrics_{timestamp}.json'
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, ensure_ascii=False, indent=2)
                    
            elif format == 'csv':
                filename = f'metrics_{timestamp}.csv'
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
                    writer.writeheader()
                    writer.writerows(metrics)
                    
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
            return filename
            
        except Exception as e:
            logger.error(f"导出监控指标数据失败: {str(e)}")
            return '' 