"""Pure presentation-facing helpers for the UFC research artifacts."""

from datetime import date

import numpy as np
import pandas as pd

from mma_pipeline import match_features

DIVISIONS = (
    "flyweight", "bantamweight", "featherweight", "lightweight", "welterweight",
    "middleweight", "light heavyweight", "heavyweight", "women's strawweight",
    "women's flyweight", "women's bantamweight",
)


def current_profile(row, as_of=None):
    """Advance age and rest days from the last fight to the comparison date."""
    as_of = as_of or date.today()
    profile = row.to_dict()
    days = (as_of - date.fromisoformat(profile["last_fight_date"])).days
    profile["age"] = profile["age"] + days / 365.25 if np.isfinite(profile["age"]) else np.nan
    profile["rest_days"] = days
    return profile


def compare(bundle, fighters, pairs, fighter_a_id, fighter_b_id, division, rounds, title_bout=False, as_of=None, specialists=None):
    """Estimate a matchup while averaging both fighter orderings."""
    if fighter_a_id == fighter_b_id or fighter_a_id not in fighters.index or fighter_b_id not in fighters.index:
        raise ValueError("Selecciona dos peleadores distintos.")
    if division not in DIVISIONS or rounds not in (3, 5):
        raise ValueError("Selecciona una división y duración válidas.")
    a = current_profile(fighters.loc[fighter_a_id], as_of)
    b = current_profile(fighters.loc[fighter_b_id], as_of)
    if a["prior_fights"] < 3 or b["prior_fights"] < 3:
        raise ValueError("Cada peleador necesita al menos tres combates UFC registrados.")
    model = bundle["model"]
    forward = pd.DataFrame([match_features(a, b, division, rounds, title_bout)])
    reverse = pd.DataFrame([match_features(b, a, division, rounds, title_bout)])
    probability = (model.predict_proba(forward)[0, 1] + 1 - model.predict_proba(reverse)[0, 1]) / 2
    pair_name = " × ".join(sorted((a["style"], b["style"])))
    matching = pairs[pairs.style_pair == pair_name]
    specialist_stats = None
    if specialists is not None and "specialist" in a and "specialist" in b:
        key = " × ".join(sorted((a["specialist"], b["specialist"])))
        detail = specialists[specialists.style_pair == key]
        if not detail.empty:
            specialist_stats = detail.iloc[0].to_dict()
    return {
        "a": a, "b": b, "probability_a": float(probability),
        "probability_b": float(1 - probability), "balance": float(1 - 2 * abs(probability - .5)),
        "pair_name": pair_name, "pair_stats": matching.iloc[0].to_dict() if len(matching) else None,
        "specialist_stats": specialist_stats,
        "source_date": bundle["source_last_date"],
    }
