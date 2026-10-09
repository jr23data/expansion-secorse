"""Etapa 01 - Diagnostico / EDA de los datos del ejercicio.
Genera tablas y figuras en reports/ e imprime hallazgos."""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FIG = ROOT / "reports" / "figures"; TAB = ROOT / "reports" / "tables"
FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)

s = pd.read_csv(RAW / "sucursales.csv"); p = pd.read_csv(RAW / "desempeno_sucursales.csv", parse_dates=["month"])
t = pd.read_csv(RAW / "transacciones.csv", parse_dates=["transaction_date"]); z = pd.read_csv(RAW / "zonas_candidatas.csv")

print("== SHAPES", s.shape, p.shape, t.shape, z.shape)
# --- calidad
q = []
for n, df in [("sucursales", s), ("desempeno", p), ("transacciones", t), ("zonas", z)]:
    nn = df.isna().sum(); nn = nn[nn > 0]
    for c, v in nn.items(): q.append((n, c, int(v), round(v / len(df) * 100, 2)))
q = pd.DataFrame(q, columns=["tabla", "campo", "nulos", "pct"]); q.to_csv(TAB / "calidad_nulos.csv", index=False); print(q)

a = p.merge(s[["store_id", "opening_year"]], on="store_id")
pre = a[a.month.dt.year < a.opening_year]
print("\nmeses con ventas ANTES de opening_year:", len(pre), "tiendas:", sorted(pre.store_id.unique()))
print(" - opening_year de esas tiendas:", s[s.store_id.isin(pre.store_id)].opening_year.value_counts().to_dict())
print(" - pct de ventas totales en esas filas:", round(pre.sales_mxn.sum() / p.sales_mxn.sum() * 100, 2))

# consistencia sales = tickets*avg_ticket
chk = (p.tickets * p.avg_ticket_mxn - p.sales_mxn).abs() / p.sales_mxn
print("\nconsistencia sales vs tickets*avg_ticket: mediana err", round(chk.median(), 4), " p95", round(chk.quantile(.95), 4))
# consistencia sucursales.avg_monthly_sales vs desempeno
m = p.groupby("store_id").sales_mxn.mean().rename("m_perf")
cc = s.merge(m, on="store_id"); print("corr avg_monthly_sales vs promedio desempeno:", round(cc[["avg_monthly_sales", "m_perf"]].corr().iloc[0, 1], 4),
      " dif rel media", round(((cc.avg_monthly_sales - cc.m_perf).abs() / cc.m_perf).mean(), 4))

# duplicados transaccion, outliers
print("\ndup transaction_id:", t.transaction_id.duplicated().sum(), " ticket<=0:", (t.ticket_mxn <= 0).sum())
q99 = t.ticket_mxn.quantile([.5, .95, .99, .999]).round(1).to_dict(); print("quantiles ticket:", q99)
print("nulos categoria por tienda (max):", t[t.product_category.isna()].groupby("store_id").size().max(),
      " - son aleatorios? ->", t.assign(n=t.product_category.isna()).groupby("channel").n.mean().round(4).to_dict())

# --- tendencia y estacionalidad
ts = p.groupby("month").sales_mxn.sum()
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ts.plot(ax=ax[0], color="#1f4e79"); ax[0].set_title("Ventas totales red (MXN) por mes")
seas = p.assign(mes=p.month.dt.month).groupby("mes").sales_mxn.mean()
seas.plot.bar(ax=ax[1], color="#c55a11"); ax[1].set_title("Ventas promedio por sucursal segun mes")
plt.tight_layout(); plt.savefig(FIG / "01_tendencia_estacionalidad.png", dpi=140); plt.close()
yoy = p.assign(y=p.month.dt.year, mo=p.month.dt.month)
h1 = yoy[yoy.mo <= 6].groupby("y").sales_mxn.sum(); print("\nventas ene-jun por anio:", h1.round(0).to_dict(), " crec 25 vs 24:", round(h1[2025] / h1[2024] - 1, 4), " 26 vs 25:", round(h1[2026] / h1[2025] - 1, 4))
sidx = (seas / seas.mean()).round(3); sidx.to_csv(TAB / "indice_estacional.csv"); print("indice estacional:", sidx.to_dict())

# tendencia por tienda (pendiente)
sl = {}
for sid, g in p.dropna(subset=["sales_mxn"]).groupby("store_id"):
    x = np.arange(len(g)); sl[sid] = np.polyfit(x, g.sales_mxn / g.sales_mxn.mean(), 1)[0] * 12
sl = pd.Series(sl); print("pendiente anual relativa tienda: media", round(sl.mean(), 4), " min", round(sl.min(), 3), " max", round(sl.max(), 3))

# --- dispersion entre sucursales
last12 = p[p.month >= "2025-07-01"].groupby("store_id").sales_mxn.mean().rename("ventas12m")
s2 = s.merge(last12, on="store_id")
s2["cv_mensual"] = s2.store_id.map(p.groupby("store_id").sales_mxn.agg(lambda x: x.std() / x.mean()))
print("\nCV ventas entre sucursales:", round(s2.ventas12m.std() / s2.ventas12m.mean(), 3), " CV mensual medio intra-tienda:", round(s2.cv_mensual.mean(), 3))
print(s2.groupby("zone_type").ventas12m.agg(["count", "mean", "std"]).round(0))
print(s2.groupby("city").ventas12m.agg(["count", "mean", "std"]).round(0))
print("corr con ventas12m:", s2[["ventas12m", "area_m2", "parking_spaces", "nearby_competitors", "distance_to_nearest_store_km", "opening_year", "avg_ticket"]].corr()["ventas12m"].round(2).to_dict())
# ventas por m2
s2["ventas_m2"] = s2.ventas12m / s2.area_m2
print("ventas/m2:", s2.ventas_m2.describe().round(0).to_dict())
# anova rapido
from scipy import stats
for col in ["city", "zone_type"]:
    gr = [g.ventas12m.values for _, g in s2.groupby(col)]
    print("ANOVA", col, "F=%.2f p=%.4f" % stats.f_oneway(*gr))
    print("Kruskal", col, "p=%.4f" % stats.kruskal(*gr).pvalue)

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
s2.boxplot(column="ventas12m", by="zone_type", ax=ax[0]); ax[0].set_title("Ventas 12m por tipo de zona"); ax[0].set_xlabel("")
s2.boxplot(column="ventas12m", by="city", ax=ax[1]); ax[1].set_title("Ventas 12m por ciudad"); ax[1].set_xlabel(""); plt.suptitle("")
plt.setp(ax[1].get_xticklabels(), rotation=30); plt.tight_layout(); plt.savefig(FIG / "02_ventas_por_zona_ciudad.png", dpi=140); plt.close()

# --- transacciones
print("\nmix categoria:", t.product_category.value_counts(normalize=True).round(3).to_dict())
print("mix canal:", t.channel.value_counts(normalize=True).round(3).to_dict())
print("mix pago:", t.payment_method.value_counts(normalize=True).round(3).to_dict())
print("ticket por canal:", t.groupby("channel").ticket_mxn.mean().round(1).to_dict())
print("ticket por categoria:", t.groupby("product_category").ticket_mxn.mean().round(1).to_dict())
mix = t.assign(app=(t.channel == "App"), dlv=(t.channel == "Delivery")).groupby("store_id").agg(pct_app=("app", "mean"), pct_delivery=("dlv", "mean"), ticket_tx=("ticket_mxn", "mean"))
s3 = s2.merge(mix, on="store_id"); print("corr mezcla vs ventas:", s3[["ventas12m", "pct_app", "pct_delivery", "ticket_tx"]].corr()["ventas12m"].round(2).to_dict())
print("escala: tickets desempeno por tienda/mes ~", int(p.tickets.mean()), " vs tx muestra/tienda total", int(len(t) / t.store_id.nunique()), "(muestra)")
mix_zt = t.merge(s[["store_id", "zone_type"]], on="store_id").groupby("zone_type").channel.value_counts(normalize=True).unstack().round(3)
print(mix_zt)
mix_zt.to_csv(TAB / "mix_canal_por_zone_type.csv")

# --- zonas
print("\n== ZONAS candidatas")
num = [c for c in z.select_dtypes(include="number").columns if c != "nearest_store_id"]
print(z[num].describe().T[["mean", "std", "min", "max"]].round(2))
print("corr entre features zonas (|r|>0.5):")
cm = z[num].corr(); 
for i in cm.index:
    for j in cm.columns:
        if i < j and abs(cm.loc[i, j]) > 0.5: print("  ", i, j, round(cm.loc[i, j], 2))
print("zonas por ciudad:", z.city.value_counts().to_dict(), "; tipo:", z.zone_type.value_counts().to_dict())
print("ciudades con sucursal y sin zona:", set(s.city) - set(z.city), " zonas en ciudades sin sucursal:", set(z.city) - set(s.city))
chk = z.merge(s[["store_id", "city"]], left_on="nearest_store_id", right_on="store_id", suffixes=("", "_s"))
print("zonas cuya sucursal 'mas cercana' esta en OTRA ciudad:", (chk.city != chk.city_s).sum(), chk[chk.city != chk.city_s][["zone_id", "city", "city_s", "distance_nearest_store_km"]].to_dict("records"))
print("renta zonas vs renta implicita? rent range", z.avg_rent_mxn_m2.min(), z.avg_rent_mxn_m2.max())
print("zonas distancia<2km:", z[z.distance_nearest_store_km < 2].zone_id.tolist())
print("rango competidores: sucursales", s.nearby_competitors.min(), s.nearby_competitors.max(), " zonas", z.competitors_1km.min(), z.competitors_1km.max())
print("rango distancia: sucursales", s.distance_to_nearest_store_km.min(), s.distance_to_nearest_store_km.max(), " zonas", z.distance_nearest_store_km.min(), z.distance_nearest_store_km.max())
# consistencia interna zonas: workers>population?
print("zonas con workers_1km > population_1km:", (z.workers_1km > z.population_1km).sum(), "; students > population:", (z.students_1km > z.population_1km).sum())
print("zonas Oficinas con office_density<0.4:", z[(z.zone_type == 'Oficinas') & (z.office_density_index < .4)].zone_id.tolist(), "; Universitaria con univ_density<0.4:", z[(z.zone_type == 'Universitaria') & (z.university_density_index < .4)].zone_id.tolist())
s2.to_csv(TAB / "sucursales_con_ventas12m.csv", index=False)
