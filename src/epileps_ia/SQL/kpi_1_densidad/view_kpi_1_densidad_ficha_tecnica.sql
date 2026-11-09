use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_1_densidad_ficha_tecnica AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    volumen_informativo_de_seguridad_num_palabras,
    complejidad_del_desglose_clinico_num_tablas,
    kpi_densidad_ficha_tecnica
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;