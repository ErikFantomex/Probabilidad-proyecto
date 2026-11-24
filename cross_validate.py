"""Expanding-window evaluation of fixed MMA models on successive UFC seasons."""

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from mma_pipeline import FEATURES, PROCESSED, ROOT, model_pipeline, scores


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


def evaluate_folds(sample, start_year=2019, end_year=2027, fold_years=2):
    rows = []
    for year, stop, train, test in chronological_folds(sample, start_year, end_year, fold_years):
        if train.winner_a.nunique() < 2 or test.winner_a.nunique() < 2:
            continue
        common = {"test_period": f"{year}-{stop - 1}", "train_n": len(train),
                  "test_n": len(test), "train_last_date": train.event_date.max(),
                  "test_first_date": test.event_date.min(), "test_last_date": test.event_date.max()}
        odds = test.open_prob_a.notna()
        if odds.sum() and test.loc[odds, "winner_a"].nunique() == 2:
            rows.append({**common, "model": "market_open", "subset": "with_odds",
                         **scores(test.loc[odds, "winner_a"].astype(int),
                                  test.loc[odds, "open_prob_a"].to_numpy())})
        for name, model in candidates().items():
            model.fit(train[FEATURES], train.winner_a.astype(int))
            predicted = model.predict_proba(test[FEATURES])[:, 1]
            rows.append({**common, "model": name, "subset": "all",
                         **scores(test.winner_a.astype(int), predicted)})
            if odds.sum() and test.loc[odds, "winner_a"].nunique() == 2:
                rows.append({**common, "model": name, "subset": "with_odds",
                             **scores(test.loc[odds, "winner_a"].astype(int),
                                      predicted[odds.to_numpy()])})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2027, help="Año final exclusivo")
    parser.add_argument("--fold-years", type=int, default=2)
    parser.add_argument("--input", type=Path, default=PROCESSED)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/cross_validation.csv")
    args = parser.parse_args()
    sample = pd.read_csv(args.input)
    sample = sample[sample.winner_a.notna()].sort_values("event_date")
    result = evaluate_folds(sample, args.start_year, args.end_year, args.fold_years)
    if result.empty:
        parser.error("No hay ventanas con suficientes combates decisivos en ese rango")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result[["test_period", "model", "subset", "train_n", "n", "brier", "log_loss", "auc"]].to_string(index=False))
    print(f"\nGuardado: {args.output}")


if __name__ == "__main__":
    main()
