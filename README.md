# epileps.IA
Sistema inteligente que automatiza la recolección, ordenación y análisis de datos de medicamentos en base a enfermedades.


## Información general
En este proyecto se ha reunido la informacion de los medicamnetos de la epilepsia presentes en https://cima.aemps.es/ o en https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=buscarProductos en un solo archivo csv y mas tarde un una base de datos

Este proceso se ha realizado en multiples fases.

## Informacion tecnica
Las multiples fases han sido llamadas "historias de usuario", HU para abreviar.

Los archivos ejecutables se encuentran en `src/epileps_ia/`

Para no estar cargando repetidamente diferentes archivos xlsx o csv, entre fase y fase lo que se ha ido pasando ha sido el dataframe resultante de la fase anterior.

Al final del nombre de los archivos generados se les añade la fase del proyecto asi como la fecha + hora (AAAA-MM-DD_HH-MM-SS). Esta fecha corresponde con la fecha del log (sin la hora)

Esta marca temporal permite identificar los archivos generados en cada ejecución y conservar un histórico de resultados.

Para mas infromacion sobre el guardado de los datos acceder a `epileps.IA/data/README.md`

Cada una de las ejecuciones se registra con los logs: `epileps.IA/logs`. Para mas informacion consultar su README.md (`epileps.IA/logs/README.md`)

### Archivo principal
El archivo `EpilepsIA_epilepsia.py`

Este archivo es el que controla todo el flujo del proyecto.

### HU-1
Se accedió mediante el uso de APis a la pagina web de cima (https://cima.aemps.es/), para acceder a la informacion de todos los medicamentos relacionados con la epilepsia.

Los archivos de esta fase son: `cima.py`.

- Si el HU1 obtiene toda la informacion de los medicamentos entonces se guarda con el nombre de "medicamentos_epilepsia_HU1_fecha.xlsx".
- En caso contrario se guarda con el nombre de "medicamentos_epilepsia_HU1_fecha_Parcial.xlsx"

Los medicamentos cuya consulta falla no se incluyen en el DataFrame resultante.

### HU-2
Se realiza el Web Scraping, a partir de la url de cada ficha tecnica de cada medicamento (`url_html_ficha_tecnica`)

Se añaden tres variables relacionadas con las fichas técnicas:

- Volumen informativo de seguridad (número de palabras de la sección 4.4)
- Complejidad del desglose clínico (número de tablas)
- Indicador de riesgo severo (número de veces que aparece «grave» o «graves»)

Si no se puede procesar una ficha técnica, las tres variables reciben el valor -1.

### HU-3
Se accede a https://www.sanidad.gob.es/profesionales/nomenclator.do?metodo=buscarProductos para sacar la informacion de "Código Nacional", "Estado", "Precio venta al público con IVA", "Precio de referencia", "Tratamiento de larga duración", "Especial control médico" desde un csv que se descarga el programa, por cada uno de los medicamnetos de nuestro archivo.

En caso de que un medicamento no tuviera su correspondencia, el medicamento se sigue guardando en el excel del hu3 (medicamentos_epilepsia_HU1_HU2_HU3_fecha.xlsx), con los nuevos campos vacios.

### HU-4
En esta fase se realizo el EDA de nuestros datos.

Primero se hico sobre un archivo .ipynb (`EDA_HU_4.ipynb`) para poder tener mejor perspectiva visual de los datos.

Mas tarde se pasaron las transformaciones y tratamiento del dataframe a `epilepsIA_HU4` para que se pudiera ejecutar de manera independiente y automatica.

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

### HU-5
En esta parte se realizo un modelo (K-Means) para poder calcular posibles clusters

Al igual que en el HU-4 se creo primero un .ipynb (`hu5.ipynb`) en el que se justifica el modelo (variables elegidas, elección de k...)

En `epilepsia_HU5.py` se hace la automatizacion, para poder ejecutarlo desde nuestro archivo maestro `EpilepsIA_epilepsia.py`

Para el modelo se usan las columnas:
- "Precio venta al público con IVA"
- "Volumen Informativo de Seguridad (num palabras)"
- "Indicador de Riesgo Severo (num veces grave/s)"
- "Complejidad del Desglose Clínico (num tablas)"

El archivo csv se sobreescribe con cada ejecucion: medicamentos_epilepsia_HU5_clusters.csv

Se genera un archivo con los clusters -> data/graficos/ -> hu5_clusters_pca.png (tambien se sobreescribe)

### HU-6
Es el paso en el que nuestro csv final (el que hemos obtenido en el HU-5), se pasa a una base de datos. Para mas informacion de los archivos SQL consultar `src/epileps_ia/SQL/README.mds`

El nombre de la base de datos creada es `BD_EPILEPSIA`. En ella se crean dos tablas:
- `medicamentos_epilepsia_hu5`: Contiene la informacion de la ultima ejecucion.
- `medicamentos_epilepsia_historico`: contiene la informcacion de cada una de las ejecuciones realizadas mas los kpis. Si se realizan varias por dia solo se guarda la de la ultima ejecucion de ese dia.

Ademas tambien se realizan distintos kpis (ver carpeta SQL/) sobre la tabla `medicamentos_epilepsia_hu5`

## Configuracion del proyecto
### Entorno
En primer lugar hay que activar y sincronizar el entorno. Para ello desde la terminal (dentro de epileps.IA) escribir:
```git bash
uv sync
source .venv/Scripts/activate (si es linux o desde gitbash en windows)
```

### Variables de entorno
En el archivo `.env.example` se indica como hay que configurar las variables de entorno que son necesarias para poder conectarse con la base de datos de MySQL.

El unico realmente requerido es la contraseña. Los otros son varibales que estan definidas por defecto, pero que el usuario del programa puede cambiar en funcion de su configuracion.

```text
# Configuración de conexión a MySQL
MYSQL_PASSWORD=tu_contraseña
# varibales que tambien se pueden editar aunque por defecto son:
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
```

## Ejecucion del proyecto
Para ejecutar el proyecto, estando en el directorio del archivo principal (`src\epileps_ia\EpilepsIA_epilepsia.py`), escribe en la terminal: 
```git bash
uv run EpilepsIA_epilepsia.py
```

## Informacion adicional
Si se quiere dejar programado con el "Programdor de tareas Windows" o con "Crontab" atmbien se puede hacer. Solo hay que indicar que el archivo que se ejecute sea `EpilepsIA_apilepsia.py` y que el python con el que se ejecuta sea el del entorno del proyecto (`.venv/Scripts/python.exe`).

