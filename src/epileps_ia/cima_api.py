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


print(len(n_registros))



