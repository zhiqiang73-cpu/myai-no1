"""
文件重组脚本
自动将rl/文件移动到新的文件夹结构
"""
import os
import shutil
from pathlib import Path

# 文件移动映射
MOVE_MAP = {
    # 核心模块
    "rl/agent.py": "rl/core/agent.py",
    "rl/knowledge.py": "rl/core/knowledge.py",
    
    # 市场分析
    "rl/indicators.py": "rl/market_analysis/indicators.py",
    "rl/level_finder.py": "rl/market_analysis/level_finder.py",
    "rl/levels.py": "rl/market_analysis/levels.py",
    
    # 执行模块
    "rl/sl_tp.py": "rl/execution/sl_tp.py",
    "rl/exit_manager.py": "rl/execution/exit_manager.py",
    
    # 学习模块
    "rl/unified_learning_system.py": "rl/learning/unified_learning_system.py",
    
    # 风险控制
    "rl/risk_controller.py": "rl/risk/risk_controller.py",
    
    # 配置
    "rl/config_v4.py": "rl/config/config_v4.py",
    "rl/time_manager.py": "rl/config/time_manager.py",
    
    # 保留在根目录的文件
    # rl/__init__.py - 需要更新但不移动
    # rl/leverage_optimizer.py - 保留作为参考
}

def move_files():
    """移动文件"""
    print("="*60)
    print("开始文件重组")
    print("="*60)
    
    base_dir = Path(__file__).parent
    moved_count = 0
    failed_count = 0
    
    for source, target in MOVE_MAP.items():
        source_path = base_dir / source
        target_path = base_dir / target
        
        if not source_path.exists():
            print(f"⚠️ 源文件不存在: {source}")
            failed_count += 1
            continue
        
        # 创建目标目录
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # 移动文件
            shutil.move(str(source_path), str(target_path))
            print(f"✅ {source} → {target}")
            moved_count += 1
        except Exception as e:
            print(f"❌ 移动失败: {source}")
            print(f"   错误: {e}")
            failed_count += 1
    
    print("="*60)
    print(f"移动完成: {moved_count}个成功, {failed_count}个失败")
    print("="*60)

def backup_original():
    """备份原始文件"""
    print("\n备份原始文件...")
    base_dir = Path(__file__).parent
    backup_dir = base_dir / "rl_backup_before_reorganize"
    
    if backup_dir.exists():
        print(f"⚠️ 备份目录已存在: {backup_dir}")
        response = input("是否覆盖？(y/n): ")
        if response.lower() != 'y':
            print("取消备份")
            return False
        shutil.rmtree(backup_dir)
    
    try:
        shutil.copytree(base_dir / "rl", backup_dir, 
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        print(f"✅ 备份完成: {backup_dir}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def update_init_py():
    """更新rl/__init__.py"""
    print("\n更新rl/__init__.py...")
    
    init_content = '''"""
强化学习交易系统 v4.0
整合的自适应交易系统
"""

# 配置
from .config import (
    TIMEFRAME_WEIGHTS,
    FEATURE_LEARNING,
    DYNAMIC_THRESHOLD,
    POSITION_MANAGEMENT,
    RISK_CONTROL,
    TIME_CONFIG,
    time_manager,
    now,
    timestamp,
    format_time,
)

# 核心
from .core import TradingAgent, TradeLogger, KnowledgeBase

# 市场分析
from .market_analysis import (
    TechnicalAnalyzer,
    BestLevelFinder,
    LevelDiscovery,
    LevelScoring,
)

# 执行
from .execution import (
    StopLossTakeProfit,
    PositionSizer,
    ExitManager,
    PositionState,
    ExitDecision,
)

# 学习
from .learning import FeatureLearningSystem

# 风险控制
from .risk import RiskController

__version__ = "4.0"
__all__ = [
    # 配置
    'TIMEFRAME_WEIGHTS',
    'FEATURE_LEARNING',
    'DYNAMIC_THRESHOLD',
    'POSITION_MANAGEMENT',
    'RISK_CONTROL',
    'TIME_CONFIG',
    'time_manager',
    'now',
    'timestamp',
    'format_time',
    # 核心
    'TradingAgent',
    'TradeLogger',
    'KnowledgeBase',
    # 市场分析
    'TechnicalAnalyzer',
    'BestLevelFinder',
    'LevelDiscovery',
    'LevelScoring',
    # 执行
    'StopLossTakeProfit',
    'PositionSizer',
    'ExitManager',
    'PositionState',
    'ExitDecision',
    # 学习
    'FeatureLearningSystem',
    # 风险控制
    'RiskController',
]
'''
    
    base_dir = Path(__file__).parent
    init_file = base_dir / "rl" / "__init__.py"
    
    try:
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(init_content)
        print(f"✅ 更新完成: {init_file}")
        return True
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║        文件重组脚本 - 按功能模块整理文件夹               ║
╚═══════════════════════════════════════════════════════════╝

将执行以下操作:
1. 备份原始rl/文件夹到rl_backup_before_reorganize/
2. 将文件移动到新的文件夹结构
3. 更新rl/__init__.py

新的结构:
rl/
├── core/              # 核心模块
├── market_analysis/   # 市场分析
├── execution/         # 执行模块
├── learning/          # 学习模块
├── risk/              # 风险控制
└── config/            # 配置
""")
    
    response = input("\n是否继续？(y/n): ")
    if response.lower() != 'y':
        print("取消操作")
        exit(0)
    
    # 1. 备份
    if not backup_original():
        print("\n❌ 备份失败，终止操作")
        exit(1)
    
    # 2. 移动文件
    print()
    move_files()
    
    # 3. 更新__init__.py
    print()
    update_init_py()
    
    print("""
\n✅ 文件重组完成！

下一步:
1. 检查新的文件结构
2. 测试系统是否正常运行
3. 如有问题，从rl_backup_before_reorganize/恢复

如果一切正常，可以删除备份文件夹。
""")

