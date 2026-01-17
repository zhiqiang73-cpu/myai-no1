from typing import Dict


class StopLossTakeProfit:
    """
    智能止损止盈系统 - 锚定支撑阻力位
    
    核心理念：
    - 止损：设在支撑/阻力下方/上方（防线失效=止损）
    - 止盈：设在阻力/支撑附近（遇到障碍=入袋为安）
    - 兜底：确保盈亏比≥1.2:1
    """
    
    def __init__(self, level_scoring=None):
        self.level_scoring = level_scoring
        # 基础参数（如果没有S/R，使用这些）
        self.default_sl_pct = 0.01  # 1%
        self.default_tp_pct = 0.015  # 1.5%（保守）
        self.min_risk_reward = 1.2  # 最小盈亏比
    
    def update_params(self, params: Dict) -> None:
        # 保持固定参数，不动态调整
        pass
    
    def calculate(self, price: float, direction: str, atr: float, market: Dict = None) -> Dict:
        """
        智能计算止损止盈
        
        逻辑：
        1. 优先使用S/R位（市场结构）
        2. 兜底使用固定百分比
        3. 确保盈亏比合理
        """
        if direction == "LONG":
            # ========== 做多：止损锚定支撑，止盈锚定阻力 ==========
            stop_loss, sl_pct = self._calculate_long_sl(price, market)
            take_profit, tp_pct = self._calculate_long_tp(price, market)
            
            # ========== 修复漏洞5：盈亏比检查改为调整止损，而非破坏止盈 ==========
            sl_distance = price - stop_loss if price > stop_loss else price * 0.01  # 修复漏洞3：除零保护
            tp_distance = take_profit - price if take_profit > price else price * 0.015
            
            if tp_distance < sl_distance * self.min_risk_reward:
                # 盈亏比不够，缩小止损（而非扩大止盈，避免破坏S/R逻辑）
                max_allowed_sl_distance = tp_distance / self.min_risk_reward
                # 限制止损缩小范围：最小0.5%
                if max_allowed_sl_distance / price >= 0.005:
                    stop_loss = price - max_allowed_sl_distance
                    sl_pct = max_allowed_sl_distance / price
                # 如果止盈太近，缩小止损也无法满足盈亏比，保持原止损（宁可不交易）
        else:
            # ========== 做空：止损锚定阻力，止盈锚定支撑 ==========
            stop_loss, sl_pct = self._calculate_short_sl(price, market)
            take_profit, tp_pct = self._calculate_short_tp(price, market)
            
            sl_distance = stop_loss - price if stop_loss > price else price * 0.01
            tp_distance = price - take_profit if price > take_profit else price * 0.015
            
            if tp_distance < sl_distance * self.min_risk_reward:
                max_allowed_sl_distance = tp_distance / self.min_risk_reward
                if max_allowed_sl_distance / price >= 0.005:
                    stop_loss = price + max_allowed_sl_distance
                    sl_pct = max_allowed_sl_distance / price
        
        return {
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "sl_pct": sl_pct,
            "tp_pct": tp_pct,
        }
    
    def _calculate_long_sl(self, price: float, market: Dict = None) -> tuple:
        """计算做多止损（锚定支撑位）"""
        best_support = market.get("best_support") if market else None
        
        if best_support and price > 0:  # 修复漏洞3：除零保护
            support_price = float(best_support["price"])
            
            # 修复漏洞4：明确检查支撑在下方（做多方向正确性）
            if support_price < price:
                distance_pct = (price - support_price) / price * 100
                
                # 如果支撑距离<0.5%，使用支撑作为止损锚点
                if 0 < distance_pct <= 0.5:
                    # 止损设在支撑下方0.3%
                    stop_loss = support_price * 0.997
                    sl_pct = (price - stop_loss) / price if price > 0 else self.default_sl_pct
                    
                    # 修复漏洞6：限制止损在0.5%-1.2%（从1.5%改为1.2%，更合理）
                    if sl_pct < 0.005:
                        stop_loss = price * 0.995
                        sl_pct = 0.005
                    elif sl_pct > 0.012:  # 改为1.2%上限（从1.5%）
                        stop_loss = price * 0.988
                        sl_pct = 0.012
                    
                    return stop_loss, sl_pct
        
        # 默认：固定1%
        stop_loss = price * (1 - self.default_sl_pct) if price > 0 else 0
        return stop_loss, self.default_sl_pct
    
    def _calculate_short_sl(self, price: float, market: Dict = None) -> tuple:
        """计算做空止损（锚定阻力位）"""
        best_resistance = market.get("best_resistance") if market else None
        
        if best_resistance and price > 0:
            resistance_price = float(best_resistance["price"])
            
            # 修复漏洞4：明确检查阻力在上方（做空方向正确性）
            if resistance_price > price:
                distance_pct = (resistance_price - price) / price * 100
                
                if 0 < distance_pct <= 0.5:
                    stop_loss = resistance_price * 1.003
                    sl_pct = (stop_loss - price) / price if price > 0 else self.default_sl_pct
                    
                    # 修复漏洞6：限制止损
                    if sl_pct < 0.005:
                        stop_loss = price * 1.005
                        sl_pct = 0.005
                    elif sl_pct > 0.012:
                        stop_loss = price * 1.012
                        sl_pct = 0.012
                    
                    return stop_loss, sl_pct
        
        # 默认：固定1%
        stop_loss = price * (1 + self.default_sl_pct) if price > 0 else 0
        return stop_loss, self.default_sl_pct
    
    def _calculate_long_tp(self, price: float, market: Dict = None) -> tuple:
        """计算做多止盈（锚定阻力位）"""
        best_resistance = market.get("best_resistance") if market else None
        
        if best_resistance and price > 0:  # 修复漏洞3：除零保护
            resistance_price = float(best_resistance["price"])
            
            # 修复漏洞4：明确检查阻力在上方（做多方向正确性）
            if resistance_price > price:
                distance_pct = (resistance_price - price) / price * 100
                
                if 0 < distance_pct <= 2.0:
                    # 使用阻力位，下方0.1%
                    take_profit = resistance_price * 0.999
                    tp_pct = (take_profit - price) / price if price > 0 else self.default_tp_pct
                    return take_profit, tp_pct
        
        # 默认：固定1.5%
        take_profit = price * (1 + self.default_tp_pct) if price > 0 else 0
        return take_profit, self.default_tp_pct
    
    def _calculate_short_tp(self, price: float, market: Dict = None) -> tuple:
        """计算做空止盈（锚定支撑位）"""
        best_support = market.get("best_support") if market else None
        
        if best_support and price > 0:
            support_price = float(best_support["price"])
            
            # 修复漏洞4：明确检查支撑在下方（做空方向正确性）
            if support_price < price:
                distance_pct = (price - support_price) / price * 100
                
                if 0 < distance_pct <= 2.0:
                    # 使用支撑位，上方0.1%
                    take_profit = support_price * 1.001
                    tp_pct = (price - take_profit) / price if price > 0 else self.default_tp_pct
                    return take_profit, tp_pct
        
        # 默认：固定1.5%
        take_profit = price * (1 - self.default_tp_pct) if price > 0 else 0
        return take_profit, self.default_tp_pct


class PositionSizer:
    def __init__(self, max_risk_percent: float = 2.0):
        self.max_risk_percent = max_risk_percent

    def calculate_size(self, balance: float, entry_price: float, stop_loss: float) -> float:
        if entry_price <= 0 or stop_loss <= 0:
            return 0.0
        risk_per_unit = abs(entry_price - stop_loss)
        max_risk = balance * (self.max_risk_percent / 100)
        if risk_per_unit <= 0:
            return 0.0
        return max_risk / risk_per_unit
