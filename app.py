"""Responsive Streamlit interface for the UFC style and prediction study."""

import json

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st

from mma_pipeline import FIGHTERS, METRICS, MODEL, PAIR_REPORT, PROCESSED, REPORT, SPECIAL_REPORT
from mma_service import DIVISIONS, compare
from monte_carlo import BAND_LABELS, favorites, fight_outcomes, p_value, running_rate, simulate_wins, with_bands

FAVORITE_COLOR, UPSET_COLOR = "#69D7C4", "#F2777A"
PRESETS = {"Gable Steveson vs. Sean Sharaf · 2026": ("Steveson", "Sharaf"),
           "Ilia Topuria vs. Justin Gaethje · 2026": ("Topuria", "Gaethje"),
           "Ilia Topuria vs. Charles Oliveira · 2025": ("Topuria", "Oliveira")}
CUSTOM = "Probabilidad personalizada"

st.set_page_config(page_title="MMA Probabilidad", page_icon="🥊", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  .block-container {max-width: 1200px; padding-top: 2rem; padding-bottom: 3rem;}
  .hero {padding: 1.4rem 0 1.6rem; border-bottom: 1px solid #31434a; margin-bottom: 1.5rem;}
  .hero .eyebrow {font-size: .8rem; letter-spacing: .18em; color: #69d7c4; font-weight: 700;}
  .hero h1 {font-size: clamp(2rem, 5vw, 3.6rem); line-height: 1.08; margin: .5rem 0;}
  .hero p {max-width: 720px; color: #bdcbd0; font-size: 1.05rem;}
  .subtle {color: #adbdc4; font-size: .9rem;}
  [class*="st-key-mc_"] [data-testid="stMetricValue"] {font-size: clamp(1.15rem, 2vw, 1.55rem);}
  [class*="st-key-mc_"] [data-testid="stMetricValue"] > div {overflow: visible; white-space: nowrap;}
  [class*="st-key-mc_"] [data-testid="stMetricLabel"] p {font-size: .82rem; white-space: normal;}
  .coins {display: flex; flex-wrap: wrap; gap: 4px; margin: .4rem 0 .6rem;}
  .coins span {width: 14px; height: 14px; border-radius: 3px; display: inline-block;}
  .legend span {display: inline-block; width: 11px; height: 11px; border-radius: 2px; margin: 0 .3rem 0 .8rem; vertical-align: -1px;}
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


@st.cache_data(show_spinner="Cargando cuotas históricas...")
def load_favorites(path):
    return with_bands(favorites(pd.read_csv(path)))


@st.cache_data(show_spinner="Simulando historias alternativas de la UFC...")
def simulate_history(probabilities, simulations, seed):
    return simulate_wins(probabilities, simulations, np.random.default_rng(seed))


def next_seed(key):
    st.session_state[key] = int(st.session_state[key]) + 1


def seed_controls(key, column):
    st.session_state.setdefault(key, 7)
    column.number_input("Semilla aleatoria", min_value=0, max_value=1_000_000, key=key,
                        help="Misma semilla, mismos números aleatorios: la simulación es reproducible.")
    column.button("🎲 Volver a lanzar", key=f"{key}_button", on_click=next_seed, args=(key,), width="stretch")
    return int(st.session_state[key])


def coin_grid(outcomes):
    cells = "".join(f'<span style="background:{FAVORITE_COLOR if won else UPSET_COLOR}"></span>' for won in outcomes)
    st.markdown(f'<div class="coins">{cells}</div>', unsafe_allow_html=True)


def legend(favorite, underdog):
    st.markdown(f'<div class="subtle legend"><span style="background:{FAVORITE_COLOR};margin-left:0"></span>gana {favorite}'
                f'<span style="background:{UPSET_COLOR}"></span>sorpresa: gana {underdog}</div>', unsafe_allow_html=True)


def convergence_chart(outcomes, true_upset):
    """Frecuencia acumulada de sorpresas y embudo de ±1.96 errores estándar alrededor del valor real."""
    rate = running_rate(~outcomes)
    steps = np.unique(np.geomspace(1, len(rate), num=min(len(rate), 600)).astype(int))
    spread = 1.96 * np.sqrt(true_upset * (1 - true_upset) / steps)
    frame = pd.DataFrame({"Simulaciones": steps, "Estimado": 100 * rate[steps - 1],
                          "Bajo": 100 * np.clip(true_upset - spread, 0, 1), "Alto": 100 * np.clip(true_upset + spread, 0, 1)})
    x = alt.X("Simulaciones:Q", scale=alt.Scale(type="log"), title="Número de simulaciones (escala logarítmica)")
    funnel = alt.Chart(frame).mark_area(opacity=.18, color=FAVORITE_COLOR).encode(
        x=x, y=alt.Y("Bajo:Q", title="Frecuencia de sorpresas (%)"), y2="Alto:Q")
    line = alt.Chart(frame).mark_line(color=UPSET_COLOR, strokeWidth=2).encode(
        x=x, y="Estimado:Q", tooltip=[alt.Tooltip("Simulaciones:Q", format=","), alt.Tooltip("Estimado:Q", format=".2f")])
    truth = alt.Chart(pd.DataFrame({"y": [100 * true_upset]})).mark_rule(color=FAVORITE_COLOR, strokeDash=[6, 4]).encode(y="y:Q")
    st.altair_chart((funnel + truth + line).properties(height=300), width="stretch")
    st.caption("Línea roja: lo que estima Monte Carlo después de *n* lanzamientos. Línea punteada: la probabilidad real de sorpresa. "
               "Zona sombreada: donde cae el estimado el 95 % de las veces. Con pocas simulaciones el estimado brinca mucho; "
               "con más se estabiliza (ley de los grandes números) y el error baja como 1/√n.")


def history_chart(simulated, observed):
    counts = pd.Series(simulated).value_counts().sort_index().rename_axis("Victorias").reset_index(name="Simulaciones")
    low, high = np.percentile(simulated, [2.5, 97.5])
    x = alt.X("Victorias:Q", title="Victorias de favoritos en cada historia simulada")
    span = alt.Chart(pd.DataFrame({"a": [low], "b": [high]})).mark_rect(opacity=.12, color=FAVORITE_COLOR).encode(x="a:Q", x2="b:Q")
    bars = alt.Chart(counts).mark_bar(color=FAVORITE_COLOR, opacity=.85).encode(
        x=x, y=alt.Y("Simulaciones:Q", title="Historias simuladas"), tooltip=["Victorias", "Simulaciones"])
    real = pd.DataFrame({"x": [observed], "label": [f"Realidad: {observed}"]})
    rule = alt.Chart(real).mark_rule(color=UPSET_COLOR, strokeWidth=3).encode(x="x:Q")
    text = alt.Chart(real).mark_text(color=UPSET_COLOR, align="right", dx=-6, dy=-6, fontWeight="bold").encode(
        x="x:Q", y=alt.value(12), text="label:N")
    st.altair_chart((span + bars + rule + text).properties(height=320), width="stretch")


def display_monte_carlo(fights):
    st.subheader("Monte Carlo: cuando no puedes repetir la pelea, la repite la computadora")
    st.markdown("Cada pelea ocurre una sola vez, así que con un resultado no sabemos si la cuota estaba bien o si fue suerte. "
                "**El método de Monte Carlo** imita el azar con números aleatorios: repite el experimento miles de veces y cuenta qué pasa. "
                "La receta siempre es la misma:")
    steps = st.columns(3, gap="small", border=True, wrap=True)
    steps[0].markdown("**1 · Modelo del azar**  \nEl favorito gana con probabilidad *p* (la cuota sin margen).")
    steps[1].markdown("**2 · Lanzar**  \nSe sortea un número *u* entre 0 y 1. Si *u* < *p*, gana el favorito; si no, hay sorpresa.")
    steps[2].markdown("**3 · Repetir y contar**  \nMiles de lanzamientos muestran qué resultados son normales y cuáles son raros.")

    st.markdown("### 1 · Una pelea, muchas veces")
    controls, view = st.columns([1, 2], gap="large", wrap=True)
    choice = controls.selectbox("Pelea", [*PRESETS, CUSTOM])
    real_result = None
    if choice == CUSTOM:
        probability = controls.slider("Probabilidad del favorito", 50, 99, 75, format="%d %%") / 100
        favorite, underdog = "el favorito", "el no favorito"
    else:
        fav_key, dog_key = PRESETS[choice]
        match = fights[fights.favorite.str.contains(fav_key) & fights.underdog.str.contains(dog_key)]
        if match.empty:
            st.warning("Esa pelea no está en los datos procesados.")
            return
        row = match.iloc[-1]
        probability, favorite, underdog = float(row.probability), row.favorite, row.underdog
        real_result = f"En la realidad ganó **{favorite if row.favorite_won else underdog}**."
    simulations = controls.select_slider("Simulaciones", [10, 50, 100, 500, 1_000, 5_000, 20_000, 100_000], value=500)
    seed = seed_controls("mc_fight_seed", controls)

    outcomes = fight_outcomes(probability, simulations, np.random.default_rng(seed))
    upsets = int((~outcomes).sum())
    estimate, true_upset = upsets / simulations, 1 - probability
    error = np.sqrt(estimate * (1 - estimate) / simulations)
    with view:
        st.markdown(f"Cuota de apertura: **{favorite} {percent(probability)}** · {underdog} {percent(true_upset)}. "
                    + (real_result or ""))
        cards = st.container(key="mc_fight_cards").columns(3, gap="small", border=True, wrap=True)
        cards[0].metric(f"Sorpresas en {simulations:,} peleas", f"{upsets:,}")
        cards[1].metric("Estimado Monte Carlo", f"{estimate:.2%}", f"{100 * (estimate - true_upset):+.2f} pts vs. real", delta_color="off")
        cards[2].metric("Error estándar", f"±{error:.2%}", help="√(p̂(1−p̂)/n): cuánto variaría el estimado si repitieras todo con otra semilla.")
        shown = min(simulations, 300)
        st.markdown(f"**Las primeras {shown} peleas simuladas**, una por cuadrito:")
        coin_grid(outcomes[:shown])
        legend(favorite, underdog)
    convergence_chart(outcomes, true_upset)

    st.markdown("### 2 · Miles de historias alternativas de la UFC")
    st.markdown("Ahora la pregunta es más grande: **¿las cuotas aciertan con los favoritos?** Suponemos que sí (hipótesis nula) y "
                "con esa suposición volvemos a jugar *todas* las peleas del grupo, cada una con su propia moneda cargada. "
                "Cada repetición es una historia alternativa de la UFC. Luego comparamos cuántos favoritos ganaron de verdad.")
    controls, view = st.columns([1, 2], gap="large", wrap=True)
    band = controls.radio("Favoritos con probabilidad de…", [*BAND_LABELS, "Todas"], index=2)
    histories = controls.select_slider("Historias simuladas", [100, 500, 2_000, 5_000, 20_000], value=2_000)
    seed = seed_controls("mc_history_seed", controls)
    group = fights if band == "Todas" else fights[fights.band == band]
    observed = int(group.favorite_won.sum())

    with view:
        st.markdown(f"**Así se juega una historia**: {len(group):,} peleas, un número aleatorio *u* por pelea. Aquí van ocho de ellas.")
        rng = np.random.default_rng(seed)
        sample = group.sample(8, random_state=seed).copy()
        sample["u"] = rng.random(len(sample))
        st.dataframe(pd.DataFrame({
            "Fecha": sample.event_date, "Favorito": sample.favorite, "Rival": sample.underdog,
            "p (cuota)": sample.probability.map(percent), "u aleatorio": sample.u.round(3),
            "Simulación": np.where(sample.u < sample.probability, "✅ favorito", "❌ sorpresa"),
            "Realidad": np.where(sample.favorite_won == 1, "✅ favorito", "❌ sorpresa")}),
            hide_index=True, width="stretch")

    simulated = simulate_history(tuple(group.probability), histories, seed)
    low, high = np.percentile(simulated, [2.5, 97.5])
    value_p = p_value(simulated, observed)
    cards = st.container(key="mc_history_cards").columns(4, gap="small", border=True, wrap=True)
    cards[0].metric("Victorias reales de favoritos", f"{observed:,}", help=f"{percent(observed / len(group))} de {len(group):,} peleas")
    cards[1].metric("Esperadas si la cuota acierta", f"{simulated.mean():,.0f}", help=f"Probabilidad media del mercado: {percent(group.probability.mean())}")
    cards[2].metric("Rango normal (95 %)", f"{low:,.0f}–{high:,.0f}")
    cards[3].metric("Valor p", f"{value_p:.4f}", help="Fracción de historias simuladas tan extremas como la realidad (bilateral).")
    history_chart(simulated, observed)
    if low <= observed <= high:
        st.success("La realidad cae dentro de lo que el azar produce normalmente: los datos son compatibles con una cuota bien calibrada en este grupo.")
    elif observed > high:
        st.warning(f"La realidad queda **a la derecha** de casi todas las historias simuladas: estos favoritos ganaron más de lo que decía la cuota. "
                   f"El mercado los **infravaloraba** (y sobrevaloraba a sus rivales).")
    else:
        st.warning("La realidad queda **a la izquierda** de casi todas las historias simuladas: estos favoritos ganaron menos de lo que decía la cuota.")
    st.caption("Se comparan varios grupos a la vez, así que un valor p cercano a 0.05 merece cautela. Se usan cuotas de apertura sin margen; "
               "excluye peleas sin cuota y las de 50/50 exacto. Con pocas historias, el valor p más pequeño posible es 2/(historias+1).")
    with st.expander("Ver el código del método"):
        st.code("""rng = np.random.default_rng(semilla)
p = probabilidades_de_los_favoritos            # una por pelea del grupo
u = rng.random((historias, len(p)))            # un número aleatorio por pelea y por historia
victorias = (u < p).sum(axis=1)                # favoritos que ganan en cada historia
valor_p = 2 * min(np.mean(victorias <= real), np.mean(victorias >= real))""", language="python")


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

compare_tab, results_tab, monte_carlo_tab, method_tab = st.tabs(["🥊 Simular combate", "📊 Resultados", "🎲 Monte Carlo", "📖 Método y datos"])
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

with monte_carlo_tab:
    if PROCESSED.exists():
        display_monte_carlo(load_favorites(PROCESSED))
    else:
        st.info("Ejecuta `python mma_pipeline.py` para generar las peleas procesadas que usa la simulación.")

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
