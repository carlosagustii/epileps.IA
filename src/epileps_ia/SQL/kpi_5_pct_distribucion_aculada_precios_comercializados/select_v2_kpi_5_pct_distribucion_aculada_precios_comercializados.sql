-- vemos el % de medicamentos con el mismo o menor precio.
-- usamos la variable de la tabla y no la volvemos a calcular como hacemos en el otro select
-- PARA LOS COMERCIALIZADOS

use bd_epilepsia;

SELECT
    nombre,
    kpi_pct_distribucion_acumulada_precios_comercializados
FROM medicamentos_epilepsia_hu5
WHERE comercializado = 1;