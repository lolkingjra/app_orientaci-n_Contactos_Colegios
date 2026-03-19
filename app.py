import os
import csv
import io
import urllib.request
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app)

# Tu link CSV de Google Sheets
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkhFk8YNDk8jwORynRY1-pjLt6l-Vv_-W9plrrq3lRQcFIJgeTTkXAHNsTYWvIgekKyEuxE82lsm5Q/pub?gid=0&single=true&output=csv"

def cargar_colegios():
    """Descarga y lee los datos de Google Sheets en tiempo real."""
    try:
        with urllib.request.urlopen(CSV_URL) as response:
            contenido = response.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(contenido))
        colegios = [fila for fila in reader]
        return colegios
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return []

def formatear_colegios(colegios):
    """Convierte la lista de colegios a texto para el contexto del asistente."""
    if not colegios:
        return "No hay datos disponibles."
    
    texto = ""
    for c in colegios:
        texto += f"""
--- {c.get('nombre_institucion', 'Sin nombre')} ---
Tipo: {c.get('tipo_institucion', 'N/D')}
Provincia: {c.get('provincia', 'N/D')} | Cantón: {c.get('canton', 'N/D')}
Teléfono principal: {c.get('telefono_principal', 'N/D')}
Teléfono secundario: {c.get('telefono_secundario', 'N/D')}
Horario: {c.get('horario', 'N/D')}
Director/a: {c.get('nombre_director', 'N/D')} | Tel: {c.get('telefono_director', 'N/D')} | Correo: {c.get('correo_director', 'N/D')}
Orientador/a: {c.get('nombre_orientador', 'N/D')} | Tel: {c.get('telefono_orientador', 'N/D')} | Correo: {c.get('correo_orientador', 'N/D')}
Fecha de visita: {c.get('fecha_visita', 'N/D')}
"""
    return texto.strip()

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    pregunta = data.get("mensaje", "").strip()

    if not pregunta:
        return jsonify({"respuesta": "Por favor escribe una pregunta."}), 400

    # Cargar datos frescos desde Sheets cada vez
    colegios = cargar_colegios()
    datos_texto = formatear_colegios(colegios)
    total = len(colegios)

    system_prompt = f"""Eres un asistente virtual del Departamento de Orientación universitario.
Tu función es ayudar a consultar información de colegios visitados.
Tienes acceso a los datos de {total} institución(es) registrada(s).

Responde siempre en español, de forma clara y organizada.
Si te preguntan por un colegio específico, muestra todos sus datos.
Si te preguntan por todos los colegios, lista los nombres y datos clave.
Si no encuentras el colegio solicitado, indícalo amablemente.
No inventes datos que no estén en la base.

BASE DE DATOS ACTUAL:
{datos_texto}
"""

    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt
    )
    response = model.generate_content(pregunta)
    respuesta = response.text
    return jsonify({"respuesta": respuesta})

@app.route("/colegios", methods=["GET"])
def listar_colegios():
    """Endpoint para ver todos los colegios en JSON (útil para debug)."""
    colegios = cargar_colegios()
    return jsonify({"total": len(colegios), "colegios": colegios})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)