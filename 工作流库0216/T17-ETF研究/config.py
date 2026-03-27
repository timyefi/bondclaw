"""
ETF Research Configuration Module
=======================

Configuration settings for ETF research project.
All sensitive information is loaded from environment variables.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging

# ============================================================================
# Base Paths
# ============================================================================

# Project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for dir_path in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Database Configuration (Environment Variables Required)
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = field(default_factory=lambda: os.getenv("ETF_DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("ETF_DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("ETF_DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("ETF_DB_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("ETF_DB_NAME", "fund"))
    charset: str = "utf8mb4"
    pool_size: int = 5
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 minutes

    @property
    def connection_url(self) -> str:
        """Get SQLAlchemy connection URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"


@dataclass
class BondDatabaseConfig:
    """Bond database configuration"""
    host: str = field(default_factory=lambda: os.getenv("BOND_DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("BOND_DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("BOND_DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("BOND_DB_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("BOND_DB_NAME", "bond"))
    charset: str = "utf8mb4"

    @property
    def connection_url(self) -> str:
        """Get SQLAlchemy connection URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"


# Default database configurations
ETF_DB = DatabaseConfig()
BOND_DB = BondDatabaseConfig()


# ============================================================================
# THS (Tonghuashun) Configuration
# ============================================================================

@dataclass
class THSConfig:
    """Tonghuashun API configuration"""
    username: str = field(default_factory=lambda: os.getenv("THS_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("THS_PASSWORD", ""))


THS_CONFIG = THSConfig()


# ============================================================================
# Performance Analysis Configuration
# ============================================================================

@dataclass
class PerformanceConfig:
    """Performance analysis configuration"""
    # Risk-free rate (annualized)
    risk_free_rate: float = 0.02

    # Trading days per year
    trading_days_per_year: int = 252

    # Default analysis period (years)
    default_analysis_years: int = 3

    # Rolling window for volatility calculation
    volatility_window: int = 20

    # Confidence level for VaR calculation
    var_confidence: float = 0.95

    # Maximum drawdown calculation window
    max_drawdown_window: int = 252


PERFORMANCE_CONFIG = PerformanceConfig()


# ============================================================================
# ETF Classification Configuration
# ============================================================================

@dataclass
class ClassificationConfig:
    """ETF classification configuration"""
    # Market directions
    market_directions: List[str] = field(default_factory=lambda: [
        "stock",      # Stock ETF
        "bond",       # Bond ETF
        "commodity",  # Commodity ETF
        "currency",   # Currency ETF
        "mixed"       # Mixed asset ETF
    ])

    # Strategy types
    strategy_types: List[str] = field(default_factory=lambda: [
        "passive",      # Passive index
        "enhanced",     # Enhanced index
        "smart_beta",   # Smart Beta
        "leveraged"     # Leveraged/Inverse
    ])

    # Bond ETF duration categories
    duration_categories: List[str] = field(default_factory=lambda: [
        "short",    # Short term (< 1 year)
        "medium",   # Medium term (1-3 years)
        "long"      # Long term (> 3 years)
    ])

    # Credit rating categories
    credit_ratings: List[str] = field(default_factory=lambda: [
        "high",      # High quality
        "medium",    # Medium quality
        "low"        # Low quality / High yield
    ])


CLASSIFICATION_CONFIG = ClassificationConfig()


# ============================================================================
# Logging Configuration
# ============================================================================

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: int = logging.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_file: Optional[str] = str(LOGS_DIR / "etf_research.log")
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


LOGGING_CONFIG = LoggingConfig()


# ============================================================================
# Output Configuration
# ============================================================================

@dataclass
class OutputConfig:
    """Output configuration"""
    # Table generation settings
    table_theme: str = "classic"
    table_style: str = "default"
    table_layout: str = "standard"

    # Plot settings
    figure_dpi: int = 150
    figure_size: tuple = (12, 8)

    # Export formats
    export_formats: List[str] = field(default_factory=lambda: ["csv", "xlsx", "png"])

    # Data source attribution
    data_source: str = "Data Source: Research, WIND, THS"


OUTPUT_CONFIG = OutputConfig()

# Convenience paths
PLOT_DIR = OUTPUT_DIR


# ============================================================================
# Table Configuration for Visualization
# ============================================================================

from enum import Enum

class TableTheme(Enum):
    """Table theme options"""
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMAL = "minimal"


class TableStyle(Enum):
    """Table style options"""
    DEFAULT = "default"
    COMPACT = "compact"
    DETAILED = "detailed"


class TableLayout(Enum):
    """Table layout options"""
    STANDARD = "standard"
    WIDE = "wide"
    NARROW = "narrow"


# ============================================================================
# Utility Functions
# ============================================================================

def setup_logging(name: str = None) -> logging.Logger:
    """Setup and return a logger instance

    Args:
        name: Logger name, defaults to root logger

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            LOGGING_CONFIG.format,
            LOGGING_CONFIG.date_format
        ))
        logger.addHandler(handler)
        logger.setLevel(LOGGING_CONFIG.level)

    return logger


def get_database_engine(config: DatabaseConfig = None):
    """Get SQLAlchemy database engine

    Args:
        config: Database configuration, defaults to ETF_DB

    Returns:
        SQLAlchemy Engine instance
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import QueuePool

    if config is None:
        config = ETF_DB

    return create_engine(
        config.connection_url,
        pool_size=config.pool_size,
        pool_timeout=config.pool_timeout,
        pool_recycle=config.pool_recycle,
        poolclass=QueuePool,
        echo=False
    )


def validate_config() -> bool:
    """Validate that all required configuration is present

    Returns:
        bool: True if configuration is valid
    """
    errors = []

    # Check database configuration
    if not ETF_DB.host:
        errors.append("ETF_DB_HOST environment variable is not set")
    if not ETF_DB.user:
        errors.append("ETF_DB_USER environment variable is not set")

    if errors:
        for error in errors:
            print(f"Configuration error: {error}")
        return False

    return True


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Paths
    "PROJECT_ROOT",
    "DATA_DIR",
    "OUTPUT_DIR",
    "LOGS_DIR",
    "PLOT_DIR",

    # Database configs
    "DatabaseConfig",
    "BondDatabaseConfig",
    "ETF_DB",
    "BOND_DB",

    # Other configs
    "THS_CONFIG",
    "PERFORMANCE_CONFIG",
    "CLASSIFICATION_CONFIG",
    "LOGGING_CONFIG",
    "OUTPUT_CONFIG",

    # Enums
    "TableTheme",
    "TableStyle",
    "TableLayout",

    # Utility functions
    "setup_logging",
    "get_database_engine",
    "validate_config",
]
