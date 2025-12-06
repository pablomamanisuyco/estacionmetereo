#!/usr/bin/env python3
"""
mqttpyton.py
Suscriptor MQTT (HiveMQ Cloud). Muestra por pantalla temperatura, humedad y presión.
Requiere: paho-mqtt
"""

import ssl
import json
import time
import sys
import argparse
import paho.mqtt.client as mqtt

# Valores por defecto (modifica si lo necesitas)
BROKER = "f97725ae76b641a3b27f3cfee11cc92a.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "Huamanga1"
PASSWORD = "Huamanga12"
TOPIC = "estacion/#"
CLIENT_ID = "mqtt_reader_pc"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT.")
        client.subscribe(TOPIC)
        print(f"Suscrito a: {TOPIC}")
    else:
        print(f"Fallo al conectar, rc={rc}")

def try_parse_json(payload_bytes):
    try:
        text = payload_bytes.decode('utf-8')
    except Exception:
        return None, payload_bytes
    try:
        data = json.loads(text)
        return data, text
    except Exception:
        return None, text

def print_separated_readings(topic, timestamp, temperatura, humedad, presion, viento, lluvia):
    # Imprime los datos separadamente, con unidades
    print(f"--- Mensaje recibido en tópico: {topic} ---")
    print(f"Timestamp : {timestamp}")
    if temperatura is not None:
        print(f"Temperatura: {temperatura:.2f} °C")
    if humedad is not None:
        print(f"Humedad    : {humedad:.1f} %")
    if presion is not None:
        print(f"Presion    : {presion:.2f} hPa")
    if viento is not None:
        print(f"Viento     : {viento:.1f} km/h")
    if lluvia is not None:
        print(f"Lluvia     : {lluvia} %")
    print("-----------------------------------------")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload_bytes = msg.payload
    data, raw = try_parse_json(payload_bytes)

    # Si viene JSON con las claves esperadas, mostrar separado
    if isinstance(data, dict):
        # Leer campos posibles (acepta varias variantes de nombre)
        timestamp = data.get("timestamp") or data.get("time") or None

        def get_num(*keys):
            for k in keys:
                if k in data:
                    try:
                        return float(data[k])
                    except Exception:
                        return None
            return None

        temperatura = get_num("temperatura", "temp", "Temperatura")
        humedad = get_num("humedad", "hum", "Humedad")
        presion = get_num("presion", "pressure", "Presion")
        viento = get_num("viento", "wind", "viento")
        # lluvia puede venir como int
        lluvia = None
        for k in ("lluvia", "rain", "rainfall"):
            if k in data:
                try:
                    lluvia = int(data[k])
                except Exception:
                    try:
                        lluvia = int(float(data[k]))
                    except Exception:
                        lluvia = None
                break

        # Si encontramos al menos uno de los valores/ timestamp, imprimimos separado
        if timestamp or temperatura is not None or humedad is not None or presion is not None or viento is not None or lluvia is not None:
            # Si no hay timestamp en el JSON, usar hora local
            if not timestamp:
                timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
            print_separated_readings(topic, timestamp, temperatura, humedad, presion, viento, lluvia)
            return

    # Si no es JSON con campos esperados, intentar extraer número según tópico (compatibilidad)
    text = raw if isinstance(raw, str) else None
    if text:
        text = text.strip().strip('"')
        # topic específico
        if topic.endswith("temperatura"):
            try:
                val = float(text)
                print_separated_readings(topic, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()), val, None, None, None, None)
                return
            except Exception:
                pass
        if topic.endswith("humedad"):
            try:
                val = float(text)
                print_separated_readings(topic, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()), None, val, None, None, None)
                return
            except Exception:
                pass
        if topic.endswith("presion"):
            try:
                val = float(text)
                print_separated_readings(topic, time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()), None, None, val, None, None)
                return
            except Exception:
                pass

    # Si no se pudo extraer nada reconocible, imprimir mensaje crudo
    if isinstance(raw, bytes):
        try:
            raw = raw.decode('utf-8')
        except Exception:
            raw = str(raw)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    print(f"[{ts}] {topic} -> {raw}")

def on_disconnect(client, userdata, rc):
    print("Desconectado del broker MQTT (rc=%s). Intentando reconectar..." % rc)

def make_client(broker, port, user, password, client_id):
    client = mqtt.Client(client_id=client_id)
    client.username_pw_set(user, password)

    # TLS: usar contexto por defecto para validar certificados del servidor
    context = ssl.create_default_context()
    client.tls_set_context(context)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    return client

def main():
    parser = argparse.ArgumentParser(description="Suscriptor MQTT para mostrar temperatura, humedad y presion.")
    parser.add_argument("--broker", "-b", default=BROKER, help="Broker MQTT")
    parser.add_argument("--port", "-p", type=int, default=PORT, help="Puerto MQTT (TLS)")
    parser.add_argument("--user", "-u", default=USERNAME, help="Usuario MQTT")
    parser.add_argument("--password", "-P", default=PASSWORD, help="Contraseña MQTT")
    parser.add_argument("--topic", "-t", default=TOPIC, help="Tópico a suscribirse (default: estacion/#)")
    parser.add_argument("--client-id", "-i", default=CLIENT_ID, help="ID del cliente MQTT")
    args = parser.parse_args()

    client = make_client(args.broker, args.port, args.user, args.password, args.client_id)
    print(f"Conectando a {args.broker}:{args.port} como {args.user} ...")
    try:
        client.connect(args.broker, args.port, keepalive=60)
    except Exception as e:
        print("Error al conectar:", e)
        print("Saliendo.")
        sys.exit(1)

    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()