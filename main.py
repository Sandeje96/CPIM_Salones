import os
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from db import lifespan, get_db
from psycopg import Connection
from logica import calcular_franjas_libres

app = FastAPI(lifespan=lifespan, title="CPIM Salones")

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET", "super-secret-default"),
    max_age=86400 * 7
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def inicio(request: Request, db: Connection = Depends(get_db)):
    salones = db.execute("SELECT id, slug, nombre, descripcion, capacidad FROM salones WHERE activo = TRUE ORDER BY orden").fetchall()
    return templates.TemplateResponse("public/inicio.html", {"request": request, "salones": salones})

@app.get("/salones/{slug}")
def salon_detalle(request: Request, slug: str, db: Connection = Depends(get_db)):
    salon = db.execute("SELECT * FROM salones WHERE slug = %s", (slug,)).fetchone()
    if not salon:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    equipamiento = db.execute("SELECT * FROM equipamiento WHERE salon_id = %s ORDER BY orden", (salon["id"],)).fetchall()
    return templates.TemplateResponse("public/salon.html", {"request": request, "salon": salon, "equipamiento": equipamiento})

@app.get("/disponibilidad")
def disponibilidad(request: Request, salon: int = None, db: Connection = Depends(get_db)):
    salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE ORDER BY orden").fetchall()
    ajustes = {r["clave"]: r["valor"] for r in db.execute("SELECT clave, valor FROM ajustes").fetchall()}
    return templates.TemplateResponse("public/disponibilidad.html", {
        "request": request, 
        "salones": salones,
        "salon_seleccionado": salon,
        "whatsapp": ajustes.get("whatsapp", "")
    })

@app.get("/api/public/disponibilidad")
def api_disponibilidad(
    salon_id: int, 
    desde: datetime.date, 
    hasta: datetime.date,
    db: Connection = Depends(get_db)
):
    """
    Retorna datos sanitizados del calendario. 
    Busca reservas y eventos institucionales bloqueantes y devuelve una lista de fechas con bloques ocupados.
    """
    # Buscar reservas
    reservas = db.execute("""
        SELECT fecha, hora_inicio, hora_fin 
        FROM reservas 
        WHERE salon_id = %s AND fecha >= %s AND fecha <= %s AND estado_reserva = 'RESERVADO'
    """, (salon_id, desde, hasta)).fetchall()

    # Buscar eventos
    eventos = db.execute("""
        SELECT fecha, hora_inicio, hora_fin 
        FROM eventos_institucionales 
        WHERE salon_id = %s AND fecha >= %s AND fecha <= %s AND cancelado = FALSE
    """, (salon_id, desde, hasta)).fetchall()

    dias_ocupados = {}

    def agregar_bloque(f, inicio, fin):
        if f not in dias_ocupados:
            dias_ocupados[f] = []
        if inicio is None and fin is None:
            # Dia completo
            dias_ocupados[f].append({"inicio": "00:00:00", "fin": "23:59:59"})
        else:
            dias_ocupados[f].append({"inicio": str(inicio), "fin": str(fin)})

    for r in reservas:
        agregar_bloque(r["fecha"], r["hora_inicio"], r["hora_fin"])
        
    for e in eventos:
        agregar_bloque(e["fecha"], e["hora_inicio"], e["hora_fin"])
        
    # Formatear salida
    resultado = []
    for f, bloques in dias_ocupados.items():
        resultado.append({
            "fecha": f.isoformat(),
            "bloqueos": bloques
        })
        
    return resultado

# --- RUTAS ADMIN ---

from fastapi import Form, status
from fastapi.responses import RedirectResponse
from auth import verify_password, init_session, require_login, require_any_role, verify_csrf

@app.get("/admin/login")
def login_get(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.post("/admin/login")
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Connection = Depends(get_db)):
    user = db.execute("SELECT * FROM usuarios WHERE LOWER(email) = LOWER(%s)", (email,)).fetchone()
    if not user or not user["activo"] or not verify_password(password, user["password_hash"]):
        return templates.TemplateResponse("auth/login.html", {"request": request, "error": "Credenciales inválidas"}, status_code=401)
    
    init_session(request, user["id"], user["rol"])
    db.execute("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s", (user["id"],))
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/logout")
async def logout(request: Request):
    # En V1, logout simple
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin")
def admin_panel(request: Request, db: Connection = Depends(get_db)):
    user_id = require_login(request)
    # Estadisticas basicas
    hoy = datetime.date.today()
    reservas_hoy = db.execute("SELECT COUNT(*) as c FROM reservas WHERE fecha = %s AND estado_reserva = 'RESERVADO'", (hoy,)).fetchone()["c"]
    
    # Proximas ocupaciones
    proximas = db.execute("""
        SELECT 'RESERVA' as tipo, id, fecha, hora_inicio, hora_fin, responsable as titulo, estado_pago as estado, salon_id
        FROM reservas WHERE fecha >= %s AND estado_reserva = 'RESERVADO'
        UNION ALL
        SELECT 'INSTITUCIONAL' as tipo, id, fecha, hora_inicio, hora_fin, titulo, 'N/A' as estado, salon_id
        FROM eventos_institucionales WHERE fecha >= %s AND cancelado = FALSE
        ORDER BY fecha ASC, hora_inicio ASC
        LIMIT 10
    """, (hoy, hoy)).fetchall()
    
    # Salones para nombres
    salones_map = {s["id"]: s["nombre"] for s in db.execute("SELECT id, nombre FROM salones").fetchall()}
    for p in proximas:
        p["salon"] = salones_map.get(p["salon_id"], "N/A")
        
    return templates.TemplateResponse("admin/panel.html", {
        "request": request,
        "reservas_hoy": reservas_hoy,
        "proximas": proximas
    })

@app.get("/admin/reservas")
def admin_reservas(request: Request, db: Connection = Depends(get_db)):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    reservas = db.execute("""
        SELECT r.*, s.nombre as salon_nombre 
        FROM reservas r
        JOIN salones s ON r.salon_id = s.id
        ORDER BY r.fecha DESC, r.hora_inicio DESC
    """).fetchall()
    return templates.TemplateResponse("admin/reservas.html", {"request": request, "reservas": reservas})

@app.get("/admin/reservas/nueva")
def admin_reservas_nueva(request: Request, db: Connection = Depends(get_db)):
    require_role(request, "ADMINISTRACION")
    salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
    return templates.TemplateResponse("admin/reserva_form.html", {"request": request, "salones": salones, "reserva": None})

@app.post("/admin/reservas")
async def admin_reservas_post(
    request: Request,
    salon_id: int = Form(...),
    fecha: datetime.date = Form(...),
    hora_inicio: datetime.time = Form(...),
    hora_fin: datetime.time = Form(...),
    responsable: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    motivo: str = Form(""),
    asistentes: int = Form(None),
    estado_pago: str = Form("PENDIENTE"),
    importe: float = Form(0),
    observaciones: str = Form(""),
    db: Connection = Depends(get_db)
):
    user_id = require_role(request, "ADMINISTRACION")
    await verify_csrf(request)
    
    from logica import verificar_disponibilidad
    try:
        with db.transaction():
            verificar_disponibilidad(db, salon_id, fecha, hora_inicio, hora_fin)
            
            cur = db.execute("""
                INSERT INTO reservas (salon_id, fecha, hora_inicio, hora_fin, responsable, telefono, email, motivo, asistentes, estado_reserva, estado_pago, importe, observaciones, creado_por, actualizado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'RESERVADO', %s, %s, %s, %s, %s)
                RETURNING id
            """, (salon_id, fecha, hora_inicio, hora_fin, responsable, telefono, email, motivo, asistentes, estado_pago, importe, observaciones, user_id, user_id))
            nuevo_id = cur.fetchone()["id"]
            
            db.execute("INSERT INTO auditoria (usuario_id, entidad, entidad_id, accion) VALUES (%s, 'reserva', %s, 'CREAR_RESERVA')", (user_id, nuevo_id))
            
    except ValueError as e:
        salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
        return templates.TemplateResponse("admin/reserva_form.html", {"request": request, "salones": salones, "error": str(e)}, status_code=400)
        
    return RedirectResponse(url="/admin/reservas", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/reservas/{id}/pagar")
async def admin_reservas_pagar(request: Request, id: int, db: Connection = Depends(get_db)):
    user_id = require_role(request, "ADMINISTRACION")
    await verify_csrf(request)
    db.execute("UPDATE reservas SET estado_pago = 'PAGADO', actualizado_por = %s, actualizado_en = NOW() WHERE id = %s", (user_id, id))
    db.execute("INSERT INTO auditoria (usuario_id, entidad, entidad_id, accion) VALUES (%s, 'reserva', %s, 'MARCAR_PAGO')", (user_id, id))
    return RedirectResponse(url=f"/admin/reservas", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/reservas/{id}/cancelar")
async def admin_reservas_cancelar(request: Request, id: int, db: Connection = Depends(get_db)):
    user_id = require_role(request, "ADMINISTRACION")
    await verify_csrf(request)
    db.execute("UPDATE reservas SET estado_reserva = 'CANCELADO', actualizado_por = %s, actualizado_en = NOW() WHERE id = %s", (user_id, id))
    db.execute("INSERT INTO auditoria (usuario_id, entidad, entidad_id, accion) VALUES (%s, 'reserva', %s, 'CANCELAR_RESERVA')", (user_id, id))
    return RedirectResponse(url=f"/admin/reservas", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/agenda")
def admin_agenda(request: Request, db: Connection = Depends(get_db)):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    eventos = db.execute("""
        SELECT e.*, s.nombre as salon_nombre 
        FROM eventos_institucionales e
        LEFT JOIN salones s ON e.salon_id = s.id
        ORDER BY e.fecha DESC, e.hora_inicio DESC
    """).fetchall()
    return templates.TemplateResponse("admin/agenda.html", {"request": request, "eventos": eventos})

@app.get("/admin/agenda/nuevo")
def admin_agenda_nuevo(request: Request, db: Connection = Depends(get_db)):
    require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
    return templates.TemplateResponse("admin/evento_form.html", {"request": request, "salones": salones, "evento": None})

import uuid
from dateutil.relativedelta import relativedelta

@app.post("/admin/agenda")
async def admin_agenda_post(
    request: Request,
    titulo: str = Form(...),
    tipo: str = Form("OTRO"),
    descripcion: str = Form(""),
    salon_id: int = Form(None),
    fecha: datetime.date = Form(...),
    hora_inicio: datetime.time = Form(None),
    hora_fin: datetime.time = Form(None),
    recurrencia: str = Form("UNA_VEZ"),
    fecha_fin_recurrencia: datetime.date = Form(None),
    observaciones: str = Form(""),
    db: Connection = Depends(get_db)
):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    await verify_csrf(request)
    
    if (hora_inicio and not hora_fin) or (hora_fin and not hora_inicio):
        salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
        return templates.TemplateResponse("admin/evento_form.html", {"request": request, "salones": salones, "error": "Debe especificar hora de inicio y fin, o dejar ambas vacías (día completo)."}, status_code=400)
    
    # Generar ocurrencias
    fechas = [fecha]
    if recurrencia != "UNA_VEZ" and fecha_fin_recurrencia:
        actual = fecha
        while True:
            if recurrencia == "SEMANAL":
                actual = actual + relativedelta(days=7)
            elif recurrencia == "MENSUAL":
                actual = actual + relativedelta(months=1)
            
            if actual > fecha_fin_recurrencia:
                break
            fechas.append(actual)
            
            if len(fechas) > 100: # Limite de seguridad
                break

    from logica import verificar_disponibilidad
    serie_id = str(uuid.uuid4()) if len(fechas) > 1 else None
    
    try:
        with db.transaction():
            # Validar todos primero
            if salon_id:
                for f in fechas:
                    verificar_disponibilidad(db, salon_id, f, hora_inicio, hora_fin)
            
            # Insertar
            for f in fechas:
                cur = db.execute("""
                    INSERT INTO eventos_institucionales (serie_id, salon_id, titulo, descripcion, tipo, fecha, hora_inicio, hora_fin, recurrencia, fecha_fin_recurrencia, observaciones, creado_por, actualizado_por)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (serie_id, salon_id, titulo, descripcion, tipo, f, hora_inicio, hora_fin, recurrencia, fecha_fin_recurrencia, observaciones, user_id, user_id))
                nuevo_id = cur.fetchone()["id"]
                db.execute("INSERT INTO auditoria (usuario_id, entidad, entidad_id, accion) VALUES (%s, 'evento', %s, 'CREAR_EVENTO')", (user_id, nuevo_id))
                
    except ValueError as e:
        salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
        return templates.TemplateResponse("admin/evento_form.html", {"request": request, "salones": salones, "error": f"Conflicto: {str(e)}"}, status_code=400)
        
    return RedirectResponse(url="/admin/agenda", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/agenda/{id}/cancelar")
async def admin_agenda_cancelar(request: Request, id: int, db: Connection = Depends(get_db)):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    await verify_csrf(request)
    db.execute("UPDATE eventos_institucionales SET cancelado = TRUE, actualizado_por = %s, actualizado_en = NOW() WHERE id = %s", (user_id, id))
    db.execute("INSERT INTO auditoria (usuario_id, entidad, entidad_id, accion) VALUES (%s, 'evento', %s, 'CANCELAR_EVENTO')", (user_id, id))
    return RedirectResponse(url=f"/admin/agenda", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/admin/calendario")
def admin_calendario(request: Request, db: Connection = Depends(get_db)):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    salones = db.execute("SELECT id, nombre FROM salones WHERE activo = TRUE").fetchall()
    return templates.TemplateResponse("admin/calendario.html", {"request": request, "salones": salones})

@app.get("/admin/api/calendario")
def admin_api_calendario(
    request: Request,
    salon_id: int = None,
    desde: datetime.date = Query(...),
    hasta: datetime.date = Query(...),
    db: Connection = Depends(get_db)
):
    user_id = require_any_role(request, ["ADMINISTRACION", "COMISION_DIRECTIVA"])
    
    # Construir query dinamicamente
    q_res = "SELECT 'RESERVA' as tipo, id, fecha, hora_inicio, hora_fin, responsable as titulo, estado_pago, salon_id FROM reservas WHERE fecha >= %s AND fecha <= %s AND estado_reserva = 'RESERVADO'"
    p_res = [desde, hasta]
    if salon_id:
        q_res += " AND salon_id = %s"
        p_res.append(salon_id)
        
    q_evt = "SELECT 'INSTITUCIONAL' as tipo, id, fecha, hora_inicio, hora_fin, titulo, 'N/A' as estado_pago, salon_id FROM eventos_institucionales WHERE fecha >= %s AND fecha <= %s AND cancelado = FALSE"
    p_evt = [desde, hasta]
    if salon_id:
        q_evt += " AND salon_id = %s"
        p_evt.append(salon_id)
        
    reservas = db.execute(q_res, p_res).fetchall()
    eventos = db.execute(q_evt, p_evt).fetchall()
    
    salones_map = {s["id"]: s["nombre"] for s in db.execute("SELECT id, nombre FROM salones").fetchall()}
    
    eventos_completos = []
    for o in (reservas + eventos):
        o["salon_nombre"] = salones_map.get(o["salon_id"], "Sin Salón")
        # Asegurar formato string
        o["fecha"] = o["fecha"].isoformat()
        o["hora_inicio"] = o["hora_inicio"].strftime('%H:%M') if o["hora_inicio"] else None
        o["hora_fin"] = o["hora_fin"].strftime('%H:%M') if o["hora_fin"] else None
        eventos_completos.append(o)
        
    return eventos_completos

@app.get("/admin/salones")
def admin_salones(request: Request, db: Connection = Depends(get_db)):
    require_role(request, "ADMINISTRACION")
    salones = db.execute("SELECT * FROM salones ORDER BY orden").fetchall()
    return templates.TemplateResponse("admin/salones.html", {"request": request, "salones": salones})

@app.get("/admin/historial")
def admin_historial(request: Request, db: Connection = Depends(get_db)):
    require_role(request, "ADMINISTRACION")
    logs = db.execute("""
        SELECT a.*, u.nombre as usuario_nombre 
        FROM auditoria a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.creado_en DESC LIMIT 100
    """).fetchall()
    return templates.TemplateResponse("admin/historial.html", {"request": request, "logs": logs})

@app.get("/admin/configuracion")
def admin_configuracion(request: Request, db: Connection = Depends(get_db)):
    require_role(request, "ADMINISTRACION")
    ajustes = {r["clave"]: r["valor"] for r in db.execute("SELECT clave, valor FROM ajustes").fetchall()}
    return templates.TemplateResponse("admin/configuracion.html", {"request": request, "ajustes": ajustes})

@app.post("/admin/configuracion")
async def admin_configuracion_post(request: Request, db: Connection = Depends(get_db)):
    user_id = require_role(request, "ADMINISTRACION")
    await verify_csrf(request)
    form = await request.form()
    
    # Actualizar claves (excepto csrf)
    with db.transaction():
        for k, v in form.items():
            if k != "csrf_token":
                db.execute("INSERT INTO ajustes (clave, valor) VALUES (%s, %s) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor", (k, v))
                
        db.execute("INSERT INTO auditoria (usuario_id, entidad, accion) VALUES (%s, 'ajustes', 'EDITAR_AJUSTES')", (user_id,))
    
    return RedirectResponse(url="/admin/configuracion", status_code=status.HTTP_303_SEE_OTHER)

from fastapi.responses import StreamingResponse
import csv
import io

@app.get("/admin/exportar/reservas.csv")
def exportar_reservas(request: Request, db: Connection = Depends(get_db)):
    require_role(request, "ADMINISTRACION")
    reservas = db.execute("SELECT id, fecha, hora_inicio, hora_fin, salon_id, responsable, telefono, email, motivo, asistentes, estado_reserva, estado_pago, importe, observaciones, creado_en, actualizado_en FROM reservas ORDER BY fecha DESC").fetchall()
    
    salones = {s["id"]: s["nombre"] for s in db.execute("SELECT id, nombre FROM salones").fetchall()}
    
    output = io.StringIO()
    # Escribir BOM para Excel
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['id', 'fecha', 'hora_inicio', 'hora_fin', 'salon', 'responsable', 'telefono', 'email', 'motivo', 'asistentes', 'estado_reserva', 'estado_pago', 'importe', 'observaciones', 'creado_en', 'actualizado_en'])
    
    for r in reservas:
        writer.writerow([
            r['id'], r['fecha'], r['hora_inicio'], r['hora_fin'], 
            salones.get(r['salon_id'], ''), r['responsable'], r['telefono'], 
            r['email'], r['motivo'], r['asistentes'], r['estado_reserva'], 
            r['estado_pago'], r['importe'], r['observaciones'], 
            r['creado_en'], r['actualizado_en']
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=reservas.csv"}
    )

@app.get("/admin/cuenta")
def admin_cuenta(request: Request, db: Connection = Depends(get_db)):
    user_id = require_login(request)
    user = db.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,)).fetchone()
    return templates.TemplateResponse("admin/cuenta.html", {"request": request, "user": user})

@app.post("/admin/cuenta/password")
async def admin_cuenta_password(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    db: Connection = Depends(get_db)
):
    user_id = require_login(request)
    await verify_csrf(request)
    
    user = db.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,)).fetchone()
    if not verify_password(password_actual, user["password_hash"]):
        return templates.TemplateResponse("admin/cuenta.html", {"request": request, "user": user, "error": "Contraseña actual incorrecta"}, status_code=400)
    
    db.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", (get_password_hash(password_nueva), user_id))
    return RedirectResponse(url="/admin/cuenta?success=1", status_code=status.HTTP_303_SEE_OTHER)




