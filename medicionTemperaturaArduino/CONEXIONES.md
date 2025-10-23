# Diagrama de Conexiones

## Esquema Arduino

```
                     +5V
                      |
                      |
                   [LM35]
                      |
                    Vout
                      |
                      +--> A0 (Arduino)
                      
    +5V              GND
     |                |
     |                |
  [Botón] ----+---> GND
              |
            GPIO 2 (Arduino)
            
    LED Rojo (+) ---[220Ω]--- GPIO 11
    LED Rojo (-) --------------- GND
    
    LED Amarillo (+) ---[220Ω]--- GPIO 10
    LED Amarillo (-) ---------------- GND
    
    LED Verde (+) ---[220Ω]--- GPIO 9
    LED Verde (-) --------------- GND
```

## Esquema Raspberry Pi con MCP3008

```
Raspberry Pi GPIO:
                    3.3V/5V
                      |
                   [LM35]
                      |
                    Vout
                      |
                      +--> CH0 (MCP3008 pin 1)
                      

          MCP3008 Pinout (vista superior):
          
          CH0  [1    16] VDD (3.3V)
          CH1  [2    15] VREF (3.3V)
          CH2  [3    14] AGND (GND)
          CH3  [4    13] CLK  -> GPIO 11 (SCLK)
          CH4  [5    12] DOUT -> GPIO 9  (MISO)
          CH5  [6    11] DIN  -> GPIO 10 (MOSI)
          CH6  [7    10] CS   -> GPIO 8  (CE0)
          CH7  [8     9] DGND (GND)


    3.3V             GND
     |                |
     |                |
  [Botón] ----+---> GND
              |
            GPIO 2 (Raspberry Pi)
            
    LED Rojo (+) ---[220Ω]--- GPIO 11
    LED Rojo (-) --------------- GND
    
    LED Amarillo (+) ---[220Ω]--- GPIO 10
    LED Amarillo (-) ---------------- GND
    
    LED Verde (+) ---[220Ω]--- GPIO 9
    LED Verde (-) --------------- GND
```

## Lista de Materiales

### Para Arduino:
- [ ] 1x Arduino Uno/Nano/Mega
- [ ] 1x Sensor LM35
- [ ] 3x LEDs (1 Rojo, 1 Amarillo, 1 Verde)
- [ ] 3x Resistencias 220Ω
- [ ] 1x Pulsador (push button)
- [ ] 1x Resistencia 10kΩ (opcional, para pull-down)
- [ ] 1x Protoboard
- [ ] Cables jumper (macho-macho)
- [ ] Cable USB para programar Arduino

### Para Raspberry Pi (ADICIONAL a lo anterior):
- [ ] 1x Raspberry Pi (cualquier modelo con GPIO)
- [ ] 1x MCP3008 (ADC de 10 bits)
- [ ] Tarjeta microSD con Raspberry Pi OS
- [ ] Fuente de alimentación para Raspberry Pi

## Notas Importantes

### Arduino
- El LM35 se conecta directamente al pin analógico A0
- Arduino tiene ADC interno de 10 bits (valores 0-1023)
- Voltaje de referencia: 5V

### Raspberry Pi
- La Raspberry Pi NO tiene pines analógicos, por eso necesita el MCP3008
- El MCP3008 se comunica por SPI con la Raspberry Pi
- Voltaje de referencia: 3.3V (o 5V según tu configuración)
- Debes habilitar SPI en la configuración de la Raspberry Pi
- Los pines GPIO usados son los estándar de SPI0:
  - SCLK: GPIO 11 (pin físico 23)
  - MISO: GPIO 9 (pin físico 21)
  - MOSI: GPIO 10 (pin físico 19)
  - CE0: GPIO 8 (pin físico 24)

### Advertencias
⚠️ **IMPORTANTE**: 
- No conectes 5V directamente a los GPIO de la Raspberry Pi (solo soportan 3.3V)
- Si usas el LM35 con 5V, asegúrate de que la salida no exceda 3.3V
- Los LEDs siempre deben tener resistencias limitadoras de corriente
- Verifica la polaridad correcta de los LEDs (ánodo/cátodo)
