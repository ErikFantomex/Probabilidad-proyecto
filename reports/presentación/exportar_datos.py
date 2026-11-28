"""Exporta las peleas con cuota de apertura a datos_mma.js para las diapositivas de Monte Carlo.

Uso (desde la raíz del proyecto, después de download_mma_data.py, mma_pipeline.py y monte_carlo.py):
    python "reports/presentación/exportar_datos.py"

Genera un archivo .js (no .json) para que index.html funcione abierto con doble clic, sin servidor.
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mma_pipeline import PROCESSED  # noqa: E402
from monte_carlo import TABLE, favorites, with_bands  # noqa: E402

OUT = Path(__file__).resolve().parent / "datos_mma.js"


def main():
    if not PROCESSED.exists():
        raise SystemExit("Falta data/processed/pre_fight_bouts.csv: ejecuta primero mma_pipeline.py")
    fights = with_bands(favorites(pd.read_csv(PROCESSED))).sort_values("event_date")
    rows = [[r.event_date, r.favorite, r.underdog, round(float(r.probability), 4), int(r.favorite_won)]
            for r in fights.itertuples()]
    summary = pd.read_csv(TABLE).to_dict(orient="records") if TABLE.exists() else []
    data = {"columns": ["fecha", "favorito", "rival", "probabilidad", "gano_favorito"],
            "fights": rows, "summary": summary,
            "first_date": rows[0][0], "last_date": rows[-1][0]}
    OUT.write_text("// Generado por exportar_datos.py — no editar a mano.\nwindow.MMA = "
                   + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"{len(rows):,} peleas → {OUT} ({OUT.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
