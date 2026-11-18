
import pandas as pd
import shutil
import time
import logging

from pathlib import Path

#from epileps_ia.webScraping_HU2 import *
from epileps_ia import webScraping_HU2


# CONFIGURACIÓN
logger = logging.getLogger(__name__)

RUTA_DATA = Path(__file__).resolve().parents[2] / "data"

"""
RUTA_EXCEL_HU2 = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "medicamentos_epilepsia_HU1_HU2.xlsx"
)
"""

"""
RUTA_EXCEL_HU2_PARCIAL = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "medicamentos_epilepsia_HU1_HU2_Parcial.xlsx"
)
"""

#def guardar_excel_hu2(df, medicamentos_fallidos):
def guardar_excel_hu2(df, fecha):
    """
    Funcion para guardar el excel del HU2

    Se guardan todos los datos del HU1

    Si hay datos que no se pueden obtener estos se guardaran con un valor de -1
    """

    logger.info("Inicio del guardado del Excel hu1-hu2")

    RUTA_TEMPORAL = None

    try:
        nombre_excel = f"medicamentos_epilepsia_HU1_HU2_{fecha}"
        RUTA_EXCEL_DESTINO = RUTA_DATA / f"{nombre_excel}.xlsx"

        # CREAMOS LA CARPETA DATA SI NO EXISTE
        RUTA_EXCEL_DESTINO.parent.mkdir(parents=True, exist_ok=True)

        # DEFINIMOS EL ARCHIVO TEMPORAL
        RUTA_TEMPORAL = RUTA_EXCEL_DESTINO.with_name(RUTA_EXCEL_DESTINO.stem + "_temporal.xlsx")

        # GUARDAMOS EL EXCEL TEMPORAL
        df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

        # SUSTITUIMOS EL EXCEL DEFINITIVO
        RUTA_TEMPORAL.replace(RUTA_EXCEL_DESTINO)
    
        logger.info(f"Excel HU1-HU2 se ha guardado correctamente en: {RUTA_EXCEL_DESTINO}")

        
        #if medicamentos_fallidos:
            # CREAMOS LA CARPETA DATA SI NO EXISTE
        #    RUTA_EXCEL_HU2_PARCIAL.parent.mkdir(parents=True, exist_ok=True)

            # DEFINIMOS EL ARCHIVO TEMPORAL
        #    RUTA_TEMPORAL = RUTA_EXCEL_HU2_PARCIAL.with_name(RUTA_EXCEL_HU2_PARCIAL.stem + "_parcial_temporal.xlsx")

            # GUARDAMOS EL EXCEL TEMPORAL
        #    df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

            # SUSTITUIMOS EL EXCEL DEFINITIVO
        #    RUTA_TEMPORAL.replace(RUTA_EXCEL_HU2_PARCIAL)

        #    logger.info(f"Excel HU1-HU2 Parcial guardado correctamente en: {RUTA_EXCEL_HU2_PARCIAL}")

        #else:
            # CREAMOS LA CARPETA DATA SI NO EXISTE
        #    RUTA_EXCEL_HU2.parent.mkdir(parents=True, exist_ok=True)

            # DEFINIMOS EL ARCHIVO TEMPORAL
        #    RUTA_TEMPORAL = RUTA_EXCEL_HU2.with_name(RUTA_EXCEL_HU2.stem + "_temporal.xlsx")

            # GUARDAMOS EL EXCEL TEMPORAL
        #    df.to_excel(RUTA_TEMPORAL, index=False, na_rep="NaN")

            # SUSTITUIMOS EL EXCEL DEFINITIVO
        #    RUTA_TEMPORAL.replace(RUTA_EXCEL_HU2)

        #    logger.info(f"Excel HU1-HU2 guardado correctamente en: {RUTA_EXCEL_HU2}")

    except Exception:

        # ELIMINAMOS EL ARCHIVO TEMPORAL SI EXISTE
        try:
            if RUTA_TEMPORAL is not None:
                RUTA_TEMPORAL.unlink(missing_ok=True)

        except OSError:
            logger.exception("No se ha podido eliminar el archivo temporal de HU2")

        raise

#def obtener_datos_hu2(df):
def obtener_datos_hu2(df, fecha):
    """
    Recibe el DataFrame obtenido en HU1
    Consulta las fichas técnicas y añade las variables de HU2.
    """

    logger.info("Iniciando extracción de información de HU2")

    # EN CASO DE QUE EN HU1 NO SE HAYAN PODIDO OBTENER LOS DATOS
    # EL DATAFRAME ESTARA VACIO, LO QUE DARA ERROR, POR ELLO PRIEMRO LO COMPROBAMOS
    if df.empty:
        logger.warning("HU1 no ha proporcionado medicamentos para procesar en HU2")
        return df.copy(), False

    # DEFINIMOS LAS VARIABLES QUE QUEREMOS EXTRAER
    ID_SECTION = "4.4"
    ETIQUETA_BUSCAR = "table"

    len_section_column = []
    num_tablas_column = []
    veces_grave_s_column = []

    medicamentos_fallidos = []
    secciones_no_encontradas = []


    # RECORREMOS LAS URL DE LAS FICHAS TÉCNICAS
    urls = df["url_html_ficha_tecnica"]

    for posicion, (indice, url) in enumerate(urls.items(), start=1):

        logger.info(f"Consultando ficha técnica {posicion}/{len(urls)}")

        try:
            # COMPROBAMOS QUE LA URL TIENE VALOR
            if pd.isna(url) or not url:
                raise ValueError("El medicamento no tiene URL de ficha técnica")

            soup = webScraping_HU2.get_url(url)

            # OBTENEMOS LA INFORMACIÓN DE LA SECCIÓN 4.4
            len_section = webScraping_HU2.numPalabrasSeccion(soup, ID_SECTION)

            # SI NO SE ENCUENTRA LA SECCIÓN 4.4, REGISTRAMOS LA INCIDENCIA
            if len_section == -1:
                secciones_no_encontradas.append(indice)

            # CONTAMOS LAS TABLAS
            num_tablas = webScraping_HU2.numEtiquetaBuscar(soup, ETIQUETA_BUSCAR)

            # CONTAMOS LAS VECES QUE APARECE GRAVE/GRAVES
            veces_grave_s = webScraping_HU2.contarPalabraGrave(soup)

            len_section_column.append(len_section)
            num_tablas_column.append(num_tablas)
            veces_grave_s_column.append(veces_grave_s)

        except Exception: # ENGLOBA TODAS LAS EXCEPCIONES
            logger.exception(f"Ha fallado el procesamiento de la ficha técnica: posicion: {posicion}, url: {url}")

            medicamentos_fallidos.append(indice)

            len_section_column.append(-1)
            num_tablas_column.append(-1)
            veces_grave_s_column.append(-1)

        # ESPERAMOS MEDIO SEGUNDO ENTRE CONSULTAS
        time.sleep(0.5)

    # AÑADIMOS LAS NUEVAS COLUMNAS AL DATAFRAME
    df2 = df.copy()

    df2["Volumen Informativo de Seguridad (num palabras)"] = len_section_column
    df2["Complejidad del Desglose Clínico (num tablas)"] = num_tablas_column
    df2["Indicador de Riesgo Severo (num veces grave/s)"] = veces_grave_s_column

    # INFORMAMOS DEL RESULTADO
    logger.info(
        f"Fichas técnicas procesadas sin errores de procesamiento: "
        f"{len(df2) - len(medicamentos_fallidos)}"
    )

    logger.info(f"Total de fichas técnicas fallidas: {len(medicamentos_fallidos)}")
    logger.info(f"Secciones {ID_SECTION} no encontradas: {len(secciones_no_encontradas)}")

    if medicamentos_fallidos:
        logger.warning(f"Índices de medicamentos fallidos en HU2: {medicamentos_fallidos}")
    #else:
    #    logger.info("Todas las fichas técnicas se han procesado correctamente")

    if secciones_no_encontradas:
        logger.warning(f"Índices sin sección {ID_SECTION}: {secciones_no_encontradas}")

    # DETERMINAMOS SI HU2 HA SIDO COMPLETA
    hu2_completo = not medicamentos_fallidos and not secciones_no_encontradas

    if hu2_completo:
        logger.info("Todas las fichas técnicas se han procesado correctamente")
    else:
        logger.warning("HU2 presenta datos faltantes")

    # GUARDAMOS EL EXCEL FINAL
    #guardar_excel_hu2(df2, medicamentos_fallidos)
    guardar_excel_hu2(df2, fecha)
    #hu2_completo = not medicamentos_fallidos

    return df2, hu2_completo
    #return df2



# ESTE ES NUESTRO ARCHIVO ORIGINAL (start_epileps_ia.py) QUE SE HA CAMBIADO POR 
# EL CODIGO ANTERIORI PARA LA AUTOMATIZACION Y TENER
# CONTROL CON LOS LOGS
"""
#LEE EL EXCEL

#excel_original = "Pruebas2.xlsx"
#excel_copia = "Pruebas2_HU1_HU2.xlsx"

excel_original = "medicamentos_epilepsia.xlsx"
excel_copia = "medicamentos_epilepsia_HU1_HU2.xlsx"

shutil.copy2(excel_original, excel_copia)


#df = pd.read_csv("Pruebas2.csv", sep=";") #PAra csv. El ; indica la separacion de cada componente de una fila
df = pd.read_excel(excel_copia) #para excel

print(df.columns)
#urls = df["url"]
urls = df["url_html_ficha_tecnica"]

print("urls: ", urls)

len_section_column = []
num_tablas_column = []
veces_grave_s_column = []

ID_SECTION = "4.4"
ETIQUETA_BUSCAR = "table"

""
#Recorro cada una de las url sacadas del csv
#Y actuo sobre ellas
""
i=1
for url in urls:
    print("\n", i)
    print("URL: ", url)
    try:
        soup = get_url(url)
        print(f"    OK: {soup.status_code}")


        len_section = numPalabrasSeccion(soup, ID_SECTION) 
        print("\nLEN: ", len_section)
        len_section_column.append(len_section)

        num_tablas = numEtiquetaBuscar(soup, ETIQUETA_BUSCAR)
        print("NUM ETIQUETA: ", num_tablas)
        num_tablas_column.append(num_tablas)

        veces_grave_s = contarPalabraGrave(soup)
        print("GRAVE: ", veces_grave_s)
        veces_grave_s_column.append(veces_grave_s)

    except requests.exceptions.Timeout:
        len_section_column.append(-1)
        num_tablas_column.append(-1)
        veces_grave_s_column.append(-1)

        print(f"    -> TIMEOUT: {url}")

    except requests.exceptions.RequestException as e:
        len_section_column.append(-1)
        num_tablas_column.append(-1)
        veces_grave_s_column.append(-1)
        print(f"    -> ERROR: {e}")

    i = i+1
    print("  -> Esperando 0.5 segundos...")

    time.sleep(0.5)

print("\nCOLUMNS:\n", len_section_column)
print(num_tablas_column)
print(veces_grave_s_column)

df["Volumen Informativo de Seguridad (num palabras)"] = len_section_column
df["Complejidad del Desglose Clínico (num tablas)"] = num_tablas_column
df["Indicador de Riesgo Severo (num veces grave/s)"] = veces_grave_s_column

#GUARDA EN EL EXCEL
#df.to_csv("Pruebas2.csv", sep=";", index=False) #para csv.
#df.to_excel("medicamentos_epilepsia.xlsx", index=False) #para excel. El index=False indica que no quiero columna adicional indicando numeor fila
df.to_excel(excel_copia, index=False) #para excel. El index=False indica que no quiero columna adicional indicando numeor fila


print("EXCEL GUARDADO")
"""