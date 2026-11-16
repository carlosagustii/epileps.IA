"""
Esta es la file principal de nuestro proyecto.
Es la que relaciona y une todas las files del proyecto

Se ejcutara usando el comando "uv run EpilepsIA_epilepsia.py" desde el directorio del archivo
"""

import logging
from pathlib import Path
from datetime import datetime

from epileps_ia import cima_api

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
        print("inicio\n")
        cima_api.obtener_medicamentos_epilepsia()


        print("\nFin")
        logger.info("Proceso finalizado correctamente")

        # TODO ir añadiedno el resto de llamadas al codigo HU2-HU7

    except Exception:
        # REGISTRA EL ERROR Y SU TRACEBACK
        logger.exception("Se ha producido un error durante la ejecución")
        raise
    


if __name__ == "__main__":
    main()
