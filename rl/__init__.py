"""
强化学习交易系统 v4.0
整合的自适应交易系统
"""

# 配置
from .config import (
    TIMEFRAME_WEIGHTS,
    FEATURE_LEARNING,
    DYNAMIC_THRESHOLD,
    POSITION_MANAGEMENT,
    RISK_CONTROL,
    TIME_CONFIG,
    time_manager,
    now,
    timestamp,
    format_time,
)

# 核心
from .core import TradingAgent, TradeLogger, KnowledgeBase

# 市场分析
from .market_analysis import (
    TechnicalAnalyzer,
    BestLevelFinder,
    LevelDiscovery,
    LevelScoring,
)

# 执行
from .execution import (
    StopLossTakeProfit,
    PositionSizer,
    ExitManager,
    PositionState,
    ExitDecision,
)

# 学习
from .learning import UnifiedLearningSystem

# 风险控制
from .risk import RiskController

__version__ = "4.0"
__all__ = [
    # 配置
    'TIMEFRAME_WEIGHTS',
    'FEATURE_LEARNING',
    'DYNAMIC_THRESHOLD',
    'POSITION_MANAGEMENT',
    'RISK_CONTROL',
    'TIME_CONFIG',
    'time_manager',
    'now',
    'timestamp',
    'format_time',
    # 核心
    'TradingAgent',
    'TradeLogger',
    'KnowledgeBase',
    # 市场分析
    'TechnicalAnalyzer',
    'BestLevelFinder',
    'LevelDiscovery',
    'LevelScoring',
    # 执行
    'StopLossTakeProfit',
    'PositionSizer',
    'ExitManager',
    'PositionState',
    'ExitDecision',
    # 学习
    'UnifiedLearningSystem',
    # 风险控制
    'RiskController',
]
