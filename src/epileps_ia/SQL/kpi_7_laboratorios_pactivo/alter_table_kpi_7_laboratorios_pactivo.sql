-- laboratorios por principio activo
-- numero de laboratorios distintos que fabrican el principio activo de cada medicamento
-- creamos la columna en la tabla medicamentos_epilepsia_hu5

use bd_epilepsia;

ALTER TABLE BD_EPILEPSIA.medicamentos_epilepsia_hu5
    ADD COLUMN kpi_num_laboratorios_pactivo INT NULL;