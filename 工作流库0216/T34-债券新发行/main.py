# -*- coding: utf-8 -*-
"""
T34 - 债券新发行系统

主程序入口，执行债券到期数据采集和债券新发行数据采集。

使用方法:
    python main.py [--maturity] [--issue] [--all]

参数:
    --maturity: 仅执行债券到期数据采集
    --issue: 仅执行债券新发行数据采集
    --all: 执行全部采集任务（默认）
"""

import os
import sys
import argparse
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 导入配置
from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    BOND_MATURITY_CONFIG, BOND_ISSUE_CONFIG,
    validate_config, print_config_summary
)

# 数据库
import sqlalchemy
from sqlalchemy import create_engine, text
import sqlalchemy.pool as pool


# 日志配置
def setup_logging():
    """配置日志系统"""
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"bond_new_issue_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger('BondNewIssue')


logger = setup_logging()


def get_db_engine():
    """创建数据库连接引擎"""
    connection_string = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    return create_engine(connection_string, poolclass=pool.NullPool, pool_recycle=3600)


def run_maturity_collection(engine):
    """
    执行债券到期数据采集

    Args:
        engine: 数据库引擎

    Returns:
        执行结果字典
    """
    result = {
        'task': 'maturity_collection',
        'status': 'unknown',
        'start_time': datetime.now().isoformat(),
        'records': 0,
        'message': ''
    }

    try:
        logger.info("=" * 50)
        logger.info("开始执行债券到期数据采集")
        logger.info("=" * 50)

        # 检查Wind API是否可用
        try:
            from WindPy import w
            w.start()
            logger.info("Wind API初始化成功")
        except ImportError:
            result['status'] = 'skipped'
            result['message'] = 'Wind API不可用，跳过债券到期数据采集'
            logger.warning(result['message'])
            return result

        # 获取日期范围
        from datetime import timedelta
        import pandas as pd

        current_date = datetime.now()
        days_ahead = BOND_MATURITY_CONFIG['days_ahead']
        end_date = current_date + timedelta(days=days_ahead)
        dt0 = current_date.strftime('%Y-%m-%d')
        dt1 = end_date.strftime('%Y-%m-%d')

        logger.info(f"采集日期范围: {dt0} ~ {dt1}")

        # 查询已有日期
        query = f"SELECT DISTINCT dt FROM {BOND_MATURITY_CONFIG['table_name']} WHERE dt >= '{dt0}'"
        try:
            with engine.connect() as conn:
                existing_df = pd.read_sql(query, conn)
            existing_dates = set(pd.to_datetime(existing_df['dt']).values)
        except Exception:
            existing_dates = set()

        logger.info(f"已有数据日期数: {len(existing_dates)}")

        # 债券类型配置
        from config import BOND_TYPES

        total_records = 0

        # 循环处理每个日期
        for dt in pd.date_range(start=dt0, end=dt1):
            if dt in existing_dates:
                logger.info(f"跳过 {dt.strftime('%Y-%m-%d')} (已有数据)")
                continue

            dt_str = dt.strftime('%Y-%m-%d')
            logger.info(f"处理日期: {dt_str}")

            # 获取每种债券类型的数据
            for bond_type_code, bond_type_name, is_urban in BOND_TYPES:
                conceptbond = 'urbaninvestmentbonds(wind)' if is_urban == '是' else 'default'

                error_code, wsd_data = w.wset(
                    "bondissuanceandmaturity",
                    f"startdate={dt_str};enddate={dt_str};frequency=day;maingrade=all;zxgrade=all;"
                    f"datetype=startdate;duedatetype=byactualpaymentdate;type=default;publishlimited=all;"
                    f"bondtype={bond_type_code};dealmarket=allmarkets;conceptbond={conceptbond};"
                    f"field=startdate,enddate,totalredemption",
                    usedf=True
                )

                if error_code == 0 and wsd_data is not None and not wsd_data.empty:
                    wsd_data['bondtype'] = bond_type_name
                    wsd_data['isurbaninvestmentbonds'] = is_urban
                    wsd_data.rename(columns={'startdate': 'dt'}, inplace=True)
                    if 'enddate' in wsd_data.columns:
                        wsd_data.drop(columns=['enddate'], inplace=True)

                    # TODO: 实现数据入库
                    total_records += len(wsd_data)
                    logger.info(f"  {bond_type_name}（城投:{is_urban}）: {len(wsd_data)}条")

        result['status'] = 'success'
        result['records'] = total_records
        result['message'] = f'采集完成，共 {total_records} 条记录'
        logger.info(result['message'])

    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['traceback'] = traceback.format_exc()
        logger.error(f"债券到期数据采集失败: {e}")
        logger.error(traceback.format_exc())

    finally:
        result['end_time'] = datetime.now().isoformat()

    return result


def run_issue_collection(engine):
    """
    执行债券新发行数据采集

    Args:
        engine: 数据库引擎

    Returns:
        执行结果字典
    """
    result = {
        'task': 'issue_collection',
        'status': 'unknown',
        'start_time': datetime.now().isoformat(),
        'records': 0,
        'message': ''
    }

    try:
        logger.info("=" * 50)
        logger.info("开始执行债券新发行数据采集")
        logger.info("=" * 50)

        # 检查iFinD API是否可用
        try:
            from iFinDPy import THS_iFinDLogin, THS_DR

            username = os.environ.get('IFIND_USERNAME', '')
            password = os.environ.get('IFIND_PASSWORD', '')

            if not username or not password:
                result['status'] = 'skipped'
                result['message'] = 'iFinD API凭证未配置，跳过债券新发行数据采集'
                logger.warning(result['message'])
                return result

            login_result = THS_iFinDLogin(username, password)
            logger.info(f"iFinD登录结果: {login_result}")

        except ImportError:
            result['status'] = 'skipped'
            result['message'] = 'iFinD API不可用，跳过债券新发行数据采集'
            logger.warning(result['message'])
            return result

        # 获取日期范围
        from datetime import timedelta

        current_date = datetime.now()
        days_start = BOND_ISSUE_CONFIG['days_start']
        days_end = BOND_ISSUE_CONFIG['days_end']
        start_date = current_date + timedelta(days=days_start)
        end_date = current_date + timedelta(days=days_end)
        dt0 = start_date.strftime('%Y%m%d')
        dt1 = end_date.strftime('%Y%m%d')

        logger.info(f"采集日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

        # 调用iFinD API
        from config import IFIND_BOND_TYPES

        df = THS_DR(
            'p04524',
            f'sdate={dt0};edate={dt1};zqlx={IFIND_BOND_TYPES};'
            f'sclx=0;jglx=0;datetype=5;fxqx=0;ztpj=0;hy=0;qyxz=0;dq=0;gnfl=0',
            'jydm:Y,jydm_mc:Y,p04524_f005:Y,p04524_f006:Y,p04524_f009:Y,p04524_f029:Y,p04524_f063:Y',
            'format:dataframe'
        )

        if df is None or df.data is None:
            result['status'] = 'success'
            result['message'] = '未获取到数据'
            logger.info(result['message'])
            return result

        df = df.data

        if df.empty:
            result['status'] = 'success'
            result['message'] = '数据为空'
            logger.info(result['message'])
            return result

        # 重命名列
        df.columns = ['trade_code', 'sec_name', 'dt', 'planissueamount', 'bondterm', 'bondtype', 'isurbaninvestmentbonds']

        logger.info(f"获取数据: {len(df)}条")

        # TODO: 实现数据入库和去重

        result['status'] = 'success'
        result['records'] = len(df)
        result['message'] = f'采集完成，共 {len(df)} 条记录'
        logger.info(result['message'])

    except Exception as e:
        result['status'] = 'failed'
        result['message'] = str(e)
        result['traceback'] = traceback.format_exc()
        logger.error(f"债券新发行数据采集失败: {e}")
        logger.error(traceback.format_exc())

    finally:
        result['end_time'] = datetime.now().isoformat()

    return result


def main():
    """主程序入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='债券新发行数据采集系统')
    parser.add_argument('--maturity', action='store_true', help='仅执行债券到期数据采集')
    parser.add_argument('--issue', action='store_true', help='仅执行债券新发行数据采集')
    parser.add_argument('--all', action='store_true', help='执行全部采集任务（默认）')
    args = parser.parse_args()

    # 确定执行模式
    run_all = not (args.maturity or args.issue) or args.all

    logger.info("=" * 60)
    logger.info("T34 债券新发行系统启动")
    logger.info("=" * 60)

    # 打印配置摘要
    print_config_summary()

    # 验证配置
    if not validate_config():
        logger.warning("配置验证未通过，部分功能可能不可用")

    # 创建数据库连接
    try:
        engine = get_db_engine()
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return {'status': 'failed', 'message': '数据库连接失败'}

    results = []

    # 执行任务
    if run_all or args.maturity:
        result = run_maturity_collection(engine)
        results.append(result)

    if run_all or args.issue:
        result = run_issue_collection(engine)
        results.append(result)

    # 汇总结果
    summary = {
        'run_time': datetime.now().isoformat(),
        'total_tasks': len(results),
        'success_count': sum(1 for r in results if r['status'] == 'success'),
        'failed_count': sum(1 for r in results if r['status'] == 'failed'),
        'skipped_count': sum(1 for r in results if r['status'] == 'skipped'),
        'results': results
    }

    logger.info("=" * 60)
    logger.info(f"执行摘要: 成功 {summary['success_count']}, 失败 {summary['failed_count']}, 跳过 {summary['skipped_count']}")
    logger.info("=" * 60)

    return summary


if __name__ == '__main__':
    result = main()

    # 输出JSON格式结果
    print("\n执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
