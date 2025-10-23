import time
import RPi.GPIO as GPIO
import spidev   # para leer ADC MCP3008

# =========================
# Configuración de pines
# =========================
LED_R = 17
LED_Y = 27
LED_G = 22
BUTTON = 4
LM35_CH = 0  # canal del MCP3008 conectado al LM35

# =========================
# Parámetros del sistema
# =========================
X = 0.07
N = 5
lecturas = []
ciclo = 3.5
t0 = time.time()

# =========================
# Inicialización GPIO
# =========================
GPIO.setmode(GPIO.BCM)
GPIO.setup([LED_R, LED_Y, LED_G], GPIO.OUT)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# =========================
# Inicialización SPI (ADC)
# =========================
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

def leer_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def leer_temperatura():
    lectura = leer_adc(LM35_CH)
    voltaje = lectura * 3.3 / 1023
    temp_c = voltaje / 0.01  # 10mV/°C
    return temp_c

# =========================
# Funciones auxiliares
# =========================
def promedioN(datos):
    return sum(datos) / len(datos)

def encenderTodos():
    GPIO.output([LED_R, LED_Y, LED_G], GPIO.HIGH)

def apagarTodos():
    GPIO.output([LED_R, LED_Y, LED_G], GPIO.LOW)

def encenderUno(pin):
    apagarTodos()
    GPIO.output(pin, GPIO.HIGH)

def destellar():
    encenderTodos()
    time.sleep(0.05)
    apagarTodos()

# =========================
# Bucle principal
# =========================
print("=====================================")
print("Estacion de Monitoreo de Temperatura")
print("=====================================")
print(f"Ciclo inicial: {ciclo} s")

try:
    while True:
        # --- leer botón ---
        if GPIO.input(BUTTON) == GPIO.LOW:
            t_presionado = time.time()
            while GPIO.input(BUTTON) == GPIO.LOW:
                destellar()
                time.sleep(1)
            duracion = time.time() - t_presionado
            print(f"Pulsacion de {duracion:.2f}s")

            if duracion < 1:
                print("Pulsacion corta: fin del monitoreo")
                encenderTodos()
                break
            elif duracion < 2.5:
                ciclo = 2.5
            elif duracion <= 10:
                ciclo = duracion
            else:
                ciclo = 10
            print(f"Nuevo ciclo: {ciclo:.2f}s")

        # --- medir temperatura ---
        if time.time() - t0 >= ciclo:
            t0 = time.time()
            temp = leer_temperatura()
            lecturas.append(temp)
            if len(lecturas) > N:
                lecturas.pop(0)
            promedio = promedioN(lecturas)

            print(f"\nTemperatura: {temp:.2f}°C | Promedio: {promedio:.2f}°C")

            if len(lecturas) < N:
                encenderTodos()
                print("No hay suficientes datos aún.")
            else:
                diff = temp - promedio
                if diff > promedio * X:
                    encenderUno(LED_R)
                    print("Tendencia: ALZA")
                elif diff < -promedio * X:
                    encenderUno(LED_G)
                    print("Tendencia: BAJA")
                else:
                    encenderUno(LED_Y)
                    print("Tendencia: ESTABLE")

            destellar()
            print(f"Ciclo de {ciclo:.2f}s completado.")
except KeyboardInterrupt:
    GPIO.cleanup()
    spi.close()
    print("Programa finalizado.")