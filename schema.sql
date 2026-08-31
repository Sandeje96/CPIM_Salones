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
