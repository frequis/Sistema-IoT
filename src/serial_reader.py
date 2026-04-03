import serial, json, requests, time
PORTA = 'COM3' # Windows: COM3 / Linux: /dev/ttyUSB0
BAUD = 9600
URL = 'http://localhost:5000/leituras'
def ler_serial():
with serial.Serial(PORTA, BAUD, timeout=2) as ser:
while True:
linha = ser.readline().decode('utf-8').strip()
if linha:
try:
dados = json.loads(linha)
requests.post(URL, json=dados)
print(f'Enviado: {dados}')
except json.JSONDecodeError:
print(f'Linha inválida: {linha}')
time.sleep(0.1)
if __name__ == '__main__':
ler_serial()
