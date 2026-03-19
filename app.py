import os
import csv
import io
import unicodedata
import urllib.request
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkhFk8YNDk8jwORynRY1-pjLt6l-Vv_-W9plrrq3lRQcFIJgeTTkXAHNsTYWvIgekKyEuxE82lsm5Q/pub?gid=0&single=true&output=csv"

def normalizar(texto):
    texto = texto.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def cargar_colegios():
    try:
        with urllib.request.urlopen(CSV_URL) as response:
            contenido = response.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(contenido))
        return [fila for fila in reader]
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return []

def formatear_colegio(c):
    def v(campo): return c.get(campo, '').strip() or 'No registrado'
    return (
        f"🏫 {v('nombre_institucion')}\n"
        f"   Tipo: {v('tipo_institucion')} | Provincia: {v('provincia')} | Canton: {v('canton')}\n"
        f"   📞 Tel. principal: {v('telefono_principal')}\n"
        f"   📞 Tel. secundario: {v('telefono_secundario')}\n"
        f"   🕐 Horario: {v('horario')}\n"
        f"   👤 Director/a: {v('nombre_director')} | {v('telefono_director')} | {v('correo_director')}\n"
        f"   🧭 Orientador/a: {v('nombre_orientador')} | {v('telefono_orientador')} | {v('correo_orientador')}\n"
        f"   📅 Fecha de visita: {v('fecha_visita')}"
    )

def buscar(colegios, termino):
    t = normalizar(termino)
    campos = ['nombre_institucion', 'provincia', 'canton', 'tipo_institucion',
              'nombre_director', 'nombre_orientador']
    return [c for c in colegios if any(t in normalizar(c.get(campo, '')) for campo in campos)]

def procesar_consulta(texto, colegios):
    t = normalizar(texto)
    total = len(colegios)

    if t in ['hola', 'hi', 'buenos dias', 'buenas', 'buenas tardes', 'buenas noches']:
        return f"Hola! Soy el asistente de orientacion. Tengo registrados {total} colegio(s).\n\nPuedes buscar por nombre, provincia, canton o nombre del director/orientador.\nEjemplo: \"Colegio Lincoln\" o \"colegios de Heredia\""

    if any(p in t for p in ['todos', 'lista', 'listar', 'mostrar todos', 'ver todos', 'cuantos']):
        if total == 0:
            return "No hay colegios registrados aun."
        lista = "\n".join(f"  {i+1}. {c.get('nombre_institucion','Sin nombre')} ({c.get('provincia','?')})"
                          for i, c in enumerate(colegios))
        return f"Colegios registrados ({total} en total):\n\n{lista}"

    resultados = buscar(colegios, texto)
    if not resultados:
        return f"No encontre ningun colegio con \"{texto}\".\n\nIntenta con el nombre completo o parcial, provincia o canton."
    if len(resultados) == 1:
        return f"Encontre 1 resultado:\n\n{formatear_colegio(resultados[0])}"
    detalle = "\n\n".join(formatear_colegio(c) for c in resultados)
    return f"Encontre {len(resultados)} resultados para \"{texto}\":\n\n{detalle}"

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    pregunta = data.get("mensaje", "").strip()
    if not pregunta:
        return jsonify({"respuesta": "Por favor escribe una consulta."}), 400
    colegios = cargar_colegios()
    respuesta = procesar_consulta(pregunta, colegios)
    return jsonify({"respuesta": respuesta})

@app.route("/colegios", methods=["GET"])
def listar_colegios():
    colegios = cargar_colegios()
    return jsonify({"total": len(colegios), "colegios": colegios})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)