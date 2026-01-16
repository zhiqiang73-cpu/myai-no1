# -*- coding: utf-8 -*-
"""Quick test for Agent initialization"""
import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(__file__))

# Create data directory
os.makedirs("data", exist_ok=True)

try:
    print("Importing modules...")
    from rl.core.agent import TradingAgent
    from client import BinanceFuturesClient
    
    print("[OK] Modules imported")
    
    print("\nInitializing API client...")
    client = BinanceFuturesClient()
    
    print("[OK] API client initialized")
    
    print("\nInitializing Agent...")
    agent = TradingAgent(client, data_dir="data")
    
    print("[OK] Agent initialized successfully!")
    print("\n=== All tests passed! Web UI can be started. ===")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print(f"  Module: {e.name if hasattr(e, 'name') else 'Unknown'}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"[ERROR] Initialization error: {e}")
    import traceback
    traceback.print_exc()

