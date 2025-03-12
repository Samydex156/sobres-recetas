import pandas as pd
from database import get_db_connection
from datetime import datetime

# Ruta al archivo Excel (ajusta según la ubicación de tu archivo)
excel_file = "ruta_a_tu_archivo.xlsx"  # Reemplaza con la ruta real, ej. "recetas.xlsx"

# Tamaño del lote para procesamiento e inserción
CHUNK_SIZE = 1000  # Ajusta según tu memoria disponible (1000 filas por lote es un buen punto de partida)

# Conectar a la base de datos usando database.py
conn = get_db_connection()
cursor = conn.cursor()

# Consulta SQL con las 35 columnas (excluyendo id)
query = """
INSERT INTO recetas (
    numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion,
    fecha_receta, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od,
    cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi, esf_cerca_od,
    cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi, eje_cerca_oi, dip_lejos,
    dip_cerca, dip_od, dip_oi, base_lente, material_cristal_01, material_cristal_02,
    proveedor_optica, armador_optica, altura_lente, armazon_lente, numero_sobre,
    fecha_entrega, numero_pedido
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Contador de filas procesadas
total_filas = 0

# Leer el Excel en fragmentos
for chunk in pd.read_excel(excel_file, chunksize=CHUNK_SIZE):
    valores_lote = []
    
    # Procesar cada fila del fragmento
    for index, row in chunk.iterrows():
        try:
            # Convertir fechas al formato YYYY-MM-DD
            fecha_receta = datetime.strptime(str(row["FECHA_RECETA"]), "%d/%m/%Y").strftime("%Y-%m-%d") if pd.notna(row["FECHA_RECETA"]) else "-"
            fecha_entrega = datetime.strptime(str(row["FECHA_ENTREGA"]), "%d/%m/%Y").strftime("%Y-%m-%d") if pd.notna(row["FECHA_ENTREGA"]) else "-"

            # Mapear los valores, manteniendo "-" como valor válido
            valores = (
                row["NRO_RECETA"] if pd.notna(row["NRO_RECETA"]) else "-",
                row["NOMBRES"] if pd.notna(row["NOMBRES"]) else "-",
                row["AP_PATERNO"] if pd.notna(row["AP_PATERNO"]) else "-",
                row["AP_MATERNO"] if pd.notna(row["AP_MATERNO"]) else "-",
                row["DIR_TEL"] if pd.notna(row["DIR_TEL"]) else "-",
                fecha_receta,
                row["DOCTOR"] if pd.notna(row["DOCTOR"]) else "-",
                row["TIENDA"] if pd.notna(row["TIENDA"]) else "-",
                row["PROCEDENCIA"] if pd.notna(row["PROCEDENCIA"]) else "-",
                str(row["ESF_OD_LEJ"]) if pd.notna(row["ESF_OD_LEJ"]) else "-",
                str(row["CIL_OD_LEJ"]) if pd.notna(row["CIL_OD_LEJ"]) else "-",
                str(row["EJE_OD_LEJ"]) if pd.notna(row["EJE_OD_LEJ"]) else "-",
                str(row["ESF_OI_LEJ"]) if pd.notna(row["ESF_OI_LEJ"]) else "-",
                str(row["CIL_OI_LEJ"]) if pd.notna(row["CIL_OI_LEJ"]) else "-",
                str(row["EJE_OI_LEJ"]) if pd.notna(row["EJE_OI_LEJ"]) else "-",
                str(row["ESF_OD_CER"]) if pd.notna(row["ESF_OD_CER"]) else "-",
                str(row["CIL_OD_CER"]) if pd.notna(row["CIL_OD_CER"]) else "-",
                str(row["EJE_OD_CER"]) if pd.notna(row["EJE_OD_CER"]) else "-",
                str(row["ESF_OI_CER"]) if pd.notna(row["ESF_OI_CER"]) else "-",
                str(row["CIL_OI_CER"]) if pd.notna(row["CIL_OI_CER"]) else "-",
                str(row["EJE_OI_CER"]) if pd.notna(row["EJE_OI_CER"]) else "-",
                str(row["DIP_LEJOS"]) if pd.notna(row["DIP_LEJOS"]) else "-",
                str(row["DIP_CERCA"]) if pd.notna(row["DIP_CERCA"]) else "-",
                str(row["DIP_OD"]) if pd.notna(row["DIP_OD"]) else "-",
                str(row["DIP_OI"]) if pd.notna(row["DIP_OI"]) else "-",
                str(row["BASE"]) if pd.notna(row["BASE"]) else "-",
                str(row["CRISTALES_1"]) if pd.notna(row["CRISTALES_1"]) else "-",
                str(row["CRISTALES_2"]) if pd.notna(row["CRISTALES_2"]) else "-",
                str(row["PROVEEDOR"]) if pd.notna(row["PROVEEDOR"]) else "-",
                str(row["ARMADOR"]) if pd.notna(row["ARMADOR"]) else "-",
                str(row["ALTURA"]) if pd.notna(row["ALTURA"]) else "-",
                str(row["ARMAZON"]) if pd.notna(row["ARMAZON"]) else "-",
                str(row["NRO_SOBRE"]) if pd.notna(row["NRO_SOBRE"]) else "-",
                fecha_entrega,
                str(row["NRO_BOLETA"]) if pd.notna(row["NRO_BOLETA"]) else "-"
            )
            valores_lote.append(valores)
        except Exception as e:
            print(f"Error al procesar fila {index + total_filas + 2} (NRO_RECETA: {row['NRO_RECETA']}): {e}")
            continue

    # Insertar el lote completo
    try:
        cursor.executemany(query, valores_lote)
        conn.commit()
        total_filas += len(valores_lote)
        print(f"Insertadas {len(valores_lote)} filas (Total hasta ahora: {total_filas})")
    except Exception as e:
        print(f"Error al insertar lote de {len(valores_lote)} filas: {e}")
        conn.rollback()

# Cerrar la conexión
cursor.close()
conn.close()

print(f"Importación completada. Total de filas insertadas: {total_filas}")