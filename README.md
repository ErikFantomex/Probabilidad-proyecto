# MMA Probabilidad

Aplicación Streamlit para comparar dos peleadores UFC y explorar qué relación tienen sus estilos observados con los resultados. La interfaz se adapta a pantallas estrechas y presenta probabilidades, antecedentes, tasas de finalización, calibración y comparación con cuotas iniciales.

La presentación de cinco diapositivas está en [docs/mma-estilos-y-prediccion.pptx](docs/mma-estilos-y-prediccion.pptx). Su copia editable se puede regenerar con `pip install python-pptx` y `python docs/build_slides.py`.

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

El [estudio de Topuria–Gaethje, Steveson–Sharaf y Gane–Hokit](docs/dinamica-de-poder.md) compara el cambio de división, la oportunidad de imponer un estilo y la relación entre peso, golpeo y control.

La fuente fija cubre del 16 de febrero de 2013 al 10 de octubre de 2026. Incluye 6,743 combates; 6,618 son decisivos y se usan para el modelo binario. Se acreditan [UFC Data](https://github.com/nlbair/ufc-data), UFC Stats, MMA Decisions, BestFightOdds y los archivos de rankings empleados por esa base. Los datos se publican bajo CC BY 4.0. Cita: Bair, N. (2026). *UFC Data: scorecards, round statistics, and betting odds, 2013 to 2026* (v0.1.1). Zenodo. https://doi.org/10.5281/zenodo.23458636.

Cada fila de `data/processed/pre_fight_bouts.csv` representa un combate. Las características del peleador proceden únicamente de fechas anteriores; las peleas del mismo día se incorporan juntas una vez construidas sus variables. El orden de los peleadores se fija por ID e ignora quién ganó. Empates y *no contests* actualizan historiales, pero no entran en la clasificación binaria. La cuota inicial se usa solo como referencia externa.

Los estilos `Golpeador`, `Luchador`, `Sometedor` y `Mixto` se asignan con umbrales exploratorios de golpeo, derribos, control y sumisiones previas. Con menos de tres peleas UFC se marca `Sin historial`. Estas etiquetas describen conducta observada, no una disciplina declarada ni una causa comprobada de victoria.

El entrenamiento usa peleas anteriores a 2023; la selección del modelo, 2023–2024; la prueba, 2025–2026. Se reportan exactitud, Brier, pérdida logarítmica, AUC y calibración. El [informe generado](reports/analysis.md) contiene las tasas por estilo y sus intervalos. El modelo de la interfaz se reajusta después con todos los combates decisivos disponibles.

## Guía para hacer más pruebas cruzadas

### Comparar striker contra mixto, striker KO contra grappler y otros cruces

En **Resultados → Cruces de estilos**, elige **Estilo general** para ver a todos los golpeadores (*strikers*) frente a mixtos, luchadores o sometedores. En **Especialidad**, *Grappler* agrupa a luchadores y sometedores. Un **Golpeador KO** cumple la regla de Golpeador y tiene al menos dos victorias previas por KO/TKO, que representan al menos el 50 % de sus victorias registradas. Los demás golpeadores forman el grupo **Otro golpeador**. Son umbrales exploratorios basados en el historial disponible hasta el día anterior.

Cada vista cuenta una vez cada combate decisivo con ambos estilos conocidos. Las dos vistas comparten peleas. La tasa de victorias corresponde al primer estilo del nombre del cruce y queda vacía cuando ambos coinciden. Las tasas de KO/TKO y sumisión incluyen victorias de cualquiera de los dos. Consulta el número de peleas y el intervalo de Wilson al 95 % junto a cada tasa de victoria, especialmente en los cruces menos frecuentes.

Desde la raíz del repositorio, con el entorno y los datos locales preparados, ejecuta en PowerShell

```powershell
.\.venv\Scripts\python.exe mma_pipeline.py
.\.venv\Scripts\python.exe cross_validate.py --group-by style
.\.venv\Scripts\python.exe cross_validate.py --group-by specialist
```

El primer comando regenera los [cruces generales](reports/style_matchups.csv) y los [cruces por especialidad](reports/specialist_matchups.csv) de todo el historial. Los otros dos entrenan cada modelo con las peleas anteriores a cada ventana y desglosan sus pronósticos por [estilo](reports/cross_validation_style.csv) o [especialidad](reports/cross_validation_specialist.csv). En esos archivos, filtra `style_pair` por `Golpeador × Mixto` o `Golpeador KO × Grappler`. La columna `n` cuenta los combates del cruce y subconjunto en esa ventana. AUC queda vacía si todos los resultados observados pertenecen a una sola clase. Puedes combinar `--group-by` con los parámetros de años y de salida que se explican a continuación.

### Evaluación general por ventanas

El comando `cross_validate.py` hace **validación temporal con ventana de entrenamiento creciente**. Para cada periodo de prueba entrena de cero con todos los combates decisivos anteriores y predice solamente combates posteriores. Por defecto prueba 2019–2020, 2021–2022, 2023–2024 y 2025–2026. Mantiene fijos los dos modelos y sus hiperparámetros de `mma_pipeline.py`; no elige el ganador usando el periodo que evalúa. Evita `KFold` aleatorio: mezclar fechas permitiría aprender del futuro de un peleador.

Desde la raíz del repositorio, en PowerShell:

```powershell
# Solo la primera vez, si aún no existen .venv ni los datos procesados:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_mma_data.py
.\.venv\Scripts\python.exe mma_pipeline.py

# Repetir la evaluación y guardar el detalle por ventana:
.\.venv\Scripts\python.exe cross_validate.py

# Comprobar la lógica de construcción de variables y del servicio:
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

El resultado queda en `reports/cross_validation.csv`. `--start-year` cambia el primer año probado, `--end-year` es exclusivo y `--fold-years` fija la duración de cada ventana. Por ejemplo, para ventanas anuales de 2021 a 2026:

```powershell
.\.venv\Scripts\python.exe cross_validate.py --start-year 2021 --end-year 2027 --fold-years 1 --output reports/cv_anual.csv
```

Cada fila del CSV informa `train_n`, fechas máxima de entrenamiento y mínima/máxima de prueba, `n` y métricas. `subset=all` usa todos los combates decisivos de la ventana. `subset=with_odds` restringe **los tres pronósticos a las mismas peleas con cuota inicial**; solo ahí es justa la comparación con `market_open`. Menor `brier` y `log_loss` es mejor; mayor `auc` y `accuracy` es mejor. Brier y pérdida logarítmica juzgan la calidad de las probabilidades, no solo quién fue favorito. Revisa cada ventana por separado: una media puede ocultar deterioro reciente. No compares métricas de filas con distintos `subset` o tamaños `n` como si fueran el mismo conjunto.

Para avanzar de forma reproducible:

1. Conserva el CSV original, su versión, fecha final y SHA-256 del descargador. Si actualizas datos, revisa columnas, duplicados, fechas y peleas sin resultado antes de regenerar `data/processed/pre_fight_bouts.csv`.
2. Define **antes de ejecutar** una hipótesis y una métrica principal; por ejemplo, “añadir una variable histórica de control reduce la pérdida logarítmica en al menos 0.01 en varias ventanas”. Cambia una cosa a la vez y guarda el comando, commit y CSV resultante.
3. Calcula cualquier variable nueva solo con información anterior al evento. Mantén juntas las peleas del mismo día y verifica que `train_last_date < test_first_date` en todas las filas. Si una variable depende de cuotas, no la uses en el modelo que quieres comparar con el mercado.
4. Compara la propuesta con `logistic`, `hist_gradient_boosting` y `market_open` en el mismo subconjunto. Revisa también resultados por año, división y pareja de estilos; informa el número de peleas y evita conclusiones fuertes en grupos pequeños. Para el análisis de estilos usa `reports/style_matchups.csv` y sus intervalos, sin atribuir causalidad a las etiquetas.
5. Elige cambios con las ventanas anteriores y reserva combates posteriores, todavía no examinados, para una prueba final. Vuelve a entrenar el modelo de la aplicación mediante `mma_pipeline.py` solo después de decidir la configuración. Registra también cambios que empeoren el resultado para no seleccionar por azar el mejor intento.

La prueba 2025–2026 y estos pliegues ya son datos históricos inspeccionados; tras iterar con ellos dejan de ser una prueba independiente. La evaluación futura requiere descargar eventos nuevos y fijar las predicciones **antes** de conocer sus resultados. Diferencias de tasa entre estilos son asociaciones descriptivas: el historial, la división y el emparejamiento pueden explicarlas parcialmente.

## Ejemplo de Monte Carlo: ¿las cuotas aciertan con los favoritos?

`monte_carlo.py` responde con simulación una pregunta que plantea el [estudio de casos](docs/dinamica-de-poder.md): ¿la sorpresa de Sharaf sobre Steveson, que abrió con 90,4 %, fue mala suerte o un error del mercado?

1. **Una pelea.** Repite Steveson–Sharaf 100 000 veces con la probabilidad de la cuota y cuenta las sorpresas (≈ 1 de cada 10).
2. **Todas las peleas.** Supone que el mercado está bien calibrado: cada favorito gana con su probabilidad implícita. Simula 20 000 historias alternativas de la UFC lanzando una "moneda cargada" por pelea y compara las victorias reales de los favoritos con el rango simulado, por tramos de probabilidad. El valor p es la fracción de simulaciones tan extremas como lo observado.

```powershell
.\.venv\Scripts\python.exe mma_pipeline.py      # si aún no existen los datos procesados
.\.venv\Scripts\python.exe monte_carlo.py --simulations 20000 --seed 42
```

Genera [reports/monte_carlo.md](reports/monte_carlo.md) y [reports/monte_carlo_favorites.csv](reports/monte_carlo_favorites.csv). Con los datos fijos, los favoritos de 50–70 % ganan lo esperado, pero los de 70 % o más ganan más de lo que indica la cuota de apertura: el mercado los infravaloraba. Son comparaciones múltiples sobre cuotas de apertura, no de cierre.

## Archivos principales

| Archivo | Función |
|---|---|
| `app.py` | Interfaz Streamlit. |
| `mma_service.py` | Comparación de peleadores independiente de la interfaz. |
| `mma_pipeline.py` | Auditoría, variables previas, estilos, entrenamiento e informes. |
| `cross_validate.py` | Pruebas cronológicas repetidas y CSV de métricas por ventana. |
| `monte_carlo.py` | Simulación Monte Carlo de sorpresas frente a la cuota de apertura. |
| `download_mma_data.py` | Descarga fija con verificación SHA-256. |
| `Dockerfile`, `compose.yaml` | Construcción y ejecución del contenedor. |
| `reports/` | Métricas, cruces e informe generados. |

El archivo de origen, los datos procesados y el modelo están excluidos de Git porque se regeneran. Para actualizar la fuente hay que revisar esquema, procedencia y checksum. UFC no representa todas las MMA y la base no mide daño, lesiones ni preparación. Las asociaciones entre estilos son descriptivas.
