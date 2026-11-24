# Análisis de estilos y predictibilidad UFC

## Alcance y auditoría

Fuente: nlbair/ufc-data v0.1.1 (a9c6543), 2013–2026. Filas: 6743; peleadores: 2067.
Combates decisivos: 6618; con cuota inicial: 6705; IDs duplicados: 0.
Empates y no contests permanecen en la historia, pero se excluyen del modelo binario.
Los estilos son etiquetas de comportamiento previo: no equivalen al arte marcial declarado por el peleador.

## Cruces de estilos

Tasas descriptivas, sin ajuste causal. IC del 95% de Wilson para finalizaciones.

| Cruce | Peleas | Victoria del primer estilo | IC 95% victoria | Finalización | IC 95% finalización | KO/TKO | Sumisión | Victoria del no favorito |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Luchador × Luchador | 1403 | — | — | 45.6% | 43.0%–48.2% | 29.3% | 16.3% | 34.1% |
| Golpeador × Luchador | 494 | 46.2% | 41.8%–50.6% | 49.6% | 45.2%–54.0% | 35.4% | 14.2% | 34.8% |
| Luchador × Mixto | 387 | 57.4% | 52.4%–62.2% | 51.4% | 46.5%–56.4% | 38.2% | 13.2% | 32.9% |
| Luchador × Sometedor | 360 | 48.1% | 42.9%–53.2% | 56.9% | 51.8%–62.0% | 30.3% | 26.7% | 31.6% |
| Golpeador × Mixto | 81 | 44.4% | 34.1%–55.3% | 54.3% | 43.5%–64.7% | 44.4% | 9.9% | 29.1% |
| Golpeador × Sometedor | 75 | 45.3% | 34.6%–56.5% | 53.3% | 42.2%–64.2% | 30.7% | 22.7% | 35.1% |
| Golpeador × Golpeador | 66 | — | — | 43.9% | 32.6%–55.9% | 39.4% | 4.5% | 25.0% |
| Mixto × Sometedor | 41 | 43.9% | 29.9%–59.0% | 65.8% | 50.5%–78.4% | 26.8% | 39.0% | 39.0% |
| Mixto × Mixto | 36 | — | — | 61.1% | 44.9%–75.2% | 52.8% | 8.3% | 22.2% |
| Sometedor × Sometedor | 31 | — | — | 51.6% | 34.8%–68.0% | 22.6% | 29.0% | 43.3% |

### Cruces por especialidad

Grappler agrupa Luchador y Sometedor. Golpeador KO exige dos victorias previas por KO/TKO y al menos la mitad de las victorias registradas por esa vía. Cada pelea figura una vez por tabla.

| Cruce | Peleas | Victoria del primer estilo (IC 95%) | KO/TKO de cualquiera | Sumisión de cualquiera |
|---|---:|---:|---:|---:|
| Grappler × Grappler | 1794 | — | 29.4% | 18.6% |
| Grappler × Mixto | 428 | 57.2% (52.5%–61.9%) | 37.1% | 15.7% |
| Grappler × Otro golpeador | 335 | 56.4% (51.1%–61.6%) | 29.5% | 15.8% |
| Golpeador KO × Grappler | 234 | 49.6% (43.2%–55.9%) | 42.3% | 14.5% |
| Golpeador KO × Mixto | 50 | 50.0% (36.6%–63.4%) | 52.0% | 12.0% |
| Mixto × Mixto | 36 | — | 52.8% | 8.3% |
| Mixto × Otro golpeador | 31 | 64.5% (46.9%–78.9%) | 32.3% | 6.5% |
| Golpeador KO × Otro golpeador | 28 | 53.6% (35.8%–70.5%) | 57.1% | 7.1% |
| Otro golpeador × Otro golpeador | 23 | — | 17.4% | 4.3% |
| Golpeador KO × Golpeador KO | 15 | — | 40.0% | 0.0% |

## Predicción cronológica

Entrenamiento: antes de 2023 (4653); selección: 2023–2024 (1017); prueba: 2025–2026 (948).
Modelo elegido por pérdida logarítmica de validación: **hist_gradient_boosting**.

| Prueba | Combates | Exactitud | Brier | Pérdida logarítmica | AUC |
|---|---:|---:|---:|---:|---:|
| Modelo | 948 | 63.2% | 0.2257 | 0.6427 | 0.6820 |
| Modelo, peleas con cuotas | 937 | 63.5% | 0.2245 | 0.6401 | 0.6876 |
| Cuota inicial sin margen | 937 | 66.6% | 0.2094 | 0.6071 | 0.7354 |

### Calibración del modelo en prueba

| Probabilidad estimada | Combates | Probabilidad media | Victorias observadas |
|---|---:|---:|---:|
| (-0.001, 0.1] | 2 | 9.0% | 0.0% |
| (0.1, 0.2] | 12 | 17.4% | 0.0% |
| (0.2, 0.3] | 65 | 26.3% | 24.6% |
| (0.3, 0.4] | 169 | 35.4% | 31.4% |
| (0.4, 0.5] | 279 | 45.4% | 43.7% |
| (0.5, 0.6] | 223 | 54.9% | 57.0% |
| (0.6, 0.7] | 133 | 64.8% | 65.4% |
| (0.7, 0.8] | 61 | 73.4% | 73.8% |
| (0.8, 0.9] | 4 | 82.2% | 100.0% |

La frecuencia de victorias del no favorito cuantifica sorpresas respecto al mercado; Brier, pérdida logarítmica y calibración cuantifican incertidumbre predictiva. Una exactitud mayor que 50% no demuestra que las peleas sean fáciles de predecir.

## Limitaciones

- UFC solamente; los primeros combates UFC tienen poco historial observable.
- Los umbrales de estilo son exploratorios y las categorías pueden cambiar con el tiempo.
- Las asociaciones entre estilos no prueban causalidad; división, nivel del rival y época pueden influir.
- La cuota inicial es una referencia externa, no una variable de entrada del modelo.
- El último combate en la fuente es del 10 de octubre de 2026; la interfaz no actualiza resultados automáticamente.
