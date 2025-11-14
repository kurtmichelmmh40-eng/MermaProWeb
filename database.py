import sqlite3, hashlib, os
from datetime import datetime

DB_FILE = "mermas.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS productos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_crudo TEXT,
                    nombre_limpio TEXT,
                    categoria TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS mermas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    producto_id INTEGER,
                    peso_original REAL,
                    peso_merma REAL,
                    peso_final REAL,
                    foto_path TEXT,
                    fecha TEXT,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY(producto_id) REFERENCES productos(id))""")
    # Productos demo
    productos = [
        ("Palta", "Palta limpia", "Fruta"),
        ("Tomate", "Tomate limpio", "Verdura"),
        ("Lechuga", "Lechuga limpia", "Verdura"),
        ("Pimiento", "Pimiento limpio", "Verdura"),
        ("Cebolla", "Cebolla limpia", "Verdura"),
        ("Zanahoria", "Zanahoria limpia", "Verdura"),
        ("Papa", "Papa limpia", "Tubérculo"),
        ("Pollo", "Pollo limpio", "Proteína"),
        ("Pescado", "Pescado limpio", "Proteína"),
        ("Res", "Res limpia", "Proteína")
    ]
    c.executemany("INSERT OR IGNORE INTO productos(nombre_crudo,nombre_limpio,categoria) VALUES(?,?,?)", productos)
    conn.commit()
    conn.close()

def registrar_usuario(email, password):
    conn = get_connection()
    c = conn.cursor()
    phash = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO usuarios(email,password) VALUES(?,?)", (email, phash))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        user_id = None
    conn.close()
    return user_id

def login_user(email, password):
    conn = get_connection()
    c = conn.cursor()
    phash = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id,email FROM usuarios WHERE email=? AND password=?", (email, phash))
    user = c.fetchone()
    conn.close()
    return {"id": user[0], "email": user[1]} if user else None

def get_productos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT nombre_crudo FROM productos ORDER BY nombre_crudo")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def guardar_merma(usuario_id, producto_nombre, inicial, merma, final, foto_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM productos WHERE nombre_crudo=?", (producto_nombre,))
    prod_id = c.fetchone()[0]
    c.execute("""INSERT INTO mermas(usuario_id,producto_id,peso_original,peso_merma,peso_final,foto_path,fecha)
                 VALUES(?,?,?,?,?,?,?)""",
              (usuario_id, prod_id, inicial, merma, final, foto_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def obtener_mermas_usuario(usuario_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT p.nombre_crudo, m.peso_original, m.peso_merma, m.peso_final,
                        ROUND(m.peso_merma * 100.0 / m.peso_original, 1) AS porc_merma,
                        m.foto_path, m.fecha
                 FROM mermas m
                 JOIN productos p ON p.id = m.producto_id
                 WHERE m.usuario_id = ?
                 ORDER BY m.fecha DESC""", (usuario_id,))
    rows = [dict(zip(["producto", "inicial", "merma", "final", "porc_merma", "foto", "fecha"], row)) for row in c.fetchall()]
    conn.close()
    return rows
