-- intensidad de riesgo
-- veces que aparece "grave" por cada 1000 palabras de la seccion 4.4
-- si la seccion no tiene palabras se pone NULL

use bd_epilepsia;

UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5
SET kpi_intensidad_riesgo = ROUND(
    indicador_de_riesgo_severo_num_veces_grave_s * 1000
    / NULLIF(volumen_informativo_de_seguridad_num_palabras, 0),
2);