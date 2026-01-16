# 技术分析指标规格 + 支撑阻力初始识别方案

---

## 一、技术指标明细

### 1.1 趋势类指标

| 指标 | 参数 | 用途 | 计算周期 |
|------|------|------|----------|
| EMA | 7, 25, 99 | 短中长期趋势 | 1m, 15m, 8h, 1w |
| SMA | 20, 50, 200 | 经典均线系统 | 15m, 8h |
| ADX | 14 | 趋势强度 (>25强趋势) | 15m, 8h |

**趋势判断逻辑：**
```python
def get_trend(close, ema7, ema25, ema99):
    if close > ema7 > ema25 > ema99:
        return "STRONG_UP"      # 强上涨
    elif close > ema25 > ema99:
        return "UP"             # 上涨
    elif close < ema7 < ema25 < ema99:
        return "STRONG_DOWN"    # 强下跌
    elif close < ema25 < ema99:
        return "DOWN"           # 下跌
    else:
        return "SIDEWAYS"       # 震荡
```

### 1.2 动量类指标

| 指标 | 参数 | 信号 | 计算周期 |
|------|------|------|----------|
| RSI | 14 | <30超卖, >70超买 | 1m, 15m |
| MACD | 12, 26, 9 | 金叉死叉, 背离 | 15m, 8h |
| Stoch RSI | 14, 14, 3, 3 | <20超卖, >80超买 | 15m |

**RSI使用逻辑：**
```python
def rsi_signal(rsi, trend):
    if trend in ["UP", "STRONG_UP"]:
        # 上涨趋势中，RSI回调到40-50是买入机会
        if 35 <= rsi <= 50:
            return "BUY_OPPORTUNITY"
    elif trend in ["DOWN", "STRONG_DOWN"]:
        # 下跌趋势中，RSI反弹到50-65是做空机会
        if 50 <= rsi <= 65:
            return "SHORT_OPPORTUNITY"
    
    # 极端值
    if rsi < 25:
        return "OVERSOLD"       # 超卖，可能反弹
    elif rsi > 75:
        return "OVERBOUGHT"     # 超买，可能回调
    
    return "NEUTRAL"
```

### 1.3 波动率指标

| 指标 | 参数 | 用途 | 计算周期 |
|------|------|------|----------|
| ATR | 14 | 止损止盈距离 | 1m, 15m, 8h |
| Bollinger Bands | 20, 2 | 波动区间, 突破 | 15m, 8h |
| Keltner Channel | 20, 1.5 | 配合BB判断挤压 | 15m |

**ATR用于仓位和止损：**
```python
def calculate_stop_loss(entry_price, direction, atr, multiplier=1.5):
    stop_distance = atr * multiplier
    if direction == "LONG":
        return entry_price - stop_distance
    else:
        return entry_price + stop_distance

def calculate_position_size(account_balance, risk_percent, entry_price, stop_loss):
    """基于风险的仓位计算"""
    risk_amount = account_balance * risk_percent  # 如2%
    price_risk = abs(entry_price - stop_loss)
    position_size = risk_amount / price_risk
    return position_size
```

### 1.4 成交量指标 ⭐重要

| 指标 | 参数 | 用途 | 计算周期 |
|------|------|------|----------|
| Volume | - | 原始成交量 | 1m, 15m, 8h |
| Volume MA | 20 | 成交量均线 | 15m, 8h |
| Volume Ratio | - | 当前量/均量 | 15m |
| OBV | - | 能量潮，趋势确认 | 15m, 8h |
| VWAP | - | 成交量加权均价 | 日内 |
| CVD | - | 累积成交量差 (买-卖) | 15m |

**成交量分析逻辑：**
```python
def analyze_volume(volume, volume_ma, price_change, prev_price_change):
    volume_ratio = volume / volume_ma
    
    result = {
        "volume_ratio": volume_ratio,
        "is_high_volume": volume_ratio > 1.5,
        "is_low_volume": volume_ratio < 0.5,
    }
    
    # 量价配合分析
    if price_change > 0:  # 价格上涨
        if volume_ratio > 1.5:
            result["signal"] = "BULLISH_VOLUME"      # 放量上涨，强势
        elif volume_ratio < 0.7:
            result["signal"] = "WEAK_RALLY"          # 缩量上涨，可能见顶
    elif price_change < 0:  # 价格下跌
        if volume_ratio > 1.5:
            result["signal"] = "BEARISH_VOLUME"      # 放量下跌，弱势
        elif volume_ratio < 0.7:
            result["signal"] = "WEAK_DECLINE"        # 缩量下跌，可能见底
    
    # 成交量突变检测
    if volume_ratio > 3.0:
        result["alert"] = "VOLUME_SPIKE"             # 成交量异常放大
    
    return result
```

**成交量密集区 (Volume Profile) 计算：**
```python
def calculate_volume_profile(klines, num_bins=50):
    """
    计算成交量分布，找出成交密集区
    成交密集区往往是支撑阻力位
    """
    prices = []
    volumes = []
    
    for k in klines:
        # 将每根K线的成交量分配到价格区间
        high, low, volume = k['high'], k['low'], k['volume']
        avg_price = (high + low) / 2
        prices.append(avg_price)
        volumes.append(volume)
    
    # 创建价格区间
    price_min, price_max = min(prices), max(prices)
    bin_size = (price_max - price_min) / num_bins
    
    # 统计每个价格区间的成交量
    volume_profile = {}
    for price, vol in zip(prices, volumes):
        bin_index = int((price - price_min) / bin_size)
        bin_price = price_min + bin_index * bin_size + bin_size / 2
        volume_profile[bin_price] = volume_profile.get(bin_price, 0) + vol
    
    # 找出成交量最大的几个价格区间 (POC - Point of Control)
    sorted_levels = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "poc": sorted_levels[0][0],  # 最大成交量价位
        "high_volume_nodes": [p for p, v in sorted_levels[:5]],  # 前5个高成交量价位
        "value_area": calculate_value_area(sorted_levels),  # 70%成交量区间
    }
```

---

## 二、支撑阻力初始识别方案

### 2.1 识别方法汇总

```
┌─────────────────────────────────────────────────────────────────┐
│              支撑阻力位识别方法 (5种)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  方法1: Pivot Points (局部高低点)                                │
│  ├── 原理: 价格反转的历史位置                                    │
│  ├── 参数: 左右各N根K线 (N=5)                                   │
│  └── 权重: 30%                                                  │
│                                                                 │
│  方法2: Volume Profile (成交量密集区)                            │
│  ├── 原理: 大量交易发生的价位有支撑阻力作用                       │
│  ├── 参数: 统计最近500根K线                                     │
│  └── 权重: 25%                                                  │
│                                                                 │
│  方法3: 整数关口 (Psychological Levels)                         │
│  ├── 原理: 人类心理倾向于关注整数                                │
│  ├── 价位: 90000, 91000, 92000... 95000, 100000                │
│  └── 权重: 15%                                                  │
│                                                                 │
│  方法4: 均线位置 (Dynamic S/R)                                  │
│  ├── 原理: 均线本身就是动态支撑阻力                              │
│  ├── 均线: EMA99(8h), SMA200(8h)                               │
│  └── 权重: 15%                                                  │
│                                                                 │
│  方法5: 前高前低 (Swing High/Low)                               │
│  ├── 原理: 历史的高点低点容易再次起作用                          │
│  ├── 周期: 8h和1w的近期高低点                                   │
│  └── 权重: 15%                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 方法1: Pivot Points 实现

```python
def find_pivot_points(klines, left_bars=5, right_bars=5):
    """
    找出局部高点和低点
    一个点是Pivot High: 如果它比左边N根和右边N根K线的高点都高
    一个点是Pivot Low: 如果它比左边N根和右边N根K线的低点都低
    """
    pivots = {"highs": [], "lows": []}
    
    for i in range(left_bars, len(klines) - right_bars):
        current = klines[i]
        
        # 检查是否是Pivot High
        is_pivot_high = True
        for j in range(i - left_bars, i + right_bars + 1):
            if j != i and klines[j]['high'] >= current['high']:
                is_pivot_high = False
                break
        
        if is_pivot_high:
            pivots["highs"].append({
                "price": current['high'],
                "time": current['time'],
                "strength": calculate_pivot_strength(klines, i, "high")
            })
        
        # 检查是否是Pivot Low
        is_pivot_low = True
        for j in range(i - left_bars, i + right_bars + 1):
            if j != i and klines[j]['low'] <= current['low']:
                is_pivot_low = False
                break
        
        if is_pivot_low:
            pivots["lows"].append({
                "price": current['low'],
                "time": current['time'],
                "strength": calculate_pivot_strength(klines, i, "low")
            })
    
    return pivots

def calculate_pivot_strength(klines, index, pivot_type):
    """
    计算Pivot点的强度
    基于: 反转幅度、成交量、触及次数
    """
    current = klines[index]
    
    # 反转幅度 (之后价格走了多远)
    if pivot_type == "high":
        max_move = max(current['high'] - k['low'] for k in klines[index:index+10])
    else:
        max_move = max(k['high'] - current['low'] for k in klines[index:index+10])
    
    move_percent = max_move / current['close'] * 100
    
    # 成交量 (该K线成交量相对于均值)
    avg_volume = sum(k['volume'] for k in klines[index-20:index]) / 20
    volume_ratio = current['volume'] / avg_volume
    
    # 综合强度评分 (0-100)
    strength = min(100, move_percent * 10 + volume_ratio * 20)
    
    return strength
```

### 2.3 方法2: Volume Profile 实现

```python
def find_volume_nodes(klines, num_bins=100, min_volume_ratio=1.5):
    """
    找出成交量密集区作为支撑阻力
    """
    # 计算价格范围
    all_highs = [k['high'] for k in klines]
    all_lows = [k['low'] for k in klines]
    price_min, price_max = min(all_lows), max(all_highs)
    bin_size = (price_max - price_min) / num_bins
    
    # 初始化成交量分布
    volume_bins = [0] * num_bins
    
    # 分配成交量到价格区间
    for k in klines:
        # 假设成交量均匀分布在K线的高低点之间
        low_bin = int((k['low'] - price_min) / bin_size)
        high_bin = int((k['high'] - price_min) / bin_size)
        
        bins_covered = max(1, high_bin - low_bin + 1)
        volume_per_bin = k['volume'] / bins_covered
        
        for b in range(low_bin, min(high_bin + 1, num_bins)):
            volume_bins[b] += volume_per_bin
    
    # 计算平均成交量
    avg_volume = sum(volume_bins) / num_bins
    
    # 找出高成交量节点
    high_volume_nodes = []
    for i, vol in enumerate(volume_bins):
        if vol > avg_volume * min_volume_ratio:
            price = price_min + (i + 0.5) * bin_size
            high_volume_nodes.append({
                "price": price,
                "volume": vol,
                "volume_ratio": vol / avg_volume,
                "type": "VOLUME_NODE"
            })
    
    # 合并相邻节点
    merged_nodes = merge_nearby_levels(high_volume_nodes, threshold_percent=0.3)
    
    return merged_nodes
```

### 2.4 方法3-5: 其他方法实现

```python
def find_psychological_levels(current_price, range_percent=10):
    """
    找出整数关口
    """
    levels = []
    
    # 确定搜索范围
    price_low = current_price * (1 - range_percent / 100)
    price_high = current_price * (1 + range_percent / 100)
    
    # 1000的整数倍 (主要关口)
    for price in range(int(price_low / 1000) * 1000, int(price_high / 1000 + 1) * 1000, 1000):
        if price_low <= price <= price_high:
            levels.append({
                "price": price,
                "type": "PSYCHOLOGICAL",
                "strength": 80 if price % 5000 == 0 else 60 if price % 1000 == 0 else 40
            })
    
    return levels

def find_ma_levels(klines, current_price):
    """
    找出均线作为动态支撑阻力
    """
    levels = []
    
    # 计算各均线值
    closes = [k['close'] for k in klines]
    
    ma_configs = [
        ("EMA99", calculate_ema(closes, 99)),
        ("SMA200", calculate_sma(closes, 200)),
        ("EMA25", calculate_ema(closes, 25)),
    ]
    
    for name, ma_value in ma_configs:
        if ma_value:
            distance_percent = abs(current_price - ma_value) / current_price * 100
            if distance_percent < 5:  # 只关注距离5%以内的均线
                levels.append({
                    "price": ma_value,
                    "type": "MOVING_AVERAGE",
                    "name": name,
                    "strength": 70 if "200" in name else 50
                })
    
    return levels

def find_swing_levels(klines_8h, klines_1w):
    """
    找出近期的摆动高低点
    """
    levels = []
    
    # 8小时级别的近期高低点
    recent_8h = klines_8h[-30:]  # 最近30根8小时K线 (10天)
    high_8h = max(k['high'] for k in recent_8h)
    low_8h = min(k['low'] for k in recent_8h)
    
    levels.append({"price": high_8h, "type": "SWING_HIGH", "timeframe": "8h", "strength": 65})
    levels.append({"price": low_8h, "type": "SWING_LOW", "timeframe": "8h", "strength": 65})
    
    # 周线级别的近期高低点
    recent_1w = klines_1w[-8:]  # 最近8周
    high_1w = max(k['high'] for k in recent_1w)
    low_1w = min(k['low'] for k in recent_1w)
    
    levels.append({"price": high_1w, "type": "SWING_HIGH", "timeframe": "1w", "strength": 85})
    levels.append({"price": low_1w, "type": "SWING_LOW", "timeframe": "1w", "strength": 85})
    
    return levels
```

### 2.5 综合识别函数

```python
def identify_support_resistance(klines_1m, klines_15m, klines_8h, klines_1w, current_price):
    """
    综合所有方法识别支撑阻力位
    """
    all_levels = []
    
    # 方法1: Pivot Points (使用15m和8h数据)
    pivots_15m = find_pivot_points(klines_15m, left_bars=5, right_bars=5)
    pivots_8h = find_pivot_points(klines_8h, left_bars=3, right_bars=3)
    
    for p in pivots_15m["highs"]:
        all_levels.append({**p, "type": "RESISTANCE", "source": "PIVOT", "weight": 0.3})
    for p in pivots_15m["lows"]:
        all_levels.append({**p, "type": "SUPPORT", "source": "PIVOT", "weight": 0.3})
    for p in pivots_8h["highs"]:
        all_levels.append({**p, "type": "RESISTANCE", "source": "PIVOT", "weight": 0.3})
    for p in pivots_8h["lows"]:
        all_levels.append({**p, "type": "SUPPORT", "source": "PIVOT", "weight": 0.3})
    
    # 方法2: Volume Profile (使用8h数据)
    volume_nodes = find_volume_nodes(klines_8h)
    for node in volume_nodes:
        level_type = "SUPPORT" if node["price"] < current_price else "RESISTANCE"
        all_levels.append({**node, "type": level_type, "source": "VOLUME", "weight": 0.25})
    
    # 方法3: 整数关口
    psych_levels = find_psychological_levels(current_price)
    for level in psych_levels:
        level_type = "SUPPORT" if level["price"] < current_price else "RESISTANCE"
        all_levels.append({**level, "type": level_type, "source": "PSYCHOLOGICAL", "weight": 0.15})
    
    # 方法4: 均线
    ma_levels = find_ma_levels(klines_8h, current_price)
    for level in ma_levels:
        level_type = "SUPPORT" if level["price"] < current_price else "RESISTANCE"
        all_levels.append({**level, "type": level_type, "source": "MA", "weight": 0.15})
    
    # 方法5: 摆动高低点
    swing_levels = find_swing_levels(klines_8h, klines_1w)
    for level in swing_levels:
        level_type = "SUPPORT" if "LOW" in level["type"] else "RESISTANCE"
        all_levels.append({**level, "type": level_type, "source": "SWING", "weight": 0.15})
    
    # 合并相近的价位
    merged_levels = merge_and_score_levels(all_levels, threshold_percent=0.5)
    
    # 按强度排序
    merged_levels.sort(key=lambda x: x["final_score"], reverse=True)
    
    return merged_levels

def merge_and_score_levels(levels, threshold_percent=0.5):
    """
    合并相近价位，计算综合得分
    """
    if not levels:
        return []
    
    # 按价格排序
    levels.sort(key=lambda x: x["price"])
    
    merged = []
    current_group = [levels[0]]
    
    for level in levels[1:]:
        # 检查是否与当前组相近
        group_avg_price = sum(l["price"] for l in current_group) / len(current_group)
        distance_percent = abs(level["price"] - group_avg_price) / group_avg_price * 100
        
        if distance_percent < threshold_percent:
            current_group.append(level)
        else:
            # 合并当前组
            merged.append(merge_group(current_group))
            current_group = [level]
    
    # 处理最后一组
    merged.append(merge_group(current_group))
    
    return merged

def merge_group(group):
    """
    合并一组相近的价位
    """
    # 加权平均价格
    total_weight = sum(l.get("weight", 1) * l.get("strength", 50) for l in group)
    weighted_price = sum(l["price"] * l.get("weight", 1) * l.get("strength", 50) for l in group) / total_weight
    
    # 综合得分 (多个来源确认的价位得分更高)
    sources = set(l.get("source", "UNKNOWN") for l in group)
    source_bonus = len(sources) * 10  # 每多一个来源+10分
    
    avg_strength = sum(l.get("strength", 50) for l in group) / len(group)
    final_score = avg_strength + source_bonus
    
    return {
        "price": round(weighted_price, 2),
        "type": group[0]["type"],
        "sources": list(sources),
        "touch_count": len(group),
        "avg_strength": avg_strength,
        "final_score": min(100, final_score),
        "confirmed_by": len(sources),
    }
```

---

## 三、状态向量完整定义

```python
def build_state_vector(market_data, position_info, knowledge_base):
    """
    构建完整的状态向量，用于强化学习输入
    """
    state = {}
    
    # ===== 价格特征 =====
    current_price = market_data["current_price"]
    state["price_normalized"] = normalize_price(current_price)
    
    # ===== 趋势特征 =====
    state["trend_1m"] = encode_trend(market_data["trend_1m"])      # [-1, 1]
    state["trend_15m"] = encode_trend(market_data["trend_15m"])
    state["trend_8h"] = encode_trend(market_data["trend_8h"])
    state["trend_1w"] = encode_trend(market_data["trend_1w"])
    state["adx_15m"] = market_data["adx_15m"] / 100               # [0, 1]
    
    # ===== 动量特征 =====
    state["rsi_1m"] = market_data["rsi_1m"] / 100                 # [0, 1]
    state["rsi_15m"] = market_data["rsi_15m"] / 100
    state["macd_histogram"] = normalize(market_data["macd_hist"]) # [-1, 1]
    state["stoch_rsi"] = market_data["stoch_rsi"] / 100           # [0, 1]
    
    # ===== 波动率特征 =====
    state["atr_percent"] = market_data["atr"] / current_price     # 相对ATR
    state["bb_position"] = market_data["bb_position"]             # [-1, 1] 在布林带中的位置
    state["volatility_rank"] = market_data["volatility_rank"]     # [0, 1] 波动率百分位
    
    # ===== 成交量特征 ⭐ =====
    state["volume_ratio"] = min(3, market_data["volume_ratio"]) / 3  # [0, 1]
    state["obv_trend"] = encode_trend(market_data["obv_trend"])      # [-1, 1]
    state["cvd_trend"] = encode_trend(market_data["cvd_trend"])      # [-1, 1] 买卖压力
    state["volume_ma_cross"] = market_data["volume_above_ma"]        # 0 or 1
    
    # ===== 支撑阻力特征 ⭐ =====
    nearest_support = find_nearest_level(current_price, "SUPPORT", knowledge_base)
    nearest_resistance = find_nearest_level(current_price, "RESISTANCE", knowledge_base)
    
    state["distance_to_support"] = (current_price - nearest_support["price"]) / current_price
    state["distance_to_resistance"] = (nearest_resistance["price"] - current_price) / current_price
    state["support_strength"] = nearest_support["final_score"] / 100
    state["resistance_strength"] = nearest_resistance["final_score"] / 100
    state["in_value_area"] = 1 if market_data["in_volume_value_area"] else 0
    
    # ===== 持仓特征 =====
    state["position_side"] = encode_position(position_info["side"])  # -1/0/1
    state["position_size"] = position_info["size_percent"]           # [0, 1]
    state["unrealized_pnl"] = normalize(position_info["pnl_percent"])# [-1, 1]
    state["hold_duration"] = min(1, position_info["hold_bars"] / 100)# [0, 1]
    
    # ===== 账户特征 =====
    state["available_margin"] = position_info["available_margin_percent"]
    
    return state
```

---

## 四、实现优先级

```
Phase 1 (本周): 基础指标计算
├── 实现所有技术指标计算函数
├── 实现支撑阻力初始识别
├── 测试数据获取和指标计算
└── 输出: indicators.py

Phase 2 (下周): 知识库和日志
├── 实现交易日志数据库
├── 实现知识库存储
├── 实现支撑阻力动态更新
└── 输出: knowledge.py, logger.py

Phase 3: 强化学习环境
├── 封装为Gym环境
├── 实现状态向量构建
├── 实现奖励函数
└── 输出: trading_env.py
```

准备好开始实现Phase 1了吗？
