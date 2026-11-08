-- vemos el % de medicamentos con el mismo o menor precio. Es lo que haremos en las tablas
-- El segundo calcula los percentiles en funcion del precio. 0 barato y 1 el mas caro. Sin embargo como hay poca variabilidad no es muy util verlo de esta manera

SELECT nombre, pactivos, dosis, precio_venta_al_publico_con_iva,
       ROUND(CUME_DIST() OVER (PARTITION BY pactivos, dosis
                                  ORDER BY precio_venta_al_publico_con_iva), 2) AS kpi_pct_menor_igual_precio
FROM medicamentos_epilepsia_hu5;

SELECT nombre, pactivos, dosis, precio_venta_al_publico_con_iva,
       ROUND(PERCENT_RANK() OVER (PARTITION BY pactivos, dosis
                                  ORDER BY precio_venta_al_publico_con_iva), 2) AS kpi_percentil_precio
FROM medicamentos_epilepsia_hu5;