#!/usr/bin/env python3
import socket
import matplotlib.pyplot as plt
import time

HOST = '192.168.1.43'   # IP de la Raspberry Pi
PORT = 25565

# Listas para graficar
tiempos = []
temperaturas = []
colores = []

def color_por_tendencia(tendencia):
    if tendencia == 'A': return 'red'
    if tendencia == 'B': return 'green'
    if tendencia == 'E': return 'gold'
    return 'gray'

print(f"Intentando conectar con el servidor {HOST}:{PORT}...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("✅ Conectado correctamente al servidor.\n")

    buffer = b""
    plt.ion()  # modo interactivo
    fig, ax = plt.subplots()
    ax.set_title("Evolución de la Temperatura en Tiempo Real")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Temperatura [°C]")
    plt.xticks(rotation=45)

    try:
        while True:
            chunk = s.recv(1024)
            if not chunk:
                print("🔚 Conexión cerrada por el servidor.")
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                data = line.decode().strip()
                if not data:
                    continue

                # Procesa línea CSV: fecha, tendencia, temperatura
                try:
                    fecha, tendencia, temp_str = data.split(",")
                    temperatura = float(temp_str)
                    tiempos.append(fecha[-8:])  # hh:mm:ss
                    temperaturas.append(temperatura)
                    colores.append(color_por_tendencia(tendencia))

                    # Actualiza gráfico
                    ax.clear()
                    ax.set_title("Evolución de la Temperatura en Tiempo Real")
                    ax.set_xlabel("Hora")
                    ax.set_ylabel("Temperatura [°C]")
                    ax.grid(True, linestyle='--', alpha=0.5)
                    plt.xticks(rotation=45)
                    ax.plot(tiempos, temperaturas, color='lightgray', linestyle='--', linewidth=1)
                    ax.scatter(tiempos, temperaturas, c=colores, s=60)
                    plt.pause(0.5)  # refresco suave
                except ValueError:
                    pass
    except KeyboardInterrupt:
        print("🛑 Conexión interrumpida por el usuario.")
    finally:
        plt.ioff()
        plt.show()
        print("✅ Todos los datos fueron graficados correctamente.")
