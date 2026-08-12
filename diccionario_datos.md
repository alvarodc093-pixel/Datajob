# Diccionario de datos

Base de datos SQLite `datos.db` generada por `ingesta.py` a partir de la API
de Adzuna. Contiene dos tablas.

## Tabla `ofertas`

Una fila por oferta de empleo descargada.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | TEXT (PK) | Identificador único de la oferta en Adzuna |
| `title` | TEXT | Título de la oferta |
| `description` | TEXT | Fragmento de la descripción (Adzuna solo devuelve un resumen) |
| `salary_min` | REAL | Salario mínimo anunciado (null si no se publica) |
| `salary_max` | REAL | Salario máximo anunciado (null si no se publica) |
| `salary_is_predicted` | INTEGER | 1 si el salario es estimado por Adzuna, 0 si lo publica la empresa |
| `salary_currency` | TEXT | Moneda del salario según país (EUR, CHF, PLN) |
| `contract_type` | TEXT | Tipo de contrato (permanent, contract, ...) |
| `contract_time` | TEXT | Jornada (full_time, part_time, ...) |
| `category_label` | TEXT | Categoría/sector asignada por Adzuna (p.ej. "IT Jobs") |
| `category_tag` | TEXT | Etiqueta corta de la categoría |
| `company` | TEXT | Nombre de la empresa |
| `location_display` | TEXT | Ubicación legible (p.ej. "Madrid, Comunidad de Madrid") |
| `location_area` | TEXT | JSON con la jerarquía de ubicación (país, región, ciudad) |
| `latitude` | REAL | Latitud |
| `longitude` | REAL | Longitud |
| `remote` | INTEGER | 1 si se detectó trabajo remoto por texto, 0 si no |
| `created` | TEXT | Fecha de publicación de la oferta (ISO) |
| `redirect_url` | TEXT | Enlace a la oferta en Adzuna |
| `country` | TEXT | Código ISO 3166-1 alpha-2 del país de la oferta |
| `query_used` | TEXT | Búsqueda con la que se descargó (p.ej. "data analyst") |
| `fetched_at` | TEXT | Fecha en la que se descargó la oferta |

Códigos de país: `es` España, `de` Alemania, `fr` Francia, `nl` Países Bajos,
`pl` Polonia, `it` Italia, `at` Austria, `be` Bélgica, `ch` Suiza.

## Tabla `api_cache`

Guarda las respuestas crudas de la API. Permite re-ejecutar `ingesta.py` sin
volver a llamar a Adzuna (clave para no gastar las peticiones del plan gratis).

| Columna | Tipo | Descripción |
|---|---|---|
| `cache_key` | TEXT (PK) | Hash de la consulta (país + búsqueda + página) |
| `country` | TEXT | País de la consulta |
| `query` | TEXT | Término buscado |
| `page` | INTEGER | Página de resultados |
| `fetched_at` | TEXT | Fecha de la descarga |
| `payload` | TEXT | JSON crudo devuelto por la API |

## Variables derivadas (calculadas en el EDA y la app)

- `pais_nombre`: nombre legible del país a partir de `country`.
- `skills`: lista de habilidades/tecnologías detectadas por `skills.py`.
- `rol`: categoría del puesto (Data Analyst, BI Analyst, Data Scientist,
  Data Engineer) según el título.
- `salario_medio`: `(salary_min + salary_max) / 2`.
- `nivel`: nivel de experiencia estimado (Senior/Lead, Mid, Junior/Entry)
  a partir del título.
