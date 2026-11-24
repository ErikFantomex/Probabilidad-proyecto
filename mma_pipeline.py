"""Reproducible UFC style analysis and strictly pre-fight prediction pipeline."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/raw/ufc_all_fights_wide.csv"
PROCESSED = ROOT / "data/processed/pre_fight_bouts.csv"
FIGHTERS = ROOT / "data/processed/fighters_latest.csv"
MODEL = ROOT / "models/mma_model.joblib"
REPORT = ROOT / "reports/analysis.md"
PAIR_REPORT = ROOT / "reports/style_matchups.csv"
METRICS = ROOT / "reports/metrics.json"

METRIC_FIELDS = ["sig_str_landed", "sig_str_att", "td_landed", "td_att", "sub_att", "ctrl_sec", "kd"]
BASE_FIELDS = ["age", "height_cm", "reach_cm", "prior_fights", "rest_days", "win_rate", "finish_rate", "slpm", "sapm", "str_acc", "td15", "td_att15", "td_def", "ctrl15", "sub15", "kd15"]
NUMERIC = [f"{side}_{field}" for side in "ab" for field in BASE_FIELDS] + [f"diff_{field}" for field in BASE_FIELDS] + ["scheduled_rounds", "is_title_bout"]
CATEGORICAL = ["division", "a_style", "b_style"]
FEATURES = NUMERIC + CATEGORICAL


def number(value):
    try:
        result = float(value)
        return result if np.isfinite(result) else np.nan
    except (ValueError, TypeError):
        return np.nan


def ratio(top, bottom):
    return top / bottom if bottom > 0 else np.nan


def new_history():
    return {"fights": 0, "wins": 0, "finishes": 0, "last_date": None, "seconds": 0.0,
            **{name: 0.0 for name in METRIC_FIELDS}, "opp_sig_landed": 0.0,
            "opp_td_landed": 0.0, "opp_td_att": 0.0}


def style(profile):
    """Behavioral label, based only on UFC fights completed before the bout."""
    if profile["prior_fights"] < 3 or not np.isfinite(profile["td_att15"]):
        return "Sin historial"
    if profile["sub15"] >= 1.5:
        return "Sometedor"
    if profile["td_att15"] >= 3.0 or profile["ctrl15"] >= 90.0:
        return "Luchador"
    if profile["slpm"] >= 4.0 and profile["td_att15"] < 2.0:
        return "Golpeador"
    return "Mixto"


def profile(history, bout_date, age=np.nan, height=np.nan, reach=np.nan):
    seconds = history["seconds"]
    minutes = seconds / 60
    per15 = seconds / 900
    last = history["last_date"]
    result = {
        "age": age, "height_cm": height, "reach_cm": reach,
        "prior_fights": history["fights"],
        "rest_days": (bout_date - last).days if last else np.nan,
        "win_rate": ratio(history["wins"], history["fights"]),
        "finish_rate": ratio(history["finishes"], history["fights"]),
        "slpm": ratio(history["sig_str_landed"], minutes),
        "sapm": ratio(history["opp_sig_landed"], minutes),
        "str_acc": ratio(history["sig_str_landed"], history["sig_str_att"]),
        "td15": ratio(history["td_landed"], per15),
        "td_att15": ratio(history["td_att"], per15),
        "td_def": 1 - ratio(history["opp_td_landed"], history["opp_td_att"])
        if history["opp_td_att"] else np.nan,
        "ctrl15": ratio(history["ctrl_sec"], per15),
        "sub15": ratio(history["sub_att"], per15),
        "kd15": ratio(history["kd"], per15),
    }
    result["style"] = style(result)
    return result


def match_features(a, b, division, rounds, title=False):
    data = {f"{side}_{key}": p[key] for side, p in (("a", a), ("b", b)) for key in BASE_FIELDS}
    for key in BASE_FIELDS:
        data[f"diff_{key}"] = a[key] - b[key]
    data.update(division=division, a_style=a["style"], b_style=b["style"],
                scheduled_rounds=rounds, is_title_bout=int(title))
    return data


def update(history, row, side, opponent, result, bout_date):
    history["fights"] += 1
    history["wins"] += int(result == "W")
    history["finishes"] += int(result == "W" and row["finish_type"] in ("ko_tko", "submission"))
    history["last_date"] = bout_date
    duration = number(row["fight_duration_sec"])
    if not np.isfinite(duration) or duration <= 0:
        return
    values = [number(row[f"{side}_tot_{key}"]) for key in METRIC_FIELDS]
    if not all(np.isfinite(value) for value in values):
        return
    history["seconds"] += duration
    for key, value in zip(METRIC_FIELDS, values):
        history[key] += value
    for key in ("sig_str_landed", "td_landed", "td_att"):
        value = number(row[f"{opponent}_tot_{key}"])
        if np.isfinite(value):
            history["opp_" + ("sig_landed" if key == "sig_str_landed" else key)] += value


def build_dataset(source=SOURCE):
    raw = pd.read_csv(source, low_memory=False)
    audit = {"source_rows": len(raw), "duplicate_fight_ids": int(raw.fight_id.duplicated().sum())}
    raw = raw.drop_duplicates("fight_id").sort_values(["event_date", "fight_id"])
    histories = defaultdict(new_history)
    names = {}
    recent = {}
    output = []
    for event_date, event in raw.groupby("event_date", sort=True):
        bout_date = date.fromisoformat(event_date)
        day_updates = []
        for _, row in event.iterrows():
            f1, f2 = str(row.f1_id), str(row.f2_id)
            if f1 == "nan" or f2 == "nan" or f1 == f2:
                continue
            names[f1], names[f2] = row.f1_name, row.f2_name
            recent[f1], recent[f2] = event_date, event_date
            p1 = profile(histories[f1], bout_date, number(row.f1_age), number(row.f1_height_cm), number(row.f1_reach_cm))
            p2 = profile(histories[f2], bout_date, number(row.f2_age), number(row.f2_height_cm), number(row.f2_reach_cm))
            swap = int(f1 > f2)  # Stable fighter-ID order; independent of winner listing.
            a, b = (p2, p1) if swap else (p1, p2)
            aid, bid = (f2, f1) if swap else (f1, f2)
            result = {"fight_id": row.fight_id, "event_date": event_date,
                      "event_name": row.event_name, "fighter_a_id": aid, "fighter_b_id": bid,
                      "fighter_a": names[aid], "fighter_b": names[bid],
                      "finish_type": row.finish_type, "result_f1": row.result_f1,
                      "result_f2": row.result_f2}
            result.update(match_features(a, b, row.bout_division, number(row.scheduled_rounds), row.is_title_bout is True))
            winner = number(row.winner)
            result["winner_a"] = int((winner == 2 and swap) or (winner == 1 and not swap)) if winner in (1, 2) else np.nan
            odd = number(row.f2_open_prob_novig if swap else row.f1_open_prob_novig)
            result["open_prob_a"] = odd if 0 < odd < 1 else np.nan
            result["underdog_won"] = int((result["winner_a"] == 1 and odd < .5) or (result["winner_a"] == 0 and odd > .5)) if np.isfinite(result["winner_a"]) and np.isfinite(odd) else np.nan
            output.append(result)
            day_updates.append((row, bout_date, f1, f2))
        # No result from this event is available to another bout on the same day.
        for row, bout_date, f1, f2 in day_updates:
            update(histories[f1], row, "f1", "f2", row.result_f1, bout_date)
            update(histories[f2], row, "f2", "f1", row.result_f2, bout_date)
    bouts = pd.DataFrame(output)
    latest = []
    for fighter_id, history in histories.items():
        last = history["last_date"]
        if not last:
            continue
        previous = raw.loc[(raw.f1_id == fighter_id) | (raw.f2_id == fighter_id)].iloc[-1]
        side = "f1" if previous.f1_id == fighter_id else "f2"
        p = profile(history, last, number(previous[f"{side}_age"]), number(previous[f"{side}_height_cm"]), number(previous[f"{side}_reach_cm"]))
        latest.append({"fighter_id": fighter_id, "name": names[fighter_id], "last_fight_date": last.isoformat(), **p})
    audit.update(clean_rows=len(bouts), decisive_rows=int(bouts.winner_a.notna().sum()),
                 first_fight_rows=int(((bouts.a_prior_fights == 0) | (bouts.b_prior_fights == 0)).sum()),
                 odds_rows=int(bouts.open_prob_a.notna().sum()), fighters=len(latest),
                 first_date=bouts.event_date.min(), last_date=bouts.event_date.max())
    return bouts, pd.DataFrame(latest), audit


def model_pipeline(estimator):
    numeric = Pipeline([("fill", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())])
    categories = Pipeline([("fill", SimpleImputer(strategy="most_frequent")),
                           ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return Pipeline([("prepare", ColumnTransformer([("num", numeric, NUMERIC), ("cat", categories, CATEGORICAL)])),
                     ("model", estimator)])


def scores(y, probability):
    return {"n": len(y), "accuracy": round(float(accuracy_score(y, probability >= .5)), 4),
            "brier": round(float(brier_score_loss(y, probability)), 4),
            "log_loss": round(float(log_loss(y, probability, labels=[0, 1])), 4),
            "auc": round(float(roc_auc_score(y, probability)), 4)}


def calibration(y, probability):
    """Fixed probability bins on a held-out period; no fitting on test data."""
    frame = pd.DataFrame({"actual": np.asarray(y), "predicted": probability})
    frame["bin"] = pd.cut(frame.predicted, bins=np.linspace(0, 1, 11), include_lowest=True)
    return [{"range": str(interval), "n": len(group),
             "mean_probability": round(float(group.predicted.mean()), 4),
             "observed_win_rate": round(float(group.actual.mean()), 4)}
            for interval, group in frame.groupby("bin", observed=True)]


def evaluate(bouts):
    sample = bouts[bouts.winner_a.notna()].copy()
    train = sample[sample.event_date < "2023-01-01"]
    validation = sample[(sample.event_date >= "2023-01-01") & (sample.event_date < "2025-01-01")]
    test = sample[sample.event_date >= "2025-01-01"]
    candidates = {
        "logistic": model_pipeline(LogisticRegression(max_iter=1500, C=.3)),
        "hist_gradient_boosting": model_pipeline(HistGradientBoostingClassifier(max_iter=180, learning_rate=.04, max_leaf_nodes=15, l2_regularization=5, random_state=42)),
    }
    validation_scores = {}
    for name, model in candidates.items():
        model.fit(train[FEATURES], train.winner_a.astype(int))
        validation_scores[name] = scores(validation.winner_a.astype(int), model.predict_proba(validation[FEATURES])[:, 1])
    selected = min(validation_scores, key=lambda name: validation_scores[name]["log_loss"])
    fitted = clone(candidates[selected]).fit(pd.concat([train, validation])[FEATURES], pd.concat([train, validation]).winner_a.astype(int))
    test_prob = fitted.predict_proba(test[FEATURES])[:, 1]
    test_scores = scores(test.winner_a.astype(int), test_prob)
    odds = test.open_prob_a.notna()
    market_scores = scores(test.loc[odds, "winner_a"].astype(int), test.loc[odds, "open_prob_a"].to_numpy())
    model_on_odds = scores(test.loc[odds, "winner_a"].astype(int), test_prob[odds.to_numpy()])
    final_model = clone(candidates[selected]).fit(sample[FEATURES], sample.winner_a.astype(int))
    return final_model, {"splits": {"train": len(train), "validation": len(validation), "test": len(test)},
                         "validation": validation_scores, "selected": selected,
                         "test": test_scores, "market_open_test": market_scores,
                         "model_on_market_subset": model_on_odds,
                         "calibration_test": calibration(test.winner_a.astype(int), test_prob)}


def wilson(successes, count):
    if not count:
        return (np.nan, np.nan)
    z = 1.96
    p = successes / count
    denominator = 1 + z*z/count
    center = (p + z*z/(2*count)) / denominator
    half = z * np.sqrt(p*(1-p)/count + z*z/(4*count*count)) / denominator
    return round(center-half, 4), round(center+half, 4)


def matchups(bouts):
    subset = bouts[(bouts.winner_a.notna()) & (bouts.a_style != "Sin historial") & (bouts.b_style != "Sin historial")].copy()
    subset["style_pair"] = subset.apply(lambda row: " × ".join(sorted((row.a_style, row.b_style))), axis=1)
    subset["is_finish"] = subset.finish_type.isin(["ko_tko", "submission"]).astype(int)
    rows = []
    for pair, group in subset.groupby("style_pair"):
        n = len(group)
        first_style, second_style = pair.split(" × ")
        first_wins = int(((group.a_style == first_style) & (group.winner_a == 1) | (group.b_style == first_style) & (group.winner_a == 0)).sum()) if first_style != second_style else np.nan
        finishes = int(group.is_finish.sum())
        odds_group = group[group.underdog_won.notna()]
        upset_n = len(odds_group)
        upsets = int(odds_group.underdog_won.sum())
        lower, upper = wilson(finishes, n)
        win_low, win_high = wilson(first_wins, n) if np.isfinite(first_wins) else (np.nan, np.nan)
        rows.append({"style_pair": pair, "fights": n, "finish_rate": round(finishes/n, 4),
                     "first_style_win_rate": round(first_wins/n, 4) if np.isfinite(first_wins) else np.nan,
                     "first_style_win_ci_low": win_low, "first_style_win_ci_high": win_high,
                     "finish_ci_low": lower, "finish_ci_high": upper,
                     "ko_rate": round(float((group.finish_type == "ko_tko").mean()), 4),
                     "submission_rate": round(float((group.finish_type == "submission").mean()), 4),
                     "odds_fights": upset_n, "underdog_win_rate": round(upsets/upset_n, 4) if upset_n else np.nan})
    return pd.DataFrame(rows).sort_values("fights", ascending=False)


def write_report(audit, metrics, pair):
    top = pair[pair.fights >= 100].sort_values("finish_rate", ascending=False)
    lines = ["# Análisis de estilos y predictibilidad UFC", "", "## Alcance y auditoría", "",
             f"Fuente: nlbair/ufc-data v0.1.1 (a9c6543), 2013–2026. Filas: {audit['source_rows']}; peleadores: {audit['fighters']}.",
             f"Combates decisivos: {audit['decisive_rows']}; con cuota inicial: {audit['odds_rows']}; IDs duplicados: {audit['duplicate_fight_ids']}.",
             "Empates y no contests permanecen en la historia, pero se excluyen del modelo binario.",
             "Los estilos son etiquetas de comportamiento previo: no equivalen al arte marcial declarado por el peleador.",
             "", "## Cruces de estilos", "", "Tasas descriptivas, sin ajuste causal. IC del 95% de Wilson para finalizaciones.", "",
             "| Cruce | Peleas | Victoria del primer estilo | IC 95% victoria | Finalización | IC 95% finalización | KO/TKO | Sumisión | Victoria del no favorito |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in top.itertuples():
        style_win = f"{row.first_style_win_rate:.1%}" if np.isfinite(row.first_style_win_rate) else "—"
        win_ci = f"{row.first_style_win_ci_low:.1%}–{row.first_style_win_ci_high:.1%}" if np.isfinite(row.first_style_win_ci_low) else "—"
        lines.append(f"| {row.style_pair} | {row.fights} | {style_win} | {win_ci} | {row.finish_rate:.1%} | {row.finish_ci_low:.1%}–{row.finish_ci_high:.1%} | {row.ko_rate:.1%} | {row.submission_rate:.1%} | {row.underdog_win_rate:.1%} |")
    lines += ["", "## Predicción cronológica", "",
              f"Entrenamiento: antes de 2023 ({metrics['splits']['train']}); selección: 2023–2024 ({metrics['splits']['validation']}); prueba: 2025–2026 ({metrics['splits']['test']}).",
              f"Modelo elegido por pérdida logarítmica de validación: **{metrics['selected']}**.", "",
              "| Prueba | Combates | Exactitud | Brier | Pérdida logarítmica | AUC |", "|---|---:|---:|---:|---:|---:|"]
    for label, key in [("Modelo", "test"), ("Modelo, peleas con cuotas", "model_on_market_subset"), ("Cuota inicial sin margen", "market_open_test")]:
        item = metrics[key]
        lines.append(f"| {label} | {item['n']} | {item['accuracy']:.1%} | {item['brier']:.4f} | {item['log_loss']:.4f} | {item['auc']:.4f} |")
    lines += ["", "### Calibración del modelo en prueba", "", "| Probabilidad estimada | Combates | Probabilidad media | Victorias observadas |", "|---|---:|---:|---:|"]
    for row in metrics["calibration_test"]:
        lines.append(f"| {row['range']} | {row['n']} | {row['mean_probability']:.1%} | {row['observed_win_rate']:.1%} |")
    lines += ["", "La frecuencia de victorias del no favorito cuantifica sorpresas respecto al mercado; Brier, pérdida logarítmica y calibración cuantifican incertidumbre predictiva. Una exactitud mayor que 50% no demuestra que las peleas sean fáciles de predecir.",
              "", "## Limitaciones", "", "- UFC solamente; los primeros combates UFC tienen poco historial observable.",
              "- Los umbrales de estilo son exploratorios y las categorías pueden cambiar con el tiempo.",
              "- Las asociaciones entre estilos no prueban causalidad; división, nivel del rival y época pueden influir.",
              "- La cuota inicial es una referencia externa, no una variable de entrada del modelo.",
              "- El último combate en la fuente es del 10 de octubre de 2026; la interfaz no actualiza resultados automáticamente.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    for path in (PROCESSED, FIGHTERS, MODEL, REPORT, PAIR_REPORT, METRICS):
        path.parent.mkdir(parents=True, exist_ok=True)
    bouts, fighters, audit = build_dataset(args.source)
    bouts.to_csv(PROCESSED, index=False)
    fighters.to_csv(FIGHTERS, index=False)
    pair = matchups(bouts)
    pair.to_csv(PAIR_REPORT, index=False)
    model, metrics = evaluate(bouts)
    joblib.dump({"model": model, "features": FEATURES, "source_last_date": audit["last_date"], "selected": metrics["selected"]}, MODEL)
    METRICS.write_text(json.dumps({"audit": audit, **metrics}, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(audit, metrics, pair)
    print(json.dumps({"audit": audit, "selected": metrics["selected"], "test": metrics["test"], "market": metrics["market_open_test"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
