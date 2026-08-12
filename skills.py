"""
DataJobs Radar - skills.py
Extraccion de habilidades/tecnologias a partir del titulo y la descripcion
de las ofertas. Se usa desde el EDA, la app y el chat.

El diccionario mapea variantes (en varias lenguas) a un skill canonico.
"""

from __future__ import annotations

import re

SKILLS = {
    "sql": ["sql"],
    "python": ["python"],
    "r": [" r ", "r language", "r programming"],
    "power bi": ["power bi", "powerbi", "power bi desktop"],
    "tableau": ["tableau"],
    "excel": ["excel"],
    "google sheets": ["google sheets"],
    "looker": ["looker"],
    "looker studio": ["looker studio"],
    "apache spark": ["apache spark"],
    "spark": ["spark"],
    "hadoop": ["hadoop"],
    "airflow": ["airflow"],
    "dbt": ["dbt", "dbt core"],
    "kafka": ["kafka"],
    "snowflake": ["snowflake"],
    "aws": ["aws", "amazon web services", "amazon s3", "s3", "ec2", "lambda",
             "athena", "redshift", "glue"],
    "azure": ["azure", "azure sql", "azure databricks", "azure synapse",
               "azure data factory", "azure blob"],
    "gcp": ["gcp", "google cloud", "google cloud platform", "bigquery",
            "google bigquery", "gcs", "cloud storage"],
    "databricks": ["databricks"],
    "sas": ["sas"],
    "statistics": ["statistics", "statistical", "estadística", "estadisticas",
                   "estadísticas"],
    "probability": ["probability", "probabilidad"],
    "hypothesis testing": ["hypothesis test", "ab testing", "a/b testing",
                           "statistical test", "pruebas estad"],
    "machine learning": ["machine learning", "ml", "modelos", "modelos de ml",
                         "modelos predictivos"],
    "deep learning": ["deep learning", "redes neuronales", "neural network"],
    "data visualization": ["data visualization", "visualization", "visualisation",
                           "visualización", "visualizacion", "dashboards",
                           "dashboarding", "reporting", "powerpoint"],
    "etl": ["etl", "data pipeline", "pipelines de datos", "data pipelines"],
    "data warehousing": ["data warehouse", "data warehousing", "almacén de datos",
                         "almacen de datos", "olap"],
    "data modeling": ["data modeling", "data modelling", "modelado de datos",
                      "modelado dimensional"],
    "git": ["git", "github", "gitlab", "bitbucket"],
    "docker": ["docker", "kubernetes", "k8s", "containers", "contenedores"],
    "ci/cd": ["ci/cd", "jenkins", "devops", "terraform"],
    "rest apis": ["api", "apis", "rest", "graphql", "restful"],
    "mongodb": ["mongodb", "mongo"],
    "postgresql": ["postgres", "postgresql"],
    "mysql": ["mysql", "mariadb"],
    "nosql": ["nosql", "cassandra", "couchbase", "elasticsearch"],
    "datastage": ["datastage", "data stage", "informatica"],
    "qlik": ["qlik", "qliksense", "qlikview"],
    "microstrategy": ["microstrategy"],
    "alteryx": ["alteryx"],
    "spss": ["spss"],
    "jira": ["jira", "confluence"],
    "agile": ["agile", "scrum", "kanban"],
    "communication": ["communication", "comunicación", "comunicacion",
                      "comunication", "storytelling", "presentation skills",
                      "habilidades comunicativas", "soft skills",
                      "habilidades blandas", "teamwork", "trabajo en equipo"],
    "problem solving": ["problem solving", "resolución de problemas",
                        "resolucion de problemas", "analytical skills",
                        "capacidad analítica", "capacidad analitica",
                        "critical thinking", "pensamiento crítico",
                        "pensamiento critico"],
    "business acumen": ["business acumen", "business intelligence",
                        "understanding of the business", "domain knowledge",
                        "business context"],
    "project management": ["project management", "gestión de proyectos",
                           "gestion de proyectos", "deliver projects"],
    "powerpoint": ["powerpoint"],
    "scala": ["scala"],
    "java": ["java"],
    "c++": ["c++", "c plus plus"],
    "julia": ["julia"],
    "tensorflow": ["tensorflow", "keras", "pytorch"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "sap": ["sap", "sap bo", "sap bw", "sap hana", "sap business objects"],
    "oracle": ["oracle", "oracle sql", "pl/sql", "oracle bi"],
    "teradata": ["teradata", "teradata sql"],
    "tibco": ["tibco", "tibco spotfire"],
    "spotfire": ["spotfire"],
    "cognos": ["cognos", "ibm cognos"],
    "informatica": ["informatica", "informatica powercenter"],
    "ssis": ["ssis", "ssas", "ssrs", "sql server"],
    "sql server": ["sql server"],
}

ROLES = {
    "Data Analyst": ["data analyst", "analista de datos", "analista de da",
                     "bi analyst", "business intelligence analyst"],
    "BI Analyst": ["bi analyst", "business intelligence analyst",
                   "power bi developer", "business analyst"],
    "Data Scientist": ["data scientist", "científico de datos", "cientifico de datos"],
    "Data Engineer": ["data engineer", "ingeniero de datos", "ingeniero de datos"],
    "Data Analyst": ["data analyst", "analista de datos", "analista de da"],
}

# Prioridad para asignar rol cuando coinciden varias variantes.
ROLE_ORDER = ["Data Scientist", "Data Engineer", "BI Analyst", "Data Analyst"]


def _regex_variante(v: str) -> re.Pattern:
    """Convierte una variante en regex con limites de palabra.

    Variantes de varias palabras (p.ej. "power bi") mantienen el espacio
    como separador de palabras, lo que evita falsos positivos tipo "digital".
    """
    return re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)


def detectar_skills(texto: str) -> list[str]:
    """Devuelve la lista de skills canonicos presentes en un texto."""
    if not texto:
        return []
    encontrados = []
    for skill, variantes in SKILLS.items():
        if skill in encontrados:
            continue
        for v in variantes:
            if _regex_variante(v).search(texto):
                encontrados.append(skill)
                break
    return encontrados


def detectar_rol(titulo: str) -> str | None:
    """Asigna una de las categorias principales al titulo de la oferta."""
    if not titulo:
        return None
    t = titulo.lower()
    candidatos = []
    for rol, variantes in ROLES.items():
        for v in variantes:
            if v in t:
                candidatos.append(rol)
                break
    for rol in ROLE_ORDER:
        if rol in candidatos:
            return rol
    return None
