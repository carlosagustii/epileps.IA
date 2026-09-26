


import requests
import pandas as pd
import json
import re

from bs4 import BeautifulSoup #hice el uv add bs4 -> esto instalo bs4

"""
import sys
print(sys.executable)
"""


#TODO crear file para el csv

def get_url(url):
    response = requests.get(url) #accede a la pagina y la guarda
    """
    si se hace 
        response.status_code 
        print(response.status_code)
    es mejor hacerla en un bucle if que compruebe que ha dado lo esperado. 
    Continuar el codigo dentro te devuelve el codigo resultante de hacer la peticion. 
    Se espara que devuelva 200 ya que entonces se ha podido acceder 
    para no hacer el if se puede usar raise for status que lanzara exception si no se puede acceder.
    """
    response.raise_for_status()
    #print("Raise: ", response.raise_for_status())

    html = response.content

    soup = BeautifulSoup(html, "html.parser")
    #soup tiene ahora el texto del html
    #print(soup)
    return soup


"""
esta funcion cuenta el nuemro de palabras dentro de una secion.
Si es secion 4 cuenta hasta secion 5
si es secion 3.4 cuenta hasta llegar a la secion 3.5
"""
def numPalabrasSeccion(soup, id_section): 
    #print("h2: \n",  soup.find_all("h2"))# imprime todos los h2
    text4_4 = soup.find("h2", id=id_section) #como soloq uiero el 4.4 no necesittaria el find all
    #print(f"test 4.4: {text4_4} \ntest 4.4.text: ", text4_4.text) # sin el .text nos da las etiquetas tambien. el text da solo el texto
    title4_4 = text4_4.text #se podria poner en una sola linea:  title4_4 = soup.find("h2", id=4.4).text
    #print("\nTITLE: ", title4_4)

    texto_subseccion = "" #para tener todo el texto, es mejor en una sola string a tener varias string en un array
    """
    find_next_siblings busca etiquetas, que estan al mismo nivel de h2. 
    Esto es importante porque las etiquetas dentro de una etiqueta no las cuenta por separado.
    En nuestro caso tenemos:
    <h2>4.4</h2>
    <div>
        <p>....</p>
        <p>....</p>
    </div>
    <h2>4.5</h2>

    find_next_siblings() considerara todo el div como una etiqueta, y nosotros que intentamos tener 
    el texto. auqneu hagamos el .strip(), no considereara los retorno de carro de en medio (los que dividen cada parrafo de la web) 
    solo los de el inicio y el final de todo el texto
    En nuestro caso da igual porque lo que qeuremos es contar las palabras
    Por otro lado, si hubiera mas etiquetas al nivel de h2 las seguiria viendo e incluyendo hasta llegar al h2 del 4.5
    """
    for elemento in text4_4.find_next_siblings(): 
        if elemento.name == "h2": #quiero parar de guardar el texto al llegar a la siguiente seccion. Solo quiero las del 4.4  y no del 4.5
            break

        #print(elemento.get_text(strip=True))
        #informacion.append(elemento.text.strip())
        texto_subseccion = texto_subseccion + elemento.text.strip()
        #print(elemento.text)

    #print("\nesto es informacion: \n", texto_subseccion.strip())
    texto_subseccion_len = len(texto_subseccion.split())
    #print(f"\nEl numeor de palabras que tiene la subseccion {title4_4}: ", texto_subseccion_len) #2558
    return texto_subseccion_len


def numEtiquetaBuscar(soup, etiqueta_busqueda):
    numero_etiqueta = len(soup.find_all(etiqueta_busqueda))
    return numero_etiqueta



"""
Nunmero de veces que aparece "grave"/"graves" en el texto
"""
def contarPalabraGrave(soup):
    text = soup.text


    """
    Con .count(""), cuenta cuantas veces aparece una parabra con esos caracteres en ese orden.
    Es decir que para nuestro caso "grave" podria ser tambien "graves"o "gravemente"
    Por eso usaremos regex y findall
    finall busca todas la coincidencias
    \b indica que la palabra inicia o acaba.
    ? indica que el ultimo elemento puede o no aparecer
    """
    number_grave = len(re.findall(r"\bgraves?\b", text))

    #print("\n", number_grave)
    return number_grave


#SE PODRIA HACER EN UNA FILE SEPARADA
"""
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
#Recorro cada una de las url sacadas del csv
#Y actuo sobre ellas
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
"""



# TODO hacer historial de usuario 3


