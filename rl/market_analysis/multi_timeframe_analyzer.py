from typing import Dict


class MultiTimeframeAnalyzer:
    def __init__(self, weights=None):
        self.weights = weights or {"1m": 0.3, "15m": 0.3, "8h": 0.2, "1w": 0.2}

    def _trend_score(self, analysis: Dict) -> float:
        trend = analysis.get("trend", "NEUTRAL")
        if trend == "BULLISH":
            return 1.0
        if trend == "BEARISH":
            return -1.0
        return 0.0

    def analyze(self, a1m: Dict, a15m: Dict, a8h: Dict, a1w: Dict) -> Dict:
        macro_score = (
            self._trend_score(a8h) * self.weights.get("8h", 0.2)
            + self._trend_score(a1w) * self.weights.get("1w", 0.2)
        )
        micro_score = (
            self._trend_score(a1m) * self.weights.get("1m", 0.3)
            + self._trend_score(a15m) * self.weights.get("15m", 0.3)
        )

        macro_dir = "NEUTRAL"
        if macro_score > 0.1:
            macro_dir = "BULLISH"
        elif macro_score < -0.1:
            macro_dir = "BEARISH"

        micro_dir = "NEUTRAL"
        if micro_score > 0.1:
            micro_dir = "BULLISH"
        elif micro_score < -0.1:
            micro_dir = "BEARISH"

        return {
            "macro_trend": {"direction": macro_dir, "score": macro_score},
            "micro_trend": {"direction": micro_dir, "score": micro_score},
        }


