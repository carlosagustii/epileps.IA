-- vemos el % de medicamentos con el mismo o menor precio
-- añadimos los valores a la tabla medicamentos_epilepsia_hu5 -> update
-- PARA LOS COMERCIALIZADOS
-- los no comercializados se ponene en NULL

-- cume_dist() = num filas precio menor o igual / numeor de filas totales grupo

use bd_epilepsia;

UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5 as t
JOIN (
    SELECT record_id,
           ROUND(CUME_DIST() OVER (PARTITION BY pactivos, dosis
                                      ORDER BY precio_venta_al_publico_con_iva), 2) AS kpi_pct_menor_igual_precio
    FROM medicamentos_epilepsia_hu5
    WHERE comercializado = 1
) s ON t.record_id = s.record_id
SET t.kpi_pct_distribucion_acumulada_precios_comercializados = s.kpi_pct_menor_igual_precio;