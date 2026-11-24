-- laboratorios por principio activo
-- la subconsulta s cuenta los laboratorios distintos de cada principio activo
-- con el JOIN se pone ese numero en cada medicamento de ese principio activo

use bd_epilepsia;

UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5 t
JOIN (
    SELECT pactivos, COUNT(DISTINCT labtitular) AS num_laboratorios
    FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5
    GROUP BY pactivos
) s ON t.pactivos = s.pactivos
SET t.kpi_num_laboratorios_pactivo = s.num_laboratorios;