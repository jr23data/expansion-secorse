import pandas as pd
import pyodbc
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def get_sql_server_driver():
    """Obtiene el driver ODBC más reciente instalado en el sistema para SQL Server"""
    drivers = [driver for driver in pyodbc.drivers() if 'SQL Server' in driver or 'SQL' in driver]
    # Preferir drivers modernos
    modern_drivers = [d for d in drivers if '17' in d or '18' in d or 'Native' in d]
    if modern_drivers:
        return modern_drivers[-1]
    return 'SQL Server' if drivers else None

def run_etl():
    load_dotenv()
    
    server = os.getenv('DB_SERVER', 'localhost')
    db_name = 'SECORSE_Expansion'
    driver = get_sql_server_driver()
    
    if not driver:
        print("Error: No se encontraron drivers ODBC de SQL Server en tu equipo.")
        return
        
    print(f"Iniciando ETL. Conectando a {server} usando el driver: [{driver}]")

    # 1. Crear la base de datos (Requiere autocommit en SQL Server)
    try:
        conn_str = f"Driver={{{driver}}};Server={server};Database=master;Trusted_Connection=yes;"
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Crear base si no existe
        cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{db_name}') CREATE DATABASE {db_name}")
        conn.close()
        print(f"EXITO: Base de datos '{db_name}' validada/creada exitosamente en el servidor.")
    except Exception as e:
        print(f"NOTA al crear base de datos (probablemente ya existe): {e}")

    # 2. Conexión SQLAlchemy para carga masiva
    driver_url = driver.replace(' ', '+')
    engine_url = f"mssql+pyodbc://@{server}/{db_name}?driver={driver_url}&Trusted_Connection=yes"
    engine = create_engine(engine_url, fast_executemany=True)

    # 3. Extracción (Extract) desde el Data Lake simulado (CSVs)
    print("Leyendo datos crudos desde la capa de archivos...")
    sucursales = pd.read_csv('data/raw/sucursales.csv')
    zonas = pd.read_csv('data/raw/zonas_candidatas.csv')
    transacciones = pd.read_csv('data/raw/transacciones.csv')

    # 4. Carga (Load) al Data Warehouse en Modelo Estrella
    print("Cargando tablas Dimensionales y de Hechos en SQL Server...")
    
    # Dimensión Sucursales
    sucursales.to_sql('Dim_Sucursales', engine, if_exists='replace', index=False)
    print("   - Tabla Dim_Sucursales cargada.")
    
    # Dimensión Zonas
    zonas.to_sql('Dim_Zonas', engine, if_exists='replace', index=False)
    print("   - Tabla Dim_Zonas cargada.")
    
    # Hechos Transacciones
    transacciones.to_sql('Fact_Transacciones', engine, if_exists='replace', index=False)
    print("   - Tabla Fact_Transacciones cargada.")

    # 5. Transformación Semántica (SQL Views)
    # Creamos una vista que haga el trabajo de agregación que antes hacíamos en Pandas.
    print("Construyendo Capa Semántica (Vistas) en SQL...")
    with engine.begin() as connection:
        view_sql = """
        CREATE OR ALTER VIEW vw_Features_MachineLearning AS
        SELECT 
            city,
            AVG(avg_monthly_sales) as baseline_city_sales
        FROM Dim_Sucursales
        GROUP BY city;
        """
        connection.execute(text(view_sql))
        
    print("¡Pipeline ETL finalizado con éxito! El Data Warehouse local está listo para ser consumido por el modelo.")

if __name__ == "__main__":
    run_etl()
