-- ahorro potencial.
-- Vemos el ahorro entre el medicamento mas caro y barato con el mismo principio activo y dosis
-- vemos el nombre y los nuevos valores (kpi_ahorro_potencial_eur, kpi_ahorro_potencial_pct)
-- de la tabla medicamentos_epilepsia_hu5 -> update

use bd_epilepsia;

SELECT nombre, kpi_ahorro_potencial_eur, kpi_ahorro_potencial_pct
FROM medicamentos_epilepsia_hu5;