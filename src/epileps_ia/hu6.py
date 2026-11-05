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
SOURCE_FORMAT = "csv"   # "excel" o "csv"
SOURCE_PATH = Path(__file__).resolve().parent / "medicamentos_epilepsia_HU5_clusters.csv"

if SOURCE_FORMAT == "excel":
    df = pd.read_excel(SOURCE_PATH)
else:
    df = pd.read_csv(SOURCE_PATH, keep_default_na=False)


# Nombres de columna válidos para MySQL (sin espacios/tildes, máx. 64 caracteres)
def to_sql_name(name):
    name = name.strip().lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")[:64]

df.columns = [to_sql_name(c) for c in df.columns]

TABLE_NAME = "medicamentos_epilepsia_hu5"

columns_sql = ",\n ".join(f"`{c}` {to_mysql_type(df[c])}" for c in df.columns)
create_sql = f"""
CREATE TABLE IF NOT EXISTS
 {TABLE_NAME} (
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
    tuple(cell for cell in row)
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

# Una transacción: se guardan todas las filas o ninguna
conn = None
cursor = None
try:
    conn = mysql.connector.connect(password=password, **config)
    cursor = conn.cursor()
    cursor.execute(create_sql)
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
