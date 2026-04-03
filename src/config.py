import os

# Porta serial do Arduino
SERIAL_PORTA = os.getenv("SERIAL_PORTA", "COM5")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "9600"))

# URL base da API Flask
API_URL = os.getenv("API_URL", "http://localhost:5000/leituras")

# Flask
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
