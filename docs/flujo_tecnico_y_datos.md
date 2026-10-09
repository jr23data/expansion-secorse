# Diccionario de Datos y Flujo del Código (Pipeline)
Este documento explica la estructura técnica del proyecto de Expansión SECORSE para otorgar contexto a herramientas de IA generativa.

## 1. Diccionario de Datos (Archivos Crudos / SQL Server)
* **sucursales.csv**: Contiene el histórico de 40 tiendas activas.
  - `store_id`: ID único.
  - `city`: Ciudad de operación (Monterrey, Mérida, Puebla, Querétaro, Cancún).
  - `area_m2`: Tamaño del local.
  - `avg_monthly_sales`: **(Target Continuo)** Ventas reales mensuales.
  - `nearby_competitors`, `parking_spaces`, `distance_to_nearest_store_km`: Features del local.
* **transacciones.csv**: Muestra transaccional temporal de los tickets (usado para graficar estacionalidad y ramp-up).
* **zonas_candidatas.csv**: Las 20 ubicaciones nuevas a evaluar. No tienen ventas, tienen variables del entorno geográfico (DENUE/INEGI) como `population_1km`, `foot_traffic_index`, `cafes_1km`.

## 2. Flujo del Código (Arquitectura)
1. **00_etl_sqlserver.py (Data Engineering):** Lee los 3 CSVs usando Pandas y los inyecta en una base de datos local de SQL Server mediante `pyodbc` y `SQLAlchemy`. Crea un esquema de estrella y genera una `VIEW` (vw_Features_MachineLearning) que calcula el promedio de ventas por ciudad en el motor SQL.
2. **05_economia_ranking.py (Data Science & Business):** 
   - Lee el Baseline de ciudad desde la vista de SQL Server (con un Fallback a Pandas si falla la conexión).
   - Aplica la lógica de Negocio: ZAI (Ajuste por zona topado a ±25%) y Penalización por canibalización.
   - Entrena un modelo de **Regresión Logística** con las tiendas históricas (Features: Competidores y Distancia) para calcular la *Probabilidad de Éxito* de las nuevas zonas.
   - Calcula el ROI, Payback y el **VNE Ajustado por Riesgo**. Ordena el Top 5.
3. **06_generar_presentacion.py (Automatización):** Usa la librería `python-pptx` para volcar los resultados en presentaciones ejecutivas.
4. **07_generar_graficas.py (EDA & ML Evaluation):** Usa `seaborn` para exportar gráficas a la carpeta `entregables/graficas/`. Genera boxplots, límites de control, Matriz de Confusión y Curva ROC.
