import requests
import pandas as pd
import json
import numpy as np

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
        "cn": int(valores.get("presentaciones")[0].get("cn")),
        "dosis": valores.get("dosis"),
        "forma_farmaceutica_simplificada": valores.get("formaFarmaceuticaSimplificada")["nombre"],
        "estado_aut": pd.to_datetime(valores.get("estado").get("aut"), unit = "ms"), #nos lo dan en un formato raro que con esta función se pasa a fecha formateada
        "estado_rev": pd.to_datetime(valores.get("estado").get("rev"), unit= "ms") if valores.get("estado").get("rev") is not None else float("NaN"),
        "vias_administracion": valores.get("viasAdministracion")[0]["nombre"],  #nos lo dan en un formato raro que con esta función se pasa a fecha formateada
        "comercializado": float("1") if valores.get("comerc") is True else float("0"), #Indicador binario (1 si el campo comerc es verdadero, 0 en caso contrario)
        "requiere_receta": float("1") if valores.get("receta") is True else float("0"),    
        "generico": float("1") if valores.get("generico") is True else float("0"),
        "afecta_conduccion": float("1") if valores.get("conduc") is True else float("0"),
        "triangulo_negro":float("1") if valores.get("triangulo") is True else float("0"),
        "medicamento_huerfano": float("1") if valores.get("huerfano") is True else float("0"),
        "biosimilar": float("1") if valores.get("biosimilar") is True else float("0"),
        "url_html_ficha_tecnica": ([doc.get("urlHtml") for doc in valores.get("docs", []) if doc.get("tipo") == 1 and doc.get("urlHtml", "").lower().endswith(".html")] or [np.nan])[0],
        "url_foto_materiales": ([foto.get("url") for foto in valores.get("fotos", []) if "material" in foto.get("tipo", "").lower() and foto.get("url", "").lower().endswith(".jpg")] or [np.nan])[0],
        "num_registros_atc": len(valores.get("atcs")),
        "num_principios_activos": len(valores.get("principiosActivos") or []), #el or por si devuelve None la API, que me lo ha hecho con excipientes
        "num_excipientes": len(valores.get("excipiente") or [])
    }
    columnas.append(fila)
df = pd.DataFrame(columnas) #meto todas las filas añadidas en cada iteración asignada a cada nregistro
#print(df.head())

df.to_excel("src/epileps_ia/medicamentos_epilepsia.xlsx", index=False, na_rep="NaN") #lo pasamos al excel y quier que se vean los NaN


