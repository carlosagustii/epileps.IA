use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_3_ahorro_comercializados AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    comercializado,
    precio_venta_al_publico_con_iva,
    kpi_ahorro_potencial_comercializados_eur,
    kpi_ahorro_potencial_comercializados_pct
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;