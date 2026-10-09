import pandas as pd
import numpy as np
import os

# ==========================================
# 0. DEFINICIÓN DE SUPUESTOS DE NEGOCIO
# ==========================================
AREA_M2 = 100  # Tamaño promedio de una cafetería estándar
CAPEX_POR_M2 = 12000  # MXN (basado en promedios del mercado mexicano)
MARGEN_BRUTO = 0.65  # 65% Post-COGS
COSTOS_OPERATIVOS_FIJOS_PCT = 0.25 # 25% de la venta va a staff y servicios
RAMP_UP_PROMEDIO_ANO1 = 0.75 # (arranca al 50% mes 1, llega al 100% mes 12)
LIMITE_VARIANZA_ZONA = 0.25  # ±25% de ajuste máximo por microlocalización

def run_economic_ranking():
    # 1. Cargar Zonas Candidatas
    zonas = pd.read_csv('data/raw/zonas_candidatas.csv')
    
    # 2. Obtener el Baseline de Ciudad (Conexión Empresarial a SQL Server)
    ventas_ciudad = None
    
    try:
        from sqlalchemy import create_engine
        from dotenv import load_dotenv
        import os
        import pyodbc
        
        load_dotenv()
        server = os.getenv('DB_SERVER', 'localhost')
        
        # Buscar driver dinámico
        drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d or 'SQL' in d]
        modern_drivers = [d for d in drivers if '17' in d or '18' in d or 'Native' in d]
        driver = modern_drivers[-1] if modern_drivers else ('SQL Server' if drivers else None)
        
        if driver:
            driver_url = driver.replace(' ', '+')
            engine_url = f"mssql+pyodbc://@{server}/SECORSE_Expansion?driver={driver_url}&Trusted_Connection=yes"
            engine = create_engine(engine_url)
            
            # El motor de SQL hace el cómputo masivo y nos devuelve solo el agregado
            ventas_ciudad = pd.read_sql("SELECT city, baseline_city_sales FROM vw_Features_MachineLearning", engine)
            print("[EXITO] INFO: Baseline macro extraído exitosamente desde SQL Server (Data Warehouse).")
    except Exception as e:
        print(f"[AVISO] No se pudo conectar a SQL Server ({e}). Fallback a procesamiento en memoria con Pandas.")
        ventas_ciudad = None

    # Fallback (Si SQL Server falla o no está configurado, calculamos en Pandas)
    if ventas_ciudad is None:
        sucursales = pd.read_csv('data/raw/sucursales.csv')
        ventas_ciudad = sucursales.groupby('city')['avg_monthly_sales'].mean().reset_index()
        ventas_ciudad.rename(columns={'avg_monthly_sales': 'baseline_city_sales'}, inplace=True)
        print("[INFO] Baseline macro calculado en memoria desde CSV local.")
    
    # 3. Cruzar zonas candidatas con su baseline de ciudad
    df = zonas.merge(ventas_ciudad, on='city', how='left')
    
    # Si alguna ciudad no tiene historial (ej. no está en sucursales), 
    # imputamos con la media global. (En nuestra data sintética todas cruzan, pero es buena práctica)
    media_nacional = ventas_ciudad['baseline_city_sales'].mean()
    df['baseline_city_sales'] = df['baseline_city_sales'].fillna(media_nacional)
    
    # 4. Calcular Índice de Microlocalización (ZAI - Zone Attractiveness Index)
    # Normalizamos (Min-Max) las variables clave de la zona para crear un índice compuesto
    # Población (+) y Tráfico (+) suman, Competencia (-) resta.
    
    for col in ['population_1km', 'foot_traffic_index', 'cafes_1km']:
        df[f'{col}_norm'] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        
    # Índice de -1 a 1
    df['zone_score'] = (
        (df['population_1km_norm'] * 0.4) + 
        (df['foot_traffic_index_norm'] * 0.4) - 
        (df['cafes_1km_norm'] * 0.2)
    )
    # Reescalar al límite de negocio: de -LIMITE_VARIANZA_ZONA a +LIMITE_VARIANZA_ZONA
    df['zone_adjustment'] = df['zone_score'].apply(lambda x: (x * 2 - 1) * LIMITE_VARIANZA_ZONA)
    
    # 5. Penalización por Canibalización (Analogía con cruce de carteras)
    # Si hay una tienda a menos de 2km, penalizamos la venta esperada.
    df['cannibalization_penalty'] = df['distance_nearest_store_km'].apply(
        lambda x: 0.15 if x <= 1.0 else (0.05 if x <= 2.0 else 0)
    )
    
    # 6. Proyección de Ventas (Expected Revenue)
    df['ventas_potenciales_mensuales'] = df['baseline_city_sales'] * (1 + df['zone_adjustment']) * (1 - df['cannibalization_penalty'])
    
    # 7. Modelo Económico (El ROI)
    df['capex_total'] = AREA_M2 * CAPEX_POR_M2
    df['renta_mensual'] = df['avg_rent_mxn_m2'] * AREA_M2
    
    # VNE: Flujo de caja neto operativo estabilizado
    # Ingreso * Margen Bruto - Costos Operativos Fijos - Renta Mensual
    df['flujo_operativo_bruto'] = df['ventas_potenciales_mensuales'] * MARGEN_BRUTO
    df['costos_operativos'] = df['ventas_potenciales_mensuales'] * COSTOS_OPERATIVOS_FIJOS_PCT
    
    df['vne_mensual_estabilizado'] = df['flujo_operativo_bruto'] - df['costos_operativos'] - df['renta_mensual']
    
    # Payback considerando Ramp-up el primer año
    df['flujo_ano_1'] = (df['vne_mensual_estabilizado'] * RAMP_UP_PROMEDIO_ANO1) * 12
    # El resto del capex por recuperar después del año 1
    df['capex_residual'] = df['capex_total'] - df['flujo_ano_1']
    
    # Meses adicionales requeridos después del año 1
    df['meses_adicionales_payback'] = df['capex_residual'] / df['vne_mensual_estabilizado']
    df['payback_months'] = 12 + df['meses_adicionales_payback']
    
    # ROI a 3 años
    df['flujo_3_anos'] = df['flujo_ano_1'] + (df['vne_mensual_estabilizado'] * 24)
    df['roi_3_anos_pct'] = ((df['flujo_3_anos'] - df['capex_total']) / df['capex_total']) * 100
    
    # 8. Ordenar y Seleccionar Top 5
    df_ranking = df.sort_values(by='vne_mensual_estabilizado', ascending=False).head(5)
    
    print("\n" + "="*50)
    print("TOP 5 ZONAS PARA EXPANSIÓN (BASADO EN VNE)")
    print("="*50)
    for index, row in df_ranking.iterrows():
        print(f"[{row['zone_id']}] {row['city']}")
        print(f"  Ventas Base (Ciudad)   : ${row['baseline_city_sales']:,.2f}")
        print(f"  Ajuste Zona (Index)    : {row['zone_adjustment']*100:+.1f}%")
        print(f"  Ventas Proyectadas     : ${row['ventas_potenciales_mensuales']:,.2f}")
        print(f"  VNE (Utilidad Mensual) : ${row['vne_mensual_estabilizado']:,.2f}")
        print(f"  Renta Mensual          : ${row['renta_mensual']:,.2f}")
        print(f"  Payback (Meses)        : {row['payback_months']:.1f} meses")
        print(f"  ROI 3 Años             : {row['roi_3_anos_pct']:.1f}%")
        print("-" * 50)
        
    # Guardar resultados
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/ranking_zonas_candidatas.csv', index=False)

if __name__ == '__main__':
    run_economic_ranking()
