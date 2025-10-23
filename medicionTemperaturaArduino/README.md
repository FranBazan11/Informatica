# Estación de Monitoreo de Temperatura

Sistema de monitoreo de temperatura con dos implementaciones:
1. **Arduino** - Hardware standalone
2. **Raspberry Pi** - Python con GPIO

---

## 📋 Características

- Medición continua de temperatura con sensor LM35
- Control de ciclo de muestreo mediante pulsador
- Indicadores LED de tendencia térmica:
  - 🔴 **Rojo**: Temperatura en ALZA
  - 🟡 **Amarillo**: Temperatura ESTABLE
  - 🟢 **Verde**: Temperatura en BAJA
- Promedio móvil de últimas 5 lecturas
- Ciclo de muestreo ajustable (2.5s - 10s)

---

## 🔧 Implementación Arduino

### Hardware necesario
- Arduino Uno/Nano/Mega
- Sensor LM35
- 3 LEDs (Rojo, Amarillo, Verde)
- 3 Resistencias 220Ω
- Pulsador
- Resistencia 10kΩ (pull-down)
- Protoboard y cables

### Conexiones
```
LM35:
  - Vout → A0
  - VCC → 5V
  - GND → GND

Pulsador:
  - Un terminal → GPIO 2
  - Otro terminal → GND
  
LEDs:
  - LED Rojo → GPIO 11 (con resistencia 220Ω)
  - LED Amarillo → GPIO 10 (con resistencia 220Ω)
  - LED Verde → GPIO 9 (con resistencia 220Ω)
```

### Instalación
1. Abre Arduino IDE
2. Abre el archivo `medicionTemperaturaArduino.ino`
3. Selecciona tu placa en Tools → Board
4. Selecciona el puerto en Tools → Port
5. Sube el código (Ctrl+U)

### Uso
- **Pulsación < 1s**: Finaliza el monitoreo
- **Pulsación 1s - 2.5s**: Ciclo de 2.5s
- **Pulsación 2.5s - 10s**: Ciclo igual a duración
- **Pulsación > 10s**: Ciclo de 10s

---

## 🍓 Implementación Raspberry Pi

### Hardware necesario
- Raspberry Pi (cualquier modelo con GPIO)
- MCP3008 (Conversor ADC de 10 bits)
- Sensor LM35
- 3 LEDs (Rojo, Amarillo, Verde)
- 3 Resistencias 220Ω
- Pulsador
- Resistencia 10kΩ (pull-down)
- Protoboard y cables

### Conexiones

#### MCP3008 (ADC) → Raspberry Pi
```
MCP3008          Raspberry Pi
VDD     (16) →   3.3V
VREF    (15) →   3.3V
AGND    (14) →   GND
CLK     (13) →   GPIO 11 (SCLK)
DOUT    (12) →   GPIO 9  (MISO)
DIN     (11) →   GPIO 10 (MOSI)
CS/SHDN (10) →   GPIO 8  (CE0)
DGND    (9)  →   GND
CH0     (1)  →   LM35 Vout
```

#### LM35 → MCP3008
```
LM35:
  - Vout → Canal 0 del MCP3008
  - VCC → 3.3V o 5V
  - GND → GND
```

#### Otros componentes → Raspberry Pi
```
Pulsador:
  - Un terminal → GPIO 2
  - Otro terminal → GND
  
LEDs:
  - LED Rojo → GPIO 11 (con resistencia 220Ω)
  - LED Amarillo → GPIO 10 (con resistencia 220Ω)
  - LED Verde → GPIO 9 (con resistencia 220Ω)
```

### Instalación

1. **Habilitar SPI en la Raspberry Pi**
```bash
sudo raspi-config
# Navega a: Interface Options → SPI → Enable
# Reinicia la Raspberry Pi
```

2. **Instalar dependencias**
```bash
# Actualizar sistema
sudo apt-get update
sudo apt-get upgrade

# Instalar Python 3 y pip (si no están instalados)
sudo apt-get install python3 python3-pip

# Instalar librerías necesarias
sudo pip3 install RPi.GPIO spidev
```

3. **Copiar el archivo Python**
```bash
# Copia el archivo a tu Raspberry Pi
scp monitoreo_temperatura_raspberry.py pi@<IP_DE_TU_RPI>:~/
```

4. **Dar permisos de ejecución**
```bash
chmod +x monitoreo_temperatura_raspberry.py
```

### Ejecución
```bash
# Ejecutar el programa
sudo python3 monitoreo_temperatura_raspberry.py

# O directamente si tiene permisos
sudo ./monitoreo_temperatura_raspberry.py
```

**Nota**: Se necesita `sudo` para acceder a los pines GPIO.

### Uso
El funcionamiento es idéntico a la versión Arduino:
- **Pulsación < 1s**: Finaliza el monitoreo
- **Pulsación 1s - 2.5s**: Ciclo de 2.5s
- **Pulsación 2.5s - 10s**: Ciclo igual a duración
- **Pulsación > 10s**: Ciclo de 10s

---

## ⚙️ Configuración

### Ajustar voltaje de referencia (Raspberry Pi)
En el archivo `monitoreo_temperatura_raspberry.py`, línea 60:
```python
voltaje_ref = 3.3  # Cambia a 5.0 si usas 5V
```

### Ajustar margen de variación
En ambos archivos, modifica la constante `X`:
```cpp
// Arduino
const float X = 0.07;   // 7% de margen
```
```python
# Raspberry Pi
X = 0.07  # 7% de margen
```

---

## 🐛 Solución de problemas

### Arduino
- **No se detecta el puerto**: Verifica drivers USB
- **Lecturas erráticas**: Verifica conexión del LM35
- **LEDs no encienden**: Verifica resistencias y polaridad

### Raspberry Pi
- **Error "SPI not enabled"**: Habilita SPI con `raspi-config`
- **Error "Permission denied"**: Ejecuta con `sudo`
- **Lecturas incorrectas**: 
  - Verifica conexiones del MCP3008
  - Verifica voltaje de referencia en el código
  - Verifica que SPI esté funcionando: `ls /dev/spi*`
- **No detecta pulsador**: Verifica pull-down resistor

---

## 📊 Salida del programa

Ambas versiones muestran información en el monitor serial/terminal:
```
===========================================
 Estacion de Monitoreo de Temperatura 
===========================================
Ciclo inicial: 3.5 s

------ NUEVO CICLO DE MEDICION ------
Lectura analogica: 512
Temperatura: 25.00 C
Promedio ultimas 5 lecturas: 24.85 C
Diferencia: 0.150
Tendencia: ESTABLE
Ciclo de 3.5 s completado.
-------------------------------------------
```

---

## 📝 Notas

- La Raspberry Pi requiere un ADC externo (MCP3008) porque no tiene pines analógicos
- El Arduino tiene ADC integrado de 10 bits (0-1023)
- Ambas versiones mantienen la misma lógica y funcionalidad
- Para sistemas de producción, considera agregar calibración del sensor

---

## 👤 Autor

Juan Francisco Bazan Carrizo

## 📄 Licencia

Código libre para uso educativo.
