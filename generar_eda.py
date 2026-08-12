"""Genera notebooks/eda.ipynb a partir de las celdas definidas aqui."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python",
                              "name": "python3"}}
nb.cells = []


def md(text):
    nb.cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    nb.cells.append(nbf.v4.new_code_cell(text))


md("""# DataJobs Radar — Análisis exploratorio

**Pregunta**: ¿Qué buscan realmente las empresas cuando contratan Data Analysts?

Analizamos ofertas reales descargadas de la API de Adzuna (España + Europa)
y guardadas en `datos.db` por `ingesta.py`.

Preguntas que responde este EDA:
1. ¿Cuántas ofertas y de dónde?
2. ¿Qué habilidades/tecnologías se piden más?
3. ¿Qué se ofrece de salario?
4. ¿Qué diferencia hay entre Data Analyst, BI Analyst y Data Scientist?
5. ¿Qué porcentaje de ofertas son remotas?
6. ¿Qué ciudades tienen más oportunidades?
7. ¿Qué experiencia se solicita?
8. Conclusión: ¿qué debería aprender alguien que quiere ser Data Analyst?""")

code("""# %pip install pandas plotly nbformat --quiet
import sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio

pio.renderers.default = "notebook"

# La base vive en la raiz del proyecto (una carpeta arriba del notebook).
RAIZ = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
DB = RAIZ / "datos.db"
conn = sqlite3.connect(DB)
df = pd.read_sql_query("SELECT * FROM ofertas", conn)
print(f"Filas: {df.shape[0]} | Columnas: {df.shape[1]}")
df.head(3)""")

md("""## 1. Volumen y procedencia de las ofertas""")

code("""import sys
sys.path.insert(0, str(RAIZ))""")

code("""pais = df["country"].value_counts().rename(index={
    "es": "España", "de": "Alemania", "fr": "Francia", "nl": "Países Bajos",
    "pl": "Polonia", "it": "Italia", "at": "Austria", "be": "Bélgica",
    "ch": "Suiza"}).sort_values(ascending=True)
fig = px.bar(pais, orientation="h", labels={"value": "Ofertas", "index": "País"},
             title="Ofertas por país")
fig.show()
pais""")

md("""## 2. Habilidades más demandadas

Extraemos skills de títulos y descripciones con `skills.py`.""")

code("""from skills import detectar_skills

df["skills"] = df.apply(
    lambda r: detectar_skills(str(r["title"]) + " " + str(r["description"])), axis=1)

from collections import Counter
conteo = Counter(s for lista in df["skills"] for s in lista)
top = pd.Series(conteo).sort_values(ascending=False).head(25)

fig = px.bar(top.sort_values(), orientation="h",
             labels={"value": "Ofertas", "index": "Skill"},
             title="Top 25 habilidades/tecnologías")
fig.show()
top""")

md("""### Habilidades por rol""")

code("""from skills import detectar_rol

df["rol"] = df["title"].apply(detectar_rol)
df_rol = df[df["rol"].notna()].copy()

matriz = pd.DataFrame(0, index=df_rol["rol"].unique(),
                      columns=sorted(set(conteo.keys()) & set(df_rol["skills"].explode())))
for rol, grupo in df_rol.groupby("rol"):
    for skills in grupo["skills"]:
        for s in skills:
            if s in matriz.columns:
                matriz.loc[rol, s] += 1

top_skills = matriz.sum().sort_values(ascending=False).head(12).index
fig = px.imshow(matriz[top_skills].T, color_continuous_scale="Blues",
                labels=dict(color="Ofertas"),
                title="Habilidades por rol (nº de ofertas)")
fig.update_yaxes(title="Skill")
fig.show()""")

md("""## 3. Salarios

Adzuna solo publica salario en una parte de las ofertas (213 de 1202).
Agrupamos los países que usan euro (EUR) para comparar medianas.""")

code("""sal = df.dropna(subset=["salary_min"]).copy()
sal["salario_medio"] = (sal["salary_min"] + sal["salary_max"]) / 2
sal_euro = sal[sal["salary_currency"] == "EUR"].copy()

fig = px.box(sal_euro, x="country", y="salario_medio",
             title="Salario (EUR) por país", labels={"country": "País",
                     "salario_medio": "Salario medio (EUR/año)"})
fig.show()

print(sal_euro.groupby("country")["salario_medio"]
      .agg(["median", "mean", "count"]).round(0))

print("\\nMediana global (EUR):", round(sal_euro["salario_medio"].median()))
print("Mediana por rol (EUR):")
print(sal_euro.dropna(subset=["rol"]).groupby("rol")["salario_medio"]
      .median().round(0).sort_values(ascending=False))""")

md("""## 4. Comparativa de roles""")

code("""vol = df["rol"].value_counts()
fig = px.pie(vol, names=vol.index, values=vol.values,
             title="Distribución de roles en las ofertas")
fig.show()
vol""")

md("""## 5. Ofertas remotas""")

code("""rem = df["remote"].value_counts()
fig = px.pie(rem, names=["No", "Sí"], values=rem.values,
             title="Ofertas remotas",
             hole=0.4, color_discrete_sequence=["#c7d4e0", "#2b6cb0"])
fig.show()
print(f"Remotas: {int(rem.get(1, 0))} de {len(df)} "
      f"({rem.get(1, 0) / len(df):.1%})")""")

md("""## 6. Ciudades con más oportunidades""")

code("""ciudades = df["location_display"].value_counts().head(20)
fig = px.bar(ciudades.sort_values(), orientation="h",
             labels={"value": "Ofertas", "index": "Ubicación"},
             title="Top ubicaciones")
fig.show()
ciudades""")

md("""## 7. Experiencia solicitada

Buscamos patrones de experiencia (junior/senior/años) en el título.""")

code("""def nivel_exp(titulo):
    t = (titulo or "").lower()
    if any(k in t for k in ("senior", "sr.", "sr ", "principal", "lead",
                            "manager", "jefe", "seniority")):
        return "Senior/Lead"
    if any(k in t for k in ("junior", "jr", "entry", "graduate", "trainee",
                            "becario", "junior/mid")):
        return "Junior/Entry"
    if any(k in t for k in ("mid", "intermediate", "middle")):
        return "Mid"
    return "No especificado"

df["nivel"] = df["title"].apply(nivel_exp)
niveles = df["nivel"].value_counts()
fig = px.bar(niveles, labels={"value": "Ofertas", "index": "Nivel"},
             title="Nivel de experiencia según título")
fig.show()
niveles""")

md("""## 8. Conclusión: qué aprender para ser Data Analyst

Respondemos con datos: las skills del top 10 que más se repiten y las
diferencias clave entre roles.""")

code("""print("=== Top 15 skills generales ===")
print(top.head(15).to_string())

print("\\n=== Roles mejor pagados (EUR, mediana) ===")
sal_roles = sal_euro.dropna(subset=["rol"]).groupby("rol")["salario_medio"].median()
print(sal_roles.sort_values(ascending=False).round(0).to_string())

print("\\n=== % remoto por rol ===")
rem_rol = df_rol.groupby("rol")["remote"].mean() * 100
print(rem_rol.round(1).to_string())""")

md("""### Resumen ejecutivo

- **Habilidades**: Power BI y machine learning lideran (116 ofertas cada una),
  seguidas de visualización de datos (105), SQL (48) y Python (43). Ojo: Adzuna
  solo devuelve fragmentos de descripción, así que SQL/Python probablemente
  están infrarrepresentados en estas búsquedas concretas.
- **Salario**: mediana de ~56.500 €/año en Europa; Alemania lidera (77.500 €) e
  Italia es la más baja (30.650 €).
- **Roles**: Data Scientist paga más (70.000 €), seguido de Data Engineer
  (52.800 €), Data Analyst (45.493 €) y BI Analyst (41.250 €).
- **Remoto**: solo el 5,4% de las ofertas son remotas; Data Analyst es el rol
  con mayor porcentaje (6,9%).
- **Geografía**: España tiene el mayor volumen de ofertas (182), seguida de
  Francia (150) y Polonia (149).
- **Recomendación**: para ser Data Analyst, el combo SQL + Python + Power BI /
  Tableau + visualización + estadística es la base; el salario y el remoto
  dependen mucho del país y del rol objetivo.""")

with open("notebooks/eda.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("Generado notebooks/eda.ipynb")
