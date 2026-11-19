Contiene los archivos csv/xlsx usados/generados en el proyecto

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

Cada fase se registra también en el log de ejecución.

### HU3
Se desgarga automaticamente el archivo csv de https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=buscarProductos&especialidad=%25%25%25&d-4015021-e=1&6578706f7274=1

Este archivo se descarga con el nombre de Nomenclator_(fecha + hora).csv

Antes de guardar el archivo con el nombre mencionado anteriormente, se confirma que el csv descargado contiene las columnas que necesitamos para luego poder acceder a ellas

Las columnas:
    "Código Nacional",
    "Estado",
    "Precio venta al público con IVA",
    "Precio de referencia",
    "Tratamiento de larga duración",
    "Especial control médico"

Se recibe el dataframe del HU2. 

Se tratan de unir los datos del HU2 con los nuevos datos del csv Nomenclator mediante el codigo nacional (cn)

En caso de que un medicamento no tuviera su correspondiente, el medicamento se sigue guardando en el excel del hu3 (medicamentos_epilepsia_HU1_HU2_HU3_fecha.xlsx), con los nuevos campos vacios.

Se considera completo cuando todos los medicamentos encuentran coincidencia.

Al igual que en los otros HU, cada fase registra también su actividad, incidencias y resultado en el log de ejecución.

### HU4
Se recibe el dataframe del HU3.

Sobre este dataframe se realiza todo el EDA. 

- Se eliminan columnas:
    "nregistro", 
    "cn", 
    "estado_rev", 
    "estado_aut", 
    "url_html_ficha_tecnica", 
    "url_foto_materiales", 
    "requiere_receta", 
    "medicamento_huerfano", 
    "biosimilar", 
    "num_registros_atc", 
    "num_excipientes", 
    "Especial control médico"

- Se hacen transformaciones, como pasar de categorico a numerico:
    "forma_farmaceutica_simplificada", 
    "vias_administracion", 
    "Tratamiento de larga duración", 
    "Estado"

- Se eliminan los medicamentos sin precio de venta al público
- Se eliminan los medicamentos en los que ha fallado el scraping de HU2 (alguna de las tres variables tiene valor -1)
- Se eliminan duplicados
- Se separa la dosis en valor numérico y unidad.
- Se eliminan los registros cuya dosis o unidad no se puede interpretar

El nuevo dataframe se guarda en un nuevo csv (medicamentos_epilepsia_HU4_limpio_fecha.csv)

Al igual que en los otros HU, cada fase registra también su actividad, incidencias y resultado en el log de ejecución.

### HU5
Se recibe el dataframe del HU4, sobre el que se calculan los clusters

Para el modelo se usan las columnas:
- "Precio venta al público con IVA"
- "Volumen Informativo de Seguridad (num palabras)"
- "Indicador de Riesgo Severo (num veces grave/s)"
- "Complejidad del Desglose Clínico (num tablas)"

El archivo csv se sobreescribe con cada ejecucion: medicamentos_epilepsia_HU5_clusters.csv

Se genera un archivo con los clusters -> data/graficos/ -> hu5_clusters_pca.png (tambien se sobreescribe)