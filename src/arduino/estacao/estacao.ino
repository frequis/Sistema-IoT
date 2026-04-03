// Estação Meteorológica — sensor ultrassônico HC-SR04
// Envia apenas a distância bruta; o servidor Python faz o mapeamento
// para temperatura, umidade e pressão.

const int trigPin = 9;
const int echoPin = 10;

float lerDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH, 30000); // timeout 30 ms
  if (duracao == 0) return -1;                  // sem eco

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
    delay(500);
    return;
  }

  Serial.print("{\"distancia\":");
  Serial.print(distancia, 1);
  Serial.println("}");

  delay(2000);
}
