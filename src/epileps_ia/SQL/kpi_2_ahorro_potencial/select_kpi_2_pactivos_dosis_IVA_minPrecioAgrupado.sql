SELECT
    pactivos,
    dosis,
    precio_venta_al_publico_con_iva,
    MIN(precio_venta_al_publico_con_iva)
        OVER (PARTITION BY pactivos, dosis) AS precio_minimo
FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5;