from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class ExitDecision:
    reason: str
    confirmations: List[str]


class PositionState:
    def __init__(self, position: dict):
        self.position = position


class ExitManager:
    def __init__(self, _params_path: str = None):
        self.params = {
            "max_loss_pct": 1.0,
            "min_profit_pct": 0.3,
            "max_hold_minutes": 45,
            "min_hold_minutes": 5,
            "opportunity_delta": 15,
            "profit_lock_start": 0.6,
            "profit_lock_base_drop": 0.5,
            "profit_lock_slope": 0.05,
        }

    def update_params(self, params: dict) -> None:
        if not params:
            return
        for k, v in params.items():
            if k in self.params and v is not None:
                self.params[k] = v

    def _get_hold_minutes(self, position: dict) -> Optional[float]:
        ts = position.get("timestamp_open")
        if not ts:
            return None
        try:
            opened = datetime.fromisoformat(ts)
        except Exception:
            return None
        return (datetime.now() - opened).total_seconds() / 60

    def _get_signal_scores(self, market: dict) -> Tuple[float, float, float]:
        scores = market.get("entry_scores") or {}
        threshold = market.get("entry_threshold") or {}
        long_score = float(scores.get("long", 0))
        short_score = float(scores.get("short", 0))
        min_score = float(threshold.get("threshold", market.get("min_score", 0)))
        return long_score, short_score, min_score

    def evaluate(
        self, position: dict, market: dict, current_price: float, state: Optional[dict] = None
    ) -> Optional[ExitDecision]:
        direction = position.get("direction")
        entry = position.get("entry_price", 0)
        stop_loss = position.get("stop_loss")
        take_profit = position.get("take_profit")
        if entry <= 0:
            return None

        if direction == "LONG":
            pnl_pct = (current_price - entry) / entry * 100
            if stop_loss and current_price <= stop_loss:
                return ExitDecision("STOP_LOSS", ["stop_loss_hit"])
            if take_profit and current_price >= take_profit:
                return ExitDecision("TAKE_PROFIT", ["take_profit_hit"])
        else:
            pnl_pct = (entry - current_price) / entry * 100
            if stop_loss and current_price >= stop_loss:
                return ExitDecision("STOP_LOSS", ["stop_loss_hit"])
            if take_profit and current_price <= take_profit:
                return ExitDecision("TAKE_PROFIT", ["take_profit_hit"])

        if pnl_pct <= -self.params["max_loss_pct"]:
            return ExitDecision("MAX_LOSS", ["max_loss"])

        if state is not None:
            max_pnl = max(state.get("max_pnl_pct", pnl_pct), pnl_pct)
            state["max_pnl_pct"] = max_pnl
            lock_start = self.params.get("profit_lock_start", 0.6)
            base_drop = self.params.get("profit_lock_base_drop", 0.5)
            slope = self.params.get("profit_lock_slope", 0.05)
            if max_pnl >= lock_start:
                drop = max(0.15, base_drop - max_pnl * slope)
                if pnl_pct <= max_pnl - drop:
                    return ExitDecision(
                        "PROFIT_LOCK",
                        [f"max_pnl={max_pnl:.2f}", f"drop={drop:.2f}"],
                    )

        hold_minutes = self._get_hold_minutes(position)
        long_score, short_score, min_score = self._get_signal_scores(market)
        min_profit = self.params["min_profit_pct"]
        min_hold = self.params["min_hold_minutes"]
        opportunity_delta = self.params["opportunity_delta"]

        if hold_minutes is not None and hold_minutes >= min_hold and min_score > 0:
            if direction == "LONG":
                if short_score >= min_score + opportunity_delta and pnl_pct < min_profit:
                    return ExitDecision(
                        "OPPORTUNITY_SWITCH",
                        [
                            "better_short_signal",
                            f"short={short_score:.0f}",
                            f"threshold={min_score:.0f}",
                        ],
                    )
            else:
                if long_score >= min_score + opportunity_delta and pnl_pct < min_profit:
                    return ExitDecision(
                        "OPPORTUNITY_SWITCH",
                        [
                            "better_long_signal",
                            f"long={long_score:.0f}",
                            f"threshold={min_score:.0f}",
                        ],
                    )

        max_hold = self.params["max_hold_minutes"]
        if hold_minutes is not None and hold_minutes >= max_hold and abs(pnl_pct) < min_profit:
            return ExitDecision(
                "TIME_COST",
                ["time_cost", f"hold_minutes={hold_minutes:.1f}"],
            )

        if pnl_pct >= self.params["min_profit_pct"]:
            return None

        return None

