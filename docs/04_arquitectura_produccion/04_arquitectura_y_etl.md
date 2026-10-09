# Arquitectura de Datos y Producción

Este documento detalla la estructura física y lógica que soporta el sistema de evaluación de sucursales, diseñado nativamente para el ecosistema Microsoft.

## 1. Data Engineering (ETL y DWH)
No operamos sobre archivos planos. El proyecto incluye un pipeline automatizado `00_etl_sqlserver.py` desarrollado con **SQLAlchemy** y **pyodbc** que:
1. Extrae los datos desde la capa cruda.
2. Construye un esquema dimensional (Modelo Estrella) en **SQL Server**.
3. Implementa una Capa Semántica a través de una `VIEW` precalculada, delegando el cómputo pesado al motor de base de datos en lugar de sobrecargar la RAM en Python.

## 2. MLOps y Resiliencia Operativa (Fallback)
El código de inferencia en Python (`05_economia_ranking.py`) está dotado con un mecanismo de resiliencia empresarial:
* **Fase Primaria:** Consume el Baseline y los features procesados directamente desde SQL Server.
* **Fallback de Emergencia:** Si la conexión de red o la base de datos presenta intermitencias (Timeout), el código atrapa la excepción y conmuta instantáneamente a procesamiento en memoria utilizando Pandas, garantizando la continuidad del negocio y el flujo ininterrumpido del algoritmo predictivo.

## 3. Integración con BI
Al estar cimentado sobre SQL Server, el consumo de la solución se conecta de manera nativa a **Power BI** vía *DirectQuery*, eliminando la necesidad de programar APIs complejas de Python intermedias.
