"""Local UFC matchup explorer."""
import json
from datetime import date

import joblib
import numpy as np
import pandas as pd
from flask import Flask, render_template, request

from mma_pipeline import FIGHTERS, METRICS, MODEL, PAIR_REPORT, match_features

app = Flask(__name__)
DIVISIONS = ["bantamweight", "featherweight", "flyweight", "heavyweight", "light heavyweight", "lightweight", "middleweight", "welterweight", "women's bantamweight", "women's flyweight", "women's strawweight"]


def current_profile(row):
    data = row.to_dict()
    days = (date.today() - date.fromisoformat(data["last_fight_date"])).days
    data["age"] = data["age"] + days / 365.25 if np.isfinite(data["age"]) else np.nan
    data["rest_days"] = days
    return data


@app.route("/", methods=["GET", "POST"])
def home():
    if not MODEL.exists() or not FIGHTERS.exists():
        return render_template("home.html", ready=False)
    bundle = joblib.load(MODEL)
    fighters = pd.read_csv(FIGHTERS).set_index("fighter_id", drop=False)
    choices = fighters[fighters.prior_fights >= 3].sort_values("name")[["fighter_id", "name", "prior_fights"]].to_dict("records")
    result, error = None, None
    selected = request.form.to_dict()
    if request.method == "POST":
        try:
            aid, bid = selected.get("fighter_a"), selected.get("fighter_b")
            division, rounds = selected.get("division"), int(selected.get("rounds", 3))
            if aid not in fighters.index or bid not in fighters.index or aid == bid:
                raise ValueError("Selecciona dos peleadores diferentes.")
            if division not in DIVISIONS or rounds not in (3, 5):
                raise ValueError("Selecciona una división y duración válidas.")
            a, b = current_profile(fighters.loc[aid]), current_profile(fighters.loc[bid])
            model = bundle["model"]
            title_bout = selected.get("title_bout") == "yes"
            forward = pd.DataFrame([match_features(a, b, division, rounds, title_bout)])
            reverse = pd.DataFrame([match_features(b, a, division, rounds, title_bout)])
            p = (model.predict_proba(forward)[0, 1] + 1 - model.predict_proba(reverse)[0, 1]) / 2
            pair = " × ".join(sorted((a["style"], b["style"])))
            pair_table = pd.read_csv(PAIR_REPORT)
            match = pair_table[pair_table.style_pair == pair]
            result = {"a": a, "b": b, "p_a": round(100*p, 1), "p_b": round(100*(1-p), 1),
                      "closeness": round(100*(1-2*abs(p-.5)), 1), "pair": pair,
                      "pair_stats": match.iloc[0].to_dict() if len(match) else None,
                      "source_date": bundle["source_last_date"]}
        except (ValueError, KeyError) as exc:
            error = str(exc)
    return render_template("home.html", ready=True, fighters=choices, divisions=DIVISIONS,
                           selected=selected, result=result, error=error)


@app.route("/analysis")
def analysis():
    if not METRICS.exists() or not PAIR_REPORT.exists():
        return render_template("analysis.html", ready=False)
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    pairs = pd.read_csv(PAIR_REPORT).query("fights >= 100").sort_values("fights", ascending=False).to_dict("records")
    return render_template("analysis.html", ready=True, metrics=metrics, pairs=pairs)


if __name__ == "__main__":
    app.run(debug=False)
