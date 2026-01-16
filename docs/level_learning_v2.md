# 支撑阻力位特征学习系统 v2

## 核心思想

**不学习具体价位，而是学习"什么特征的价位更有效"**

价格是不断变化的，记忆具体价位没有意义。系统应该学习的是：
- 什么样的特征组合，能让一个价位成为有效的支撑/阻力
- 通过交易结果反馈，调整各特征的权重

## 有效特征（6个）

| 特征 | 数学定义 | 为什么有效 |
|------|----------|------------|
| **volume_density** | 该价位±0.5%区间的成交量 / 总成交量 | 真金白银=真实信念，成交量密集说明多空在此博弈 |
| **touch_bounce_count** | 价格触及后反弹的次数 / 10 | 统计验证，多次反弹说明价位有效 |
| **bounce_magnitude** | 触及后平均反弹% / 3% | 反弹越强=支撑/阻力越强 |
| **failed_breakout_count** | 假突破次数 / 5 | 假突破=强支撑阻力，突破后又回来说明价位有效 |
| **duration_days** | 有效持续天数 / 30 | 越久=市场记忆越深 |
| **multi_tf_confirm** | 确认的周期数 / 4 | 多周期共振更可靠 |

## 移除的特征（非数学/非逻辑）

| 特征 | 移除原因 |
|------|----------|
| is_round_number | 心理因素，非数学逻辑 |
| distance_ratio | 筛选指标，不是有效性指标 |
| price_velocity | 与价位有效性无关 |

## 学习机制

### 初始权重
```python
{
    "volume_density": 0.20,        # 成交量密集度
    "touch_bounce_count": 0.20,    # 触及反弹次数
    "bounce_magnitude": 0.15,      # 反弹幅度
    "failed_breakout_count": 0.20, # 假突破次数
    "duration_days": 0.10,         # 持续天数
    "multi_tf_confirm": 0.15,      # 多周期确认
}
```

### 奖励信号
- 价位有效且盈利 → reward = 1.0 + pnl/5
- 价位有效但亏损 → reward = 0.3（方向错了，但价位判断对了）
- 价位无效（被突破）→ reward = -1.0 - |pnl|/5

### 权重更新
```
gradient = feature_value × reward × learning_rate
weight[feature] += gradient
```

然后归一化，保持权重总和为1。

## 使用流程

1. **发现价位**：使用原有的 `LevelDiscovery` 发现支撑阻力位
2. **提取特征**：对每个价位提取6个特征
3. **计算评分**：`score = Σ(feature_value × weight) × 100`
4. **入场决策**：只使用评分>=40的价位
5. **交易结束**：根据结果更新权重

## 文件结构

```
binance-futures-trading/rl/
├── level_learning.py    # 特征学习模块
│   ├── LevelFeatureExtractor   # 特征提取器
│   ├── LevelEffectivenessLearner  # 权重学习器
│   └── SmartLevelDiscovery     # 智能价位发现
├── agent.py             # 集成学习系统
└── levels.py            # 原有价位发现（保留）
```

## 数据存储

权重保存在 `rl_data/level_weights_v2.json`:
```json
{
    "weights": {...},
    "updated_at": "2026-01-07T...",
    "training_count": 50,
    "version": "2.0"
}
```
