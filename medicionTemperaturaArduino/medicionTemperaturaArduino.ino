// --- Estación de Monitoreo de Temperatura ---
// Versión Arduino - Parte A (LEDs en 10, 9, 8)

#define LM35_PIN A0
#define BTN_PIN  2
#define LED_R 11
#define LED_Y 10
#define LED_G 9

const float X = 0.07;       // 7% de tolerancia
const int N = 5;            // cantidad de muestras para promedio
float lecturas[N];
int idx = 0;
int total = 0;
float promedio = 0;
float ciclo = 3.5;          // segundos
unsigned long t0 = 0;

void setup() {
  Serial.begin(9600);
  pinMode(LM35_PIN, INPUT);
  pinMode(BTN_PIN, INPUT_PULLUP); // botón a GND
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);

  Serial.println("Iniciando monitoreo de temperatura...");
  Serial.print("Frecuencia inicial: ");
  Serial.print(ciclo);
  Serial.println(" s");
  encenderTodos();
}

void loop() {
  // --- verificar pulsador ---
  if (digitalRead(BTN_PIN) == LOW) {  // LOW = presionado
    unsigned long presionado = millis();
    int segundos = 0;
    while (digitalRead(BTN_PIN) == LOW) {
      if (millis() - presionado >= (unsigned long)(segundos + 1) * 1000) {
        destellar();
        segundos++;
      }
    }
    float segundosPress = (millis() - presionado) / 1000.0;

    if (segundosPress < 1.0) {
      Serial.println("Pulsacion corta: fin del monitoreo");
      encenderTodos();
      while (true);
    } else if (segundosPress < 2.5) {
      ciclo = 2.5;
    } else if (segundosPress <= 10.0) {
      ciclo = segundosPress;
    } else {
      ciclo = 10.0;
    }
    Serial.print("Nuevo ciclo configurado: ");
    Serial.print(ciclo);
    Serial.println(" s");
  }

  // --- medir temperatura ---
  if (millis() - t0 >= ciclo * 1000) {
    t0 = millis();
    float lectura = analogRead(LM35_PIN);
    float temperatura = (lectura * 5.0 / 1023.0) / 0.01; // LM35: 10 mV/°C

    if (total < N) total++;
    lecturas[idx] = temperatura;
    idx = (idx + 1) % N;

    promedio = promedioN(lecturas, total);

    String tendencia;
    if (total < N) {
      tendencia = "INSUFICIENTE";
      encenderTodos();
    } else {
      float diff = temperatura - promedio;
      if (diff > promedio * X) {
        tendencia = "ALZA";
        encenderUno(LED_R);
      } else if (diff < -promedio * X) {
        tendencia = "BAJA";
        encenderUno(LED_G);
      } else {
        tendencia = "ESTABLE";
        encenderUno(LED_Y);
      }
    }

    destellar();
    Serial.print("Temperatura: ");
    Serial.print(temperatura, 2);
    Serial.print(" °C | Promedio (N=");
    Serial.print(total);
    Serial.print("): ");
    Serial.print(promedio, 2);
    Serial.print(" °C | Tendencia: ");
    Serial.println(tendencia);
  }
}

// --- Funciones auxiliares ---
float promedioN(float arr[], int n) {
  float sum = 0;
  for (int i = 0; i < n; i++) sum += arr[i];
  return sum / n;
}

void encenderTodos() {
  digitalWrite(LED_R, HIGH);
  digitalWrite(LED_Y, HIGH);
  digitalWrite(LED_G, HIGH);
}

void encenderUno(int led) {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, LOW);
  digitalWrite(led, HIGH);
}

void destellar() {
  encenderTodos();
  delay(50);
  apagarTodos();
}

void apagarTodos() {
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_Y, LOW);
  digitalWrite(LED_G, LOW);
}