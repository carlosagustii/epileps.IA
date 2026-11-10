-- ahorro potencial.
-- Vemos el ahorro entre el medicamento mas caro y barato con el mismo principio activo y dosis PARA AQUELLOS COMERCIALIZADOS
-- añadimos las nuevas columnas

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_ahorro_potencial_comercializados_eur DOUBLE NULL,
    ADD COLUMN kpi_ahorro_potencial_comercializados_pct DOUBLE NULL;
