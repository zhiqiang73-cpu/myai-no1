"""
动态杠杆优化器 - 基于历史表现智能调整杠杆倍数

核心思想:
1. 根据信号强度动态调整杠杆
2. 基于最近胜率保护资金
3. 使用Kelly公式优化仓位
4. 回撤保护机制
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque


class LeverageOptimizer:
    """
    智能杠杆优化器
    
    调整因素:
    1. 信号强度 (30-40%权重)
    2. 历史胜率 (30-40%权重)
    3. 账户回撤 (20-30%权重)
    4. 连续盈亏 (10%权重)
    """
    
    def __init__(self, data_file: str = "rl_data/leverage_stats.json"):
        self.data_file = data_file
        self.data = self._load_data()
        
        # 基础参数
        self.base_leverage = 10
        self.min_leverage = 5
        self.max_leverage = 50  # 最大杠杆50倍（高风险）
        
        # 杠杆历史记录
        self.leverage_history: deque = deque(maxlen=100)
        self._load_history()
        
        # 统计数据
        self.stats = self.data.get("stats", {
            "total_trades": 0,
            "avg_leverage": 10.0,
            "leverage_distribution": {},  # {leverage: count}
            "leverage_performance": {}    # {leverage: {trades, wins, avg_pnl}}
        })
    
    def _load_data(self) -> Dict:
        """加载历史数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载杠杆数据失败: {e}")
        return {}
    
    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump({
                    "stats": self.stats,
                    "updated_at": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存杠杆数据失败: {e}")
    
    def _load_history(self):
        """加载最近的杠杆历史"""
        history = self.data.get("recent_history", [])
        self.leverage_history = deque(history[-100:], maxlen=100)
    
    def calculate_dynamic_leverage(
        self,
        signal: Dict,
        market_state: Dict,
        account_stats: Dict
    ) -> int:
        """
        计算动态杠杆
        
        Args:
            signal: 入场信号 {score, direction, confidence, ...}
            market_state: 市场状态 {macro_trend, micro_trend, ...}
            account_stats: 账户统计 {win_rate, max_drawdown, ...}
        
        Returns:
            int: 建议的杠杆倍数 (5-20)
        """
        # 基础杠杆
        leverage = float(self.base_leverage)
        
        # ===== 1. 信号强度调整 (权重: 35%) =====
        signal_score = signal.get("score", 30)
        signal_multiplier = self._calculate_signal_multiplier(signal_score)
        leverage *= signal_multiplier
        
        # ===== 2. 胜率调整 (权重: 35%) =====
        win_rate = account_stats.get("win_rate", 0.5)
        win_rate_multiplier = self._calculate_winrate_multiplier(win_rate)
        leverage *= win_rate_multiplier
        
        # ===== 3. 回撤保护 (权重: 25%) =====
        max_drawdown = account_stats.get("max_drawdown", 0)
        drawdown_multiplier = self._calculate_drawdown_multiplier(max_drawdown)
        leverage *= drawdown_multiplier
        
        # ===== 4. 连续盈亏调整 (权重: 5%) =====
        streak_multiplier = self._calculate_streak_multiplier(account_stats)
        leverage *= streak_multiplier
        
        # ===== 5. Kelly公式优化 (可选) =====
        kelly_leverage = self._calculate_kelly_leverage(account_stats)
        if kelly_leverage > 0:
            # 使用Half-Kelly更保守
            leverage = (leverage * 0.7 + kelly_leverage * 0.3)
        
        # ===== 6. 限制范围 =====
        final_leverage = int(round(leverage))
        final_leverage = max(self.min_leverage, min(self.max_leverage, final_leverage))
        
        # 记录决策
        self._record_decision(signal, account_stats, final_leverage)
        
        return final_leverage
    
    def _calculate_signal_multiplier(self, score: float) -> float:
        """
        根据信号强度计算杠杆乘数
        
        分数范围:
        - 80+分: 1.5x (非常强)
        - 60-80分: 1.3x (强)
        - 45-60分: 1.1x (中等)
        - 30-45分: 1.0x (基准)
        - <30分: 0.8x (弱)
        """
        if score >= 80:
            return 1.5
        elif score >= 60:
            return 1.3
        elif score >= 45:
            return 1.1
        elif score >= 30:
            return 1.0
        else:
            return 0.8
    
    def _calculate_winrate_multiplier(self, win_rate: float) -> float:
        """
        根据胜率计算杠杆乘数
        
        胜率范围:
        - >65%: 1.4x (优秀)
        - 55-65%: 1.2x (良好)
        - 45-55%: 1.0x (基准)
        - 35-45%: 0.8x (较差)
        - <35%: 0.6x (很差，强制降杠杆)
        """
        if win_rate >= 0.65:
            return 1.4
        elif win_rate >= 0.55:
            return 1.2
        elif win_rate >= 0.45:
            return 1.0
        elif win_rate >= 0.35:
            return 0.8
        else:
            return 0.6  # 强制降低
    
    def _calculate_drawdown_multiplier(self, drawdown: float) -> float:
        """
        根据最大回撤计算杠杆乘数
        
        回撤范围:
        - <3%: 1.2x (安全)
        - 3-5%: 1.0x (正常)
        - 5-8%: 0.8x (注意)
        - 8-12%: 0.6x (警告)
        - >12%: 0.5x (危险，强制降杠杆)
        """
        drawdown = abs(drawdown)
        
        if drawdown < 3:
            return 1.2
        elif drawdown < 5:
            return 1.0
        elif drawdown < 8:
            return 0.8
        elif drawdown < 12:
            return 0.6
        else:
            return 0.5  # 强制大幅降低
    
    def _calculate_streak_multiplier(self, stats: Dict) -> float:
        """
        根据连续盈亏计算杠杆乘数
        
        连续盈利: 可以适当提高杠杆
        连续亏损: 必须降低杠杆
        """
        # 从最近交易历史获取连续盈亏
        recent_trades = stats.get("recent_trades", [])
        if not recent_trades:
            return 1.0
        
        # 计算连续盈亏次数
        streak = 0
        last_result = None
        
        for trade in reversed(recent_trades[-10:]):  # 最近10笔
            pnl = trade.get("pnl", 0)
            is_win = pnl > 0
            
            if last_result is None:
                last_result = is_win
                streak = 1
            elif is_win == last_result:
                streak += 1
            else:
                break
        
        # 根据连续结果调整
        if last_result:  # 连续盈利
            if streak >= 5:
                return 1.1  # 适当提高
            elif streak >= 3:
                return 1.05
            else:
                return 1.0
        else:  # 连续亏损
            if streak >= 5:
                return 0.7  # 大幅降低
            elif streak >= 3:
                return 0.85
            else:
                return 0.95
    
    def _calculate_kelly_leverage(self, stats: Dict) -> float:
        """
        使用Kelly公式计算最优杠杆
        
        Kelly公式: f = (p×b - q) / b
        - p = 胜率
        - q = 败率 (1-p)
        - b = 盈亏比 (平均盈利/平均亏损)
        
        使用Half-Kelly更保守
        """
        win_rate = stats.get("win_rate", 0)
        avg_win = abs(stats.get("avg_win_percent", 0))
        avg_loss = abs(stats.get("avg_loss_percent", 0))
        
        # 需要至少20笔交易才使用Kelly
        total_trades = stats.get("total_trades", 0)
        if total_trades < 20 or avg_loss == 0:
            return 0
        
        # 计算盈亏比
        profit_loss_ratio = avg_win / avg_loss
        
        # Kelly公式
        kelly_fraction = (win_rate * profit_loss_ratio - (1 - win_rate)) / profit_loss_ratio
        
        # Half-Kelly (更保守)
        kelly_fraction *= 0.5
        
        # 限制范围
        kelly_fraction = max(0, min(1, kelly_fraction))
        
        # 转换为杠杆倍数 (假设基准是10倍)
        kelly_leverage = self.base_leverage * (1 + kelly_fraction)
        
        return kelly_leverage
    
    def _record_decision(self, signal: Dict, stats: Dict, leverage: int):
        """记录杠杆决策"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "leverage": leverage,
            "signal_score": signal.get("score", 0),
            "win_rate": stats.get("win_rate", 0),
            "max_drawdown": stats.get("max_drawdown", 0)
        }
        self.leverage_history.append(record)
    
    def record_trade_result(self, leverage: int, pnl_percent: float, 
                           is_win: bool, trade_duration: int):
        """
        记录交易结果，用于优化杠杆策略
        
        Args:
            leverage: 使用的杠杆
            pnl_percent: 盈亏百分比
            is_win: 是否盈利
            trade_duration: 持仓时长(分钟)
        """
        # 更新统计
        self.stats["total_trades"] += 1
        
        # 更新杠杆分布
        lev_str = str(leverage)
        if lev_str not in self.stats["leverage_distribution"]:
            self.stats["leverage_distribution"][lev_str] = 0
        self.stats["leverage_distribution"][lev_str] += 1
        
        # 更新杠杆表现
        if lev_str not in self.stats["leverage_performance"]:
            self.stats["leverage_performance"][lev_str] = {
                "trades": 0,
                "wins": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "win_rate": 0
            }
        
        perf = self.stats["leverage_performance"][lev_str]
        perf["trades"] += 1
        if is_win:
            perf["wins"] += 1
        perf["total_pnl"] += pnl_percent
        perf["avg_pnl"] = perf["total_pnl"] / perf["trades"]
        perf["win_rate"] = perf["wins"] / perf["trades"]
        
        # 计算平均杠杆
        total_leverage = sum(
            int(lev) * count 
            for lev, count in self.stats["leverage_distribution"].items()
        )
        total_trades = sum(self.stats["leverage_distribution"].values())
        self.stats["avg_leverage"] = total_leverage / total_trades if total_trades > 0 else 10
        
        # 保存
        self._save_data()
    
    def get_stats(self) -> Dict:
        """获取杠杆统计信息"""
        return {
            "total_trades": self.stats["total_trades"],
            "avg_leverage": round(self.stats["avg_leverage"], 2),
            "leverage_distribution": self.stats["leverage_distribution"],
            "leverage_performance": self.stats["leverage_performance"],
            "recent_history": list(self.leverage_history)[-10:]
        }
    
    def get_recommendation(self, signal: Dict, market: Dict, account: Dict) -> Dict:
        """
        获取杠杆推荐及详细说明
        
        Returns:
            {
                "leverage": int,
                "explanation": str,
                "factors": {...}
            }
        """
        leverage = self.calculate_dynamic_leverage(signal, market, account)
        
        # 构建解释
        factors = {
            "signal_score": signal.get("score", 0),
            "win_rate": account.get("win_rate", 0) * 100,
            "max_drawdown": abs(account.get("max_drawdown", 0)),
            "base_leverage": self.base_leverage
        }
        
        explanation = f"基于信号{factors['signal_score']:.0f}分, "
        explanation += f"胜率{factors['win_rate']:.1f}%, "
        explanation += f"回撤{factors['max_drawdown']:.1f}% "
        explanation += f"→ 建议{leverage}x杠杆"
        
        return {
            "leverage": leverage,
            "explanation": explanation,
            "factors": factors
        }

