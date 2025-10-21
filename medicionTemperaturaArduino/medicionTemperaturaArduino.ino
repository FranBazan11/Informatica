// =============================================================
//  Estacion de Monitoreo de Temperatura - Parte A
//  Autor: Juan Francisco Bazan Carrizo
//  Descripcion:
//  Mide temperatura con LM35, controla el ciclo de muestreo
//  mediante un pulsador y muestra la tendencia termica con LEDs.
// =============================================================

#define LM35_PIN A0     // Pin analogico del sensor LM35
#define BTN_PIN  2      // Pin digital del pulsador
#define LED_R 11        // LED ROJO
#define LED_Y 10        // LED AMARILLO
#define LED_G 9         // LED VERDE

const float X = 0.07;   // Margen de variacion de 7%
const int N = 5;        // Cantidad de muestras para el promedio
float lecturas[N];      // Ultimas lecturas
int idx = 0;
int total = 0;
float promedio = 0;
float ciclo = 3.5;      // Ciclo inicial en segundos
unsigned long t0 = 0;   // Marca de tiempo

void setup() {
  Serial.begin(9600);
  pinMode(LM35_PIN, INPUT);
  pinMode(BTN_PIN, INPUT_PULLUP); // boton a GND
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);
  pinMode(LED_G, OUTPUT);

  Serial.println("===========================================");
  Serial.println(" Estacion de Monitoreo de Temperatura ");
  Serial.println("===========================================");
  Serial.print("Ciclo inicial: ");
  Serial.print(ciclo);
  Serial.println(" s");
  encenderTodos();
  delay(1000);
  apagarTodos();
}

void loop() {
  // ============================================================
  // --- SECCION 1: Verificar pulsador --------------------------
  // ============================================================

  // Verifica si el boton esta presionado
  if (digitalRead(BTN_PIN) == LOW) {
    delay(20); // antirrebote simple
    if (digitalRead(BTN_PIN) == LOW) { // confirmacion
      unsigned long presionado = millis();

      // Espera hasta que se suelte el boton
      while (digitalRead(BTN_PIN) == LOW) {
        // Cada segundo destella LEDs 50ms
        if ((millis() - presionado) % 1000 < 50) destellar();
      }

      // Tiempo total de presion en segundos
      float segundosPress = (millis() - presionado) / 1000.0;
      Serial.print("Duracion de pulsacion: ");
      Serial.print(segundosPress);
      Serial.println(" s");

      // --- Acciones segun la duracion ---
      if (segundosPress < 1.0) {
        Serial.println("Pulsacion corta: fin del monitoreo.");
        encenderTodos();
        while (true); // Detiene ejecucion
      }
      else if (segundosPress < 2.5) {
        ciclo = 2.5;
        Serial.println("Nuevo ciclo: 2.5 s");
      }
      else if (segundosPress <= 10.0) {
        ciclo = segundosPress;
        Serial.print("Nuevo ciclo: ");
        Serial.print(ciclo);
        Serial.println(" s");
      }
      else {
        ciclo = 10.0;
        Serial.println("Pulsacion larga: ciclo limitado a 10 s");
      }

      Serial.println("-------------------------------------------");
    }
  }

  // ============================================================
  // --- SECCION 2: Medir temperatura ---------------------------
  // ============================================================

  if (millis() - t0 >= ciclo * 1000) {
    t0 = millis();
    float lectura = analogRead(LM35_PIN);
    float temperatura = (lectura * 5.0 / 1023.0) / 0.01;

    Serial.println();
    Serial.println("------ NUEVO CICLO DE MEDICION ------");
    Serial.print("Lectura analogica: ");
    Serial.println(lectura);
    Serial.print("Temperatura: ");
    Serial.print(temperatura, 2);
    Serial.println(" C");

    // Actualiza buffer de lecturas
    if (total < N) total++;
    lecturas[idx] = temperatura;
    idx = (idx + 1) % N;

    promedio = promedioN(lecturas, total);

    Serial.print("Promedio ultimas ");
    Serial.print(total);
    Serial.print(" lecturas: ");
    Serial.print(promedio, 2);
    Serial.println(" C");

    // Determinar tendencia
    String tendencia;
    if (total < N) {
      tendencia = "INSUFICIENTE";
      encenderTodos();
      Serial.println("No hay suficientes datos para calcular tendencia.");
    }
    else {
      float diff = temperatura - promedio;
      if (diff > promedio * X) {
        tendencia = "ALZA";
        encenderUno(LED_R);
      }
      else if (diff < -promedio * X) {
        tendencia = "BAJA";
        encenderUno(LED_G);
      }
      else {
        tendencia = "ESTABLE";
        encenderUno(LED_Y);
      }
      Serial.print("Diferencia: ");
      Serial.println(diff, 3);
      Serial.print("Tendencia: ");
      Serial.println(tendencia);
    }

    destellar();
    Serial.print("Ciclo de ");
    Serial.print(ciclo);
    Serial.println(" s completado.");
    Serial.println("-------------------------------------------");
  }
}

// ============================================================
// --- FUNCIONES AUXILIARES -----------------------------------
// ============================================================

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