use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_5_distribucion_acumulada_comercializados AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    comercializado,
    precio_venta_al_publico_con_iva,
    kpi_pct_distribucion_acumulada_precios_comercializados
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;