from flask import Flask, render_template, request, redirect, url_for, session, send_file
from database import (init_db, registrar_usuario, login_user, get_productos,
                      guardar_merma, obtener_mermas_usuario)
from datetime import datetime
import os
from openpyxl import Workbook

@app.template_filter('datetimeformat')
def datetimeformat(value):
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(value)
        # ➜ Cambia aquí tu zona horaria
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return value
app = Flask(__name__)
app.secret_key = "mermapro2025"

# Inicializar BD
init_db()

# Carpeta de uploads
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- RUTAS ----------
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = login_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        uid = registrar_usuario(email, password)
        if uid:
            session["user_id"] = uid
            session["email"] = email
            return redirect(url_for("dashboard"))
        else:
            return render_template("register.html", error="El correo ya existe")
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    mermas = obtener_mermas_usuario(session["user_id"])
    return render_template("dashboard.html", mermas=mermas, email=session["email"])

@app.route("/nueva", methods=["GET", "POST"])
def nueva():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        producto = request.form["producto"]
        inicial = float(request.form["inicial"])
        merma = float(request.form["merma"])
        final = inicial - merma
        foto = request.files["foto"]
        foto_path = None
        if foto and foto.filename:
            foto_path = os.path.join(app.config["UPLOAD_FOLDER"], foto.filename)
            foto.save(foto_path)
        guardar_merma(session["user_id"], producto, inicial, merma, final, foto_path)
        return redirect(url_for("dashboard"))
    productos = get_productos()
    return render_template("merma_form.html", productos=productos)

@app.route("/exportar_excel")
def exportar_excel():
    if "user_id" not in session:
        return redirect(url_for("login"))
    mermas = obtener_mermas_usuario(session["user_id"])
    wb = Workbook()
    ws = wb.active
    ws.title = "Mis Mermas"
    ws.append(["Producto", "Peso Inicial (g)", "Merma (g)", "Final (g)", "% Merma", "Fecha"])
    for m in mermas:
        ws.append([m["producto"], f"{m['inicial']:.2f}", f"{m['merma']:.2f}",
                   f"{m['final']:.2f}", f"{m['porc_merma']:.1f} %", m["fecha"][:16]])
    archivo = f"exports/MisMermas_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    os.makedirs("exports", exist_ok=True)
    wb.save(archivo)
    return send_file(archivo, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

