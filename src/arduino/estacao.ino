// Estação Meteorológica — simulação via sensor ultrassônico HC-SR04
// A distância medida é mapeada para temperatura, umidade e pressão,
// permitindo variar os valores aproximando/afastando a mão do sensor.

const int trigPin = 9;
const int echoPin = 10;

// Faixa de distância útil do HC-SR04 (cm)
const float DIST_MIN = 2.0;
const float DIST_MAX = 200.0;

// Faixas de saída de cada variável
const float TEMP_MIN  = 15.0,  TEMP_MAX  = 40.0;   // °C
const float UMID_MIN  = 30.0,  UMID_MAX  = 95.0;   // %
const float PRES_MIN  = 990.0, PRES_MAX  = 1030.0; // hPa

// Mapeia um valor float de uma faixa para outra
float mapFloat(float valor, float inMin, float inMax, float outMin, float outMax) {
  valor = constrain(valor, inMin, inMax);
  return (valor - inMin) / (inMax - inMin) * (outMax - outMin) + outMin;
}

float lerDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH, 30000); // timeout 30ms
  if (duracao == 0) return -1; // sem eco — objeto fora de alcance

  return duracao * 0.034 / 2.0;
}

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  float distancia = lerDistancia();

  if (distancia < 0) {
    // Leitura inválida — aguarda sem enviar
    delay(500);
    return;
  }

  float temperatura = mapFloat(distancia, DIST_MIN, DIST_MAX, TEMP_MIN,  TEMP_MAX);
  float umidade     = mapFloat(distancia, DIST_MIN, DIST_MAX, UMID_MAX,  UMID_MIN); // inverso: perto = mais úmido
  float pressao     = mapFloat(distancia, DIST_MIN, DIST_MAX, PRES_MIN,  PRES_MAX);

  // Saída JSON — lida pelo serial_reader.py
  Serial.print("{");
  Serial.print("\"temperatura\":"); Serial.print(temperatura, 1);
  Serial.print(",\"umidade\":");    Serial.print(umidade, 1);
  Serial.print(",\"pressao\":");    Serial.print(pressao, 1);
  Serial.print(",\"distancia\":");  Serial.print(distancia, 1);
  Serial.println("}");

  delay(2000);
}
