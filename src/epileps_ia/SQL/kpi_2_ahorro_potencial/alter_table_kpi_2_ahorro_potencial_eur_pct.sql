-- ahorro potencial.
-- Vemos el ahorro entre el medicamento mas caro y barato con el mismo principio activo y dosis
-- creamos fila en la tabla medicamentos_epilepsia_hu5

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_ahorro_potencial_eur DOUBLE NULL,
    ADD COLUMN kpi_ahorro_potencial_pct DOUBLE NULL;
