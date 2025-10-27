#!/usr/bin/env python3
# =============================================================
#  Estacion de Monitoreo de Temperatura - Raspberry Pi
#  Autor: Juan Francisco Bazan Carrizo
#  Descripcion:
#  Mide temperatura con DS18B20, controla el ciclo de muestreo
#  mediante un pulsador y muestra la tendencia termica con LEDs.
#  
#  Configuracion de pines GPIO (BCM):
#  Nota: Este script usa numeracion BCM (GPIO.setmode(GPIO.BCM)).
#  A continuacion se indica el equivalente de "pin fisico" del header de 40 pines:
#  - DS18B20: GPIO 4 (BCM)  = pin fisico 7   | VDD = pin fisico 1 (3.3V) | GND = pin fisico 6
#  - Boton:   GPIO 2 (BCM)  = pin fisico 3
#  - LED Rojo:      GPIO 22 (BCM) = pin fisico 15
#  - LED Amarillo:  GPIO 27 (BCM) = pin fisico 13
#  - LED Verde:     GPIO 17 (BCM) = pin fisico 11
# =============================================================

import RPi.GPIO as GPIO
import time
import os
import glob
from collections import deque

# =============================================================
# Configuracion de pines (BCM -> equivalente pin fisico)
# =============================================================
PIN_BOTON = 3           # Boton - GPIO 2 (BCM)  = pin fisico 3
PIN_LED_ROJO = 22       # LED Rojo - GPIO 22 (BCM) = pin fisico 15
PIN_LED_AMARILLO = 27   # LED Amarillo - GPIO 27 (BCM) = pin fisico 13
PIN_LED_VERDE = 17      # LED Verde - GPIO 17 (BCM) = pin fisico 11

# Constantes
X = 0.07            # Margen de variacion de 7%
N = 5               # Cantidad de muestras para el promedio

# Variables globales
lecturas = deque(maxlen=N)  # Ultimas lecturas
promedio = 0.0
ciclo = 3.5         # Ciclo inicial en segundos
t0 = 0              # Marca de tiempo

# =============================================================
# Configuracion del sensor DS18B20 (1-Wire)
# =============================================================
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]
device_file = device_folder + '/w1_slave'

# =============================================================
# Funciones para leer el sensor DS18B20 (1-Wire)
# =============================================================
def leer_temperatura_raw():
    """
    Lee los datos brutos del sensor DS18B20
    Retorna: lineas del archivo del sensor
    """
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def leer_temperatura():
    """
    Lee la temperatura del sensor DS18B20
    Retorna: temperatura en grados Celsius
    """
    lines = leer_temperatura_raw()
    
    # Verifica que la lectura sea valida (CRC OK)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = leer_temperatura_raw()
    
    # Extrae la temperatura
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c
    else:
        return None

# =============================================================
# Funciones de control de LEDs
# =============================================================
def encender_todos():
    """Enciende todos los LEDs"""
    GPIO.output(PIN_LED_ROJO, GPIO.HIGH)
    GPIO.output(PIN_LED_AMARILLO, GPIO.HIGH)
    GPIO.output(PIN_LED_VERDE, GPIO.HIGH)

def apagar_todos():
    """Apaga todos los LEDs"""
    GPIO.output(PIN_LED_ROJO, GPIO.LOW)
    GPIO.output(PIN_LED_AMARILLO, GPIO.LOW)
    GPIO.output(PIN_LED_VERDE, GPIO.LOW)

def encender_uno(led):
    """Enciende solo un LED especifico"""
    apagar_todos()
    GPIO.output(led, GPIO.HIGH)

def destellar(tiempo=0.05):
    """Destella todos los LEDs con tiempo configurable"""
    apagar_todos()           # Asegura estado inicial
    time.sleep(0.01)         # Pausa para contraste visual
    encender_todos()
    time.sleep(tiempo)       # Tiempo del destello (parametrizable)
    apagar_todos()
    time.sleep(0.01)         # Pausa final

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
    GPIO.setup(PIN_BOTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(PIN_LED_ROJO, GPIO.OUT)
    GPIO.setup(PIN_LED_AMARILLO, GPIO.OUT)
    GPIO.setup(PIN_LED_VERDE, GPIO.OUT)
    
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
            
            if GPIO.input(PIN_BOTON) == GPIO.LOW:
                print("Boton presionado detectado")
                time.sleep(0.02)  # Antirrebote
                
                if GPIO.input(PIN_BOTON) == GPIO.LOW:  # Confirmacion
                    presionado = time.time()
                    
                    # Espera hasta que se suelte el boton
                    while GPIO.input(PIN_BOTON) == GPIO.LOW:
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
                temperatura = leer_temperatura()
                
                if temperatura is None:
                    print("Error al leer temperatura")
                    continue
                
                print()
                print("------ NUEVO CICLO DE MEDICION ------")
                print(f"Temperatura: {temperatura:.2f} C")
                
                # Actualiza buffer de lecturas
                lecturas.append(temperatura)
                promedio = promedio_n(lecturas)
                
                print(f"Promedio ultimas {len(lecturas)} lecturas: {promedio:.2f} C")
                
                # Determinar tendencia
                if len(lecturas) < N:
                    tendencia = "INSUFICIENTE"
                    destellar()
                    print("No hay suficientes datos para calcular tendencia.")
                else:
                    diff = temperatura - promedio
                    if diff > promedio * X:
                        tendencia = "ALZA"
                        apagar_todos()
                        encender_uno(PIN_LED_ROJO)
                    elif diff < -promedio * X:
                        tendencia = "BAJA"
                        apagar_todos()
                        encender_uno(PIN_LED_VERDE)
                    else:
                        tendencia = "ESTABLE"
                        apagar_todos()
                        encender_uno(PIN_LED_AMARILLO)
                    
                    print(f"Diferencia: {diff:.3f}")
                    print(f"Tendencia: {tendencia}")
                
               
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
    print("Programa finalizado")

# =============================================================
# Punto de entrada
# =============================================================
if __name__ == "__main__":
    setup()
    loop()
