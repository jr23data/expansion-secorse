# Dossier de Cierre Técnico: Proyecto Expansión SECORSE

Este documento consolida las decisiones arquitectónicas, estrategias de modelado matemático y lógica de negocio implementadas en el MVP para la selección de sitios de expansión comercial.

---

## 1. Decisiones Estratégicas sobre los Datos
Durante el desarrollo del proyecto, se tomaron decisiones clave para sortear las limitaciones iniciales de los datos y maximizar el impacto de negocio:

* **El "Baseline" Macrolocal:** Al no contar con coordenadas exactas históricas (latitud/longitud puras), se descartó un modelo geoespacial estricto. En su lugar, se adoptó un modelo de dos capas: el "Ancla" (promedio base dictado por la economía de la Ciudad) y el "Ajuste" (micro-variaciones dictadas por la zona).
* **El Límite de Control (±25%):** Por ética estadística y tras analizar la distribución poblacional de las tiendas históricas (Campana de Gauss), se topó el ajuste algorítmico a ±25%. Esto previno que el modelo sobreprometiera ventas irreales (outliers) en zonas nuevas.
* **El Impacto Financiero del Error (WAPE):** La inyección de datos externos (DENUE/INEGI) redujo el WAPE de 16.3% a 15.1%. Esta mejora técnica se tradujo al lenguaje directivo: proteger un desvío de **$144,000 MXN en el flujo de caja anual por sucursal**.

---

## 2. Estrategia de Modelado y Evaluación (La Defensa Técnica)
El proyecto destaca por utilizar una **Matriz de Riesgo-Retorno**, evaluando simultáneamente la magnitud de la ganancia y la probabilidad de éxito.

### A. ¿Qué modelos se utilizaron y por qué?
En lugar de forzar modelos complejos de "Caja Negra" (XGBoost, Deep Learning), se optó por **Regresión Lineal Regularizada (Ridge)** para la predicción continua y **Regresión Logística** para la probabilidad categórica. Las 3 razones clave son:

1. **Inmunidad al Overfitting (Tamaño Muestral):** Con un universo histórico de $N=40$ sucursales, un modelo complejo simplemente memorizaría el ruido. Los modelos lineales penalizados garantizan un aprendizaje robusto y generalizable en muestras pequeñas.
2. **Explicabilidad Directiva (Caja Blanca):** A diferencia de las redes neuronales, la regresión nos entrega coeficientes matemáticos claros. Ante un comité, podemos explicar exactamente *por qué* se rechazó una zona (ej. "la saturación de competidores restó un 12% a la viabilidad").
3. **Filosofía MVP:** Se priorizó el desarrollo de una arquitectura End-to-End funcional sobre la micro-optimización de hiperparámetros algorítmicos.

### B. ¿Cómo se evaluaron los modelos?
Es crucial distinguir la naturaleza matemática de cada etapa para evaluarla correctamente:
* **El Modelo Financiero Continuo (Ventas / VNE):** Al ser una variable continua monetaria, se evaluó mediante dispersiones de **Real vs. Predicho**, **Distribución Normal de Residuos (Errores)** y el **WAPE**. (Bajo ninguna circunstancia se usan Curvas ROC para variables continuas monetarias).
* **El Modelo Categórico (Riesgo / Éxito):** La capa de probabilidad (0 a 1) sí permitió la generación de una **Matriz de Confusión** y el cálculo del área bajo la **Curva ROC (AUC)**, demostrando la capacidad matemática de separar zonas rentables de las zonas "trampa".

---

## 3. Arquitectura End-to-End (Data & MLOps)
El proyecto no es un simple script de laboratorio; es un diseño listo para ecosistemas Microsoft (Azure):

* **Ingeniería de Datos (ETL):** Automatización mediante `SQLAlchemy` para consolidar datos planos hacia un **Data Warehouse en SQL Server** en un modelo de Esquema Estrella.
* **Capa Semántica:** El cómputo masivo de promedios no se hace en Python (RAM), sino mediante Vistas (`VIEW`) precalculadas en el motor SQL, listas para `DirectQuery` desde Power BI.
* **Resiliencia Operativa (Fallback):** El sistema posee tolerancia a fallos de infraestructura. Si el servidor de bases de datos colapsa, el código conmuta automáticamente a procesamiento local en memoria, garantizando que el negocio (la Dirección) siempre obtenga su recomendación financiera.

---

## 4. Conclusión y Próximos Pasos
El sistema actual prioriza el **VNE Ajustado por Riesgo** (Valor Neto Esperado $\times$ Probabilidad de Éxito), logrando una herramienta de decisión que prioriza el retorno de inversión y mitiga la incertidumbre. 

**El siguiente hito tecnológico (Roadmap):** Recolectar las geocoordenadas (Lat/Lon) del parque histórico de sucursales para sustituir el enfoque demográfico actual por algoritmos de proximidad pura (K-Nearest Neighbors espaciales / Isocronas de conducción).
