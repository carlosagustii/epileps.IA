""" 
hu3: Se van a añadir a los datos de la hu2, datos económicos del csv Nomenclátor del Ministerio de Sanidad

Hay que cruzar el xlsx generado en la hu2 con el fichero csv Nomenclator usando el Código Nacional (cn) y guardarlo en un nuevo xlsx.

"""
import pandas as pd 
import logging
import requests
import io

from pathlib import Path


# CONFIGURACIÓN
logger = logging.getLogger(__name__)

# DE ESTA DIR SE SACAN LO PARAMETROS Y LA WEB
# SE HA SACADO HACIENDO CLICK DERECHO EN EL BOTON DE DESCARGA Y COPIANDO LA DIRECCION
# https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=buscarProductos&especialidad=%25%25%25&d-4015021-e=1&6578706f7274=1

URL_NOMENCLATOR = "https://www.sanidad.gob.es/profesionales/nomenclator.do"

# ESTOS PARAMETROS CORRESPONDEN A LA EXPORTACION DEL LISTADO COMPLETO EN CSV
PARAMETROS_NOMENCLATOR = { 
    "metodo": "buscarProductos",
    "especialidad": "%%%",
    "d-4015021-e": "1",
    "6578706f7274": "1"
}

RUTA_DATA = Path(__file__).resolve().parents[2] / "data"

COLUMNAS_NOMENCLATOR = [
    "Código Nacional",
    "Estado",
    "Precio venta al público con IVA",
    "Precio de referencia",
    "Tratamiento de larga duración",
    "Especial control médico"
]


def descargar_nomenclator(fecha):

    """
    Descarga el CSV completo del Nomenclátor del Ministerio de Sanidad
    y lo guarda en la carpeta data.
    """

    logger.info("Iniciando descarga del Nomenclátor")

    RUTA_DATA.mkdir(parents=True, exist_ok=True)

    nombre_csv = f"Nomenclator_{fecha}.csv"
    RUTA_CSV = RUTA_DATA / nombre_csv

    RUTA_TEMPORAL = RUTA_CSV.with_name(RUTA_CSV.stem + "_temporal.csv")

    try:
        # SE INTENTA ACCEDER AL CSV Y DESCARGAR LA INFORMACION
        # RESPONSE CONTIENE EL CONTENIDO EN BYTES DEL HTTP
        response = requests.get(
            URL_NOMENCLATOR,
            params=PARAMETROS_NOMENCLATOR,
            timeout=60
        )

        response.raise_for_status()

        if not response.content:
            raise ValueError("El CSV descargado (Nomenclator) está vacío")

        # COMPRUEBO QUE LO DESCARGADO ES LO QUE REALMENTE NECESITO
        nomenclator = pd.read_csv(
            io.BytesIO(response.content), # HACE QUE PANDAS PUEDA LEEER BYTES DIRECTAMENTE
            nrows=0, # QUE SE LEAN SOLO LOS ENCABEZADOS
            encoding="utf-8-sig"
        )

        # COLUMNAS QUE NECESITO - LAS QUE TIENE EL ARCHIVO
        columnas_faltantes = set(COLUMNAS_NOMENCLATOR) - set(nomenclator.columns)

        if columnas_faltantes:
            raise ValueError(f"La descarga no contiene las columnas esperadas. Faltan: {columnas_faltantes}")

        # PRIMERO GUARDAMOS EN BYTES EL ARCHIVO TEMPORAL
        RUTA_TEMPORAL.write_bytes(response.content)

        # SUSTITUIMOS EL ARCHIVO DEFINITIVO
        RUTA_TEMPORAL.replace(RUTA_CSV)

        logger.info(f"Nomenclator descargado correctamente: {RUTA_CSV}")

        return RUTA_CSV

    except Exception:
        try:
            RUTA_TEMPORAL.unlink(missing_ok=True)
        except OSError:
            logger.exception("No se ha podido eliminar el CSV temporal del nomenclator")

        logger.exception("Ha fallado la descarga del Nomenclátor")
        raise

def leer_nomenclator(ruta_csv):
    """
    Lee únicamente las columnas necesarias del Nomenclátor.
    El Código Nacional se lee como texto para facilitar el cruce.
    """

    logger.info("Leyendo el CSV del Nomenclátor")

    # LEEMOS EL CSV (BYTES) Y LO PASAMOS A UN CSV INTERPRETABLE
    nomenclator = pd.read_csv(
        ruta_csv,
        usecols=COLUMNAS_NOMENCLATOR,
        dtype={"Código Nacional": "string"},
        encoding="utf-8-sig"
    )

    logger.info(f"Registros leídos del Nomenclator: {len(nomenclator)}")

    return nomenclator

def guardar_excel_hu3(df, fecha):
    """
    Guarda el DataFrame resultante de HU3 en un nuevo Excel.
    """

    logger.info("Inicio del guardado del Excel hu1-hu2-hu3")

    RUTA_TEMPORAL = None

    try:

        nombre_excel = (f"medicamentos_epilepsia_HU1_HU2_HU3_{fecha}")

        RUTA_EXCEL_DESTINO = (RUTA_DATA / f"{nombre_excel}.xlsx")

        RUTA_EXCEL_DESTINO.parent.mkdir(parents=True, exist_ok=True)

        RUTA_TEMPORAL = RUTA_EXCEL_DESTINO.with_name(
            RUTA_EXCEL_DESTINO.stem + "_temporal.xlsx"
        )

        df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

        RUTA_TEMPORAL.replace(RUTA_EXCEL_DESTINO)

        logger.info(
            f"Excel HU3 guardado correctamente en: "
            f"{RUTA_EXCEL_DESTINO}"
        )

    except Exception:
        try:
            if RUTA_TEMPORAL is not None:
                RUTA_TEMPORAL.unlink(missing_ok=True)

        except OSError:
            logger.exception("No se ha podido eliminar el Excel temporal de HU3")

        raise

def obtener_datos_hu3(df, fecha):

    """
    Recibe el DataFrame obtenido en HU2.

    Descarga el Nomenclátor, selecciona las columnas necesarias
    y añade los datos económicos mediante el Código Nacional.

    Devuelve el DataFrame ampliado y un booleano que indica
    si todos los medicamentos han encontrado coincidencia.
    """

    logger.info("Iniciando procesamiento de HU3")

    # DESCARGAMOS Y LEEMOS EL NOMENCLÁTOR
    ruta_csv = descargar_nomenclator(fecha)
    nomenclator = leer_nomenclator(ruta_csv)

    # COPIAMOS EL DATAFRAME DE HU2
    df3 = df.copy()

    # NORMALIZAMOS LOS CÓDIGOS PARA REALIZAR EL CRUCE
    # ELIMINAMOS ESPACION Y EL DECIMAL .0
    # CREAMOS 2 COLUMNS NUEVAS PARA QUE TENAGN EL FORMATO QUE QUEREMOS Y QUE REPRESENTEN DESDE DONDE VAMOS A UNIRLOS
    # \. ES UN .    ;  0 ES EL NUMEORO CERO     ;   $ INDICA EL FINAL DEL TEXTO
    df3["_cn_cruce"] = (
        df3["cn"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    nomenclator["_cn_cruce"] = (
        nomenclator["Código Nacional"]
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    # CRUZAMOS LOS DATAFRAMES
    df3 = df3.merge(
        nomenclator,
        how="left",
        on="_cn_cruce", # LOS UNIMOS POR EL _CN_CRUCE
        indicator=True, # ANADE TEMPORALMENTE _MERGE (COLUMNA) pARA IDENTIFICAR LO QUE SUCEDE EN CADA CRUCE
        validate="many_to_one" # COMPRUEBA QUE CADA CODIGO NACIONAL DEL NOMENCLATOR APARECE COMO MAX UNA VEZ
    )

    # CONTAMOS LAS COINCIDENCIAS
    encontrados = (df3["_merge"] == "both").sum() # BOTH -> QUE EL MEDICAMENTEO APRAEZCA EN AMBOS ARCHIVOS
    sin_coincidencia = (df3["_merge"] == "left_only").sum() # LEFT_ONLY -> QUE PARAREZCA EN HU2 PERO NO EN NOMENCLATOR

    logger.info(f"Medicamentos con coincidencia en el Nomenclator: {encontrados}")

    logger.info(f"Medicamentos sin coincidencia en el Nomenclator: {sin_coincidencia}")

    # ELIMINAMOS LAS COLUMNAS AUXILIARES
    df3 = df3.drop(
        columns=[
            "Código Nacional", # LO ELIMINAMOS AY QUE ES LO MISMO QUE CN
            "_cn_cruce", # LO ELIMINAMOS YA QUE ERA UN AUXILIAR PARA UNIRLOS
            "_merge" # LOS ELIMINAMOS PORQUE ES UNA COLUMUNA AUXILIAR PARA COMPROBAR COINCIDENCIAS
        ]
    )

    # DETERMINAMOS SI HU3 ESTÁ COMPLETA
    hu3_completo = (sin_coincidencia == 0)

    if hu3_completo:
        logger.info("HU3 finalizada: todos los medicamentos tienen coincidencia en el Nomenclator")
    else:
        logger.warning("HU3 finalizada: algunos medicamentos no tienen coincidencia en el Nomenclator")
        # EN ESTE CASO SE DEVULEVE FALSE (hu3_completo)

    # GUARDAMOS EL EXCEL FINAL
    guardar_excel_hu3(df3, fecha)

    return df3, hu3_completo


# ESTE ES NUESTRO ARCHIVO ORIGINAL QUE SE HA CAMBIADO POR 
# EL CODIGO ANTERIORI PARA LA AUTOMATIZACION Y TENER
# CONTROL CON LOS LOGS
"""
#Ficheros 
excel_hu2 = "src/epileps_ia/medicamentos_epilepsia_HU1_HU2.xlsx"
csv_nomenclator = "src/epileps_ia/20260927_Nomenclator_de_Facturacion.csv"
excel_hu3 = "src/epileps_ia/medicamentos_epilepsia_HU3.xlsx"


#Leemos el excel de la hu2

df = pd.read_excel(excel_hu2, dtype={"cn" : str})
print ("medicamentos hu2" , len(df))

#Leemos el csv del nomenclator 
columnas = [
    "Código Nacional",
    "Estado",
    "Precio venta al público con IVA",
    "Precio de referencia",
    "Tratamiento de larga duración",
    "Especial control médico",
]

nomenclator = pd.read_csv(csv_nomenclator, usecols=columnas, dtype={"Código Nacional": str})
print("Filas nomenclator: ", len(nomenclator))

#Lo cruzamos por cn 
""
merge une las dos tablas usando el cn del excel y el Código Nacional del csv.
how="left" mantiene todos los medicamentos de la HU-2, aunque su cn no esté
en el nomenclátor (en ese caso las columnas nuevas quedan vacías).
""

df_hu3 = df.merge(nomenclator, how="left", left_on="cn", right_on="Código Nacional")

# el Código Nacional es igual que el cn, así que lo quitamos para no repetirlo
df_hu3 = df_hu3.drop(columns=["Código Nacional"])

encontrados = df["cn"].isin(nomenclator["Código Nacional"]).sum()
print("Con cn en el nomenclator: ", encontrados)
print("Sin coincidencia: ", len(df) - encontrados)


# GUARDA EL EXCEL
df_hu3.to_excel(excel_hu3, index=False)
print("EXCEL GUARDADO: ", excel_hu3)
"""