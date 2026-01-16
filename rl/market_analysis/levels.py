import json
import os
from typing import Dict, List

from .level_finder import LevelFeatureCalculator, DEFAULT_WEIGHTS


class LevelDiscovery:
    def __init__(self, buckets: List[int] = None):
        self.buckets = buckets or [50, 100, 250, 500, 1000]

    def _round_level(self, price: float, bucket: int) -> float:
        return round(price / bucket) * bucket

    def _integer_levels(self, prices: List[float]) -> List[float]:
        levels = set()
        for bucket in self.buckets:
            for price in prices:
                levels.add(self._round_level(price, bucket))
        return list(levels)

    def _swing_levels(self, klines: List[Dict], window: int = 5) -> List[float]:
        # 增大窗口到5根K线，更准确识别局部高低点
        levels = set()
        for i in range(window, len(klines) - window):
            high = klines[i]["high"]
            low = klines[i]["low"]
            left = klines[i - window:i]
            right = klines[i + 1:i + 1 + window]
            if all(high >= k["high"] for k in left) and all(
                high >= k["high"] for k in right
            ):
                levels.add(high)
            if all(low <= k["low"] for k in left) and all(
                low <= k["low"] for k in right
            ):
                levels.add(low)
        return list(levels)

    def _fractal_levels(self, klines: List[Dict], window: int = 3) -> List[float]:
        # 分形高低点识别（更严格的高低点）
        levels = set()
        for i in range(window, len(klines) - window):
            high = klines[i]["high"]
            low = klines[i]["low"]
            left = klines[i - window:i]
            right = klines[i + 1:i + 1 + window]
            # 分形高点：中间K线的high严格高于左右所有K线的high
            if all(high > k["high"] for k in left) and all(high > k["high"] for k in right):
                levels.add(high)
            # 分形低点
            if all(low < k["low"] for k in left) and all(low < k["low"] for k in right):
                levels.add(low)
        return list(levels)

    def _consolidation_levels(self, klines: List[Dict], min_touches: int = 3) -> List[float]:
        # 识别价格盘整区域（多次触及的价格）
        if len(klines) < 20:
            return []
        levels = set()
        tolerance = 0.005  # 0.5%容差
        price_touches = {}
        for k in klines:
            for p in [k["high"], k["low"], k["close"]]:
                rounded = round(p / 50) * 50  # 50美元精度
                price_touches[rounded] = price_touches.get(rounded, 0) + 1
        for price, count in price_touches.items():
            if count >= min_touches:
                levels.add(price)
        return list(levels)

    def _volume_profile_levels(self, klines: List[Dict], bucket: int = 50) -> List[float]:
        # 成交量密集区（增加更多级别）
        buckets = {}
        for k in klines:
            price = self._round_level(k["close"], bucket)
            buckets[price] = buckets.get(price, 0) + k.get("volume", 0)
        top = sorted(buckets.items(), key=lambda x: x[1], reverse=True)[:8]
        return [p for p, _ in top]

    def _recent_high_low(self, klines: List[Dict], lookback: int = 20) -> List[float]:
        # 最近N根K线的最高最低点
        if len(klines) < lookback:
            lookback = len(klines)
        recent = klines[-lookback:]
        highs = [k["high"] for k in recent]
        lows = [k["low"] for k in recent]
        return [max(highs), min(lows)]

    def discover_all(
        self,
        klines: List[Dict],
        current_price: float = None,
        atr: float = None,
        max_distance_pct: float = None,
    ) -> Dict:
        if not klines:
            return {"support": [], "resistance": []}

        prices = [k["close"] for k in klines]
        current_price = current_price or prices[-1]

        candidates = set()
        # 多种方法发现候选位
        candidates.update(self._integer_levels(prices))
        candidates.update(self._swing_levels(klines, window=5))
        candidates.update(self._fractal_levels(klines, window=3))
        candidates.update(self._consolidation_levels(klines, min_touches=3))
        candidates.update(self._volume_profile_levels(klines))
        candidates.update(self._recent_high_low(klines, lookback=30))

        # Dynamic band based on volatility (ATR)
        if max_distance_pct is None:
            if atr and current_price > 0:
                # 波动率越高，搜索范围越大
                max_distance_pct = min(max((atr / current_price) * 400, 1.0), 10.0)
            else:
                max_distance_pct = 5.0

        def within_band(level: float) -> bool:
            return abs(level - current_price) / current_price * 100 <= max_distance_pct

        filtered = [c for c in candidates if within_band(c)]
        if not filtered:
            filtered = list(candidates)

        # 增加返回的候选位数量
        support = sorted([c for c in filtered if c <= current_price])[-12:]
        resistance = sorted([c for c in filtered if c >= current_price])[:12]

        return {"support": support, "resistance": resistance}


class LevelScoring:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.weights = self._load_weights()
        self.feature_calc = LevelFeatureCalculator()

    def _load_weights(self) -> Dict:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                weights = data.get("weights", DEFAULT_WEIGHTS.copy())
                for k, v in DEFAULT_WEIGHTS.items():
                    weights.setdefault(k, v)
                total = sum(weights.values())
                if total > 0:
                    for k in weights:
                        weights[k] = weights[k] / total
                return weights
        return DEFAULT_WEIGHTS.copy()

    def save_weights(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"weights": self.weights}, f, indent=2)

    def score(self, level: float, klines: List[Dict]) -> float:
        features = self.feature_calc.calculate(level, klines)
        score = 0.0
        for k, w in self.weights.items():
            score += float(features.get(k, 0)) * w
        return score * 100

    def score_multi_tf(
        self,
        level: float,
        klines_by_tf: Dict[str, List[Dict]],
        tf_weights: Dict[str, float],
        extra_features: Dict[str, float] = None,
    ) -> Dict:
        combined = {}
        for tf, kl in klines_by_tf.items():
            features = self.feature_calc.calculate(level, kl)
            w = tf_weights.get(tf, 0)
            for k, v in features.items():
                combined[k] = combined.get(k, 0) + v * w

        combined["multi_tf_confirm"] = self.feature_calc.multi_tf_confirm(
            level, klines_by_tf, tf_weights
        )
        if extra_features:
            for k, v in extra_features.items():
                combined[k] = v

        score = 0.0
        for k, w in self.weights.items():
            score += float(combined.get(k, 0)) * w
        return {"score": score * 100, "features": combined}

    def get_features(self, level: float, klines: List[Dict]) -> Dict:
        return self.feature_calc.calculate(level, klines)

