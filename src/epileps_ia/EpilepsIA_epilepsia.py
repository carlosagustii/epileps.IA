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
from epileps_ia import hu3_nomenclator

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
    #fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fecha = datetime.now().strftime("%Y-%m-%d") # LOGS DIARIOS EN MISMO FICHERO
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

    # TODO una vez completo todos los HU hay que comprobar que el flujo funciona!!!

    configurar_logging()

    logger = logging.getLogger(__name__)

    logger.info("Iniciando el proyecto")

    # FECHA DE LA EJECUCIÓN (ANO/MES/DIA/HORA/MIN/SEG)
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    try:
        #print("inicio\n")
        
        # HU1 CONSEGUIR LA INFO DE LOS MEDICAMNETOS DE EPILEPSIA DE CIMA
        logger.info("Iniciando HU1")
        df, hu1_completo = cima_api.obtener_medicamentos_epilepsia(fecha)
        #logger.info("HU1 finalizada correctamente")
        if hu1_completo:
            logger.info("HU1 finalizada: extracción completa")
        else:
            logger.warning("HU1 finalizada: extracción parcial. Algunos de los medicamentos no se pudieron acceder")

        # HU2 OBTENER INFORMACIÓN DE LAS FICHAS TÉCNICAS
        logger.info("Iniciando HU2")
        df2, hu2_completo = epilepsia_HU2.obtener_datos_hu2(df, fecha)
        #logger.info("HU2 finalizada correctamente")
        if hu2_completo:
            logger.info("HU2 finalizada: procesamiento completo")
        else:
            logger.warning("HU2 finalizada: procesamiento parcial. Algunos datos no se pudieron conseguir")

        # HU3: OBTENER INFORMACIÓN ECONÓMICA DEL NOMENCLÁTOR
        logger.info("Iniciando HU3")
        df3, hu3_completo = hu3_nomenclator.obtener_datos_hu3(df2, fecha)
        if hu3_completo:
            logger.info("HU3 finalizada: procesamiento completo")
        else:
            logger.warning("HU3 finalizada: procesamiento parcial. Algunos medicamentos no tienen coincidencia en el Nomenclator")

        # TODO añadir lo correspondiente al HU4 siguiendo este formato

        # HU5 CLUSTERING CON K-MEANS
        logger.info("Iniciando HU5")
        df5 = epilepsia_HU5.obtener_clusters(df4)
        logger.info("HU5 finalizada correctamente")

        # HU6 CARGA EN MYSQL, KPIs E HISTORICO
        logger.info("Iniciando HU6")
        epilepsia_HU6.cargar_en_mysql(df5)
        logger.info("HU6 finalizada correctamente")

        # RESUMEN FINAL
        # TODO hacer y cambiar esto para el resto --> falta HU4

        logger.info("RESUMEN DEL PROCESO")
        logger.info(f"HU1 completa: {hu1_completo}")
        logger.info(f"HU2 completa: {hu2_completo}")
        logger.info(f"HU3 completa: {hu3_completo}")

        # TODO poner logger final del hu4 -> comprobar tbn que se puede hacer completo?

        logger.info("HU5 completa")
        logger.info("HU6 completa")

        if hu1_completo and hu2_completo and hu3_completo:
            logger.info("RESULTADO GLOBAL: DATOS COMPLETOS")
        else:
            logger.warning("RESULTADO GLOBAL: DATOS PARCIALES")
        
        # print("\nFin")
        logger.info("Proceso finalizado correctamente")

    except Exception:
        # REGISTRA EL ERROR Y SU TRACEBACK
        logger.exception("Se ha producido un error durante la ejecución")
        raise
    


if __name__ == "__main__":
    main()
