#!/usr/bin/env python3
# =============================================================
#  Estacion de Monitoreo de Temperatura - VERSION UNIFICADA
#  Autor: Juan Francisco Bazan Carrizo
#  Descripcion:
#  Un solo codigo Python que funciona en:
#  1. Raspberry Pi (GPIO directo)
#  2. Arduino (via Firmata/pySerial)
#  
#  El programa detecta automaticamente el hardware disponible.
# =============================================================

import time
import sys
from collections import deque

# =============================================================
# Deteccion automatica de plataforma
# =============================================================
PLATAFORMA = None
gpio = None
spi = None
board = None

def detectar_plataforma():
    """Detecta si estamos en Raspberry Pi o usando Arduino"""
    global PLATAFORMA, gpio, spi, board
    
    # Intentar importar RPi.GPIO (Raspberry Pi)
    try:
        import RPi.GPIO as GPIO
        import spidev
        gpio = GPIO
        spi = spidev.SpiDev()
        PLATAFORMA = "RASPBERRY_PI"
        print("✓ Raspberry Pi detectada")
        return True
    except (ImportError, RuntimeError):
        pass
    
    # Intentar conectar con Arduino via pyfirmata
    try:
        from pyfirmata import Arduino, util
        import serial.tools.list_ports
        
        # Buscar puerto Arduino
        ports = list(serial.tools.list_ports.comports())
        arduino_port = None
        
        for port in ports:
            # Buscar puertos que parezcan Arduino
            if 'Arduino' in port.description or 'ttyACM' in port.device or 'ttyUSB' in port.device or 'cu.usbmodem' in port.device or 'cu.usbserial' in port.device:
                arduino_port = port.device
                break
        
        if arduino_port:
            print(f"✓ Arduino detectado en {arduino_port}")
            board = Arduino(arduino_port)
            # Iniciar el iterator para leer pines analogicos
            it = util.Iterator(board)
            it.start()
            PLATAFORMA = "ARDUINO"
            return True
        else:
            print("✗ No se encontró Arduino conectado")
            return False
            
    except ImportError:
        print("✗ PyFirmata no instalado. Instala con: pip install pyfirmata")
        return False
    except Exception as e:
        print(f"✗ Error al conectar con Arduino: {e}")
        return False

# =============================================================
# Clase abstracta para hardware
# =============================================================
class HardwareInterface:
    """Interfaz unificada para controlar hardware"""
    
    def __init__(self):
        self.BTN_PIN = 2
        self.LED_R = 11
        self.LED_Y = 10
        self.LED_G = 9
        
    def setup(self):
        raise NotImplementedError
    
    def leer_temperatura(self):
        raise NotImplementedError
    
    def leer_boton(self):
        raise NotImplementedError
    
    def encender_led(self, pin, estado):
        raise NotImplementedError
    
    def cleanup(self):
        raise NotImplementedError

# =============================================================
# Implementacion para Raspberry Pi
# =============================================================
class RaspberryPiHardware(HardwareInterface):
    """Control de hardware para Raspberry Pi"""
    
    def __init__(self):
        super().__init__()
        self.spi = spidev.SpiDev()
        
    def setup(self):
        """Configura GPIO y SPI"""
        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)
        
        gpio.setup(self.BTN_PIN, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        gpio.setup(self.LED_R, gpio.OUT)
        gpio.setup(self.LED_Y, gpio.OUT)
        gpio.setup(self.LED_G, gpio.OUT)
        
        # Configurar SPI para MCP3008
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 1350000
        
    def _leer_adc(self, canal):
        """Lee el MCP3008"""
        if canal < 0 or canal > 7:
            return -1
        adc = self.spi.xfer2([1, (8 + canal) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
        
    def leer_temperatura(self):
        """Lee temperatura del LM35 via MCP3008"""
        lectura = self._leer_adc(0)
        voltaje_ref = 3.3  # Ajusta segun tu circuito
        voltaje = (lectura * voltaje_ref) / 1023.0
        temperatura = voltaje / 0.01
        return temperatura, lectura
    
    def leer_boton(self):
        """Lee estado del boton"""
        return gpio.input(self.BTN_PIN) == gpio.HIGH
    
    def encender_led(self, pin, estado):
        """Enciende/apaga un LED"""
        gpio.output(pin, gpio.HIGH if estado else gpio.LOW)
    
    def cleanup(self):
        """Limpia recursos"""
        self.encender_led(self.LED_R, False)
        self.encender_led(self.LED_Y, False)
        self.encender_led(self.LED_G, False)
        gpio.cleanup()
        self.spi.close()

# =============================================================
# Implementacion para Arduino (via Firmata)
# =============================================================
class ArduinoHardware(HardwareInterface):
    """Control de hardware para Arduino via Firmata"""
    
    def __init__(self, board):
        super().__init__()
        self.board = board
        self.LM35_PIN = 0  # A0
        self.analog_pin = None
        
    def setup(self):
        """Configura pines de Arduino"""
        # Pin analogico para LM35
        self.analog_pin = self.board.get_pin(f'a:{self.LM35_PIN}:i')
        
        # Pines digitales para LEDs (modo OUTPUT)
        self.led_r = self.board.get_pin(f'd:{self.LED_R}:o')
        self.led_y = self.board.get_pin(f'd:{self.LED_Y}:o')
        self.led_g = self.board.get_pin(f'd:{self.LED_G}:o')
        
        # Pin digital para boton (modo INPUT)
        self.boton = self.board.get_pin(f'd:{self.BTN_PIN}:i')
        
        # Esperar a que se inicialicen los pines
        time.sleep(2)
        
    def leer_temperatura(self):
        """Lee temperatura del LM35"""
        # Leer valor analogico (0.0 a 1.0)
        valor = self.analog_pin.read()
        
        # Manejar lecturas None (primeras lecturas)
        if valor is None:
            time.sleep(0.1)
            valor = self.analog_pin.read()
            if valor is None:
                valor = 0.5  # Valor por defecto
        
        # Convertir a lectura ADC de 10 bits (0-1023)
        lectura = int(valor * 1023)
        
        # Convertir a temperatura (LM35: 10mV/°C, ref 5V)
        voltaje = (lectura * 5.0) / 1023.0
        temperatura = voltaje / 0.01
        
        return temperatura, lectura
    
    def leer_boton(self):
        """Lee estado del boton"""
        valor = self.boton.read()
        return valor == 1 if valor is not None else False
    
    def encender_led(self, pin, estado):
        """Enciende/apaga un LED"""
        if pin == self.LED_R:
            self.led_r.write(1 if estado else 0)
        elif pin == self.LED_Y:
            self.led_y.write(1 if estado else 0)
        elif pin == self.LED_G:
            self.led_g.write(1 if estado else 0)
    
    def cleanup(self):
        """Limpia recursos"""
        self.encender_led(self.LED_R, False)
        self.encender_led(self.LED_Y, False)
        self.encender_led(self.LED_G, False)
        self.board.exit()

# =============================================================
# Logica principal (independiente del hardware)
# =============================================================
class MonitorTemperatura:
    """Logica de monitoreo de temperatura"""
    
    def __init__(self, hardware):
        self.hw = hardware
        self.X = 0.07  # Margen de variacion 7%
        self.N = 5     # Cantidad de muestras
        self.lecturas = deque(maxlen=self.N)
        self.promedio = 0.0
        self.ciclo = 3.5  # Ciclo inicial en segundos
        self.t0 = 0
        
    def encender_todos(self):
        """Enciende todos los LEDs"""
        self.hw.encender_led(self.hw.LED_R, True)
        self.hw.encender_led(self.hw.LED_Y, True)
        self.hw.encender_led(self.hw.LED_G, True)
    
    def apagar_todos(self):
        """Apaga todos los LEDs"""
        self.hw.encender_led(self.hw.LED_R, False)
        self.hw.encender_led(self.hw.LED_Y, False)
        self.hw.encender_led(self.hw.LED_G, False)
    
    def encender_uno(self, led):
        """Enciende solo un LED"""
        self.apagar_todos()
        self.hw.encender_led(led, True)
    
    def destellar(self):
        """Destella todos los LEDs"""
        self.encender_todos()
        time.sleep(0.05)
        self.apagar_todos()
    
    def promedio_n(self):
        """Calcula promedio de lecturas"""
        if len(self.lecturas) == 0:
            return 0.0
        return sum(self.lecturas) / len(self.lecturas)
    
    def manejar_pulsador(self):
        """Maneja la logica del pulsador"""
        if self.hw.leer_boton():
            print("Boton presionado detectado")
            time.sleep(0.02)  # Antirrebote
            
            if self.hw.leer_boton():  # Confirmacion
                print("Confirmacion de boton presionado")
                presionado = time.time()
                
                # Esperar hasta que se suelte
                while self.hw.leer_boton():
                    tiempo_transcurrido = time.time() - presionado
                    if int(tiempo_transcurrido * 1000) % 1000 < 50:
                        self.destellar()
                    time.sleep(0.01)
                
                segundos_press = time.time() - presionado
                print(f"Duracion de pulsacion: {segundos_press:.2f} s")
                
                # Determinar accion
                if segundos_press < 1.0:
                    print("Pulsacion corta: fin del monitoreo.")
                    self.encender_todos()
                    return "TERMINAR"
                elif segundos_press < 2.5:
                    self.ciclo = 2.5
                    print("Nuevo ciclo: 2.5 s")
                elif segundos_press <= 10.0:
                    self.ciclo = segundos_press
                    print(f"Nuevo ciclo: {self.ciclo:.2f} s")
                else:
                    self.ciclo = 10.0
                    print("Pulsacion larga: ciclo limitado a 10 s")
                
                print("-------------------------------------------")
        
        return "CONTINUAR"
    
    def medir_temperatura(self):
        """Realiza medicion de temperatura"""
        tiempo_actual = time.time()
        
        if tiempo_actual - self.t0 >= self.ciclo:
            self.t0 = tiempo_actual
            temperatura, lectura = self.hw.leer_temperatura()
            
            print()
            print("------ NUEVO CICLO DE MEDICION ------")
            print(f"Lectura analogica: {lectura}")
            print(f"Temperatura: {temperatura:.2f} C")
            
            # Actualizar buffer
            self.lecturas.append(temperatura)
            self.promedio = self.promedio_n()
            
            print(f"Promedio ultimas {len(self.lecturas)} lecturas: {self.promedio:.2f} C")
            
            # Determinar tendencia
            if len(self.lecturas) < self.N:
                tendencia = "INSUFICIENTE"
                self.encender_todos()
                print("No hay suficientes datos para calcular tendencia.")
            else:
                diff = temperatura - self.promedio
                if diff > self.promedio * self.X:
                    tendencia = "ALZA"
                    self.encender_uno(self.hw.LED_R)
                elif diff < -self.promedio * self.X:
                    tendencia = "BAJA"
                    self.encender_uno(self.hw.LED_G)
                else:
                    tendencia = "ESTABLE"
                    self.encender_uno(self.hw.LED_Y)
                
                print(f"Diferencia: {diff:.3f}")
                print(f"Tendencia: {tendencia}")
            
            self.destellar()
            print(f"Ciclo de {self.ciclo:.2f} s completado.")
            print("-------------------------------------------")
    
    def iniciar(self):
        """Inicia el monitoreo"""
        print("===========================================")
        print(" Estacion de Monitoreo de Temperatura")
        print(f" Plataforma: {PLATAFORMA}")
        print("===========================================")
        print(f"Ciclo inicial: {self.ciclo} s")
        
        self.encender_todos()
        time.sleep(1)
        self.apagar_todos()
        
        self.t0 = time.time()
        
        try:
            while True:
                # Manejar pulsador
                resultado = self.manejar_pulsador()
                if resultado == "TERMINAR":
                    break
                
                # Medir temperatura
                self.medir_temperatura()
                
                # Pausa pequeña
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nPrograma interrumpido por el usuario")
        finally:
            self.hw.cleanup()
            print("Programa finalizado")

# =============================================================
# Punto de entrada principal
# =============================================================
def main():
    """Funcion principal"""
    print("===========================================")
    print(" Sistema de Monitoreo de Temperatura")
    print(" Version Unificada Python")
    print("===========================================")
    print()
    print("Detectando hardware...")
    
    if not detectar_plataforma():
        print("\n✗ No se pudo detectar hardware compatible")
        print("\nOpciones:")
        print("1. Raspberry Pi: Instala RPi.GPIO y spidev")
        print("   sudo pip3 install RPi.GPIO spidev")
        print()
        print("2. Arduino: Instala pyfirmata y carga StandardFirmata")
        print("   pip install pyfirmata")
        print("   En Arduino IDE: File → Examples → Firmata → StandardFirmata")
        sys.exit(1)
    
    # Crear instancia de hardware apropiada
    if PLATAFORMA == "RASPBERRY_PI":
        hardware = RaspberryPiHardware()
    else:  # ARDUINO
        hardware = ArduinoHardware(board)
    
    # Configurar hardware
    print("Configurando hardware...")
    hardware.setup()
    
    # Crear e iniciar monitor
    monitor = MonitorTemperatura(hardware)
    monitor.iniciar()

if __name__ == "__main__":
    main()
