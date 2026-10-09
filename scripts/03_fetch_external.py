"""Etapa 03 - Descarga de fuentes externas (version B), a nivel municipio.
Fuentes:
  1) INEGI - Censo de Poblacion y Vivienda 2020 (ITER, principales resultados por localidad)
  2) INEGI - DENUE (API Cuantificar) - conteo de establecimientos por actividad SCIAN
Nota: ni sucursales ni zonas tienen coordenadas -> solo se puede enriquecer por ciudad/municipio.
"""
import io, os, zipfile, json
import requests, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"; EXT.mkdir(parents=True, exist_ok=True)

env = ROOT / ".env"
TOKEN = os.environ.get("DENUE_TOKEN") or dict(l.strip().split("=", 1) for l in env.read_text().splitlines() if "=" in l)["DENUE_TOKEN"]

# ciudad -> clave geoestadistica INEGI (entidad+municipio); CDMX = entidad completa (16 alcaldias)
CITIES = {"Leon": ("11020", "León"), "Guadalajara": ("14039", "Guadalajara"), "Monterrey": ("19039", "Monterrey"),
          "Queretaro": ("22014", "Querétaro"), "CDMX": ("09", "CDMX"), "Oaxaca": ("20067", "Oaxaca"),
          "Puebla": ("21114", "Puebla"), "Merida": ("31050", "Mérida")}

# ---- 1) Censo 2020 ITER
zpath = EXT / "_iter_00_cpv2020_csv.zip"
if not zpath.exists():
    r = requests.get("https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip", timeout=300)
    zpath.write_bytes(r.content)
zf = zipfile.ZipFile(zpath)
name = [n for n in zf.namelist() if n.lower().endswith(".csv") and "conjunto_de_datos" in n.lower() and "iter" in n.lower()][0]
cols = ["ENTIDAD", "MUN", "LOC", "NOM_LOC", "POBTOT", "POBFEM", "P_15YMAS", "P_18YMAS", "GRAPROES", "PEA", "POCUPADA", "VIVPAR_HAB", "PRO_OCUP_C",
        "VPH_AUTOM", "VPH_INTER", "VPH_PC", "P18YM_PB", "PCON_DISC", "PRES2015"]
hdr = pd.read_csv(zf.open(name), nrows=0, encoding="utf-8-sig").columns
use = [c for c in cols if c in hdr]
it = pd.read_csv(zf.open(name), usecols=use, encoding="utf-8-sig", dtype=str)
it["ENTIDAD"] = it.ENTIDAD.str.zfill(2); it["MUN"] = it.MUN.str.zfill(3); it["LOC"] = it.LOC.str.zfill(4)
rows = []
for city, (cve, label) in CITIES.items():
    if len(cve) == 2:
        sub = it[(it.ENTIDAD == cve) & (it.MUN == "000") & (it.LOC == "0000")]
    else:
        sub = it[(it.ENTIDAD == cve[:2]) & (it.MUN == cve[2:]) & (it.LOC == "0000")]
    assert len(sub) == 1, (city, len(sub))
    d = sub.iloc[0].to_dict(); d["city_key"] = city; rows.append(d)
censo = pd.DataFrame(rows).set_index("city_key").drop(columns=["ENTIDAD", "MUN", "LOC", "NOM_LOC"])
censo = censo.apply(pd.to_numeric, errors="coerce")
censo.to_csv(EXT / "censo2020_municipios.csv")
print(censo[["POBTOT", "GRAPROES", "PEA", "POCUPADA", "VPH_INTER", "VPH_AUTOM", "VIVPAR_HAB"]])

# ---- 2) DENUE (conteo por actividad)
ACT = {"cafeterias_722515": "722515", "restaurantes_7225": "7225", "comercio_menor_46": "46", "serv_prof_54": "54",
       "serv_financieros_52": "52", "educ_superior_6113": "6113", "corporativos_55": "55", "total_establecimientos": "0"}
out = {}
for city, (cve, _) in CITIES.items():
    out[city] = {}
    for k, a in ACT.items():
        u = f"https://www.inegi.org.mx/app/api/denue/v1/consulta/Cuantificar/{a}/{cve}/0/{TOKEN}"
        j = requests.get(u, timeout=60).json()
        if a == "0":  # total: sumar sectores de 2 digitos no es trivial; usar suma de los nodos 2-digitos
            tot = sum(int(x["Total"]) for x in j if len(x["AE"]) == 2)
        else:
            tot = int(next(x["Total"] for x in j if x["AE"] == a))
        out[city][k] = tot
denue = pd.DataFrame(out).T
denue.to_csv(EXT / "denue_conteos_municipios.csv")
print(denue)
meta = {"censo": "INEGI Censo de Poblacion y Vivienda 2020 - ITER nacional", "denue": "INEGI DENUE API Cuantificar (consulta realizada en la fecha de ejecucion)",
        "nivel": "municipio (CDMX = entidad completa)", "claves": {k: v[0] for k, v in CITIES.items()}}
(EXT / "fuentes.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


