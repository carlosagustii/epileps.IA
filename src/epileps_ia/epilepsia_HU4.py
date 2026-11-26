
# HU4 limpieza de los datos (EDA)


import logging
from pathlib import Path
import pandas as pd


logger = logging.getLogger(__name__)

RUTA_DATA = Path(__file__).resolve().parents[2] / "data"  # epileps_ia/ src/ epileps.IA

COLUMNAS_SCRAPING = [
    "Volumen Informativo de Seguridad (num palabras)",
    "Complejidad del Desglose Clínico (num tablas)",
    "Indicador de Riesgo Severo (num veces grave/s)",
]
COLUMNAS_URL = ["url_html_ficha_tecnica", "url_foto_materiales"]

def sacar_unidad(texto):
    texto = str(texto).lower()

    if "desconocida" in texto:
        return None

    if "mbq" in texto:
        unidad = "mbq"
    elif "%" in texto:
        unidad = "%"
    else:
        unidad = "mg"  # si no pone nada, asumimos mg

    if "ml" in texto:
        unidad = unidad + "/ml"

    return unidad


def sacar_numero(texto):
    numero = ""
    for letra in str(texto):
        if letra.isdigit():
            numero = numero + letra
        elif letra in ".," and numero != "":
            numero = numero + letra
        elif numero != "":
            break  # el nº ya ha terminado

    if numero == "":
        return None  #es desconocida

    # "1.500" es milquinientos, no 1,5
    if "." in numero and len(numero.split(".")[1]) == 3:

        numero = numero.replace(".", "")

    numero = numero.replace(",", ".")  # "cambiamos , por .
    return float(numero)


def obtener_datos_hu4(df, fecha):

    logger.info(f"Iniciando la limpieza de {len(df)} medicamentos")
    df4 = df.copy()

    # quitar meds ssin precio y precio de ref 
    df4 = df4.dropna(subset=["Precio venta al público con IVA"])
    df4 = df4.drop(columns=["Precio de referencia"])
    logger.info(f"Quedan {len(df4)} medicamentos con precio")

    # quitar meds en los que ha fallado el scraping de la HU2
    #la hi5 no acepta valores negativos 
    con_fallo = (df4[COLUMNAS_SCRAPING] == -1).any(axis=1)

    df4 = df4[~con_fallo]

    if con_fallo.sum() > 0:
        logger.warning(f"Quitados {con_fallo.sum()} medicamentos con fallo de scraping en la HU2")

    # quitar colum que no interesan y ctes 
    df4 = df4.drop(columns=["nregistro", "cn", "estado_rev", "estado_aut"])
    df4 = df4.drop(columns=["requiere_receta", "medicamento_huerfano", "biosimilar",
                            "num_registros_atc", "num_excipientes", "Especial control médico"])

    #quitar duplicados 
    columnas_datos = [c for c in df4.columns if c not in COLUMNAS_URL]
    logger.info(f"Duplicados quitados: {df4.duplicated(subset=columnas_datos).sum()}")
    df4 = df4.drop_duplicates(subset=columnas_datos)

    # pasar cat a nº
    df4 = pd.get_dummies(df4, columns=["forma_farmaceutica_simplificada", "vias_administracion"], dtype=int)
    df4["Tratamiento de larga duración"] = df4["Tratamiento de larga duración"].map({"SI": 1, "NO": 0})
    df4 = pd.get_dummies(df4, columns=["Estado"], dtype=int)

    # separar dosis en nº y ud 
    df4["dosis_unidad"] = df4["dosis"].apply(sacar_unidad)
    df4["dosis"] = df4["dosis"].apply(sacar_numero)
    columna = df4.pop("dosis_unidad")
    df4.insert(df4.columns.get_loc("dosis") + 1, "dosis_unidad", columna)  # LA PONEMOS AL LADO DE DOSIS
    df4 = df4.dropna(subset=["dosis", "dosis_unidad"])

    # comprobar que no hay nulos (la foto puede faltar, no todos los medicamentos tienen)
    nulos = df4.drop(columns=["url_foto_materiales"]).isnull().sum().sum()
    if nulos > 0:
        raise ValueError(f"Después de la limpieza quedan {nulos} nulos")

    logger.info(f"Datos limpios: {df4.shape[0]} medicamentos y {df4.shape[1]} columnas")

        #la hu4 esta completa si no hay ningun fallo de scraping en la hu2
    hu4_completo = (con_fallo.sum() == 0)

    #guardar csv de la hu4
    ruta_csv = RUTA_DATA / f"medicamentos_epilepsia_HU4_limpio_{fecha}.csv"
    df4.to_csv(ruta_csv, index=False)
    logger.info(f"CSV HU4 guardado en: {ruta_csv}")

    return df4, hu4_completo

# PARA PROBAR SOLO ESTA HU CON EL ÚLTIMO EXCEL DE LA HU3 QUE HAYA EN data/
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ultimo_excel_hu3 = sorted(RUTA_DATA.glob("medicamentos_epilepsia_HU1_HU2_HU3_*.xlsx"))[-1]
    obtener_datos_hu4(pd.read_excel(ultimo_excel_hu3), "prueba")