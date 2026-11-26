use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_7_laboratorios_pactivo AS
SELECT
    record_id,
    nombre,
    pactivos,
    labtitular,
    kpi_num_laboratorios_pactivo
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;