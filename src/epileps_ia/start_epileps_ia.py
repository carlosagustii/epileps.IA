"""
PAra ejecutar usar: 
uv run python -m start_epileps_ia

"""


import pandas as pd
import shutil
import time

from epileps_ia.webScraping import *



#LEE EL EXCEL

#excel_original = "Pruebas2.xlsx"
#excel_copia = "Pruebas2_HU1_HU2.xlsx"

excel_original = "medicamentos_epilepsia.xlsx"
excel_copia = "medicamentos_epilepsia_HU1_HU2.xlsx"

shutil.copy2(excel_original, excel_copia)


#df = pd.read_csv("Pruebas2.csv", sep=";") #PAra csv. El ; indica la separacion de cada componente de una fila
df = pd.read_excel(excel_copia) #para excel

print(df.columns)
#urls = df["url"]
urls = df["url_html_ficha_tecnica"]

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
i=1
for url in urls:
    print("\n", i)
    print("URL: ", url)
    try:
        soup = get_url(url)
        print(f"    OK: {soup.status_code}")


        len_section = numPalabrasSeccion(soup, ID_SECTION) 
        print("\nLEN: ", len_section)
        len_section_column.append(len_section)

        num_tablas = numEtiquetaBuscar(soup, ETIQUETA_BUSCAR)
        print("NUM ETIQUETA: ", num_tablas)
        num_tablas_column.append(num_tablas)

        veces_grave_s = contarPalabraGrave(soup)
        print("GRAVE: ", veces_grave_s)
        veces_grave_s_column.append(veces_grave_s)

    except requests.exceptions.Timeout:
        len_section_column.append(-1)
        num_tablas_column.append(-1)
        veces_grave_s_column.append(-1)

        print(f"    -> TIMEOUT: {url}")

    except requests.exceptions.RequestException as e:
        len_section_column.append(-1)
        num_tablas_column.append(-1)
        veces_grave_s_column.append(-1)
        print(f"    -> ERROR: {e}")

    i = i+1
    print("  -> Esperando 0.5 segundos...")

    time.sleep(0.5)

print("\nCOLUMNS:\n", len_section_column)
print(num_tablas_column)
print(veces_grave_s_column)

df["Volumen Informativo de Seguridad (num palabras)"] = len_section_column
df["Complejidad del Desglose Clínico (num tablas)"] = num_tablas_column
df["Indicador de Riesgo Severo (num veces grave/s)"] = veces_grave_s_column

#GUARDA EN EL EXCEL
#df.to_csv("Pruebas2.csv", sep=";", index=False) #para csv.
#df.to_excel("medicamentos_epilepsia.xlsx", index=False) #para excel. El index=False indica que no quiero columna adicional indicando numeor fila
df.to_excel(excel_copia, index=False) #para excel. El index=False indica que no quiero columna adicional indicando numeor fila


print("EXCEL GUARDADO")