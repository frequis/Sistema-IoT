import serial
import json
import requests
import time
from config import SERIAL_PORTA as PORTA, SERIAL_BAUD as BAUD, API_URL as URL

INTERVALO = 0.1  # segundos entre leituras do buffer serial


def ler_serial():
    while True:
        try:
            print(f"Conectando em {PORTA} @ {BAUD} baud...")
            with serial.Serial(PORTA, BAUD, timeout=2) as ser:
                print("Conexão estabelecida. Aguardando dados do Arduino...")
                while True:
                    linha = ser.readline().decode("utf-8", errors="replace").strip()
                    if not linha:
                        continue
                    try:
                        dados = json.loads(linha)
                        resp = requests.post(URL, json=dados, timeout=5)
                        print(f"Enviado: {dados} → HTTP {resp.status_code}")
                    except json.JSONDecodeError:
                        print(f"Linha inválida (não é JSON): {linha}")
                    except requests.exceptions.ConnectionError:
                        print("Erro: não foi possível conectar à API Flask. Verifique se o servidor está rodando.")
                    except requests.exceptions.Timeout:
                        print("Erro: timeout ao enviar para a API.")
                    time.sleep(INTERVALO)

        except serial.SerialException as e:
            print(f"Erro serial: {e}. Tentando reconectar em 5 segundos...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\nLeitura serial encerrada pelo usuário.")
            break


if __name__ == "__main__":
    ler_serial()
