"""Etapa 02 - Experimento de validacion del modelo de ventas maduras (Version A: solo datos del ejercicio)."""
import warnings
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.model_selection import LeaveOneOut, RepeatedKFold, cross_val_predict
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
s = pd.read_csv(ROOT / "reports/tables/sucursales_con_ventas12m.csv")
y = s.ventas12m.values

num = ["nearby_competitors", "distance_to_nearest_store_km"]
cat = ["city", "zone_type"]
X = s[num + cat]

def ct(num_cols, cat_cols):
    return ColumnTransformer([("n", StandardScaler(), num_cols), ("c", OneHotEncoder(handle_unknown="ignore"), cat_cols)])

def wape(a, b): return np.abs(a - b).sum() / a.sum()
def r2(a, b): return 1 - ((a - b) ** 2).sum() / ((a - a.mean()) ** 2).sum()

res = []
def report(name, pred):
    res.append((name, np.abs(y - pred).mean(), wape(y, pred), r2(y, pred)))

# baseline: media global (LOO)
report("Media global", np.array([np.delete(y, i).mean() for i in range(len(y))]))
# ciudad con contraccion (shrinkage) hacia la media global
def city_shrink(k):
    pr = []
    for i in range(len(s)):
        tr = s.drop(i); gm = tr.ventas12m.mean(); st = tr.groupby("city").ventas12m.agg(["mean", "count"])
        c = s.loc[i, "city"]
        if c in st.index: m, n = st.loc[c]; pr.append((n * m + k * gm) / (n + k))
        else: pr.append(gm)
    return np.array(pr)
for k in (0, 1, 2, 4):
    report(f"Media por ciudad (shrink k={k})", city_shrink(k))
# modelos
models = {
    "Ridge (ciudad+tipo+comp+dist)": make_pipeline(ct(num, cat), RidgeCV(alphas=np.logspace(-1, 3, 30))),
    "Random Forest": make_pipeline(ct(num, cat), RandomForestRegressor(300, min_samples_leaf=3, random_state=0)),
    "GBM": make_pipeline(ct(num, cat), GradientBoostingRegressor(n_estimators=120, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)),
}
for n, m in models.items():
    report(n, cross_val_predict(m, X, y, cv=LeaveOneOut()))
# ridge solo ciudad / solo numericas
report("Ridge solo ciudad", cross_val_predict(make_pipeline(ct([], ["city"]) if False else ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), ["city"])]), RidgeCV(alphas=np.logspace(-1, 3, 30))), s[["city"]], y, cv=LeaveOneOut()))
report("Ridge solo numericas", cross_val_predict(make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-1, 3, 30))), s[num], y, cv=LeaveOneOut()))

out = pd.DataFrame(res, columns=["modelo", "MAE", "WAPE", "R2_LOO"]).round(3)
print(out.to_string(index=False))
