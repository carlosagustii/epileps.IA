"""
Esta es la file principal de nuestro proyecto.
Es la que relaciona y une todas las files del proyecto

Se ejcutara usando el comando "uv run EpilepsIA_epilepsia.py" desde el directorio del archivo
"""

import logging
from pathlib import Path
from datetime import datetime

from epileps_ia import cima_api
from epileps_ia import epilepsia_HU2

from epileps_ia import epilepsia_HU5
from epileps_ia import epilepsia_HU6

def configurar_logging():

    # CREAMOS LA CARPETA LOGS SI NO EXISTE
    RUTA_LOGS = (Path(__file__).resolve().parents[2] / "logs") # SUBO 2 CARPETAS: epileps_ia -> src -> epileps.IA
    RUTA_LOGS.mkdir(parents=True, exist_ok=True)

    # EN EL EJERCICIO DEL HU7 NOS PIDEN 
    # "todas las trazas, eventos, éxitos y errores en un
    # fichero de LOG dedicado (NombreEquipo_enfermedad_fecha.log)"
    # POR ESO USAMOS datatime
    fecha = datetime.now().strftime("%Y-%m-%d")
    nombre_log = f"EpilepsIA_epilepsia_{fecha}.log"

    # CONFIGURAMOS LOS LOGS
    logging.basicConfig(
        level=logging.INFO, # QUEREMOS CONFIGURAR INFO, WARNING, ERROR y CRITICAL
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", # SE ESTABLECE COMO SE VAN A MOSTRAR LOS LOGS
        # INDICA DONDE SE GUARDARAN LOS LOGS
        handlers=[
            logging.FileHandler(
                RUTA_LOGS / nombre_log,
                encoding="utf-8"
            ),
            logging.StreamHandler() # MUSTRA LOS MENSAJES TAMBIEN POR PANTALLA
        ]
    )

def main():

    configurar_logging()

    logger = logging.getLogger(__name__)

    logger.info("Iniciando el proyecto")

    try:
        #print("inicio\n")
        
        # HU1 CONSEGUIR LA INFO DE LOS MEDICAMNETOS DE EPILEPSIA DE CIMA
        logger.info("Trabajando en el HU1")
        df = cima_api.obtener_medicamentos_epilepsia()
        logger.info("HU1 finalizada correctamente")

        # HU2 OBTENER INFORMACIÓN DE LAS FICHAS TÉCNICAS
        logger.info("Iniciando HU2")
        df2 = epilepsia_HU2.obtener_datos_hu2(df)
        logger.info("HU2 finalizada correctamente")

        # HU5 CLUSTERING CON K-MEANS
        logger.info("Iniciando HU5")
        df5 = epilepsia_HU5.obtener_clusters(df4)
        logger.info("HU5 finalizada correctamente")

        # HU6 CARGA EN MYSQL, KPIs E HISTORICO
        logger.info("Iniciando HU6")
        epilepsia_HU6.cargar_en_mysql(df5)
        logger.info("HU6 finalizada correctamente")
        
        # print("\nFin")
        logger.info("Proceso finalizado correctamente")

        # TODO ir añadiedno el resto de llamadas al codigo HU2-HU7

    except Exception:
        # REGISTRA EL ERROR Y SU TRACEBACK
        logger.exception("Se ha producido un error durante la ejecución")
        raise
    


if __name__ == "__main__":
    main()
