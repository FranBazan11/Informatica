#!/usr/bin/env python3
# =============================================================
#  Estacion de Monitoreo de Temperatura - Raspberry Pi
#  Autor: Juan Francisco Bazan Carrizo
#  Descripcion:
#  Mide temperatura con LM35, controla el ciclo de muestreo
#  mediante un pulsador y muestra la tendencia termica con LEDs.
#  
#  Configuracion de pines GPIO (BCM):
#  - LM35: Canal 0 del MCP3008 (ADC SPI)
#  - Boton: GPIO 2
#  - LED Rojo: GPIO 11
#  - LED Amarillo: GPIO 10
#  - LED Verde: GPIO 9
# =============================================================

import RPi.GPIO as GPIO
import spidev
import time
from collections import deque

# =============================================================
# Configuracion de pines
# =============================================================
PIN_BOTON = 2           # Pin digital del pulsador
PIN_LED_ROJO = 22       # LED ROJO
PIN_LED_AMARILLO = 27   # LED AMARILLO
PIN_LED_VERDE = 17      # LED VERDE
PIN_SENSOR = 4 			# PENSOR TEMPERATURA


# Constantes
X = 0.07            # Margen de variacion de 7%
N = 5               # Cantidad de muestras para el promedio

# Variables globales
lecturas = deque(maxlen=N)  # Ultimas lecturas
promedio = 0.0
ciclo = 3.5         # Ciclo inicial en segundos
t0 = 0              # Marca de tiempo

# Configuracion SPI para MCP3008 (ADC)
spi = spidev.SpiDev()
spi.open(0, 0)      # Bus 0, Device 0
spi.max_speed_hz = 1350000

# =============================================================
# Funciones para leer el ADC (MCP3008)
# =============================================================
def leer_adc(canal):
    """
    Lee un valor analogico del MCP3008
    Canal: 0-7
    Retorna: valor entre 0-1023
    """
    if canal < 0 or canal > 7:
        return -1
    
    # Enviar comando al MCP3008
    adc = spi.xfer2([1, (8 + canal) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def leer_temperatura():
    """
    Lee la temperatura del sensor LM35
    Retorna: temperatura en grados Celsius
    """
    lectura = leer_adc(0)  # Canal 0 del MCP3008
    # LM35: 10mV/°C, referencia 3.3V o 5V segun tu configuracion
    # Ajusta el voltaje de referencia segun tu circuito (3.3 o 5.0)
    voltaje_ref = 3.3  # Cambia a 5.0 si usas 5V
    voltaje = (lectura * voltaje_ref) / 1023.0
    temperatura = voltaje / 0.01  # 10mV por grado
    return temperatura, lectura

# =============================================================
# Funciones de control de LEDs
# =============================================================
def encender_todos():
    """Enciende todos los LEDs"""
    GPIO.output(LED_R, GPIO.HIGH)
    GPIO.output(LED_Y, GPIO.HIGH)
    GPIO.output(LED_G, GPIO.HIGH)

def apagar_todos():
    """Apaga todos los LEDs"""
    GPIO.output(LED_R, GPIO.LOW)
    GPIO.output(LED_Y, GPIO.LOW)
    GPIO.output(LED_G, GPIO.LOW)

def encender_uno(led):
    """Enciende solo un LED especifico"""
    apagar_todos()
    GPIO.output(led, GPIO.HIGH)

def destellar():
    """Destella todos los LEDs por 50ms"""
    encender_todos()
    time.sleep(0.05)
    apagar_todos()

# =============================================================
# Funciones auxiliares
# =============================================================
def promedio_n(arr):
    """Calcula el promedio de un array"""
    if len(arr) == 0:
        return 0.0
    return sum(arr) / len(arr)

# =============================================================
# Configuracion inicial
# =============================================================
def setup():
    """Inicializa GPIO y muestra mensaje de bienvenida"""
    global t0
    
    # Configurar GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Configurar pines
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(LED_R, GPIO.OUT)
    GPIO.setup(LED_Y, GPIO.OUT)
    GPIO.setup(LED_G, GPIO.OUT)
    
    # Mensaje de bienvenida
    print("===========================================")
    print(" Estacion de Monitoreo de Temperatura ")
    print(" Raspberry Pi Edition")
    print("===========================================")
    print(f"Ciclo inicial: {ciclo} s")
    
    encender_todos()
    time.sleep(1)
    apagar_todos()
    
    t0 = time.time()

# =============================================================
# Funcion principal
# =============================================================
def loop():
    """Bucle principal del programa"""
    global ciclo, t0, promedio
    
    try:
        while True:
            # ============================================================
            # --- SECCION 1: Verificar pulsador --------------------------
            # ============================================================
            
            if GPIO.input(BTN_PIN) == GPIO.HIGH:
                print("Boton presionado detectado")
                time.sleep(0.02)  # Antirrebote
                
                if GPIO.input(BTN_PIN) == GPIO.HIGH:  # Confirmacion
                    print("Confirmacion de boton presionado")
                    presionado = time.time()
                    
                    # Espera hasta que se suelte el boton
                    while GPIO.input(BTN_PIN) == GPIO.HIGH:
                        # Cada segundo destella LEDs 50ms
                        tiempo_transcurrido = time.time() - presionado
                        if int(tiempo_transcurrido * 1000) % 1000 < 50:
                            destellar()
                        time.sleep(0.01)
                    
                    # Tiempo total de presion en segundos
                    segundos_press = time.time() - presionado
                    print(f"Duracion de pulsacion: {segundos_press:.2f} s")
                    
                    # --- Acciones segun la duracion ---
                    if segundos_press < 1.0:
                        print("Pulsacion corta: fin del monitoreo.")
                        encender_todos()
                        return  # Termina el programa
                    elif segundos_press < 2.5:
                        ciclo = 2.5
                        print("Nuevo ciclo: 2.5 s")
                    elif segundos_press <= 10.0:
                        ciclo = segundos_press
                        print(f"Nuevo ciclo: {ciclo:.2f} s")
                    else:
                        ciclo = 10.0
                        print("Pulsacion larga: ciclo limitado a 10 s")
                    
                    print("-------------------------------------------")
            
            # ============================================================
            # --- SECCION 2: Medir temperatura ---------------------------
            # ============================================================
            
            tiempo_actual = time.time()
            if tiempo_actual - t0 >= ciclo:
                t0 = tiempo_actual
                temperatura, lectura = leer_temperatura()
                
                print()
                print("------ NUEVO CICLO DE MEDICION ------")
                print(f"Lectura analogica: {lectura}")
                print(f"Temperatura: {temperatura:.2f} C")
                
                # Actualiza buffer de lecturas
                lecturas.append(temperatura)
                promedio = promedio_n(lecturas)
                
                print(f"Promedio ultimas {len(lecturas)} lecturas: {promedio:.2f} C")
                
                # Determinar tendencia
                if len(lecturas) < N:
                    tendencia = "INSUFICIENTE"
                    encender_todos()
                    print("No hay suficientes datos para calcular tendencia.")
                else:
                    diff = temperatura - promedio
                    if diff > promedio * X:
                        tendencia = "ALZA"
                        encender_uno(LED_R)
                    elif diff < -promedio * X:
                        tendencia = "BAJA"
                        encender_uno(LED_G)
                    else:
                        tendencia = "ESTABLE"
                        encender_uno(LED_Y)
                    
                    print(f"Diferencia: {diff:.3f}")
                    print(f"Tendencia: {tendencia}")
                
                destellar()
                print(f"Ciclo de {ciclo:.2f} s completado.")
                print("-------------------------------------------")
            
            # Pequeña pausa para no saturar el CPU
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
    finally:
        cleanup()

def cleanup():
    """Limpia los recursos antes de salir"""
    print("Limpiando GPIO...")
    apagar_todos()
    GPIO.cleanup()
    spi.close()
    print("Programa finalizado")

# =============================================================
# Punto de entrada
# =============================================================
if __name__ == "__main__":
    setup()
    loop()
