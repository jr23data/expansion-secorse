CASO GERENTE DE DATA SCIENCE – CAFETERÍA

Archivos:
- sucursales.csv
- desempeno_sucursales.csv
- zonas_candidatas.csv
- transacciones.csv
- diccionario_datos.csv

Los datos son sintéticos y fueron creados exclusivamente para el ejercicio.
Se incluyeron algunos valores faltantes de manera intencional para evaluar la preparación y calidad de datos.

Relaciones principales:
- sucursales.store_id = desempeno_sucursales.store_id
- sucursales.store_id = transacciones.store_id
- zonas_candidatas.nearest_store_id = sucursales.store_id

Las 20 zonas candidatas representan alternativas para una nueva sucursal.

No se proporciona una variable objetivo explícita. El candidato debe definir qué significa
"potencial de una zona" y justificar la metodología/modelo que utilizaría.

El candidato puede complementar los datos con fuentes públicas si considera que aportan valor.
