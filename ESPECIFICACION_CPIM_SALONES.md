# CPIM Salones — Especificación del proyecto

App web pública + área privada para gestión de disponibilidad, reservas y agenda institucional de los espacios del Consejo Profesional de Ingeniería de Misiones (CPIM).

Documento para pasarle a Claude Code / Antigravity como brief inicial y construir una primera versión lista para desplegar en Railway.

---

## 1. Qué resuelve

Actualmente las consultas y reservas de los salones del CPIM se manejan principalmente por WhatsApp y se registran en un calendario físico. Esto genera problemas repetitivos:

1. Las personas consultan constantemente si una fecha está disponible.
2. Se repiten preguntas sobre capacidad, características y equipamiento de cada salón.
3. Las reservas escritas y tachadas manualmente son difíciles de consultar y actualizar.
4. Administración necesita saber quién reservó, en qué horario, si abonó y cualquier observación asociada.
5. La Comisión Directiva también tiene reuniones, capacitaciones y eventos institucionales que deben quedar agendados.
6. No existe una vista única que permita detectar rápidamente ocupaciones y evitar superposiciones.

La aplicación reemplaza el calendario físico como **fuente de verdad** de la agenda de los espacios.

La idea central es tener dos experiencias claramente separadas:

- **Área pública:** cualquier visitante puede consultar los espacios, sus características y su disponibilidad sin iniciar sesión.
- **Área privada:** Administración y Comisión Directiva acceden con usuario y contraseña y ven información completa, gestionan reservas y cargan agenda institucional.

La app se enlazará desde la web oficial del CPIM.

**Importante:** en la versión 1 el visitante NO realiza una reserva automática. Consulta disponibilidad y se comunica con el CPIM por WhatsApp. La reserva se confirma y carga desde Administración.

---

## 2. Los tres espacios

Los espacios iniciales son:

### 2.1 Aula Ing. Arijón

- Capacidad aproximada: **30 personas**.
- Uso principal: charlas, clases, capacitaciones y reuniones.
- Descripción pública inicial: "Un espacio funcional para charlas, clases, capacitaciones y reuniones de grupos reducidos."
- Equipamiento: configurable desde Administración.
- Fotografías: soportadas y editables desde Administración.

### 2.2 Salón Cacique Andresito

- Capacidad aproximada: **70 personas**.
- Uso principal: charlas, conversatorios, exposiciones y reuniones en general.
- Descripción pública inicial: "Un espacio versátil para charlas, conversatorios, exposiciones, capacitaciones y reuniones."
- Equipamiento: configurable desde Administración.
- Fotografías: soportadas y editables desde Administración.

### 2.3 Salón de Eventos CPIM

- Capacidad aproximada: **100 personas**.
- Uso principal: eventos festivos, celebraciones y encuentros.
- Descripción pública inicial: "Un espacio amplio destinado a eventos, celebraciones y encuentros."
- Equipamiento: configurable desde Administración.
- Fotografías: soportadas y editables desde Administración.

Estos datos se cargan mediante `seed.py`, pero después son editables. No hardcodear capacidades, descripciones ni equipamiento en templates.

---

## 3. Regla central: disponibilidad por fecha Y horario

Una reserva no bloquea necesariamente un día completo.

Ejemplo:

- Reserva A: 18/09/2026 de 08:00 a 12:00
- El mismo salón puede seguir disponible de 12:00 en adelante.
- Otra reserva de 10:00 a 14:00 NO puede guardarse porque se superpone.

La regla de solapamiento para un mismo salón es:

```text
nuevo_inicio < existente_fin AND nuevo_fin > existente_inicio
```

Solo se consideran bloqueantes los registros activos que ocupan el salón.

Estados de reserva:

```text
RESERVADO
CANCELADO
```

Estados de pago:

```text
PENDIENTE
PAGADO
```

**Reserva y pago son conceptos separados.**

Una reserva puede ser:

```text
estado_reserva = RESERVADO
estado_pago    = PENDIENTE
```

y luego pasar únicamente a:

```text
estado_pago = PAGADO
```

sin cambiar el estado de la reserva.

Una reserva `CANCELADO` deja de bloquear el horario, pero NO se elimina de la base. Debe conservarse como historial.

La validación de superposición se hace **siempre en el servidor y dentro de la misma transacción que crea o modifica la reserva**. Nunca confiar solamente en JavaScript.

---

## 4. Qué ve cada tipo de usuario

### 4.1 Público

No necesita cuenta.

Puede:

- Ver los tres salones.
- Ver fotografías.
- Ver capacidad.
- Ver descripción.
- Ver equipamiento y servicios.
- Consultar calendario.
- Elegir un salón.
- Elegir un día.
- Ver franjas ocupadas/disponibles.
- Usar un botón de WhatsApp para consultar/reservar.
- Ver teléfono, dirección y datos públicos configurados por el CPIM.

El público **NUNCA** recibe desde backend:

- Nombre de quien reservó.
- Teléfono del cliente.
- Correo.
- Importe.
- Estado de pago.
- Observaciones internas.
- Usuario que creó/modificó la reserva.
- Detalles privados de reuniones de Comisión Directiva.

Para el visitante, un horario bloqueado se muestra simplemente como:

```text
NO DISPONIBLE
```

No enviar datos privados y luego ocultarlos con CSS. La consulta SQL/template público debe trabajar con una representación sanitizada.

### 4.2 ADMINISTRACION

Puede:

- Ver información completa del calendario.
- Crear reservas.
- Editar reservas.
- Cancelar reservas.
- Marcar pagos.
- Registrar importe.
- Ver datos de contacto.
- Agregar observaciones.
- Crear eventos institucionales.
- Editar salones.
- Editar equipamiento.
- Editar datos de contacto públicos.
- Administrar fotografías.
- Consultar historial de cambios.
- Exportar reservas.
- Ver panel/resumen.
- Cambiar su propia contraseña.

### 4.3 COMISION_DIRECTIVA

Puede:

- Acceder al calendario privado.
- Ver información completa de ocupación.
- Crear, editar y cancelar eventos/reuniones institucionales.
- Consultar reservas y sus datos administrativos.
- Consultar agenda próxima.
- Cambiar su propia contraseña.

En V1, Comisión Directiva **no modifica datos económicos de reservas ni configuración general**.

Los permisos se verifican en backend en cada endpoint privado. Ocultar un botón en HTML no constituye autorización.

---

## 5. Tipos de ocupación del calendario

Hay dos tipos principales.

### RESERVA

Alquiler/uso del salón solicitado por un tercero.

Incluye:

- salón
- fecha
- hora inicio
- hora fin
- nombre/responsable
- teléfono
- email opcional
- tipo o motivo del evento
- cantidad estimada de asistentes
- estado de reserva
- estado de pago
- importe
- observaciones internas
- usuario creador
- fecha de creación/modificación

### INSTITUCIONAL

Actividad propia del CPIM:

- reunión de Comisión Directiva
- plenaria
- capacitación
- conversatorio
- acto
- reunión interna
- actividad institucional
- otro

Puede ocupar un salón y por lo tanto bloquearlo.

También puede existir una actividad institucional **sin salón asignado**, únicamente para usar el sistema como agenda de compromisos.

Debe admitir eventos recurrentes:

```text
UNA_VEZ
SEMANAL
MENSUAL
```

En V1, las recurrencias se generan como ocurrencias individuales hasta una `fecha_fin_recurrencia`. Eso simplifica el calendario, permite editar/cancelar una fecha concreta y evita cálculos complejos en cada request.

Al crear una serie recurrente, validar conflictos para **todas** las ocurrencias antes de insertar. Si alguna colisiona, no crear la serie y mostrar las fechas conflictivas.

---

## 6. Stack

Mantener una arquitectura liviana, mantenible y fácil de desplegar.

| Capa | Elección | Motivo |
|---|---|---|
| Backend | **Python + FastAPI** | Simple, rápido y adecuado para Railway |
| Vistas | **Jinja2** | HTML server-side, SEO y carga rápida |
| Interacción | **HTMX** | Filtros, formularios y parciales sin SPA |
| JS | **Vanilla JS mínimo** | Solo calendario e interacciones que realmente lo necesiten |
| CSS | **CSS propio** | Identidad CPIM, sin aspecto de dashboard genérico |
| Base | **PostgreSQL** | Persistencia y servicio nativo en Railway |
| Driver | **psycopg 3** (`psycopg[binary,pool]`) | SQL directo y pool liviano |
| Auth | **Sesión con cookie firmada + password hashing** | Área privada real |
| Password | **pwdlib[argon2]** | No guardar contraseñas en texto plano |
| Deploy | **Railway + Procfile** | Flujo actual del CPIM |

No usar:

- React
- Next.js
- Vue
- Tailwind
- Bootstrap
- Node
- bundlers
- ORM
- frameworks visuales de dashboard
- librerías de íconos pesadas

Se permiten SVG inline propios.

La app pública debe cargar rápido y conservar HTML semántico.

---

## 7. Sistema visual CPIM

La interfaz debe sentirse como una extensión profesional del sitio del Consejo, no como un software separado o una plantilla administrativa.

Referencia visual institucional:

`https://cpim.org.ar/elementor-8037/`

Tomar de esa referencia:

- predominio del azul institucional
- fondos claros
- bloques bien separados
- títulos fuertes
- jerarquía visual limpia
- información presentada en tarjetas
- llamados a la acción claros
- estética institucional contemporánea

### 7.1 Principios

La palabra guía es:

**PROFESIONAL · MINIMALISTA · INSTITUCIONAL**

No usar:

- gradientes decorativos
- glassmorphism
- neón
- sombras exageradas
- fondos recargados
- emojis como iconografía principal
- exceso de badges
- colores sin significado
- bordes negros pesados
- estética "SaaS genérico"
- estética "panel de administrador comprado"

Priorizar:

- blanco
- azul CPIM
- azul oscuro
- grises neutros
- mucho espacio negativo
- bordes sutiles
- jerarquía tipográfica
- íconos SVG lineales
- estados cromáticos solo cuando comunican algo

### 7.2 Variables CSS

Centralizar todo en `:root`.

Valores iniciales orientativos:

```css
:root {
    --cpim-primary: #0b4f8a;
    --cpim-primary-dark: #07375f;
    --cpim-primary-soft: #edf5fb;

    --bg: #f7f9fb;
    --surface: #ffffff;
    --surface-secondary: #f2f5f7;

    --text: #17212b;
    --text-secondary: #637180;
    --border: #dfe5ea;

    --success: #23855b;
    --success-soft: #eaf6f0;
    --warning: #a96d12;
    --warning-soft: #fff5df;
    --danger: #b84444;
    --danger-soft: #fbecec;

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 18px;

    --shadow-sm: 0 1px 3px rgba(20, 38, 55, .08);
}
```

**No asumir que el HEX orientativo es exacto.** Antes de cerrar el diseño, dejar `--cpim-primary` y derivados centralizados para poder reemplazarlos en segundos por el valor institucional definitivo.

No repetir colores hardcodeados por todo el CSS.

### 7.3 Tipografía

Preferir:

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

Si Inter requiere una descarga externa que perjudique rendimiento/privacidad, usar `system-ui`.

Jerarquía:

- Hero desktop: 40–48 px.
- H1 interno: 30–36 px.
- H2: 24–28 px.
- H3: 18–21 px.
- Texto: 16 px.
- Texto auxiliar: 14 px.
- No usar textos funcionales menores a 13 px.

### 7.4 Tarjetas

Cards blancas sobre fondo general muy claro.

```text
border: 1px solid var(--border)
border-radius: var(--radius-lg)
box-shadow: var(--shadow-sm)
```

La sombra debe ser casi imperceptible.

Hover desktop: borde ligeramente más azul o elevación mínima.

### 7.5 Botones

Primario:

- fondo azul CPIM
- texto blanco
- sin gradiente
- altura mínima 44 px
- radius 8–10 px

Secundario:

- fondo blanco
- borde gris/azul
- texto azul

Destructivo:

- rojo solo para cancelar/eliminar acciones
- pedir confirmación

### 7.6 Estados

Los colores tienen semántica:

| Estado | Uso |
|---|---|
| Azul CPIM | acción principal / reservado |
| Verde | pagado / disponible |
| Ámbar | pago pendiente |
| Rojo | conflicto / error |
| Gris | cancelado / deshabilitado |
| Azul oscuro o violeta sobrio | institucional |

En el calendario público evitar un "arcoíris". Mostrar principalmente disponible/no disponible.

---

## 8. Modelo de datos

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,
    email           TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    rol             TEXT NOT NULL CHECK (rol IN ('ADMINISTRACION', 'COMISION_DIRECTIVA')),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultimo_acceso   TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email_lower
ON usuarios (LOWER(email));


CREATE TABLE IF NOT EXISTS salones (
    id              SERIAL PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    nombre          TEXT NOT NULL,
    descripcion     TEXT NOT NULL DEFAULT '',
    capacidad       INTEGER NOT NULL CHECK (capacidad > 0),
    usos            TEXT NOT NULL DEFAULT '',
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    orden           INTEGER NOT NULL DEFAULT 0,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS equipamiento (
    id              SERIAL PRIMARY KEY,
    salon_id        INTEGER NOT NULL REFERENCES salones(id) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,
    descripcion     TEXT NOT NULL DEFAULT '',
    cantidad        INTEGER,
    disponible      BOOLEAN NOT NULL DEFAULT TRUE,
    orden           INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_equipamiento_salon
ON equipamiento(salon_id);


CREATE TABLE IF NOT EXISTS salon_fotos (
    id              SERIAL PRIMARY KEY,
    salon_id        INTEGER NOT NULL REFERENCES salones(id) ON DELETE CASCADE,
    archivo         TEXT NOT NULL,
    alt_text        TEXT NOT NULL DEFAULT '',
    es_portada      BOOLEAN NOT NULL DEFAULT FALSE,
    orden           INTEGER NOT NULL DEFAULT 0,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fotos_salon
ON salon_fotos(salon_id);


CREATE TABLE IF NOT EXISTS reservas (
    id                  SERIAL PRIMARY KEY,
    salon_id            INTEGER NOT NULL REFERENCES salones(id),
    fecha               DATE NOT NULL,
    hora_inicio         TIME NOT NULL,
    hora_fin            TIME NOT NULL,

    responsable         TEXT NOT NULL,
    telefono            TEXT NOT NULL DEFAULT '',
    email               TEXT NOT NULL DEFAULT '',
    motivo              TEXT NOT NULL DEFAULT '',
    asistentes          INTEGER,

    estado_reserva      TEXT NOT NULL DEFAULT 'RESERVADO'
                        CHECK (estado_reserva IN ('RESERVADO', 'CANCELADO')),

    estado_pago         TEXT NOT NULL DEFAULT 'PENDIENTE'
                        CHECK (estado_pago IN ('PENDIENTE', 'PAGADO')),

    importe             NUMERIC(12,2) NOT NULL DEFAULT 0,
    observaciones       TEXT NOT NULL DEFAULT '',

    creado_por          INTEGER REFERENCES usuarios(id),
    actualizado_por     INTEGER REFERENCES usuarios(id),

    creado_en           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (hora_fin > hora_inicio),
    CHECK (asistentes IS NULL OR asistentes > 0),
    CHECK (importe >= 0)
);

CREATE INDEX IF NOT EXISTS idx_reservas_salon_fecha
ON reservas(salon_id, fecha);

CREATE INDEX IF NOT EXISTS idx_reservas_fecha
ON reservas(fecha);


CREATE TABLE IF NOT EXISTS eventos_institucionales (
    id                      SERIAL PRIMARY KEY,
    serie_id                UUID,
    salon_id                INTEGER REFERENCES salones(id),

    titulo                  TEXT NOT NULL,
    descripcion             TEXT NOT NULL DEFAULT '',
    tipo                    TEXT NOT NULL DEFAULT 'OTRO'
                            CHECK (tipo IN (
                                'REUNION_COMISION',
                                'PLENARIA',
                                'CAPACITACION',
                                'CONVERSATORIO',
                                'ACTO',
                                'REUNION_INTERNA',
                                'OTRO'
                            )),

    fecha                   DATE NOT NULL,
    hora_inicio             TIME,
    hora_fin                TIME,

    recurrencia             TEXT NOT NULL DEFAULT 'UNA_VEZ'
                            CHECK (recurrencia IN ('UNA_VEZ', 'SEMANAL', 'MENSUAL')),

    fecha_fin_recurrencia   DATE,
    cancelado               BOOLEAN NOT NULL DEFAULT FALSE,
    observaciones           TEXT NOT NULL DEFAULT '',

    creado_por              INTEGER REFERENCES usuarios(id),
    actualizado_por         INTEGER REFERENCES usuarios(id),

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        (hora_inicio IS NULL AND hora_fin IS NULL)
        OR
        (hora_inicio IS NOT NULL AND hora_fin IS NOT NULL AND hora_fin > hora_inicio)
    )
);

CREATE INDEX IF NOT EXISTS idx_eventos_fecha
ON eventos_institucionales(fecha);

CREATE INDEX IF NOT EXISTS idx_eventos_salon_fecha
ON eventos_institucionales(salon_id, fecha);

CREATE INDEX IF NOT EXISTS idx_eventos_serie
ON eventos_institucionales(serie_id);


CREATE TABLE IF NOT EXISTS auditoria (
    id              BIGSERIAL PRIMARY KEY,
    usuario_id      INTEGER REFERENCES usuarios(id),
    entidad         TEXT NOT NULL,
    entidad_id      INTEGER,
    accion          TEXT NOT NULL,
    detalle         JSONB NOT NULL DEFAULT '{}'::jsonb,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auditoria_entidad
ON auditoria(entidad, entidad_id);

CREATE INDEX IF NOT EXISTS idx_auditoria_fecha
ON auditoria(creado_en);


CREATE TABLE IF NOT EXISTS ajustes (
    clave           TEXT PRIMARY KEY,
    valor           TEXT NOT NULL
);
```

Ajustes iniciales:

```text
nombre_institucion=Consejo Profesional de Ingeniería de Misiones
whatsapp=5493765176817
telefono=+54 (0376) 4425355
email=infocpaim@gmail.com
direccion=Av. Francisco de Haro 2745 · Planta Baja · Posadas, Misiones
hora_publica_desde=07:00
hora_publica_hasta=23:00
intervalo_calendario_minutos=30
```

El teléfono/WhatsApp, email y dirección son configurables. No dispersarlos hardcodeados en templates.

---

## 9. Integridad y conflictos

La función central de negocio es:

```python
verificar_disponibilidad(
    salon_id,
    fecha,
    hora_inicio,
    hora_fin,
    excluir_reserva_id=None,
    excluir_evento_id=None
)
```

Debe comprobar:

1. Reservas `RESERVADO` del mismo salón y fecha.
2. Eventos institucionales no cancelados del mismo salón y fecha.
3. Superposición horaria.

Una actividad institucional sin salón no bloquea ningún espacio.

Si un evento institucional con salón no tiene horario, se interpreta como **bloqueo de día completo**.

Una reserva siempre requiere inicio y fin.

Al editar, excluir el propio registro de la búsqueda de conflictos.

### 9.1 Protección contra doble reserva concurrente

No alcanza con hacer:

```text
SELECT disponibilidad
INSERT reserva
```

sin protección, porque dos requests simultáneos podrían ver disponibilidad y reservar a la vez.

La creación/edición debe ejecutarse dentro de una transacción y adquirir un bloqueo transaccional por `salon_id + fecha` antes de comprobar conflictos e insertar/actualizar.

Usar, por ejemplo, un `pg_advisory_xact_lock` derivado de salón + fecha, o una estrategia equivalente documentada.

**Es requisito que dos requests simultáneos no puedan generar una doble reserva.**

---

## 10. Autenticación y seguridad

El área pública no requiere login.

Rutas `/admin/*` requieren autenticación.

### Login

Campos:

- email
- contraseña

No usar PIN global.

Contraseñas:

- nunca texto plano
- hash Argon2
- mínimo 10 caracteres al crear/cambiar
- comparación mediante librería de hashing

Sesión:

- cookie firmada
- `HttpOnly`
- `Secure` en producción
- `SameSite=Lax`
- expiración configurable
- regenerar sesión al iniciar sesión

Variables:

```text
SESSION_SECRET
ADMIN_INITIAL_EMAIL
ADMIN_INITIAL_PASSWORD
```

El usuario inicial se crea solamente si no existe ningún usuario y están presentes las variables correspondientes.

No mostrar ni loguear contraseñas.

### CSRF

Todos los formularios privados que modifican datos (`POST`) deben llevar token CSRF asociado a la sesión.

HTMX debe enviar el token en sus requests de escritura.

### Autorización

Helpers:

```python
require_login()
require_role("ADMINISTRACION")
require_any_role("ADMINISTRACION", "COMISION_DIRECTIVA")
```

La autorización se hace antes de ejecutar la operación.

### Rate limiting de login

Implementar limitación básica por IP/sesión para intentos fallidos de login. No hace falta infraestructura externa en V1.

### Headers

Configurar al menos:

```text
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-Frame-Options: SAMEORIGIN
```

---

## 11. Auditoría

Registrar acciones relevantes:

```text
CREAR_RESERVA
EDITAR_RESERVA
CANCELAR_RESERVA
MARCAR_PAGO
CREAR_EVENTO
EDITAR_EVENTO
CANCELAR_EVENTO
EDITAR_SALON
EDITAR_EQUIPAMIENTO
EDITAR_AJUSTES
LOGIN
```

En `detalle JSONB` guardar únicamente datos útiles para reconstruir qué cambió.

No guardar contraseñas, hashes, cookies ni secretos.

El historial es privado.

---

## 12. Pantallas públicas

La experiencia pública debe ser muy simple.

### 12.1 Inicio (`/`)

Hero:

```text
ESPACIOS CPIM

Espacios para encuentros,
capacitación y eventos.

Conocé nuestros salones, su equipamiento
y consultá disponibilidad en tiempo real.
```

CTA principal:

```text
Consultar disponibilidad
```

Debajo: tres cards de salones.

Cada card:

- fotografía de portada
- nombre
- capacidad
- usos principales
- botón `Ver salón`
- botón secundario `Consultar disponibilidad`

No mostrar precios en V1.

### 12.2 Detalle (`/salones/{slug}`)

Orden:

1. breadcrumb discreto
2. nombre
3. descripción
4. capacidad
5. galería
6. equipamiento
7. usos recomendados
8. calendario
9. CTA WhatsApp

Equipamiento con SVG lineal/check discreto.

No convertir cada artefacto en una tarjeta gigante.

### 12.3 Disponibilidad (`/disponibilidad`)

Selector superior de salón:

```text
Aula Ing. Arijón
Salón Cacique Andresito
Salón de Eventos CPIM
```

Desktop: calendario mensual.

Mobile: calendario mensual compacto + detalle del día seleccionado debajo.

Controles:

```text
‹  Septiembre 2026  ›
```

No permitir navegación infinita hacia el pasado. Puede consultarse el mes actual y meses futuros.

### 12.4 Día seleccionado

Ejemplo:

```text
Viernes 18 de septiembre

07:00 — 12:00   DISPONIBLE
12:00 — 16:00   NO DISPONIBLE
16:00 — 23:00   DISPONIBLE
```

Las franjas libres se calculan desde:

```text
hora_publica_desde
hora_publica_hasta
```

restando los intervalos bloqueados.

Unir ocupaciones contiguas antes de calcular huecos.

Si todo el día está libre:

```text
Disponible durante toda la jornada
```

Si está totalmente ocupado:

```text
Sin disponibilidad para esta fecha
```

CTA:

```text
¿Querés consultar por este salón?

Comunicate con Administración del CPIM
por WhatsApp indicando salón, fecha y horario.

[ Consultar por WhatsApp ]
```

El mensaje se precompleta:

```text
Hola, quisiera consultar por la disponibilidad del [SALON]
para el día [FECHA], en el horario [HORARIO].
```

Si el visitante todavía no seleccionó horario, omitirlo.

---

## 13. Calendario público: privacidad y UX

API/parcial público:

```text
GET /api/public/disponibilidad?salon_id=&desde=&hasta=
```

Respuesta conceptual:

```json
[
  {
    "fecha": "2026-09-18",
    "bloqueos": [
      {"inicio": "12:00", "fin": "16:00"}
    ]
  }
]
```

Nunca:

```json
{
  "responsable": "...",
  "telefono": "...",
  "importe": "...",
  "motivo": "..."
}
```

El calendario mensual marca días:

```text
LIBRE
PARCIAL
SIN_DISPONIBILIDAD
```

Visualmente:

- LIBRE: neutro con pequeño indicador verde.
- PARCIAL: indicador azul/gris.
- SIN_DISPONIBILIDAD: fondo/indicador sobrio de no disponibilidad.
- HOY: borde azul CPIM.
- SELECCIONADO: fondo azul CPIM y texto blanco.

No llenar cada celda de texto.

---

## 14. Área privada

Desktop:

- sidebar izquierda
- header superior discreto
- contenido con ancho cómodo

Mobile:

- header compacto
- navegación inferior o menú desplegable
- acciones principales accesibles con pulgar

Navegación:

```text
Panel
Calendario
Reservas
Agenda CPIM
Salones
Historial
Configuración
```

`Salones`, `Historial` y `Configuración` pueden ocultarse a Comisión Directiva cuando no corresponda.

### 14.1 Panel (`/admin`)

No hacer un dashboard lleno de gráficos.

Mostrar información accionable:

Cards:

```text
Reservas de hoy
Próximos 7 días
Pagos pendientes
Eventos CPIM próximos
```

Debajo:

**Próximas ocupaciones**

Lista cronológica con:

- fecha
- horario
- salón
- tipo
- responsable/título
- estado
- pago si corresponde

### 14.2 Calendario (`/admin/calendario`)

Es la pantalla central privada.

Filtros:

```text
Todos
Aula Ing. Arijón
Cacique Andresito
Eventos CPIM
```

Vistas:

```text
MES
SEMANA
AGENDA
```

En V1, MES y AGENDA son obligatorias. SEMANA puede implementarse después si complica la primera entrega.

Una ocupación privada muestra:

**Reserva**

```text
14:00–17:00
Salón Cacique Andresito
Juan Pérez
Pago pendiente
```

**Institucional**

```text
20:00–21:30
Reunión Comisión Directiva
Aula Ing. Arijón
```

Click abre detalle/modal o página lateral.

### 14.3 Reservas (`/admin/reservas`)

Tabla/lista responsive.

Filtros:

- búsqueda por responsable
- salón
- desde/hasta
- estado
- pago

Columnas desktop:

```text
Fecha
Horario
Salón
Responsable
Contacto
Reserva
Pago
Importe
Acciones
```

Mobile: cards compactas.

### 14.4 Nueva reserva (`/admin/reservas/nueva`)

Formulario:

```text
Salón *
Fecha *
Hora inicio *
Hora fin *

Responsable *
Teléfono
Email
Motivo / tipo de evento
Cantidad estimada de asistentes

Estado de reserva
Estado de pago
Importe
Observaciones internas
```

Antes de guardar:

- validar datos
- validar capacidad de forma informativa si `asistentes > capacidad`
- verificar conflicto
- si hay conflicto, no guardar

Mensaje:

```text
El Salón Cacique Andresito ya está ocupado
el 18/09/2026 de 14:00 a 17:00.
```

No permitir "guardar de todas formas" en V1.

### 14.5 Detalle de reserva

Mostrar:

- información general
- contacto
- pago
- observaciones
- creado por
- última modificación
- acciones

Acciones:

```text
Editar
Marcar como pagado
Cancelar reserva
```

Si ya está pagado:

```text
PAGADO
```

No mostrar botón redundante.

Cancelar pide confirmación y conserva el registro.

### 14.6 Agenda CPIM (`/admin/agenda`)

Lista de eventos institucionales.

Filtros:

- próximos
- pasados
- tipo
- salón

Botón:

```text
+ Nuevo evento
```

Formulario:

```text
Título *
Tipo *
Descripción
Salón (opcional)
Fecha *
Hora inicio
Hora fin
Recurrencia
Fecha fin de recurrencia
Observaciones
```

Si se asigna salón, validar conflicto.

Para recurrencia semanal/mensual mostrar antes de confirmar:

```text
Se crearán 8 ocurrencias.
```

Si hay conflictos, listar fechas y no crear ninguna.

### 14.7 Salones (`/admin/salones`)

Administración solamente.

Cada salón:

- nombre
- slug
- capacidad
- descripción
- usos
- activo
- equipamiento
- fotos
- portada

No eliminar físicamente un salón que ya tenga historial. Usar `activo=false`.

### 14.8 Configuración (`/admin/configuracion`)

Administración:

- WhatsApp
- teléfono
- email
- dirección
- horario público desde/hasta
- intervalo visual
- datos institucionales básicos

No incluir secretos/variables de entorno.

### 14.9 Historial (`/admin/historial`)

Administración.

Filtros:

- usuario
- acción
- entidad
- fecha

Mostrar:

```text
31/08/2026 10:42
Administración
EDITAR_RESERVA #128
```

Detalle expandible con cambios.

---

## 15. Endpoints

```text
# Público
GET  /                                      → inicio
GET  /salones/{slug}                        → ficha pública
GET  /disponibilidad                        → calendario público
GET  /api/public/disponibilidad             → datos sanitizados del calendario
GET  /health                                → 200 OK

# Auth
GET  /admin/login                           → login
POST /admin/login                           → autenticar
POST /admin/logout                          → cerrar sesión
GET  /admin/cuenta                          → cuenta propia
POST /admin/cuenta/password                 → cambiar contraseña

# Panel
GET  /admin                                 → resumen privado

# Calendario
GET  /admin/calendario                      → calendario completo
GET  /admin/api/calendario                  → ocupaciones privadas

# Reservas
GET  /admin/reservas                        → listado/filtros
GET  /admin/reservas/nueva                  → formulario
POST /admin/reservas                        → crear
GET  /admin/reservas/{id}                   → detalle
GET  /admin/reservas/{id}/editar            → formulario edición
POST /admin/reservas/{id}                   → actualizar
POST /admin/reservas/{id}/pagar             → marcar pagado
POST /admin/reservas/{id}/cancelar          → cancelar

# Agenda institucional
GET  /admin/agenda                          → listado
GET  /admin/agenda/nuevo                    → formulario
POST /admin/agenda                          → crear una/serie
GET  /admin/agenda/{id}                     → detalle
GET  /admin/agenda/{id}/editar              → editar
POST /admin/agenda/{id}                     → actualizar ocurrencia
POST /admin/agenda/{id}/cancelar            → cancelar ocurrencia

# Salones
GET  /admin/salones                         → listado
GET  /admin/salones/{id}                    → edición
POST /admin/salones/{id}                    → actualizar
POST /admin/salones/{id}/equipamiento       → agregar equipamiento
POST /admin/equipamiento/{id}               → editar
POST /admin/equipamiento/{id}/eliminar      → quitar
POST /admin/salones/{id}/fotos              → subir foto
POST /admin/fotos/{id}/portada              → definir portada
POST /admin/fotos/{id}/eliminar             → eliminar foto

# Ajustes / auditoría / exportación
GET  /admin/configuracion                    → ajustes
POST /admin/configuracion                    → guardar
GET  /admin/historial                       → auditoría
GET  /admin/exportar/reservas.csv            → exportar
```

---

## 16. Estructura de archivos

```text
cpim_salones/
├── main.py
├── db.py
├── auth.py
├── logica.py
├── schema.sql
├── seed.py
├── templates/
│   ├── base_public.html
│   ├── public/
│   │   ├── inicio.html
│   │   ├── salon.html
│   │   └── disponibilidad.html
│   ├── base_admin.html
│   ├── auth/
│   │   └── login.html
│   └── admin/
│       ├── panel.html
│       ├── calendario.html
│       ├── reservas.html
│       ├── reserva_form.html
│       ├── reserva_detalle.html
│       ├── agenda.html
│       ├── evento_form.html
│       ├── evento_detalle.html
│       ├── salones.html
│       ├── salon_form.html
│       ├── configuracion.html
│       ├── historial.html
│       └── cuenta.html
├── templates/partials/
│   ├── calendario_publico.html
│   ├── dia_disponibilidad.html
│   ├── calendario_admin.html
│   ├── reservas_lista.html
│   └── flash.html
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── calendar.js
│   │   └── admin.js
│   ├── img/
│   │   ├── cpim-logo.svg
│   │   └── salones/
│   └── htmx.min.js
├── uploads/
│   └── .gitkeep
├── tests/
│   ├── test_disponibilidad.py
│   ├── test_conflictos.py
│   ├── test_permisos.py
│   └── test_privacidad_publica.py
├── requirements.txt
├── Procfile
├── .env.example
├── .gitignore
└── README.md
```

No dividir el backend en una arquitectura empresarial innecesaria. `main.py`, `db.py`, `auth.py` y `logica.py` alcanzan para V1.

---

## 17. Fotografías y almacenamiento

**No guardar imágenes binarias dentro de PostgreSQL.**

La tabla `salon_fotos` guarda referencia/ruta.

Para desarrollo local puede existir `uploads/`.

En Railway, el filesystem normal del contenedor es efímero. Por lo tanto:

- si las fotos se administran desde la app en producción, configurar un **Railway Volume** montado, por ejemplo, en `/app/uploads`;
- definir `UPLOAD_DIR=/app/uploads`;
- no asumir que una foto subida al filesystem del contenedor sobrevivirá un redeploy sin Volume.

Alternativa futura: almacenamiento externo compatible con S3.

Validar uploads:

- JPEG / PNG / WebP
- tamaño máximo configurable (default 5 MB)
- generar nombre UUID, nunca confiar en el nombre enviado por el usuario
- rechazar extensiones/tipos no permitidos
- `alt_text` editable

Si todavía no hay fotografías reales al construir la app, usar placeholders sobrios y dejar la carga lista. No inventar fotografías de los salones.

---

## 18. Responsive obligatorio

### Desktop

- ancho máximo público aproximado: 1200 px
- hero amplio
- cards en 3 columnas
- calendario mensual cómodo
- admin con sidebar

### Tablet

- cards 2/1
- calendario mantiene mes si entra correctamente
- sidebar puede colapsar

### Mobile

- diseño desde 360 px
- cards una columna
- formularios una columna
- calendario sin scroll horizontal de toda la página
- celdas compactas
- detalle del día debajo
- botones mínimo 44 px
- inputs mínimo 16 px
- `inputmode="tel"` para teléfono
- `inputmode="decimal"` para importe
- safe-area para iPhone

Meta:

```html
<meta name="viewport"
      content="width=device-width, initial-scale=1, viewport-fit=cover">
```

No hacer una web de escritorio simplemente "encogida".

---

## 19. Accesibilidad

Requisitos V1:

- contraste legible
- `label` real en inputs
- foco visible con teclado
- botones semánticos
- no comunicar estado solo por color
- `aria-label` en botones de mes anterior/siguiente
- imágenes con `alt`
- errores asociados al campo correspondiente
- `aria-current="date"` para hoy cuando corresponda
- modal, si se usa, con manejo correcto de foco

---

## 20. Reglas de fecha y zona horaria

Zona:

```text
America/Argentina/Buenos_Aires
```

En Python:

```python
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
ahora = datetime.now(TZ)
hoy = ahora.date()
```

No usar `date.today()` para reglas dependientes del día local.

PostgreSQL guarda timestamps con `TIMESTAMPTZ`.

Las columnas `DATE` y `TIME` de reservas representan fecha y hora civil local del evento.

---

## 21. Conexión a PostgreSQL

`db.py`:

```python
import os
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

POOL = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},
    open=False,
)
```

Abrir/cerrar el pool en `lifespan` de FastAPI.

`init_db()` ejecuta `schema.sql`.

Consultas:

```python
cur.execute(
    "SELECT * FROM reservas WHERE salon_id = %s AND fecha = %s",
    (salon_id, fecha),
)
```

**Nunca** interpolar datos del usuario con f-strings.

Para identificadores/ordenamientos dinámicos usar listas blancas, no parámetros concatenados arbitrariamente.

---

## 22. Datos iniciales (`seed.py`)

Crear idempotentemente los tres salones.

```text
aula-ing-arijon
Aula Ing. Arijón
30

salon-cacique-andresito
Salón Cacique Andresito
70

salon-eventos-cpim
Salón de Eventos CPIM
100
```

Cargar las descripciones de la sección 2.

No cargar equipamiento inventado.

Si no existe ningún usuario, el arranque/seed puede crear el administrador inicial desde:

```text
ADMIN_INITIAL_EMAIL
ADMIN_INITIAL_PASSWORD
```

Hash antes de insertar.

No escribir la contraseña en logs.

---

## 23. Datos públicos institucionales iniciales

Usar como valores iniciales configurables:

```text
Consejo Profesional de Ingeniería de Misiones
Av. Francisco de Haro 2745 · Planta Baja
Posadas, Misiones
WhatsApp: +54 9 376 517-6817
Teléfono: +54 (0376) 4425355
Email: infocpaim@gmail.com
```

El botón de WhatsApp usa:

```text
5493765176817
```

Estos valores deben vivir en `ajustes`, no repetirse manualmente en distintas vistas.

---

## 24. Exportación y backup

Ruta:

```text
GET /admin/exportar/reservas.csv
```

Columnas:

```text
id
fecha
hora_inicio
hora_fin
salon
responsable
telefono
email
motivo
asistentes
estado_reserva
estado_pago
importe
observaciones
creado_en
actualizado_en
```

Solo Administración.

UTF-8 con BOM para abrir correctamente en Excel de Windows.

La exportación no reemplaza los backups de PostgreSQL.

---

## 25. Tests obligatorios

Antes de terminar V1 escribir tests para:

### Disponibilidad

- día totalmente libre
- una reserva en el medio
- dos reservas separadas
- reservas contiguas
- día completo bloqueado
- reserva cancelada no bloquea
- evento institucional bloquea
- evento sin salón no bloquea

### Conflictos

- mismo horario
- inicio dentro de reserva
- fin dentro de reserva
- nueva reserva contiene existente
- horario termina exactamente cuando empieza otro: permitido
- horario empieza exactamente cuando termina otro: permitido
- salón diferente: permitido
- fecha diferente: permitido
- edición excluye el propio ID
- concurrencia: dos intentos simultáneos no crean doble reserva

### Privacidad

La respuesta pública jamás contiene:

```text
responsable
telefono privado de la reserva
email de reserva
importe
estado_pago
observaciones
```

### Permisos

- público no entra a `/admin`
- Comisión no modifica importe/pago
- Comisión puede crear evento institucional
- Administración puede gestionar reservas
- usuario inactivo no puede iniciar sesión

---

## 26. Manejo de errores

No mostrar traceback.

Páginas:

```text
404
403
500
```

Con estética CPIM.

Errores de formulario aparecen dentro de la misma pantalla.

Mensajes exitosos:

```text
Reserva creada correctamente.
Reserva actualizada.
Pago registrado.
Evento agregado a la agenda.
```

Usar flash messages discretos.

---

## 27. Despliegue en Railway

`Procfile`:

```text
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Variables:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
TZ=America/Argentina/Buenos_Aires
SESSION_SECRET=<cadena larga aleatoria>
ADMIN_INITIAL_EMAIL=<email inicial>
ADMIN_INITIAL_PASSWORD=<contraseña inicial>
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_MB=5
ENVIRONMENT=production
```

En Railway:

1. Crear repo GitHub.
2. Deploy from GitHub.
3. Agregar PostgreSQL al mismo proyecto.
4. Crear referencia `DATABASE_URL=${{Postgres.DATABASE_URL}}`.
5. Configurar variables.
6. Si habrá uploads administrables, agregar Railway Volume montado en `/app/uploads`.
7. Healthcheck: `/health`.
8. Generate Domain.
9. Verificar HTTPS.
10. Crear/cambiar inmediatamente la contraseña del administrador inicial.
11. Enlazar el dominio final desde la web oficial del CPIM.

El `.env` real va en `.gitignore`.

Nunca subir secretos a GitHub.

---

## 28. Criterios de aceptación de V1

La V1 está terminada cuando:

1. Un visitante puede abrir la app sin login.
2. Puede ver los tres salones y sus capacidades.
3. Puede consultar disponibilidad por salón y fecha.
4. Nunca recibe datos privados de una reserva.
5. Puede iniciar una consulta por WhatsApp con mensaje precompletado.
6. Administración puede iniciar sesión.
7. Puede crear, editar, cancelar y marcar pago de reservas.
8. El sistema impide solapamientos, incluso ante requests concurrentes.
9. Comisión Directiva puede entrar y gestionar agenda institucional.
10. Eventos institucionales con salón bloquean disponibilidad pública.
11. Se pueden crear recurrencias semanales/mensuales.
12. Administración puede editar descripción/equipamiento de salones.
13. La interfaz funciona correctamente en celular y escritorio.
14. Existe auditoría de operaciones relevantes.
15. Existe exportación CSV.
16. `/health` responde 200.
17. La aplicación funciona con PostgreSQL de Railway.
18. La identidad visual es coherente con CPIM y no parece una plantilla genérica.

---

## 29. Fuera de alcance — V1

Dejar afuera deliberadamente:

- reserva automática por parte del público
- pagos online
- Mercado Pago
- seña online
- factura automática
- integración con Google Calendar
- envío automático de WhatsApp
- emails automáticos
- notificaciones push
- códigos QR
- firma de contratos
- precios públicos
- múltiples sedes
- aplicación nativa
- drag & drop complejo del calendario
- sincronización offline
- estadísticas avanzadas
- edición masiva de series recurrentes

La V1 debe resolver muy bien:

**informar + visualizar + registrar + evitar conflictos + recordar agenda.**

---

## 30. Mejoras previstas después de V1

Diseñar sin implementarlas todavía:

- solicitud de reserva online con estado `SOLICITADA`
- aprobación/rechazo por Administración
- integración con WhatsApp Business
- comprobantes
- señas/pagos
- sincronización Google Calendar
- recordatorios de pagos pendientes
- recordatorios de eventos
- precios por salón/tipo de uso
- reportes de ocupación
- ingresos por salón
- agenda institucional con participantes
- integración futura con otros sistemas CPIM

No crear tablas ni complejidad innecesaria para estas funciones hasta que se decida implementarlas.

---

## 31. Orden de implementación

Claude Code / Antigravity debe trabajar por etapas.

### Etapa 1 — Base técnica

Crear:

```text
requirements.txt
Procfile
.env.example
.gitignore
schema.sql
db.py
```

Configurar lifespan y `/health`.

### Etapa 2 — Lógica central

Crear `logica.py`.

Implementar:

```text
hay_solapamiento()
verificar_disponibilidad()
calcular_franjas_libres()
generar_ocurrencias()
```

Escribir tests antes de seguir.

### Etapa 3 — Auth

Crear:

```text
auth.py
login
sesiones
roles
CSRF
password hashing
```

Tests de permisos.

### Etapa 4 — Seed

Crear los tres salones y administrador inicial.

### Etapa 5 — Público

Construir:

```text
inicio
salón
calendario
día seleccionado
WhatsApp
```

Aplicar sistema visual CPIM desde el inicio.

### Etapa 6 — Reservas privadas

CRUD + pago + cancelación + conflictos + auditoría.

### Etapa 7 — Agenda institucional

Eventos simples y recurrencias.

### Etapa 8 — Gestión

Salones, equipamiento, fotos, configuración, historial y CSV.

### Etapa 9 — QA

Probar:

```text
360px
390px
768px
1366px
1920px
```

Revisar privacidad, roles, conflictos, zona horaria y accesibilidad.

---

## 32. Prompt inicial para Claude Code / Antigravity

> Creá el proyecto **cpim_salones** siguiendo exactamente la especificación del archivo
> `ESPECIFICACION_CPIM_SALONES.md` que está en la raíz.
>
> Es una aplicación pública + área privada para el Consejo Profesional de Ingeniería de Misiones.
> No improvises funcionalidades ni cambies el stack sin consultarme.
>
> Stack: Python + FastAPI + Jinja2 + HTMX + Vanilla JS mínimo + PostgreSQL con psycopg 3.
> Sin React, Next, Vue, Tailwind, Bootstrap, Node, bundlers ni ORM.
>
> El diseño es parte del requisito funcional. Debe ser profesional, minimalista e institucional,
> coherente con la identidad visual del CPIM. Usá la sección "Sistema visual CPIM" como contrato de
> diseño. Evitá completamente el aspecto de dashboard genérico.
>
> La regla más importante es impedir dobles reservas. Implementá la comprobación de solapamiento
> dentro de transacciones y protegela también frente a dos requests concurrentes.
>
> La segunda regla crítica es privacidad: los endpoints/templates públicos nunca deben recibir datos
> personales, económicos ni observaciones internas de las reservas.
>
> La conexión sale de `DATABASE_URL`; nunca hardcodear credenciales. Todas las consultas SQL con
> parámetros `%s`, nunca interpolación de datos del usuario.
>
> Usá `America/Argentina/Buenos_Aires` para toda lógica de fecha/hora.
>
> Empezá en este orden:
>
> 1. Base técnica (`requirements.txt`, `Procfile`, `.env.example`, `.gitignore`, `schema.sql`, `db.py`, `/health`).
> 2. `logica.py` + tests de disponibilidad, solapamientos y concurrencia.
> 3. `auth.py` + login, roles, sesiones y CSRF + tests.
> 4. `seed.py`.
> 5. Experiencia pública completa.
> 6. Reservas privadas.
> 7. Agenda institucional y recurrencias.
> 8. Gestión de salones/equipamiento/fotos/configuración/auditoría/exportación.
> 9. QA responsive, privacidad y accesibilidad.
>
> Después de cada etapa:
>
> - ejecutá los tests;
> - mostrame qué archivos creaste o modificaste;
> - explicá brevemente las decisiones;
> - indicá cómo probar esa etapa;
> - no avances a la siguiente hasta que la etapa actual funcione.
>
> Si encontrás una ambigüedad que afecte datos, permisos, seguridad o reglas de reserva, preguntame
> antes de decidir. Para detalles menores de implementación, elegí la solución más simple y
> mantenible compatible con esta especificación.
