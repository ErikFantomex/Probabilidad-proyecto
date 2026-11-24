"""Responsive Streamlit interface for the UFC style and prediction study."""

import json

import joblib
import pandas as pd
import streamlit as st

from mma_pipeline import FIGHTERS, METRICS, MODEL, PAIR_REPORT, REPORT, SPECIAL_REPORT
from mma_service import DIVISIONS, compare

st.set_page_config(page_title="MMA Probabilidad", page_icon="🥊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .block-container {max-width: 1200px; padding-top: 2rem; padding-bottom: 3rem;}
  .hero {padding: 1.4rem 0 1.6rem; border-bottom: 1px solid #31434a; margin-bottom: 1.5rem;}
  .hero .eyebrow {font-size: .8rem; letter-spacing: .18em; color: #69d7c4; font-weight: 700;}
  .hero h1 {font-size: clamp(2rem, 5vw, 3.6rem); line-height: 1.08; margin: .5rem 0;}
  .hero p {max-width: 720px; color: #bdcbd0; font-size: 1.05rem;}
  .subtle {color: #adbdc4; font-size: .9rem;}
  @media (max-width: 640px) {.block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1rem;} .hero {padding-top: .4rem;}}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Cargando modelo...")
def load_model(path):
    return joblib.load(path)


@st.cache_data(show_spinner="Cargando datos del estudio...")
def load_tables(fighters_path, pairs_path, metrics_path, specialist_path):
    fighters = pd.read_csv(fighters_path).set_index("fighter_id", drop=False)
    pairs = pd.read_csv(pairs_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return fighters, pairs, metrics, pd.read_csv(specialist_path)


def percent(value):
    return f"{value:.1%}" if pd.notna(value) else "—"


def value(value, digits=2):
    return f"{value:,.{digits}f}" if pd.notna(value) else "—"


def display_comparison(result):
    st.subheader("Probabilidad estimada")
    left, right = st.columns(2, gap="large", border=True, wrap=True)
    with left:
        st.caption(result["a"]["style"])
        st.metric(result["a"]["name"], percent(result["probability_a"]))
        st.progress(result["probability_a"], text="Probabilidad del peleador A")
    with right:
        st.caption(result["b"]["style"])
        st.metric(result["b"]["name"], percent(result["probability_b"]))
        st.progress(result["probability_b"], text="Probabilidad del peleador B")
    st.caption(f"Cercanía al 50/50: {percent(result['balance'])}. Esta medida describe el equilibrio de la predicción; no es un intervalo de confianza.")
    history_tab, styles_tab = st.tabs(["Antecedentes", "Cruce de estilos"])
    with history_tab:
        a, b = result["a"], result["b"]
        frame = pd.DataFrame({
            "Indicador": ["Peleas UFC previas", "Golpes significativos por minuto", "Golpes recibidos por minuto",
                          "Intentos de derribo por 15 min", "Control en segundos por 15 min",
                          "Intentos de sumisión por 15 min", "Días desde última pelea"],
            a["name"]: [str(int(a["prior_fights"])), value(a["slpm"]), value(a["sapm"]),
                         value(a["td_att15"]), value(a["ctrl15"], 0), value(a["sub15"]), str(int(a["rest_days"]))],
            b["name"]: [str(int(b["prior_fights"])), value(b["slpm"]), value(b["sapm"]),
                         value(b["td_att15"]), value(b["ctrl15"], 0), value(b["sub15"]), str(int(b["rest_days"]))],
        })
        st.dataframe(frame, hide_index=True, width="stretch")
    with styles_tab:
        st.markdown(f"**{result['pair_name']}**")
        pair = result["pair_stats"]
        if pair:
            st.metric("Finalizaciones en este cruce", percent(pair["finish_rate"]), help=f"{int(pair['fights'])} combates históricos")
            st.caption(f"IC descriptivo del 95%: {percent(pair['finish_ci_low'])}–{percent(pair['finish_ci_high'])}. Incluye KO/TKO y sumisiones.")
            if pd.notna(pair["first_style_win_rate"]):
                first_style = result["pair_name"].split(" × ")[0]
                st.write(f"{first_style} ganó {percent(pair['first_style_win_rate'])} de estos cruces.")
        else:
            st.info("Este cruce no tiene antecedentes suficientes con estilos clasificados.")
        if result.get("specialist_stats"):
            detail = result["specialist_stats"]
            st.markdown(f"**{detail['style_pair']}**")
            st.write(f"{detail['fights']} peleas históricas · KO/TKO {percent(detail['ko_rate'])} · Sumisión {percent(detail['submission_rate'])}")
            if pd.notna(detail["first_style_win_rate"]):
                st.caption(f"Victorias del primer perfil: {percent(detail['first_style_win_rate'])} (IC 95% {percent(detail['first_style_win_ci_low'])}–{percent(detail['first_style_win_ci_high'])}).")
        st.caption("Las tasas son descriptivas y no atribuyen causalidad a un estilo.")
    st.caption(f"Datos hasta {result['source_date']}. El modelo no conoce lesiones, preparación ni cambios recientes de equipo.")


def display_results(metrics, pairs, specialists):
    st.subheader("¿Qué muestran las peleas históricas?")
    cards = st.columns(3, gap="medium", border=True, wrap=True)
    cards[0].metric("Combates registrados", f"{metrics['audit']['source_rows']:,}")
    cards[1].metric("Combates decisivos", f"{metrics['audit']['decisive_rows']:,}")
    cards[2].metric("Peleas de prueba · 2025–2026", f"{metrics['test']['n']:,}")

    st.markdown("### Predicción fuera de muestra")
    same = metrics["model_on_market_subset"]
    market = metrics["market_open_test"]
    comparison = pd.DataFrame({
        "Método": ["Modelo de historiales", "Cuotas iniciales sin margen"],
        "Combates": [same["n"], market["n"]],
        "Exactitud (%)": [100 * same["accuracy"], 100 * market["accuracy"]],
        "Brier ↓": [same["brier"], market["brier"]],
        "Pérdida logarítmica ↓": [same["log_loss"], market["log_loss"]],
        "AUC": [same["auc"], market["auc"]],
    })
    st.dataframe(comparison, hide_index=True, width="stretch", column_config={"Exactitud (%)": st.column_config.NumberColumn(format="%.1f%%")})
    st.caption("Comparación sobre los mismos combates con cuotas disponibles. Brier y pérdida logarítmica: menor es mejor.")

    st.markdown("### Calibración del modelo")
    calibration = pd.DataFrame(metrics["calibration_test"])
    chart = calibration.set_index("mean_probability")[["observed_win_rate"]].rename(columns={"observed_win_rate": "Victorias observadas"}) * 100
    chart.index = chart.index * 100
    chart["Calibración ideal"] = chart.index
    st.line_chart(chart, x_label="Probabilidad estimada (%)", y_label="Frecuencia de victoria (%)", width="stretch")
    st.caption("Los extremos tienen pocas peleas; consulta el número de observaciones por intervalo en la tabla.")
    calibration_table = calibration.rename(columns={"range": "Intervalo", "n": "Peleas", "mean_probability": "Probabilidad media", "observed_win_rate": "Victorias observadas"})
    for column in ("Probabilidad media", "Victorias observadas"):
        calibration_table[column] = calibration_table[column].map(percent)
    st.dataframe(calibration_table, hide_index=True, width="stretch")

    st.markdown("### Cruces de estilos")
    view = st.radio("Agrupar combates por", ["Estilo general", "Especialidad"], horizontal=True)
    if view == "Especialidad":
        st.caption("Grappler reúne a luchadores y sometedores. Golpeador KO requiere al menos dos victorias previas por KO/TKO y al menos la mitad de sus victorias por esa vía.")
    common = (specialists if view == "Especialidad" else pairs).sort_values("fights", ascending=False)
    chart_data = (100 * common.set_index("style_pair")[["finish_rate", "ko_rate", "submission_rate"]]).rename(
        columns={"finish_rate": "Finalización (%)", "ko_rate": "KO/TKO (%)", "submission_rate": "Sumisión (%)"})
    st.bar_chart(chart_data, horizontal=True, width="stretch", stack=False)
    table = common[["style_pair", "fights", "first_style_win_rate", "first_style_win_ci_low", "first_style_win_ci_high",
                    "finish_rate", "finish_ci_low", "finish_ci_high", "underdog_win_rate"]].rename(columns={
        "style_pair": "Cruce", "fights": "Peleas", "first_style_win_rate": "Victoria del primer estilo",
        "first_style_win_ci_low": "Victoria IC inferior", "first_style_win_ci_high": "Victoria IC superior",
        "finish_rate": "Finalización", "finish_ci_low": "Finalización IC inferior",
        "finish_ci_high": "Finalización IC superior", "underdog_win_rate": "Victoria del no favorito"})
    for column in table.columns:
        if column not in ("Cruce", "Peleas"):
            table[column] = table[column].map(percent)
    st.dataframe(table, hide_index=True, width="stretch")
    st.caption("Los intervalos son de Wilson al 95%. Los cruces no prueban que el estilo cause el resultado.")
    if REPORT.exists():
        st.download_button("Descargar informe completo", REPORT.read_text(encoding="utf-8"),
                           file_name="analisis_mma.md", mime="text/markdown", width="stretch")


st.markdown("""<section class="hero"><div class="eyebrow">MMA · DATOS · INCERTIDUMBRE</div>
<h1>Antes de la campana, ¿qué podemos saber?</h1>
<p>Explora enfrentamientos UFC y observa cómo cambian las probabilidades y los resultados entre estilos de pelea.</p></section>""", unsafe_allow_html=True)

missing = [path for path in (MODEL, FIGHTERS, PAIR_REPORT, METRICS, SPECIAL_REPORT) if not path.exists()]
if missing:
    st.error("Faltan datos del estudio. Ejecuta `python download_mma_data.py` y `python mma_pipeline.py` antes de abrir la aplicación.")
    st.stop()

bundle = load_model(MODEL)
fighters, pairs, metrics, specialists = load_tables(FIGHTERS, PAIR_REPORT, METRICS, SPECIAL_REPORT)
eligible = fighters[fighters.prior_fights >= 3].sort_values("name")
labels = {fighter_id: f"{row['name']} · {int(row['prior_fights'])} peleas" for fighter_id, row in eligible.iterrows()}

compare_tab, results_tab, method_tab = st.tabs(["🥊 Simular combate", "📊 Resultados", "📖 Método y datos"])
with compare_tab:
    st.write("Elige dos peleadores y las condiciones del enfrentamiento. La estimación usa sus antecedentes UFC.")
    with st.form("matchup"):
        left, right = st.columns(2, gap="large", wrap=True)
        fighter_a_id = left.selectbox("Peleador A", options=list(labels), index=None, placeholder="Selecciona un peleador", format_func=lambda x: labels[x])
        fighter_b_id = right.selectbox("Peleador B", options=list(labels), index=None, placeholder="Selecciona un peleador", format_func=lambda x: labels[x])
        left, right = st.columns(2, gap="large", wrap=True)
        division = left.selectbox("División", DIVISIONS, index=None, placeholder="Selecciona una división", format_func=lambda x: x.title())
        rounds = right.selectbox("Duración", [3, 5], format_func=lambda x: f"{x} asaltos")
        title_bout = st.checkbox("Pelea por título")
        submitted = st.form_submit_button("Calcular enfrentamiento", type="primary", width="stretch")
    if submitted:
        try:
            st.session_state["matchup_result"] = compare(bundle, fighters, pairs, fighter_a_id, fighter_b_id, division, rounds, title_bout, specialists=specialists)
        except ValueError as exc:
            st.session_state.pop("matchup_result", None)
            st.warning(str(exc))
    if "matchup_result" in st.session_state:
        display_comparison(st.session_state["matchup_result"])

with results_tab:
    display_results(metrics, pairs, specialists)

with method_tab:
    st.subheader("Cómo se construyó el estudio")
    st.markdown("""
1. Cada pelea conserva los IDs de ambos atletas. Se calculan estadísticas con combates de **fechas anteriores**; ninguna acción del combate que se predice entra en sus variables.
2. Los perfiles `Golpeador`, `Luchador`, `Sometedor` y `Mixto` se asignan mediante umbrales de golpes, derribos, control y sumisiones. Con menos de tres peleas UFC se usa `Sin historial`.
3. Se entrenó con peleas anteriores a 2023, se seleccionó el modelo con 2023–2024 y se probó con 2025–2026. La referencia de cuotas nunca fue una entrada del modelo.
4. La aplicación usa el modelo final reajustado con todos los combates decisivos de la fuente.
""")
    st.info("Una probabilidad no garantiza el ganador. Las categorías de estilo son aproximaciones descriptivas; UFC no cubre todas las MMA.")
    st.markdown("**Fuente:** [UFC Data v0.1.1, Bair (2026)](https://github.com/nlbair/ufc-data), publicada bajo CC BY 4.0. Se acredita también a UFC Stats, MMA Decisions, BestFightOdds y los archivos de rankings usados por esa base.")
    st.caption(f"Ventana de datos: {metrics['audit']['first_date']} a {metrics['audit']['last_date']}. No hay actualización automática de combates posteriores.")
