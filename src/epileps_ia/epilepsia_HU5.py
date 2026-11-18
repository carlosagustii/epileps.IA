"""
HU5 - Clustering de medicamentos con K-Means

Es la versión automatizada del notebook hu5.ipynb, basicamente hemos transformado cada celda y paso en una funcion.
Recibe el DataFrame limpio de la HU4, le añade las columnas "cluster" y "perfil",
guarda el CSV en data/ y devuelve el DataFrame.

La justificación del modelo (variables elegidas, elección de k...) está en hu5.ipynb
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # PARA GUARDAR LOS GRAFICOS EN UN ARCHIVO SIN ABRIR NINGUNA VENTANA
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


# CONFIGURACIÓN
logger = logging.getLogger(__name__)

RUTA_DATA = Path(__file__).resolve().parents[2] / "data"  # epileps_ia -> src -> epileps.IA
RUTA_CSV_HU5 = RUTA_DATA / "medicamentos_epilepsia_HU5_clusters.csv"
RUTA_GRAFICO_PCA = RUTA_DATA / "graficos" / "hu5_clusters_pca.png"

# COLUMNAS QUE USA EL MODELO
PRECIO = "Precio venta al público con IVA"
PALABRAS = "Volumen Informativo de Seguridad (num palabras)"
GRAVE = "Indicador de Riesgo Severo (num veces grave/s)"
TABLAS = "Complejidad del Desglose Clínico (num tablas)"
COLUMNAS_MODELO = [PRECIO, PALABRAS, GRAVE, TABLAS]

K = 5  # NUMERO DE CLUSTERES, ELEGIDO EN EL NOTEBOOK CON EL CODO Y LA SILUETA
RANDOM_SEED = 42
# UMBRALES PARA PONER NOMBRE A LOS CLUSTERES (DECIDIDOS EN EL NOTEBOOK)
PRECIO_BAJO_HASTA = 15       # PRECIO MEDIANO DEL CLUSTER, EN EUROS
PRECIO_ALTO_DESDE = 50
MUCHOS_AVISOS_DESDE = 8.5    # MEDIA DE VECES QUE APARECE "GRAVE" EN EL CLUSTER

# AVISOS DE CALIDAD DEL MODELO
SILUETA_MINIMA = 0.25
PCT_MINIMO_CLUSTER = 0.05


def validar_datos(df):
    """
    Comprueba que el DataFrame sirve para entrenar el modelo.
    Si no sirve lanza un ValueError para que el proceso se pare
    """

    faltan = [col for col in COLUMNAS_MODELO if col not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas para el modelo: {faltan}")

    nulos = int(df[COLUMNAS_MODELO].isna().sum().sum())
    if nulos > 0:
        raise ValueError(f"Hay {nulos} valores nulos en las columnas del modelo")

    # EN LA HU2 SE PONE -1 CUANDO FALLA EL SCRAPING DE UNA FICHA TECNICA
    # ESAS FILAS SE TIENEN QUE HABER QUITADO ANTES DE LLEGAR AQUI
    negativos = int((df[COLUMNAS_MODELO] < 0).sum().sum())
    if negativos > 0:
        raise ValueError(f"Hay {negativos} valores negativos en las columnas del modelo")

    if len(df) < K * 10:
        raise ValueError(f"Solo hay {len(df)} medicamentos, son muy pocos para {K} clústeres")


def preparar_variables(df):
    """
    Crea la tabla X del modelo (4 variables) y la escala
    """

    X = pd.DataFrame({
        "log_precio": np.log1p(df[PRECIO]),
        "log_palabras": np.log1p(df[PALABRAS]),
        "num_grave": df[GRAVE],
        "num_tablas": df[TABLAS],
    })

    return StandardScaler().fit_transform(X)


def nombrar_clusters(df):
    """
    Genera el nombre de cada clúster con reglas, a partir de su precio y de sus avisos graves.
    Así los nombres no se descuadran cuando cambian los datos
    """

    resumen = df.groupby("cluster").agg(
        precio_mediano=(PRECIO, "median"),
        grave_media=(GRAVE, "mean"),
    )

    nombres = {}
    for cluster, fila in resumen.iterrows():
        if fila["precio_mediano"] < PRECIO_BAJO_HASTA:
            precio = "Precio bajo"
        elif fila["precio_mediano"] >= PRECIO_ALTO_DESDE:
            precio = "Precio alto"
        else:
            precio = "Precio medio"

        if fila["grave_media"] >= MUCHOS_AVISOS_DESDE:
            avisos = "muchos avisos graves"
        else:
            avisos = "pocos avisos graves"

        nombres[cluster] = f"{precio}, {avisos}"

    # SI DOS CLUSTERES TIENEN EL MISMO NOMBRE LES AÑADIMOS SU NUMERO PARA DISTINGUIRLOS
    repetidos = [n for n in set(nombres.values()) if list(nombres.values()).count(n) > 1]
    if repetidos:
        logger.warning(f"Hay clústeres con el mismo nombre: {repetidos}. Se les añade el número de clúster")
        nombres = {c: (f"{n} (grupo {c})" if n in repetidos else n) for c, n in nombres.items()}

    return nombres


def guardar_grafico_pca(X_escalado, df):
    """
    Guarda en un PNG los medicamentos en 2D (PCA) coloreados por clúster
    """

    pca = PCA(n_components=2, random_state=RANDOM_SEED)
    X_2d = pca.fit_transform(X_escalado)

    fig, ax = plt.subplots(figsize=(9, 6))
    for cluster, nombre in df.groupby("cluster")["perfil"].first().items():
        mask = (df["cluster"] == cluster).values
        ax.scatter(X_2d[mask, 0], X_2d[mask, 1], s=40, alpha=0.7,
                   label=f"{cluster}: {nombre} ({mask.sum()})")
    ax.set_title("Medicamentos agrupados por K-Means (proyección PCA en 2D)")
    ax.set_xlabel(f"Componente 1 ({pca.explained_variance_ratio_[0]:.0%} de la variación)")
    ax.set_ylabel(f"Componente 2 ({pca.explained_variance_ratio_[1]:.0%} de la variación)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), frameon=False)
    fig.tight_layout()

    RUTA_GRAFICO_PCA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(RUTA_GRAFICO_PCA, dpi=150)
    plt.close(fig)  # CERRAMOS LA FIGURA PARA LIBERAR MEMORIA

    logger.info(f"Gráfico PCA guardado en: {RUTA_GRAFICO_PCA}")


def guardar_csv_hu5(df):
    """
    Guarda el CSV de la HU5.
    Primero se guarda en un archivo temporal y si va bien se sustituye el definitivo,
    así si falla el guardado no se pierde el CSV anterior
    """

    RUTA_CSV_HU5.parent.mkdir(parents=True, exist_ok=True)
    RUTA_TEMPORAL = RUTA_CSV_HU5.with_name(RUTA_CSV_HU5.stem + "_temporal.csv")

    try:
        df.to_csv(RUTA_TEMPORAL, index=False)
        RUTA_TEMPORAL.replace(RUTA_CSV_HU5)
        logger.info(f"CSV HU5 guardado correctamente en: {RUTA_CSV_HU5}")

    except Exception:
        RUTA_TEMPORAL.unlink(missing_ok=True)
        raise


# FUNCIÓN PRINCIPAL
def obtener_clusters(df):
    """
    Recibe el DataFrame limpio de la HU4.
    Entrena K-Means y devuelve el DataFrame con las columnas "cluster" y "perfil"
    """

    logger.info(f"Iniciando el clustering de {len(df)} medicamentos")

    validar_datos(df)
    df5 = df.copy()  # NO MODIFICAMOS EL DATAFRAME QUE NOS LLEGA

    # ENTRENAMOS EL MODELO
    X_escalado = preparar_variables(df5)
    kmeans = KMeans(n_clusters=K, random_state=RANDOM_SEED, n_init=10)
    df5["cluster"] = kmeans.fit_predict(X_escalado)

    # RENUMERAMOS POR PRECIO MEDIANO: 0 = EL MAS BARATO
    orden = df5.groupby("cluster")[PRECIO].median().sort_values().index
    df5["cluster"] = df5["cluster"].map({viejo: nuevo for nuevo, viejo in enumerate(orden)})

    # PONEMOS NOMBRE A LOS CLUSTERES
    df5["perfil"] = df5["cluster"].map(nombrar_clusters(df5))

    # INFORMAMOS DEL RESULTADO
    silueta = silhouette_score(X_escalado, df5["cluster"])
    logger.info(f"Silueta del modelo con k={K}: {silueta:.3f}")
    if silueta < SILUETA_MINIMA:
        logger.warning(f"La silueta es menor que {SILUETA_MINIMA}: los clústeres están poco separados")

    for (cluster, perfil), n in df5.groupby(["cluster", "perfil"]).size().items():
        logger.info(f"Clúster {cluster} - {perfil}: {n} medicamentos")
        if n < len(df5) * PCT_MINIMO_CLUSTER:
            logger.warning(f"El clúster {cluster} tiene menos del {PCT_MINIMO_CLUSTER:.0%} de los medicamentos")

    guardar_grafico_pca(X_escalado, df5)
    guardar_csv_hu5(df5)

    return df5


# PARA PROBAR SOLO ESTA HU, SIN EJECUTAR TODO EL PROYECTO
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    df_hu4 = pd.read_csv(Path(__file__).resolve().parent / "medicamentos_epilepsia_HU4_limpio.csv")
    obtener_clusters(df_hu4)