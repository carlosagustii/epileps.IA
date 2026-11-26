-- intensidad de riesgo
-- veces que aparece "grave" por cada 1000 palabras de la seccion 4.4
-- creamos la columna en la tabla medicamentos_epilepsia_hu5

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_intensidad_riesgo DOUBLE NULL;