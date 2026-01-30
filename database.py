import sqlite3

def conectar():
    # Usamos el nombre oficial del proyecto para la DB
    return sqlite3.connect('vialactea_datos.db')

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabla de Hato: Agregamos 'estado' y 'ultimo_parto' para las alertas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hato (
            id_vaca TEXT PRIMARY KEY,
            nombre TEXT,
            raza TEXT,
            estado TEXT DEFAULT 'Abierta', -- Abierta, Inseminada, Preñada, Seca
            fecha_ingreso DATE,
            ultimo_parto DATE
        )
    ''')
    
    # Tabla de Producción: Mantenemos tu esquema pero optimizado para índices
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vaca TEXT,
            litros REAL,
            fecha DATE DEFAULT (date('now')),
            FOREIGN KEY (id_vaca) REFERENCES hato (id_vaca)
        )
    ''')

    # Nueva Tabla de Eventos: Para el historial clínico y reproductivo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_vaca TEXT,
            tipo_evento TEXT, -- IA, TACTO, SECADO, VACUNA
            resultado TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_vaca) REFERENCES hato (id_vaca)
        )
    ''')
    
    conn.commit()
    conn.close()

# Inicialización automática
crear_tablas()
