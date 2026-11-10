-- creamos las nuevas columnas
-- vemos el % de medicamentos con el mismo o menor precio.
-- PARA LOS COMERCIALIZADOS

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_pct_distribucion_acumulada_precios_comercializados DOUBLE NULL;