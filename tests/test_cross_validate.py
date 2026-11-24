import unittest

import pandas as pd

from cross_validate import chronological_folds


class ChronologicalFoldsTests(unittest.TestCase):
    def test_each_fold_trains_only_on_earlier_dates(self):
        sample = pd.DataFrame({"event_date": ["2018-12-31", "2019-01-01", "2020-12-31",
                                              "2021-01-01", "2022-12-31", "2023-01-01"]})
        folds = list(chronological_folds(sample, 2019, 2023, 2))
        self.assertEqual([fold[:2] for fold in folds], [(2019, 2021), (2021, 2023)])
        for _, _, train, test in folds:
            self.assertLess(train.event_date.max(), test.event_date.min())
        self.assertEqual(folds[0][3].event_date.tolist(), ["2019-01-01", "2020-12-31"])
        self.assertEqual(folds[1][3].event_date.tolist(), ["2021-01-01", "2022-12-31"])


if __name__ == "__main__":
    unittest.main()
