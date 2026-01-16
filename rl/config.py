"""
统一配置文件 v4.0
整合所有模块的配置参数
"""
from datetime import timezone, datetime

# ========================================
# 时间管理
# ========================================
class TimeManager:
    """统一UTC时间管理"""

@staticmethod
def now():
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)

@staticmethod
def format_timestamp(dt):
    """格式化时间戳"""
    if isinstance(dt, datetime):
        return dt.isoformat()
        return dt

@staticmethod
def parse_binance_time(timestamp_ms):
    """解析Binance时间戳（毫秒）"""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

    time_manager = TimeManager()


    # ========================================
    # 多周期权重配置
    # ========================================
    TIMEFRAME_WEIGHTS = {
    # 趋势分析权重（用户指定）
    "trend_analysis": {
    "1m": 0.30, # 30%
    "15m": 0.40, # 40%
    "8h": 0.20, # 20%
    "1w": 0.10, # 10%
    },

    # 支撑阻力发现权重
    "level_discovery": {
    "1m": 0.50, # 50%
    "15m": 0.30, # 30%
    "8h": 0.15, # 15%
    "1w": 0.05, # 5%
    },

    # 入场时机权重（只看短周期）
    "entry_timing": {
    "1m": 0.40, # 40%
    "15m": 0.60, # 60%
    }
    }


    # ========================================
    # AI动态阈值配置
    # ========================================
    DYNAMIC_THRESHOLD = {
    # 阈值范围
    "min_threshold": 30,
    "max_threshold": 80,

    # 基础阈值（根据交易数量平滑过渡）
    "base_thresholds": {
    "phase_1": {
    "trades": [0, 20],
    "threshold": 50, # 初期：中等阈值
    },
    "phase_2": {
    "trades": [20, 50],
    "threshold": 55, # 学习期：略高
    },
    "phase_3": {
    "trades": [50, 100],
    "threshold": 60, # 成熟期：较高
    },
    "phase_4": {
    "trades": [100, 9999],
    "threshold": 65, # 稳定期：高阈值
    },
    },

    # 市场状态调整
    "market_adjustments": {
    "high_volatility": +10, # 高波动提高阈值
    "strong_trend": -5, # 强趋势降低阈值
    "ranging_market": +8, # 震荡市提高阈值
    "low_liquidity": +5, # 低流动性提高阈值
    },

    # 表现调整
    "performance_adjustments": {
    "recent_win_rate_low": +8, # 最近胜率低，提高阈值
    "recent_win_rate_high": -5, # 最近胜率高，降低阈值
    "consecutive_losses_3": +10, # 连续亏损3次，提高阈值
    "consecutive_wins_3": -5, # 连续盈利3次，降低阈值
    },

    # 信号质量调整
    "quality_adjustments": {
    "signal_win_rate_high": -5, # 同类信号胜率高
    "signal_win_rate_low": +8, # 同类信号胜率低
    },
    }


    # ========================================
    # 分批建仓/减仓配置
    # ========================================
    BATCH_ENTRY_EXIT = {
    # 分批建仓
    "batch_entry": {
    # 根据信号强度分批
    "signal_strength_tiers": {
    "strong": { # 80-100
    "batches": 3,
    "ratios": [0.4, 0.3, 0.3], # 40%, 30%, 30%
    },
    "medium": { # 60-80
    "batches": 2,
    "ratios": [0.5, 0.5], # 50%, 50%
    },
    "weak": { # <60
    "batches": 1,
    "ratios": [1.0], # 100%（一次性）
    },
    },

    # 入场偏移（等待回调百分比）
    "entry_offsets": [
    0.0, # 第1批：立即
    0.001, # 第2批：回调0.1%
    0.002, # 第3批：回调0.2%
    ],
    },

    # 分批止盈
    "batch_exit": {
    "profit_levels": [
    {"target_pnl": 1.5, "close_ratio": 0.3}, # 盈利1.5%时平30%
    {"target_pnl": 2.5, "close_ratio": 0.3}, # 盈利2.5%时再平30%
    {"target_pnl": 4.0, "close_ratio": 0.4}, # 盈利4.0%时平剩余40%
    ],
    },

    # Kelly公式杠杆
    "kelly_formula": {
    "max_leverage": 20,
    "min_leverage": 5,
    "conservative_factor": 0.5, # Kelly建议的1/2

    # 市场状态调整系数
    "market_adjustments": {
    "high_volatility": 0.7, # 高波动降低杠杆
    "strong_trend": 1.2, # 强趋势提高杠杆
    "ranging_market": 0.8, # 震荡市降低杠杆
    "low_liquidity": 0.6, # 低流动性降低杠杆
    },
    },
    }


    # ========================================
    # 风险控制配置
    # ========================================
    RISK_CONTROL = {
    # 基础风控
    "max_positions": 3,
    "max_risk_per_trade": 0.02, # 单笔最大风险2%
    "max_total_risk": 0.06, # 总风险6%

    # 日内风控
    "daily_loss_limit": 0.05, # 日损失5%
    "daily_max_trades": 20, # 日最大交易20笔

    # 连续亏损控制
    "consecutive_loss_limit": 3, # 连续亏损3次暂停
    "pause_duration_minutes": 60, # 暂停60分钟

    # 回撤控制
    "max_drawdown": 0.15, # 最大回撤15%
    }


    # ========================================
    # 统一学习系统配置
    # ========================================
    UNIFIED_LEARNING = {
    # 支撑阻力特征权重学习
    "level_feature_learning": {
    "features": [
    "volume_density", # 成交量密度
    "touch_bounce_count", # 触碰/反弹次数
    "bounce_magnitude", # 反弹幅度
    "failed_breakout_count", # 假突破次数
    "duration", # 持续时间
    "multi_tf_confirm", # 多周期确认
    ],

    # 初始权重
    "initial_weights": {
    "volume_density": 0.20,
    "touch_bounce_count": 0.25,
    "bounce_magnitude": 0.15,
    "failed_breakout_count": 0.15,
    "duration": 0.10,
    "multi_tf_confirm": 0.15,
    },

    # 学习参数
    "learning_rate": 0.1,
    "min_samples": 20,
    "correlation_threshold": 0.3,
    },

    # 入场决策学习
    "entry_decision_learning": {
    "learning_rate": 0.05,
    "min_samples": 30,
    },

    # SL/TP学习
    "sl_tp_learning": {
    "learning_rate": 0.08,
    "min_samples": 25,
    },
    }


    # ========================================
    # ATR动态止损止盈配置
    # ========================================
    ATR_SL_TP = {
    # 止损
    "stop_loss": {
    "atr_multiplier": 2.0,
    "min_percent": 0.008, # 最小0.8%
    "max_percent": 0.03, # 最大3%
    },

    # 止盈
    "take_profit": {
    "atr_multiplier": 3.5,
    "min_percent": 0.015, # 最小1.5%
    "max_percent": 0.06, # 最大6%
    },

    # 移动止损
    "trailing_stop": {
    "enabled": True,
    "activation_pnl": 0.015, # 盈利1.5%后启动
    "trail_percent": 0.005, # 回撤0.5%止损
    },
    }


    # ========================================
    # 旧配置（兼容性）
    # ========================================
    # 这些可以保留用于测试或逐步迁移

    LEVEL_WEIGHTS_V3 = {
    "volume_density": 0.20,
    "touch_bounce_count": 0.25,
    "bounce_magnitude": 0.15,
    "failed_breakout_count": 0.15,
    "duration": 0.10,
    "multi_tf_confirm": 0.15,
    }


    if __name__ == "__main__":
        print("="*60)
        print("统一配置文件 v4.0")
        print("="*60)

        print("\n多周期权重:")
        print(f" 趋势分析: {TIMEFRAME_WEIGHTS['trend_analysis']}")
        print(f" 入场时机: {TIMEFRAME_WEIGHTS['entry_timing']}")

        print("\nAI动态阈值:")
        print(f" 范围: {DYNAMIC_THRESHOLD['min_threshold']}-{DYNAMIC_THRESHOLD['max_threshold']}")
        print(f" 阶段: {len(DYNAMIC_THRESHOLD['base_thresholds'])}个")

        print("\n分批建仓:")
        print(f" 强信号: {BATCH_ENTRY_EXIT['batch_entry']['signal_strength_tiers']['strong']}")

        print("\nKelly公式杠杆:")
        print(f" 范围: {BATCH_ENTRY_EXIT['kelly_formula']['min_leverage']}-{BATCH_ENTRY_EXIT['kelly_formula']['max_leverage']}x")

        print("\n风险控制:")
        print(f" 最大持仓: {RISK_CONTROL['max_positions']}")
        print(f" 单笔风险: {RISK_CONTROL['max_risk_per_trade']*100}%")

        print("\n 配置加载完成！")


