from typing import Dict


class RiskController:
    def __init__(self):
        self.max_daily_loss_pct = 3.0
        self.max_consecutive_losses = 5
        self.consecutive_losses = 0
        self.daily_pnl_pct = 0.0

    def update_trade_result(self, pnl_percent: float) -> None:
        self.daily_pnl_pct += pnl_percent
        if pnl_percent < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def can_trade(self) -> Dict:
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            return {"allowed": False, "reason": "daily_loss_limit"}
        if self.consecutive_losses >= self.max_consecutive_losses:
            return {"allowed": False, "reason": "consecutive_losses"}
        return {"allowed": True, "reason": "ok"}


