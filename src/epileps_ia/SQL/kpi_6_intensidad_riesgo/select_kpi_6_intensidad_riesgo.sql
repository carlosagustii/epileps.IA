use bd_epilepsia;

SELECT nombre, indicador_de_riesgo_severo_num_veces_grave_s,
       volumen_informativo_de_seguridad_num_palabras, kpi_intensidad_riesgo
FROM medicamentos_epilepsia_hu5
ORDER BY kpi_intensidad_riesgo DESC;