SELECT nombre, 
        volumen_informativo_de_seguridad_num_palabras AS palabras_seccion_44,
        complejidad_del_desglose_clinico_num_tablas AS num_tablas_documento,
        ROUND(
            volumen_informativo_de_seguridad_num_palabras
            / NULLIF(complejidad_del_desglose_clinico_num_tablas, 0), 2) AS densidad_ficha_tecnica
    FROM medicamentos_epilepsia_hu5
    ORDER BY densidad_ficha_tecnica DESC