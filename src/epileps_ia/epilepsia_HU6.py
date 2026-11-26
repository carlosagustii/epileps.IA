"""
HU6 - Carga en MySQL y cálculo de los KPIs

Es la versión automatizada de hu6_v2_correcto.py.
Recibe el DataFrame de la HU5, lo sube a MySQL y después ejecuta los .sql de la carpeta SQL/
para volver a crear las columnas de los KPIs y las views.
Al final guarda una copia de la carga en la tabla de histórico (una versión por día).

La contraseña de MySQL no se pide por pantalla: se lee del archivo .env (que no se sube a git)
"""

import logging
import os
import re
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd
from dotenv import load_dotenv


# CONFIGURACIÓN
logger = logging.getLogger(__name__)

RUTA_PROYECTO = Path(__file__).resolve().parents[2]  # epileps_ia -> src -> epileps.IA
RUTA_ENV = RUTA_PROYECTO / ".env"
RUTA_SQL = Path(__file__).resolve().parent / "SQL"

DB_NAME = "BD_EPILEPSIA"
TABLE_NAME = "medicamentos_epilepsia_hu5"              # ULTIMA EJECUCION, ES LA QUE LEE POWER BI
TABLA_HISTORICO = "medicamentos_epilepsia_historico"  # TODAS LAS VERSIONES, UNA POR DIA
VIEW_KPIS = "view_kpis_medicamentos_completo"

# FICHEROS .sql QUE SE EJECUTAN DESPUES DE LA CARGA, EN ESTE ORDEN
# PARA CADA KPI: 1) alter table  2) update  3) view
# AL AÑADIR UN KPI NUEVO HAY QUE AÑADIR AQUI SUS FICHEROS
FICHEROS_SQL = [
    "kpi_1_densidad/añadir columna.sql",
    "kpi_1_densidad/UPDATE densidad.sql",
    "kpi_1_densidad/view_kpi_1_densidad_ficha_tecnica.sql",

    "kpi_2_ahorro_potencial/alter_table_kpi_2_ahorro_potencial_eur_pct.sql",
    "kpi_2_ahorro_potencial/update_kpi_2_ahorro_potencial_eur_pct.sql",
    "kpi_2_ahorro_potencial/view_kpi_2_ahorro_potencial.sql",

    "kpi_3_ahorro_potencial_comercializados/alter_table_kpi_3_ahorro_potencial_comercializados_eur_pct.sql",
    "kpi_3_ahorro_potencial_comercializados/update_kpi_3_ahorro_potencial_comercializados_eur_pct.sql",
    "kpi_3_ahorro_potencial_comercializados/view_kpi_3_ahorro_comercializados.sql",

    "kpi_4_pct_distribucion_aculada_precios/alter_table_kpi_4_pct_distribucion_aculada_precios.sql",
    "kpi_4_pct_distribucion_aculada_precios/update_kpi_4_pct_distribucion_aculada_precios.sql",
    "kpi_4_pct_distribucion_aculada_precios/view_kpi_4_distribucion_acumulada_precios.sql",

    "kpi_5_pct_distribucion_aculada_precios_comercializados/alter_table_kpi_5_pct_distribucion_aculada_precios_comercializados.sql",
    "kpi_5_pct_distribucion_aculada_precios_comercializados/update_kpi_5_pct_distribucion_aculada_precios_comercializados.sql",
    "kpi_5_pct_distribucion_aculada_precios_comercializados/view_kpi_5_distribucion_acumulada_comercializados.sql",

    "kpi_6_intensidad_riesgo/alter_table_kpi_6_intensidad_riesgo.sql",
    "kpi_6_intensidad_riesgo/update_kpi_6_intensidad_riesgo.sql",
    "kpi_6_intensidad_riesgo/view_kpi_6_intensidad_riesgo.sql",

    "kpi_7_laboratorios_pactivo/alter_table_kpi_7_laboratorios_pactivo.sql",
    "kpi_7_laboratorios_pactivo/update_kpi_7_laboratorios_pactivo.sql",
    "kpi_7_laboratorios_pactivo/view_kpi_7_laboratorios_pactivo.sql",

    "view_kpis_medicamentos_completo.sql",
]


def obtener_config():
    """
    Lee del archivo .env los datos de conexión a MySQL.
    Solo es obligatoria la contraseña, el resto tienen valor por defecto
    """

    load_dotenv(RUTA_ENV)  # SI EL .env NO EXISTE NO DA ERROR, SE USAN LAS VARIABLES DEL SISTEMA

    password = os.environ.get("MYSQL_PASSWORD")
    if not password:
        raise ValueError(f"Falta la variable MYSQL_PASSWORD. Hay que definirla en el archivo {RUTA_ENV}")

    return {
        "host": os.environ.get("MYSQL_HOST", "localhost"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": password,
        "use_pure": True,
        "charset": "utf8mb4",
        "connection_timeout": 10,
        "autocommit": False,
    }


def to_sql_name(name):
    """
    Nombres de columna válidos para MySQL (sin espacios/tildes, máx. 64 caracteres)
    """

    name = str(name).strip().lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")[:64]


def to_mysql_type(serie):
    """
    Tipo MySQL según el tipo de la columna en pandas
    """

    if pd.api.types.is_bool_dtype(serie):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(serie):
        return "BIGINT"
    if pd.api.types.is_float_dtype(serie):
        return "DOUBLE"
    if pd.api.types.is_datetime64_any_dtype(serie):
        return "DATETIME"
    max_len = serie.astype(str).str.len().max() if len(serie) else 0
    max_len = int(max_len) if pd.notna(max_len) else 0
    # VARCHAR(255) FIJO: ASI EL HISTORICO NO FALLA SI OTRO DIA LLEGA UN TEXTO MAS LARGO
    return "VARCHAR(255)" if max_len <= 255 else "TEXT"


def to_python(cell):
    """
    Convierte los valores de numpy a tipos de Python y los NaN a NULL
    """

    if isinstance(cell, np.generic):
        cell = cell.item()
    if isinstance(cell, float) and np.isnan(cell):
        return None
    if isinstance(cell, pd.Timestamp):
        return cell.to_pydatetime()
    return cell


def leer_sentencias_sql(ruta):
    """
    Lee un fichero .sql y devuelve la lista de sentencias que contiene.
    Se quitan los comentarios y se separa por ;
    """

    texto = ruta.read_text(encoding="utf-8")
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.DOTALL)  # COMENTARIOS /* ... */
    texto = re.sub(r"--[^\n]*", "", texto)                    # COMENTARIOS -- ...

    return [sentencia.strip() for sentencia in texto.split(";") if sentencia.strip()]


def crear_base_de_datos(config):
    """
    Crea la base de datos si no existe
    """

    conn = mysql.connector.connect(**config)
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.close()
    finally:
        conn.close()

    logger.info(f"Base de datos lista: {DB_NAME}")


def cargar_tabla(conn, df):
    """
    Borra la tabla, la vuelve a crear con las columnas del DataFrame e inserta todas las filas.
    Se guardan todas las filas o ninguna
    """

    columns_sql = ",\n ".join(f"`{c}` {to_mysql_type(df[c])}" for c in df.columns)

    create_sql = f"""
    CREATE TABLE {TABLE_NAME} (
     record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
     {columns_sql}
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """

    insert_sql = f"""
    INSERT INTO {TABLE_NAME}
     ({", ".join(f"`{c}`" for c in df.columns)})
    VALUES ({", ".join(["%s"] * len(df.columns))})
    """

    rows = [
        tuple(to_python(cell) for cell in row)
        for row in df.itertuples(index=False, name=None)
    ]

    cursor = conn.cursor()
    try:
        # EN MySQL, DROP/CREATE TABLE NO SE PUEDEN DESHACER CON ROLLBACK
        # SE BORRA LA TABLA PARA QUE AL VOLVER A EJECUTAR NO SE DUPLIQUEN LAS FILAS
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        cursor.execute(create_sql)
        logger.info(f"Tabla creada: {TABLE_NAME} ({len(df.columns)} columnas)")

        cursor.executemany(insert_sql, rows)

        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        n_table = cursor.fetchone()[0]
        if n_table != len(df):
            raise ValueError(f"No coinciden las filas: la tabla tiene {n_table} y el DataFrame {len(df)}")

        conn.commit()
        logger.info(f"Filas insertadas en {TABLE_NAME}: {n_table}")

    except Exception:
        conn.rollback()
        logger.error("Ha fallado la carga de la tabla. Se ha hecho rollback de las filas")
        raise

    finally:
        cursor.close()


def ejecutar_kpis(conn):
    """
    Ejecuta los .sql de los KPIs en el orden de FICHEROS_SQL.
    Hace falta porque al borrar la tabla se pierden las columnas de los KPIs
    """

    # COMPROBAMOS ANTES DE EMPEZAR QUE ESTAN TODOS LOS FICHEROS
    faltan = [f for f in FICHEROS_SQL if not (RUTA_SQL / f).is_file()]
    if faltan:
        raise FileNotFoundError(f"No se encuentran estos ficheros .sql: {faltan}")

    cursor = conn.cursor()
    try:
        for fichero in FICHEROS_SQL:
            logger.info(f"Ejecutando SQL: {fichero}")

            try:
                for sentencia in leer_sentencias_sql(RUTA_SQL / fichero):
                    cursor.execute(sentencia)
                conn.commit()  # LOS UPDATE NO SE GUARDAN HASTA HACER COMMIT

            except Exception:
                conn.rollback()
                logger.error(f"Ha fallado el fichero SQL: {fichero}")
                raise

        # COMPROBAMOS QUE LA VIEW CON TODOS LOS KPIs TIENE TODAS LAS FILAS
        cursor.execute(f"SELECT COUNT(*) FROM {VIEW_KPIS}")
        n_view = cursor.fetchone()[0]

    finally:
        cursor.close()

    logger.info(f"KPIs calculados. Ficheros SQL ejecutados: {len(FICHEROS_SQL)}")
    return n_view


def obtener_columnas(cursor, tabla):
    """
    Devuelve un diccionario {nombre de columna: tipo} de una tabla de MySQL
    """

    cursor.execute(f"SHOW COLUMNS FROM {tabla}")

    columnas = {}
    for fila in cursor.fetchall():
        nombre, tipo = fila[0], fila[1]
        if isinstance(tipo, (bytes, bytearray)):  # A VECES EL CONECTOR DEVUELVE EL TIPO EN BYTES
            tipo = tipo.decode()
        columnas[nombre] = tipo

    return columnas


def guardar_historico(conn):
    """
    Copia la tabla de la última ejecución (con sus KPIs) a la tabla de histórico,
    añadiendo la columna fecha_ejecucion.
    Solo hay una versión por día: si ya había una de hoy, se sustituye
    """

    cursor = conn.cursor()
    try:
        # LA PRIMERA VEZ SE CREA EL HISTORICO VACIO, CON LAS MISMAS COLUMNAS QUE LA TABLA + LA FECHA
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {TABLA_HISTORICO} AS "
            f"SELECT CURDATE() AS fecha_ejecucion, t.* FROM {TABLE_NAME} t WHERE 1 = 0"
        )

        # SI LA TABLA TIENE COLUMNAS NUEVAS (POR EJEMPLO UN KPI NUEVO), SE AÑADEN AL HISTORICO
        columnas_tabla = obtener_columnas(cursor, TABLE_NAME)
        columnas_historico = obtener_columnas(cursor, TABLA_HISTORICO)

        for columna, tipo in columnas_tabla.items():
            if columna not in columnas_historico:
                cursor.execute(f"ALTER TABLE {TABLA_HISTORICO} ADD COLUMN `{columna}` {tipo} NULL")
                logger.warning(f"Columna nueva añadida al histórico: {columna}")

        # BORRAMOS LA VERSION DE HOY SI YA EXISTIA Y COPIAMOS LA NUEVA
        cursor.execute(f"DELETE FROM {TABLA_HISTORICO} WHERE fecha_ejecucion = CURDATE()")
        if cursor.rowcount > 0:
            logger.info(f"Ya había una versión de hoy en el histórico ({cursor.rowcount} filas). Se sustituye")

        lista_columnas = ", ".join(f"`{c}`" for c in columnas_tabla)
        cursor.execute(
            f"INSERT INTO {TABLA_HISTORICO} (fecha_ejecucion, {lista_columnas}) "
            f"SELECT CURDATE(), {lista_columnas} FROM {TABLE_NAME}"
        )
        n_copiadas = cursor.rowcount

        conn.commit()

        cursor.execute(f"SELECT COUNT(DISTINCT fecha_ejecucion) FROM {TABLA_HISTORICO}")
        n_versiones = cursor.fetchone()[0]

    except Exception:
        conn.rollback()
        logger.error("Ha fallado el guardado en el histórico. La tabla de la última ejecución sí está cargada")
        raise

    finally:
        cursor.close()

    logger.info(f"Histórico actualizado: {n_copiadas} filas copiadas. Versiones guardadas: {n_versiones}")
    return n_copiadas


# FUNCIÓN PRINCIPAL
def cargar_en_mysql(df):
    """
    Recibe el DataFrame de la HU5.
    Lo sube a MySQL, calcula los KPIs y guarda la versión en el histórico.
    Devuelve el número de filas cargadas
    """

    logger.info(f"Iniciando la carga en MySQL de {len(df)} medicamentos")

    if df.empty:
        raise ValueError("El DataFrame está vacío, no se carga nada en MySQL")

    df6 = df.copy()  # NO MODIFICAMOS EL DATAFRAME QUE NOS LLEGA
    df6.columns = [to_sql_name(c) for c in df6.columns]

    repetidas = df6.columns[df6.columns.duplicated()].tolist()
    if repetidas:
        raise ValueError(f"Hay nombres de columna repetidos al pasarlos a MySQL: {repetidas}")

    config = obtener_config()
    crear_base_de_datos(config)

    conn = mysql.connector.connect(database=DB_NAME, **config)
    try:
        cargar_tabla(conn, df6)
        n_view = ejecutar_kpis(conn)

        if n_view != len(df6):
            raise ValueError(f"La view {VIEW_KPIS} tiene {n_view} filas y el DataFrame {len(df6)}")

        n_historico = guardar_historico(conn)  # SOLO SE GUARDA LA VERSION SI TODO LO ANTERIOR HA IDO BIEN

        if n_historico != len(df6):
            raise ValueError(f"Al histórico se han copiado {n_historico} filas y el DataFrame tiene {len(df6)}")
    finally:
        conn.close()

    logger.info(f"HU6 finalizada: {n_view} medicamentos en MySQL con sus KPIs")
    return n_view


# PARA PROBAR SOLO ESTA HU, SIN EJECUTAR TODO EL PROYECTO
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # LEEMOS EL CSV QUE GENERA epilepsia_HU5.py
    RUTA_CSV_HU5 = RUTA_PROYECTO / "data" / "medicamentos_epilepsia_HU5_clusters.csv"
    cargar_en_mysql(pd.read_csv(RUTA_CSV_HU5))



#VERSION ANTIGUA DE HU6 ANTES DE AUTOMATIZACION DE HU7
# """
# HU6 - Subir a MySQL el dataset de la HU5 (mismo estilo que load_Agusti_20261015.ipynb).
# La tabla se crea automáticamente a partir de las columnas y tipos del fichero.
# """

# import re
# from getpass import getpass
# from pathlib import Path

# import mysql.connector
# import numpy as np
# import pandas as pd

# print(pd.__version__, np.__version__)
# print(mysql.connector.__version__)

# # Cargar el fichero de la HU5
# SOURCE_FORMAT = "csv" # "excel" o "csv"
# FILE_NAME = "medicamentos_epilepsia_HU5_clusters.csv"

# # Funciona tanto en un script .py como en un notebook (donde __file__ no existe)
# try:
#     BASE_DIR = Path(__file__).resolve().parent
# except NameError:
#     BASE_DIR = Path.cwd()

# SOURCE_PATH = BASE_DIR / FILE_NAME
# print("Leyendo:", SOURCE_PATH)

# if SOURCE_FORMAT == "excel":
#     df = pd.read_excel(SOURCE_PATH)
# else:
#     df = pd.read_csv(SOURCE_PATH, keep_default_na=False)


# # Nombres de columna válidos para MySQL (sin espacios/tildes, máx. 64 caracteres)
# def to_sql_name(name):
#     name = str(name).strip().lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
#     return re.sub(r"[^a-z0-9]+", "_", name).strip("_")[:64]

# df.columns = [to_sql_name(c) for c in df.columns]


# # Tipo MySQL según el tipo de la columna en pandas
# def to_mysql_type(serie):
#     if pd.api.types.is_bool_dtype(serie):
#         return "BOOLEAN"
#     if pd.api.types.is_integer_dtype(serie):
#         return "BIGINT"
#     if pd.api.types.is_float_dtype(serie):
#         return "DOUBLE"
#     if pd.api.types.is_datetime64_any_dtype(serie):
#         return "DATETIME"
#     max_len = serie.astype(str).str.len().max() if len(serie) else 0
#     max_len = int(max_len) if pd.notna(max_len) else 0
#     return f"VARCHAR({max(max_len, 1)})" if max_len <= 255 else "TEXT"


# TABLE_NAME = "medicamentos_epilepsia_hu5"

# columns_sql = ",\n ".join(f"`{c}` {to_mysql_type(df[c])}" for c in df.columns)

# # Se borra la tabla antes de crearla para que, al volver a ejecutar,
# # no se dupliquen las filas (si no, la comprobación del recuento fallaría).
# drop_sql = f"DROP TABLE IF EXISTS {TABLE_NAME}"

# create_sql = f"""
# CREATE TABLE {TABLE_NAME} (
#  record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
#  {columns_sql}
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
# """
# print(create_sql)

# insert_sql = f"""
# INSERT INTO {TABLE_NAME}
#  ({", ".join(f"`{c}`" for c in df.columns)})
# VALUES ({", ".join(["%s"] * len(df.columns))})
# """


# # Convertir valores de numpy a tipos de Python y NaN a NULL
# def to_python(cell):
#     if isinstance(cell, np.generic):
#         cell = cell.item()
#     if isinstance(cell, float) and np.isnan(cell):
#         return None
#     if isinstance(cell, pd.Timestamp):
#         return cell.to_pydatetime()
#     return cell

# rows = [
#     tuple(to_python(cell) for cell in row)
#     for row in df.itertuples(index=False, name=None)
# ]
# print(len(rows), "rows ready. First one:", rows[0])

# # Conexión
# DB_NAME = "BD_EPILEPSIA"

# config = {
#     "host": "localhost",
#     "port": 3306,
#     "user": "root",
#     "database": DB_NAME,
#     "use_pure": True,
#     "charset": "utf8mb4",
#     "connection_timeout": 10,
#     "autocommit": False,
# }

# password = getpass("MySQL password: ")

# # Crear la base de datos si no existe
# config_no_db = {k: v for k, v in config.items() if k != "database"}
# conn = mysql.connector.connect(password=password, **config_no_db)
# cursor = conn.cursor()
# cursor.execute(
#     f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
#     "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
# )
# cursor.close()
# conn.close()
# print("Base de datos lista:", DB_NAME)

# # Crear la tabla (en MySQL, DROP/CREATE TABLE no se pueden deshacer con rollback)
# conn = mysql.connector.connect(password=password, **config)
# cursor = conn.cursor()
# cursor.execute(drop_sql)
# cursor.execute(create_sql)
# cursor.close()
# conn.close()
# print("Tabla creada:", TABLE_NAME)

# # Una transacción para los datos: se guardan todas las filas o ninguna
# conn = None
# cursor = None
# try:
#     conn = mysql.connector.connect(password=password, **config)
#     cursor = conn.cursor()
#     cursor.executemany(insert_sql, rows)

#     cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
#     n_table = cursor.fetchone()[0]
#     if n_table != len(df):
#         raise ValueError(
#             f"Count mismatch: table has {n_table}, df has {len(df)}"
#         )

#     conn.commit()
#     print("Committed", n_table, "rows")
# except Exception:
#     if conn is not None and conn.is_connected():
#         conn.rollback()
#         print("Rolled back")
#     raise
# finally:
#     if cursor is not None:
#         cursor.close()
#     if conn is not None:
#         conn.close()

# # Comprobación
# conn = mysql.connector.connect(password=password, **config)
# cursor = conn.cursor()

# cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
# print("Rows in table:", cursor.fetchone()[0])

# cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 5")
# for r in cursor.fetchall():
#     print(r)

# cursor.close()
# conn.close()
