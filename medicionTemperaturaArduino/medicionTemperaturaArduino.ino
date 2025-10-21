// =============================================================
//  Estación de Monitoreo de Temperatura - Parte A
//  Autor: Juan Francisco Bazan Carrizo
//  Descripción:
//  Este programa mide temperatura usando un sensor LM35,
//  controla un ciclo de muestreo variable mediante un pulsador,
//  y muestra la tendencia térmica con un semáforo de 3 LEDs.
//
//  LED_R (rojo): Temperatura en alza
//  LED_Y (amarillo): Temperatura estable
//  LED_G (verde): Temperatura en baja
// =============================================================

#define LM35_PIN A0     // Pin analógico donde está conectado el sensor LM35
#define BTN_PIN  2      // Pin digital del pulsador (usa PULLUP interno)
#define LED_R 11         // LED ROJO
#define LED_Y 10         // LED AMARILLO
#define LED_G 9          // LED VERDE

const float X = 0.07;   // Margen de variación de ±7% para definir "estable"
const int N = 5;        // Cantidad de muestras para calcular el promedio
float lecturas[N];      // Arreglo circular para almacenar las últimas N lecturas
int idx = 0;            // Índice del arreglo circular
int total = 0;          // Cantidad de lecturas acumuladas (hasta N)
float promedio = 0;     // Promedio de las N lecturas
float ciclo = 3.5;      // Duración del ciclo de medición en segundos
unsigned long t0 = 0;   // Marca de tiempo del último ciclo

void setup() {
  // --- Configuración inicial ---
  Serial.begin(9600);                  // Inicia la comunicación serial con el monitor
  pinMode(LM35_PIN, INPUT);            // Sensor de temperatura
  pinMode(BTN_PIN, INPUT);      // Pulsador con resistencia PULLUP interna
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);

  // Mensajes iniciales
  Serial.println("===========================================");
  Serial.println("     Estacion de Monitoreo de Temperatura  ");
  Serial.println("===========================================");
  Serial.println("Configuracion inicial:");
  Serial.print("Ciclo de medicion = ");
  Serial.print(ciclo);
  Serial.println(" s");
  Serial.println("Listo para comenzar...");
  encenderTodos();                     // Encendemos los 3 LEDs como indicador de inicio
  delay(1000);
  apagarTodos();
}

void loop() {
  // ============================================================
  // --- SECCIÓN 1: Verificar el pulsador -----------------------
  // ============================================================
  if (digitalRead(BTN_PIN) == LOW) {   // LOW = presionado (por el INPUT_PULLUP)
    unsigned long presionado = millis();
    int segundos = 0;

    Serial.println();
    Serial.println("Boton presionado... midiendo duracion...");
    
    // Mientras el botón se mantenga presionado
    if (digitalRead(BTN_PIN) == HIGH) {  // HIGH = presionado
      // Cada segundo exacto destella los LEDs por 50ms
      if (millis() - presionado >= (unsigned long)(segundos + 1) * 1000) {
        destellar();
        segundos++;
        Serial.print("   Segundos presionado: ");
        Serial.println(segundos);
      }
    }

    // Tiempo total de pulsación en segundos
    float segundosPress = (millis() - presionado) / 1000.0;
    Serial.print("Duracion total del pulso: ");
    Serial.print(segundosPress);
    Serial.println(" segundos");

    // --- Decisiones según la duración ---
    if (segundosPress < 1.0) {
      Serial.println("Pulsacion corta detectada: Fin del monitoreo.");
      encenderTodos();
      while (true);  // Se detiene el programa aquí
    } 
    else if (segundosPress < 2.5) {
      ciclo = 2.5;
      Serial.println("Pulsacion media: nuevo ciclo = 2.5 s");
    } 
    else if (segundosPress <= 10.0) {
      ciclo = segundosPress;
      Serial.print("Pulsacion larga: nuevo ciclo = ");
      Serial.print(ciclo);
      Serial.println(" s");
    } 
    else {
      ciclo = 10.0;
      Serial.println("Pulsacion muy larga: ciclo limitado a 10 s");
    }

    Serial.println("-------------------------------------------");
  }

  // ============================================================
  // --- SECCIÓN 2: Medir temperatura ----------------------------
  // ============================================================
  if (millis() - t0 >= ciclo * 1000) {     // Si pasó el tiempo del ciclo
    t0 = millis();                         // Reinicia el contador del ciclo
    float lectura = analogRead(LM35_PIN);  // Lee valor analógico del sensor (0–1023)
    float temperatura = (lectura * 5.0 / 1023.0) / 0.01; // Conversión a °C (10mV/°C)

    Serial.println();
    Serial.println("------ NUEVO CICLO DE MEDICIÓN ------");
    Serial.print("Lectura analogica cruda: ");
    Serial.println(lectura);
    Serial.print("Temperatura medida: ");
    Serial.print(temperatura, 2);
    Serial.println(" °C");

    // --- Actualizar buffer circular de lecturas ---
    if (total < N) total++;                // Hasta llenar el arreglo
    lecturas[idx] = temperatura;
    idx = (idx + 1) % N;                   // Avanza circularmente

    // --- Calcular promedio actual ---
    promedio = promedioN(lecturas, total);
    Serial.print("Promedio de las ultimas ");
    Serial.print(total);
    Serial.print(" lecturas: ");
    Serial.print(promedio, 2);
    Serial.println(" °C");

    // --- Determinar tendencia ---
    String tendencia;
    if (total < N) {
      tendencia = "INSUFICIENTE";
      encenderTodos();                     // No hay suficientes datos todavía
      Serial.println("Tendencia: No hay suficientes lecturas para analizar.");
    } 
    else {
      float diff = temperatura - promedio;

      if (diff > promedio * X) {           // Temperatura sube más del X%
        tendencia = "ALZA";
        encenderUno(LED_R);
      } 
      else if (diff < -promedio * X) {     // Temperatura baja más del X%
        tendencia = "BAJA";
        encenderUno(LED_G);
      } 
      else {                               // Se mantiene estable
        tendencia = "ESTABLE";
        encenderUno(LED_Y);
      }

      Serial.print("Diferencia respecto al promedio: ");
      Serial.println(diff, 3);
      Serial.print("Tendencia detectada: ");
      Serial.println(tendencia);
    }

    // --- Señal visual de fin de ciclo ---
    destellar(); // parpadeo de 50ms de los tres LEDs

    Serial.print("Ciclo de ");
    Serial.print(ciclo);
    Serial.println(" segundos completado.");
    Serial.println("-------------------------------------------");
  }
}

// ============================================================
// --- Funciones auxiliares -----------------------------------
// ============================================================

// Calcula el promedio de las últimas n lecturas
float promedioN(float arr[], int n) {
  float sum = 0;
  for (int i = 0; i < n; i++) sum += arr[i];
  return sum / n;
}

// Enciende los tres LEDs
void encenderTodos() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_Y, HIGH);
  digitalWrite(LED_G, HIGH);
}

// Enciende solo un LED y apaga los otros
void encenderUno(int led) {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(led, HIGH);
}

// Hace parpadear los tres LEDs durante 50 ms
void destellar() {
  encenderTodos();
  delay(50);
  apagarTodos();
}

// Apaga los tres LEDs
void apagarTodos() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, LOW);
}