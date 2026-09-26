"""
PAra ejecutar usar: 
uv run python -m start_epileps_ia

"""


import pandas as pd
from epileps_ia.webScraping import *



#LEE EL EXCEL
# TODO cambiar nombre por el correcto
#df = pd.read_csv("Pruebas2.csv", sep=";") #PAra csv. El ; indica la separacion de cada componente de una fila
df = pd.read_excel("Pruebas2.xlsx") #para excel
print(df.columns)
urls = df["url"]

print("urls: ", urls)

len_section_column = []
num_tablas_column = []
veces_grave_s_column = []

ID_SECTION = "4.4"
ETIQUETA_BUSCAR = "table"

"""
Recorro cada una de las url sacadas del csv
Y actuo sobre ellas
"""
for url in urls:
    print("\nURL: ", url)
    soup = get_url(url)

    len_section = numPalabrasSeccion(soup, ID_SECTION) 
    print("\nLEN: ", len_section)
    len_section_column.append(len_section)

    num_tablas = numEtiquetaBuscar(soup, ETIQUETA_BUSCAR)
    print("NUM ETIQUETA: ", num_tablas)
    num_tablas_column.append(num_tablas)

    veces_grave_s = contarPalabraGrave(soup)
    print("GRAVE: ", veces_grave_s)
    veces_grave_s_column.append(veces_grave_s)

print("\nCOLUMNS:\n", len_section_column)
print(num_tablas_column)
print(veces_grave_s_column)

df["Volumen Informativo de Seguridad (num palabras)"] = len_section_column
df["Complejidad del Desglose Clínico (num tablas)"] = num_tablas_column
df["Indicador de Riesgo Severo (num veces grave/s)"] = veces_grave_s_column

#GUARDA EN EL EXCEL
# TODO cambiar nombre por el correcto
#df.to_csv("Pruebas2.csv", sep=";", index=False) #para csv.
df.to_excel("Pruebas2.xlsx", index=False) #para excel. El index=False indica que no quiero columna adicional indicando numeor fila
print("EXCEL GUARDADO")