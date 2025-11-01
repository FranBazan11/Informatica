#!/usr/bin/env python3
import socket
import csv
import time
import os

HOST = '0.0.0.0'   # Escucha en todas las interfaces (LAN)
PORT = 25565
CSV_PATH = os.path.join(os.path.dirname(__file__), "temperaturas.csv")

def enviar_datos(conn):
    """Lee el CSV y envía todas las líneas simulando transmisión en tiempo real"""
    try:
        with open(CSV_PATH, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # salta cabecera si existe
            lineas = [row for row in reader if row]  # evita filas vacías

        total = len(lineas)
        print(f"📄 Enviando {total} registros...\n")

        for i, row in enumerate(lineas, start=1):
            linea = ",".join(row)
            conn.sendall((linea + "\n").encode('utf-8'))
            print(f"[{i}/{total}] Enviado: {linea}")
            time.sleep(1)  # Simula datos en tiempo real (1 segundo entre lecturas)

        # Espera breve para garantizar que el cliente procese el último paquete
        time.sleep(2)
        print("✅ Todos los datos fueron enviados correctamente.")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {CSV_PATH}")
    except (BrokenPipeError, ConnectionResetError):
        print("⚠️  El cliente cerró la conexión antes de tiempo.")
    finally:
        conn.close()
        print("🔌 Conexión cerrada correctamente.\n")

def main():
    print(f"Servidor escuchando en {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print("💤 Esperando conexión del cliente...\n")
        conn, addr = s.accept()
        print(f"✅ Cliente conectado desde: {addr}\n")
        enviar_datos(conn)
        print("🟢 Transmisión finalizada. Servidor listo para salir.\n")

if __name__ == "__main__":
    main()
