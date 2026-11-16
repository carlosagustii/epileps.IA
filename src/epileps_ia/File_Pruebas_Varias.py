"""
ESTE ES UN ARCHIVO AUXILIAR PARA COMPROBAR EN QUE DIFIERE 
EL NUEVO EXCEL data/medicamentos_epilepsia_HU1.xlsx CON EL ANTIGUO medicamentos_epilepsia.xlsx
"""

import pandas as pd


# Leer los Excel conservando los registros como texto
nuevo = pd.read_excel("../../data/medicamentos_epilepsia_HU1.xlsx", dtype={"nregistro": str})
#nuevo =  pd.read_excel("../../data/medicamentos_epilepsia_Pruebas.xlsx", dtype={"nregistro": str})
antiguo = pd.read_excel("medicamentos_epilepsia.xlsx", dtype={"nregistro": str})

# Limpiar posibles espacios
nuevo["nregistro"] = nuevo["nregistro"].str.strip()
antiguo["nregistro"] = antiguo["nregistro"].str.strip()

# Eliminar valores vacíos
reg_nuevo = nuevo["nregistro"].dropna()
reg_antiguo = antiguo["nregistro"].dropna()

# Comparar registros únicos
set_nuevo = set(reg_nuevo)
set_antiguo = set(reg_antiguo)

# Medicamentos nuevos y eliminados
nuevos = set_nuevo - set_antiguo
eliminados = set_antiguo - set_nuevo

# Resultados
print("===== RESUMEN =====")
print(f"Filas Excel nuevo: {len(reg_nuevo)}")
print(f"Filas Excel antiguo: {len(reg_antiguo)}")

print(f"Registros únicos nuevo: {len(set_nuevo)}")
print(f"Registros únicos antiguo: {len(set_antiguo)}")

print(f"\nMedicamentos nuevos: {len(nuevos)}")
print(f"Medicamentos eliminados: {len(eliminados)}")

print("\n===== NUEVOS MEDICAMENTOS =====")
print(sorted(nuevos))

print("\n===== MEDICAMENTOS ELIMINADOS =====")
print(sorted(eliminados))

# Comprobar si hay duplicados
print("\n===== DUPLICADOS =====")
print("Nuevo:", reg_nuevo[reg_nuevo.duplicated()].tolist())
print("Antiguo:", reg_antiguo[reg_antiguo.duplicated()].tolist())

"""
# Guardar diferencias en Excel
with pd.ExcelWriter("diferencias_medicamentos.xlsx") as writer:
    nuevo[nuevo["nregistro"].isin(nuevos)].to_excel(
        writer, sheet_name="Medicamentos nuevos", index=False
    )
    antiguo[antiguo["nregistro"].isin(eliminados)].to_excel(
        writer, sheet_name="Medicamentos eliminados", index=False
    )

print("\nInforme guardado en diferencias_medicamentos.xlsx")
"""