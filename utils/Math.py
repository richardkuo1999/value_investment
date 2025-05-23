import os
import sys
import statistics
import numpy as np
from enum import Enum
from sklearn.linear_model import LinearRegression

sys.path.append(os.path.dirname(__file__) + "/..")

from utils.utils import logger


class Math(Enum):
    PROB_WEIGHTS = [0.001, 0.021, 0.136, 0.341, 0.341, 0.136, 0.021, 0.001]

    @staticmethod
    def _generate_band_labels() -> list[str]:
        """Generate labels for standard deviation bands."""
        return (
            [f"TL+{i}SD" for i in range(3, 0, -1)]
            + ["TL"]
            + [f"TL-{i}SD" for i in range(1, 4)]
        )

    @staticmethod
    def std(datas: list[float]):
        if not datas:
            raise ValueError("Input data cannot be empty")
        try:
            datas = np.array(datas, dtype=float)
        except ValueError:
            raise ValueError("Input data must contain only numeric values")

        result = {}
        result["TL"] = np.full_like(datas, statistics.median(datas))
        result["y-TL"] = datas - result["TL"]
        result["SD"] = np.std(result["y-TL"], ddof=1)  # Sample standard deviation
        if result["SD"] == 0:
            logger.warning("Standard deviation is zero, returning identical bands")
            result["SD"] = 1e-10  # Avoid division by zero

        for i in range(1, 4):
            result[f"TL-{i}SD"] = result["TL"] - i * result["SD"]
            result[f"TL+{i}SD"] = result["TL"] + i * result["SD"]
        result["datas"] = datas

        return result, Math._generate_band_labels()

    @staticmethod
    def quartile(datas: list[float]) -> list[float]:
        if not datas:
            raise ValueError("Input data cannot be empty")
        try:
            datas = np.array(datas, dtype=float)
        except ValueError:
            raise ValueError("Input data must contain only numeric values")

        percentiles = [np.percentile(datas, p) for p in (25, 50, 75)]
        mean = float(np.mean(datas))  # Avoid rounding for flexibility
        return percentiles + [mean]

    @staticmethod
    def mean_reversion(prices):
        if not isinstance(prices, np.ndarray):
            raise ValueError("Price data must contain only numeric values")

        # Fit linear regression
        reg = LinearRegression()
        idx = np.arange(1, len(prices) + 1)
        reg.fit(idx.reshape(-1, 1), prices)

        # Calculate trend line and bands
        result = {}
        result["TL"] = reg.intercept_ + idx * reg.coef_[0]
        result["y-TL"] = prices - result["TL"]
        result["SD"] = np.std(result["y-TL"], ddof=1)  # Sample standard deviation
        if result["SD"] == 0:
            logger.warning("Standard deviation is zero, using small value to avoid division by zero")
            result["SD"] = 1e-10

        for i in range(1, 4):
            result[f"TL-{i}SD"] = result["TL"] - i * result["SD"]
            result[f"TL+{i}SD"] = result["TL"] + i * result["SD"]
        result["close"] = prices

        # Calculate probabilities
        last_price = prices[-1]
        band_labels = Math._generate_band_labels()
        up_prob, hold_prob, down_prob = 0.0, 0.0, sum(Math.PROB_WEIGHTS.value)
        for idx, band in enumerate(band_labels):
            if last_price < result[band][-1]:
                up_prob += Math.PROB_WEIGHTS.value[idx]
                down_prob -= Math.PROB_WEIGHTS.value[idx]
            else:
                hold_prob += Math.PROB_WEIGHTS.value[idx]
                down_prob -= Math.PROB_WEIGHTS.value[idx]
                break

        # Calculate expected values
        TL = result["TL"][-1]
        expect_val_bull_1 = up_prob * (TL - last_price) - down_prob * last_price
        expect_val_bull_2 = up_prob * (TL - last_price) - down_prob * (last_price - result["TL-3SD"][-1])
        expect_val_bear_1 = down_prob * (last_price - TL) - up_prob * (result["TL+3SD"][-1] - last_price)

        return {
            "prob": [up_prob * 100, hold_prob * 100, down_prob * 100],
            "TL": [float(TL)],
            "expect": [expect_val_bull_1, expect_val_bull_2, expect_val_bear_1],
            "targetprice": [float(result[title][-1]) for title in band_labels]
        }

if __name__ == "__main__":
    # Example usage
    sample_data = [100, 102, 101, 103, 105, 104]
    sample_prices = ([], [100, 102, 101, 103, 105, 104])  # For mean_reversion

    # Test std
    std_result, band_labels = Math.std(sample_data)
    print("std result:", {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in std_result.items()})
    print("Band labels:", band_labels)

    # Test quartile
    quartile_result = Math.quartile(sample_data)
    print("Quartile result:", quartile_result)

    # Test mean_reversion
    mr_result = Math.mean_reversion(sample_prices)
    print("Mean reversion result:", mr_result)