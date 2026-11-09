# Sobre la carpeta SQL/

En esta carpeta estan todas las files .sql para trabajar en MySQL los distintos kpi que hemos creado

Cada una de las carpetas contiene un kpi distinto con:

1. Un `alter table` de mi tabla de medicamentos
2. Un `select` de la nueva columan creada
3. Un `select` comprobacion de la condicion
4. El `update` añadiendo el contenido a la nueva columna

Ademas tambien se ha creado una view para cada kpi:
1. `view_kpi_...` es un `create or replace view` en el que se crea la nueva vista con ciertos datos y la nueva columna de la tabla medicamentos
2. `select_view_...` es el select de la view correspondiente, con ella se puede ver solo la view

Por otro lado se ha creado una unica vista con todos los kpi (`view_kpis_medicamentos_completo.sql`) con su correspondiente `select.sql` y un `select` para ver toda la tabla (`ver_toda_tabla_medicamentos.sql`)


## Sobre las views
Las `views` es un modo de ver los datos distinto a las tablas.

Se pueden ver haciendo un SELECT normal: `select * from base de datos.nombre de la view;`

En nuestro caso `SELECT * FROM bd_epilepsia.view_kpis_medicamentos_completo;`

1. Si se modifican los datos de la tabla, en este caso la de medicamentos:
    - los kpi de las columnas de la tabla de medicamentos **NO se modifican automaticamente** por lo que **habria que hacer el update** de la columna de la tabla
    - En cambio las views de esas solumnas **SI se modifican automaticamnete** (la informacion de recalcula con los nuevos datos de la tabla). **NO hay que volver** a ejecutar el `create o replace view`

2. Si se modifican los kpi de la tabla de medicamentos:
    - Views **reflejan automaticamente** ese cammbio
    -  **NO hay que volver** a ejecutar el `create o replace view`





