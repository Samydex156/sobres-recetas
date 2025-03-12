-- Crear tabla doctores
CREATE TABLE doctores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla tiendas
CREATE TABLE tiendas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla proveedores
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla estados_pago
CREATE TABLE estados_pago (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Crear tabla armazones
CREATE TABLE armazones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla procedencias
CREATE TABLE procedencias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla armadores
CREATE TABLE armadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla cristales
CREATE TABLE cristales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla sobres
CREATE TABLE sobres (
    id SERIAL PRIMARY KEY,
    numero_sobre VARCHAR(50) NOT NULL UNIQUE,
    numero_pedido VARCHAR(50) DEFAULT '-',
    cliente VARCHAR(100) DEFAULT 'Sin nombre',
    fecha_cancelacion DATE,
    tienda VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a tiendas en el futuro
    proveedor VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a proveedores
    modelo VARCHAR(50) DEFAULT '-',
    armazon VARCHAR(50) DEFAULT '-',  -- Podría ser una FK a armazones
    doctor VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a doctores
    monto_total DECIMAL(10, 2) DEFAULT 0.0,
    monto_cuenta DECIMAL(10, 2) DEFAULT 0.0,
    saldo DECIMAL(10, 2) DEFAULT 0.0,
    estado_pago VARCHAR(50) DEFAULT 'CANCELADO'  -- Podría ser una FK a estados_pago
);

-- Crear tabla recetas
CREATE TABLE recetas (
    id SERIAL PRIMARY KEY,
    numero_receta VARCHAR(50) NOT NULL UNIQUE,
    nombres_cliente VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(50) DEFAULT '-',
    apellido_materno VARCHAR(50) DEFAULT '-',
    telefono_direccion VARCHAR(100) DEFAULT '-',
    fecha_receta DATE,
    doctor_receta VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a doctores
    tienda_optica VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a tiendas
    procedencia_cliente VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a procedencias
    esf_lejos_od VARCHAR(20) DEFAULT '-',
    cil_lejos_od VARCHAR(20) DEFAULT '-',
    eje_lejos_od VARCHAR(20) DEFAULT '-',
    esf_lejos_oi VARCHAR(20) DEFAULT '-',
    cil_lejos_oi VARCHAR(20) DEFAULT '-',
    eje_lejos_oi VARCHAR(20) DEFAULT '-',
    esf_cerca_od VARCHAR(20) DEFAULT '-',
    cil_cerca_od VARCHAR(20) DEFAULT '-',
    eje_cerca_od VARCHAR(20) DEFAULT '-',
    esf_cerca_oi VARCHAR(20) DEFAULT '-',
    cil_cerca_oi VARCHAR(20) DEFAULT '-',
    eje_cerca_oi VARCHAR(20) DEFAULT '-',
    dip_lejos VARCHAR(20) DEFAULT '-',
    dip_cerca VARCHAR(20) DEFAULT '-',
    dip_od VARCHAR(20) DEFAULT '-',
    dip_oi VARCHAR(20) DEFAULT '-',
    base_lente VARCHAR(50) DEFAULT '-',
    material_cristal_01 VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a cristales
    material_cristal_02 VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a cristales
    proveedor_optica VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a proveedores
    armador_optica VARCHAR(100) DEFAULT '-',  -- Podría ser una FK a armadores
    altura_lente VARCHAR(20) DEFAULT '-',
    armazon_lente VARCHAR(50) DEFAULT '-',  -- Podría ser una FK a armazones
    numero_sobre VARCHAR(50) DEFAULT '-',  -- Podría ser una FK a sobres
    fecha_entrega DATE,
    numero_pedido VARCHAR(50) DEFAULT '-'
);

-- Índices para mejorar búsquedas
CREATE INDEX idx_sobres_numero_sobre ON sobres(numero_sobre);
CREATE INDEX idx_sobres_fecha_cancelacion ON sobres(fecha_cancelacion);
CREATE INDEX idx_recetas_numero_receta ON recetas(numero_receta);
CREATE INDEX idx_recetas_fecha_receta ON recetas(fecha_receta);
CREATE INDEX idx_recetas_fecha_entrega ON recetas(fecha_entrega);