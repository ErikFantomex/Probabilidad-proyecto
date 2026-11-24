# MMA Probabilidad

Estudio reproducible de peleas UFC para explorar cruces de estilos y la incertidumbre al pronosticar un ganador. El proyecto anterior de Dota 2 queda en los cuadernos y archivos `utils/`, pero `app.py` ahora sirve la aplicación de MMA.

## Preguntas

1. ¿Cómo varía la frecuencia de KO/TKO, sumisión y decisión entre cruces de estilos observados antes de la pelea?
2. ¿Qué proporción de no favoritos gana en cada cruce?
3. ¿Qué tan buenas son las probabilidades de un modelo basado en historiales previos frente a las cuotas iniciales sin margen?

"Estilo" significa un perfil cuantitativo de comportamiento UFC, no una disciplina declarada. "Pelea emocionante" no tiene una definición objetiva en esta base; se reportan finalizaciones y sorpresas como resultados observables, sin afirmar que midan entretenimiento.

## Fuente y licencia

Se usa [UFC Data v0.1.1](https://github.com/nlbair/ufc-data), fijado al commit `a9c6543` y verificado con SHA-256 en `download_mma_data.py`. Cubre el 16 de febrero de 2013 al 10 de octubre de 2026 y combina UFC Stats, MMA Decisions, BestFightOdds y rankings. Los datos se publican bajo CC BY 4.0. Cita sugerida: Bair, N. (2026). *UFC Data: scorecards, round statistics, and betting odds, 2013 to 2026* (v0.1.1). Zenodo. https://doi.org/10.5281/zenodo.23458636. La [metodología original](https://github.com/nlbair/ufc-data/blob/main/METHODS.md) describe los emparejamientos entre fuentes.

El archivo descargado se guarda en `data/raw/` y no se incluye en Git. Las cuotas iniciales son una referencia de comparación; no entrenan el modelo. La actualización de UFC no es automática: para cambiar la versión de la fuente hay que revisar esquema, procedencia y checksum.

## Ejecutar en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_mma_data.py
.\.venv\Scripts\python.exe mma_pipeline.py
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:5000/`; el análisis agregado está en `/analysis`.

Para comprobar la lógica temporal: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.

## Método

- Una fila por `fight_id`. Los IDs de los peleadores determinan un orden estable e independiente del resultado. Empates y *no contests* actualizan historiales, pero no entran en el modelo binario.
- Las estadísticas acumuladas solo incluyen combates de fechas anteriores; las peleas del mismo día se incorporan juntas después de crear sus variables. Los datos del combate actual se usan únicamente para actualizar el futuro.
- Las tasas de golpeo, derribo, control y sumisión se expresan por minuto o por 15 minutos. Con menos de tres peleas UFC, el estilo es `Sin historial`. Los umbrales exploratorios de `Sometedor`, `Luchador`, `Golpeador` y `Mixto` están en `mma_pipeline.py`.
- La división temporal es entrenamiento antes de 2023, selección de modelo en 2023–2024 y prueba final en 2025–2026. Se comparan regresión logística y *histogram gradient boosting* por pérdida logarítmica de validación. Tras la prueba, el modelo de la aplicación se ajusta con todos los combates decisivos disponibles.
- Se informan exactitud, Brier, pérdida logarítmica y AUC. Las tasas de finalización tienen intervalos de Wilson del 95%. Las comparaciones de estilos son descriptivas, no causales.

## Archivos producidos

| Ruta | Contenido |
|---|---|
| `data/processed/pre_fight_bouts.csv` | Combates con variables anteriores a cada pelea. |
| `data/processed/fighters_latest.csv` | Historial acumulado de cada peleador para la interfaz. |
| `reports/analysis.md` | Hallazgos, comparación predictiva y limitaciones. |
| `reports/style_matchups.csv` | Cruces de estilos e intervalos. |
| `reports/metrics.json` | Auditoría y métricas de evaluación. |
| `models/mma_model.joblib` | Modelo final para uso local. Cargar solo si fue generado por este proyecto. |

## Límites

UFC no representa todas las MMA. Los primeros combates UFC de un atleta carecen de trayectoria observable en esta base, y las estadísticas no miden daño, lesiones o preparación. La clasificación de estilos es sensible a sus umbrales. La interfaz compara peleadores con al menos tres peleas UFC y permite indicar si la pelea es por título, pero no comprueba elegibilidad real ni cartelera futura; sus probabilidades son una exploración estadística.
