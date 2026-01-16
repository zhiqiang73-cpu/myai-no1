# 支撑阻力位权重强化学习系统

## 概述

系统现在使用**强化学习 + 反向传播**自动优化支撑阻力位的特征权重，让AI通过实战经验不断改进预测准确性。

## 系统架构

### 双层优化系统

```
┌─────────────────────────────────────────────┐
│  Level 1: 主特征权重优化 (6个特征)          │
│  - volume_density (成交量密集度)            │
│  - touch_bounce_count (触及反弹次数)        │
│  - bounce_magnitude (反弹幅度)              │
│  - failed_breakout_count (假突破次数)       │
│  - duration_days (持续天数)                 │
│  - multi_tf_confirm (多周期确认)            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Level 2: 多周期权重优化 (4个周期)         │
│  - 1分钟权重 (初始50%)                     │
│  - 15分钟权重 (初始30%)                    │
│  - 8小时权重 (初始15%)                     │
│  - 周线权重 (初始5%)                       │
└─────────────────────────────────────────────┘
```

## 学习算法

### 1. 策略梯度（REINFORCE）

使用策略梯度方法优化权重分配：

```
∇J(θ) = E[∑ ∇log π(a|s) * G_t]
```

- **策略 π(a|s)**：Softmax归一化的权重分布
- **回报 G_t**：累积折扣奖励
- **梯度更新**：θ ← θ + α * ∇J(θ)

### 2. 奖励函数设计

```python
reward = pnl_percent * 10  # 基础奖励

# 额外奖励/惩罚
if level_effective:    # 价位确实有效（支撑住/阻挡住）
    reward += 5
else:                  # 价位被突破
    reward -= 5

# 出场原因调整
if exit_reason == "TAKE_PROFIT":
    reward += 3        # 成功止盈
elif exit_reason == "STOP_LOSS":
    reward -= 3        # 触发止损

# 最终范围：[-100, +100]
```

### 3. 经验回放与批量更新

- 积累至少10笔交易经验
- 计算累积折扣奖励（γ=0.99）
- 标准化奖励（提高稳定性）
- 批量梯度更新

## 使用方式

### 自动启用（推荐）

系统默认启用强化学习优化，无需额外配置：

```python
# agent.py 中已自动启用
self.level_finder = BestLevelFinder(
    stats_path=f"{data_dir}/level_stats.json",
    db_path=f"{data_dir}/trades.db",
    use_rl_optimizer=True  # 默认开启
)
```

### 手动控制

如果需要禁用强化学习，回退到简单统计学习：

```python
self.level_finder = BestLevelFinder(
    stats_path=f"{data_dir}/level_stats.json",
    db_path=f"{data_dir}/trades.db",
    use_rl_optimizer=False  # 关闭强化学习
)
```

## 学习过程

### 阶段1：冷启动（0-30笔交易）

- 使用默认权重
- 仅收集经验数据
- 不进行权重调整

### 阶段2：探索期（30-100笔交易）

- 简单统计学习开始工作
- 强化学习每10笔交易更新一次
- 权重开始小幅调整

### 阶段3：优化期（100-500笔交易）

- 两种学习机制协同工作
- 权重逐渐收敛到最优值
- 支撑阻力位准确性提升

### 阶段4：稳定期（500笔以上）

- 权重变化趋于稳定
- 偶尔微调以适应市场变化
- 保持高准确性

## 关键参数

### 主特征优化器

```python
learning_rate = 0.01    # 学习率（较小保证稳定）
gamma = 0.99           # 折扣因子（重视长期回报）
min_episodes = 10      # 最小更新间隔
```

### 多周期优化器

```python
learning_rate = 0.02    # 略高的学习率（周期权重相对简单）
min_episodes = 5       # 更频繁的更新
```

## 监控与调试

### 查看学习进度

系统会在运行日志中输出：

```
[OK] 加载强化学习模型: rl_data/level_stats_rl.json
[RL] 权重更新: 平均奖励=15.23
```

### 查看当前权重

```python
# 获取当前特征权重
current_weights = level_finder.weights
print(current_weights)

# 获取强化学习统计
if level_finder.rl_optimizer:
    stats = level_finder.rl_optimizer.get_training_stats()
    print(f"总更新次数: {stats['total_updates']}")
    print(f"近期平均奖励: {stats['recent_avg_reward']:.2f}")
    print(f"奖励趋势: {stats['reward_trend']}")
```

### 查看多周期权重

```python
if level_finder.tf_optimizer:
    tf_weights = level_finder.tf_optimizer.get_weights()
    print(f"1分钟: {tf_weights['1m']*100:.1f}%")
    print(f"15分钟: {tf_weights['15m']*100:.1f}%")
    print(f"8小时: {tf_weights['8h']*100:.1f}%")
    print(f"周线: {tf_weights['1w']*100:.1f}%")
```

## 数据文件

系统会创建以下文件：

```
rl_data/
├── level_stats.json        # 统计数据（简单学习）
├── level_stats_rl.json     # 强化学习模型（主特征）
└── level_stats_tf.json     # 强化学习模型（多周期）
```

## 预期效果

### 1分钟权重提升

经过学习后，1分钟K线的权重预计会从初始的7.5%提升到：

- **短线交易模式**：15-25%
- **中线交易模式**：10-15%
- **长线交易模式**：5-10%

### 特征权重优化

根据实战数据，系统会自动发现：

- 哪些特征对盈利交易最重要
- 哪些特征是噪音（降低权重）
- 不同市场环境下的最优权重

### 准确性提升

预期支撑阻力位的有效率从初始的60-70%提升到：

- **30笔交易后**：65-75%
- **100笔交易后**：70-80%
- **500笔交易后**：75-85%

## 优势对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| **固定权重** | 简单稳定 | 无法适应市场变化 |
| **简单统计** | 易理解 | 只看平均值，忽略动态 |
| **强化学习** | 自适应、考虑长期回报 | 需要训练时间 |

## 注意事项

1. **训练时间**：需要至少30笔交易才开始优化
2. **过拟合风险**：系统使用小学习率和平滑更新避免过拟合
3. **市场适应**：权重会持续微调以适应市场变化
4. **数据质量**：确保交易记录准确（盈亏、止损原因等）

## 高级功能（未来）

- [ ] 多策略学习（不同市场环境不同权重）
- [ ] PPO算法替代REINFORCE（更稳定）
- [ ] Actor-Critic架构（更快收敛）
- [ ] Meta-Learning（快速适应新市场）

