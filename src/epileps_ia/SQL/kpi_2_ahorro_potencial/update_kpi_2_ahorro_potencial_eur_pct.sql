-- ahorro potencial.
-- Vemos el ahorro entre el medicamento mas caro y barato con el mismo principio activo y dosis
-- añadimos los valores a la tabla medicamentos_epilepsia_hu5 -> update

/*
Se esta selecionando: record_id, precio_venta_al_publico_con_iva
MIN(): calcula el precio mínimo.
OVER: indica que estamos utilizando una función de ventana.
PARTITION BY pactivos, dosis: divide los medicamentos en grupos según sus principios activos y dosis.
Con el JOIN se une la tabla original (t) con la subconsulta (s) utilizando record_id.
Conseguimos asi relacionar cada medicamento con el ahorro que acabamos de calcular.
kpi_ahorro_potencial_eur guarda en la tabla t lo obtenido en s.ahorro con 2 decimales
kpi_ahorro_potencial_pct se hace algo parecido pero calculamos el %. si se dividde entre 0 se pone null. se redondea a 1 decimal
*/

use bd_epilepsia;

UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5 t
JOIN (
    SELECT record_id,
           precio_venta_al_publico_con_iva
             - MIN(precio_venta_al_publico_con_iva) OVER (PARTITION BY pactivos, dosis) AS ahorro
    FROM BD_EPILEPSIA.medicamentos_epilepsia_hu5
) s ON t.record_id = s.record_id
SET t.kpi_ahorro_potencial_eur = ROUND(s.ahorro, 2),
    t.kpi_ahorro_potencial_pct = ROUND(s.ahorro * 100 / NULLIF(t.precio_venta_al_publico_con_iva, 0), 1);