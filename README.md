# 🚀 币安期货强化学习交易系统

> 基于强化学习的自动化交易系统，支持神经网络优化的止损止盈策略

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ 核心特性

- 🧠 **三层学习系统**
  - 第1层：支撑阻力位6特征权重学习
  - 第2层：规则式入场决策系统
  - 第3层：神经网络止损止盈学习（V2）

- 🎯 **训练/部署模式分离**
  - 训练模式：模拟盘充分训练，验证集监控
  - 部署模式：使用最佳模型，稳定可靠

- 📊 **智能决策**
  - 多周期分析（1m/15m/8h/1w）
  - 渐进式入场门槛（探索期→学习期→稳定期）
  - 智能平仓管理（分批止盈/移动止损）

- 🔍 **探索-利用平衡**
  - ε-贪婪策略
  - 好奇心奖励机制
  - 早停机制防止过拟合

## 📋 系统要求

- Python 3.8+
- 币安期货测试网账户（用于模拟交易）
- 币安主网API访问（用于实时K线数据）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/binance-futures-trading.git
cd binance-futures-trading
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

> ⚠️ **注意**：请使用币安期货测试网的API密钥，不要使用实盘密钥！

### 4. 配置训练模式

编辑 `config.json`：

```json
{
  "sl_tp_learner": {
    "use_v2": true,
    "mode": "training"
  }
}
```

### 5. 启动系统

**Windows:**
```bash
启动程序.bat
```

**Linux/Mac:**
```bash
python -m web.app
```

### 6. 访问Web界面

打开浏览器访问：`http://localhost:5000`

## 📚 文档

- [快速开始指南](QUICKSTART_V2.md) - V2系统快速入门
- [第一步：基础交易系统](first%20step.md) - 基础功能说明
- [第二步：规则式强化学习](docs/second_step.md) - 支撑阻力位学习
- [第三步：神经网络强化学习](docs/third_step.md) - 神经网络学习系统
- [系统架构文档](docs/system_architecture_v3.md) - 完整架构说明

## 🏗️ 项目结构

```
binance-futures-trading/
├── rl/                      # 强化学习模块
│   ├── agent.py            # 核心交易Agent
│   ├── sl_tp_learner_v2.py # 神经网络学习器V2
│   ├── level_finder.py     # 支撑阻力位学习
│   ├── exit_manager.py    # 智能平仓管理
│   └── ...
├── web/                    # Web界面
│   ├── app.py             # Flask应用
│   └── templates/         # HTML模板
├── rl_data/               # 数据目录（训练数据、模型）
├── docs/                  # 文档目录
├── config.json           # 配置文件
├── requirements.txt      # Python依赖
└── README.md            # 本文档
```

## 🎓 训练流程

### 训练阶段（模拟盘）

1. 设置 `config.json` 为训练模式
2. 启动系统，自动积累交易数据
3. 每20笔交易自动训练一次
4. 监控验证loss，等待收敛（20轮不改善）

### 部署阶段（实盘）

1. 确认训练收敛（验证loss < 0.02）
2. 切换 `config.json` 为部署模式
3. 重启系统，自动加载最佳模型
4. 探索率降至5%，稳定运行

## 📊 系统架构

```
┌─────────────────────────────────────────┐
│         第1层：支撑阻力位学习              │
│     6特征权重优化 (统计分析)               │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         第2层：入场决策系统              │
│     规则式评分系统 (渐进式门槛)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│     第3层：止损止盈神经网络学习           │
│     8→64→64→32→2 (训练/部署分离)         │
└─────────────────────────────────────────┘
```

## 🔧 配置说明

### config.json

```json
{
  "sl_tp_learner": {
    "use_v2": true,        // 使用V2版本
    "mode": "training"     // "training" 或 "deployment"
  }
}
```

### 训练参数

- **训练频率**: 每20笔交易训练一次
- **最少数据**: 100笔交易
- **推荐数据**: 500+笔交易
- **早停耐心**: 20个epoch不改善

## ⚠️ 重要提示

1. **仅用于模拟盘训练**
   - 训练阶段探索率高，可能产生试错交易
   - 必须在模拟盘充分训练后再考虑实盘

2. **数据需求**
   - 最少100笔交易才能开始训练
   - 500+笔交易才能充分学习
   - 数据不足时效果有限

3. **定期重新训练**
   - 市场环境会变化
   - 建议每月重新训练一次
   - 保留旧模型作为备份

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📝 许可证

MIT License

## 🙏 致谢

- [python-binance](https://github.com/sammchardy/python-binance) - Binance API客户端
- [Flask](https://flask.palletsprojects.com/) - Web框架

## 📞 联系方式

如有问题，请提交Issue。

---

**⚠️ 风险提示**: 本系统仅供学习和研究使用。实盘交易存在风险，请谨慎使用！

































