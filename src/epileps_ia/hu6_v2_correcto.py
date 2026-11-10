"""
HU6 - Subir a MySQL el dataset de la HU5 (mismo estilo que load_Agusti_20261015.ipynb).
La tabla se crea automáticamente a partir de las columnas y tipos del fichero.
"""

import re
from getpass import getpass
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd

print(pd.__version__, np.__version__)
print(mysql.connector.__version__)

# Cargar el fichero de la HU5
SOURCE_FORMAT = "csv" # "excel" o "csv"
FILE_NAME = "medicamentos_epilepsia_HU5_clusters.csv"

# Funciona tanto en un script .py como en un notebook (donde __file__ no existe)
try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

SOURCE_PATH = BASE_DIR / FILE_NAME
print("Leyendo:", SOURCE_PATH)

if SOURCE_FORMAT == "excel":
    df = pd.read_excel(SOURCE_PATH)
else:
    df = pd.read_csv(SOURCE_PATH, keep_default_na=False)


# Nombres de columna válidos para MySQL (sin espacios/tildes, máx. 64 caracteres)
def to_sql_name(name):
    name = str(name).strip().lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")[:64]

df.columns = [to_sql_name(c) for c in df.columns]


# Tipo MySQL según el tipo de la columna en pandas
def to_mysql_type(serie):
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
    return f"VARCHAR({max(max_len, 1)})" if max_len <= 255 else "TEXT"


TABLE_NAME = "medicamentos_epilepsia_hu5"

columns_sql = ",\n ".join(f"`{c}` {to_mysql_type(df[c])}" for c in df.columns)

# Se borra la tabla antes de crearla para que, al volver a ejecutar,
# no se dupliquen las filas (si no, la comprobación del recuento fallaría).
drop_sql = f"DROP TABLE IF EXISTS {TABLE_NAME}"

create_sql = f"""
CREATE TABLE {TABLE_NAME} (
 record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
 {columns_sql}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""
print(create_sql)

insert_sql = f"""
INSERT INTO {TABLE_NAME}
 ({", ".join(f"`{c}`" for c in df.columns)})
VALUES ({", ".join(["%s"] * len(df.columns))})
"""


# Convertir valores de numpy a tipos de Python y NaN a NULL
def to_python(cell):
    if isinstance(cell, np.generic):
        cell = cell.item()
    if isinstance(cell, float) and np.isnan(cell):
        return None
    if isinstance(cell, pd.Timestamp):
        return cell.to_pydatetime()
    return cell

rows = [
    tuple(to_python(cell) for cell in row)
    for row in df.itertuples(index=False, name=None)
]
print(len(rows), "rows ready. First one:", rows[0])

# Conexión
DB_NAME = "BD_EPILEPSIA"

config = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "database": DB_NAME,
    "use_pure": True,
    "charset": "utf8mb4",
    "connection_timeout": 10,
    "autocommit": False,
}

password = getpass("MySQL password: ")

# Crear la base de datos si no existe
config_no_db = {k: v for k, v in config.items() if k != "database"}
conn = mysql.connector.connect(password=password, **config_no_db)
cursor = conn.cursor()
cursor.execute(
    f"CREATE DATABASE IF NOT EXISTS {DB_NAME} "
    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)
cursor.close()
conn.close()
print("Base de datos lista:", DB_NAME)

# Crear la tabla (en MySQL, DROP/CREATE TABLE no se pueden deshacer con rollback)
conn = mysql.connector.connect(password=password, **config)
cursor = conn.cursor()
cursor.execute(drop_sql)
cursor.execute(create_sql)
cursor.close()
conn.close()
print("Tabla creada:", TABLE_NAME)

# Una transacción para los datos: se guardan todas las filas o ninguna
conn = None
cursor = None
try:
    conn = mysql.connector.connect(password=password, **config)
    cursor = conn.cursor()
    cursor.executemany(insert_sql, rows)

    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    n_table = cursor.fetchone()[0]
    if n_table != len(df):
        raise ValueError(
            f"Count mismatch: table has {n_table}, df has {len(df)}"
        )

    conn.commit()
    print("Committed", n_table, "rows")
except Exception:
    if conn is not None and conn.is_connected():
        conn.rollback()
        print("Rolled back")
    raise
finally:
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()

# Comprobación
conn = mysql.connector.connect(password=password, **config)
cursor = conn.cursor()

cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
print("Rows in table:", cursor.fetchone()[0])

cursor.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 5")
for r in cursor.fetchall():
    print(r)

cursor.close()
conn.close()
