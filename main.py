from fastapi import FastAPI, Form, Request, HTTPException, Query, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import get_db_connection
from typing import Optional
import pandas as pd
import io
from psycopg2.extras import DictCursor  # Importar DictCursor para resultados como diccionarios

# Crear la aplicación FastAPI
app = FastAPI()

# Montar la carpeta "static" para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

########################################################################################################################################
# RUTAS PARA MANEJAR LOS SOBRES
########################################################################################################################################

# Función auxiliar para verificar si un número de sobre ya existe
async def check_numero_sobre_exists(numero_sobre: str, exclude_id: Optional[int] = None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if exclude_id is None:
            query = "SELECT COUNT(*) FROM sobres WHERE numero_sobre = %s"
            cursor.execute(query, (numero_sobre,))
        else:
            query = "SELECT COUNT(*) FROM sobres WHERE numero_sobre = %s AND id != %s"
            cursor.execute(query, (numero_sobre, exclude_id))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta Principal para abrir el formulario de registro de sobres
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Mostrar todos los registros
@app.get("/registros", response_class=HTMLResponse)
async def mostrar_registros(request: Request):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor para resultados como diccionarios
        cursor.execute("SELECT * FROM sobres ORDER BY fecha_cancelacion DESC")
        registros = cursor.fetchall()
        return templates.TemplateResponse("registros.html", {"request": request, "registros": registros})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para registrar un sobre
@app.post("/registrar")
async def registrar_sobre(
    numero_sobre: str = Form(...),
    numero_pedido: str = Form(default="-"),
    cliente: str = Form(default="Sin nombre"),
    fecha_cancelacion: Optional[str] = Form(default=None),
    tienda: str = Form(default="-"),
    proveedor: str = Form(default="-"),
    modelo: str = Form(default="-"),
    armazon: str = Form(default="-"),
    doctor: str = Form(default="-"),
    monto_total: float = Form(default=0.0),
    monto_cuenta: float = Form(default=0.0),
    saldo: float = Form(default=0.0),
    estado_pago: str = Form(default="CANCELADO")
):
    # Verificar si el número de sobre ya existe
    if await check_numero_sobre_exists(numero_sobre):
        raise HTTPException(status_code=400, detail="El número de sobre ya existe.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if fecha_cancelacion == "":
            fecha_cancelacion = None
        query = """
        INSERT INTO sobres (numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda, proveedor, modelo, armazon, doctor, monto_total, monto_cuenta, saldo, estado_pago)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda, proveedor, modelo, armazon, doctor, monto_total, monto_cuenta, saldo, estado_pago)
        cursor.execute(query, values)
        conn.commit()
        return JSONResponse(status_code=200, content={"message": "Sobre registrado exitosamente"})
    except HTTPException as e:
        # Re-lanzar excepciones HTTP directamente
        raise e
    except Exception as e:
        # Manejar otros errores no esperados
        raise HTTPException(status_code=500, detail=f"Error al registrar: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Actualizar un registro
@app.post("/actualizar/{sobre_id}")
async def actualizar_sobre(
    sobre_id: int,
    numero_sobre: str = Form(...),
    numero_pedido: str = Form(default="-"),
    cliente: str = Form(default="Sin nombre"),
    fecha_cancelacion: Optional[str] = Form(default=None),
    tienda: str = Form(default="-"),
    proveedor: str = Form(default="-"),
    modelo: str = Form(default="-"),
    armazon: str = Form(default="-"),
    doctor: str = Form(default="-"),
    monto_total: float = Form(default=0.0),
    monto_cuenta: float = Form(default=0.0),
    saldo: float = Form(default=0.0),
    estado_pago: str = Form(default="CANCELADO")
):
    # Verificar si el número de sobre ya existe (excluyendo el registro actual)
    if await check_numero_sobre_exists(numero_sobre, exclude_id=sobre_id):
        raise HTTPException(status_code=400, detail="El número de sobre ya existe.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if fecha_cancelacion == "":
            fecha_cancelacion = None
        query = """
        UPDATE sobres 
        SET numero_sobre=%s, numero_pedido=%s, cliente=%s, fecha_cancelacion=%s, 
        tienda=%s, proveedor=%s, modelo=%s, armazon=%s, doctor=%s, monto_total=%s, 
        monto_cuenta=%s, saldo=%s, estado_pago=%s
        WHERE id=%s
        """
        values = (
            numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda,
            proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
            saldo, estado_pago, sobre_id
        )
        cursor.execute(query, values)
        conn.commit()
        return JSONResponse(status_code=200, content={"message": "Registro actualizado exitosamente"})
    except HTTPException as e:
        # Re-lanzar excepciones HTTP directamente
        raise e
    except Exception as e:
        # Manejar otros errores no esperados
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Mostrar formulario de edición
@app.get("/editar/{sobre_id}", response_class=HTMLResponse)
async def mostrar_formulario_edicion(request: Request, sobre_id: int):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        
        # Obtener el registro
        cursor.execute("SELECT * FROM sobres WHERE id = %s", (sobre_id,))
        registro = cursor.fetchone()
        if not registro:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        
        # Obtener las listas de opciones
        cursor.execute("SELECT nombre FROM doctores")
        doctores = cursor.fetchall()
        cursor.execute("SELECT nombre FROM tiendas")
        tiendas = cursor.fetchall()
        cursor.execute("SELECT nombre FROM proveedores")
        proveedores = cursor.fetchall()
        cursor.execute("SELECT nombre FROM estados_pago")
        estados_pago = cursor.fetchall()
        
        return templates.TemplateResponse("editar.html", {
            "request": request,
            "registro": registro,
            "doctores": [doctor["nombre"] for doctor in doctores],
            "tiendas": [tienda["nombre"] for tienda in tiendas],
            "proveedores": [proveedor["nombre"] for proveedor in proveedores],
            "estados_pago": [estado["nombre"] for estado in estados_pago]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registro: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Eliminar un registro
@app.post("/eliminar/{sobre_id}")
async def eliminar_sobre(sobre_id: int):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "DELETE FROM sobres WHERE id=%s"
        cursor.execute(query, (sobre_id,))
        conn.commit()
        return JSONResponse(status_code=200, content={"message": "Registro eliminado exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para mostrar la página de búsqueda
@app.get("/buscar", response_class=HTMLResponse)
async def mostrar_formulario_busqueda(request: Request):
    return templates.TemplateResponse("buscar.html", {"request": request})

# Endpoint para buscar registros dinámicamente
@app.get("/api/buscar", response_class=JSONResponse)
async def buscar_registros(
    numero_sobre: Optional[str] = Query(None),
    numero_pedido: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor

        # Construir la consulta SQL dinámicamente
        query = "SELECT * FROM sobres WHERE 1=1"
        params = []

        if numero_sobre:
            query += " AND numero_sobre LIKE %s"
            params.append(f"%{numero_sobre}%")
        if numero_pedido:
            query += " AND numero_pedido LIKE %s"
            params.append(f"%{numero_pedido}%")
        if cliente:
            query += " AND cliente LIKE %s"
            params.append(f"%{cliente}%")
        if fecha_inicio and fecha_fin:
            query += " AND fecha_cancelacion BETWEEN %s AND %s"
            params.append(fecha_inicio)
            params.append(fecha_fin)
        elif fecha_inicio:
            query += " AND fecha_cancelacion >= %s"
            params.append(fecha_inicio)
        elif fecha_fin:
            query += " AND fecha_cancelacion <= %s"
            params.append(fecha_fin)

        cursor.execute(query, params)
        registros = cursor.fetchall()
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar registros: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para mostrar la página de importación
@app.get("/importar", response_class=HTMLResponse)
async def mostrar_formulario_importar(request: Request):
    return templates.TemplateResponse("importar.html", {"request": request})

# Endpoint para importar datos desde Excel
@app.post("/importar")
async def importar_datos(file: UploadFile = File(...)):
    try:
        # Verificar que el archivo sea un Excel
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

        # Leer el archivo Excel
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl')

        # Verificar que las columnas necesarias existan
        required_columns = [
            'numero_sobre', 'numero_pedido', 'cliente', 'fecha_cancelacion',
            'tienda', 'proveedor', 'modelo', 'armazon', 'doctor',
            'monto_total', 'monto_cuenta', 'saldo', 'estado_pago'
        ]
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail="El archivo Excel debe contener todas las columnas requeridas: " + ", ".join(required_columns))

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insertar cada fila en la base de datos
            inserted_rows = 0
            for _, row in df.iterrows():
                numero_sobre = str(row['numero_sobre']).strip()
                
                # Verificar si el número de sobre ya existe
                if await check_numero_sobre_exists(numero_sobre):
                    continue  # Saltar este registro si el número de sobre ya existe

                # Manejar valores nulos o vacíos
                numero_pedido = str(row['numero_pedido']).strip() if pd.notna(row['numero_pedido']) else ""
                cliente = str(row['cliente']).strip() if pd.notna(row['cliente']) else ""
                fecha_cancelacion = row['fecha_cancelacion'] if pd.notna(row['fecha_cancelacion']) else None
                tienda = str(row['tienda']).strip() if pd.notna(row['tienda']) else ""
                proveedor = str(row['proveedor']).strip() if pd.notna(row['proveedor']) else ""
                modelo = str(row['modelo']).strip() if pd.notna(row['modelo']) else ""
                armazon = str(row['armazon']).strip() if pd.notna(row['armazon']) else ""
                doctor = str(row['doctor']).strip() if pd.notna(row['doctor']) else ""
                monto_total = float(row['monto_total']) if pd.notna(row['monto_total']) else 0.0
                monto_cuenta = float(row['monto_cuenta']) if pd.notna(row['monto_cuenta']) else 0.0
                saldo = float(row['saldo']) if pd.notna(row['saldo']) else 0.0
                estado_pago = str(row['estado_pago']).strip() if pd.notna(row['estado_pago']) else "pendiente"

                query = """
                INSERT INTO sobres (numero_sobre, numero_pedido, cliente, fecha_cancelacion, 
                tienda, proveedor, modelo, armazon, doctor, monto_total, monto_cuenta, 
                saldo, estado_pago)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda,
                    proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
                    saldo, estado_pago
                )
                cursor.execute(query, values)
                inserted_rows += 1

            conn.commit()
            return JSONResponse(status_code=200, content={"message": f"Datos importados exitosamente. {inserted_rows} registros añadidos."})
        except Exception as e:
            if conn:
                conn.rollback()
            raise HTTPException(status_code=500, detail=f"Error al importar datos: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")

# Ruta para mostrar la página de estadísticas
@app.get("/estadisticas", response_class=HTMLResponse)
async def mostrar_estadisticas(request: Request):
    return templates.TemplateResponse("estadisticas.html", {"request": request})

# Endpoint para obtener estadísticas
@app.get("/api/estadisticas", response_class=JSONResponse)
async def obtener_estadisticas():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor

        # Total de sobres
        cursor.execute("SELECT COUNT(*) as total_sobres FROM sobres")
        total_sobres = cursor.fetchone()["total_sobres"]

        # Monto total acumulado
        cursor.execute("SELECT SUM(monto_total) as monto_total_acumulado FROM sobres")
        monto_total_acumulado = cursor.fetchone()["monto_total_acumulado"] or 0.0

        # Monto a cuenta acumulado
        cursor.execute("SELECT SUM(monto_cuenta) as monto_cuenta_acumulado FROM sobres")
        monto_cuenta_acumulado = cursor.fetchone()["monto_cuenta_acumulado"] or 0.0

        # Saldo acumulado
        cursor.execute("SELECT SUM(saldo) as saldo_acumulado FROM sobres")
        saldo_acumulado = cursor.fetchone()["saldo_acumulado"] or 0.0

        # Registros por estado de pago
        cursor.execute("SELECT estado_pago, COUNT(*) as cantidad FROM sobres GROUP BY estado_pago")
        estado_pago_data = cursor.fetchall()
        estado_pago_stats = {row["estado_pago"]: row["cantidad"] for row in estado_pago_data}

        # Registros por tienda
        cursor.execute("SELECT tienda, COUNT(*) as cantidad FROM sobres GROUP BY tienda")
        tienda_data = cursor.fetchall()
        tienda_stats = {row["tienda"]: row["cantidad"] for row in tienda_data}

        # Registros por proveedor
        cursor.execute("SELECT proveedor, COUNT(*) as cantidad FROM sobres GROUP BY proveedor")
        proveedor_data = cursor.fetchall()
        proveedor_stats = {row["proveedor"]: row["cantidad"] for row in proveedor_data}

        # Registros por mes (evolución temporal)
        cursor.execute("""
            SELECT TO_CHAR(fecha_cancelacion, 'YYYY-MM') as mes, 
                   COUNT(*) as cantidad 
            FROM sobres 
            WHERE fecha_cancelacion IS NOT NULL 
            GROUP BY mes 
            ORDER BY mes
        """)
        evolucion_data = cursor.fetchall()
        evolucion_stats = [{"mes": row["mes"], "cantidad": row["cantidad"]} for row in evolucion_data]

        return {
            "total_sobres": total_sobres,
            "monto_total_acumulado": monto_total_acumulado,
            "monto_cuenta_acumulado": monto_cuenta_acumulado,
            "saldo_acumulado": saldo_acumulado,
            "estado_pago_stats": estado_pago_stats,
            "tienda_stats": tienda_stats,
            "proveedor_stats": proveedor_stats,
            "evolucion_stats": evolucion_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para obtener la lista de doctores (para autocompletado)
@app.get("/api/doctores", response_class=JSONResponse)
async def obtener_doctores(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor

        if query:
            cursor.execute("SELECT nombre FROM doctores WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM doctores")
        
        doctores = cursor.fetchall()
        return [doctor["nombre"] for doctor in doctores]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener doctores: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para obtener la lista de tiendas (para autocompletado)
@app.get("/api/tiendas", response_class=JSONResponse)
async def obtener_tiendas(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM tiendas WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM tiendas")
        tiendas = cursor.fetchall()
        return [tienda["nombre"] for tienda in tiendas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tiendas: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para obtener la lista de proveedores (para autocompletado)
@app.get("/api/proveedores", response_class=JSONResponse)
async def obtener_proveedores(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM proveedores WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM proveedores")
        proveedores = cursor.fetchall()
        return [proveedor["nombre"] for proveedor in proveedores]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proveedores: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para obtener la lista de estados_pago (para autocompletado)
@app.get("/api/estados_pago", response_class=JSONResponse)
async def obtener_estados_pago(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM estados_pago WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM estados_pago")
        estados_pago = cursor.fetchall()
        return [estado["nombre"] for estado in estados_pago]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estados_pago: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

########################################################################################################################################
# RUTAS PARA MANEJAR LAS RECETAS
########################################################################################################################################

# Función auxiliar para verificar si un número de receta ya existe
async def check_numero_receta_exists(numero_receta: str, exclude_id: Optional[int] = None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if exclude_id is None:
            query = "SELECT COUNT(*) FROM recetas WHERE numero_receta = %s"
            cursor.execute(query, (numero_receta,))
        else:
            query = "SELECT COUNT(*) FROM recetas WHERE numero_receta = %s AND id != %s"
            cursor.execute(query, (numero_receta, exclude_id))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta principal para el formulario de recetas
@app.get("/recetas", response_class=HTMLResponse)
async def read_recetas_form(request: Request):
    return templates.TemplateResponse("receta_form.html", {"request": request})

# Ruta para registrar una receta
@app.post("/registrar_receta")
async def registrar_receta(
    # Datos cliente
    numero_receta: str = Form(...),
    nombres_cliente: str = Form(...),
    apellido_paterno: str = Form(default="-"),
    apellido_materno: str = Form(default="-"),
    telefono_direccion: str = Form(default="-"),
    fecha_receta: Optional[str] = Form(default=None),
    doctor_receta: str = Form(default="-"),
    tienda_optica: str = Form(default="-"),
    procedencia_cliente: str = Form(default="-"),

    # Datos receta
    esf_lejos_od: str = Form(default="-"),
    cil_lejos_od: str = Form(default="-"),
    eje_lejos_od: str = Form(default="-"),
    esf_lejos_oi: str = Form(default="-"),
    cil_lejos_oi: str = Form(default="-"),
    eje_lejos_oi: str = Form(default="-"),
    esf_cerca_od: str = Form(default="-"),
    cil_cerca_od: str = Form(default="-"),
    eje_cerca_od: str = Form(default="-"),
    esf_cerca_oi: str = Form(default="-"),
    cil_cerca_oi: str = Form(default="-"),
    eje_cerca_oi: str = Form(default="-"),
    dip_lejos: str = Form(default="-"),
    dip_cerca: str = Form(default="-"),
    dip_od: str = Form(default="-"),
    dip_oi: str = Form(default="-"),
    base_lente: str = Form(default="-"),
    material_cristal_01: str = Form(default="-"),
    material_cristal_02: str = Form(default="-"),

    # Datos adicionales
    proveedor_optica: str = Form(default="-"),
    armador_optica: str = Form(default="-"),
    altura_lente: str = Form(default="-"),
    armazon_lente: str = Form(default="-"),
    numero_sobre: str = Form(default="-"),
    fecha_entrega: Optional[str] = Form(default=None),
    numero_pedido: str = Form(default="-")
):
    # Verificar si el número de receta ya existe
    if await check_numero_receta_exists(numero_receta):
        raise HTTPException(status_code=400, detail="El número de receta ya existe.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if fecha_receta == "":
            fecha_receta = None
        if fecha_entrega == "":
            fecha_entrega = None
        query = """
        INSERT INTO recetas 
        (numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion, fecha_receta, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od, cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi, esf_cerca_od, cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi, eje_cerca_oi, dip_lejos, dip_cerca, dip_od, dip_oi, base_lente, material_cristal_01, material_cristal_02, proveedor_optica, armador_optica, altura_lente, armazon_lente, numero_sobre, fecha_entrega, numero_pedido) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        values = (numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion, fecha_receta, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od, cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi, esf_cerca_od, cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi, eje_cerca_oi, dip_lejos, dip_cerca, dip_od, dip_oi, base_lente, material_cristal_01, material_cristal_02, proveedor_optica, armador_optica, altura_lente, armazon_lente, numero_sobre, fecha_entrega, numero_pedido)
        cursor.execute(query, values)
        conn.commit()
        return JSONResponse(status_code=200, content={"message": "Receta registrada exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar receta: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para autocompletado de armazones
@app.get("/api/armazones", response_class=JSONResponse)
async def obtener_armazones(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM armazones WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM armazones")
        armazones = cursor.fetchall()
        return [armazon["nombre"] for armazon in armazones]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener armazones: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para autocompletado de procedencias
@app.get("/api/procedencias", response_class=JSONResponse)
async def obtener_procedencias(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM procedencias WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM procedencias")
        procedencias = cursor.fetchall()
        return [proc["nombre"] for proc in procedencias]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener procedencias: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para autocompletado de armadores
@app.get("/api/armadores", response_class=JSONResponse)
async def obtener_armadores(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM armadores WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM armadores")
        armadores = cursor.fetchall()
        return [armador["nombre"] for armador in armadores]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener armadores: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint para autocompletado de cristales
@app.get("/api/cristales", response_class=JSONResponse)
async def obtener_cristales(query: Optional[str] = Query(None)):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        if query:
            cursor.execute("SELECT nombre FROM cristales WHERE nombre LIKE %s", (f"%{query}%",))
        else:
            cursor.execute("SELECT nombre FROM cristales")
        cristales = cursor.fetchall()
        return [cristal["nombre"] for cristal in cristales]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cristales: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

############################################################################################
# RUTAS PARA MOSTRAR LOS REGISTROS DE RECETAS
############################################################################################

# Ruta para mostrar todos los registros de recetas con filtros y paginación
@app.get("/registros-recetas", response_class=HTMLResponse)
async def read_registros_recetas(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    nombres_cliente: Optional[str] = Query(None),
    apellido_paterno: Optional[str] = Query(None),
    apellido_materno: Optional[str] = Query(None),
    fecha_entrega_desde: Optional[str] = Query(None),
    fecha_entrega_hasta: Optional[str] = Query(None)
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor

        # Construir la consulta base
        query_base = "SELECT * FROM recetas WHERE 1=1"
        query_count = "SELECT COUNT(*) as total FROM recetas WHERE 1=1"
        params = []

        # Aplicar filtros
        if nombres_cliente:
            query_base += " AND nombres_cliente LIKE %s"
            query_count += " AND nombres_cliente LIKE %s"
            params.append(f"%{nombres_cliente}%")
        if apellido_paterno:
            query_base += " AND apellido_paterno LIKE %s"
            query_count += " AND apellido_paterno LIKE %s"
            params.append(f"%{apellido_paterno}%")
        if apellido_materno:
            query_base += " AND apellido_materno LIKE %s"
            query_count += " AND apellido_materno LIKE %s"
            params.append(f"%{apellido_materno}%")
        if fecha_entrega_desde:
            query_base += " AND fecha_entrega >= %s"
            query_count += " AND fecha_entrega >= %s"
            params.append(fecha_entrega_desde)
        if fecha_entrega_hasta:
            query_base += " AND fecha_entrega <= %s"
            query_count += " AND fecha_entrega <= %s"
            params.append(fecha_entrega_hasta)

        # Contar el total de registros filtrados
        cursor.execute(query_count, params)
        total_records = cursor.fetchone()["total"]
        total_pages = (total_records + per_page - 1) // per_page

        if page > total_pages:
            page = total_pages if total_pages > 0 else 1

        offset = (page - 1) * per_page

        # Obtener los registros paginados
        query = f"{query_base} ORDER BY fecha_receta DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(query, params)
        recetas = cursor.fetchall()

        return templates.TemplateResponse(
            "registros_recetas.html",
            {
                "request": request,
                "recetas": recetas,
                "current_page": page,
                "total_pages": total_pages,
                "per_page": per_page,
                "total_records": total_records,
                "nombres_cliente": nombres_cliente or "",
                "apellido_paterno": apellido_paterno or "",
                "apellido_materno": apellido_materno or "",
                "fecha_entrega_desde": fecha_entrega_desde or "",
                "fecha_entrega_hasta": fecha_entrega_hasta or ""
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Endpoint API para obtener datos filtrados dinámicamente (usado por JavaScript)
@app.get("/api/registros-recetas", response_class=JSONResponse)
async def api_registros_recetas(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    nombres_cliente: Optional[str] = Query(None),
    apellido_paterno: Optional[str] = Query(None),
    apellido_materno: Optional[str] = Query(None),
    fecha_entrega_desde: Optional[str] = Query(None),
    fecha_entrega_hasta: Optional[str] = Query(None)
):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor

        query_base = "SELECT * FROM recetas WHERE 1=1"
        query_count = "SELECT COUNT(*) as total FROM recetas WHERE 1=1"
        params = []

        if nombres_cliente:
            query_base += " AND nombres_cliente LIKE %s"
            query_count += " AND nombres_cliente LIKE %s"
            params.append(f"%{nombres_cliente}%")
        if apellido_paterno:
            query_base += " AND apellido_paterno LIKE %s"
            query_count += " AND apellido_paterno LIKE %s"
            params.append(f"%{apellido_paterno}%")
        if apellido_materno:
            query_base += " AND apellido_materno LIKE %s"
            query_count += " AND apellido_materno LIKE %s"
            params.append(f"%{apellido_materno}%")
        if fecha_entrega_desde:
            query_base += " AND fecha_entrega >= %s"
            query_count += " AND fecha_entrega >= %s"
            params.append(fecha_entrega_desde)
        if fecha_entrega_hasta:
            query_base += " AND fecha_entrega <= %s"
            query_count += " AND fecha_entrega <= %s"
            params.append(fecha_entrega_hasta)

        cursor.execute(query_count, params)
        total_records = cursor.fetchone()["total"]
        total_pages = (total_records + per_page - 1) // per_page

        if page > total_pages:
            page = total_pages if total_pages > 0 else 1

        offset = (page - 1) * per_page
        query = f"{query_base} ORDER BY fecha_receta DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(query, params)
        recetas = cursor.fetchall()

        return {
            "recetas": recetas,
            "current_page": page,
            "total_pages": total_pages,
            "total_records": total_records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para mostrar el formulario de edición
@app.get("/editar-receta/{receta_id}", response_class=HTMLResponse)
async def edit_receta_form(request: Request, receta_id: int):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=DictCursor)  # Usar DictCursor
        cursor.execute("SELECT * FROM recetas WHERE id = %s", (receta_id,))
        receta = cursor.fetchone()
        if not receta:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        return templates.TemplateResponse("editar_receta.html", {"request": request, "receta": receta})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener receta: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para actualizar una receta
@app.post("/actualizar-receta/{receta_id}")
async def actualizar_receta(
    receta_id: int,
    numero_receta: str = Form(...),
    nombres_cliente: str = Form(...),
    apellido_paterno: str = Form(default="-"),
    apellido_materno: str = Form(default="-"),
    telefono_direccion: str = Form(default="-"),
    fecha_receta: Optional[str] = Form(default=None),
    doctor_receta: str = Form(default="-"),
    tienda_optica: str = Form(default="-"),
    procedencia_cliente: str = Form(default="-"),
    esf_lejos_od: str = Form(default="-"),
    cil_lejos_od: str = Form(default="-"),
    eje_lejos_od: str = Form(default="-"),
    esf_lejos_oi: str = Form(default="-"),
    cil_lejos_oi: str = Form(default="-"),
    eje_lejos_oi: str = Form(default="-"),
    esf_cerca_od: str = Form(default="-"),
    cil_cerca_od: str = Form(default="-"),
    eje_cerca_od: str = Form(default="-"),
    esf_cerca_oi: str = Form(default="-"),
    cil_cerca_oi: str = Form(default="-"),
    eje_cerca_oi: str = Form(default="-"),
    dip_lejos: str = Form(default="-"),
    dip_cerca: str = Form(default="-"),
    dip_od: str = Form(default="-"),
    dip_oi: str = Form(default="-"),
    base_lente: str = Form(default="-"),
    material_cristal_01: str = Form(default="-"),
    material_cristal_02: str = Form(default="-"),
    proveedor_optica: str = Form(default="-"),
    armador_optica: str = Form(default="-"),
    altura_lente: str = Form(default="-"),
    armazon_lente: str = Form(default="-"),
    numero_sobre: str = Form(default="-"),
    fecha_entrega: Optional[str] = Form(default=None),
    numero_pedido: str = Form(default="-")
):
    if await check_numero_receta_exists(numero_receta, exclude_id=receta_id):
        raise HTTPException(status_code=400, detail="El número de receta ya existe para otro registro.")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if fecha_receta == "":
            fecha_receta = None
        if fecha_entrega == "":
            fecha_entrega = None
        query = """
        UPDATE recetas SET 
            numero_receta = %s, nombres_cliente = %s, apellido_paterno = %s, apellido_materno = %s, 
            telefono_direccion = %s, fecha_receta = %s, doctor_receta = %s, tienda_optica = %s, 
            procedencia_cliente = %s, esf_lejos_od = %s, cil_lejos_od = %s, eje_lejos_od = %s, 
            esf_lejos_oi = %s, cil_lejos_oi = %s, eje_lejos_oi = %s, esf_cerca_od = %s, 
            cil_cerca_od = %s, eje_cerca_od = %s, esf_cerca_oi = %s, cil_cerca_oi = %s, 
            eje_cerca_oi = %s, dip_lejos = %s, dip_cerca = %s, dip_od = %s, dip_oi = %s, 
            base_lente = %s, material_cristal_01 = %s, material_cristal_02 = %s, 
            proveedor_optica = %s, armador_optica = %s, altura_lente = %s, armazon_lente = %s, 
            numero_sobre = %s, fecha_entrega = %s, numero_pedido = %s
        WHERE id = %s"""
        values = (
            numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion,
            fecha_receta, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od, cil_lejos_od,
            eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi, esf_cerca_od, cil_cerca_od,
            eje_cerca_od, esf_cerca_oi, cil_cerca_oi, eje_cerca_oi, dip_lejos, dip_cerca, dip_od,
            dip_oi, base_lente, material_cristal_01, material_cristal_02, proveedor_optica,
            armador_optica, altura_lente, armazon_lente, numero_sobre, fecha_entrega, numero_pedido,
            receta_id
        )
        cursor.execute(query, values)
        conn.commit()
        return RedirectResponse(url="/registros-recetas", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar receta: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para eliminar una receta
@app.post("/eliminar-receta/{receta_id}")
async def eliminar_receta(receta_id: int):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recetas WHERE id = %s", (receta_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Receta no encontrada")
        conn.commit()
        return RedirectResponse(url="/registros-recetas", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar receta: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()