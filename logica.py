import datetime
from typing import List, Dict, Optional, Tuple

def calcular_franjas_libres(
    ocupaciones: List[Dict], 
    hora_desde: datetime.time, 
    hora_hasta: datetime.time
) -> List[Dict]:
    """
    Dada una lista de ocupaciones (con 'inicio' y 'fin' como datetime.time),
    y un horario de apertura y cierre, calcula los intervalos libres.
    """
    if not ocupaciones:
        return [{"inicio": hora_desde, "fin": hora_hasta}]

    # Ordenar ocupaciones por hora de inicio
    ocupaciones_ordenadas = sorted(ocupaciones, key=lambda x: x["inicio"])

    # Unir solapamientos contiguos (por si los hubiera en ocupaciones)
    ocupaciones_unidas = []
    actual = ocupaciones_ordenadas[0]
    for sig in ocupaciones_ordenadas[1:]:
        if sig["inicio"] <= actual["fin"]:
            # Solapamiento o contiguo, extendemos el fin
            actual["fin"] = max(actual["fin"], sig["fin"])
        else:
            ocupaciones_unidas.append(actual)
            actual = sig
    ocupaciones_unidas.append(actual)

    franjas_libres = []
    inicio_actual = hora_desde

    for ocu in ocupaciones_unidas:
        if inicio_actual < ocu["inicio"]:
            # Hay hueco antes de esta ocupacion
            franjas_libres.append({
                "inicio": inicio_actual,
                "fin": min(ocu["inicio"], hora_hasta)
            })
        inicio_actual = max(inicio_actual, ocu["fin"])

    if inicio_actual < hora_hasta:
        franjas_libres.append({
            "inicio": inicio_actual,
            "fin": hora_hasta
        })

    return franjas_libres


def obtener_lock(conn, salon_id: int, fecha: datetime.date):
    """
    Adquiere un bloqueo transaccional para evitar dobles reservas.
    Usa pg_advisory_xact_lock(int, int).
    El primer arg es salon_id, el segundo es YYYYMMDD.
    El bloqueo se libera automáticamente al fin de la transacción (COMMIT o ROLLBACK).
    """
    fecha_int = int(fecha.strftime("%Y%m%d"))
    conn.execute("SELECT pg_advisory_xact_lock(%s, %s)", (salon_id, fecha_int))


def hay_solapamiento(
    conn,
    salon_id: int,
    fecha: datetime.date,
    hora_inicio: datetime.time,
    hora_fin: datetime.time,
    excluir_reserva_id: Optional[int] = None,
    excluir_evento_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Comprueba si existe solapamiento para un salón, fecha y horario.
    Retorna (True, "Mensaje de conflicto") si lo hay, o (False, None) si está libre.
    """
    # 1. Chequear reservas activas ('RESERVADO')
    q_reservas = """
        SELECT id, hora_inicio, hora_fin 
        FROM reservas 
        WHERE salon_id = %s 
          AND fecha = %s 
          AND estado_reserva = 'RESERVADO'
          AND %s < hora_fin 
          AND %s > hora_inicio
    """
    params_reservas = [salon_id, fecha, hora_inicio, hora_fin]
    if excluir_reserva_id:
        q_reservas += " AND id != %s"
        params_reservas.append(excluir_reserva_id)

    reserva_colision = conn.execute(q_reservas, params_reservas).fetchone()
    if reserva_colision:
        return True, "El salón ya está reservado en ese horario."

    # 2. Chequear eventos institucionales no cancelados
    q_eventos = """
        SELECT id, hora_inicio, hora_fin, titulo 
        FROM eventos_institucionales 
        WHERE salon_id = %s 
          AND fecha = %s 
          AND cancelado = FALSE
          AND (
             (hora_inicio IS NULL AND hora_fin IS NULL) -- Día completo
             OR (%s < hora_fin AND %s > hora_inicio)
          )
    """
    params_eventos = [salon_id, fecha, hora_inicio, hora_fin]
    if excluir_evento_id:
        q_eventos += " AND id != %s"
        params_eventos.append(excluir_evento_id)
        
    evento_colision = conn.execute(q_eventos, params_eventos).fetchone()
    if evento_colision:
        if evento_colision["hora_inicio"] is None:
            return True, "El salón está bloqueado todo el día por un evento institucional."
        return True, f"El salón está ocupado por el evento '{evento_colision['titulo']}' en ese horario."

    return False, None


def verificar_disponibilidad(
    conn,
    salon_id: int,
    fecha: datetime.date,
    hora_inicio: datetime.time,
    hora_fin: datetime.time,
    excluir_reserva_id: Optional[int] = None,
    excluir_evento_id: Optional[int] = None
):
    """
    Debe ser llamada dentro de una transacción activa (with conn.transaction():)
    Bloquea el salón para esa fecha, luego verifica disponibilidad.
    Si hay conflicto, levanta una excepción.
    """
    obtener_lock(conn, salon_id, fecha)
    conflicto, mensaje = hay_solapamiento(
        conn, salon_id, fecha, hora_inicio, hora_fin, 
        excluir_reserva_id, excluir_evento_id
    )
    if conflicto:
        raise ValueError(mensaje)

