import requests


url = "https://cima.aemps.es/cima/rest/medicamento"

params = {
    "nregistro": "91554"
}

response = requests.get(url, params=params)

print(response.status_code)
print(response.json())