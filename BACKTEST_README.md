# 回测训练系统使用说明

## 问题诊断

你的系统交易次数太少的原因：
1. **入场条件太严格** - 需要多重确认（趋势+RSI+MACD+布林带+支撑阻力位）
2. **评分门槛太高** - 探索期30分，学习期40分，稳定期50分
3. **距离阈值太紧** - 价格必须非常接近支撑阻力位
4. **单边行情保护** - 会禁止很多入场机会

## 解决方案

我已经创建了两个回测训练系统：

### 1. 完整版回测训练器 (`backtest_trainer.py`)
- 极度放宽入场条件
- 只看支撑阻力位，不需要其他确认
- 目标：产生大量交易来学习

**特点：**
- 距离阈值：1.5%（vs 实盘的2-5%）
- 最低评分：10分（vs 实盘的30-50分）
- 5%概率随机入场（增加样本多样性）
- 固定止损0.5%，止盈1.0%

### 2. 简化版回测 (`simple_backtest.py`)
- 更简单，避免编码问题
- 直接写日志文件
- 适合快速测试

## 如何使用

### 方法1：直接运行（推荐）

由于Windows编码问题，建议使用以下方式：

```cmd
# 1. 打开命令提示符（CMD，不是PowerShell）
# 2. 切换到项目目录
cd "D:\MyAI\My work team\强化2号\binance-futures-trading"

# 3. 运行简化版回测
python simple_backtest.py

# 4. 查看结果
type backtest_log.txt
```

### 方法2：通过Web界面

1. 启动Web服务器
2. 在浏览器中访问回测页面
3. 选择CSV文件和交易数量
4. 点击"开始训练"

## 预期结果

运行100笔交易的回测，你应该看到：

```
Loading data...
Loaded 432000 candles
Starting backtest...
============================================================
[1] LONG @ 67850 | Support: 67800 (score: 25.3)
[1] LONG TP @ 68535 | PnL: +1.01% | Balance: 10050
[2] SHORT @ 68200 | Resistance: 68250 (score: 18.7)
[2] SHORT SL @ 68541 | PnL: -0.50% | Balance: 10025
...
============================================================
Backtest Results
============================================================
Total Trades: 100
Wins: 55 | Losses: 45
Win Rate: 55.0%
Total PnL: +12.50%
Final Balance: 10625.00 USDT
============================================================
```

## 学习数据保存位置

回测完成后，学习数据会保存在：
- `rl_data/backtest_level_stats.json` - 支撑阻力位统计
- `rl_data/backtest_trades.json` - 交易记录
- `backtest_log.txt` - 运行日志

## 下一步

回测产生足够交易后：

1. **查看学习进度**
   ```python
   from rl.level_finder import BestLevelFinder
   finder = BestLevelFinder(stats_path="rl_data/backtest_level_stats.json")
   stats = finder.get_learning_progress()
   print(f"已完成 {stats['total_trades']} 笔交易")
   ```

2. **分析哪些支撑阻力位有效**
   - 查看 `backtest_trades.json`
   - 按评分分组分析胜率

3. **调整实盘参数**
   - 如果回测中评分20-40的支撑位胜率高，可以降低实盘的最低评分要求
   - 如果距离1.5%内的交易效果好，可以放宽实盘的距离阈值

## 常见问题

### Q: 为什么回测也没有交易？
A: 可能是：
1. CSV数据格式问题 - 检查 `btcusdt_1m_300days.csv` 是否存在
2. 支撑阻力位发现失败 - 检查日志中是否有错误
3. 评分都太低 - 尝试降低 `min_level_score` 到 5

### Q: 回测结果能直接用于实盘吗？
A: 不能直接用，但可以：
1. 了解哪些特征（成交量、触及次数等）更重要
2. 找到合适的评分阈值
3. 验证支撑阻力位的有效性

### Q: 如何让实盘也产生更多交易？
A: 修改 `rl/agent.py` 中的参数：
```python
# 第1步：降低评分门槛
if trade_count < 30:
    min_score = 15  # 从30降到15
elif trade_count < 100:
    min_score = 25  # 从40降到25
else:
    min_score = 35  # 从50降到35

# 第2步：放宽距离阈值
distance_threshold = 3.0  # 从2-5%改为固定3%

# 第3步：减少确认要求
# 注释掉一些不必要的确认条件
```

## 技术支持

如果遇到问题：
1. 查看 `backtest_log.txt` 日志
2. 检查 `rl_data/` 目录是否有写入权限
3. 确认Python版本 >= 3.8
