import os
from dotenv import load_dotenv

load_dotenv()

# 币安期货测试网配置
TESTNET_BASE_URL = "https://testnet.binancefuture.com"
TESTNET_WS_URL = "wss://testnet.binancefuture.com/ws"

# API密钥
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# 默认交易参数
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_LEVERAGE = 10
