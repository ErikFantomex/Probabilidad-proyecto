"""Expanding-window evaluation of fixed MMA models on successive UFC seasons."""

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from mma_pipeline import FEATURES, PROCESSED, ROOT, model_pipeline, pair_labels, scores


def chronological_folds(sample, start_year, end_year, fold_years):
    """Yield train/test windows; end_year is exclusive and training only uses the past."""
    if fold_years < 1 or end_year <= start_year:
        raise ValueError("Se requiere --fold-years >= 1 y --end-year > --start-year")
    for year in range(start_year, end_year, fold_years):
        stop = min(year + fold_years, end_year)
        train = sample[sample.event_date < f"{year}-01-01"]
        test = sample[(sample.event_date >= f"{year}-01-01") &
                      (sample.event_date < f"{stop}-01-01")]
        if len(train) and len(test):
            yield year, stop, train, test


def candidates():
    return {
        "logistic": model_pipeline(LogisticRegression(max_iter=1500, C=.3)),
        "hist_gradient_boosting": model_pipeline(HistGradientBoostingClassifier(
            max_iter=180, learning_rate=.04, max_leaf_nodes=15,
            l2_regularization=5, random_state=42)),
    }


def evaluate_folds(sample, start_year=2019, end_year=2027, fold_years=2, group_by=None):
    rows = []
    for year, stop, train, test in chronological_folds(sample, start_year, end_year, fold_years):
        if train.winner_a.nunique() < 2 or test.winner_a.nunique() < 2:
            continue
        common = {"test_period": f"{year}-{stop - 1}", "train_n": len(train),
                  "test_n": len(test), "train_last_date": train.event_date.max(),
                  "test_first_date": test.event_date.min(), "test_last_date": test.event_date.max()}
        predictions = test[["winner_a", "open_prob_a"]].copy()
        for name, model in candidates().items():
            model.fit(train[FEATURES], train.winner_a.astype(int))
            predictions[name] = model.predict_proba(test[FEATURES])[:, 1]
        groups = predictions.groupby(pair_labels(test, group_by)) if group_by else [(None, predictions)]
        for pair, group in groups:
            meta = {**common, "style_pair": pair} if group_by else common
            for subset, sample_rows in [("all", group), ("with_odds", group.dropna(subset=["open_prob_a"]))]:
                if sample_rows.empty:
                    continue
                for name in predictions.columns.drop("winner_a"):
                    if name == "open_prob_a" and subset == "all":
                        continue
                    rows.append({**meta, "model": "market_open" if name == "open_prob_a" else name,
                                 "subset": subset, **scores(sample_rows.winner_a, sample_rows[name])})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2027, help="Año final exclusivo")
    parser.add_argument("--fold-years", type=int, default=2)
    parser.add_argument("--input", type=Path, default=PROCESSED)
    parser.add_argument("--group-by", choices=["style", "specialist"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sample = pd.read_csv(args.input)
    sample = sample[sample.winner_a.notna()].sort_values("event_date")
    if args.group_by and f"a_{args.group_by}" not in sample:
        parser.error("Regenera los perfiles con python mma_pipeline.py")
    suffix = f"_{args.group_by}" if args.group_by else ""
    if args.output is None:
        args.output = ROOT / f"reports/cross_validation{suffix}.csv"
    result = evaluate_folds(sample, args.start_year, args.end_year, args.fold_years, args.group_by)
    if result.empty:
        parser.error("No hay ventanas con suficientes combates decisivos en ese rango")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    keys = ["test_period", "style_pair"] if args.group_by else ["test_period"]
    print(result[keys + ["model", "subset", "train_n", "n", "brier", "log_loss", "auc"]].to_string(index=False))
    print(f"\nGuardado: {args.output}")


if __name__ == "__main__":
    main()
