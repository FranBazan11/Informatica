# 🚀 Guía de Configuración - Código Python Unificado

## 📋 Descripción

Este proyecto te permite usar **un solo código Python** que funciona tanto en:
- ✅ **Raspberry Pi** (control directo de GPIO)
- ✅ **Arduino** (mediante protocolo Firmata)

El código **detecta automáticamente** el hardware disponible.

---

## 🔧 Configuración para Arduino

### Paso 1: Cargar StandardFirmata en el Arduino

Para usar Python con Arduino, necesitas cargar el firmware **StandardFirmata** que permite controlar el Arduino desde Python.

1. **Abre Arduino IDE**
2. **Ve a:** `File` → `Examples` → `Firmata` → `StandardFirmata`
3. **Selecciona tu placa:** `Tools` → `Board` → `Arduino Uno/Nano/Mega`
4. **Selecciona el puerto:** `Tools` → `Port` → (tu puerto Arduino)
5. **Sube el código:** Click en el botón `Upload` (→)

✅ Ahora tu Arduino puede ser controlado desde Python!

### Paso 2: Instalar PyFirmata

En tu computadora (Mac/Windows/Linux):

```bash
# Instalar pyfirmata
pip install pyfirmata

# También instala pyserial (si no está instalado)
pip install pyserial
```

### Paso 3: Conectar el Hardware

Las conexiones son **idénticas** al código Arduino original:

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

### Paso 4: Ejecutar el código Python

```bash
python3 monitoreo_temperatura_unificado.py
```

El programa detectará automáticamente el Arduino conectado! 🎉

---

## 🍓 Configuración para Raspberry Pi

### Paso 1: Habilitar SPI

```bash
sudo raspi-config
# Navega a: Interface Options → SPI → Enable
# Reinicia
```

### Paso 2: Instalar librerías

```bash
sudo pip3 install RPi.GPIO spidev
```

### Paso 3: Conectar el Hardware

**Necesitas el MCP3008** (ADC) porque la Raspberry Pi no tiene pines analógicos:

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

Pulsador y LEDs: igual que Arduino
```

### Paso 4: Ejecutar el código Python

```bash
sudo python3 monitoreo_temperatura_unificado.py
```

⚠️ Necesitas `sudo` para acceder a GPIO

---

## 🎯 Ventajas del Código Unificado

### ✅ Un solo código Python
- No necesitas mantener dos versiones
- La lógica es idéntica en ambas plataformas
- Fácil de modificar y probar

### ✅ Detección automática
- El código detecta si está en Raspberry Pi o Arduino
- No necesitas cambiar nada en el código
- Solo conecta y ejecuta

### ✅ Misma funcionalidad
- Ciclos de muestreo ajustables
- Indicadores LED de tendencia
- Control por pulsador
- Todo funciona igual

---

## 📊 Comparación de Plataformas

| Característica | Arduino + Firmata | Raspberry Pi |
|----------------|-------------------|--------------|
| **Instalación** | Más pasos (Firmata + Python) | Menos pasos |
| **Conexiones** | Más simple (ADC integrado) | MCP3008 necesario |
| **Portabilidad** | USB a cualquier PC | Standalone |
| **Procesamiento** | Limitado | Más potente |
| **Costo** | Más barato | Más caro |
| **Ideal para** | Prototipado rápido | Proyectos complejos |

---

## 🐛 Solución de Problemas

### Arduino no detectado

**Problema:** `No se encontró Arduino conectado`

**Soluciones:**
1. Verifica que StandardFirmata esté cargado
2. Verifica la conexión USB
3. Verifica permisos del puerto:
   ```bash
   # Linux/Mac
   sudo chmod 666 /dev/ttyACM0
   # O agrega tu usuario al grupo dialout
   sudo usermod -a -G dialout $USER
   ```
4. Lista puertos disponibles:
   ```bash
   python3 -m serial.tools.list_ports
   ```

### Lecturas incorrectas en Arduino

**Problema:** Temperatura muy alta/baja o erratica

**Soluciones:**
1. Verifica conexión del LM35
2. Espera ~5 segundos después de iniciar (primeras lecturas pueden ser None)
3. Verifica que StandardFirmata esté correctamente cargado
4. El código tiene protección contra lecturas None

### Error en Raspberry Pi

**Problema:** `SPI not enabled` o `Permission denied`

**Soluciones:**
1. Habilita SPI: `sudo raspi-config`
2. Ejecuta con sudo: `sudo python3 ...`
3. Verifica MCP3008 correctamente conectado
4. Verifica SPI funcionando: `ls /dev/spi*`

---

## 💡 Migración desde Arduino IDE

Si ya tenías el código `.ino` funcionando:

### ¿Qué cambió?
- ✅ La **lógica** es idéntica
- ✅ Los **pines** son los mismos
- ✅ Las **conexiones** no cambian
- ⚠️ Solo necesitas cargar StandardFirmata

### ¿Qué ganas?
- 🐍 Puedes usar Python (librerías, análisis de datos, web, etc.)
- 📊 Puedes guardar datos fácilmente
- 🌐 Puedes conectar a internet/base de datos
- 🔄 Puedes cambiar entre Arduino y Raspberry sin cambiar código

---

## 📝 Ejemplo de Uso

```bash
# Conecta tu Arduino con StandardFirmata
# O prepara tu Raspberry Pi

python3 monitoreo_temperatura_unificado.py

# Salida:
===========================================
 Sistema de Monitoreo de Temperatura
 Version Unificada Python
===========================================

Detectando hardware...
✓ Arduino detectado en /dev/ttyACM0
Configurando hardware...
===========================================
 Estacion de Monitoreo de Temperatura
 Plataforma: ARDUINO
===========================================
Ciclo inicial: 3.5 s

------ NUEVO CICLO DE MEDICION ------
Lectura analogica: 512
Temperatura: 25.00 C
...
```

---

## 🎓 Conceptos Importantes

### ¿Qué es Firmata?
Firmata es un **protocolo de comunicación** que permite controlar Arduino desde otros lenguajes (Python, Node.js, etc.). Es como un "traductor" entre Python y el Arduino.

### ¿Por qué usar Python en vez del .ino?
- **Más librerías**: pandas, matplotlib, requests, etc.
- **Más fácil**: sintaxis más simple
- **Más portable**: mismo código en diferentes hardware
- **Mejor para datos**: guardar, analizar, visualizar

### ¿Cuándo usar .ino directo?
- Proyectos standalone (sin PC conectada)
- Necesitas máxima velocidad
- Recursos muy limitados
- No necesitas las ventajas de Python

---

## 🔄 Próximos pasos

Una vez que funcione, puedes agregar:

1. **Guardar datos en archivo CSV**
   ```python
   import csv
   # Guardar temperatura, timestamp, tendencia
   ```

2. **Graficar en tiempo real**
   ```python
   import matplotlib.pyplot as plt
   # Graficar temperatura vs tiempo
   ```

3. **Enviar a base de datos**
   ```python
   import sqlite3
   # O PostgreSQL, MySQL, etc.
   ```

4. **Crear interfaz web**
   ```python
   from flask import Flask
   # Ver temperatura desde navegador
   ```

5. **Alertas por email/SMS**
   ```python
   import smtplib
   # Alertar si temperatura muy alta
   ```

---

## 👤 Autor

Juan Francisco Bazan Carrizo

## 📄 Licencia

Código libre para uso educativo.
