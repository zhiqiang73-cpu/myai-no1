"""
回测训练系统 - 专门用于快速积累学习数据

核心设计理念：
1. 极度放宽入场条件 - 目标是产生大量交易，而不是盈利
2. 简化决策逻辑 - 只看支撑阻力位 + 基本技术指标
3. 快速迭代 - 每笔交易都更新学习系统
4. 数据驱动 - 让系统从大量交易中学习什么有效什么无效

使用方法：
    python backtest_trainer.py --days 30 --max-trades 500
"""

import os
import sys
import csv
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random
import numpy as np

# 设置UTF-8编码 - 更安全的方式
if sys.platform == 'win32':
    try:
        import io
        # 只在需要时重新包装
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception as e:
        # 如果失败就不设置，使用默认编码
        pass

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rl.indicators import TechnicalAnalyzer
from rl.level_finder import BestLevelFinder, LevelFeatureCalculator
from rl.sl_tp_learner import SLTPLearner
from rl.entry_learner_v2 import EntryLearnerV2


@dataclass
class BacktestPosition:
    """回测仓位"""
    trade_id: str
    direction: str  # LONG / SHORT
    entry_price: float
    entry_time: str
    quantity: float
    stop_loss: float
    take_profit: float
    entry_reason: str
    entry_score: float
    # 用于学习的特征
    support_price: float = 0
    resistance_price: float = 0
    support_score: float = 0
    resistance_score: float = 0
    # AI 推荐值
    ai_sl_tp: Optional[Dict] = None
    # 特征学习数据
    support_features: Optional[Dict] = None
    resistance_features: Optional[Dict] = None


@dataclass 
class BacktestTrade:
    """已完成的回测交易"""
    trade_id: str
    direction: str
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    quantity: float
    pnl: float
    pnl_percent: float
    exit_reason: str
    entry_reason: str
    # 学习数据
    support_price: float
    resistance_price: float
    support_score: float
    resistance_score: float
    level_was_effective: bool  # 支撑/阻力位是否有效
    ai_sl_tp: Optional[Dict] = None
    support_features: Optional[Dict] = None  # 支撑位特征 (用于特征学习)
    resistance_features: Optional[Dict] = None  # 阻力位特征 (用于特征学习)


class BacktestTrainer:
    """
    回测训练器 - 专门用于快速积累学习数据
    支持同时训练：
    1. 特征学习 (LevelFinder)
    2. 止损止盈 AI (SLTPLearner)
    3. 入场 AI (EntryLearnerV2)
    """
    
    def __init__(self, data_dir: str = "rl_data", initial_balance: float = 10000.0,
                 leverage: int = 10, train_real: bool = False, progress_callback=None):
        self.data_dir = data_dir
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage = leverage
        self.train_real = train_real
        self.progress_callback = progress_callback
        
        # 技术分析器
        self.analyzer = TechnicalAnalyzer()
        
        # 决定数据文件名
        if train_real:
            print("[WARNING] 警告: 正在使用实盘数据文件进行训练！这将改变实盘 AI 的行为。")
            level_file = os.path.join(data_dir, "level_stats.json")
            # EntryLearnerV2 内部固定了文件名
        else:
            print("[NOTE] 使用临时测试文件，不影响实盘数据。")

            level_file = os.path.join(data_dir, "backtest_level_stats.json")
            # EntryLearnerV2 需要特殊处理
        
        # 1. 初始化特征学习
        self.level_finder = BestLevelFinder(
            stats_path=level_file
        )
        
        # 2. 初始化止损止盈 AI
        if train_real:
            sl_tp_data_dir = data_dir
        else:
            sl_tp_data_dir = os.path.join(data_dir, "backtest_temp")
            os.makedirs(sl_tp_data_dir, exist_ok=True)
            
        self.sl_tp_learner = SLTPLearner(
            data_dir=sl_tp_data_dir
        )
        
        # 3. 初始化入场 AI 
        entry_data_dir = data_dir
        if not train_real:
            entry_data_dir = os.path.join(data_dir, "backtest_temp")
            os.makedirs(entry_data_dir, exist_ok=True)
            
        self.entry_learner = EntryLearnerV2(
            data_dir=entry_data_dir
        )
        
        # 当前持仓
        self.position: Optional[BacktestPosition] = None
        
        # 交易记录
        self.trades: List[BacktestTrade] = []
        
        # 统计
        self.stats = {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0,
            "max_drawdown": 0,
            "peak_balance": initial_balance,
        }
        
        
        # 入场参数（优化后的配置 - 确保训练有效）
        self.params = {
            "distance_threshold": 2.0,  # 距离支撑阻力位 2% 以内可入场
            "min_level_score": 10,  # ⚠️ 关键：最低10分，过滤低质量信号
            "position_size_pct": 5,
            "cooldown_bars": 3,
        }
        
        # 冷却计数器
        self._cooldown = 0
        self._trade_counter = 0
    
    def load_csv_data(self, csv_file: str) -> List[Dict]:
        """加载CSV数据"""
        data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # 处理时间戳 - 支持多种格式
                    timestamp = row.get("timestamp", row.get("open_time", "0"))
                    if isinstance(timestamp, str) and "-" in timestamp:
                        # 字符串格式: "2024-04-06 00:00:00"
                        from datetime import datetime as dt
                        ts = int(dt.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
                    else:
                        ts = int(timestamp)
                    
                    data.append({
                        "time": ts,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row["volume"]),
                    })
                except (KeyError, ValueError) as e:
                    continue
        
        print(f"[OK] 加载了 {len(data)} 根K线数据")
        if data:
            print(f"    时间范围: {self._format_time(data[0]['time'])} ~ {self._format_time(data[-1]['time'])}")
        return data
    
    def run_backtest(self, csv_file: str, max_trades: int = 500, 
                     start_idx: int = 200) -> Dict:
        """运行回测训练"""
        all_data = self.load_csv_data(csv_file)
        
        if len(all_data) < start_idx + 100:
            print(f"[X] 数据不足: {len(all_data)} 根K线")
            return {"error": "数据不足"}
        
        total_bars = len(all_data) - start_idx
        print(f"\n{'='*60}")
        print(f"开始回测训练 (实盘模式: {self.train_real})")
        print(f"数据范围: {total_bars} 根K线")
        print(f"目标交易数: {max_trades}")
        print(f"{'='*60}\n")
        
        for i in range(start_idx, len(all_data)):
            if self.stats["total_trades"] >= max_trades:
                print(f"\n[OK] 达到目标交易数 {max_trades}")
                break
            
            window_1m = all_data[max(0, i-150):i+1]
            klines_dict = self._build_multi_timeframe(window_1m)
            
            current_price = window_1m[-1]["close"]
            current_time = window_1m[-1]["time"]
            
            if self._cooldown > 0:
                self._cooldown -= 1
            
            if self.position:
                self._check_exit(current_price, current_time, klines_dict, all_data, i)
            
            if not self.position and self._cooldown == 0:
                market_state = self._build_market_state(klines_dict)
                market_state["current_price"] = current_price
                self._try_entry(current_price, current_time, klines_dict, market_state)
            
            if self.progress_callback and i % 100 == 0:
                progress = (i - start_idx) / total_bars * 100
                self.progress_callback({
                    "progress": progress,
                    "trades": self.stats["total_trades"],
                    "balance": self.balance,
                    "pnl": self.balance - self.initial_balance,
                })
        
        # 强制平仓
        if self.position:
            self._force_close(all_data[-1]["close"], all_data[-1]["time"], all_data, len(all_data)-1)
        
        self._print_results()
        
        return {
            "total_trades": self.stats["total_trades"],
            "wins": self.stats["wins"],
            "losses": self.stats["losses"],
            "win_rate": self.stats["wins"] / max(1, self.stats["total_trades"]),
            "total_pnl": self.stats["total_pnl"],
            "final_balance": self.balance,
            "max_drawdown": self.stats["max_drawdown"],
        }
    
    def run_random_backtest(self, csv_file: str, max_trades: int = 500,
                            start_idx: int = 200) -> Dict:
        """
        🚀 随机采样回测训练
        逻辑：随机跳到一个时间点，寻找入场机会，交易完成后再跳到另一个随机点。
        """
        all_data = self.load_csv_data(csv_file)
        if len(all_data) < start_idx + 1000:
            return {"error": "数据不足"}
            
        print(f"\n{'='*60}")
        print(f"开始随机采样回测 (实盘模式: {self.train_real})")
        print(f"目标交易数: {max_trades}")
        print(f"{'='*60}\n")
        
        while self.stats["total_trades"] < max_trades:
            # 1. 随机选一个起始点（预留至少500根K线的空间）
            i = random.randint(start_idx, len(all_data) - 501)
            
            # 2. 从该点开始模拟
            timeout_counter = 0
            max_timeout = 500 # 最多等500分钟，没机会就跳走
            
            while timeout_counter < max_timeout and self.stats["total_trades"] < max_trades:
                idx = i + timeout_counter
                window_1m = all_data[max(0, idx-150):idx+1]
                klines_dict = self._build_multi_timeframe(window_1m)
                
                current_price = window_1m[-1]["close"]
                current_time = window_1m[-1]["time"]
                
                # 处理持仓
                if self.position:
                    self._check_exit(current_price, current_time, klines_dict, all_data, idx)
                    if not self.position: # 交易结束，立刻跳走
                        break
                else:
                    # 寻找入场
                    market_state = self._build_market_state(klines_dict)
                    market_state["current_price"] = current_price
                    self._try_entry(current_price, current_time, klines_dict, market_state)
                    
                timeout_counter += 1
                
                # 进度回调
                if self.progress_callback and timeout_counter % 50 == 0:
                    self.progress_callback({
                        "progress": (self.stats["total_trades"] / max_trades) * 100,
                        "trades": self.stats["total_trades"],
                        "balance": self.balance,
                        "pnl": self.balance - self.initial_balance,
                    })

            # 强制清空当前位置状态，准备下一次跳转
            if self.position:
                self._force_close(all_data[i + timeout_counter]["close"], all_data[i + timeout_counter]["time"], all_data, i + timeout_counter)
                
        self._print_results()
        return self.stats
    
    def _build_multi_timeframe(self, klines_1m: List[Dict]) -> Dict:
        """
        从1分钟数据构建多周期数据
        使用足够长的历史数据以便准确发现支撑阻力位
        """
        # 使用最近2000根1分钟K线（约33小时）
        # 这样可以生成约133根15分钟K线，4根8小时K线
        lookback = min(2000, len(klines_1m))
        recent_1m = klines_1m[-lookback:] if lookback > 0 else klines_1m
        
        klines_15m = self._resample_klines(recent_1m, 15)
        klines_8h = self._resample_klines(recent_1m, 480)  # 8小时 = 480分钟
        
        return {
            "1m": recent_1m[-200:] if len(recent_1m) >= 200 else recent_1m,  # 最近200根用于特征计算
            "15m": klines_15m,
            "8h": klines_8h,
            "1w": klines_8h[-4:] if len(klines_8h) >= 4 else klines_8h,  # 用8小时数据模拟周线
        }
    
    def _resample_klines(self, klines: List[Dict], period: int) -> List[Dict]:
        """重采样K线数据"""
        if len(klines) < period:
            return klines
        
        resampled = []
        for i in range(0, len(klines) - period + 1, period):
            chunk = klines[i:i+period]
            resampled.append({
                "time": chunk[0]["time"],
                "open": chunk[0]["open"],
                "high": max(k["high"] for k in chunk),
                "low": min(k["low"] for k in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(k["volume"] for k in chunk),
            })
        return resampled

    def _build_market_state(self, klines_dict: Dict) -> Dict:
        """构建市场状态供 AI 使用"""
        # 简单计算指标
        klines_15m = klines_dict["15m"]
        klines_1m = klines_dict["1m"]
        
        # 趋势
        ma7 = sum(k["close"] for k in klines_15m[-7:]) / 7 if len(klines_15m) >= 7 else 0
        ma25 = sum(k["close"] for k in klines_15m[-25:]) / 25 if len(klines_15m) >= 25 else 0
        
        trend_direction = "BULLISH" if ma7 > ma25 else "BEARISH"
        
        # RSI (简化计算)
        rsi_15m = 50 
        if len(klines_15m) > 14:
            gains = 0
            losses = 0
            for i in range(1, 15):
                change = klines_15m[-i]["close"] - klines_15m[-i-1]["close"]
                if change > 0: gains += change
                else: losses -= change
            if losses > 0:
                rs = gains / losses
                rsi_15m = 100 - (100 / (1 + rs))
        
        return {
            "macro_trend": {"direction": trend_direction, "strength": 50},
            "micro_trend": {"direction": trend_direction},
            "analysis_15m": {
                "rsi": rsi_15m,
                "trend": trend_direction
            },
            "analysis_1m": {
                "rsi": rsi_15m, 
                "volume_ratio": 1.0
            }
        }

    def _try_entry(self, price: float, time: int, klines_dict: Dict, market_state: Dict):
        """尝试入场"""
        
        # 1. 找支撑阻力位 (Feature Learning)
        level_result = self.level_finder.find_from_klines(klines_dict, price)
        best_support = level_result.get("best_support")
        best_resistance = level_result.get("best_resistance")
        
        market_state["best_support"] = best_support
        market_state["best_resistance"] = best_resistance
        
        # 计算距离
        support_dist = abs(price - best_support["price"]) / price * 100 if best_support else 999
        resistance_dist = abs(best_resistance["price"] - price) / price * 100 if best_resistance else 999
        
        direction = None
        entry_reason = ""
        level_score = 0
        
        threshold = self.params["distance_threshold"]
        min_score = self.params["min_level_score"]
        
        # 🎯 强制使用支撑阻力位入场（用于特征学习）
        # 优先选择得分最高的方向
        support_valid = best_support and support_dist < threshold and best_support["score"] >= min_score
        resistance_valid = best_resistance and resistance_dist < threshold and best_resistance["score"] >= min_score
        
        if support_valid and resistance_valid:
            # 两个都有效，选择得分更高的
            if best_support["score"] > best_resistance["score"]:
                direction = "LONG"
                entry_reason = "NEAR_SUPPORT"
                level_score = best_support["score"]
            else:
                direction = "SHORT"
                entry_reason = "NEAR_RESISTANCE"
                level_score = best_resistance["score"]
        elif support_valid:
            direction = "LONG"
            entry_reason = "NEAR_SUPPORT"
            level_score = best_support["score"]
        elif resistance_valid:
            direction = "SHORT"
            entry_reason = "NEAR_RESISTANCE"
            level_score = best_resistance["score"]
        # 🔥 完全移除随机探索，确保所有交易都基于特征学习
        
        if direction:
            # 2. 询问 SL/TP AI 获取建议 (使用 predict)
            sl_tp_suggestion = self.sl_tp_learner.predict(market_state, direction)
            
            # 3. 询问 Entry AI 获取评分 (记录这次决策)
            conditions = {
                "support_distance": support_dist / 100 if support_dist != 999 else 1,
                "resistance_distance": resistance_dist / 100 if resistance_dist != 999 else 1,
                "trend_aligned": True,
                "rsi": market_state["analysis_15m"]["rsi"]
            }
            
            trade_id = f"bt_{self._trade_counter+1:05d}"
            
            entry_index = self.entry_learner.record_entry(
                trade_id=trade_id,
                market_state=market_state,
                direction=direction,
                entry_reason=entry_reason,
                conditions=conditions,
                base_score=level_score
            )
            
            self._open_position(
                trade_id=trade_id,
                direction=direction,
                price=price,
                time=time,
                entry_reason=entry_reason,
                entry_score=level_score,
                support=best_support,
                resistance=best_resistance,
                sl_tp_suggestion=sl_tp_suggestion
            )
    
    def _open_position(self, trade_id: str, direction: str, price: float, time: int,
                       entry_reason: str, entry_score: float,
                       support: Dict, resistance: Dict, sl_tp_suggestion: Dict):
        """开仓"""
        self._trade_counter += 1
        
        position_value = self.balance * self.params["position_size_pct"] / 100 * self.leverage
        quantity = position_value / price
        
        # 使用 AI 建议的 SL/TP 比例
        sl_pct = sl_tp_suggestion["stop_loss_pct"]
        tp_pct = sl_tp_suggestion["take_profit_pct"]
        
        if direction == "LONG":
            stop_loss = price * (1 - sl_pct)
            take_profit = price * (1 + tp_pct)
        else:
            stop_loss = price * (1 + sl_pct)
            take_profit = price * (1 - tp_pct)
        
        self.position = BacktestPosition(
            trade_id=trade_id,
            direction=direction,
            entry_price=price,
            entry_time=self._format_time(time),
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_reason=entry_reason,
            entry_score=entry_score,
            support_price=support["price"] if support else 0,
            resistance_price=resistance["price"] if resistance else 0,
            support_score=support["score"] if support else 0,
            resistance_score=resistance["score"] if resistance else 0,
            ai_sl_tp=sl_tp_suggestion,
            support_features=support.get("features", {}) if support else {},
            resistance_features=resistance.get("features", {}) if resistance else {}
        )
        
        print(f"[>] {trade_id} {direction} @ {price:.2f} | SL:{sl_pct*100:.1f}% TP:{tp_pct*100:.1f}%")
    
    def _check_exit(self, price: float, time: int, klines_dict: Dict, all_data: List[Dict], current_idx: int):
        """检查出场条件"""
        pos = self.position
        exit_reason = None
        
        if pos.direction == "LONG":
            if price <= pos.stop_loss: exit_reason = "STOP_LOSS"
            elif price >= pos.take_profit: exit_reason = "TAKE_PROFIT"
            elif pos.resistance_price > 0 and price >= pos.resistance_price * 0.998:
                exit_reason = "HIT_RESISTANCE"
        else:  # SHORT
            if price >= pos.stop_loss: exit_reason = "STOP_LOSS"
            elif price <= pos.take_profit: exit_reason = "TAKE_PROFIT"
            elif pos.support_price > 0 and price <= pos.support_price * 1.002:
                exit_reason = "HIT_SUPPORT"
        
        if exit_reason:
            self._close_position(price, time, exit_reason, all_data, current_idx)
    
    def _close_position(self, price: float, time: int, exit_reason: str, all_data: List[Dict], current_idx: int):
        """平仓"""
        pos = self.position
        
        # 计算盈亏
        if pos.direction == "LONG":
            pnl_percent = (price - pos.entry_price) / pos.entry_price * 100
        else:
            pnl_percent = (pos.entry_price - price) / pos.entry_price * 100
        
        pnl = pos.quantity * pos.entry_price * pnl_percent / 100
        
        # 判断支撑/阻力位是否有效
        level_was_effective = False
        if pos.direction == "LONG" and pos.support_price > 0:
            level_was_effective = price > pos.support_price * 0.995
        elif pos.direction == "SHORT" and pos.resistance_price > 0:
            level_was_effective = price < pos.resistance_price * 1.005
        
        # 记录交易
        trade = BacktestTrade(
            trade_id=pos.trade_id,
            direction=pos.direction,
            entry_price=pos.entry_price,
            exit_price=price,
            entry_time=pos.entry_time,
            exit_time=self._format_time(time),
            quantity=pos.quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            exit_reason=exit_reason,
            entry_reason=pos.entry_reason,
            support_price=pos.support_price,
            resistance_price=pos.resistance_price,
            support_score=pos.support_score,
            resistance_score=pos.resistance_score,
            level_was_effective=level_was_effective,
            ai_sl_tp=pos.ai_sl_tp,
            support_features=getattr(pos, "support_features", None),
            resistance_features=getattr(pos, "resistance_features", None)
        )
        self.trades.append(trade)
        
        # 更新统计
        self.balance += pnl
        self.stats["total_trades"] += 1
        self.stats["total_pnl"] += pnl
        
        if pnl > 0:
            self.stats["wins"] += 1
            emoji = "[OK]"
        else:
            self.stats["losses"] += 1
            emoji = "[X]"
        
        # 更新三个 AI 模块
        # 准备事后分析 (偷看未来 5 分钟数据)
        peek_idx = min(len(all_data)-1, current_idx + 5)
        price_after = all_data[peek_idx]["close"]
        price_change_after = (price_after - price) / price * 100
        
        post_analysis = {
            "price_change_after": price_change_after,
            "exit_price": price
        }
        
        self._update_learning(trade, post_analysis)
        
        print(f"{emoji} {pos.trade_id} 平仓: {pnl:+.2f} ({pnl_percent:+.2f}%) | {exit_reason}")
        
        self.position = None
        self._cooldown = self.params["cooldown_bars"]
    
    def _force_close(self, price: float, time: int, all_data: List[Dict], current_idx: int):
        """强制平仓"""
        if self.position:
            self._close_position(price, time, "FORCE_CLOSE", all_data, current_idx)
    
    def _update_learning(self, trade: BacktestTrade, post_analysis: Dict):
        """更新所有学习系统"""
        
        # 1. 更新特征学习 (LevelFinder)
        if trade.entry_reason in ["NEAR_SUPPORT", "NEAR_RESISTANCE"]:
            if trade.direction == "LONG":
                # 做多使用支撑位，从 market_state 的 best_support 获取 features
                level_used = {
                    "price": trade.support_price, 
                    "score": trade.support_score, 
                    "features": getattr(trade, "support_features", {})
                }
            else:
                # 做空使用阻力位，从 market_state 的 best_resistance 获取 features
                level_used = {
                    "price": trade.resistance_price, 
                    "score": trade.resistance_score, 
                    "features": getattr(trade, "resistance_features", {})
                }
            
            self.level_finder.record_trade_result(
                level_used=level_used,
                was_effective=trade.level_was_effective,
                pnl_percent=trade.pnl_percent,
                level_type="ENTRY"
            )
            
        # 2. 更新止损止盈 AI (SLTPLearning)
        if trade.ai_sl_tp and "features" in trade.ai_sl_tp:
            sl_tp_used = {
                "sl_pct": trade.ai_sl_tp["stop_loss_pct"],
                "tp_pct": trade.ai_sl_tp["take_profit_pct"]
            }
            
            trade_result = {
                "pnl_percent": trade.pnl_percent,
                "exit_reason": trade.exit_reason,
                "direction": trade.direction,
                "sl_pct_used": sl_tp_used["sl_pct"],
                "tp_pct_used": sl_tp_used["tp_pct"]
            }
            
            self.sl_tp_learner.record_trade(
                entry_features=np.array(trade.ai_sl_tp["features"]),
                sl_tp_used=sl_tp_used,
                trade_result=trade_result,
                post_analysis=post_analysis,
                predicted_params=trade.ai_sl_tp
            )

        # 3. 更新入场 AI (EntryLearnerV2)
        # 通过 trade_id 匹配之前的入场记录
        self.entry_learner.update_entry_result(
            trade_id=trade.trade_id,
            pnl_percent=trade.pnl_percent,
            exit_reason=trade.exit_reason
        )
    
    def _print_results(self):
        """打印回测结果"""
        print(f"\n{'='*60}")
        print("回测训练结果")
        print(f"{'='*60}")
        print(f"总交易数: {self.stats['total_trades']}")
        print(f"盈利: {self.stats['wins']} | 亏损: {self.stats['losses']}")
        print(f"胜率: {self.stats['wins']/max(1,self.stats['total_trades'])*100:.1f}%")
        print(f"总盈亏: {self.stats['total_pnl']:+.2f} USDT")
        print(f"最终余额: {self.balance:.2f} USDT")
        print(f"最大回撤: {self.stats['max_drawdown']:.1f}%")
        print(f"{'='*60}\n")
    
    def _format_time(self, timestamp: int) -> str:
        """格式化时间戳"""
        if timestamp > 1e12:
            timestamp = timestamp // 1000
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="回测训练系统")
    parser.add_argument("--csv", type=str, default="btcusdt_1m_300days.csv",
                        help="CSV数据文件")
    parser.add_argument("--max-trades", type=int, default=500,
                        help="最大交易次数")
    parser.add_argument("--start-idx", type=int, default=200,
                        help="从第几根K线开始")
    parser.add_argument("--data-dir", type=str, default="rl_data",
                        help="数据保存目录")
    parser.add_argument("--train-real", action="store_true",
                        help="是否直接训练实盘数据文件（警告：会改变实盘AI行为）")
    parser.add_argument("--random-mode", action="store_true",
                        help="是否启用随机采样回测模式")
    
    args = parser.parse_args()
    
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(__file__), csv_path)
    
    if not os.path.exists(csv_path):
        print(f"[X] 找不到数据文件: {csv_path}")
        return
    
    trainer = BacktestTrainer(
        data_dir=args.data_dir,
        initial_balance=10000.0,
        leverage=10,
        train_real=args.train_real
    )
    
    if args.random_mode:
        trainer.run_random_backtest(
            csv_file=csv_path,
            max_trades=args.max_trades,
            start_idx=args.start_idx,
        )
    else:
        trainer.run_backtest(
            csv_file=csv_path,
            max_trades=args.max_trades,
            start_idx=args.start_idx,
        )
    
    print("\n[OK] 回测训练完成!")
    if args.train_real:
        print(f"实盘AI参数已更新！")


if __name__ == "__main__":
    main()
