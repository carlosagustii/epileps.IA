use bd_epilepsia;

CREATE OR REPLACE VIEW BD_EPILEPSIA.view_kpi_2_ahorro_potencial AS
SELECT
    record_id,
    nombre,
    pactivos,
    dosis,
    precio_venta_al_publico_con_iva,
    kpi_ahorro_potencial_eur,
    kpi_ahorro_potencial_pct
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;