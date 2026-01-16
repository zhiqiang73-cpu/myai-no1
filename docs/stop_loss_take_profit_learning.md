# 止盈止损的强化学习设计

## 核心洞察

止盈止损的本质是：**在哪个价位离场能最大化收益**

这与支撑阻力位直接相关：
- 止损应该设在支撑位下方（做多）或阻力位上方（做空）
- 止盈应该设在下一个阻力位（做多）或支撑位（做空）

**关键问题**：AI如何学会找到最优的止盈止损位置？

---

## 一、止盈止损学习的三种方案

### 方案A：固定规则 + 参数优化（简单但有效）

```
止损 = 入场价 ± ATR × 止损倍数
止盈 = 入场价 ± ATR × 止盈倍数

AI学习的是：最优的止损倍数和止盈倍数
```

**优点**：简单，容易学习
**缺点**：不考虑市场结构，可能错过更好的位置

### 方案B：基于支撑阻力的动态止盈止损（推荐）⭐

```
止损 = 最近的支撑/阻力位 ± 缓冲距离
止盈 = 下一个阻力/支撑位

AI学习的是：
1. 哪些价位是有效的支撑阻力
2. 缓冲距离应该多大
3. 是否应该分批止盈
```

**优点**：符合市场逻辑，止盈止损有依据
**缺点**：需要先学会识别支撑阻力

### 方案C：完全由AI决定（最灵活但最难）

```
AI直接输出：止损价格、止盈价格

动作空间扩展为：
[方向, 仓位, 止损价, 止盈价]
```

**优点**：最灵活
**缺点**：搜索空间太大，难以收敛

---

## 二、推荐方案：分层学习

我建议采用**分层学习**，把问题拆解：

```
┌─────────────────────────────────────────────────────────────────┐
│                    分层学习架构                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: 价位发现层 (Level Discovery)                           │
│  ├── 输入: K线数据、成交量数据                                    │
│  ├── 输出: 候选支撑阻力位列表                                     │
│  ├── 方法: 技术分析 + 统计验证                                    │
│  └── 学习: 哪些价位被市场尊重（价格在此反转）                      │
│                                                                 │
│  Layer 2: 价位评分层 (Level Scoring)                             │
│  ├── 输入: 候选价位 + 历史交易结果                                │
│  ├── 输出: 每个价位的有效性得分                                   │
│  ├── 方法: 强化学习更新得分                                       │
│  └── 学习: 在某价位交易的成功率和盈亏比                           │
│                                                                 │
│  Layer 3: 止盈止损决策层 (SL/TP Decision)                        │
│  ├── 输入: 入场价 + 评分后的支撑阻力位                            │
│  ├── 输出: 止损价、止盈价（可能多个目标）                         │
│  ├── 方法: 基于规则 + AI微调                                     │
│  └── 学习: 最优的缓冲距离、是否分批止盈                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、Layer 1: 价位发现 - 详细实现

### 3.1 价位候选生成

```python
class LevelDiscovery:
    """价位发现器"""
    
    def __init__(self):
        self.candidate_levels = []  # 候选价位
        self.confirmed_levels = []  # 已确认的有效价位
    
    def discover_levels(self, klines_15m, klines_8h, current_price):
        """
        发现候选支撑阻力位
        """
        candidates = []
        
        # 1. Pivot Points
        pivots = self._find_pivots(klines_15m)
        candidates.extend(pivots)
        
        # 2. Volume Nodes
        volume_levels = self._find_volume_nodes(klines_8h)
        candidates.extend(volume_levels)
        
        # 3. Round Numbers
        round_levels = self._find_round_numbers(current_price)
        candidates.extend(round_levels)
        
        # 4. 合并相近价位
        merged = self._merge_nearby_levels(candidates)
        
        # 5. 初始化得分
        for level in merged:
            level["score"] = level.get("initial_score", 50)
            level["touch_count"] = 0
            level["success_count"] = 0
            level["total_pnl"] = 0
        
        return merged
```

### 3.2 价位的"触及"检测

```python
def detect_level_touch(self, price_history, level, threshold_percent=0.3):
    """
    检测价格是否触及某个价位
    
    触及的定义：
    1. 价格接近该价位（距离 < threshold）
    2. 然后发生反转（反向移动超过threshold）
    """
    level_price = level["price"]
    touches = []
    
    for i in range(1, len(price_history) - 1):
        current = price_history[i]
        prev = price_history[i - 1]
        next_price = price_history[i + 1]
        
        # 计算距离
        distance_percent = abs(current - level_price) / level_price * 100
        
        if distance_percent < threshold_percent:
            # 价格接近该价位，检查是否反转
            came_from = "above" if prev > current else "below"
            went_to = "above" if next_price > current else "below"
            
            if came_from != went_to:
                # 发生反转！
                touches.append({
                    "index": i,
                    "price": current,
                    "direction": came_from,
                    "bounced": True
                })
            else:
                # 穿越了该价位
                touches.append({
                    "index": i,
                    "price": current,
                    "direction": came_from,
                    "bounced": False,
                    "broke_through": True
                })
    
    return touches
```

---

## 四、Layer 2: 价位评分 - 强化学习核心

### 4.1 评分更新机制

```python
class LevelScoring:
    """
    价位评分系统
    
    核心思想：
    - 每次在某价位附近交易，记录结果
    - 成功的交易提升该价位得分
    - 失败的交易降低该价位得分
    - 得分高的价位更可能被用作止盈止损
    """
    
    def __init__(self, learning_rate=0.1):
        self.lr = learning_rate
        self.levels = {}  # price -> LevelStats
    
    def update_level_score(self, level_price, trade_result):
        """
        根据交易结果更新价位得分
        
        trade_result = {
            "entry_price": 92000,
            "exit_price": 92500,
            "direction": "LONG",
            "pnl_percent": 0.54,
            "used_as": "SUPPORT",  # 这个价位被用作什么
            "outcome": "BOUNCE"    # BOUNCE(反弹成功) / BREAK(突破失败)
        }
        """
        if level_price not in self.levels:
            self.levels[level_price] = {
                "score": 50,
                "touch_count": 0,
                "bounce_count": 0,
                "break_count": 0,
                "total_pnl": 0,
                "trades": []
            }
        
        stats = self.levels[level_price]
        stats["touch_count"] += 1
        stats["trades"].append(trade_result)
        
        if trade_result["outcome"] == "BOUNCE":
            # 价位有效，价格在此反弹
            stats["bounce_count"] += 1
            
            # 得分更新：成功反弹 + 盈利 = 大幅加分
            if trade_result["pnl_percent"] > 0:
                score_delta = self.lr * (10 + trade_result["pnl_percent"] * 5)
            else:
                # 反弹了但还是亏钱（可能入场时机不对）
                score_delta = self.lr * 2
            
            stats["score"] = min(100, stats["score"] + score_delta)
            
        elif trade_result["outcome"] == "BREAK":
            # 价位失效，价格突破了
            stats["break_count"] += 1
            
            # 得分更新：突破 = 减分
            score_delta = self.lr * (5 + abs(trade_result["pnl_percent"]) * 3)
            stats["score"] = max(0, stats["score"] - score_delta)
        
        stats["total_pnl"] += trade_result["pnl_percent"]
        
        # 计算成功率
        if stats["touch_count"] > 0:
            stats["success_rate"] = stats["bounce_count"] / stats["touch_count"]
        
        return stats
    
    def get_best_levels(self, current_price, direction, top_n=5):
        """
        获取最佳的支撑阻力位用于止盈止损
        
        direction: "LONG" or "SHORT"
        """
        support_levels = []
        resistance_levels = []
        
        for price, stats in self.levels.items():
            if stats["score"] < 30:  # 过滤低分价位
                continue
            if stats["touch_count"] < 2:  # 至少被验证过2次
                continue
            
            level_info = {
                "price": price,
                "score": stats["score"],
                "success_rate": stats.get("success_rate", 0),
                "touch_count": stats["touch_count"]
            }
            
            if price < current_price:
                support_levels.append(level_info)
            else:
                resistance_levels.append(level_info)
        
        # 按得分排序
        support_levels.sort(key=lambda x: x["score"], reverse=True)
        resistance_levels.sort(key=lambda x: x["score"], reverse=True)
        
        if direction == "LONG":
            return {
                "stop_loss_candidates": support_levels[:top_n],
                "take_profit_candidates": resistance_levels[:top_n]
            }
        else:
            return {
                "stop_loss_candidates": resistance_levels[:top_n],
                "take_profit_candidates": support_levels[:top_n]
            }
```

### 4.2 价位得分的衰减机制

```python
def decay_old_levels(self, current_time, decay_rate=0.99):
    """
    长期未被触及的价位，得分逐渐衰减
    
    原因：市场结构会变化，旧的支撑阻力可能失效
    """
    for price, stats in self.levels.items():
        if stats["trades"]:
            last_trade_time = stats["trades"][-1].get("time")
            days_since_last = (current_time - last_trade_time).days
            
            if days_since_last > 7:
                # 超过7天未触及，开始衰减
                decay_factor = decay_rate ** (days_since_last - 7)
                stats["score"] *= decay_factor
```

---

## 五、Layer 3: 止盈止损决策

### 5.1 基于评分价位的止盈止损

```python
class StopLossTakeProfitDecision:
    """
    止盈止损决策器
    """
    
    def __init__(self, level_scoring: LevelScoring):
        self.scoring = level_scoring
        
        # 可学习的参数
        self.params = {
            "sl_buffer_atr_mult": 0.5,   # 止损缓冲 = ATR × 这个值
            "min_risk_reward": 1.5,       # 最小风险收益比
            "partial_tp_enabled": True,   # 是否分批止盈
            "partial_tp_ratio": 0.5,      # 第一目标止盈比例
        }
    
    def calculate_sl_tp(self, entry_price, direction, atr, current_price):
        """
        计算止损止盈位置
        
        逻辑：
        1. 找到最近的高分支撑/阻力位
        2. 止损设在该价位外侧 + 缓冲
        3. 止盈设在下一个高分阻力/支撑位
        4. 检查风险收益比，不满足则放弃交易
        """
        
        # 获取候选价位
        levels = self.scoring.get_best_levels(current_price, direction)
        
        if direction == "LONG":
            # 做多：止损在支撑下方，止盈在阻力
            sl_candidates = levels["stop_loss_candidates"]
            tp_candidates = levels["take_profit_candidates"]
            
            if not sl_candidates:
                # 没有已知支撑，使用ATR
                stop_loss = entry_price - atr * 1.5
            else:
                # 使用最近的高分支撑
                nearest_support = min(sl_candidates, key=lambda x: entry_price - x["price"])
                buffer = atr * self.params["sl_buffer_atr_mult"]
                stop_loss = nearest_support["price"] - buffer
            
            if not tp_candidates:
                # 没有已知阻力，使用风险收益比计算
                risk = entry_price - stop_loss
                take_profit = entry_price + risk * self.params["min_risk_reward"]
            else:
                # 使用最近的高分阻力
                nearest_resistance = min(tp_candidates, key=lambda x: x["price"] - entry_price)
                take_profit = nearest_resistance["price"]
        
        else:  # SHORT
            sl_candidates = levels["stop_loss_candidates"]
            tp_candidates = levels["take_profit_candidates"]
            
            if not sl_candidates:
                stop_loss = entry_price + atr * 1.5
            else:
                nearest_resistance = min(sl_candidates, key=lambda x: x["price"] - entry_price)
                buffer = atr * self.params["sl_buffer_atr_mult"]
                stop_loss = nearest_resistance["price"] + buffer
            
            if not tp_candidates:
                risk = stop_loss - entry_price
                take_profit = entry_price - risk * self.params["min_risk_reward"]
            else:
                nearest_support = min(tp_candidates, key=lambda x: entry_price - x["price"])
                take_profit = nearest_support["price"]
        
        # 计算风险收益比
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        return {
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk": risk,
            "reward": reward,
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "is_valid": risk_reward_ratio >= self.params["min_risk_reward"],
            "sl_based_on": "SUPPORT_LEVEL" if sl_candidates else "ATR",
            "tp_based_on": "RESISTANCE_LEVEL" if tp_candidates else "RISK_REWARD",
        }
```

### 5.2 参数的强化学习优化

```python
class SLTPParameterLearner:
    """
    学习最优的止盈止损参数
    
    使用简单的进化策略：
    1. 维护一组参数
    2. 每N笔交易评估效果
    3. 好的参数保留，差的参数变异
    """
    
    def __init__(self):
        # 参数搜索空间
        self.param_space = {
            "sl_buffer_atr_mult": (0.2, 1.0),   # 范围
            "min_risk_reward": (1.0, 3.0),
            "partial_tp_ratio": (0.3, 0.7),
        }
        
        # 当前最优参数
        self.best_params = {
            "sl_buffer_atr_mult": 0.5,
            "min_risk_reward": 1.5,
            "partial_tp_ratio": 0.5,
        }
        self.best_score = 0
        
        # 参数历史
        self.param_history = []
    
    def evaluate_params(self, trades):
        """
        评估当前参数的效果
        """
        if len(trades) < 20:
            return None
        
        # 计算关键指标
        wins = sum(1 for t in trades if t["pnl"] > 0)
        win_rate = wins / len(trades)
        
        total_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
        total_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 综合得分
        score = win_rate * 0.3 + min(profit_factor, 3) / 3 * 0.7
        
        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "score": score,
            "trades_count": len(trades)
        }
    
    def mutate_params(self, mutation_rate=0.1):
        """
        变异参数，探索新的组合
        """
        import random
        
        new_params = {}
        for key, (min_val, max_val) in self.param_space.items():
            current = self.best_params[key]
            
            # 高斯变异
            mutation = random.gauss(0, (max_val - min_val) * mutation_rate)
            new_value = current + mutation
            
            # 限制在范围内
            new_value = max(min_val, min(max_val, new_value))
            new_params[key] = round(new_value, 3)
        
        return new_params
    
    def update(self, trades, current_params):
        """
        根据交易结果更新参数
        """
        eval_result = self.evaluate_params(trades)
        if eval_result is None:
            return
        
        self.param_history.append({
            "params": current_params.copy(),
            "result": eval_result
        })
        
        if eval_result["score"] > self.best_score:
            self.best_score = eval_result["score"]
            self.best_params = current_params.copy()
            print(f"🎯 发现更优参数! Score: {eval_result['score']:.3f}")
            print(f"   Win Rate: {eval_result['win_rate']:.1%}")
            print(f"   Profit Factor: {eval_result['profit_factor']:.2f}")
            print(f"   Params: {self.best_params}")
```
