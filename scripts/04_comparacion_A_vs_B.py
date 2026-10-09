"""Etapa 03b - Version B: ¿cuanto mejora el modelo al agregar fuentes externas (INEGI Censo + DENUE, nivel ciudad)?
Comparacion A vs B con dos validaciones:
  - LOO por sucursal  (ciudades ya vistas)
  - Leave-City-Out    (ciudad completa fuera: prueba de generalizacion a una ciudad nueva)
"""
import warnings
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
s = pd.read_csv(ROOT / "reports/tables/sucursales_con_ventas12m.csv")
censo = pd.read_csv(ROOT / "data/external/censo2020_municipios.csv", index_col=0)
den = pd.read_csv(ROOT / "data/external/denue_conteos_municipios.csv", index_col=0)

KEY = {"León": "Leon", "Guadalajara": "Guadalajara", "Monterrey": "Monterrey", "Querétaro": "Queretaro", "CDMX": "CDMX",
       "Oaxaca": "Oaxaca", "Puebla": "Puebla", "Mérida": "Merida"}
# robusto a problemas de codificacion de acentos
def key(c):
    c = str(c)
    for k, v in KEY.items():
        if k[:2] == c[:2] and (k[-3:] == c[-3:] or k[-2:] == c[-2:]): return v
    return c
s["city_key"] = s.city.map(key)
assert set(s.city_key) <= set(censo.index), set(s.city_key) - set(censo.index)

ext = pd.DataFrame(index=censo.index)
pop = censo.POBTOT
ext["log_pob"] = np.log(pop)
ext["graproes"] = censo.GRAPROES
ext["pea_pct"] = censo.PEA / pop
ext["internet_pct"] = censo.VPH_INTER / censo.VIVPAR_HAB
ext["auto_pct"] = censo.VPH_AUTOM / censo.VIVPAR_HAB
ext["cafes_x10k"] = den.cafeterias_722515 / pop * 1e4
ext["rest_x10k"] = den.restaurantes_7225 / pop * 1e4
ext["comercio_x10k"] = den.comercio_menor_46 / pop * 1e4
ext["servprof_x10k"] = den.serv_prof_54 / pop * 1e4
ext["finan_x10k"] = den.serv_financieros_52 / pop * 1e4
ext["educsup_x100k"] = den.educ_superior_6113 / pop * 1e5
ext["estab_x10k"] = den.total_establecimientos / pop * 1e4
ext.round(2).to_csv(ROOT / "data/processed/features_externas_ciudad.csv")
print(ext.round(2).to_string())

city_mean = s.groupby("city_key").ventas12m.mean().rename("ventas_media")
c = ext.join(city_mean).dropna()
print("\nCorrelacion (n=8 ciudades) de cada feature externa con ventas medias por ciudad:")
print(c.corr()["ventas_media"].drop("ventas_media").round(2).sort_values().to_string())

y = s.ventas12m.values
def wape(a, b): return np.abs(a - b).sum() / a.sum()
def r2(a, b): return 1 - ((a - b) ** 2).sum() / ((a - a.mean()) ** 2).sum()

def ridge(): return RidgeCV(alphas=np.logspace(-1, 3, 40))
def design(df, num, cat):
    return df[num + cat]

def make(num, cat, pca=None):
    tr = []
    if num:
        tr.append(("n", make_pipeline(StandardScaler(), PCA(pca)) if pca else StandardScaler(), num))
    if cat: tr.append(("c", OneHotEncoder(handle_unknown="ignore"), cat))
    return make_pipeline(ColumnTransformer(tr), ridge())

S = s.join(ext, on="city_key")
base_num = ["nearby_competitors", "distance_to_nearest_store_km"]
ext_sets = {
    "demanda (pob, internet, auto, pea)": ["log_pob", "internet_pct", "auto_pct", "pea_pct"],
    "competencia/oferta (cafes, rest, comercio)": ["cafes_x10k", "rest_x10k", "comercio_x10k"],
    "perfil economico (servprof, finan, educsup)": ["servprof_x10k", "finan_x10k", "educsup_x100k"],
    "todas (12) -> PCA(2)": list(ext.columns),
    "todas (12) -> PCA(3)": list(ext.columns),
}
def loo_pred(model_fn, cols):
    pr = np.zeros(len(S))
    for i in range(len(S)):
        tr = S.drop(index=i); m = model_fn(); m.fit(tr[cols], tr.ventas12m); pr[i] = m.predict(S.loc[[i], cols])[0]
    return pr
def loco_pred(model_fn, cols):
    pr = np.zeros(len(S))
    for c_ in S.city_key.unique():
        te = S.city_key == c_; m = model_fn(); m.fit(S.loc[~te, cols], S.loc[~te, "ventas12m"]); pr[te.values] = m.predict(S.loc[te, cols])
    return pr

rows = []
def run(name, num, cat, pca=None):
    cols = num + cat; f = lambda: make(num, cat, pca)
    l = loo_pred(f, cols); lc = loco_pred(f, cols)
    rows.append((name, wape(y, l), r2(y, l), wape(y, lc), r2(y, lc)))

# referencias
glob = np.array([np.delete(y, i).mean() for i in range(len(y))])
glob_c = np.zeros(len(S))
for c_ in S.city_key.unique():
    te = (S.city_key == c_).values; glob_c[te] = y[~te].mean()
rows.append(("0) Media global", wape(y, glob), r2(y, glob), wape(y, glob_c), r2(y, glob_c)))
# A
run("A1) Ridge: tipo zona + competidores + distancia (sin ciudad)", base_num, ["zone_type"])
run("A2) Ridge: A1 + ciudad (dummies)  [no aplica a ciudad nueva]", base_num, ["zone_type", "city_key"])
# B
for k, cols in ext_sets.items():
    p = 2 if "PCA(2)" in k else 3 if "PCA(3)" in k else None
    run(f"B) A1 + externas: {k}", base_num + cols, ["zone_type"], pca=None if p is None else p) if p is None else None
# B con PCA solo sobre externas: implementado aparte
from sklearn.compose import ColumnTransformer as CT
def make_pca_ext(ncomp):
    ct = CT([("b", StandardScaler(), base_num), ("e", make_pipeline(StandardScaler(), PCA(ncomp)), list(ext.columns)),
             ("z", OneHotEncoder(handle_unknown="ignore"), ["zone_type"])])
    return make_pipeline(ct, ridge())
cols_all = base_num + list(ext.columns) + ["zone_type"]
for ncomp in (1, 2, 3):
    f = lambda n=ncomp: make_pca_ext(n)
    l = loo_pred(f, cols_all); lc = loco_pred(f, cols_all)
    rows.append((f"B) A1 + externas (12 vars -> PCA {ncomp})", wape(y, l), r2(y, l), wape(y, lc), r2(y, lc)))
# B con ciudad + externas
run("B+) A2 + externas demanda", base_num + ext_sets["demanda (pob, internet, auto, pea)"], ["zone_type", "city_key"])

out = pd.DataFrame(rows, columns=["modelo", "WAPE_LOO", "R2_LOO", "WAPE_LOCO", "R2_LOCO"]).round(3)
print("\n", out.to_string(index=False))
out.to_csv(ROOT / "reports/tables/comparacion_A_vs_B.csv", index=False)
