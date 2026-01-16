"""
系统功能验证脚本
在开发Web界面之前，先验证所有后端功能是否正常工作

测试项目：
1. API连接测试
2. K线数据获取（4个周期）
3. 技术指标计算
4. 支撑阻力位识别
5. 多周期趋势分析
6. AI动态阈值计算
7. 入场信号生成
8. 交易记录读取
9. 学习系统状态
"""
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client import BinanceFuturesClient
from config import API_KEY, API_SECRET, TESTNET_BASE_URL


def print_section(title):
    """打印分隔线"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_api_connection():
    """测试1: API连接"""
    print_section("TEST 1: API Connection")
    
    try:
        client = BinanceFuturesClient()
        
        # 测试时间同步
        server_time_response = client.get_server_time()
        server_time = server_time_response['serverTime']
        print(f"Server Time: {datetime.fromtimestamp(server_time/1000)}")
        print(f"Time Offset: {client.time_offset}ms")
        
        # 测试账户信息
        account = client.get_account()
        balance = float(account['totalWalletBalance'])
        print(f"Account Balance: ${balance:.2f} USDT")
        
        # 测试价格获取
        ticker = client.get_ticker_price("BTCUSDT")
        price = float(ticker['price'])
        print(f"BTC Price: ${price:,.2f}")
        
        print("Result: PASS")
        return client
    except Exception as e:
        print(f"Result: FAIL - {e}")
        return None


def test_klines_fetch(client):
    """测试2: K线数据获取"""
    print_section("TEST 2: K-line Data Fetching (4 Timeframes)")
    
    if not client:
        print("Result: SKIP - No client")
        return None
    
    try:
        intervals = ["1m", "15m", "8h", "1w"]
        limits = {"1m": 200, "15m": 200, "8h": 150, "1w": 100}
        klines_data = {}
        
        for interval in intervals:
            klines = client.get_klines("BTCUSDT", interval, limit=limits[interval])
            klines_data[interval] = klines
            
            if klines:
                last = klines[-1]
                close_price = float(last[4])
                volume = float(last[5])
                print(f"  {interval:>3}: {len(klines)} candles, Latest Close: ${close_price:,.2f}, Vol: {volume:.2f}")
            else:
                print(f"  {interval:>3}: No data")
        
        print("Result: PASS")
        return klines_data
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_klines_format(klines_raw):
    """转换K线格式：从API格式到字典格式"""
    return [{
        "time": k[0],
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5])
    } for k in klines_raw]


def test_technical_indicators(klines_data):
    """测试3: 技术指标计算"""
    print_section("TEST 3: Technical Indicators Calculation")
    
    if not klines_data or "1m" not in klines_data:
        print("Result: SKIP - No klines data")
        return None
    
    try:
        # 直接导入，避免通过rl包
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rl', 'market_analysis'))
        from indicators import TechnicalAnalyzer
        sys.path.pop(0)
        
        analyzer = TechnicalAnalyzer()
        
        # 测试1m周期 - 转换格式
        klines_1m_raw = klines_data["1m"]
        klines_1m = convert_klines_format(klines_1m_raw)
        analysis = analyzer.analyze(klines_1m)
        
        if not analysis:
            print("Result: FAIL - Not enough data")
            return None
        
        current = analysis['current']
        
        print(f"  Close Price: ${current['close']:,.2f}")
        print(f"  EMA7: ${current['ema7']:,.2f}")
        print(f"  EMA25: ${current['ema25']:,.2f}")
        print(f"  EMA99: ${current['ema99']:,.2f}")
        print(f"  RSI: {current['rsi']:.2f}")
        print(f"  MACD: {current['macd']:.4f}")
        print(f"  MACD Signal: {current['macd_signal']:.4f}")
        print(f"  MACD Histogram: {current['macd_histogram']:.4f}")
        print(f"  ADX: {current['adx']:.2f} ({current.get('trend_strength', 'N/A')})")
        print(f"  Bollinger Position: {current['bb_position']:.2f}")
        print(f"  Volume Ratio: {current['volume_ratio']:.2f}")
        print(f"  Trend: {current['trend']}")
        
        print("Result: PASS")
        return analysis
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_support_resistance(klines_data):
    """测试4: 支撑阻力位识别"""
    print_section("TEST 4: Support/Resistance Level Detection")
    
    if not klines_data:
        print("Result: SKIP - No klines data")
        return None
    
    try:
        # 直接导入
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rl', 'market_analysis'))
        from levels import LevelDiscovery
        sys.path.pop(0)
        
        discovery = LevelDiscovery()
        
        # 只测试1m和15m
        for interval in ["1m", "15m"]:
            klines = klines_data.get(interval, [])
            if not klines:
                continue
            
            print(f"\n  {interval} Timeframe:")
            
            # 转换格式
            klines_converted = convert_klines_format(klines)
            
            # 获取当前价格
            current_price = float(klines[-1][4])
            
            # 发现候选价位
            all_levels = discovery.discover_all(klines_converted, current_price)
            
            # 分类为支撑和阻力
            support_levels = [l for l in all_levels if l['type'] == 'SUPPORT']
            resistance_levels = [l for l in all_levels if l['type'] == 'RESISTANCE']
            
            print(f"    Found {len(support_levels)} support levels")
            print(f"    Found {len(resistance_levels)} resistance levels")
            
            # 显示Top 3（按强度排序）
            all_levels_sorted = sorted(all_levels, key=lambda x: x.get('strength', 0), reverse=True)
            if all_levels_sorted:
                print(f"    Top 3 Levels:")
                for i, level in enumerate(all_levels_sorted[:3], 1):
                    print(f"      {i}. {level['type']:>10} @ ${level['price']:,.0f} "
                          f"(Strength: {level.get('strength', 0):.2f})")
        
        print("\nResult: PASS")
        return True
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_multi_timeframe_analysis():
    """测试5: 多周期趋势分析（使用新模块）"""
    print_section("TEST 5: Multi-Timeframe Trend Analysis")
    
    try:
        # 检查新模块是否存在
        new_module_path = "rl/market_analysis/multi_timeframe_analyzer.py"
        if not os.path.exists(new_module_path):
            print("Result: SKIP - New module not integrated yet")
            print("  File expected at: " + new_module_path)
            return None
        
        # 使用绝对导入
        from rl.market_analysis.multi_timeframe_analyzer import MultiTimeframeAnalyzer
        from rl.market_analysis.indicators import TechnicalAnalyzer
        
        # 需要获取K线数据
        from client import BinanceFuturesClient
        
        client = BinanceFuturesClient()
        
        # 获取K线
        klines_1m_raw = client.get_klines("BTCUSDT", "1m", 200)
        klines_15m_raw = client.get_klines("BTCUSDT", "15m", 200)
        klines_8h_raw = client.get_klines("BTCUSDT", "8h", 150)
        klines_1w_raw = client.get_klines("BTCUSDT", "1w", 100)
        
        # 转换格式
        klines_dict = {
            "1m": convert_klines_format(klines_1m_raw),
            "15m": convert_klines_format(klines_15m_raw),
            "8h": convert_klines_format(klines_8h_raw),
            "1w": convert_klines_format(klines_1w_raw)
        }
        
        # 分析各周期
        analyzer = TechnicalAnalyzer()
        analysis_dict = {}
        for tf, klines in klines_dict.items():
            if klines:
                analysis_dict[tf] = analyzer.analyze(klines)
        
        # 多周期综合分析
        multi_analyzer = MultiTimeframeAnalyzer()
        trend = multi_analyzer.analyze_综合趋势(klines_dict, analysis_dict)
        timing = multi_analyzer.analyze_入场时机(klines_dict, analysis_dict)
        
        print(f"\n  Comprehensive Trend:")
        print(f"    Direction: {trend['direction']}")
        print(f"    Confidence: {trend['confidence']*100:.1f}%")
        print(f"    Type: {trend['type']}")
        print(f"    Strength: {trend['strength']:.1f}")
        print(f"    Consistency: {trend['consistency']*100:.1f}%")
        
        print(f"\n  Entry Timing:")
        print(f"    Quality: {timing['quality']}")
        print(f"    Score: {timing['score']:.1f}")
        if timing['signals']:
            print(f"    Signals: {', '.join(timing['signals'][:3])}")
        
        print(f"\n  Timeframe Details:")
        for tf, details in trend['timeframe_details'].items():
            weight = trend['weights_used'].get(tf, 0)
            print(f"    {tf:>3}: {details['direction']:>8} (ADX: {details['adx']:.1f}, Weight: {weight*100:.0f}%)")
        
        print("\nResult: PASS")
        return trend
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_dynamic_threshold():
    """测试6: AI动态阈值计算（使用新模块）"""
    print_section("TEST 6: AI Dynamic Threshold Calculation")
    
    try:
        # 检查新模块是否存在
        new_module_path = "rl/learning/dynamic_threshold.py"
        if not os.path.exists(new_module_path):
            print("Result: SKIP - New module not integrated yet")
            print("  File expected at: " + new_module_path)
            return None
        
        # 使用绝对导入
        from rl.learning.dynamic_threshold import DynamicThresholdOptimizer
        
        optimizer = DynamicThresholdOptimizer("rl_data")
        
        # 模拟市场状态
        market_state = {
            "volatility": 0.03,
            "adx": 35,
            "volume_ratio": 1.2
        }
        
        # 模拟最近交易
        recent_trades = [
            {"pnl": 50, "timestamp": "2026-01-15T10:00:00"},
            {"pnl": -30, "timestamp": "2026-01-15T10:15:00"},
            {"pnl": 40, "timestamp": "2026-01-15T10:30:00"},
        ]
        
        threshold, details = optimizer.get_threshold(market_state, recent_trades)
        
        print(f"\n  Current Threshold: {threshold}")
        print(f"    Base: {details['base']:.1f}")
        print(f"    Market Adjustment: {details['market_adj']:+.1f}")
        print(f"    Performance Adjustment: {details['performance_adj']:+.1f}")
        print(f"    Final: {details['final']}")
        
        # 获取统计
        stats = optimizer.get_stats()
        print(f"\n  Statistics:")
        print(f"    Average Threshold: {stats['avg_threshold']:.1f}")
        print(f"    Threshold Range: [{stats['threshold_range'][0]:.0f}, {stats['threshold_range'][1]:.0f}]")
        print(f"    Total Adjustments: {stats['total_adjustments']}")
        
        print("\nResult: PASS")
        return threshold
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_trade_history():
    """测试7: 交易记录读取"""
    print_section("TEST 7: Trade History Reading")
    
    try:
        # 直接导入
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rl', 'core'))
        from knowledge import TradeLogger
        sys.path.pop(0)
        
        logger = TradeLogger("rl_data/trades.db")
        
        # 读取最近5笔交易
        trades = logger.get_recent_trades(limit=5)
        
        print(f"\n  Total Trades in DB: {len(logger.get_recent_trades(limit=1000))}")
        print(f"\n  Last 5 Trades:")
        
        for i, trade in enumerate(trades, 1):
            trade_id = trade.get('trade_id', 'N/A')
            direction = trade.get('direction', 'N/A')
            pnl = trade.get('pnl', 0)
            pnl_pct = trade.get('pnl_percent', 0)
            reason = trade.get('exit_reason', 'N/A')
            
            print(f"    {i}. {trade_id[:8]} | {direction:>5} | "
                  f"PnL: ${pnl:+.2f} ({pnl_pct:+.2f}%) | {reason}")
        
        # 统计信息
        stats = logger.get_stats()
        print(f"\n  Performance Statistics:")
        print(f"    Total Trades: {stats.get('total_trades', 0)}")
        print(f"    Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"    Total PnL: ${stats.get('total_pnl', 0):.2f}")
        print(f"    Profit Factor: {stats.get('profit_factor', 0):.2f}")
        print(f"    Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}")
        print(f"    Max Drawdown: {stats.get('max_drawdown', 0):.2f}%")
        
        print("\nResult: PASS")
        return stats
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_learning_system():
    """测试8: 学习系统状态"""
    print_section("TEST 8: Learning System Status")
    
    try:
        import json
        
        # 读取各学习模块的状态文件
        learning_files = {
            "Level Stats": "rl_data/level_stats.json",
            "SL/TP Stats": "rl_data/sl_tp_stats.json",
            "Entry Learner": "rl_data/entry_learner_v2.json",
            "Dynamic Threshold": "rl_data/dynamic_threshold.json",
        }
        
        for name, file_path in learning_files.items():
            print(f"\n  {name}:")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 显示关键信息
                if "Level Stats" in name:
                    print(f"    Total Trades: {data.get('total_trades', 0)}")
                    print(f"    Effective Trades: {data.get('effective_trades', 0)}")
                    weights = data.get('weights', {})
                    print(f"    Feature Weights:")
                    for feat, weight in list(weights.items())[:3]:
                        print(f"      - {feat}: {weight*100:.1f}%")
                
                elif "SL/TP" in name:
                    print(f"    Total Trades: {data.get('total_trades', 0)}")
                    print(f"    Default SL: {data.get('default_sl_pct', 0):.2f}%")
                    print(f"    Default TP: {data.get('default_tp_pct', 0):.2f}%")
                    print(f"    Epsilon: {data.get('epsilon', 0):.2f}")
                
                elif "Entry Learner" in name:
                    records = data.get('entry_records', [])
                    print(f"    Total Samples: {len(records)}")
                    print(f"    Epsilon: {data.get('epsilon', 0):.2f}")
                    weights = data.get('params', {}).get('entry_type_weights', {})
                    if weights:
                        print(f"    Entry Type Weights:")
                        for etype, weight in list(weights.items())[:3]:
                            print(f"      - {etype}: {weight:.2f}")
                
                elif "Dynamic Threshold" in name:
                    print(f"    Current Threshold: {data.get('current_threshold', 0)}")
                    history = data.get('threshold_history', [])
                    print(f"    Adjustment History: {len(history)} records")
            else:
                print(f"    File not found")
        
        print("\nResult: PASS")
        return True
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def test_batch_position_manager():
    """测试9: 智能分批建仓系统"""
    print_section("TEST 9: Batch Position Manager")
    
    try:
        # 检查新模块是否存在
        new_module_path = "rl/position/batch_position_manager.py"
        if not os.path.exists(new_module_path):
            print("Result: SKIP - New module not integrated yet")
            print("  File expected at: " + new_module_path)
            return None
        
        # 使用绝对导入
        from rl.position.batch_position_manager import BatchPositionManager
        
        manager = BatchPositionManager()
        
        # 测试分批建仓规划
        market_state = {
            "volatility": 0.03,
            "adx": 35,
            "volume_ratio": 1.2
        }
        
        batches = manager.plan_entry_batches(
            total_capital=10000,
            signal_strength=75,
            win_rate=0.55,
            avg_win_loss_ratio=1.8,
            current_positions=1,
            market_state=market_state
        )
        
        print(f"\n  Entry Batch Plan:")
        print(f"    Total Batches: {len(batches)}")
        for batch in batches:
            print(f"      Batch {batch['batch_id']}: "
                  f"Size {batch['size_ratio']*100:.0f}%, "
                  f"Leverage {batch['leverage']}x, "
                  f"Offset {batch['entry_offset']*100:.1f}%")
        
        summary = manager.calculate_position_summary(batches, 10000)
        print(f"\n  Summary:")
        print(f"    Total Size: {summary['total_size_ratio']*100:.0f}%")
        print(f"    Avg Leverage: {summary['avg_leverage']:.1f}x")
        print(f"    Total Risk: {summary['total_risk']*100:.2f}%")
        
        # 测试分批止盈规划
        exit_batches = manager.plan_exit_batches(
            entry_price=91000,
            position_size=0.5,
            current_price=91500,
            unrealized_pnl_pct=2.5
        )
        
        print(f"\n  Exit Batch Plan:")
        print(f"    Total Levels: {len(exit_batches)}")
        for batch in exit_batches:
            print(f"      At {batch['target_pnl']}% profit: "
                  f"Close {batch['close_ratio']*100:.0f}% "
                  f"@ ${batch['target_price']:.0f}")
        
        print("\nResult: PASS")
        return True
    except Exception as e:
        print(f"Result: FAIL - {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试流程"""
    print("\n")
    print("################################################################################")
    print("#                                                                              #")
    print("#                  BTC Trading System v4.0 - Function Test                    #")
    print("#                                                                              #")
    print("################################################################################")
    print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试1: API连接
    client = test_api_connection()
    results['API Connection'] = client is not None
    
    if not client:
        print("\n" + "="*80)
        print("ERROR: Cannot proceed without API connection")
        print("Please check your API keys in .env file")
        print("="*80)
        return
    
    # 测试2: K线数据
    klines_data = test_klines_fetch(client)
    results['K-line Fetching'] = klines_data is not None
    
    # 测试3: 技术指标
    analysis = test_technical_indicators(klines_data)
    results['Technical Indicators'] = analysis is not None
    
    # 测试4: 支撑阻力
    sr_result = test_support_resistance(klines_data)
    results['Support/Resistance'] = sr_result is not None
    
    # 测试5: 多周期分析（新模块）
    trend = test_multi_timeframe_analysis()
    results['Multi-Timeframe Analysis'] = trend is not None
    
    # 测试6: 动态阈值（新模块）
    threshold = test_dynamic_threshold()
    results['Dynamic Threshold'] = threshold is not None
    
    # 测试7: 交易历史
    trade_stats = test_trade_history()
    results['Trade History'] = trade_stats is not None
    
    # 测试8: 学习系统
    learning = test_learning_system()
    results['Learning System'] = learning is not None
    
    # 测试9: 分批建仓（新模块）
    batch_result = test_batch_position_manager()
    results['Batch Position Manager'] = batch_result is not None
    
    # 汇总结果
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n  Total Tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass Rate: {passed/total*100:.1f}%")
    
    print(f"\n  Details:")
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[XX]"
        print(f"    {symbol} {test_name:<30} {status}")
    
    print(f"\n" + "="*80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    if passed == total:
        print("All tests passed! System is ready for Web UI development.")
    else:
        print("Some tests failed. Please fix the issues before proceeding.")
    
    return results


if __name__ == "__main__":
    main()

