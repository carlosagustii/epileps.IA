import requests
import pandas as pd
import json

pagina = 1
n_registros = []
for i in range(5): #el total de filas es 988 y cada pagina son 200
    URL_BUSQUEDA = "https://cima.aemps.es/cima/rest/buscarEnFichaTecnica?pagina="+ str(pagina) 
    URL_MEDICAMENTO = "https://cima.aemps.es/cima/rest/medicamento"
    payload = json.dumps([
    {
        "seccion": "4.1",
        "texto": "epilepsia",
        "contiene": 1
    }
    ])
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", URL_BUSQUEDA, headers=headers, data=payload)
    respuesta_json=response.json() #devuelve diccionario de listas
    lista=respuesta_json["resultados"] #devuelve lista de diccionarios

    for i in lista:
        n_registros.append(i["nregistro"])#con estos nregistros hacemos posteriormente el get
    pagina+=1


columnas = []
for registro in n_registros:
    url = "https://cima.aemps.es/cima/rest/medicamento"

    params = {
        "nregistro": registro
    }

    response = requests.get(url, params=params)

    valores = response.json()
    fila = {
        "nregistro": valores.get("nregistro"),
        "nombre": valores.get("nombre"),
        "pactivos": valores.get("pactivos"),
        "labtitular": valores.get("labtitular"),
        "labcomercializador": valores.get("labcomercializador"),
        "cn": valores.get("cn"),
        "dosis": valores.get("dosis"),
        "forma_farmaceutica_simplificada": valores.get("forma_farmaceutica_simplificada"),
        "estado_aut": valores.get("estado_aut"),
        "estado_rev": valores.get("estado_rev"),
        "vias_administracion": valores.get("vias_administracion"),
        "comercializado": valores.get("comercializado"),
        "requiere_receta": valores.get("requiere_receta"),
        "generico": valores.get("generico"),
        "afecta_conduccion": valores.get("afecta_conduccion"),
        "triangulo_negro": valores.get("triangulo_negro"),
        "medicamento_huerfano": valores.get("medicamento_huerfano"),
        "biosimilar": valores.get("biosimilar"),
        "url_html_ficha_tecnica": valores.get("url_html_ficha_tecnica"),
        "url_foto_materiales": valores.get("url_foto_materiales"),
        "num_registros_atc": valores.get("num_registros_atc"),
        "num_principios_activos": valores.get("num_principios_activos"),
        "num_excipientes": valores.get("num_excipientes")
    }
    columnas.append(fila)
df = pd.DataFrame(columnas) #meto todas las filas añadidas en cada iteración asignada a cada nregistro
#print(df.head())

df.to_excel("medicamentos_epilepsia.xlsx", index=False) #lo pasamos al excel


