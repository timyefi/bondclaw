"""
ETF Research Utility Module
=====================

Utility functions for ETF research project including:
- Data loading and preprocessing
- Performance calculations
- Visualization helpers
- Table generation
"""

import datetime
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import (
    ETF_DB, BOND_DB, PERFORMANCE_CONFIG, LOGGING_CONFIG,
    OUTPUT_DIR, setup_logging
)

warnings.filterwarnings('ignore')

# ============================================================================
# Logger Setup
# ============================================================================

logger = setup_logging(__name__)


# ============================================================================
# Data Loading Utilities
# ============================================================================

class DataLoader:
    """Data loading utilities for ETF research"""

    def __init__(self, db_config=None):
        """Initialize data loader

        Args:
            db_config: Database configuration, defaults to ETF_DB
        """
        self.db_config = db_config or ETF_DB
        self._engine = None

    @property
    def engine(self) -> Engine:
        """Get database engine (lazy initialization)"""
        if self._engine is None:
            self._engine = create_engine(
                self.db_config.connection_url,
                pool_size=self.db_config.pool_size,
                pool_recycle=self.db_config.pool_recycle
            )
        return self._engine

    def query_df(self, sql: str, params: tuple = None) -> pd.DataFrame:
        """Execute SQL query and return DataFrame

        Args:
            sql: SQL query string
            params: Query parameters

        Returns:
            Query result as DataFrame
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql(text(sql), conn, params=params)
                else:
                    result = pd.read_sql(text(sql), conn)
            return result
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise

    def get_etf_base_info(self, dt: str = None) -> pd.DataFrame:
        """Get ETF base information

        Args:
            dt: Date string (YYYY-MM-DD), defaults to latest date

        Returns:
            DataFrame with ETF base information
        """
        if dt is None:
            sql = """
            SELECT * FROM yq.etf_base_info
            WHERE DT = (SELECT MAX(DT) FROM yq.etf_base_info)
            """
        else:
            sql = """
            SELECT * FROM yq.etf_base_info WHERE DT = :dt
            """
        return self.query_df(sql, (dt,) if dt else None)

    def get_etf_nav_data(self, codes: List[str], start_date: str = None,
                         end_date: str = None) -> pd.DataFrame:
        """Get ETF NAV data

        Args:
            codes: List of ETF codes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with NAV data
        """
        code_list = "','".join(codes)

        sql = f"""
        SELECT TRADE_CODE, DT, NAV, NAV_ADJ, NAV_ACC, CLOSE
        FROM fund.marketinfo
        WHERE TRADE_CODE IN ('{code_list}')
        """

        conditions = []
        params = []

        if start_date:
            conditions.append("DT >= :start_date")
            params.append(start_date)
        if end_date:
            conditions.append("DT <= :end_date")
            params.append(end_date)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        sql += " ORDER BY TRADE_CODE, DT"

        return self.query_df(sql, tuple(params) if params else None)

    def get_etf_unit_data(self, codes: List[str], start_date: str = None,
                          end_date: str = None) -> pd.DataFrame:
        """Get ETF unit/share data

        Args:
            codes: List of ETF codes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with unit data
        """
        code_list = "','".join(codes)

        sql = f"""
        SELECT TRADE_CODE, DT, UNIT_TOTAL, UNIT_ALL
        FROM fund.marketinfo_unit
        WHERE TRADE_CODE IN ('{code_list}')
        """

        conditions = []
        params = []

        if start_date:
            conditions.append("DT >= :start_date")
            params.append(start_date)
        if end_date:
            conditions.append("DT <= :end_date")
            params.append(end_date)

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        sql += " ORDER BY TRADE_CODE, DT"

        return self.query_df(sql, tuple(params) if params else None)

    def get_bond_curve_data(self, start_date: str, end_date: str = None,
                            bond_type: str = None, term: float = None) -> pd.DataFrame:
        """Get bond curve data

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bond_type: Bond type filter
            term: Term filter

        Returns:
            DataFrame with bond curve data
        """
        sql = """
        SELECT * FROM bond.bond_curve
        WHERE dt >= :start_date
        """
        params = [start_date]

        if end_date:
            sql += " AND dt <= :end_date"
            params.append(end_date)
        if bond_type:
            sql += " AND bond_type = :bond_type"
            params.append(bond_type)
        if term:
            sql += " AND term = :term"
            params.append(term)

        sql += " ORDER BY dt"

        return self.query_df(sql, tuple(params))

    def close(self):
        """Close database connection"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================================
# Performance Analysis Utilities
# ============================================================================

class PerformanceAnalyzer:
    """Performance analysis utilities"""

    def __init__(self, config=None):
        """Initialize performance analyzer

        Args:
            config: Performance configuration
        """
        self.config = config or PERFORMANCE_CONFIG

    def calculate_returns(self, nav: pd.Series, annualized: bool = True) -> float:
        """Calculate returns

        Args:
            nav: NAV series
            annualized: Whether to annualize returns

        Returns:
            Returns value
        """
        if len(nav) < 2:
            return 0.0

        total_return = (nav.iloc[-1] / nav.iloc[0]) - 1

        if annualized:
            days = (nav.index[-1] - nav.index[0]).days
            if days > 0:
                total_return = (1 + total_return) ** (365 / days) - 1

        return total_return

    def calculate_volatility(self, returns: pd.Series, annualized: bool = True) -> float:
        """Calculate volatility

        Args:
            returns: Returns series
            annualized: Whether to annualize volatility

        Returns:
            Volatility value
        """
        if len(returns) < 2:
            return 0.0

        vol = returns.std()

        if annualized:
            vol *= np.sqrt(self.config.trading_days_per_year)

        return vol

    def calculate_max_drawdown(self, nav: pd.Series) -> float:
        """Calculate maximum drawdown

        Args:
            nav: NAV series

        Returns:
            Maximum drawdown value
        """
        if len(nav) < 2:
            return 0.0

        rolling_max = nav.expanding().max()
        drawdown = (nav / rolling_max - 1)
        return abs(drawdown.min())

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio

        Args:
            returns: Returns series

        Returns:
            Sharpe ratio value
        """
        if len(returns) < 2:
            return 0.0

        excess_returns = returns - self.config.risk_free_rate / self.config.trading_days_per_year

        if excess_returns.std() == 0:
            return 0.0

        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(self.config.trading_days_per_year)
        return sharpe

    def calculate_var(self, returns: pd.Series, confidence: float = None) -> float:
        """Calculate Value at Risk

        Args:
            returns: Returns series
            confidence: Confidence level, defaults to config value

        Returns:
            VaR value
        """
        if len(returns) < 2:
            return 0.0

        confidence = confidence or self.config.var_confidence
        return abs(np.percentile(returns, (1 - confidence) * 100))

    def calculate_all_metrics(self, nav: pd.Series) -> Dict[str, float]:
        """Calculate all performance metrics

        Args:
            nav: NAV series

        Returns:
            Dictionary with all metrics
        """
        returns = nav.pct_change().dropna()

        return {
            'total_return': self.calculate_returns(nav, annualized=False),
            'annual_return': self.calculate_returns(nav, annualized=True),
            'volatility': self.calculate_volatility(returns),
            'max_drawdown': self.calculate_max_drawdown(nav),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'var_95': self.calculate_var(returns)
        }


# ============================================================================
# ETF Classifier Utilities
# ============================================================================

class ETFClassifier:
    """ETF classification utilities"""

    def __init__(self, data_loader: DataLoader = None):
        """Initialize ETF classifier

        Args:
            data_loader: DataLoader instance
        """
        self.data_loader = data_loader or DataLoader()

    def get_etf_categories(self, dt: str = None) -> pd.DataFrame:
        """Get ETF categories

        Args:
            dt: Date string (YYYY-MM-DD)

        Returns:
            DataFrame with ETF categories
        """
        df = self.data_loader.get_etf_base_info(dt)
        categories = []

        # Process market directions
        market_directions = df['MARKET_DIRECTION'].dropna().unique()

        for market in market_directions:
            sectors = df[df['MARKET_DIRECTION'] == market]['SECTOR'].dropna().unique()

            for sector in sectors:
                if market == 'bond':
                    # Process duration and credit rating for bond ETFs
                    durations = df[(df['MARKET_DIRECTION'] == market) &
                                   (df['SECTOR'] == sector)]['DURATION'].dropna().unique()
                    ratings = df[(df['MARKET_DIRECTION'] == market) &
                                 (df['SECTOR'] == sector)]['CREDIT_RATING'].dropna().unique()

                    for duration in durations:
                        for rating in ratings:
                            funds = df[
                                (df['MARKET_DIRECTION'] == market) &
                                (df['SECTOR'] == sector) &
                                (df['DURATION'] == duration) &
                                (df['CREDIT_RATING'] == rating)
                            ]

                            if not funds.empty:
                                representative = funds.nlargest(1, 'UNIT_TOTAL').iloc[0]
                                categories.append({
                                    'market_direction': market,
                                    'sector': sector,
                                    'duration': duration,
                                    'credit_rating': rating,
                                    'total_size': funds['UNIT_TOTAL'].sum(),
                                    'fund_count': len(funds),
                                    'representative_code': representative['TRADE_CODE'],
                                    'representative_name': representative['SEC_NAME']
                                })
                else:
                    # Non-bond ETFs
                    funds = df[
                        (df['MARKET_DIRECTION'] == market) &
                        (df['SECTOR'] == sector)
                    ]

                    if not funds.empty:
                        representative = funds.nlargest(1, 'UNIT_TOTAL').iloc[0]
                        categories.append({
                            'market_direction': market,
                            'sector': sector,
                            'duration': None,
                            'credit_rating': None,
                            'total_size': funds['UNIT_TOTAL'].sum(),
                            'fund_count': len(funds),
                            'representative_code': representative['TRADE_CODE'],
                            'representative_name': representative['SEC_NAME']
                        })

        return pd.DataFrame(categories)

    def get_top_performers(self, start_date: str = None, end_date: str = None,
                           top_n: int = 5) -> pd.DataFrame:
        """Get top performing ETFs

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            top_n: Number of top performers to return

        Returns:
            DataFrame with top performers
        """
        categories = self.get_etf_categories()
        codes = categories['representative_code'].tolist()
        nav_data = self.data_loader.get_etf_nav_data(codes, start_date, end_date)

        performance = []
        for _, category in categories.iterrows():
            code = category['representative_code']
            fund_nav = nav_data[nav_data['TRADE_CODE'] == code].sort_values('DT')

            if len(fund_nav) >= 20:
                returns = (fund_nav['NAV_ADJ'].iloc[-1] / fund_nav['NAV_ADJ'].iloc[0] - 1) * 100
                performance.append({
                    'market_direction': category['market_direction'],
                    'sector': category['sector'],
                    'duration': category['duration'],
                    'credit_rating': category['credit_rating'],
                    'code': code,
                    'name': category['representative_name'],
                    'returns': returns
                })

        performance_df = pd.DataFrame(performance)
        if not performance_df.empty:
            return performance_df.nlargest(top_n, 'returns')
        return performance_df


# ============================================================================
# Visualization Utilities
# ============================================================================

class Visualizer:
    """Visualization utilities"""

    @staticmethod
    def plot_nav_comparison(nav_data: Dict[str, pd.Series], title: str = 'NAV Comparison'):
        """Plot NAV comparison chart

        Args:
            nav_data: Dictionary of {name: NAV series}
            title: Chart title

        Returns:
            Plotly Figure object
        """
        import plotly.graph_objects as go

        fig = go.Figure()

        for name, data in nav_data.items():
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data.values,
                name=name,
                mode='lines'
            ))

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='NAV',
            template='plotly_white',
            showlegend=True
        )

        return fig

    @staticmethod
    def plot_drawdown(nav_data: Dict[str, pd.Series], title: str = 'Drawdown Analysis'):
        """Plot drawdown analysis

        Args:
            nav_data: Dictionary of {name: NAV series}
            title: Chart title

        Returns:
            Plotly Figure object
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('NAV', 'Drawdown'),
            vertical_spacing=0.15
        )

        for name, nav in nav_data.items():
            fig.add_trace(
                go.Scatter(x=nav.index, y=nav.values, name=f'{name} NAV', mode='lines'),
                row=1, col=1
            )

            rolling_max = nav.expanding().max()
            drawdown = (nav / rolling_max - 1) * 100
            fig.add_trace(
                go.Scatter(x=nav.index, y=drawdown, name=f'{name} Drawdown', mode='lines'),
                row=2, col=1
            )

        fig.update_layout(
            title=title,
            template='plotly_white',
            showlegend=True,
            height=800
        )

        return fig

    @staticmethod
    def plot_correlation_heatmap(returns_data: Dict[str, pd.Series], title: str = 'Correlation Heatmap'):
        """Plot correlation heatmap

        Args:
            returns_data: Dictionary of {name: returns series}
            title: Chart title

        Returns:
            Plotly Figure object
        """
        import plotly.graph_objects as go

        returns_df = pd.DataFrame(returns_data)
        corr_matrix = returns_df.corr()

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu',
            zmin=-1,
            zmax=1,
            text=np.round(corr_matrix.values, 2),
            texttemplate='%{text}',
            textfont={'size': 12}
        ))

        fig.update_layout(
            title=title,
            template='plotly_white',
            width=800,
            height=800
        )

        return fig


# ============================================================================
# Date Utilities
# ============================================================================

def get_trading_days(start_date: str, end_date: str, data_loader: DataLoader = None) -> List[str]:
    """Get trading days between dates

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        data_loader: DataLoader instance

    Returns:
        List of trading day strings
    """
    if data_loader is None:
        data_loader = DataLoader()

    sql = """
    SELECT DISTINCT DT FROM fund.marketinfo
    WHERE DT BETWEEN :start_date AND :end_date
    ORDER BY DT
    """
    result = data_loader.query_df(sql, (start_date, end_date))
    return result['DT'].dt.strftime('%Y-%m-%d').tolist()


def get_latest_trading_day(data_loader: DataLoader = None) -> str:
    """Get latest trading day

    Args:
        data_loader: DataLoader instance

    Returns:
        Latest trading day string
    """
    if data_loader is None:
        data_loader = DataLoader()

    sql = "SELECT MAX(DT) as latest FROM fund.marketinfo"
    result = data_loader.query_df(sql)
    return result['latest'].iloc[0].strftime('%Y-%m-%d')


def get_date_range(years: int = 3) -> Tuple[str, str]:
    """Get date range for analysis

    Args:
        years: Number of years to look back

    Returns:
        Tuple of (start_date, end_date)
    """
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=years * 365)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


# ============================================================================
# Export Utilities
# ============================================================================

def save_to_csv(df: pd.DataFrame, filename: str, output_dir: Path = None):
    """Save DataFrame to CSV

    Args:
        df: DataFrame to save
        filename: Output filename
        output_dir: Output directory, defaults to OUTPUT_DIR
    """
    output_dir = output_dir or OUTPUT_DIR
    output_path = output_dir / filename
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"Saved to {output_path}")


def save_to_excel(df: pd.DataFrame, filename: str, output_dir: Path = None, sheet_name: str = 'Sheet1'):
    """Save DataFrame to Excel

    Args:
        df: DataFrame to save
        filename: Output filename
        output_dir: Output directory, defaults to OUTPUT_DIR
        sheet_name: Sheet name
    """
    output_dir = output_dir or OUTPUT_DIR
    output_path = output_dir / filename
    df.to_excel(output_path, index=False, sheet_name=sheet_name)
    logger.info(f"Saved to {output_path}")


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Classes
    "DataLoader",
    "PerformanceAnalyzer",
    "ETFClassifier",
    "Visualizer",

    # Functions
    "get_trading_days",
    "get_latest_trading_day",
    "get_date_range",
    "save_to_csv",
    "save_to_excel",

    # Variables
    "logger",
]
