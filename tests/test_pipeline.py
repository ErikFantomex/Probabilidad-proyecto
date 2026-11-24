import tempfile
import unittest
from pathlib import Path

import pandas as pd

from mma_pipeline import build_dataset, new_history, profile


class PipelineTests(unittest.TestCase):
    def test_same_day_results_do_not_enter_pre_fight_features(self):
        def bout(fid, day, f1, f2, winner):
            data = {"fight_id": fid, "event_date": day, "f1_id": f1, "f2_id": f2,
                    "f1_name": f1, "f2_name": f2, "f1_age": 30, "f2_age": 30,
                    "f1_height_cm": 180, "f2_height_cm": 180,
                    "f1_reach_cm": 180, "f2_reach_cm": 180,
                    "event_name": "Test", "bout_division": "lightweight",
                    "scheduled_rounds": 3, "is_title_bout": False,
                    "winner": winner, "result_f1": "W" if winner == 1 else "L",
                    "result_f2": "L" if winner == 1 else "W",
                    "finish_type": "decision", "fight_duration_sec": 900,
                    "f1_open_prob_novig": .5, "f2_open_prob_novig": .5}
            for side in ("f1", "f2"):
                for field in ("sig_str_landed", "sig_str_att", "td_landed", "td_att", "sub_att", "ctrl_sec", "kd"):
                    data[f"{side}_tot_{field}"] = 10
            return data
        data = [bout("f1", "2022-01-01", "a", "b", 1),
                bout("f2", "2022-01-01", "a", "c", 2),
                bout("f3", "2022-02-01", "a", "d", 2)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fights.csv"
            pd.DataFrame(data).to_csv(path, index=False)
            fights, _, audit = build_dataset(path)
        self.assertEqual(audit["clean_rows"], 3)
        for fid in ("f1", "f2"):
            row = fights.set_index("fight_id").loc[fid]
            self.assertEqual(row["a_prior_fights"], 0)
        self.assertEqual(fights.set_index("fight_id").loc["f3", "a_prior_fights"], 2)
        self.assertEqual(fights.set_index("fight_id").loc["f2", "winner_a"], 0)

    def test_style_needs_prior_evidence(self):
        self.assertEqual(profile(new_history(), pd.Timestamp("2022-01-01").date())["style"], "Sin historial")


if __name__ == "__main__":
    unittest.main()
