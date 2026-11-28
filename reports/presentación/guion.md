# Guion · Método de Monte Carlo y control probabilístico del error

> Tono de plática, no de lectura. Lo que está entre corchetes son acciones: **[→]** es avanzar, **[demo]** es usar un botón de la diapositiva.
> Tiempo aproximado: 18–22 minutos.

---

## 1 · Portada

¡Hola a todos! Hoy les vamos a platicar del **método de Monte Carlo**. Suena muy elegante, pero la idea es casi de sentido común: si no puedes calcular algo, simúlalo muchas veces y fíjate qué pasa.

Y no nos vamos a quedar en la teoría: al final lo vamos a usar con peleas reales de la UFC para ver si las casas de apuestas le atinan o no.

**[→]**

---

## 2 · ¿Qué es?

Esta frase resume todo: *si un problema es difícil de resolver analíticamente, lo simulamos miles de veces y estudiamos estadísticamente los resultados.*

O sea, en vez de sentarnos a hacer una integral horrible, ponemos a la computadora a "jugar" el experimento una y otra vez.

**[→]** Y la receta siempre son tres pasos: **simular** muchas veces, **promediar** lo que salió y, lo más importante, **medir el error**. Porque una simulación siempre da un número aproximado, y tenemos que saber qué tan lejos podemos estar del valor real. De eso va lo de "control probabilístico del error".

**[→]**

---

## 3 · Teorema del Límite Central

¿Y cómo medimos ese error? Aquí entra nuestro amigo el **Teorema del Límite Central**.

Lo que dice, en cristiano, es que si sacas el promedio de muchas variables aleatorias, ese promedio se comporta como una normal, *sin importar* de qué distribución vengan los datos. Y además nos dice qué tan ancha es esa campana: su desviación es **σ entre raíz de n**.

**[demo]** Miren, aquí tenemos una exponencial, que está toda chueca. Si promedio de a 1, se ve igual de chueca. Pero conforme subo la *n*… *(mover el slider a 30 o más)* …se va poniendo bonita, en forma de campana, y la línea roja, que es la normal teórica, le queda casi perfecto. Abajo pueden ver que la desviación que observamos y la de σ/√n prácticamente coinciden.

Pueden cambiarle a dado o a Bernoulli y pasa lo mismo. Esa es la magia.

**[→]**

---

## 4 · Propiedades estadísticas

Gracias a eso, el estimador de Monte Carlo tiene cuatro propiedades muy chidas:

1. **Es insesgado:** en promedio le atina. No se carga ni para arriba ni para abajo.
2. **Es consistente:** por la Ley de los Grandes Números, entre más simulaciones, más se acerca al valor real.
3. **Tasa de convergencia:** el error baja como 1 entre raíz de N. Ojo con esto: si quieres **10 veces menos error**, necesitas **100 veces más simulaciones**. Lo bueno es que esto no depende de la dimensión del problema.
4. **Intervalos de confianza:** no nada más damos un numerito, damos un rango. "π está entre tanto y tanto, con 95 % de confianza".

**[→]**

---

## 5 · Componentes de un algoritmo

Todo algoritmo de Monte Carlo tiene estas cinco piezas. Las vamos a seguir con el ejemplo de estimar π, que viene en un ratito:

1. **Definir el modelo:** este es el truco principal. Hay que convertir nuestra pregunta en *el promedio de algo que podamos simular*. Con π: tiro un punto al azar en el cuadrado y anoto un **1** si cayó dentro del círculo y un **0** si cayó fuera. Si hago eso muchas veces y saco el promedio de los unos y ceros, me da la fracción de puntos que cayeron dentro, que se acerca a π/4. Ya convertimos "¿cuánto vale π?" en "¿qué porcentaje de puntos cae en el círculo?", y eso sí lo podemos simular.
2. **Números pseudoaleatorios:** la computadora genera números que *parecen* al azar. Con la misma semilla salen los mismos, y eso sirve para que cualquiera pueda repetir nuestro resultado.
3. **Simular N veces:** tirar los N puntos y anotar qué pasó con cada uno.
4. **Agregar:** sacar el promedio. Para π es 4 por la proporción de puntos que cayeron dentro.
5. **Evaluar la incertidumbre:** decir qué tanto nos podemos estar equivocando. El resultado nunca va solo; va con su "±".

**[→]**

---

## 6 · Limitaciones

Ahora, no todo es color de rosa:

- **Converge lento.** Lo de la raíz de N: cada dígito extra de precisión te cuesta 100 veces más trabajo.
- **Depende de la varianza.** Si lo que simulas brinca mucho, el error es grande.
- **Eventos raros.** Si quieres estimar algo que pasa una vez en un millón, casi ninguna simulación le va a "pegar".
- **El generador importa.** Son números *pseudo*aleatorios; un generador malo te mete sesgo.
- **El modelo manda.** Si tu modelo está mal, vas a obtener una respuesta muy precisa… pero equivocada.
- Y siempre es **aproximado**: cada corrida da un número distinto. Por eso reportamos intervalos.

**[→]**

---

## 7 · El error σ/√N en acción

Vamos a ver lo de la raíz de N con nuestros propios ojos.

**[demo: «Correr 30 réplicas por N»]** Cada puntito es una estimación de π, y en vertical está qué tan lejos quedó del valor real. Para cada tamaño N corremos 30 veces.

Fíjense: la nube va bajando y sigue la línea roja, que es σ/√N. Como está en escala logarítmica, la pendiente es de **menos un medio**. Y ahí está anotado: cuando N crece **por 100**, el error baja **entre 10**. Justo lo que dijimos.

**[→]**

---

## 8 · Control probabilístico del error

Bueno, ya vimos que el error baja como σ/√N. Ahora viene la parte que le da nombre a la presentación: el **control probabilístico del error**.

La idea es muy sencilla: equivocarnos es inevitable, porque cada simulación sale un poquito distinta. Pero sí podemos **decidir cuánto y qué tan seguido** nos equivocamos. Para eso movemos dos perillas:

- **¿Cuánto me puedo equivocar?** Esa es la precisión. Por ejemplo: "quiero que π me salga a menos de 0.01 del valor real".
- **¿Qué tan seguido quiero acertar?** Esa es la confianza. Con 95 %, le atinamos 19 de cada 20 veces.

¿Y cómo sabemos cuántas simulaciones hacen falta? Gracias al Teorema del Límite Central hay una receta: **N ≈ (z·σ/ε)²**. Sin asustarse, cada letra es algo que ya conocemos: la *z* sale de la confianza (1.96 para el 95 %), la *σ* es qué tanto brinca cada simulación y la *ε* es el error que aceptamos. Moraleja: **más precisión o más confianza, más simulaciones**.

**[demo]** Miren la calculadora: para estimar π con un error menor a 0.01 y 95 % de confianza necesitamos unas **100 mil** simulaciones. Si quiero el doble de precisión, no es el doble de trabajo: es **4 veces** más. Y si le pido 0.001, un dígito más, son **100 veces** más. Si le subo la confianza a 99 %, la campana se abre y también necesito más. Ese es el precio de la precisión.

Y la receta también funciona al revés: si ya hicimos nuestras simulaciones, damos el resultado con su "±". Por ejemplo, con mil puntos nos salió π = 3.15 ± 0.10, o sea: "π está entre 3.05 y 3.25, con 95 % de confianza".

Un detalle: casi nunca sabemos de antemano qué tanto brinca la simulación. Lo que se hace es una corrida de prueba, se mide y con eso se calcula N.

**[→]**

---

## 9 · Ejemplo de la circunferencia

Ese ejemplo de π ± 0.10 no salió de la nada; vamos a verlo en vivo. Es el clásico de clásicos: **estimar π con puntos al azar**.

Tenemos un cuadrado de lado 2 y un círculo de radio 1 adentro. La proporción de área entre los dos es π/4. Entonces, si tiro puntos al azar, la fracción que cae dentro del círculo debería ser más o menos π/4… y si la multiplico por 4, ¡me da π!

**[demo: «+100», «+1 000», y luego «▶ Animar»]** Los azules cayeron dentro, los naranjas fuera. Arriba va la estimación con su ± y abajo cómo va convergiendo. Con mil puntos andamos por 3.1 y pico, y con muchos más ya se acerca bastante a 3.14159.

¿Le atina perfecto? No. Pero fíjense en el número chiquito junto a la estimación: ese es el **±** de la diapositiva anterior. Sabemos *qué tanto* nos podemos equivocar, y conforme agregamos puntos ese ± se va haciendo más chico. Eso es justo el control del error que acabamos de ver.

**[→]**

---

## 10 · ¿El intervalo cumple lo que promete?

Ahora, ese ± promete que acertamos el 95 % de las veces. ¿Cómo sabemos que es cierto? Pues… ¡con Monte Carlo!

Aquí repetimos **100 veces** el experimento que acabamos de ver, estimar π con mil puntos, y para cada uno dibujamos su intervalo de confianza del 95 %. La línea negra es el π real.

Los azules **sí atrapan a π**; los naranjas **fallan**. Y fíjense: fallan más o menos **5 de cada 100**. Justo lo que prometimos.

**[demo: «Repetir 100 experimentos» varias veces]** Cada tanda da un número un poquito distinto, 93, 96, 95… pero el acumulado se va pegando al 95 %.

Y esto es importante porque aclara qué significa "95 % de confianza": **no** es que π tenga 95 % de probabilidad de estar en *este* intervalo. Significa que el **método** atrapa el valor real en 95 de cada 100 veces. O sea, sabemos con qué frecuencia nos equivocamos. Eso es controlar el error.

**[demo opcional: cambiar a 90 % o 99 %]** Con 99 % los intervalos son más anchos y casi nunca fallan; con 90 % son más angostos, pero fallan más. No hay almuerzo gratis.

**[→]**

---

## 11 · Hay de dos sopas

Dejemos π y vamos con otro ejemplo, todavía más sencillo, para comparar los dos caminos: tiramos dos dados. ¿Cuál es la probabilidad de que la suma sea **mayor que 10**?

**Opción 1, la analítica:** hacemos la tablita de 6 por 6. Hay 36 combinaciones y solo 3 suman más de 10: 5-6, 6-5 y 6-6. Entonces es 3/36, o sea **1/12**, más o menos 0.083. Fácil.

**Opción 2, Monte Carlo:** ¡pues tiramos los dados!

**[demo: «Lanzar 1 vez», luego «+100», luego «+10 000»]** Con pocos tiros la estimación anda brincando por todos lados. Pero conforme tiramos más, se va pegando a la línea punteada del 1/12, y la banda azul, que es el intervalo de confianza, se va cerrando.

Aquí el analítico gana, claro. Pero imagínense un problema donde no puedes hacer la tablita. Ahí es donde Monte Carlo brilla.

**[→]**

---

## 12 · En resumen

Y en resumen… *(pausa)* …demostrar todo analíticamente, con pizarrón y teoremas: está bien, respetable, pero no siempre se puede.

**[→]** ¿Lo otro? Tirar los dados diez mil veces y promediar. 😎

Ese es el espíritu de Monte Carlo.

**[→]**

---

## 13 · Genética y estadística

Bueno, ahora sí, ¿para qué queremos esto en nuestro proyecto? Nosotros trabajamos con **MMA, con la UFC**, y nos hicimos varias preguntas:

- ¿Qué tanto depende un peleador de la **suerte** para dedicarse a esto?
- ¿Cómo cambia la dinámica de poder entre divisiones?
- ¿Y por qué las MMA son tan difíciles de predecir con la estadística tradicional?

Para responder parte de esto usamos Monte Carlo. Vamos a ver cómo.

**[→]**

---

## 14 · Cuando no puedes repetir la pelea…

El problema con las peleas es que cada una **pasa una sola vez**. Si el favorito pierde, ¿la casa de apuestas se equivocó o simplemente le tocó mala suerte? Con un solo resultado no lo podemos saber.

Pero la computadora sí puede repetir la pelea. La receta es la misma de siempre:

1. **Modelo del azar:** el favorito gana con probabilidad *p*, que sacamos de la cuota de apertura, ya sin la comisión de la casa.
2. **Lanzar:** sorteamos un número *u* entre 0 y 1. Si sale menor que *p*, gana el favorito; si no, sorpresa.
3. **Repetir y contar.**

Ejemplo real: **Gable Steveson contra Sean Sharaf**. El mercado le daba a Steveson **90.4 %**.

**[demo: «Sortear u» varias veces]** Casi siempre cae en la parte azul y gana Steveson… pero de vez en cuando cae en la parte naranja. Y adivinen qué pasó en la vida real: **ganó Sharaf**.

**[→]**

---

## 15 · Una pelea, muchas veces

Vamos a repetir esa pelea muchas veces. Cada cuadrito es una pelea simulada: azul, gana Steveson; naranja, sorpresa.

Con 500 simulaciones salen unas cuantas sorpresas, y el estimado anda cerca del 9.6 % real. Abajo ven la línea roja brincando al principio y luego metiéndose en el embudo azul. Eso es la Ley de los Grandes Números en vivo.

**[demo: subir a 100,000 simulaciones]** Ahora el error estándar ya es chiquito, de décimas de punto.

¿La conclusión? El KO de Sharaf fue **raro, pero no extraordinario**: más o menos **una de cada diez** peleas así termina en sorpresa. No es que las cuotas estuvieran mal; así es el azar.

*(Opcional: cambiar a Topuria vs. Gaethje u Oliveira para ver otros casos.)*

**[→]**

---

## 16 · Miles de historias alternativas

Ahora la pregunta grande: no una pelea, sino **todas**. ¿Las cuotas le atinan con los favoritos?

Vamos a suponer que sí; esa es nuestra **hipótesis nula**. Con esa idea volvemos a jugar *todas* las peleas de un grupo, cada una con su propia moneda cargada. A cada repetición le llamamos una **historia alternativa** de la UFC.

Aquí estamos viendo el grupo de favoritos que tenían entre **70 y 80 %**, que son 1,234 peleas. En la tabla ven ocho de ellas: su probabilidad, el número aleatorio que salió, qué dijo la simulación y qué pasó de verdad.

Y abajo a la izquierda: en *esta* historia inventada ganaron unos 935 favoritos, pero **en la realidad ganaron 990**. ¿Es suerte o hay algo ahí? Para saberlo… hay que repetir esto miles de veces.

**[→]**

---

## 17 · ¿Aciertan las cuotas?

Y eso hicimos. Cada barra del histograma junta las historias simuladas: si las cuotas fueran perfectas, lo normal sería que ganaran entre unos **884 y 943** favoritos. Esa es la zona sombreada.

¿Y la realidad? **990**. Hasta allá a la derecha, fuera de casi todas las historias. El valor p sale chiquitísimo.

O sea: en ese rango, **los favoritos ganaron más de lo que decían las cuotas**. El mercado los estaba *infravalorando*.

**[demo: cambiar a «50–60 %» o «60–70 %»]** En cambio, en las peleas más parejas la realidad cae justo en medio de la campana. Ahí las cuotas sí le atinan.

**[→]**

---

## 18 · ¿Qué nos dijo Monte Carlo?

Para cerrar, todo junto en una sola gráfica, con 6,376 peleas de 2013 a 2026. La cajita azul es el rango que esperaríamos si las cuotas fueran perfectas, y el punto naranja es lo que pasó de verdad.

- En peleas **parejas, de 50 a 70 %**, el punto cae dentro de la cajita: **las cuotas están bien calibradas**.
- En **favoritos claros, de 70 % para arriba**, el punto se sale por la derecha: estos favoritos ganan **más** de lo que dice el mercado. Con 70–80 % ganaron 80 % de las veces cuando el mercado decía 74 %.
- ¿Y las sorpresas? Existen y son normales. Lo raro no es *una* sorpresa, sino ver **demasiadas o muy pocas**.
- Eso sí, con cautela: estamos haciendo varias pruebas a la vez y usamos cuotas de apertura, no de cierre.

Y esa es la gracia de Monte Carlo: no podemos repetir la historia de la UFC, pero sí podemos simular miles de historias para saber si lo que pasó fue suerte o no.

¡Muchas gracias! ¿Preguntas?
