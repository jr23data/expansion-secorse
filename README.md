# Caso Práctico: Expansión de Sucursales (Data Science)

Repositorio con la solución técnica y de negocio para la evaluación de zonas candidatas de expansión. Este proyecto implementa un modelo analítico y financiero diseñado para optimizar el **Valor Neto Esperado (VNE)** y minimizar el riesgo de inversión (Payback).

## 📌 Enfoque Estratégico (Filosofía SECORSE)

El reto de expansión se abordó con la misma rigurosidad que la optimización de carteras de cobranza masiva:
1. **Capacity Planning & Ramp-up:** Proyección operativa con una curva de maduración de 12 meses (arranque al 50%, estabilización al 100%).
2. **Modelo Champion/Challenger:** Uso de la macrolocalización (ciudad) como base ancla (*Champion*), ajustado dinámicamente por la microlocalización (zona) mediante un índice compuesto (*Challenger*).
3. **Maximización del VNE:** Integración de proyecciones de ventas con variables financieras duras (Capex, Opex, Renta y Canibalización).

## 🧠 Arquitectura del Modelo (Híbrido de 2 Niveles)

Debido a que el histórico de sucursales no contaba con coordenadas exactas, se descartó un modelo espacial tradicional por riesgo de *overfitting* geográfico. En su lugar, se diseñó un modelo de dos capas:

* **Nivel 1 (Baseline Ciudad):** Establece el ancla de ingresos esperados utilizando el volumen histórico consolidado y validado a nivel ciudad.
* **Nivel 2 (ZAI - Zone Attractiveness Index):** Ajusta la proyección base hasta un ±25% evaluando variables micro-espaciales de la zona candidata:
  * Tráfico Peatonal (+)
  * Población en radio de 1km (+)
  * Saturación Comercial / Competencia (-)
* **Penalización por Canibalización:** Descuento directo sobre ventas proyectadas si existe otra sucursal operando a menos de 2km de distancia en la misma plaza.

## 💼 Supuestos Económicos

El modelo económico que dictamina el Ranking final de zonas se basó en los siguientes parámetros de mercado (Formato Barra/Kiosco):
* **Capex (Habilitación):** \$12,000 MXN por m² (Formato estándar estimado: 100 m² = \$1.2M MXN).
* **Rentabilidad:** Margen Bruto del 65% (Post-COGS) y Gastos Operativos Fijos del 25%.
* **KPI Principal:** Período de recuperación de inversión (*Payback*) menor a 24 meses.

## 📂 Estructura del Proyecto

* `data/` : Contiene los datasets crudos y procesados (Censo, DENUE, Transacciones).
* `docs/` : Documentación técnica, metodológica y guiones de presentación directiva.
* `scripts/` : Pipelines de Machine Learning, EDA, y simuladores económicos (`05_economia_ranking.py`).
* `entregables/` : Presentaciones ejecutivas `.pptx` generadas automáticamente por el pipeline.

## 🛠 Stack Tecnológico y MLOps

* **Lenguaje:** Python 3 (Pandas, Numpy, Scikit-Learn)
* **Automatización Ejecutiva:** `python-pptx` para la generación dinámica de entregables.
* **Proyección a Producción (Azure):** Código estructurado listo para ser orquestado vía **MLflow** y contenedorizado mediante **Docker** para consumo en tableros de Power BI vía APIs REST (FastAPI).

---
*Elaborado para la Gerencia de Data Science.*
