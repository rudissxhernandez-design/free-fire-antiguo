
import os
import uuid
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


def conectar():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no configurada")
    return psycopg2.connect(DATABASE_URL, connect_timeout=10)


def inicializar_base_datos():
    with conectar() as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jugadores (
                    id TEXT PRIMARY KEY,
                    nombre VARCHAR(20) NOT NULL,
                    fecha TIMESTAMPTZ NOT NULL
                )
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                jugadores_nombre_lower_idx
                ON jugadores (LOWER(nombre))
            """)


@app.route("/")
def inicio():
    return jsonify({
        "servidor": "BARBOSA SERVER",
        "version": "1.53.2",
        "estado": "ONLINE",
        "modo": "POSTGRESQL"
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
    try:
        with conectar() as conexion:
            with conexion.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, nombre, fecha
                    FROM jugadores
                    ORDER BY fecha
                """)
                filas = cursor.fetchall()

        jugadores = [
            {
                "id": fila["id"],
                "nombre": fila["nombre"],
                "fecha": fila["fecha"].isoformat()
            }
            for fila in filas
        ]

        return jsonify({
            "total": len(jugadores),
            "jugadores": jugadores
        })

    except Exception:
        app.logger.exception("Error consultando jugadores")
        return jsonify({"error": "Error de base de datos"}), 500


@app.route("/registro", methods=["POST"])
def registrar_jugador():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("nombre", "")).strip()

    if not nombre or len(nombre) > 20:
        return jsonify({
            "error": "El nombre debe tener entre 1 y 20 caracteres"
        }), 400

    jugador_id = str(uuid.uuid4())
    fecha = datetime.now(timezone.utc)

    try:
        with conectar() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO jugadores (id, nombre, fecha)
                    VALUES (%s, %s, %s)
                """, (jugador_id, nombre, fecha))

        return jsonify({
            "mensaje": "Jugador registrado",
            "jugador": {
                "id": jugador_id,
                "nombre": nombre,
                "fecha": fecha.isoformat()
            }
        }), 201

    except psycopg2.errors.UniqueViolation:
        return jsonify({
            "error": "Ese nombre ya está registrado"
        }), 409

    except Exception:
        app.logger.exception("Error registrando jugador")
        return jsonify({"error": "Error registrando jugador"}), 500


inicializar_base_datos()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

