# 1分钟图表Y轴自动调整测试说明

## 功能说明

当1分钟K线图的支撑/阻力位不在当前K线价格范围内时，系统会自动调整Y轴范围，通过压缩K线显示大小来确保支撑和阻力线始终可见。

## 测试步骤

1. **启动Web界面**
   ```bash
   cd binance-futures-trading/web
   python app.py
   ```

2. **打开浏览器**
   - 访问 `http://localhost:5000`
   - 按 F12 打开开发者工具，切换到 Console 标签

3. **观察日志输出**
   
   当支撑/阻力位更新时，控制台会输出以下日志：
   
   ```
   📊 开始调整1分钟图表Y轴: 支撑=89332, 阻力=91692, K线数量=100
   📊 K线价格范围: [91000.00, 91200.00], 范围=200.00
   📊 支撑位 89332.00 在K线下方，需要扩展下界
   📊 阻力位 91692.00 在K线上方，需要扩展上界
   📊 1分钟图表Y轴已调整: 目标范围 [89332.00, 91692.00], 边距 top=8.5%, bottom=15.2%
   ```

4. **验证效果**
   - 查看1分钟图表，应该能看到：
     - 绿色虚线（支撑位）显示在K线下方
     - 红色虚线（阻力位）显示在K线上方
     - K线被压缩显示，但支撑阻力线完全可见

## 实现原理

### 关键函数

1. **`adjust1mChartRangeWithData(klines, supportPrice, resistancePrice)`**
   - 接收K线数据和支撑阻力价格
   - 计算K线的价格范围
   - 判断支撑阻力位是否超出范围
   - 动态计算 `scaleMargins` 来扩展Y轴

2. **调用时机**
   - 当K线数据更新时（`loadKlines` 函数）
   - 当支撑阻力位更新时（`updateSRLines` 函数）

### 边距计算公式

```javascript
// 计算需要的额外空间
topSpace = resistancePrice - maxKlinePrice
bottomSpace = minKlinePrice - supportPrice

// 添加5%的额外边距
extraMargin = targetRange * 0.05
totalRange = targetRange + extraMargin * 2

// 计算边距比例（限制在5%-40%之间）
topMargin = (topSpace + extraMargin) / totalRange
bottomMargin = (bottomSpace + extraMargin) / totalRange
```

## 故障排查

### 如果支撑阻力线仍然不可见

1. **检查控制台日志**
   - 是否有 "📊 开始调整1分钟图表Y轴" 的日志？
   - 如果没有，说明函数没有被调用

2. **检查支撑阻力位数据**
   - 在控制台输入：`console.log(currentSupport, currentResistance)`
   - 确认数据是否有效

3. **手动触发调整**
   - 在控制台输入：
   ```javascript
   adjust1mChartRange(89332, 91692)
   ```

4. **检查图表状态**
   - 在控制台输入：
   ```javascript
   console.log(charts['1m'])
   console.log(candleSeries['1m'].data())
   ```

### 常见问题

1. **Q: 刷新后仍然看不到支撑阻力线**
   - A: 确保 Agent 正在运行，支撑阻力位数据需要从后端获取

2. **Q: 控制台没有任何日志**
   - A: 检查是否有 JavaScript 错误，可能是代码执行被中断

3. **Q: Y轴调整后又恢复了**
   - A: 可能是 `fitContent()` 或其他操作重置了Y轴，已添加 `setTimeout` 延迟执行

## 代码位置

- **HTML文件**: `binance-futures-trading/web/templates/index.html`
- **关键函数**: 
  - 第 1414 行: `adjust1mChartRangeWithData`
  - 第 1507 行: `adjust1mChartRange`
  - 第 753 行: K线更新时调用
  - 第 1404 行: 支撑阻力更新时调用

































