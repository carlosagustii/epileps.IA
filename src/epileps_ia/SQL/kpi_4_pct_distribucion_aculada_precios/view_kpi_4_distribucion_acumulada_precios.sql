use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_4_distribucion_acumulada_precios AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    precio_venta_al_publico_con_iva,
    kpi_pct_distribucion_acumulada_precios
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;