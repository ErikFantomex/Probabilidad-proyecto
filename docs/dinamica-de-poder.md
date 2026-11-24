# ¿Cuándo puede un peleador imponer su estilo?

Aquí usamos *poder* en un sentido deportivo observable. Un peleador puede ganar intercambios, decidir en qué fase transcurre la pelea o producir una acción que la termine. Esas ventajas pueden pertenecer a distintos atletas en un mismo combate. Los tres casos permiten examinar qué ventaja se esperaba antes del evento, cuál apareció en la jaula y cuánto duró.

## Ilia Topuria frente a Oliveira y Gaethje

| Rival | División | Resultado de Topuria | Golpes significativos conectados, Topuria–rival |
|---|---|---|---:|
| Alexander Volkanovski | 145 lb | Ganó el cinturón por KO, R2 | 35–47 |
| Max Holloway | 145 lb | Defendió por KO, R3 | 75–79 |
| Charles Oliveira | 155 lb | Ganó el cinturón vacante por KO, 2:27 de R1 | 21–9 |
| Justin Gaethje | 155 lb | Perdió por TKO tras el cuarto asalto | 97–91 |

En sus dos peleas de campeonato en pluma, Topuria conectó menos golpes significativos que su rival y consiguió el KO. La evidencia más clara de su dominio fue su capacidad de terminar peleas aun cuando el otro seguía produciendo ofensiva. Esa capacidad también apareció contra Oliveira en ligero. Además, Topuria ya había ganado en 155 lb contra Jai Herbert en 2022. [Registro del título de peso ligero](https://www.boxing.nv.gov/siteassets/results2/2025-results/06-28-25MMA_REDACTED.pdf)

Ante Gaethje, Topuria abrió con un 80,2 % de probabilidad implícita sin margen. Durante el segundo asalto puso en dificultades a Gaethje y buscó la sumisión. Al cabo de cuatro asaltos llevaba más golpes significativos y tenía el único derribo por golpe (*knockdown*) registrado. Sin embargo, su esquina detuvo la pelea antes del quinto. Posteriormente se reportaron fracturas en ambas órbitas. El resultado oficial fue TKO por detención de la esquina. [Crónica de UFC](https://www.ufc.com/news/ufc-freedom-250-results-highlights-interviews) · [Reporte posterior sobre las lesiones](https://as.com/masdeporte/polideportivo/topuria-avanza-la-hinchazon-ha-desaparecido-f202606-n/)

Oliveira y Gaethje ofrecen la comparación más informativa porque ambos combates fueron a 155 lb. En uno, Topuria impuso un desenlace temprano. En el otro también creó oportunidades, pero el rival siguió compitiendo hasta que Topuria quedó imposibilitado para continuar. Atribuir esa diferencia al salto de división exigiría comparar más peleadores que subieron de peso y considerar la calidad y el estilo de sus oponentes.

## Gable Steveson frente a Sean Sharaf

Steveson llegó invicto a UFC, con oro olímpico en lucha, experiencia en WWE y la mentoría de Jon Jones. En su debut frenó a Elisha Ellison en el primer asalto. Los golpes significativos quedaron 41–13 a favor de Steveson. Los 13 de Ellison dan sustento a una observación que ya aparecía en la previa de su segunda pelea: sus rivales encontraban ocasiones para conectar. Un solo combate apenas permite estimar la frecuencia de esas ocasiones. [Perfil de Steveson](https://www.ufc.com/athlete/gable-steveson) · [Previa publicada antes del combate con Sharaf](https://www.ufc.com/news/fight-fight-preview-cryptocom-ufc-331-van-vs-pantoja-2)

Contra Sharaf, la cuota inicial de Steveson equivalía al 90,4 % sin margen, lo que dejaba un 9,6 % a Sharaf. Sharaf ganó por KO a los 12 segundos. Ese tiempo explica por qué importa el orden de los acontecimientos: la pelea pudo terminar antes de que hubiera una fase prolongada de lucha en la que observar la ventaja olímpica. Con una sola pelea UFC previa, Steveson además quedaba en la categoría **Sin historial** según la regla del proyecto. El 90,4 % procede del mercado. Para estudiar si esas cuotas sobrevaloran a los grandes favoritos habría que comparar la frecuencia de sorpresas en todo ese grupo. [Resultado oficial](https://www.ufc.com/athlete/sean-sharaf)

## Ciryl Gane frente a Josh Hokit

En el pesaje oficial, Gane marcó **242,6 lb** y Hokit **231,4 lb**, una diferencia de **11,2 lb**. El desglose registra **237 golpes significativos de Gane**, de los cuales **170 fueron a la cabeza**, 63 al cuerpo y 4 a las piernas. Hokit conectó 146 significativos, consiguió tres derribos y acumuló 4:37 de control. Llegaron al final de los cinco asaltos y los tres jueces puntuaron 48–47 a favor de Gane. [Pesaje de UFC](https://www.ufc.com/news/official-weigh-results-polymarket-ufc-334-gane-vs-hokit) · [Desglose del combate](https://mmaelo.com/fight?id=f26dd1b67870) · [Tarjetas oficiales](https://www.ufc.com/news/polymarket-ufc-334-gane-vs-hokit-official-scorecards)

Gane sostuvo una ventaja de 91 golpes significativos. Hokit, el más ligero, consiguió llevar la pelea al suelo y ganó dos asaltos en cada tarjeta. El peso del pesaje, el volumen de golpeo y los minutos de control describen tres cosas distintas. El registro cuenta impactos y sus destinos, pero carece de mediciones de fuerza por impacto o de tolerancia fisiológica. La comparación entre fases explica mejor cómo siguió siendo competitivo Hokit que su aspecto físico o el conteo total por sí solo.

## Cómo contrastar estas lecturas

Los conteos de Topuria y Steveson y las cuotas de apertura se pueden reproducir en `data/raw/ufc_all_fights_wide.csv` filtrando por ambos nombres, respetando el orden de `f1_name` y `f2_name`, y consultando `f1_tot_sig_str_landed`, `f2_tot_sig_str_landed`, `method_detail` y `f1_open_prob_novig`. Gane–Hokit ocurrió el 14 de noviembre de 2026, después del cierre del CSV el 10 de octubre. Se presenta como caso externo.

Para ampliar el análisis, compara peleas de un mismo atleta antes y después de subir de división, registra las oportunidades de lucha y el tiempo hasta el desenlace en debutantes de élite, y cruza los pesajes oficiales con las tarjetas por asalto en pesos pesados. Conserva todos los encuentros que cumplan el criterio, incluidas las victorias esperadas y las decisiones. Estos tres ejemplos, elegidos por sus desenlaces, sirven para formular esas hipótesis.
