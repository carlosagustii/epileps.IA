-- vemos el % de medicamentos con el mismo o menor precio
use bd_epilepsia;

SELECT nombre, kpi_pct_distribucion_acumulada_precios 
FROM medicamentos_epilepsia_hu5;