"""Monte Carlo: ¿las cuotas de apertura describen bien la probabilidad de sorpresa?

1. Una pelea: se repite Steveson–Sharaf muchas veces con la probabilidad del mercado.
2. Muchas peleas: si el mercado estuviera bien calibrado, cada favorito ganaría con su
   probabilidad implícita. Se simulan miles de "historias alternativas" de la UFC bajo esa
   hipótesis y se compara cuántas victorias de favoritos hubo de verdad.
"""

import argparse

import numpy as np
import pandas as pd

from mma_pipeline import PROCESSED, ROOT

BANDS = [.5, .6, .7, .8, 1.0]
BAND_LABELS = ["50–60 %", "60–70 %", "70–80 %", "80 % o más"]
REPORT = ROOT / "reports/monte_carlo.md"
TABLE = ROOT / "reports/monte_carlo_favorites.csv"


def favorites(bouts):
    """Una fila por pelea decisiva con cuota: probabilidad del favorito y si ganó."""
    rows = bouts[bouts.winner_a.notna() & bouts.open_prob_a.notna() & bouts.open_prob_a.ne(.5)]
    a_favored = rows.open_prob_a > .5
    return pd.DataFrame({
        "event_date": rows.event_date,
        "favorite": rows.fighter_a.where(a_favored, rows.fighter_b),
        "underdog": rows.fighter_b.where(a_favored, rows.fighter_a),
        "probability": rows.open_prob_a.where(a_favored, 1 - rows.open_prob_a),
        "favorite_won": rows.winner_a.where(a_favored, 1 - rows.winner_a).astype(int),
    })


def simulate_fight(probability, simulations, rng):
    """Repite una pelea; devuelve la frecuencia de sorpresas y su error estándar."""
    upsets = rng.random(simulations) >= probability
    rate = upsets.mean()
    return rate, np.sqrt(rate * (1 - rate) / simulations)


def simulate_wins(probabilities, simulations, rng, chunk=500):
    """Victorias totales de favoritos en cada historia simulada bajo calibración perfecta."""
    probabilities = np.asarray(probabilities, dtype=float)
    totals = np.empty(simulations, dtype=np.int64)
    for start in range(0, simulations, chunk):
        size = min(chunk, simulations - start)
        totals[start:start + size] = (rng.random((size, len(probabilities))) < probabilities).sum(axis=1)
    return totals


def calibration_test(probabilities, observed_wins, simulations, rng):
    simulated = simulate_wins(probabilities, simulations, rng)
    # Valor p bilateral con corrección +1 para no reportar nunca exactamente cero.
    lower = (np.sum(simulated <= observed_wins) + 1) / (simulations + 1)
    upper = (np.sum(simulated >= observed_wins) + 1) / (simulations + 1)
    low, high = np.percentile(simulated, [2.5, 97.5])
    return {"expected_wins": float(simulated.mean()), "range_low": float(low), "range_high": float(high),
            "p_value": float(min(1.0, 2 * min(lower, upper)))}


def run(bouts, simulations=20_000, seed=42):
    rng = np.random.default_rng(seed)
    fights = favorites(bouts)
    fights["band"] = pd.cut(fights.probability, BANDS, labels=BAND_LABELS, include_lowest=True)
    rows = []
    for band, group in [*fights.groupby("band", observed=True), ("Todas", fights)]:
        test = calibration_test(group.probability, group.favorite_won.sum(), simulations, rng)
        rows.append({"band": str(band), "fights": len(group),
                     "mean_market_probability": round(group.probability.mean(), 4),
                     "observed_favorite_wins": int(group.favorite_won.sum()),
                     "observed_win_rate": round(group.favorite_won.mean(), 4),
                     "expected_wins": round(test["expected_wins"], 1),
                     "simulated_95_low": int(test["range_low"]), "simulated_95_high": int(test["range_high"]),
                     "p_value": round(test["p_value"], 4)})
    table = pd.DataFrame(rows)

    example = fights[fights.favorite.str.contains("Steveson") & fights.underdog.str.contains("Sharaf")]
    probability = float(example.probability.iloc[0]) if len(example) else .904
    upset_rate, error = simulate_fight(probability, simulations * 5, rng)
    return table, {"probability": probability, "simulations": simulations * 5,
                   "upset_rate": upset_rate, "standard_error": error}


def write_report(table, single, simulations, seed):
    lines = ["# Monte Carlo: sorpresas frente a la cuota de apertura", "",
             f"Simulaciones por grupo: {simulations:,}; semilla: {seed}. Fuente: `data/processed/pre_fight_bouts.csv` "
             "(peleas decisivas con cuota inicial sin margen; se excluyen las cuotas exactas de 50 %).", "",
             "## 1. Una pelea: Steveson frente a Sharaf", "",
             f"El mercado daba a Steveson {single['probability']:.1%}. Al repetir la pelea {single['simulations']:,} veces "
             f"con esa probabilidad, Sharaf gana en {single['upset_rate']:.2%} de los casos "
             f"(error estándar Monte Carlo ±{single['standard_error']:.2%}). Aproximadamente una de cada "
             f"{1 / single['upset_rate']:.0f} peleas así termina en sorpresa: el KO de Sharaf es raro, pero no extraordinario.", "",
             "## 2. Muchas peleas: ¿están bien calibradas las cuotas?", "",
             "Hipótesis nula: cada favorito gana con su probabilidad implícita. En cada simulación se lanza una "
             "\"moneda cargada\" por pelea y se cuentan las victorias de favoritos. El rango del 95 % muestra qué sería "
             "normal si el mercado acertara; el valor p indica qué tan raro es lo observado bajo esa hipótesis.", "",
             "| Probabilidad del favorito | Peleas | Prob. media del mercado | Victorias observadas | Esperadas | Rango simulado 95 % | Valor p |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for row in table.itertuples():
        lines.append(f"| {row.band} | {row.fights} | {row.mean_market_probability:.1%} | "
                     f"{row.observed_favorite_wins} ({row.observed_win_rate:.1%}) | {row.expected_wins:.0f} | "
                     f"{row.simulated_95_low}–{row.simulated_95_high} | {row.p_value:.4f} |")
    lines += ["", "## Lectura", "",
              "- Si las victorias observadas caen dentro del rango simulado, los datos son compatibles con un mercado calibrado en ese grupo.",
              "- Si caen por encima, los favoritos ganaron más de lo que sugería la cuota (el mercado les daba poco); por debajo, lo contrario.",
              "- Se hacen varias comparaciones a la vez; conviene leer valores p cercanos a 0.05 con cautela.",
              "- La cuota de apertura puede moverse antes de la pelea; aquí no se usa la cuota de cierre.", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not PROCESSED.exists():
        raise SystemExit("Falta data/processed/pre_fight_bouts.csv: ejecuta primero mma_pipeline.py")
    table, single = run(pd.read_csv(PROCESSED), args.simulations, args.seed)
    table.to_csv(TABLE, index=False)
    write_report(table, single, args.simulations, args.seed)
    print(table.to_string(index=False))
    print(f"\nSteveson–Sharaf: sorpresa en {single['upset_rate']:.2%} de {single['simulations']:,} simulaciones")
    print(f"Informe: {REPORT}")


if __name__ == "__main__":
    main()
