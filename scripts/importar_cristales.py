import pandas as pd
from database import get_db_connection

# Ruta al archivo Excel (ajusta según la ubicación de tu archivo)
excel_file = "G:/cristalesv0.xlsx"  # Reemplaza con la ruta real, ej. "cristales.xlsx"

# Leer el Excel
df = pd.read_excel(excel_file)

# Asumimos que la columna con los cristales se llama "Cristales" (ajusta si es diferente)
cristales = df["Cristales"].tolist()

# Conectar a la base de datos usando database.py
conn = get_db_connection()
cursor = conn.cursor()

# Insertar cada cristal en la tabla
for cristal in cristales:
    try:
        query = "INSERT INTO cristales (nombre) VALUES (%s)"
        cursor.execute(query, (str(cristal),))  # Convertimos a string por si hay números
        conn.commit()
    except Exception as e:
        print(f"Error al insertar {cristal}: {e}")

# Cerrar la conexión
cursor.close()
conn.close()

print("Cristales importados exitosamente.")
print(f"Total importados: {len(cristales)}")