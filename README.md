# MMA Probabilidad

Aplicación Streamlit para comparar dos peleadores UFC y explorar qué relación tienen sus estilos observados con los resultados. La interfaz se adapta a pantallas estrechas y presenta probabilidades, antecedentes, tasas de finalización, calibración y comparación con cuotas iniciales.

## Inicio rápido con Docker

```powershell
docker compose up --build -d
```

Abre <http://localhost:8501>. Para detenerla: `docker compose down`.

El Dockerfile instala las dependencias, descarga [UFC Data v0.1.1](https://github.com/nlbair/ufc-data) desde un commit fijo, comprueba su SHA-256 y genera los historiales, informes y modelo dentro de la imagen. La construcción requiere acceso a Internet y puede tardar varios minutos. El contenedor ejecuta Streamlit como usuario sin privilegios y publica el puerto 8501.

## Ejecución local en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_mma_data.py
.\.venv\Scripts\python.exe mma_pipeline.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre <http://localhost:8501>. Para verificar la lógica temporal: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.

## Qué muestra la aplicación

- **Simular combate:** elige dos peleadores con al menos tres peleas UFC, división, duración y si disputan un título. Muestra probabilidades de victoria, antecedentes previos y el resultado histórico del cruce de estilos. Es una estimación de enfrentamiento; no simula asaltos ni conoce lesiones o cambios de preparación.
- **Resultados:** métricas de prueba cronológica para el modelo y las cuotas iniciales en los mismos combates, calibración por intervalos y tasas de victoria, KO/TKO, sumisión y finalización por cruce de estilos.
- **Método y datos:** explica la procedencia, las fechas y las limitaciones. También se puede descargar el informe completo desde la vista de resultados.

Las columnas de Streamlit se apilan en pantallas estrechas. Las tablas y gráficos ocupan el ancho disponible, de acuerdo con la [documentación de diseño adaptable de Streamlit](https://docs.streamlit.io/develop/api-reference/layout/st.columns).

## Datos y metodología

La fuente fija cubre del 16 de febrero de 2013 al 10 de octubre de 2026. Incluye 6,743 combates; 6,618 son decisivos y se usan para el modelo binario. Se acreditan [UFC Data](https://github.com/nlbair/ufc-data), UFC Stats, MMA Decisions, BestFightOdds y los archivos de rankings empleados por esa base. Los datos se publican bajo CC BY 4.0. Cita: Bair, N. (2026). *UFC Data: scorecards, round statistics, and betting odds, 2013 to 2026* (v0.1.1). Zenodo. https://doi.org/10.5281/zenodo.23458636.

Cada fila de `data/processed/pre_fight_bouts.csv` representa un combate. Las características del peleador proceden únicamente de fechas anteriores; las peleas del mismo día se incorporan juntas una vez construidas sus variables. El orden de los peleadores se fija por ID e ignora quién ganó. Empates y *no contests* actualizan historiales, pero no entran en la clasificación binaria. La cuota inicial se usa solo como referencia externa.

Los estilos `Golpeador`, `Luchador`, `Sometedor` y `Mixto` se asignan con umbrales exploratorios de golpeo, derribos, control y sumisiones previas. Con menos de tres peleas UFC se marca `Sin historial`. Estas etiquetas describen conducta observada, no una disciplina declarada ni una causa comprobada de victoria.

El entrenamiento usa peleas anteriores a 2023; la selección del modelo, 2023–2024; la prueba, 2025–2026. Se reportan exactitud, Brier, pérdida logarítmica, AUC y calibración. El [informe generado](reports/analysis.md) contiene las tasas por estilo y sus intervalos. El modelo de la interfaz se reajusta después con todos los combates decisivos disponibles.

## Archivos principales

| Archivo | Función |
|---|---|
| `app.py` | Interfaz Streamlit. |
| `mma_service.py` | Comparación de peleadores independiente de la interfaz. |
| `mma_pipeline.py` | Auditoría, variables previas, estilos, entrenamiento e informes. |
| `download_mma_data.py` | Descarga fija con verificación SHA-256. |
| `Dockerfile`, `compose.yaml` | Construcción y ejecución del contenedor. |
| `reports/` | Métricas, cruces e informe generados. |

El archivo de origen, los datos procesados y el modelo están excluidos de Git porque se regeneran. Para actualizar la fuente hay que revisar esquema, procedencia y checksum. UFC no representa todas las MMA y la base no mide daño, lesiones ni preparación. Las asociaciones entre estilos son descriptivas.
