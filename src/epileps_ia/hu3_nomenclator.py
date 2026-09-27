""" 
hu3: Se van a añadir a los datos de la hu2, datos económicos del csv Nomenclator

Hay que cruzar el xlsx generado en la hu2 con el fichero csv Nomenclator usando el Código Nacional (cn) y guardarlo en un nuevo xlsx.

"""
import pandas as pd 

#Ficheros 

excel_hu2 = "src/epileps_ia/medicamentos_epilepsia_HU1_HU2.xlsx"
csv_nomenclator = "src/epileps_ia/20260927_Nomenclator_de_Facturacion.csv"
excel_hu3 = "src/epileps_ia/medicamentos_epilepsia_HU3.xlsx"


#Leemos el excel de la hu2

df = pd.read_excel(excel_hu2, dtype={"cn" : str})
print ("medicamentos hu2" , len(df))

#Leemos el csv del nomenclator 
columnas = [
    "Código Nacional",
    "Estado",
    "Precio venta al público con IVA",
    "Precio de referencia",
    "Tratamiento de larga duración",
    "Especial control médico",
]

nomenclator = pd.read_csv(csv_nomenclator, usecols=columnas, dtype={"Código Nacional": str})
print("Filas nomenclator: ", len(nomenclator))

#Lo cruzamos por cn 
"""
merge une las dos tablas usando el cn del excel y el Código Nacional del csv.
how="left" mantiene todos los medicamentos de la HU-2, aunque su cn no esté
en el nomenclátor (en ese caso las columnas nuevas quedan vacías).
"""

df_hu3 = df.merge(nomenclator, how="left", left_on="cn", right_on="Código Nacional")

# el Código Nacional es igual que el cn, así que lo quitamos para no repetirlo
df_hu3 = df_hu3.drop(columns=["Código Nacional"])

encontrados = df["cn"].isin(nomenclator["Código Nacional"]).sum()
print("Con cn en el nomenclator: ", encontrados)
print("Sin coincidencia: ", len(df) - encontrados)


# GUARDA EL EXCEL
df_hu3.to_excel(excel_hu3, index=False)
print("EXCEL GUARDADO: ", excel_hu3)