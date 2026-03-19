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

def v(c, campo):
    val = c.get(campo, '').strip()
    return val if val else None

def formatear_colegio_completo(c):
    lineas = [f"🏫  {v(c,'nombre_institucion') or 'Sin nombre'}"]
    if v(c,'tipo_institucion'): lineas.append(f"   Tipo        : {v(c,'tipo_institucion')}")
    if v(c,'provincia'):        lineas.append(f"   Provincia   : {v(c,'provincia')}")
    if v(c,'canton'):           lineas.append(f"   Canton      : {v(c,'canton')}")
    if v(c,'horario'):          lineas.append(f"   Horario     : {v(c,'horario')}")
    lineas.append("")
    lineas.append("   — Director/a —")
    lineas.append(f"   Nombre   : {v(c,'nombre_director') or 'No registrado'}")
    lineas.append(f"   Telefono : {v(c,'telefono_director') or 'No registrado'}")
    lineas.append(f"   Correo   : {v(c,'correo_director') or 'No registrado'}")
    lineas.append("")
    lineas.append("   — Orientador/a —")
    lineas.append(f"   Nombre   : {v(c,'nombre_orientador') or 'No registrado'}")
    lineas.append(f"   Telefono : {v(c,'telefono_orientador') or 'No registrado'}")
    lineas.append(f"   Correo   : {v(c,'correo_orientador') or 'No registrado'}")
    lineas.append("")
    lineas.append(f"   Telefonos  : {v(c,'telefono_principal') or 'N/D'}  /  {v(c,'telefono_secundario') or 'N/D'}")
    if v(c,'fecha_visita'): lineas.append(f"   Fecha visita: {v(c,'fecha_visita')}")
    return "\n".join(lineas)

def buscar_colegios(colegios, termino):
    t = normalizar(termino)
    campos = ['nombre_institucion','provincia','canton','tipo_institucion','nombre_director','nombre_orientador']
    return [c for c in colegios if any(t in normalizar(c.get(campo,'')) for campo in campos)]

def procesar(texto, colegios):
    t = normalizar(texto)
    total = len(colegios)

    # ---------- saludos ----------
    saludos = ['hola','hi','buenas','buenos dias','buenas tardes','buenas noches','buen dia','hey']
    if t in saludos or any(t.startswith(s) for s in saludos):
        return (f"Hola! Soy el asistente de orientacion.\n"
                f"Tengo {total} colegio(s) registrado(s).\n\n"
                f"Puedes preguntarme cosas como:\n"
                f"  • dame los datos del Colegio Lincoln\n"
                f"  • que colegios hay en Heredia\n"
                f"  • cual es el telefono del Liceo Nacional\n"
                f"  • quien es el director del Colegio Tecnico\n"
                f"  • correo del orientador del Liceo X\n"
                f"  • horario del Colegio Y\n"
                f"  • lista todos los colegios\n"
                f"  • colegios publicos / privados / tecnicos")

    # ---------- ayuda ----------
    if any(p in t for p in ['ayuda','que puedo','como uso','opciones','comandos']):
        return ("Comandos disponibles:\n\n"
                "BUSCAR COLEGIO\n"
                "  datos del [nombre]\n"
                "  informacion de [nombre]\n\n"
                "TELEFONOS\n"
                "  telefono de [nombre]\n"
                "  numero de [nombre]\n\n"
                "CORREOS\n"
                "  correo de [nombre]\n"
                "  correo del orientador de [nombre]\n"
                "  correo del director de [nombre]\n\n"
                "DIRECTOR / ORIENTADOR\n"
                "  quien es el director de [nombre]\n"
                "  quien es el orientador de [nombre]\n\n"
                "HORARIO\n"
                "  horario de [nombre]\n\n"
                "POR PROVINCIA / TIPO\n"
                "  colegios en [provincia]\n"
                "  colegios publicos / privados / tecnicos\n\n"
                "VER TODOS\n"
                "  lista todos / ver todos")

    # ---------- ver todos ----------
    if any(p in t for p in ['todos los colegios','lista todos','ver todos','listar todos','mostrar todos','cuantos colegios hay','cuantos hay']):
        if total == 0:
            return "No hay colegios registrados aun."
        lista = "\n".join(f"  {i+1}. {c.get('nombre_institucion','Sin nombre')}  ({c.get('provincia','?')})"
                          for i, c in enumerate(colegios))
        return f"Colegios registrados — {total} en total:\n\n{lista}"

    # ---------- por tipo ----------
    for tipo_key, tipo_label in [('public','Publico'),('privado','Privado'),('tecnico','Tecnico'),('academico','Academico')]:
        if tipo_key in t:
            filtrados = [c for c in colegios if tipo_key in normalizar(c.get('tipo_institucion',''))]
            if not filtrados:
                return f"No encontre colegios de tipo '{tipo_label}'."
            lista = "\n".join(f"  {i+1}. {c.get('nombre_institucion','?')}  ({c.get('provincia','?')})" for i,c in enumerate(filtrados))
            return f"Colegios {tipo_label} ({len(filtrados)}):\n\n{lista}"

    # ---------- telefono ----------
    pide_tel = any(p in t for p in ['telefono','numero','tel ','numero de telefono','celular'])
    pide_correo_orient = any(p in t for p in ['correo del orientador','email del orientador','correo orientador'])
    pide_correo_dir = any(p in t for p in ['correo del director','email del director','correo director'])
    pide_correo = any(p in t for p in ['correo','email','mail']) and not pide_correo_orient and not pide_correo_dir
    pide_director = any(p in t for p in ['director','directora','quien dirige'])
    pide_orientador = any(p in t for p in ['orientador','orientadora','encargado de orientacion'])
    pide_horario = any(p in t for p in ['horario','hora','atienden','abierto'])

    # extraer nombre del colegio eliminando palabras clave
    palabras_clave = ['telefono','numero','correo','email','mail','director','directora',
                      'orientador','orientadora','horario','hora','datos','informacion',
                      'del','de la','de los','quien es el','quien es la','cual es el',
                      'cual es la','dame','quiero','necesito','busca','buscar','ver',
                      'colegio','liceo','instituto','escuela','centro','tecnico']
    termino_limpio = t
    for pk in palabras_clave:
        termino_limpio = termino_limpio.replace(pk, ' ')
    termino_limpio = ' '.join(termino_limpio.split()).strip()

    resultados = buscar_colegios(colegios, termino_limpio) if len(termino_limpio) > 2 else []

    # si no encontro con limpio, busca con texto original
    if not resultados and len(t) > 3:
        resultados = buscar_colegios(colegios, texto)

    if not resultados:
        return (f"No encontre ningun colegio con '{texto}'.\n\n"
                f"Sugerencias:\n"
                f"  • Escribe el nombre o parte del nombre\n"
                f"  • Prueba con la provincia: 'colegios en Heredia'\n"
                f"  • Escribe 'lista todos' para ver todos los colegios")

    c = resultados[0]
    nombre = c.get('nombre_institucion','este colegio')

    # respuesta especifica segun lo que pide
    if pide_tel:
        t1 = v(c,'telefono_principal') or 'No registrado'
        t2 = v(c,'telefono_secundario')
        resp = f"Telefonos de {nombre}:\n\n  Principal  : {t1}"
        if t2: resp += f"\n  Secundario : {t2}"
        return resp

    if pide_correo_orient:
        co = v(c,'correo_orientador') or 'No registrado'
        no = v(c,'nombre_orientador') or 'No registrado'
        return f"Orientador/a de {nombre}:\n\n  Nombre : {no}\n  Correo : {co}"

    if pide_correo_dir:
        cd = v(c,'correo_director') or 'No registrado'
        nd = v(c,'nombre_director') or 'No registrado'
        return f"Director/a de {nombre}:\n\n  Nombre : {nd}\n  Correo : {cd}"

    if pide_correo:
        co = v(c,'correo_orientador') or 'No registrado'
        cd = v(c,'correo_director') or 'No registrado'
        return (f"Correos de {nombre}:\n\n"
                f"  Director/a   : {cd}\n"
                f"  Orientador/a : {co}")

    if pide_director:
        nd = v(c,'nombre_director') or 'No registrado'
        td = v(c,'telefono_director') or 'No registrado'
        cd = v(c,'correo_director') or 'No registrado'
        return f"Director/a de {nombre}:\n\n  Nombre   : {nd}\n  Telefono : {td}\n  Correo   : {cd}"

    if pide_orientador:
        no = v(c,'nombre_orientador') or 'No registrado'
        to = v(c,'telefono_orientador') or 'No registrado'
        co = v(c,'correo_orientador') or 'No registrado'
        return f"Orientador/a de {nombre}:\n\n  Nombre   : {no}\n  Telefono : {to}\n  Correo   : {co}"

    if pide_horario:
        h = v(c,'horario') or 'No registrado'
        return f"Horario de {nombre}:\n\n  {h}"

    # datos completos (o multiples resultados)
    if len(resultados) == 1:
        return f"Datos de {nombre}:\n\n{formatear_colegio_completo(c)}"

    if len(resultados) <= 5:
        detalle = "\n\n" + "—"*40 + "\n\n"
        detalle = detalle.join(formatear_colegio_completo(r) for r in resultados)
        return f"Encontre {len(resultados)} coincidencias:\n\n{detalle}"

    lista = "\n".join(f"  {i+1}. {r.get('nombre_institucion','?')}  ({r.get('provincia','?')})" for i,r in enumerate(resultados))
    return f"Encontre {len(resultados)} coincidencias. Sé mas especifico o escoge uno:\n\n{lista}"

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
    respuesta = procesar(pregunta, colegios)
    return jsonify({"respuesta": respuesta})

@app.route("/colegios", methods=["GET"])
def listar_colegios():
    colegios = cargar_colegios()
    return jsonify({"total": len(colegios), "colegios": colegios})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)