import requests
import pandas as pd
import json
import numpy as np
import math
import logging


from pathlib import Path


# CONFIGURACIÓN
logger = logging.getLogger(__name__) # INDICO EL LOG

URL_BUSQUEDA = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica"
URL_MEDICAMENTO = "https://cima.aemps.es/cima/rest/medicamento"

CONDICIONES_BUSQUEDA = [
    {
        "seccion": "4.1",
        "texto": "epilepsia",
        "contiene": 1
    }
]

RUTA_DATA = Path(__file__).resolve().parents[2] / "data"


"""
RUTA_EXCEL = (
    Path(__file__).resolve().parents[2] # SE SUBEN DOS CARPETAS EPILESIA -> SRC -> APILEPSIA
    / "data" # SE ACCEDE A DATA
    / "medicamentos_epilepsia_HU1.xlsx" # NOMBRE DEL EXCEL
)

# RUTA DEL EXCEL SI HAY MEDICAMENTOS A LOS QUE NO SE HA PODIDO ACCEDER
RUTA_EXCEL_PARCIAL = (
    Path(__file__).resolve().parents[2] # SE SUBEN DOS CARPETAS EPILESIA -> SRC -> APILEPSIA
    / "data" # SE ACCEDE A DATA
    / "medicamentos_epilepsia_HU1_Parcial.xlsx" # NOMBRE DEL EXCEL
)
"""

# OBTENER TODOS LOS NÚMEROS DE REGISTRO
def obtener_n_registros(session): 

    """
    Se obtienne todos los numeros de registro
    """

    # SE HACE LA LLAMADA A LA PRIMERA PAGINA
    # DE LA QUE SECARAN EL NUMOER TOTAL DE REGISTROS Y
    # EL NUMEOR DE REGISTROS POR PAGINA
    response = session.post( # SE HACE POST
        URL_BUSQUEDA,
        params={"pagina": 1}, # SE ACCEDE A LA PRIMERA PAGINA
        json=CONDICIONES_BUSQUEDA, 
        timeout=30 # ESTO SE USA PARA QUE SI LA PAGINA NO RESPONDE EL POST SE PARE
    )

    response.raise_for_status() # INDICA EL STATUS DE LA RESPUESTA: 200 ES QUE VA BIEN
    respuesta_json = response.json() # CONSIGUES LA INFORMACION EN FORMATO JSON

    total_filas = respuesta_json["totalFilas"] # NUMOER TOTAL DE REGISTROS
    tamanio_pagina = respuesta_json["tamanioPagina"] # NUMEOR DE REGISTROS POR PAGINA

    # cALCULAMOS NUM TOTAL PAGINAS
    total_paginas = math.ceil(total_filas / tamanio_pagina)

    n_registros = []

    # GUARDAMOS LOS REGISTROS DE LA PRIMERA PAGINA
    for medicamento in respuesta_json["resultados"]:
        n_registros.append(medicamento["nregistro"])

    # CONSULTAMOS EL RESTO DE PAGINAS 
    for pagina in range(2, total_paginas + 1): # DESDE LA 2 A LA N (RANGE VA HASTA N-1, POR ESO EL +1)

        response = session.post( # SE HACE POST
            URL_BUSQUEDA,
            params={"pagina": pagina},
            json=CONDICIONES_BUSQUEDA,
            timeout=30
        )

        response.raise_for_status()
        respuesta_json = response.json()

        # GUARDAMOS EL RESTO DE REGISTROS PARA CADA PAGINA
        for medicamento in respuesta_json["resultados"]:
            n_registros.append(medicamento["nregistro"])

    # print(f"Se han encontrado {len(n_registros)} medicamentos") 
    # # NO NECESITAMOS YA EL PRINT PORQUE EL LOG SE IMPRIME TAMBIEN POR PANTALLA
    logger.info(f"Se han encontrado {len(n_registros)} medicamentos")
    return n_registros


# OBTENER LOS DATOS DE CADA MEDICAMENTO
def obtener_datos_medicamento(session, registro):

    """
    Por cada medicamento se obtienen sus datos
    """
    response = session.get( # SE HACE UN GET
        URL_MEDICAMENTO,
        params={"nregistro": registro}, # SE BUSCA ESE MEDICAMENTO
        timeout=30
    )

    response.raise_for_status()

    valores = response.json()

    # SE AHCEN COMPROBACIONES ANTES DE ASIGANR LOS VALORES AL MEDICAMNETO (FILA)

    # COMPRUEBA QUE PRESENTACIONES Y EL PRIMER VALOR DE PRESENTACIONES (cn) 
    # TENGA VALOR SI NO ES UN NaN
    cn = (int(valores.get("presentaciones")[0].get("cn")) 
        if valores.get("presentaciones") and valores.get("presentaciones")[0].get("cn")
        else np.nan)

    forma_fs = valores.get("formaFarmaceuticaSimplificada") or {} # SI NO EXISTE SE ASIGNA UN DICCIONARIO VACIO

    vias_administracion = (
        valores.get("viasAdministracion")[0].get("nombre")
        if valores.get("viasAdministracion")
        else np.nan)

    fila = {
        "nregistro": valores.get("nregistro"),
        "nombre": valores.get("nombre"),
        "pactivos": valores.get("pactivos"),
        "labtitular": valores.get("labtitular"),
        "labcomercializador": valores.get("labcomercializador"),

        "cn": cn,

        "dosis": valores.get("dosis"),

        "forma_farmaceutica_simplificada": forma_fs.get("nombre"), # SERA NONE SI ES VACIO

        "estado_aut": pd.to_datetime(
            valores.get("estado", {}).get("aut"), # ES VACIO SI ESTADO NO EXISTE
            unit="ms",
            errors="coerce" # DEVUELVE NAT (NOT A TIME) SI LA FECHA NO ES VALIDA
        ),

        "estado_rev": pd.to_datetime(
            valores.get("estado", {}).get("rev"),
            unit="ms",
            errors="coerce"
        ),

        "vias_administracion": vias_administracion,

        "comercializado": float(valores.get("comerc") is True),
        "requiere_receta": float(valores.get("receta") is True),
        "generico": float(valores.get("generico") is True),
        "afecta_conduccion": float(valores.get("conduc") is True),
        "triangulo_negro": float(valores.get("triangulo") is True),
        "medicamento_huerfano": float(valores.get("huerfano") is True),
        "biosimilar": float(valores.get("biosimilar") is True),

        "url_html_ficha_tecnica": (
            [doc.get("urlHtml") for doc in valores.get("docs", [])
             if doc.get("tipo") == 1
             and doc.get("urlHtml", "").lower().endswith(".html")]
            or [np.nan]
        )[0],

        "url_foto_materiales": (
            [foto.get("url") for foto in valores.get("fotos", [])
             if "material" in foto.get("tipo", "").lower()
             and foto.get("url", "").lower().endswith(".jpg")]
            or [np.nan]
        )[0],

        "num_registros_atc": len(valores.get("atcs") or []),
        "num_principios_activos": len(valores.get("principiosActivos") or []),
        "num_excipientes": len(valores.get("excipiente") or [])
    }

    return fila


def guardar_excel(df, medicamentos_fallidos, fecha):

    """
    Mediante esta funcion guardamos el excel
    Solo lo guardamos si no hay problemas en la carga de los datos
    En caso de que hubiera el archivo "antiguo" no se sobreescribe
    """

    RUTA_TEMPORAL = None

    try:

        nombre_excel = f"medicamentos_epilepsia_HU1_{fecha}"
        
        # COMPRUEBO SI SE PUDO ACCEDER A TODOS LOS DATOS DE HU1 O SOLO A ALGUNOS
        if medicamentos_fallidos:
            nombre_excel += "_Parcial"

        RUTA_EXCEL_DESTINO = RUTA_DATA / f"{nombre_excel}.xlsx"

        # CREAMOS LA CARPETA DATA SI NO EXISTE
        RUTA_EXCEL_DESTINO.parent.mkdir(parents=True, exist_ok=True)

        # DEFINIMOS UN ARCHIVO TEMPORAL
        # CON EL STEM CONSEGUIMOS EL NOMBRE DEL ARCHIVO SIN LA EXTENSION
        RUTA_TEMPORAL = RUTA_EXCEL_DESTINO.with_name(RUTA_EXCEL_DESTINO.stem + "_temporal.xlsx")

        # GUARDAMOS EL EXCEL TEMPORAL
        df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

        # SI SE HA GUARDADO CORRECTAMENTE,
        # SUSTITUIMOS EL EXCEL DEFINITIVO
        RUTA_TEMPORAL.replace(RUTA_EXCEL_DESTINO)

        logger.info(f"Excel hu1 guardado correctamente en: {RUTA_EXCEL_DESTINO}")
        
        
        # SI HAY MEDICAMENTOS QUE NO SE HAN PODIDO ACCEDER EL EXCEL ES PARCIAL
        # if medicamentos_fallidos:
        #    # CREAMOS LA CARPETA DATA SI NO EXISTE
        #    RUTA_EXCEL_PARCIAL.parent.mkdir(parents=True, exist_ok=True)

        #   # DEFINIMOS UN ARCHIVO TEMPORAL
        #    # CON EL STEM CONSEGUIMOS EL NOMBRE DEL ARCHIVO SIN LA EXTENSION
        #    RUTA_TEMPORAL = RUTA_EXCEL_PARCIAL.with_name(RUTA_EXCEL_PARCIAL.stem + "_parcial_temporal.xlsx")

        #    # GUARDAMOS EL EXCEL TEMPORAL
        #    df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

            # SI SE HA GUARDADO CORRECTAMENTE,
            # SUSTITUIMOS EL EXCEL DEFINITIVO
        #    RUTA_TEMPORAL.replace(RUTA_EXCEL_PARCIAL)

        #    logger.info(f"Excel guardado correctamente en: {RUTA_EXCEL_PARCIAL}")

        # SI SE HA PODIDO ACCEDER A TODOS LOS MEDICAMENTOS EL EXCEL ES COMPLETO
        #else:
            # CREAMOS LA CARPETA DATA SI NO EXISTE
        #    RUTA_EXCEL.parent.mkdir(parents=True, exist_ok=True)

            # DEFINIMOS UN ARCHIVO TEMPORAL
            # CON EL STEM CONSEGUIMOS EL NOMBRE DEL ARCHIVO SIN LA EXTENSION
        #    RUTA_TEMPORAL = RUTA_EXCEL.with_name(RUTA_EXCEL.stem + "_temporal.xlsx")

            # GUARDAMOS EL EXCEL TEMPORAL
        #    df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

            # SI SE HA GUARDADO CORRECTAMENTE,
            # SUSTITUIMOS EL EXCEL DEFINITIVO
        #    RUTA_TEMPORAL.replace(RUTA_EXCEL)

        #    logger.info(f"Excel guardado correctamente en: {RUTA_EXCEL}")

    except Exception:

        # ELIMINAMOS EL ARCHIVO TEMPORAL SI EXISTE
        try:
            if RUTA_TEMPORAL is not None:
                RUTA_TEMPORAL.unlink(missing_ok=True)
        except OSError:
            logger.exception("No se ha podido eliminar el archivo temporal del hu1")

        raise


# FUNCIÓN PRINCIPAL
def obtener_medicamentos_epilepsia(fecha):

    """
    Mediante esta funcion se obtienen los medicamentos de la epilepsia al hacer 
    peticiones post y get a la pagina de cima
    """

    # print("Iniciando búsqueda de medicamentos en CIMA...")
    logger.info("Iniciando búsqueda de medicamentos en CIMA...")
    
    # CREAMOS UNA SESION HTTP
    # DE ESTA MANERA SE EVITA TENER QUE CREAR NUEVAS CONEXIONES CADA VEZ 
    # QUE SE HAGA UN POST O GET
    with requests.Session() as session:

        # OBTENEMOS TODOS LOS NUMEROS DE REGISTRO
        n_registros = obtener_n_registros(session)

        # CONSULTAMOS LA INFORMACIONN DE CADA MEDICAMENTO
        columnas = []
        medicamentos_fallidos = []

        for posicion, registro in enumerate(n_registros, start=1):

            # print(f"Consultando medicamento {posicion}/{len(n_registros)}")
            logger.info(f"Consultando medicamento {posicion}/{len(n_registros)}")
            # SE AV AINTENTAR ACCEDER AL MEDICAMENTO Y CONSEGUIR SUS DATOS
            # SI NO SE PUDIERA SE GUARDARA EL REGISTRO DEL MEDICAMENTO Y SE INDICARA EN UN LOG
            # SE CONTINUA CON EL RESTO DE MEDICAMNETOS, ASI NO SE PARA EL PROGRAMA POR UN ERROR DE ACCESO
            try:
                fila = obtener_datos_medicamento(session, registro)
                columnas.append(fila)
            except Exception:
                logger.exception(f"Ha fallado la consulta del medicamento {registro}")
                medicamentos_fallidos.append(registro)
                continue

    # INFORMAMOS DEL RESULTADO DE LAS CONSULTAS
    logger.info(f"Medicamentos obtenidos correctamente: {len(columnas)}")
    logger.info(f"Total de medicamentos fallidos: {len(medicamentos_fallidos)}")

    if medicamentos_fallidos:
        logger.warning(f"Lista de medicamentos fallidos: {medicamentos_fallidos}")
    else:
        logger.info("Todos los medicamentos se han consultado correctamente.")


    df = pd.DataFrame(columnas)

    # EXPORTAMOS EL EXCEL
    guardar_excel(df, medicamentos_fallidos, fecha)

    #return df

    # COMPRUEBO SI MI EXCEL DE MEDICAMENTOS DEL HU1 ESTA COMPLETO O NO
    # FALSE si no esta completo
    # TRUE si esta completo
    hu1_completo = not medicamentos_fallidos 

    # DEVUELVO EL DATAFRAME Y SI ESTA O NO "COMPLETO"
    return df, hu1_completo

    """
    # CREAMOS LA CARPETA DATA SI NO EXISTE
    RUTA_EXCEL.parent.mkdir(parents=True, exist_ok=True)

    # EXPORTAMOS A EXCEL
    df.to_excel(RUTA_EXCEL, index=False, na_rep="NaN")

    # print(f"Excel guardado correctamente en: {RUTA_EXCEL}")
    logger.info(f"Excel guardado correctamente en: {RUTA_EXCEL}")
    
    return df
    """



# ESTE ERA NUESTRO CODIGO INICIAL.
# AHORA SE HA DIVIDIDO PARA QUE SE PUEDIERA AUTOMATIZAR MEJOR
"""
pagina = 1
n_registros = []
for i in range(5): #el total de filas es 988 y cada pagina son 200
    URL_BUSQUEDA = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="+ str(pagina) 
    URL_MEDICAMENTO = "https://cima.aemps.es/cima/rest/medicamento"
    payload = json.dumps([
    {
        "seccion": "4.1",
        "texto": "epilepsia",
        "contiene": 1
    }
    ])
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", URL_BUSQUEDA, headers=headers, data=payload)
    respuesta_json=response.json() #devuelve diccionario de listas
    lista=respuesta_json["resultados"] #devuelve lista de diccionarios

    for i in lista:
        n_registros.append(i["nregistro"])#con estos nregistros hacemos posteriormente el get
    pagina+=1


columnas = []
for registro in n_registros:
    url = "https://cima.aemps.es/cima/rest/medicamento"

    params = {
        "nregistro": registro
    }

    response = requests.get(url, params=params)

    valores = response.json()
    fila = {
        "nregistro": valores.get("nregistro"),
        "nombre": valores.get("nombre"),
        "pactivos": valores.get("pactivos"),
        "labtitular": valores.get("labtitular"),
        "labcomercializador": valores.get("labcomercializador"),
        "cn": int(valores.get("presentaciones")[0].get("cn")),
        "dosis": valores.get("dosis"),
        "forma_farmaceutica_simplificada": valores.get("formaFarmaceuticaSimplificada")["nombre"],
        "estado_aut": pd.to_datetime(valores.get("estado").get("aut"), unit = "ms"), #nos lo dan en un formato raro que con esta función se pasa a fecha formateada
        "estado_rev": pd.to_datetime(valores.get("estado").get("rev"), unit= "ms") if valores.get("estado").get("rev") is not None else float("NaN"),
        "vias_administracion": valores.get("viasAdministracion")[0]["nombre"],  #nos lo dan en un formato raro que con esta función se pasa a fecha formateada
        "comercializado": float("1") if valores.get("comerc") is True else float("0"), #Indicador binario (1 si el campo comerc es verdadero, 0 en caso contrario)
        "requiere_receta": float("1") if valores.get("receta") is True else float("0"),    
        "generico": float("1") if valores.get("generico") is True else float("0"),
        "afecta_conduccion": float("1") if valores.get("conduc") is True else float("0"),
        "triangulo_negro":float("1") if valores.get("triangulo") is True else float("0"),
        "medicamento_huerfano": float("1") if valores.get("huerfano") is True else float("0"),
        "biosimilar": float("1") if valores.get("biosimilar") is True else float("0"),
        "url_html_ficha_tecnica": ([doc.get("urlHtml") for doc in valores.get("docs", []) if doc.get("tipo") == 1 and doc.get("urlHtml", "").lower().endswith(".html")] or [np.nan])[0],
        "url_foto_materiales": ([foto.get("url") for foto in valores.get("fotos", []) if "material" in foto.get("tipo", "").lower() and foto.get("url", "").lower().endswith(".jpg")] or [np.nan])[0],
        "num_registros_atc": len(valores.get("atcs")),
        "num_principios_activos": len(valores.get("principiosActivos") or []), #el or por si devuelve None la API, que me lo ha hecho con excipientes
        "num_excipientes": len(valores.get("excipiente") or [])
    }
    columnas.append(fila)
df = pd.DataFrame(columnas) #meto todas las filas añadidas en cada iteración asignada a cada nregistro
#print(df.head())

#ORIGINAL:
df.to_excel("src/epileps_ia/medicamentos_epilepsia.xlsx", index=False, na_rep="NaN") #lo pasamos al excel y quier que se vean los NaN

# df.to_excel("../../data/medicamentos_epilepsia_Pruebas.xlsx", index=False, na_rep="NaN") #lo pasamos al excel y quier que se vean los NaN

"""