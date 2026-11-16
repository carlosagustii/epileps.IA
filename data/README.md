Contiene los archivos csv/xlsx usados en el proyecto

Todos tienen la base "medicamentos_epilepsia"

Al final del nombre se les añade la fase del proyecto asi como la fecha + hora (AAAA-MM-DD_HH-MM-SS). Esta fecha corresponde con la fecha del log (sin la hora)

Esta marca temporal permite identificar los archivos generados en cada ejecución y conservar un histórico de resultados.

### HU1
El HU1 obtiene la información de los medicamentos para la epilepsia a través de la API de CIMA.
- Si el HU1 obtiene toda la informacion de los medicamentos entonces se guarda con el nombre de "medicamentos_epilepsia_HU1_fecha.xlsx". 
- En caso contrario se guarda con el nombre de "medicamentos_epilepsia_HU1_fecha_Parcial.xlsx"

Los medicamentos cuya consulta falla no se incluyen en el DataFrame resultante.

### HU2
El HU2 recibe los datos directamente del dataframe de HU1, por lo que los puede recibir completos o parciales. En ambos casos los datos se tratan de la misma manera.

Se añaden tres variables relacionadas con las fichas técnicas:
- Volumen informativo de seguridad (número de palabras de la sección 4.4)
- Complejidad del desglose clínico (número de tablas)
- Indicador de riesgo severo (número de veces que aparece «grave» o «graves»)


Si no se puede procesar una ficha técnica, las tres variables reciben el valor -1.

Si se consigue procesar la ficha, pero no se encuentra la sección 4.4, únicamente la variable correspondiente al número de palabras de esa sección recibe el valor -1. Las otras dos variables se calculan normalmente.

El HU2 conserva todos los medicamentos recibidos de HU1 y guarda un único archivo con el nombre medicamentos_epilepsia_HU1_HU2_fecha.xlsx, independientemente de si se han producido incidencias.

La completitud de cada fase se registra también en el log de ejecución.