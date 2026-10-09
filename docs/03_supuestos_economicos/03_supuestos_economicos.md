# Supuestos Económicos y Financieros

Para traducir las proyecciones algorítmicas (Machine Learning) al lenguaje de negocio (Finanzas y ROI), el modelo incorpora una capa de modelado económico que rige la viabilidad de cada zona. Estos son los supuestos estructurales utilizados en el simulador:

## 1. Inversión Inicial (CAPEX)
* **Tamaño del Local (Área):** Se asume un estándar operativo de `100 m²` por sucursal.
* **Costo de Acondicionamiento:** Se estimó en un rango de mercado de \$8,000 a \$15,000 MXN por m². Se tomó un enfoque conservador de **\$12,000 MXN por m²**.
* **CAPEX Total Proyectado:** \$1,200,000 MXN por apertura.

## 2. Estructura de Costos Operativos (OPEX) y Margen
* **Margen Bruto:** Se asume un **65%** sobre las ventas proyectadas.
* **Costos Operativos Fijos:** Se asume un **25%** sobre las ventas proyectadas (servicios, nómina base).
* **Renta:** Dinámica, calculada a partir del *average_rent_mxn_m2* de la zona objetivo multiplicado por los 100 m² de la sucursal.

## 3. Comportamiento Financiero y Maduración (Ramp-up)
Ningún negocio nuevo vende a su máxima capacidad el día uno. Para que el modelo de "Payback" sea realista, se aplicó una curva de maduración:
* **Mes 1:** La sucursal abre operando al **50%** de su potencial.
* **Mes 12:** La sucursal alcanza el **100%** de estabilización.
* **Flujo Año 1:** En consecuencia, el primer año operativo promedia un **75%** del flujo de caja esperado. Este efecto retrasa ligeramente el retorno de inversión, otorgando una estimación mucho más realista para los directivos.

## 4. Métricas de Evaluación
1. **VNE (Valor Neto Esperado):** Utilidad mensual proyectada tras descontar la renta y los costos fijos (basado en el modelo de ventas macrolocal y ZAI).
2. **Payback (Meses):** Tiempo requerido para recuperar los \$1.2 MDP del CAPEX considerando el Ramp-up. (La meta directiva exige < 24 meses).
3. **ROI a 3 años:** Retorno de inversión porcentual proyectado tras recuperar el flujo estabilizado durante 36 meses.
