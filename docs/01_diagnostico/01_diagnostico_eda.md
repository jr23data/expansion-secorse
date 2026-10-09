# Etapa 01 · Diagnóstico y EDA

> **Para ti (preparación):** este documento explica qué hicimos, **por qué** lo hicimos y qué encontramos. Reproducible con `python scripts/01_eda.py`. Tablas en `reports/tables/`, figuras en `reports/figures/`.

## 1. Por qué empezamos aquí
Antes de modelar hay que saber **qué decisión se toma, con qué datos y qué trampas tienen**. En cobranza es igual: antes de un modelo de propensión se audita cartera, calidad y *cutoff*. Un diagnóstico sólido es lo que diferencia a un gerente de un analista que corre un algoritmo.

## 2. Qué hay en la base (inventario)

| Tabla | Filas | Granularidad | Uso previsto |
|---|---:|---|---|
| `sucursales` | 40 | sucursal | Unidad de aprendizaje (n pequeño) |
| `desempeno_sucursales` | 1,200 | sucursal-mes (ene-2024 a jun-2026, 30 meses × 40) | Target y estacionalidad |
| `transacciones` | 120,000 | ticket (≈3,000 por sucursal) | Mezcla de canal / categoría / pago |
| `zonas_candidatas` | 20 | zona | Objeto a puntuar |

## 3. Hallazgos de calidad de datos (y qué decisión tomamos)

| # | Hallazgo | Evidencia | Decisión |
|---|---|---|---|
| 1 | **Nulos pequeños e intencionales** | `sales_mxn` 12 (1%), `product_category` 960 (0.8%), `area_m2` 1 (2.5%), `avg_income_index` 1 (zona Z16, 5%) | Ventas: imputar con la mediana de la propia sucursal por mes del año; área: mediana; ingreso Z16: mediana de la ciudad + bandera. Los nulos de categoría son aleatorios (≈0.8% en todos los canales) → "Sin dato". |
| 2 | **Ventas antes de la apertura** | 24 meses en las sucursales 18 y 29 (`opening_year`=2025 pero hay ventas desde 2024) = 1.75% de las ventas | Se trata como **error de `opening_year`**: las sucursales se consideran abiertas desde su primer mes con ventas. Se documenta. No se descartan datos. |
| 3 | **Coherencia interna de ventas** | `ventas = tickets × ticket promedio` con error mediano 0.01%; `avg_monthly_sales` coincide con el promedio mensual (dif. 0.08%) | Los datos son internamente consistentes. Se usa `desempeno` como fuente de verdad. |
| 4 | **`nearest_store_id` no es confiable** | En **19 de 20** zonas la "sucursal más cercana" está en **otra ciudad** (ej. Z03 en Mérida, a 1.24 km de una sucursal de Puebla) | **No se usa la llave literal.** Para canibalización se usa la distancia declarada (`distance_nearest_store_km`) con las ventas de las sucursales **de la misma ciudad**. Se declara como limitación. *(Es la clase de hallazgo que muestra criterio.)* |
| 5 | **Ciudades desbalanceadas** | Guadalajara: 7 sucursales y **0 zonas**. Mérida: 2 sucursales y 3 zonas. Puebla: 4 sucursales y 6 zonas | Cuidado con extrapolar. Guadalajara aporta a lo "global" pero no se puntúa. |
| 6 | **Escala de transacciones** | ≈3,000 tx por sucursal vs ≈7,500 tickets/mes reales | Son una **muestra**: sirve para mezcla, no para volumen. |
| 7 | **Duplicados y valores inválidos** | 0 `transaction_id` repetidos, 0 tickets ≤ 0 | Sin acciones. |
| 8 | **Zonas con más trabajadores que población** | 4 zonas (`workers_1km` > `population_1km`) | Plausible en zonas de oficinas (población diurna vs residente). Se conserva y se documenta. |
| 9 | **`zone_type` vs densidades** | Z14 y Z19 (Oficinas) con densidad de oficinas baja; Z17 (Universitaria) con densidad universitaria baja | Las **etiquetas no son confiables por sí solas**: pesan más las métricas continuas de densidad. Argumento para no segmentar solo por `zone_type`. |

## 4. Hallazgos del negocio (lo que cuenta la base)

### 4.1 La red está estancada, no crece
- Ventas ene–jun: 2024 = \$222.4 M; 2025 = \$222.6 M (**+0.08%**); 2026 = \$218.5 M (**−1.8%**).
- Pendiente anual por sucursal ≈ −0.2%.
- **Lectura:** el crecimiento no vendrá de la inercia. Una apertura debe justificarse con un caso de **valor incremental**, no con "el negocio va bien". Esto da un argumento de portada.

### 4.2 Hay estacionalidad clara
Índice estacional (1.00 = promedio): pico mar–may (**1.08–1.10**), valle sep–nov (**0.91**).
- **Implicación 1:** la "venta madura" debe calcularse sobre **12 meses completos** para no sesgarla.
- **Implicación 2:** si la nueva sucursal abre en septiembre, el ramp-up sale peor. Recomendación de **fecha de apertura**: arrancar en febrero–marzo.

### 4.3 La dispersión entre sucursales es real y se explica poco con lo disponible
- Ventas 12 meses: CV entre sucursales 0.21; variación mensual dentro de cada sucursal 0.10 (**la diferencia entre tiendas es "estructural"**, no ruido).
- **Ciudad pesa** (ANOVA p=0.004; Kruskal p=0.006): Puebla ≈ \$1.09 M/mes, León \$0.99 M, Querétaro \$0.96 M, Monterrey \$0.93 M, Mérida \$0.91 M, Guadalajara \$0.79 M, Oaxaca \$0.76 M, **CDMX \$0.69 M**.
- **Tipo de zona NO es significativo** (p=0.34): Oficinas \$1.00 M, Comercial \$0.92 M, Mixta \$0.88 M, Residencial \$0.82 M, Universitaria \$0.82 M, pero con mucha varianza interna.
- Correlaciones con ventas: área 0.17, competidores 0.19 (positiva: más competencia donde hay más demanda, **ojo con la causalidad**), estacionamiento 0.00, distancia a otra sucursal −0.01, ticket promedio −0.02.
- **Lectura:** con lo que traen las sucursales hay poca señal fuera de la ciudad. Es exactamente lo que justifica **agregar fuentes externas** (Versión B): la brecha de variables es el cuello de botella.

### 4.4 El ticket y la mezcla casi no varían (dato sintético)
- Ticket promedio ≈ \$166.6, sin diferencia por canal, categoría ni tipo de zona.
- Mezcla estable: Mostrador 67%, App 20%, Delivery 13%; Café 28%, Alimento 22%, Panadería 18%, Bebida fría 16%.
- **Lectura:** la mezcla no distingue zonas. El **volumen de tickets** es lo que mueve las ventas. Por eso el modelo se concentra en **tráfico/demanda**, y no en el ticket.
- Nota honesta: en datos reales sí varían. Lo declaramos como característica del dataset sintético.

### 4.5 Las zonas candidatas
- Muy distintas entre sí (población 14 mil a 66 mil; renta \$216 a \$816/m²; tráfico peatonal 0.26 a 0.99).
- Correlaciones relevantes: ingreso–renta 0.68; densidad comercial–restaurantes 0.71; distancia–restaurantes −0.52. Hay **multicolinealidad moderada** → regularización y reducción (PCA) tiene sentido.
- Puebla concentra 6 de las 20 zonas (30%), y 7 de 20 son de oficinas.
- Zonas a menos de 2 km de otra sucursal (riesgo de canibalización): Z03, Z05, Z18, Z19, Z20.

## 5. Implicaciones para el diseño de la solución
1. **No hay variable objetivo predefinida** -> Se crearon dos: Valor Neto Esperado (Regresi�n) y Probabilidad de �xito (Clasificaci�n). Todo consolidado en SQL Server. → definimos *Valor Neto Esperado* (ver etapa 02/03).
2. **n=40**, señal débil → modelos simples, regularizados, validación honesta y **mostrar la incertidumbre**.
3. **Brecha de variables** (entorno solo en zonas) → la Versión B con INEGI se justifica con evidencia.
4. **Canibalización** debe modelarse con cuidado por el problema de `nearest_store_id`.
5. **Ramp-up y fecha de apertura** importan por la estacionalidad.
6. Un **mensaje ejecutivo** que sale solo de este análisis: *"La red está plana (−1.8% en 2026); el modelo estima dónde una nueva tienda agrega valor incremental y cuánto riesgo implica."*

## 6. Posibles preguntas del Comité (y respuestas)
- **¿Por qué no usaste el `nearest_store_id`?** Porque en 19 de 20 zonas apunta a otra ciudad; usarlo habría producido canibalización absurda. Se validó la llave contra la ciudad y se corrigió el criterio.
- **¿Por qué el tipo de zona no es suficiente?** No es estadísticamente significativo (p=0.34) y hay zonas mal etiquetadas respecto a sus densidades.
- **¿Qué tanto confías en los datos?** Son consistentes internamente (ventas = tickets × ticket promedio) y con pocos nulos; las inconsistencias detectadas están documentadas con su tratamiento.
- **¿Por qué el negocio está plano y abrimos?** Porque la apertura debe medirse por **valor incremental neto de canibalización**, no por crecimiento histórico.

## 7. Conexión con cobranza (tu sello)
| Aquí | En SECORSE |
|---|---|
| Auditar `nearest_store_id` | Auditar la llave cuenta-cliente antes de cualquier modelo |
| Ventas pre-apertura | Pagos con fecha anterior a la asignación de la cuenta (leakage) |
| Estacionalidad | Estacionalidad de pago (quincenas, aguinaldo, fin de mes) |
| Muestra de transacciones ≠ universo | Muestra de gestiones ≠ universo de cartera |
| n=40 → incertidumbre explícita | Segmentos de cartera pequeños → intervalos de predicción |

## 8. Entregables de esta etapa
- `scripts/01_eda.py` · `reports/tables/*.csv` · `reports/figures/01_*.png`, `02_*.png`
