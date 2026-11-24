import unittest
from datetime import date

import numpy as np
import pandas as pd

from mma_pipeline import BASE_FIELDS
from mma_service import compare


class DummyModel:
    def predict_proba(self, frame):
        p = .5 + np.tanh(frame["diff_age"].to_numpy() / 20) * .2
        return np.column_stack((1 - p, p))


class ServiceTests(unittest.TestCase):
    def test_swapping_fighters_reverses_probability(self):
        rows = []
        for identifier, age in (("a", 29), ("b", 35)):
            row = dict.fromkeys(BASE_FIELDS, 0.0)
            row.update(fighter_id=identifier, name=identifier, age=age,
                       prior_fights=5, style="Mixto", last_fight_date="2026-10-10")
            rows.append(row)
        fighters = pd.DataFrame(rows).set_index("fighter_id", drop=False)
        pairs = pd.DataFrame({"style_pair": ["Mixto × Mixto"], "fights": [20], "first_style_win_rate": [np.nan]})
        bundle = {"model": DummyModel(), "source_last_date": "2026-10-10"}
        first = compare(bundle, fighters, pairs, "a", "b", "lightweight", 3, as_of=date(2026, 11, 23))
        second = compare(bundle, fighters, pairs, "b", "a", "lightweight", 3, as_of=date(2026, 11, 23))
        self.assertAlmostEqual(first["probability_a"] + second["probability_a"], 1)
        with self.assertRaises(ValueError):
            compare(bundle, fighters, pairs, "a", "a", "lightweight", 3)


if __name__ == "__main__":
    unittest.main()
