import statistics
import numpy as np
from enum import Enum
from sklearn.linear_model import LinearRegression


class Math(Enum):
    @staticmethod
    def std(datas, line_num=5, fig=False):
        reg = LinearRegression()

        idx = np.arange(1, len(datas) + 1)
        reg.fit(idx.reshape(-1, 1), datas)

        # print(reg.coef_[0]) # 斜率
        # print(reg.intercept_) # 截距
        df = {
            "TL": np.full((len(datas),), statistics.median(datas)),
        }

        df["y-TL"] = datas - df["TL"]
        df["SD"] = df["y-TL"].std()
        for i in range(1, 4):
            df[f"TL-{i}SD"] = df["TL"] - i * df["SD"]
            df[f"TL+{i}SD"] = df["TL"] + i * df["SD"]
        df["datas"] = np.array(datas)
        comp_list = (
            [f"TL+{i}SD" for i in range(3, 0, -1)]
            + ["TL"]
            + [f"TL-{i}SD" for i in range(1, 4)]
        )

        return (df, comp_list)

    @staticmethod
    def quartile(datas):
        lst_data = [np.percentile(datas, p) for p in (25, 50, 75)]
        lst_data.append(round(statistics.mean(datas), 2))
        return lst_data

    @staticmethod
    def mean_reversion(datas, line_num=5):
        prob_data = [0.001, 0.021, 0.136, 0.341, 0.341, 0.136, 0.021, 0.001]
        reg = LinearRegression()
        _, price = datas

        idx = np.arange(1, len(price) + 1)
        reg.fit(idx.reshape(-1, 1), price)

        # print(reg.coef_[0]) # 斜率
        # print(reg.intercept_) # 截距
        df = {"TL": reg.intercept_ + idx * reg.coef_[0]}
        df["y-TL"] = price - df["TL"]
        df["SD"] = df["y-TL"].std()
        for i in range(1, 4):
            df[f"TL-{i}SD"] = df["TL"] - i * df["SD"]
            df[f"TL+{i}SD"] = df["TL"] + i * df["SD"]

        df["close"] = np.array(price)
        lastPrice = df["close"][-1]
        up_prob, hold_prob, down_prob = 0, 0, sum(prob_data)
        comp_list = (
            [f"TL+{i}SD" for i in range(3, 0, -1)]
            + ["TL"]
            + [f"TL-{i}SD" for i in range(1, 4)]
        )

        for idx, item in enumerate(comp_list):
            if lastPrice < df[item][-1]:
                up_prob += prob_data[idx]
                down_prob -= prob_data[idx]
            else:
                hold_prob += prob_data[idx]
                down_prob -= prob_data[idx]
                break

        TL = df["TL"][-1]
        expect_val_bull_1 = up_prob * (TL - lastPrice) - down_prob * lastPrice
        expect_val_bull_2 = up_prob * (TL - lastPrice) - down_prob * (
            lastPrice - df["TL-3SD"][-1]
        )
        expect_val_bear_1 = down_prob * (lastPrice - TL) - up_prob * (
            df["TL+3SD"][-1] - lastPrice
        )

        return {
            "prob": [up_prob * 100, hold_prob * 100, down_prob * 100],
            "TL": TL,
            "expect": [expect_val_bull_1, expect_val_bull_2, expect_val_bear_1],
            "staff": [df[title][-1] for title in comp_list],
        }
