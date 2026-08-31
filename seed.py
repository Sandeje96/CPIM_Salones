import os
from dotenv import load_dotenv
import psycopg
from db import pool
from auth import get_password_hash

# Datos de salones
SALONES = [
    {
        "slug": "aula-ing-arijon",
        "nombre": "Aula Ing. Arijón",
        "descripcion": "Un espacio funcional para charlas, clases, capacitaciones y reuniones de grupos reducidos.",
        "capacidad": 30,
        "orden": 10,
    },
    {
        "slug": "salon-cacique-andresito",
        "nombre": "Salón Cacique Andresito",
        "descripcion": "Un espacio versátil para charlas, conversatorios, exposiciones, capacitaciones y reuniones.",
        "capacidad": 70,
        "orden": 20,
    },
    {
        "slug": "salon-eventos-cpim",
        "nombre": "Salón de Eventos CPIM",
        "descripcion": "Un espacio amplio destinado a eventos, celebraciones y encuentros.",
        "capacidad": 100,
        "orden": 30,
    }
]

AJUSTES_INICIALES = {
    "nombre_institucion": "Consejo Profesional de Ingeniería de Misiones",
    "whatsapp": "5493765176817",
    "telefono": "+54 (0376) 4425355",
    "email": "infocpaim@gmail.com",
    "direccion": "Av. Francisco de Haro 2745 · Planta Baja · Posadas, Misiones",
    "hora_publica_desde": "07:00",
    "hora_publica_hasta": "23:00",
    "intervalo_calendario_minutos": "30"
}

def seed():
    load_dotenv()
    
    # Aseguramos que el pool esté abierto si lo usamos fuera de FastAPI
    try:
        pool.open()
    except Exception:
        pass

    with pool.connection() as conn:
        with conn.transaction():
            # 1. Crear salones si no existen
            for s in SALONES:
                conn.execute("""
                    INSERT INTO salones (slug, nombre, descripcion, capacidad, orden)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (slug) DO NOTHING
                """, (s["slug"], s["nombre"], s["descripcion"], s["capacidad"], s["orden"]))
            
            # 2. Cargar ajustes si no existen
            for k, v in AJUSTES_INICIALES.items():
                conn.execute("""
                    INSERT INTO ajustes (clave, valor)
                    VALUES (%s, %s)
                    ON CONFLICT (clave) DO NOTHING
                """, (k, v))
            
            # 3. Crear administrador inicial si la tabla usuarios está vacía
            cur = conn.execute("SELECT COUNT(*) as count FROM usuarios")
            if cur.fetchone()["count"] == 0:
                admin_email = os.environ.get("ADMIN_INITIAL_EMAIL")
                admin_pass = os.environ.get("ADMIN_INITIAL_PASSWORD")
                
                if admin_email and admin_pass:
                    h = get_password_hash(admin_pass)
                    conn.execute("""
                        INSERT INTO usuarios (nombre, email, password_hash, rol)
                        VALUES (%s, %s, %s, 'ADMINISTRACION')
                    """, ("Administrador", admin_email, h))
                    print(f"Usuario inicial creado: {admin_email}")
                else:
                    print("No se creó usuario inicial: ADMIN_INITIAL_EMAIL o ADMIN_INITIAL_PASSWORD no definidos en entorno.")
            
    print("Base de datos inicializada con éxito.")

if __name__ == "__main__":
    seed()
    pool.close()
