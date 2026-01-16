"""
自适应交易系统 v4.0 统一配置
整合所有参数，避免分散
"""

# ========== 多周期权重配置 ==========
TIMEFRAME_WEIGHTS = {
 # 趋势分析权重（判断大方向）
 "trend_analysis": {
 "1m": 0.30, # 30% - 捕捉超短期波动
 "15m": 0.40, # 40% - 短线主趋势
 "8h": 0.20, # 20% - 大趋势方向
 "1w": 0.10, # 10% - 超大趋势确认
 },
 
 # 支撑阻力位发现权重（找关键价位）
 "level_discovery": {
 "1m": 0.50, # 50% - 超短线关键位
 "15m": 0.30, # 30% - 短线关键位
 "8h": 0.15, # 15% - 大级别参考
 "1w": 0.05, # 5% - 超大级别参考
 },
 
 # 入场时机权重（精确入场点，只看短周期）
 "entry_timing": {
 "1m": 0.70, # 70% - 精确入场点
 "15m": 0.30, # 30% - 趋势确认
 "8h": 0.0, # 不参与入场时机判断
 "1w": 0.0, # 不参与入场时机判断
 }
}

# ========== 特征学习配置 ==========
FEATURE_LEARNING = {
 # 初始特征权重（会通过学习动态调整）
 "initial_weights": {
 "volume_density": 0.20, # 成交量密集度
 "touch_bounce_count": 0.20, # 触及反弹次数
 "bounce_magnitude": 0.15, # 反弹幅度
 "failed_breakout_count": 0.20, # 假突破次数
 "duration_days": 0.10, # 有效持续天数
 "multi_tf_confirm": 0.15, # 多周期确认
 },
 
 # 学习参数
 "learning_rate": 0.1, # 权重更新速度
 "update_frequency": 10, # 每10笔交易更新一次
 "min_samples": 10, # 最少样本数
 "max_history": 100, # 保留最近100笔用于学习
 
 # 有效性判断标准
 "effectiveness_thresholds": {
 "support_tolerance": 0.5, # 支撑位容忍度（ATR倍数）
 "resistance_tolerance": 0.5, # 阻力位容忍度（ATR倍数）
 "high_effectiveness": 0.7, # 高有效性阈值
 "low_effectiveness": 0.3, # 低有效性阈值
 }
}

# ========== AI动态阈值配置 ==========
DYNAMIC_THRESHOLD = {
 # 基础阈值（根据交易数量）
 "base_thresholds": {
 "phase_1": {"trades": (0, 10), "threshold": 30}, # 前10笔
 "phase_2": {"trades": (10, 30), "threshold": 40}, # 10-30笔
 "phase_3": {"trades": (30, 50), "threshold": 50}, # 30-50笔
 "phase_4": {"trades": (50, 999), "threshold": 55}, # 50+笔
 },
 
 # 市场状态调整
 "market_adjustments": {
 "high_volatility": +10, # 高波动市场提高门槛
 "strong_trend": -5, # 强趋势降低门槛（抓住机会）
 "ranging_market": +15, # 震荡市大幅提高门槛
 "low_liquidity": +10, # 低流动性提高门槛
 },
 
 # 表现调整
 "performance_adjustments": {
 "recent_win_rate_low": +10, # 最近5笔胜率<40%
 "recent_win_rate_high": -5, # 最近5笔胜率>70%
 "consecutive_losses_3": +20, # 连续亏损3次
 "consecutive_wins_3": -5, # 连续盈利3次
 },
 
 # 信号质量调整
 "quality_adjustments": {
 "signal_win_rate_high": -10, # 该类信号历史胜率>70%
 "signal_win_rate_low": +15, # 该类信号历史胜率<40%
 },
 
 # 阈值范围限制
 "min_threshold": 20,
 "max_threshold": 80,
}

# ========== 仓位管理配置 ==========
POSITION_MANAGEMENT = {
 # 分批建仓策略（超短线）
 "entry_batches": [
 {
 "name": "首批",
 "ratio": 0.60, # 60%仓位
 "trigger": "immediate", # 立即开仓
 "description": "立即开仓60%"
 },
 {
 "name": "二批",
 "ratio": 0.30, # 30%仓位
 "trigger": "price_confirm", # 价格确认
 "distance": 0.001, # 0.1%价格确认
 "timeout": 60, # 60秒内未确认则取消
 "description": "价格确认后开30%"
 },
 {
 "name": "三批",
 "ratio": 0.10, # 10%仓位
 "trigger": "trend_confirm", # 趋势确认
 "bars": 2, # 2根K线确认
 "timeout": 120, # 120秒内未确认则取消
 "description": "趋势确认后开10%"
 },
 ],
 
 # 分批止盈策略（超短线，快进快出）
 "tp_batches": [
 {
 "name": "TP1",
 "ratio": 0.40, # 平40%
 "target_atr": 1.5, # 盈利1.5倍ATR
 "action": "partial_close",
 "move_sl_to_entry": True, # 移动止损到成本价
 "description": "盈利1.5ATR平40%，移动止损"
 },
 {
 "name": "TP2",
 "ratio": 0.30, # 再平30%
 "target_atr": 2.5, # 盈利2.5倍ATR
 "action": "partial_close",
 "move_sl_to_breakeven": True, # 保本
 "description": "盈利2.5ATR再平30%"
 },
 {
 "name": "TP3",
 "ratio": 0.30, # 平剩余30%
 "target_atr": 4.0, # 盈利4倍ATR
 "action": "close_all",
 "description": "盈利4ATR平全部"
 },
 ],
 
 # 止损策略（超短线，快速止损）
 "stop_loss": {
 "initial_atr": 1.0, # 初始止损：1倍ATR
 "max_loss_percent": 1.5, # 最大亏损：1.5%
 "trailing_trigger_atr": 1.5, # 盈利1.5ATR启动移动止损
 "trailing_distance_atr": 0.5,# 移动止损距离：0.5ATR
 },
 
 # 持仓时间限制（超短线）
 "time_limits": {
 "max_hold_minutes": 30, # 最多持仓30分钟
 "min_hold_minutes": 1, # 至少持仓1分钟（避免频繁开平）
 },
 
 # Kelly公式杠杆优化
 "kelly_leverage": {
 "enabled": True, # 启用Kelly公式
 "base_leverage": 10, # 基础杠杆
 "min_leverage": 5, # 最小杠杆
 "max_leverage": 30, # 最大杠杆（超短线控制风险）
 "kelly_fraction": 0.5, # Half-Kelly（更保守）
 "signal_strength_weight": 0.3, # 信号强度权重
 "win_rate_weight": 0.4, # 胜率权重
 "risk_reward_weight": 0.3, # 盈亏比权重
 },
}

# ========== 风险控制配置 ==========
RISK_CONTROL = {
 "max_daily_loss": 5.0, # 单日最大亏损5%
 "max_drawdown": 10.0, # 最大回撤10%
 "stop_after_losses": 3, # 连续3次亏损停止
 "max_hourly_trades": 5, # 每小时最多5笔
 "max_concurrent_positions": 3, # 最多3个并发仓位
 "max_risk_per_trade": 2.0, # 单笔最大风险2%
}

# ========== 时区配置 ==========
TIME_CONFIG = {
 "timezone": "UTC", # 统一使用UTC
 "display_format": "%Y-%m-%d %H:%M:%S UTC", # 显示格式
 "kline_alignment": True, # K线时间对齐
}

# ========== 数据记录配置 ==========
DATA_RECORDING = {
 "record_price_trajectory": True, # 记录完整价格轨迹
 "record_feature_values": True, # 记录特征值
 "record_market_state": True, # 记录市场状态
 "trajectory_sampling_seconds": 10, # 每10秒采样一次价格
 "max_trajectory_points": 100, # 最多100个采样点
}

# ========== 系统信息 ==========
SYSTEM_INFO = {
 "version": "4.0",
 "name": "自适应强化学习交易系统",
 "description": "基于特征学习的超短线交易系统",
 "author": "AI Architect",
 "created": "2026-01-15",
}


def get_config_summary():
 """获取配置摘要"""
 return f"""
╔═══════════════════════════════════════════════════════════════╗
║ {SYSTEM_INFO['name']} v{SYSTEM_INFO['version']} ║
╚═══════════════════════════════════════════════════════════════╝

 多周期权重:
 趋势分析: 1m({TIMEFRAME_WEIGHTS['trend_analysis']['1m']:.0%}) 
 15m({TIMEFRAME_WEIGHTS['trend_analysis']['15m']:.0%}) 
 8h({TIMEFRAME_WEIGHTS['trend_analysis']['8h']:.0%}) 
 1w({TIMEFRAME_WEIGHTS['trend_analysis']['1w']:.0%})
 
 支撑阻力: 1m({TIMEFRAME_WEIGHTS['level_discovery']['1m']:.0%}) 
 15m({TIMEFRAME_WEIGHTS['level_discovery']['15m']:.0%}) 
 8h({TIMEFRAME_WEIGHTS['level_discovery']['8h']:.0%}) 
 1w({TIMEFRAME_WEIGHTS['level_discovery']['1w']:.0%})

 动态阈值范围: {DYNAMIC_THRESHOLD['min_threshold']}-{DYNAMIC_THRESHOLD['max_threshold']}分

 仓位管理:
 建仓: {' + '.join([f"{b['ratio']:.0%}" for b in POSITION_MANAGEMENT['entry_batches']])}
 止盈: {' + '.join([f"TP{i+1}({b['target_atr']:.1f}ATR)" for i, b in enumerate(POSITION_MANAGEMENT['tp_batches'])])}
 杠杆: {POSITION_MANAGEMENT['kelly_leverage']['min_leverage']}-{POSITION_MANAGEMENT['kelly_leverage']['max_leverage']}x (Kelly公式)

️ 风险控制:
 单日亏损: ≤{RISK_CONTROL['max_daily_loss']}%
 最大回撤: ≤{RISK_CONTROL['max_drawdown']}%
 连续亏损: {RISK_CONTROL['stop_after_losses']}次停止

⏰ 时区: {TIME_CONFIG['timezone']}
"""


if __name__ == "__main__":
 print(get_config_summary())

