# Guía de examen · Ingeniería de Datos (proyecto epileps.IA)

Temario: **Extracción** (CSV, `read_html`, API REST con `requests`, web scraping con BeautifulSoup) → **EDA** → **Transformación** (técnica, analítica, de negocio).
El proyecto epileps.IA (HU-1, HU-2 y HU-3) es el ejemplo práctico que recorre todo el temario.

---

## 0. Mapa mental (apréndete esto primero)

```
FUENTE                    TÉCNICA                    FUNCIÓN CLAVE           DEVUELVE
CSV                       pandas                     pd.read_csv()           1 DataFrame
Web con <table>           pandas                     pd.read_html()          LISTA de DataFrames
Web sin tabla (divs)      requests + BeautifulSoup   soup.find_all()         etiquetas -> filas -> DataFrame
API REST                  requests (+ json)          response.json()         dict/list -> filas -> DataFrame
```
> "Whichever path you take, the destination is the same: a DataFrame in memory."

En el proyecto:
- **HU-1 = API REST** (CIMA): POST para obtener los `nregistro` y luego un GET por cada uno → Excel.
- **HU-2 = Web scraping** de la ficha técnica en HTML: palabras de la sección 4.4, número de `<table>` y número de veces que aparece "grave/graves".
- **HU-3 = CSV + merge** con el Nomenclátor (cruce por el Código Nacional `cn`): precio, estado, etc.
- **EDA**: notebook `pruebas_EDA.ipynb` (`describe`, `drop`, `fillna`, gráficas).

---

## 1. Teoría: ETL, cliente/servidor y HTTP

### ETL vs ELT
| | ETL | ELT |
|---|---|---|
| Orden | Extract → **Transform** → Load | Extract → Load → **Transform** |
| Cuándo se transforma | **Antes** de guardar | **Después** de guardar, a menudo en el momento de la consulta |
| Cuándo usarlo | Esquemas estrictos, almacenamiento limitado | Data warehouses o data lakes en la nube; se conserva el dato crudo y se gana flexibilidad |

- **Idea clave:** ETL y ELT tienen **las mismas operaciones**; solo cambia **cuándo** se ejecutan.
- **EL(t)T:** casi nunca hay un ELT puro. Antes de cargar se suele hacer una transformación ligera de calidad.
- **Extracción** es la E de ETL: traer los datos a memoria **sin cambiarlos**.

### Modelo cliente/servidor
- **Cliente** = tu script de Python: pide los datos, recibe los bytes crudos y los convierte (parsea) en un DataFrame.
- **Servidor** = donde viven los datos: el sistema de ficheros, un servidor web o una API.
- **Pull model:** nada llega solo. El dato solo se mueve cuando tu script hace la petición.
- Los datos pueden estar en 3 sitios: un fichero local, un fichero remoto (se descarga por HTTP) o una web/API (puede haber problemas de permisos o de formato).
- *Pregunta del PDF: "¿Qué problemas de acceso pueden aparecer aunque sea un CSV?"* → ruta incorrecta o carpeta de trabajo distinta (`os.getcwd()`), falta de permisos, fichero remoto con 403/404, separador o encoding incorrectos…

### Librería → función → objeto → método
```python
import pandas as pd                 # Librería (pd)
df = pd.read_csv("visits.csv")      # Función read_csv(), Argumento "visits.csv", Objeto df
df.head()                           # Método del objeto
```
- **Atributo** (sin paréntesis, es un valor guardado): `response.status_code`, `response.content`, `response.text`, `df.shape`, `df.columns`, `df.dtypes`
- **Método** (con paréntesis, hace una acción): `response.json()`, `response.raise_for_status()`, `df.head()`, `df.info()`

### GET vs POST (sale seguro)
| | GET | POST |
|---|---|---|
| Para qué | **Pedir/leer** un recurso | **Enviar** datos en el cuerpo (body) para que el servidor los procese, por ejemplo un filtro de búsqueda complejo |
| Dónde van los datos | En la URL: `?clave=valor` (`params=`) | En el **body** (`data=` o `json=`) |
| En la HU-1 | `/medicamento?nregistro=XXXX` (detalle de 1 medicamento) | `/buscarEnFichaTecnica` con el payload `[{"seccion":"4.1","texto":"epilepsia","contiene":1}]` |

**¿Por qué la búsqueda es POST?** Porque el filtro es una **lista de objetos JSON** (sección, texto, contiene), que no cabe bien en la URL. Se manda en el body.

### Códigos de estado HTTP
- **200** OK · **201** Created
- **4xx = error del cliente**: 400 Bad Request, 401 Unauthorized, **403 Forbidden** (no tienes acceso; p. ej. la web bloquea scripts sin cookies ni User-Agent), **404 Not Found** (URL mal escrita)
- **5xx = error del servidor**: 500, 503
- `response.raise_for_status()` lanza una excepción si la respuesta es 4xx o 5xx. Así te ahorras el `if response.status_code == 200`.
- "Un 403 o un 404 es un **fallo de extracción**, no un bug de pandas: revisa la dirección y el acceso antes que el código".

### Contenido de la respuesta
| | Tipo | Uso |
|---|---|---|
| `response.content` | **bytes** | HTML o binario crudo (se puede pasar a BeautifulSoup) |
| `response.text` | **str** | HTML como texto |
| `response.json()` | **dict/list** de Python | Respuestas de una API REST |

### Parámetros útiles de `requests`
```python
requests.get(url, params={...}, headers={...}, timeout=30)
requests.post(url, json=payload)                                   # requests serializa y pone el Content-Type
requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"})  # equivalente (es lo que hace cima_api.py)
```
- `timeout`: deja de esperar pasado ese tiempo (evita que el script se quede colgado). Si se agota, salta `requests.exceptions.Timeout`.
- `headers={"User-Agent": "EducationalScraper/1.0"}`: identifica tu petición. Algunas webs devuelven 403 si no lo pones.
- `time.sleep(0.5)` entre peticiones: para no saturar el servidor (scraping responsable).

---

## 2. Extracción tabular con pandas

### CSV: "parece una tabla, pero no lo es"
Un CSV es **solo texto**. El fichero **no define**: el delimitador, el encoding, los tipos, cómo se marcan los nulos, el formato local (coma o punto decimal) ni el esquema. Si no le dices nada, pandas **adivina** y pone valores por defecto.

| Problema | Síntoma | Parámetro que lo arregla |
|---|---|---|
| Delimitador incorrecto | Todo acaba en **una sola columna** | `sep=";"` |
| Encoding incorrecto | Tildes y ñ rotas (`EspaÃ±a`) | `encoding="latin-1"` |
| Cabecera mal leída | La 1ª fila de datos se usa como nombres de columna | `header=None, names=[...]` |
| Nulos "escondidos" | `N/A` o `-` se quedan como texto | `na_values=["", "N/A", "-"]` |
| Tipos incorrectos | Un ID se convierte en número (y pierde los ceros a la izquierda) | `dtype={"Patient_ID": str}` |
| Truncado silencioso | Menos filas de las esperadas | `nrows`, `skiprows` |
| Solo necesitas algunas columnas | El DataFrame es enorme | `usecols=[...]` |

```python
import os, pandas as pd
csv_path = os.path.join(os.getcwd(), "data", "fichero.csv")   # ruta portable entre Windows, Mac y Linux
df = pd.read_csv(csv_path, sep=";", encoding="latin-1",
                 usecols=["Patient_ID", "Visit_Date"],
                 na_values=["", "N/A", "-"], dtype={"Patient_ID": "string"})
```
- `os.getcwd()` devuelve la carpeta de trabajo actual, que es la base de cualquier ruta relativa.
- `os.path.join()` construye la ruta con el separador correcto para cada sistema operativo.

### Comprobar el resultado (siempre, después de extraer)
| Pregunta | Código |
|---|---|
| ¿Cuántas filas y columnas tengo? | `df.shape` |
| ¿Las columnas son las que espero? | `df.columns` |
| ¿El contenido tiene buena pinta? | `df.head()` |
| ¿pandas ha adivinado bien los tipos? | `df.dtypes` |
| ¿Cuántos valores faltan? | `df.isna().sum()` |

> Esto todavía **no es transformación**: es la primera validación de la extracción.

### `pd.read_html()`
- Solo encuentra marcado `<table>` real: `<table>` → `<tr>` (fila) → `<th>` (celda de cabecera, se convierte en nombre de columna) / `<td>` (celda de datos).
- Devuelve una **LISTA de DataFrames** (uno por cada tabla de la página), así que hay que elegir uno: `df = tables[0]`. *(Pregunta del PDF: "¿por qué tables[0]?" → porque read_html devuelve una lista y tú quieres un único DataFrame.)*
- Errores típicos: `HTTPError 403` (la página no deja entrar al script) y `ValueError: No tables found` (la página no tiene `<table>`, por ejemplo una rejilla hecha con divs → hay que usar BeautifulSoup).
- La página tiene varias tablas → mira `len(tables)` y elige por índice o con `match="texto"`.
- Cabeceras en dos filas → se crea un MultiIndex → usa `header=0`.
- Números que llegan como texto (separadores europeos) → usa `decimal=","` y `thousands="."`.

---

## 3. Web scraping con requests + BeautifulSoup

**Cuándo:** la página no tiene `<table>`, pero el contenido es **regular** (bloques repetidos con la misma clase, p. ej. `<div class="list-view--item">`).

**Fases:** 1) **GET** descarga la página → 2) **PARSE** convierte el HTML en un árbol buscable → 3) recorres los bloques y sacas los campos → 4) creas el DataFrame → 5) `to_csv`.

Las clases (`list-view--item`, `timestamp`…) **no son estándar**: se encuentran con *clic derecho → Inspeccionar*.

```python
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

url = "https://www.who.int/news-room/releases/1"
headers = {"User-Agent": "EducationalScraper/1.0"}
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.content, "html.parser")
print(soup.title.get_text(strip=True))
print(len(soup.find_all("table")))           # 0 -> read_html no serviría

items = soup.find_all("div", class_="list-view--item")   # class_ lleva guion bajo porque "class" es palabra reservada de Python
rows = []
for item in items:
    date_tag  = item.find("span", class_="timestamp")
    type_tag  = item.find("div",  class_="sf-tags-list-item")
    title_tag = item.find("p",    class_="heading")
    link_tag  = item.find("a",    class_="link-container")
    if not all([date_tag, type_tag, title_tag, link_tag]):   # si falta algún campo, saltamos el bloque
        continue
    href = link_tag.get("href")                  # href es un ATRIBUTO del HTML, no texto visible
    if not href:
        continue
    rows.append([date_tag.get_text(strip=True),
                 type_tag.get_text(strip=True),
                 title_tag.get_text(" ", strip=True),
                 urljoin(url, href)])            # convierte una URL relativa en absoluta

df = pd.DataFrame(rows, columns=["Date", "Release Type", "Title", "URL"])
df.to_csv("who_health_news.csv", index=False)
```

### Chuleta de BeautifulSoup
| Código | Qué hace |
|---|---|
| `soup.find("h2", id="4.4")` | **Primer** elemento que coincide, o `None` si no hay ninguno |
| `soup.find_all("table")` | **Lista** con todos los elementos que coinciden |
| `soup.find_all("div", class_="x")` | Filtra por clase |
| `tag.get_text(strip=True)` / `tag.text` | Texto visible (sin las etiquetas) |
| `tag.get("href")` / `tag["href"]` | Valor de un atributo (`.get` devuelve None si no existe; `[]` lanza KeyError) |
| `tag.find_next_siblings()` | Los "hermanos" siguientes, es decir, los elementos del mismo nivel |
| `tag.name` | Nombre de la etiqueta (`"h2"`, `"div"`…) |
| `soup.text` | Todo el texto del documento |

### Lo que hicisteis en la HU-2 (`webScraping.py`)
```python
# 1) Palabras de la sección 4.4: recorrer los hermanos del <h2 id="4.4"> hasta el siguiente <h2>
h2 = soup.find("h2", id="4.4")
texto = ""
for el in h2.find_next_siblings():
    if el.name == "h2":            # ya hemos llegado a la 4.5 -> paramos
        break
    texto += el.text.strip()
n_palabras = len(texto.split())

# 2) Número de tablas
n_tablas = len(soup.find_all("table"))

# 3) Número de veces que aparece "grave" o "graves" (y NO "gravemente")
import re
n_grave = len(re.findall(r"\bgraves?\b", soup.text))
```
- **¿Por qué regex y no `.count("grave")`?** `.count` también contaría "gravemente" o "agravar". `\b` marca el límite de palabra y `s?` hace que la "s" sea opcional.
- Gestión de errores en el bucle: `try/except requests.exceptions.Timeout` y `except requests.exceptions.RequestException` → se escribe -1 para que la columna no se descuadre. Además, `time.sleep(0.5)` entre peticiones.

---

## 4. API REST: la HU-1 paso a paso (CIMA, de la AEMPS)

La respuesta de `buscarEnFichaTecnica` tiene esta forma (dict):
```json
{ "totalFilas": 988, "pagina": 1, "tamanioPagina": 200, "resultados": [ {"nregistro": "42991", ...}, ... ] }
```
**Nota del enunciado:** la URL solo devuelve la página 1. `totalFilas` es el total de registros, así que **hay que paginar**.

### Versión limpia (la que deberías saber escribir de memoria)
```python
import requests, math
import pandas as pd

URL_BUSQUEDA = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica"
URL_MEDICAMENTO = "https://cima.aemps.es/cima/rest/medicamento"
payload = [{"seccion": "4.1", "texto": "epilepsia", "contiene": 1}]

# --- POST: primera página, para saber cuántas filas hay en total ---
r = requests.post(URL_BUSQUEDA, params={"pagina": 1}, json=payload, timeout=30)
r.raise_for_status()
datos = r.json()                                   # dict
total = datos["totalFilas"]
por_pagina = datos["tamanioPagina"]
n_paginas = math.ceil(total / por_pagina)          # en vez de poner range(5) a mano

nregistros = [m["nregistro"] for m in datos["resultados"]]
for p in range(2, n_paginas + 1):
    r = requests.post(URL_BUSQUEDA, params={"pagina": p}, json=payload, timeout=30)
    r.raise_for_status()
    nregistros += [m["nregistro"] for m in r.json()["resultados"]]

# --- GET: detalle de cada medicamento ---
filas = []
for nreg in nregistros:
    r = requests.get(URL_MEDICAMENTO, params={"nregistro": nreg}, timeout=30)
    r.raise_for_status()
    v = r.json()
    filas.append({
        "nregistro": v.get("nregistro"),
        "nombre": v.get("nombre"),
        "cn": v["presentaciones"][0]["cn"],                       # el primero disponible
        "forma_farmaceutica_simplificada": v["formaFarmaceuticaSimplificada"]["nombre"],
        "estado_aut": pd.to_datetime(v["estado"]["aut"], unit="ms"),   # la API da milisegundos desde 1970 (epoch)
        "estado_rev": pd.to_datetime(v["estado"]["rev"], unit="ms") if v["estado"].get("rev") else pd.NA,
        "comercializado": 1 if v.get("comerc") else 0,            # indicador binario
        "requiere_receta": int(bool(v.get("receta"))),
        "url_html_ficha_tecnica": next((d["urlHtml"] for d in v.get("docs", [])
                                        if d.get("tipo") == 1 and d.get("urlHtml", "").endswith(".html")), None),
        "num_registros_atc": len(v.get("atcs") or []),
        "num_excipientes": len(v.get("excipientes") or []),
    })

df = pd.DataFrame(filas)
df.to_excel("medicamentos_epilepsia.xlsx", index=False)
```

### Cómo "sacar los nregistro del JSON" (pregunta probable)
```python
respuesta_json = response.json()            # dict
lista = respuesta_json["resultados"]        # lista de dicts
nregistros = [item["nregistro"] for item in lista]
# o con un bucle:
for item in lista:
    nregistros.append(item["nregistro"])
```
Alternativa con pandas: `pd.json_normalize(respuesta_json["resultados"])["nregistro"]` (json_normalize "aplana" el JSON anidado y es una **operación estructural**).

### `dict["clave"]` vs `dict.get("clave")`
- `v["clave"]` → lanza **KeyError** si la clave no existe.
- `v.get("clave")` → devuelve **None**, o el valor por defecto que le pases: `v.get("docs", [])`.
- `len(v.get("excipientes") or [])` → el `or []` protege por si la API devuelve `None` (`len(None)` daría error).

---

## 5. HU-3: cruce con el Nomenclátor (CSV + merge)

```python
df = pd.read_excel("medicamentos_epilepsia_HU1_HU2.xlsx", dtype={"cn": str})
cols = ["Código Nacional", "Estado", "Precio venta al público con IVA",
        "Precio de referencia", "Tratamiento de larga duración", "Especial control médico"]
nom = pd.read_csv("Nomenclator.csv", usecols=cols, dtype={"Código Nacional": str})

df_hu3 = df.merge(nom, how="left", left_on="cn", right_on="Código Nacional").drop(columns=["Código Nacional"])
df_hu3.to_excel("medicamentos_epilepsia_HU3.xlsx", index=False)
```
- **`dtype=str` en las claves:** si no, pandas lee el `cn` como número y pierde los ceros a la izquierda (`012345` se convierte en `12345`), y entonces el cruce falla.
- **`how="left"`:** conserva **todos** los medicamentos de la HU-2 aunque no aparezcan en el nomenclátor; en ese caso las columnas nuevas quedan en NaN.
  - `inner` = solo las coincidencias · `right` = todas las filas de la derecha · `outer` = todas las filas de las dos tablas.
- `left_on`/`right_on` se usan cuando la clave se llama distinto en cada tabla; `on="cn"` cuando se llama igual.
- Comprobar cuántas filas cruzan: `df["cn"].isin(nom["Código Nacional"]).sum()`.
- ¿Qué tipo de transformación es? El merge es **entity resolution / enriquecimiento** (unir registros que representan la misma entidad del mundo real) y, desde el punto de vista analítico, un **join**.

---

## 6. EDA (Análisis Exploratorio de Datos)

**Definición:** examinar un dataset de forma sistemática **antes** de transformarlo. **La EDA no modifica los datos**: aporta la evidencia (la lista de problemas) para decidir qué transformar y cuánto.

### Las 5 preguntas de la EDA
1. ¿Qué datos tenemos?
2. ¿Cómo están estructurados?
3. ¿Qué falta o es inconsistente?
4. ¿Qué valores o patrones son inesperados?
5. ¿Qué transformaciones hacen falta? → **esta respuesta se convierte en el plan de transformación técnica**.

### Los 3 tipos de profiling (según las diapositivas: "la EDA es más amplia que el data profiling")
| Técnico | Estadístico | Visual |
|---|---|---|
| Tipos y formatos, nulos y duplicados, formatos inválidos, categorías inconsistentes | Distribuciones, medias y medianas, outliers, correlaciones | Histogramas, scatter plots y boxplots, gráficos de barras, tendencias temporales |
| → lleva **directamente** a la transformación técnica | → empieza a conectar con el análisis exploratorio | → empieza a conectar con el análisis exploratorio |

### Si te preguntan "¿qué dos tipos de EDA hay?"
Las clasificaciones típicas (por si el profesor usa otra distinta a la de las diapositivas):
- **Gráfica vs no gráfica**: no gráfica = estadísticos (`describe`, `value_counts`); gráfica = plots (histogramas, boxplots).
- **Univariante vs multivariante** (o bivariante): una variable cada vez (distribución, outliers) frente a relaciones entre variables (correlación, scatter, `groupby`, `hue=`).
- Combinadas salen 4: univariante no gráfica, univariante gráfica, multivariante no gráfica y multivariante gráfica.
- **¿Cuándo usar cada una?** La no gráfica da números exactos y es reproducible y automatizable (por ejemplo, contar nulos). La gráfica deja ver formas, outliers y patrones que los números esconden (por ejemplo, asimetría o bimodalidad). La univariante sirve para entender y limpiar cada columna; la multivariante, para descubrir relaciones, redundancias (p. ej. dos precios casi idénticos → se quita uno, como en vuestro notebook) y variables útiles para un modelo.
- **EDA vs Profiling**: el profiling es la parte técnica y automatizable (tipos, nulos, duplicados). La EDA es más amplia (incluye estadística y visualización).

### EDA con pandas
```python
df.head(); df.shape; df.columns; df.info(); df.dtypes      # inspección inicial
df.describe(); df.describe(include="object")               # perfil numérico y categórico
df["col"].mean(); df["col"].median(); df["col"].quantile([.25, .75])
df["col"].value_counts(); df["col"].unique(); df["col"].nunique()
df.isna().sum(); df.duplicated().sum()                     # chequeos de calidad
df["cn"].str.match(r"^\d{6}$")                             # validación con regex
df.groupby("labtitular")["Precio venta al público con IVA"].agg(["mean", "count"])
df.pivot_table(index="forma_farmaceutica_simplificada", columns="generico", values="nregistro", aggfunc="count")
df.corr(numeric_only=True)
```
Ejemplos de vuestro notebook: `describe().T`, quitar los identificadores y las URLs con `drop(columns=[...])` (no aportan nada al análisis), comparar los 2 precios con un gráfico, quitar "Precio de referencia" porque era redundante y `fillna({"Precio venta al público con IVA": -1})`.

---

## 7. Transformación (sesión 3)

**Definición:** convertir datos crudos, inconsistentes y fragmentados en datos **fiables, estructurados y con significado** que sirvan para el análisis y la toma de decisiones. El objetivo no es "cambiar los hechos", sino hacerlos **fiables, comparables y útiles**. (Ejemplo: Mars Climate Orbiter, unidades métricas frente a imperiales.)

### Los 3 niveles (refinamiento progresivo / pirámide)
| Nivel | Pregunta clave | Qué aporta | Operaciones | Herramientas | Salida |
|---|---|---|---|---|---|
| **Técnica** | ¿Podemos **fiarnos** de los datos y procesarlos? | Fiabilidad y consistencia | Nulos, duplicados, tipos, formatos, validación, entity resolution | **pandas / Python** (también Spark, SQL, dbt) | Dataset limpio y fiable |
| **Analítica** | ¿Qué **revelan** los datos? | Preparación para el análisis | Filtrado, agrupación, agregación, joins, window functions | **SQL**, Spark SQL, DuckDB, DataFrames, dbt | Datasets listos para explorar |
| **Negocio** | ¿Qué **significan** para la organización? | Significado | KPIs, reglas de negocio, atributos derivados, modelos dimensionales (Fact/Dim), vistas, data marts | SQL, dbt, capa semántica, BI (Tableau) | Tablas y dashboards para decidir |

Frases para memorizar: *"Technical makes data reliable. Analytical makes it analyzable. Business makes it meaningful."* · *Trust → Insight → Impact.*

Ejemplos:
- **Técnica:** limpiar fechas, resolver nulos, estandarizar categorías, validar IDs.
- **Analítica:** media de un resultado de laboratorio por brazo de tratamiento, nº de pacientes por centro, tendencia mensual de visitas. (Todavía **no** son KPIs formales.)
- **Negocio:** KPI de seguridad = pacientes con eventos adversos / total de pacientes; regla "solo las visitas validadas cuentan en el informe"; tabla Fact_Visits + Dim_Patient, Dim_Site…

**Fit for purpose:** la transformación técnica es una **base común** (el dato tiene que ser válido sea cual sea su uso). El "fit for purpose" pesa sobre todo en los niveles analítico y de negocio: el mismo dataset limpio necesita agregaciones o KPIs distintos según la pregunta.

### Estrategia: las 4 preguntas antes de transformar
| Pregunta | Depende de | Decisiones típicas |
|---|---|---|
| **¿Qué** transformar? | Los hallazgos de la EDA + las preguntas de negocio y del usuario | Tipos, encoding, erratas, nulos… |
| **¿Hasta dónde?** | Caso de uso, calidad, objetivos | Solo lo que **aporta valor**: evitar sobretransformar |
| **¿Cuándo?** | Arquitectura del pipeline | Durante la ingesta, antes de guardar (ETL), después (ELT), antes del análisis, en continuo (streaming) |
| **¿Cómo?** | El propósito | Técnica (Python/pandas), Analítica (SQL/Spark), Negocio (SQL, dbt, BI) |

### Ciclo de calidad (Data Quality Loop)
Explorar → detectar problemas → elegir la familia de operaciones → aplicar → **validar** → iterar si aparecen problemas nuevos.
**Profiling (EDA) diagnostica** (lee, no modifica) → *decisión* → **la transformación resuelve** (escribe un dataset nuevo, que queda pendiente de validar).

### Dimensiones de calidad del dato
- **Completitud (Completeness)**: ¿faltan valores obligatorios?
- **Validez (Validity)**: ¿cumplen el formato, el tipo y el dominio?
- **Consistencia (Consistency)**: ¿los valores equivalentes se representan igual?
- **Unicidad (Uniqueness)**: ¿hay registros duplicados?
- **Exactitud (Accuracy)**: ¿reflejan la realidad? · **Actualidad (Timeliness)**: ¿están al día? · **Integridad (Integrity)**: ¿se mantienen las relaciones entre datos?

### Las 5 familias de transformación técnica (+ validación)
| Familia | Pregunta | Operaciones | pandas |
|---|---|---|---|
| 1. **Estructural** | ¿Está organizado de forma procesable? | Aplanar JSON, separar o unir columnas, pivot/unpivot, seleccionar campos, convertir tipos, parsear fechas | `json_normalize()`, `explode()`, `melt()`/`pivot()`, `str.split()`, `astype()`, `to_datetime()` |
| 2. **Calidad del dato** | ¿Podemos fiarnos de los valores tal cual? | Nulos, duplicados, valores inválidos, rangos imposibles, dominios inválidos, flags de error | `isna().sum()`, `fillna()`, `dropna()`, `drop_duplicates()`, `between()`, `clip()` |
| 3. **Numérica** | ¿Las magnitudes son comparables? | Escalado y normalización, redondeo, binning (franjas de edad), conversión de unidades, outliers y capping | `round()`, `cut()`/`qcut()`, `clip()`, `MinMaxScaler()`, `df[col]/100` |
| 4. **Estandarización semántica** | ¿Etiquetas distintas son el mismo concepto? | Spain/ESP/ES/España → Spain; M/male → Male; trim y mayúsculas; vocabularios controlados | `str.strip()`, `str.upper()`, `replace()`, `map()`, `str.contains(regex)` |
| 5. **Entity resolution** | ¿Estos registros son la misma entidad? | Coincidencia exacta, fuzzy o por reglas; IDs únicos; P-0210/PAT0210/P0210 → un solo paciente | `drop_duplicates(subset=)`, `merge()`, `groupby().first()`, `rapidfuzz`, `difflib.get_close_matches` |

- **Las familias no son excluyentes:** `to_datetime` es estructural (cambia la representación) **y** de calidad (si el esquema exige una fecha válida). Estandarizar España/ESP es semántico **y** arregla un problema de consistencia.
- Las decisiones de calidad y las numéricas **hay que documentarlas**, porque pueden cambiar las conclusiones.
- Entity resolution es más difícil que quitar duplicados porque los duplicados **no son idénticos**.

### Retos habituales (el iceberg)
- **Técnicos:** problemas de calidad ocultos, esquemas que cambian, formatos inconsistentes, pipelines frágiles.
- **Analíticos:** nivel de agregación equivocado, joins engañosos, **doble conteo**, datos que llegan tarde.
- **De negocio:** KPIs ambiguos, definiciones distintas según el departamento, nadie es dueño de las reglas.
- **Operativos:** transformaciones sin documentar, poca reproducibilidad, procesos manuales, sin monitorización ni linaje.
- *"Los problemas más difíciles rara vez son solo técnicos: vienen de definiciones poco claras y de una gobernanza débil."*

### Ejemplos de código de transformación (para rellenar huecos)
```python
df["estado_aut"] = pd.to_datetime(df["estado_aut"], unit="ms")          # estructural
df["cn"] = df["cn"].astype(str).str.zfill(6)                            # estructural/calidad (recupera los ceros a la izquierda)
df = df.drop_duplicates(subset=["nregistro"])                           # calidad / entity resolution
df["precio"] = df["precio"].fillna(df["precio"].median())               # calidad (imputación)
df = df.dropna(subset=["url_html_ficha_tecnica"])                       # calidad
df = df[df["precio"].between(0, 1000)]                                  # calidad (rango)
df["precio"] = df["precio"].clip(upper=df["precio"].quantile(.99))      # numérica (capping)
df["rango_precio"] = pd.cut(df["precio"], bins=[0, 5, 20, 100, float("inf")], labels=["bajo", "medio", "alto", "muy alto"])  # binning
df["via"] = df["vias_administracion"].str.strip().str.upper()           # semántica
df["receta"] = df["receta"].map({"Sí": 1, "Si": 1, "S": 1, "No": 0, "N": 0})  # semántica
df_largo = df.melt(id_vars=["nregistro"], value_vars=["num_excipientes", "num_principios_activos"])  # wide -> long
df["principios"] = df["pactivos"].str.split(", "); df = df.explode("principios")  # una fila por principio activo
```

---

## 8. Ejercicios tipo examen (intenta hacerlos antes de mirar la solución)

### Teoría
1. Diferencia entre ETL y ELT. ¿Cuándo usarías cada uno?
2. ¿Por qué en la HU-1 la búsqueda es POST y el detalle es GET?
3. ¿Qué devuelve `pd.read_html()` y por qué falla en una página de noticias de la OMS?
4. ¿Qué diferencia hay entre `response.content`, `response.text` y `response.json()`?
5. Di 4 problemas típicos al leer un CSV y el parámetro que soluciona cada uno.
6. ¿La EDA modifica los datos? ¿Qué relación tiene con la transformación técnica?
7. ¿Qué dos (o tres) tipos de EDA/profiling hay y cuándo usarías cada uno?
8. Clasifica: (a) `to_datetime` en una fecha guardada como texto; (b) "ESP" → "Spain"; (c) franjas de edad; (d) unir P-0210 y PAT0210; (e) "tasa de eventos adversos por centro" como KPI; (f) media de edad por sexo.
9. ¿Por qué se pone `dtype={"cn": str}` antes del merge de la HU-3? ¿Por qué `how="left"`?
10. ¿Por qué se usa `\bgraves?\b` y no `.count("grave")`?
11. ¿Para qué sirven `timeout`, `raise_for_status()`, `time.sleep()` y el `User-Agent`?
12. ¿Qué es la paginación y cómo se resuelve con `totalFilas`?

<details><summary><b>Soluciones de teoría</b></summary>

1. ETL transforma antes de cargar (esquemas estrictos o almacenamiento limitado). ELT carga el dato crudo y transforma después, dentro del almacén, a menudo al consultar (warehouses o lakes en la nube; se conserva el dato crudo y se gana flexibilidad). Las operaciones son las mismas; cambia el momento. En la práctica se hace EL(t)T.
2. La búsqueda manda un filtro complejo (una lista JSON con sección, texto y contiene) en el **body** → POST. El detalle es una lectura de un recurso identificado por `nregistro` en la URL → GET.
3. Devuelve una **lista** de DataFrames, uno por cada `<table>`. En la OMS las noticias están en `<div>` repetidos, no en `<table>` → `ValueError: No tables found`. Solución: requests + BeautifulSoup.
4. `content` = bytes crudos; `text` = str decodificado; `json()` = lo parsea a dict/list de Python (para APIs).
5. sep (todo en una columna), encoding (tildes rotas), header/names (cabecera mal leída), na_values (nulos escondidos), dtype (IDs convertidos en número), nrows/skiprows (truncado).
6. No. La EDA **diagnostica** (lee y produce evidencias); la transformación **resuelve** (escribe un dataset nuevo que luego se valida). La 5ª pregunta de la EDA ("¿qué transformaciones hacen falta?") es el plan de transformación.
7. Según las diapositivas: técnico (tipos, nulos, duplicados → lleva a la transformación técnica), estadístico (distribuciones, outliers, correlaciones) y visual (histogramas, boxplots). Clasificación clásica: gráfica/no gráfica y univariante/multivariante (ver sección 6).
8. (a) Estructural (+ calidad); (b) estandarización semántica (+ consistencia); (c) numérica (binning); (d) entity resolution; (e) transformación de negocio (KPI); (f) transformación analítica.
9. Para que el código nacional no se lea como número y no pierda los ceros a la izquierda (si no, la clave no coincide). `left` conserva todos los medicamentos aunque no estén en el nomenclátor (quedan con NaN).
10. `.count` también cuenta "gravemente" o "agravar". `\b` = límite de palabra, `s?` = "s" opcional.
11. timeout: no quedarse colgado esperando; raise_for_status: lanzar una excepción si llega un 4xx/5xx; sleep: no saturar el servidor; User-Agent: identificarte (algunas webs bloquean sin él → 403).
12. La API devuelve los resultados por páginas (p. ej. 200 por página). `n_paginas = ceil(totalFilas / tamanioPagina)` y se hace un bucle `for pagina in range(1, n_paginas+1)` acumulando `resultados`.
</details>

### Práctica: rellena los huecos
```python
# A) POST a CIMA
import requests
url = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica"
payload = [{"seccion": "4.1", "texto": "epilepsia", "contiene": 1}]
response = requests.____(url, params={"pagina": 1}, ____=payload, timeout=30)
response.____()                         # error si 4xx/5xx
datos = response.____()
total = datos["____"]
nregistros = [m["____"] for m in datos["____"]]

# B) GET del detalle
r = requests.get("https://cima.aemps.es/cima/rest/medicamento", ____={"nregistro": nregistros[0]})
v = r.json()
cn = v["presentaciones"][__]["cn"]
fecha = pd.to_datetime(v["estado"]["aut"], unit="____")

# C) Scraping
soup = ____(response.content, "____")
items = soup.____("div", ____="list-view--item")
for it in items:
    titulo = it.find("p", class_="heading").____(strip=True)
    link = it.find("a").____("href")

# D) CSV en español
df = pd.read_csv("fichero.csv", sep="__", encoding="____", na_values=["N/A", "-"], dtype={"cn": ___})

# E) Merge
df_final = df.____(nom, how="____", left_on="cn", right_on="Código Nacional")
```
<details><summary><b>Soluciones</b></summary>

A) `post`, `json` (o `data=json.dumps(payload)` + headers con Content-Type), `raise_for_status`, `json`, `totalFilas`, `nregistro`, `resultados`
B) `params`, `0`, `ms`
C) `BeautifulSoup`, `html.parser`, `find_all`, `class_`, `get_text`, `get`
D) `;`, `latin-1`, `str`
E) `merge`, `left`
</details>

### Práctica: escribe el código
1. Haz una función `obtener_nregistros(enfermedad)` que recorra todas las páginas de CIMA usando `totalFilas`.
2. A partir de una lista de URLs, crea un DataFrame con la URL y el nº de `<table>` de cada una, con control de errores (-1 si falla).
3. Lee una tabla de Wikipedia con `read_html`, quédate con la primera y comprueba su shape, sus tipos y sus nulos.
4. EDA rápido: nº de nulos por columna, duplicados por `nregistro`, top 5 de laboratorios y precio medio por forma farmacéutica.

<details><summary><b>Soluciones</b></summary>

```python
# 1
import math, requests
def obtener_nregistros(enfermedad):
    url = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica"
    payload = [{"seccion": "4.1", "texto": enfermedad, "contiene": 1}]
    r = requests.post(url, params={"pagina": 1}, json=payload, timeout=30); r.raise_for_status()
    d = r.json()
    res = [m["nregistro"] for m in d["resultados"]]
    for p in range(2, math.ceil(d["totalFilas"] / d["tamanioPagina"]) + 1):
        r = requests.post(url, params={"pagina": p}, json=payload, timeout=30); r.raise_for_status()
        res += [m["nregistro"] for m in r.json()["resultados"]]
    return res

# 2
import time
from bs4 import BeautifulSoup
filas = []
for url in urls:
    try:
        r = requests.get(url, timeout=20); r.raise_for_status()
        n = len(BeautifulSoup(r.content, "html.parser").find_all("table"))
    except requests.exceptions.RequestException:
        n = -1
    filas.append({"url": url, "num_tablas": n})
    time.sleep(0.5)
df = pd.DataFrame(filas)

# 3
tables = pd.read_html("https://en.wikipedia.org/wiki/List_of_countries_by_maternal_mortality_ratio")
print(len(tables)); df = tables[0]
print(df.shape, df.dtypes, df.isna().sum(), sep="\n")

# 4
df.isna().sum()
df.duplicated(subset=["nregistro"]).sum()
df["labtitular"].value_counts().head(5)
df.groupby("forma_farmaceutica_simplificada")["Precio venta al público con IVA"].mean()
```
</details>

---

## 9. Cosas mejorables de vuestro código (para el examen y para el proyecto)
- `cima_api.py`: `range(5)` está puesto a mano ("988 filas / 200 por página"). Lo correcto es calcularlo con `totalFilas` y `math.ceil`. Además, el `for i` interno reutiliza la misma variable `i` que el bucle externo.
- `cima_api.py`: no usa `timeout` ni `raise_for_status()`. Si un `GET` falla, `response.json()` rompe el script entero.
- `"excipiente"` vs `"excipientes"`: en `medicamentos_epilepsia.xlsx`, `num_excipientes` vale **0 en los 988 medicamentos**. Casi seguro la clave está mal escrita (en el enunciado aparece como `excipientes`). Con el `or []`, una clave mal escrita da 0 sin avisar. Es un buen ejemplo de por qué hay que hacer EDA: un `value_counts()` lo detecta enseguida.
- `start_epileps_ia.py`: `soup.status_code` no existe en BeautifulSoup (imprime `None`): el status code es de `response`, no de `soup`.
- Indicadores binarios: `float("1")` funciona, pero `int(bool(v.get("comerc")))` es más claro.

---

## 10. Si prefieres estudiar con Claude "normal" (claude.ai)
Sube a un chat **este fichero + los 4 PDFs + `cima_api.py`, `webScraping.py`, `start_epileps_ia.py`, `hu3_nomenclator.py`** y pega este prompt:

> Tengo un examen de Ingeniería de Datos (máster de IA aplicada, Comillas). El temario: extracción (CSV, read_html, API REST con requests, scraping con BeautifulSoup), EDA y transformación (técnica, analítica y de negocio; 5 familias). Adjunto las diapositivas, una guía resumen y el código de mi proyecto (API CIMA de la AEMPS + scraping de fichas técnicas + merge con el Nomenclátor). Hazme de examinador: pregúntame UNA cosa cada vez, mezclando teoría ("¿por qué usarías X y no Y?") y huecos de código para rellenar (POST/GET, sacar campos del JSON, find/find_all, read_csv con parámetros, merge, fillna...). Corrige mi respuesta, explícame el fallo y sube la dificultad poco a poco. Al final, dame un resumen de mis puntos débiles.
