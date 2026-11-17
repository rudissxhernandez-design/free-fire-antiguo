
from flask import Flask, jsonify, request
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

app = Flask(__name__)

ARCHIVO = Path(r"C:\BARBOSA_SERVER\config\jugadores.json")


def cargar_jugadores():
    if not ARCHIVO.exists():
        return []
    try:
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def guardar_jugadores(jugadores):
    ARCHIVO.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVO.write_text(
        json.dumps(jugadores, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )


@app.route("/")
def inicio():
    return jsonify({
        "servidor": "BARBOSA SERVER",
        "version": "1.53.2",
        "estado": "ONLINE",
        "modo": "LOCAL"
    })


@app.route("/status")
def estado():
    return jsonify({
        "online": True,
        "servidor": "BARBOSA SERVER",
        "version": "1.53.2"
    })


@app.route("/jugadores", methods=["GET"])
def listar_jugadores():
    return jsonify({
        "total": len(cargar_jugadores()),
        "jugadores": cargar_jugadores()
    })


@app.route("/registro", methods=["POST"])
def registrar_jugador():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("nombre", "")).strip()

    if not nombre or len(nombre) > 20:
        return jsonify({
            "error": "El nombre debe tener entre 1 y 20 caracteres"
        }), 400

    jugadores = cargar_jugadores()

    if any(j["nombre"].lower() == nombre.lower() for j in jugadores):
        return jsonify({"error": "Ese nombre ya está registrado"}), 409

    jugador = {
        "id": str(uuid.uuid4()),
        "nombre": nombre,
        "fecha": datetime.now(timezone.utc).isoformat()
    }

    jugadores.append(jugador)
    guardar_jugadores(jugadores)

    return jsonify({
        "mensaje": "Jugador registrado",
        "jugador": jugador
    }), 201


if __name__ == "__main__":
    print("BARBOSA SERVER iniciado")
    app.run(host="0.0.0.0", port=5000, debug=False)
