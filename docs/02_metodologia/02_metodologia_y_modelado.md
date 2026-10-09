# Metodología y Modelado Estadístico

Este documento detalla el enfoque matemático aplicado para rankear las zonas de expansión de SECORSE. 
A diferencia de los enfoques tradicionales que evalúan rentabilidad absoluta, se implementó una **Matriz de Riesgo-Retorno** soportada por dos algoritmos complementarios.

## 1. El Retorno: Valor Neto Esperado (Regresión)
Para estimar las ventas potenciales, se definió un algoritmo Heurístico validado mediante **Regresión Lineal Regularizada (Ridge)**. 
- **¿Por qué Ridge?** Debido al reducido tamaño de la muestra ($N=40$ sucursales), algoritmos complejos de ensamble o Deep Learning sufrirían de sobreajuste masivo (*Overfitting*). Una regularización lineal (Ridge/Lasso) permite controlar la varianza y mantener los coeficientes explicables.
- **Métrica de evaluación:** Se utilizó el **WAPE** (Weighted Absolute Percentage Error), logrando reducirlo a 15.1% gracias a la inyección de fuentes externas (DENUE/INEGI).

## 2. El Riesgo: Probabilidad de Éxito (Clasificación)
Para evitar inversiones ciegas, se diseñó un target histórico de éxito: `ventas_promedio > mediana_nacional = 1`.
- **Modelo:** **Regresión Logística** con pesos balanceados.
- **¿Por qué Logística?** Al ser un modelo paramétrico de "Caja Blanca", permite obtener probabilidades continuas (.predict_proba) y explicar matemáticamente por qué una zona se penaliza.
- **Métrica de evaluación:** Área bajo la curva **ROC (AUC)** y **Matriz de Confusión**.

## 3. Síntesis (La Métrica Estrella)
Las proyecciones se unifican bajo la siguiente fórmula rectora del proyecto:
`VNE Ajustado por Riesgo = Valor Neto Esperado (flujo) × Probabilidad de Éxito`
