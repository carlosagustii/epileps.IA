-- ahorro potencial.
-- Vemos el ahorro entre el medicamento mas caro y barato con el mismo principio activo y dosis PARA AQUELLOS COMERCIALIZADOS
-- Añadimos los valores a las nuevas columnas: kpi_ahorro_potencial_comercializados_eur y kpi_ahorro_potencial_comercializados_pct
-- si comercializado = 0 lo añade en las columnas como nulo

UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5 AS t
JOIN (
    SELECT
        record_id,
        precio_venta_al_publico_con_iva
        - MIN(precio_venta_al_publico_con_iva)
          OVER (PARTITION BY pactivos, dosis) AS ahorro
    FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5
    WHERE comercializado = 1
) AS s
ON t.record_id = s.record_id

SET
    t.kpi_ahorro_potencial_comercializados_eur = ROUND(s.ahorro, 2),
    t.kpi_ahorro_potencial_comercializados_pct = ROUND(
        s.ahorro * 100 / NULLIF(t.precio_venta_al_publico_con_iva, 0),
        1
    );