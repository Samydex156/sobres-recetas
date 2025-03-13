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

# Verificar si un número de sobre ya existe
async def check_numero_sobre_exists(numero_sobre: str, exclude_id: Optional[int] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT EXISTS(SELECT 1 FROM sobres WHERE numero_sobre = %s"
            if exclude_id:
                query += " AND id != %s"
            query += ")"
            params = [numero_sobre] if not exclude_id else [numero_sobre, exclude_id]
            cursor.execute(query, params)
            return cursor.fetchone()["exists"]
    finally:
        conn.close()

# Ruta principal para formulario de sobres
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Mostrar todos los registros de sobres
@app.get("/registros", response_class=HTMLResponse)
async def mostrar_registros(request: Request):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT id, numero_sobre, numero_pedido, cliente, fecha_cancelacion::text, 
                       tienda, proveedor, modelo, armazon, doctor, monto_total, 
                       monto_cuenta, saldo, estado_pago 
                FROM sobres 
                ORDER BY fecha_cancelacion DESC
            """)
            registros = [dict(row) for row in cursor.fetchall()]
            return templates.TemplateResponse("registros.html", {"request": request, "registros": registros})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")
    finally:
        conn.close()

# Registrar un sobre
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
    if await check_numero_sobre_exists(numero_sobre):
        raise HTTPException(status_code=400, detail="El número de sobre ya existe.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO sobres (
                    numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda, 
                    proveedor, modelo, armazon, doctor, monto_total, monto_cuenta, 
                    saldo, estado_pago
                ) VALUES (%s, %s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                numero_sobre, numero_pedido, cliente, fecha_cancelacion or None, tienda,
                proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
                saldo, estado_pago
            )
            cursor.execute(query, values)
            conn.commit()
            return JSONResponse(status_code=200, content={"message": "Sobre registrado exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar: {str(e)}")
    finally:
        conn.close()

# Actualizar un sobre
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
    if await check_numero_sobre_exists(numero_sobre, exclude_id=sobre_id):
        raise HTTPException(status_code=400, detail="El número de sobre ya existe.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                UPDATE sobres SET
                    numero_sobre = %s, numero_pedido = %s, cliente = %s, fecha_cancelacion = %s::date,
                    tienda = %s, proveedor = %s, modelo = %s, armazon = %s, doctor = %s,
                    monto_total = %s, monto_cuenta = %s, saldo = %s, estado_pago = %s
                WHERE id = %s
            """
            values = (
                numero_sobre, numero_pedido, cliente, fecha_cancelacion or None, tienda,
                proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
                saldo, estado_pago, sobre_id
            )
            cursor.execute(query, values)
            conn.commit()
            return JSONResponse(status_code=200, content={"message": "Registro actualizado exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")
    finally:
        conn.close()

# Mostrar formulario de edición
@app.get("/editar/{sobre_id}", response_class=HTMLResponse)
async def mostrar_formulario_edicion(request: Request, sobre_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM sobres WHERE id = %s", (sobre_id,))
            registro = cursor.fetchone()
            if not registro:
                raise HTTPException(status_code=404, detail="Registro no encontrado")

            cursor.execute("SELECT nombre FROM doctores ORDER BY nombre")
            doctores = [row["nombre"] for row in cursor.fetchall()]
            cursor.execute("SELECT nombre FROM tiendas ORDER BY nombre")
            tiendas = [row["nombre"] for row in cursor.fetchall()]
            cursor.execute("SELECT nombre FROM proveedores ORDER BY nombre")
            proveedores = [row["nombre"] for row in cursor.fetchall()]
            cursor.execute("SELECT nombre FROM estados_pago ORDER BY nombre")
            estados_pago = [row["nombre"] for row in cursor.fetchall()]

            return templates.TemplateResponse("editar.html", {
                "request": request,
                "registro": dict(registro),
                "doctores": doctores,
                "tiendas": tiendas,
                "proveedores": proveedores,
                "estados_pago": estados_pago
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registro: {str(e)}")
    finally:
        conn.close()

# Eliminar un sobre
@app.post("/eliminar/{sobre_id}")
async def eliminar_sobre(sobre_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM sobres WHERE id = %s", (sobre_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Registro no encontrado")
            conn.commit()
            return JSONResponse(status_code=200, content={"message": "Registro eliminado exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
    finally:
        conn.close()

# Mostrar página de búsqueda
@app.get("/buscar", response_class=HTMLResponse)
async def mostrar_formulario_busqueda(request: Request):
    return templates.TemplateResponse("buscar.html", {"request": request})

# Buscar registros dinámicamente
@app.get("/api/buscar", response_class=JSONResponse)
async def buscar_registros(
    numero_sobre: Optional[str] = Query(None),
    numero_pedido: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None)
):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = """
                SELECT id, numero_sobre, numero_pedido, cliente, fecha_cancelacion::text, 
                       tienda, proveedor, modelo, armazon, doctor, monto_total, 
                       monto_cuenta, saldo, estado_pago 
                FROM sobres WHERE 1=1
            """
            params = []

            if numero_sobre:
                query += " AND numero_sobre ILIKE %s"
                params.append(f"%{numero_sobre}%")
            if numero_pedido:
                query += " AND numero_pedido ILIKE %s"
                params.append(f"%{numero_pedido}%")
            if cliente:
                query += " AND cliente ILIKE %s"
                params.append(f"%{cliente}%")
            if fecha_inicio and fecha_fin:
                query += " AND fecha_cancelacion BETWEEN %s::date AND %s::date"
                params.extend([fecha_inicio, fecha_fin])
            elif fecha_inicio:
                query += " AND fecha_cancelacion >= %s::date"
                params.append(fecha_inicio)
            elif fecha_fin:
                query += " AND fecha_cancelacion <= %s::date"
                params.append(fecha_fin)

            cursor.execute(query, params)
            registros = [dict(row) for row in cursor.fetchall()]
            return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar registros: {str(e)}")
    finally:
        conn.close()

# Mostrar página de importación
@app.get("/importar", response_class=HTMLResponse)
async def mostrar_formulario_importar(request: Request):
    return templates.TemplateResponse("importar.html", {"request": request})

# Importar datos desde Excel
@app.post("/importar")
async def importar_datos(file: UploadFile = File(...)):
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    content = await file.read()
    df = pd.read_excel(io.BytesIO(content), engine='openpyxl')

    required_columns = [
        'numero_sobre', 'numero_pedido', 'cliente', 'fecha_cancelacion',
        'tienda', 'proveedor', 'modelo', 'armazon', 'doctor',
        'monto_total', 'monto_cuenta', 'saldo', 'estado_pago'
    ]
    if not all(col in df.columns for col in required_columns):
        raise HTTPException(status_code=400, detail="Faltan columnas requeridas: " + ", ".join(required_columns))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            inserted_rows = 0
            for _, row in df.iterrows():
                numero_sobre = str(row['numero_sobre']).strip()
                if await check_numero_sobre_exists(numero_sobre):
                    continue

                numero_pedido = str(row['numero_pedido']).strip() if pd.notna(row['numero_pedido']) else "-"
                cliente = str(row['cliente']).strip() if pd.notna(row['cliente']) else "Sin nombre"
                fecha_cancelacion = row['fecha_cancelacion'] if pd.notna(row['fecha_cancelacion']) else None
                tienda = str(row['tienda']).strip() if pd.notna(row['tienda']) else "-"
                proveedor = str(row['proveedor']).strip() if pd.notna(row['proveedor']) else "-"
                modelo = str(row['modelo']).strip() if pd.notna(row['modelo']) else "-"
                armazon = str(row['armazon']).strip() if pd.notna(row['armazon']) else "-"
                doctor = str(row['doctor']).strip() if pd.notna(row['doctor']) else "-"
                monto_total = float(row['monto_total']) if pd.notna(row['monto_total']) else 0.0
                monto_cuenta = float(row['monto_cuenta']) if pd.notna(row['monto_cuenta']) else 0.0
                saldo = float(row['saldo']) if pd.notna(row['saldo']) else 0.0
                estado_pago = str(row['estado_pago']).strip() if pd.notna(row['estado_pago']) else "CANCELADO"

                query = """
                    INSERT INTO sobres (
                        numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda,
                        proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
                        saldo, estado_pago
                    ) VALUES (%s, %s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    numero_sobre, numero_pedido, cliente, fecha_cancelacion, tienda,
                    proveedor, modelo, armazon, doctor, monto_total, monto_cuenta,
                    saldo, estado_pago
                )
                cursor.execute(query, values)
                inserted_rows += 1

            conn.commit()
            return JSONResponse(status_code=200, content={"message": f"{inserted_rows} registros importados."})
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al importar datos: {str(e)}")
    finally:
        conn.close()

# Mostrar página de estadísticas
@app.get("/estadisticas", response_class=HTMLResponse)
async def mostrar_estadisticas(request: Request):
    return templates.TemplateResponse("estadisticas.html", {"request": request})

# Obtener estadísticas
@app.get("/api/estadisticas", response_class=JSONResponse)
async def obtener_estadisticas():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) as total_sobres FROM sobres")
            total_sobres = cursor.fetchone()["total_sobres"]

            cursor.execute("SELECT COALESCE(SUM(monto_total), 0) as monto_total_acumulado FROM sobres")
            monto_total_acumulado = float(cursor.fetchone()["monto_total_acumulado"])

            cursor.execute("SELECT COALESCE(SUM(monto_cuenta), 0) as monto_cuenta_acumulado FROM sobres")
            monto_cuenta_acumulado = float(cursor.fetchone()["monto_cuenta_acumulado"])

            cursor.execute("SELECT COALESCE(SUM(saldo), 0) as saldo_acumulado FROM sobres")
            saldo_acumulado = float(cursor.fetchone()["saldo_acumulado"])

            cursor.execute("SELECT estado_pago, COUNT(*) as cantidad FROM sobres GROUP BY estado_pago")
            estado_pago_stats = {row["estado_pago"]: row["cantidad"] for row in cursor.fetchall()}

            cursor.execute("SELECT tienda, COUNT(*) as cantidad FROM sobres GROUP BY tienda")
            tienda_stats = {row["tienda"]: row["cantidad"] for row in cursor.fetchall()}

            cursor.execute("SELECT proveedor, COUNT(*) as cantidad FROM sobres GROUP BY proveedor")
            proveedor_stats = {row["proveedor"]: row["cantidad"] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT TO_CHAR(fecha_cancelacion, 'YYYY-MM') as mes, COUNT(*) as cantidad 
                FROM sobres 
                WHERE fecha_cancelacion IS NOT NULL 
                GROUP BY mes 
                ORDER BY mes
            """)
            evolucion_stats = [{"mes": row["mes"], "cantidad": row["cantidad"]} for row in cursor.fetchall()]

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
        conn.close()

# Autocompletado genérico
async def get_autocomplete_options(table: str, query: Optional[str] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            if query:
                cursor.execute(f"SELECT nombre FROM {table} WHERE nombre ILIKE %s ORDER BY nombre", (f"%{query}%",))
            else:
                cursor.execute(f"SELECT nombre FROM {table} ORDER BY nombre")
            return [row["nombre"] for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos de {table}: {str(e)}")
    finally:
        conn.close()

# Endpoints de autocompletado
@app.get("/api/doctores", response_class=JSONResponse)
async def obtener_doctores(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("doctores", query)

@app.get("/api/tiendas", response_class=JSONResponse)
async def obtener_tiendas(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("tiendas", query)

@app.get("/api/proveedores", response_class=JSONResponse)
async def obtener_proveedores(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("proveedores", query)

@app.get("/api/estados_pago", response_class=JSONResponse)
async def obtener_estados_pago(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("estados_pago", query)

########################################################################################################################################
# RUTAS PARA MANEJAR LAS RECETAS
########################################################################################################################################

# Verificar si el número de receta ya existe
async def check_numero_receta_exists(numero_receta: str, exclude_id: Optional[int] = None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query = "SELECT EXISTS(SELECT 1 FROM recetas WHERE numero_receta = %s"
            if exclude_id:
                query += " AND id != %s"
            query += ")"
            params = [numero_receta] if not exclude_id else [numero_receta, exclude_id]
            cursor.execute(query, params)
            return cursor.fetchone()["exists"]
    finally:
        conn.close()

# Formulario de recetas
@app.get("/recetas", response_class=HTMLResponse)
async def read_recetas_form(request: Request):
    return templates.TemplateResponse("receta_form.html", {"request": request})

# Registrar una receta
@app.post("/registrar_receta")
async def registrar_receta(
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
    if await check_numero_receta_exists(numero_receta):
        raise HTTPException(status_code=400, detail="El número de receta ya existe.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO recetas (
                    numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion,
                    fecha_receta, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od,
                    cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi,
                    esf_cerca_od, cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi,
                    eje_cerca_oi, dip_lejos, dip_cerca, dip_od, dip_oi, base_lente,
                    material_cristal_01, material_cristal_02, proveedor_optica, armador_optica,
                    altura_lente, armazon_lente, numero_sobre, fecha_entrega, numero_pedido
                ) VALUES (%s, %s, %s, %s, %s, %s::date, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s::date, %s)
            """
            values = (
                numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion,
                fecha_receta or None, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od,
                cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi,
                esf_cerca_od, cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi,
                eje_cerca_oi, dip_lejos, dip_cerca, dip_od, dip_oi, base_lente,
                material_cristal_01, material_cristal_02, proveedor_optica, armador_optica,
                altura_lente, armazon_lente, numero_sobre, fecha_entrega or None, numero_pedido
            )
            cursor.execute(query, values)
            conn.commit()
            return JSONResponse(status_code=200, content={"message": "Receta registrada exitosamente"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar receta: {str(e)}")
    finally:
        conn.close()

# Endpoints de autocompletado para recetas
@app.get("/api/armazones", response_class=JSONResponse)
async def obtener_armazones(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("armazones", query)

@app.get("/api/procedencias", response_class=JSONResponse)
async def obtener_procedencias(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("procedencias", query)

@app.get("/api/armadores", response_class=JSONResponse)
async def obtener_armadores(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("armadores", query)

@app.get("/api/cristales", response_class=JSONResponse)
async def obtener_cristales(query: Optional[str] = Query(None)):
    return await get_autocomplete_options("cristales", query)

# Rutas para registros de recetas (implementadas anteriormente)
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
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query_base = """
                SELECT id, numero_receta, nombres_cliente, apellido_paterno, apellido_materno,
                       fecha_receta::text, tienda_optica, numero_sobre, fecha_entrega::text,
                       numero_pedido
                FROM recetas
                WHERE 1=1
            """
            query_count = "SELECT COUNT(*) as total FROM recetas WHERE 1=1"
            params = []

            if nombres_cliente:
                query_base += " AND nombres_cliente ILIKE %s"
                query_count += " AND nombres_cliente ILIKE %s"
                params.append(f"%{nombres_cliente}%")
            if apellido_paterno:
                query_base += " AND apellido_paterno ILIKE %s"
                query_count += " AND apellido_paterno ILIKE %s"
                params.append(f"%{apellido_paterno}%")
            if apellido_materno:
                query_base += " AND apellido_materno ILIKE %s"
                query_count += " AND apellido_materno ILIKE %s"
                params.append(f"%{apellido_materno}%")
            if fecha_entrega_desde:
                query_base += " AND fecha_entrega >= %s::date"
                query_count += " AND fecha_entrega >= %s::date"
                params.append(fecha_entrega_desde)
            if fecha_entrega_hasta:
                query_base += " AND fecha_entrega <= %s::date"
                query_count += " AND fecha_entrega <= %s::date"
                params.append(fecha_entrega_hasta)

            cursor.execute(query_count, params)
            total_records = cursor.fetchone()["total"]
            total_pages = (total_records + per_page - 1) // per_page
            page = max(1, min(page, total_pages or 1))
            offset = (page - 1) * per_page

            query = f"{query_base} ORDER BY fecha_receta DESC LIMIT %s OFFSET %s"
            cursor.execute(query, params + [per_page, offset])
            recetas = [dict(row) for row in cursor.fetchall()]

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
        conn.close()

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
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            query_base = """
                SELECT id, numero_receta, nombres_cliente, apellido_paterno, apellido_materno,
                       fecha_receta::text, tienda_optica, numero_sobre, fecha_entrega::text,
                       numero_pedido
                FROM recetas
                WHERE 1=1
            """
            query_count = "SELECT COUNT(*) as total FROM recetas WHERE 1=1"
            params = []

            if nombres_cliente:
                query_base += " AND nombres_cliente ILIKE %s"
                query_count += " AND nombres_cliente ILIKE %s"
                params.append(f"%{nombres_cliente}%")
            if apellido_paterno:
                query_base += " AND apellido_paterno ILIKE %s"
                query_count += " AND apellido_paterno ILIKE %s"
                params.append(f"%{apellido_paterno}%")
            if apellido_materno:
                query_base += " AND apellido_materno ILIKE %s"
                query_count += " AND apellido_materno ILIKE %s"
                params.append(f"%{apellido_materno}%")
            if fecha_entrega_desde:
                query_base += " AND fecha_entrega >= %s::date"
                query_count += " AND fecha_entrega >= %s::date"
                params.append(fecha_entrega_desde)
            if fecha_entrega_hasta:
                query_base += " AND fecha_entrega <= %s::date"
                query_count += " AND fecha_entrega <= %s::date"
                params.append(fecha_entrega_hasta)

            cursor.execute(query_count, params)
            total_records = cursor.fetchone()["total"]
            total_pages = (total_records + per_page - 1) // per_page
            page = max(1, min(page, total_pages or 1))
            offset = (page - 1) * per_page

            query = f"{query_base} ORDER BY fecha_receta DESC LIMIT %s OFFSET %s"
            cursor.execute(query, params + [per_page, offset])
            recetas = [dict(row) for row in cursor.fetchall()]

            return {
                "recetas": recetas,
                "current_page": page,
                "total_pages": total_pages,
                "total_records": total_records
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")
    finally:
        conn.close()

@app.get("/editar-receta/{receta_id}", response_class=HTMLResponse)
async def edit_receta_form(request: Request, receta_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * FROM recetas WHERE id = %s", (receta_id,))
            receta = cursor.fetchone()
            if not receta:
                raise HTTPException(status_code=404, detail="Receta no encontrada")
            return templates.TemplateResponse("editar_receta.html", {"request": request, "receta": dict(receta)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener receta: {str(e)}")
    finally:
        conn.close()

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
        raise HTTPException(status_code=400, detail="El número de receta ya existe.")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                UPDATE recetas SET 
                    numero_receta = %s, nombres_cliente = %s, apellido_paterno = %s, apellido_materno = %s,
                    telefono_direccion = %s, fecha_receta = %s::date, doctor_receta = %s, tienda_optica = %s,
                    procedencia_cliente = %s, esf_lejos_od = %s, cil_lejos_od = %s, eje_lejos_od = %s,
                    esf_lejos_oi = %s, cil_lejos_oi = %s, eje_lejos_oi = %s, esf_cerca_od = %s,
                    cil_cerca_od = %s, eje_cerca_od = %s, esf_cerca_oi = %s, cil_cerca_oi = %s,
                    eje_cerca_oi = %s, dip_lejos = %s, dip_cerca = %s, dip_od = %s, dip_oi = %s,
                    base_lente = %s, material_cristal_01 = %s, material_cristal_02 = %s,
                    proveedor_optica = %s, armador_optica = %s, altura_lente = %s, armazon_lente = %s,
                    numero_sobre = %s, fecha_entrega = %s::date, numero_pedido = %s
                WHERE id = %s
            """
            values = (
                numero_receta, nombres_cliente, apellido_paterno, apellido_materno, telefono_direccion,
                fecha_receta or None, doctor_receta, tienda_optica, procedencia_cliente, esf_lejos_od,
                cil_lejos_od, eje_lejos_od, esf_lejos_oi, cil_lejos_oi, eje_lejos_oi,
                esf_cerca_od, cil_cerca_od, eje_cerca_od, esf_cerca_oi, cil_cerca_oi,
                eje_cerca_oi, dip_lejos, dip_cerca, dip_od, dip_oi, base_lente,
                material_cristal_01, material_cristal_02, proveedor_optica, armador_optica,
                altura_lente, armazon_lente, numero_sobre, fecha_entrega or None, numero_pedido,
                receta_id
            )
            cursor.execute(query, values)
            conn.commit()
            return RedirectResponse(url="/registros-recetas", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar receta: {str(e)}")
    finally:
        conn.close()

@app.post("/eliminar-receta/{receta_id}")
async def eliminar_receta(receta_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM recetas WHERE id = %s", (receta_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Receta no encontrada")
            conn.commit()
            return RedirectResponse(url="/registros-recetas", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar receta: {str(e)}")
    finally:
        conn.close()