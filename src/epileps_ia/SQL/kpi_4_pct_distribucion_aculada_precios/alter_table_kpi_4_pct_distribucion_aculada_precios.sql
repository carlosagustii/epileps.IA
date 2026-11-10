-- creamos las nuevas columnas
-- vemos el % de medicamentos con el mismo o menor precio.

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_pct_distribucion_acumulada_precios DOUBLE NULL