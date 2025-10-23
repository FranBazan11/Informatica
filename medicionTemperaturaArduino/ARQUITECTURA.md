# 🏗️ Arquitectura del Sistema Unificado

## 📐 Diagrama de la Solución

```
┌─────────────────────────────────────────────────────────────┐
│                  TU CÓDIGO PYTHON                           │
│           monitoreo_temperatura_unificado.py                │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │   Lógica de Negocio (Independiente)             │       │
│  │   - Control de ciclos                           │       │
│  │   - Cálculo de promedios                        │       │
│  │   - Detección de tendencias                     │       │
│  │   - Manejo de pulsador                          │       │
│  └──────────────┬──────────────────────────────────┘       │
│                 │                                           │
│                 │ Usa                                       │
│                 ▼                                           │
│  ┌──────────────────────────────────────────────┐          │
│  │   Interfaz de Hardware (Abstracción)         │          │
│  │   - setup()                                  │          │
│  │   - leer_temperatura()                       │          │
│  │   - leer_boton()                            │          │
│  │   - encender_led()                          │          │
│  └──────────┬─────────────────────────┬─────────┘          │
│             │                         │                     │
│    Detecta automáticamente            │                     │
│             │                         │                     │
│  ┌──────────▼──────────┐   ┌─────────▼──────────┐         │
│  │  RaspberryPiHardware│   │  ArduinoHardware    │         │
│  │  - GPIO directo     │   │  - PyFirmata        │         │
│  │  - SPI (MCP3008)    │   │  - Serial USB       │         │
│  └──────────┬──────────┘   └─────────┬──────────┘         │
└─────────────┼──────────────────────────┼─────────────────────┘
              │                          │
              │                          │
     ┌────────▼────────┐        ┌───────▼────────┐
     │  Raspberry Pi   │        │    Arduino     │
     │                 │        │  + Firmata     │
     │  ┌───────────┐  │        │  ┌──────────┐  │
     │  │ GPIO Pins │  │        │  │  Pins    │  │
     │  │ SPI Bus   │  │        │  │  ADC     │  │
     │  └─────┬─────┘  │        │  └────┬─────┘  │
     └────────┼────────┘        └───────┼────────┘
              │                         │
              │                         │
     ┌────────▼─────────────────────────▼────────┐
     │                                            │
     │         HARDWARE FÍSICO                    │
     │  - LM35 (Sensor de temperatura)           │
     │  - 3 LEDs (Rojo, Amarillo, Verde)         │
     │  - Pulsador                                │
     │  - MCP3008 (solo Raspberry)               │
     │                                            │
     └────────────────────────────────────────────┘
```

---

## 🔄 Flujo de Ejecución

```
1. INICIO
   │
   ├──> Detectar plataforma
   │    ├──> ¿Raspberry Pi disponible?
   │    │    └──> Sí: Usar RaspberryPiHardware
   │    │
   │    └──> ¿Arduino disponible?
   │         └──> Sí: Usar ArduinoHardware
   │
2. CONFIGURAR HARDWARE
   │
   ├──> Raspberry Pi:
   │    ├─> Inicializar GPIO (BCM)
   │    ├─> Abrir SPI para MCP3008
   │    └─> Configurar pines
   │
   └──> Arduino:
        ├─> Conectar via puerto serial
        ├─> Obtener pines digitales/analógicos
        └─> Esperar inicialización
   │
3. BUCLE PRINCIPAL
   │
   ├──> Verificar pulsador
   │    ├──> ¿Presionado?
   │    │    ├─> < 1s: Terminar programa
   │    │    ├─> 1-2.5s: Ciclo 2.5s
   │    │    ├─> 2.5-10s: Ciclo = duración
   │    │    └─> > 10s: Ciclo 10s
   │    │
   ├──> Medir temperatura (cada ciclo)
   │    ├─> Leer sensor
   │    ├─> Calcular promedio
   │    ├─> Determinar tendencia
   │    └─> Controlar LEDs
   │    
   └──> Repetir
   │
4. FIN
   └──> Limpiar recursos
        ├─> Apagar LEDs
        ├─> Cerrar GPIO/SPI (Raspberry)
        └─> Cerrar conexión serial (Arduino)
```

---

## 🔌 Capas de Abstracción

### Capa 1: Lógica de Aplicación
```python
class MonitorTemperatura:
    # Toda la lógica del negocio
    # No sabe NADA sobre hardware específico
    # Solo usa la interfaz abstracta
```

**Ventajas:**
- ✅ Código reutilizable
- ✅ Fácil de probar
- ✅ Fácil de mantener

### Capa 2: Interfaz Abstracta
```python
class HardwareInterface:
    # Define QUÉ se debe hacer
    # No define CÓMO se hace
    def leer_temperatura(self): ...
    def encender_led(self, pin, estado): ...
```

**Ventajas:**
- ✅ Contrato claro
- ✅ Intercambiable
- ✅ Extensible

### Capa 3: Implementaciones Concretas
```python
class RaspberryPiHardware(HardwareInterface):
    # Define CÓMO se hace en Raspberry Pi
    
class ArduinoHardware(HardwareInterface):
    # Define CÓMO se hace en Arduino
```

**Ventajas:**
- ✅ Código específico aislado
- ✅ Fácil agregar nuevas plataformas
- ✅ Cambios en una no afectan la otra

---

## 🔀 Diferencias entre Plataformas

### Lectura de Temperatura

**Raspberry Pi:**
```python
def leer_temperatura(self):
    # 1. Leer MCP3008 via SPI
    lectura = self._leer_adc(0)
    
    # 2. Convertir a voltaje (3.3V referencia)
    voltaje = (lectura * 3.3) / 1023.0
    
    # 3. LM35: 10mV/°C
    temperatura = voltaje / 0.01
    
    return temperatura, lectura
```

**Arduino:**
```python
def leer_temperatura(self):
    # 1. Leer pin analógico (0.0 a 1.0)
    valor = self.analog_pin.read()
    
    # 2. Convertir a ADC de 10 bits
    lectura = int(valor * 1023)
    
    # 3. Convertir a voltaje (5V referencia)
    voltaje = (lectura * 5.0) / 1023.0
    
    # 4. LM35: 10mV/°C
    temperatura = voltaje / 0.01
    
    return temperatura, lectura
```

**Diferencias clave:**
- 📍 Raspberry: SPI → MCP3008 → lectura directa ADC
- 📍 Arduino: Firmata → valor normalizado (0-1)
- ⚡ Raspberry: 3.3V referencia (¡cuidado!)
- ⚡ Arduino: 5V referencia

---

## 🎯 Patrón de Diseño: Strategy Pattern

Este código usa el **Strategy Pattern**:

```
┌─────────────────────────────────┐
│      MonitorTemperatura         │
│  (Contexto - usa estrategia)    │
│                                 │
│  + hardware: HardwareInterface  │◄─────┐
│  + medir_temperatura()          │      │
│  + manejar_pulsador()           │      │
└─────────────────────────────────┘      │
                                         │ usa
                                         │
┌─────────────────────────────────┐      │
│     HardwareInterface           │◄─────┘
│  (Estrategia abstracta)         │
│                                 │
│  + setup()                      │
│  + leer_temperatura()           │
│  + leer_boton()                 │
│  + encender_led()               │
└──────────────┬──────────────────┘
               │ implementan
       ┌───────┴────────┐
       │                │
┌──────▼────────┐  ┌───▼────────────┐
│ RaspberryPi   │  │ Arduino        │
│ Hardware      │  │ Hardware       │
│ (Estrategia   │  │ (Estrategia    │
│  concreta)    │  │  concreta)     │
└───────────────┘  └────────────────┘
```

**Beneficios:**
- ✅ Algoritmo intercambiable en runtime
- ✅ Código cliente no cambia
- ✅ Fácil agregar nuevas estrategias (ESP32, Micro:bit, etc.)

---

## 🆚 Comparación: .ino vs Python Unificado

### Código Arduino Original (.ino)
```
┌──────────────────────────────────┐
│   medicionTemperatura.ino        │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Código C++ para Arduino    │  │
│  │ - Compilado a binario      │  │
│  │ - Corre EN el Arduino      │  │
│  │ - No necesita PC           │  │
│  └────────────────────────────┘  │
└──────────────┬───────────────────┘
               │
               ▼
         ┌─────────┐
         │ Arduino │
         │ (solo)  │
         └─────────┘
```

### Código Python Unificado
```
┌──────────────────────────────────┐
│  PC o Raspberry Pi               │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Python (interpretado)      │  │
│  │ - Corre en PC/Raspberry    │  │
│  │ - Controla Arduino via USB │  │
│  │ - O GPIO directo (RPI)     │  │
│  └───────────┬────────────────┘  │
└──────────────┼───────────────────┘
               │
       ┌───────┴────────┐
       │                │
  ┌────▼─────┐    ┌─────▼──────┐
  │ Arduino  │    │ Raspberry  │
  │ +Firmata │    │ Pi (solo)  │
  └──────────┘    └────────────┘
```

---

## 🚀 Agregar Nueva Plataforma (ESP32, Micro:bit, etc.)

Gracias a la arquitectura, agregar soporte para nuevo hardware es simple:

```python
class ESP32Hardware(HardwareInterface):
    """Implementación para ESP32"""
    
    def setup(self):
        # Configurar ESP32
        pass
    
    def leer_temperatura(self):
        # Leer ADC del ESP32
        pass
    
    def leer_boton(self):
        # Leer GPIO del ESP32
        pass
    
    def encender_led(self, pin, estado):
        # Controlar LED del ESP32
        pass
```

Solo necesitas:
1. ✅ Implementar las 4 funciones
2. ✅ Agregar detección en `detectar_plataforma()`
3. ✅ ¡Listo! El resto del código funciona igual

---

## 📚 Conceptos de Programación Aplicados

### 1. Abstracción
Ocultar detalles complejos del hardware detrás de una interfaz simple.

### 2. Polimorfismo
Mismo método (`leer_temperatura()`) funciona diferente en cada plataforma.

### 3. Encapsulación
Cada clase maneja sus propios detalles internos.

### 4. Separación de Responsabilidades
- `MonitorTemperatura`: lógica de negocio
- `HardwareInterface`: contrato
- `*Hardware`: implementaciones específicas

### 5. Inyección de Dependencias
```python
monitor = MonitorTemperatura(hardware)
# hardware puede ser cualquier implementación
```

---

## 💡 Conclusión

Este diseño te da:

✅ **Flexibilidad**: Cambiar hardware sin cambiar lógica
✅ **Mantenibilidad**: Código organizado y claro
✅ **Escalabilidad**: Fácil agregar nuevas plataformas
✅ **Reutilización**: La lógica sirve para cualquier hardware
✅ **Testeo**: Puedes crear un `MockHardware` para pruebas

Es la diferencia entre:
- ❌ Copiar y pegar código para cada plataforma
- ✅ Escribir la lógica una vez y reutilizarla

**¡Esto es ingeniería de software real!** 🎯
