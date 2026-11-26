# Monte Carlo: sorpresas frente a la cuota de apertura

Simulaciones por grupo: 20,000; semilla: 42. Fuente: `data/processed/pre_fight_bouts.csv` (peleas decisivas con cuota inicial sin margen; se excluyen las cuotas exactas de 50 %).

## 1. Una pelea: Steveson frente a Sharaf

El mercado daba a Steveson 90.4%. Al repetir la pelea 100,000 veces con esa probabilidad, Sharaf gana en 9.65% de los casos (error estándar Monte Carlo ±0.09%). Aproximadamente una de cada 10 peleas así termina en sorpresa: el KO de Sharaf es raro, pero no extraordinario.

## 2. Muchas peleas: ¿están bien calibradas las cuotas?

Hipótesis nula: cada favorito gana con su probabilidad implícita. En cada simulación se lanza una "moneda cargada" por pelea y se cuentan las victorias de favoritos. El rango del 95 % muestra qué sería normal si el mercado acertara; el valor p indica qué tan raro es lo observado bajo esa hipótesis.

| Probabilidad del favorito | Peleas | Prob. media del mercado | Victorias observadas | Esperadas | Rango simulado 95 % | Valor p |
|---|---:|---:|---:|---:|---:|---:|
| 50–60 % | 2191 | 55.9% | 1215 (55.5%) | 1224 | 1179–1269 | 0.6967 |
| 60–70 % | 2724 | 64.7% | 1768 (64.9%) | 1763 | 1714–1812 | 0.8481 |
| 70–80 % | 1234 | 74.0% | 990 (80.2%) | 913 | 883–943 | 0.0002 |
| 80 % o más | 227 | 83.6% | 203 (89.4%) | 190 | 178–200 | 0.0184 |
| Todas | 6376 | 64.1% | 4176 (65.5%) | 4090 | 4015–4165 | 0.0251 |

## Lectura

- Si las victorias observadas caen dentro del rango simulado, los datos son compatibles con un mercado calibrado en ese grupo.
- Si caen por encima, los favoritos ganaron más de lo que sugería la cuota (el mercado les daba poco); por debajo, lo contrario.
- Se hacen varias comparaciones a la vez; conviene leer valores p cercanos a 0.05 con cautela.
- La cuota de apertura puede moverse antes de la pelea; aquí no se usa la cuota de cierre.
