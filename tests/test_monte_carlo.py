import unittest

import numpy as np
import pandas as pd

from monte_carlo import calibration_test, favorites, simulate_fight


class MonteCarloTests(unittest.TestCase):
    def test_single_fight_upset_rate_matches_probability(self):
        rate, error = simulate_fight(.9, 200_000, np.random.default_rng(0))
        self.assertAlmostEqual(rate, .1, delta=4 * error)

    def test_calibrated_market_is_not_rejected(self):
        rng = np.random.default_rng(1)
        probabilities = rng.uniform(.55, .9, 1000)
        observed = int((rng.random(1000) < probabilities).sum())
        self.assertGreater(calibration_test(probabilities, observed, 5000, rng)["p_value"], .01)

    def test_undervalued_favorites_are_detected(self):
        rng = np.random.default_rng(2)
        probabilities = np.full(1000, .6)
        observed = int((rng.random(1000) < .75).sum())
        result = calibration_test(probabilities, observed, 5000, rng)
        self.assertLess(result["p_value"], .001)
        self.assertGreater(observed, result["range_high"])

    def test_favorites_flips_side_and_skips_even_odds(self):
        bouts = pd.DataFrame({"event_date": ["2020-01-01"] * 3, "fighter_a": ["A", "C", "E"],
                              "fighter_b": ["B", "D", "F"], "winner_a": [1, 1, 0],
                              "open_prob_a": [.3, .5, .8]})
        result = favorites(bouts)
        self.assertEqual(result.favorite.tolist(), ["B", "E"])
        np.testing.assert_allclose(result.probability, [.7, .8])
        self.assertEqual(result.favorite_won.tolist(), [0, 0])


if __name__ == "__main__":
    unittest.main()
