use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_6_intensidad_riesgo AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    volumen_informativo_de_seguridad_num_palabras,
    indicador_de_riesgo_severo_num_veces_grave_s,
    kpi_intensidad_riesgo
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;