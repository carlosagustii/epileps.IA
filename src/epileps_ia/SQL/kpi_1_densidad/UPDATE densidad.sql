UPDATE BD_EPILEPSIA.medicamentos_epilepsia_hu5
SET kpi_densidad_ficha_tecnica = ROUND(
    volumen_informativo_de_seguridad_num_palabras
    / NULLIF(complejidad_del_desglose_clinico_num_tablas, 0),
2);
