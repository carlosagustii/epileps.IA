use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpis_medicamentos_completo AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    comercializado,
    precio_venta_al_publico_con_iva,

    kpi_densidad_ficha_tecnica,

    kpi_ahorro_potencial_eur,
    kpi_ahorro_potencial_pct,

    kpi_ahorro_potencial_comercializados_eur,
    kpi_ahorro_potencial_comercializados_pct,

    kpi_pct_distribucion_acumulada_precios,
    kpi_pct_distribucion_acumulada_precios_comercializados

FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;